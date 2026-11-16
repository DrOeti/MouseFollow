"""
mouse_follow.py - make a Logitech mouse follow a Logitech keyboard between hosts.

Both devices support Easy-Switch (up to 3 Bluetooth hosts), but each one has to
be switched by hand. This script runs on every host and watches the keyboard.
When the keyboard leaves this host (because its Easy-Switch key was pressed),
the script sends the mouse to the same target slot using the HID++ 2.0
"Change Host" feature (0x1814).

Usage:
    python mouse_follow.py --list              # show Logitech HID++ devices
    python mouse_follow.py --target 1          # run, send mouse to slot 1
    pythonw mouse_follow.py --target 1         # same, without a console (Windows)
"""
import argparse
import logging
import os
import sys
import time

import hid

LOGI_VID = 0x046D
HIDPP_USAGE_PAGE = 0xFF43       # HID++ collection of Bluetooth devices
HIDPP_LONG = 0x11               # long HID++ report (20 bytes)
DEVICE_INDEX = 0xFF             # 0xFF = device connected directly (Bluetooth)
SW_ID = 0x0A                    # arbitrary software id, echoed in replies
FEAT_ROOT = 0x0000
FEAT_CHANGE_HOST = 0x1814

DEFAULT_KEYBOARD = "ERGO_K860"
DEFAULT_MOUSE = "MX_Vertical"


# --------------------------------------------------------------------------- HID++

def hidpp_devices():
    """Yield (product_string, path) of all Logitech HID++ interfaces."""
    for d in hid.enumerate(LOGI_VID):
        if d["usage_page"] == HIDPP_USAGE_PAGE:
            yield d["product_string"], d["path"]


def find_path(name):
    for product, path in hidpp_devices():
        if product == name:
            return path
    return None


def build(feat_idx, func, *params):
    msg = [HIDPP_LONG, DEVICE_INDEX, feat_idx, (func << 4) | SW_ID] + list(params)
    return msg + [0] * (20 - len(msg))


def request(h, feat_idx, func, *params, timeout=2.0):
    """Send a HID++ request and wait for the matching reply (None on error/timeout)."""
    h.write(build(feat_idx, func, *params))
    end = time.time() + timeout
    while time.time() < end:
        r = h.read(20, 300)
        if not r:
            continue
        if r[2] == 0xFF:                            # HID++ error report
            return None
        if r[2] == feat_idx and r[3] == ((func << 4) | SW_ID):
            return r
    return None


def feature_index(h, feature_id):
    """Look up the device-specific index of a HID++ feature (0 = not supported)."""
    r = request(h, FEAT_ROOT, 0, feature_id >> 8, feature_id & 0xFF)
    return r[4] if r else 0


def host_info(h):
    """Return (number_of_hosts, current_host) with 0-based current_host, or None."""
    idx = feature_index(h, FEAT_CHANGE_HOST)
    if not idx:
        return None
    r = request(h, idx, 0)
    return (r[4], r[5]) if r else None


def send_to_host(path, slot):
    """Tell the device at `path` to switch to Easy-Switch slot `slot` (1-based)."""
    h = hid.device()
    try:
        h.open_path(path)
        idx = feature_index(h, FEAT_CHANGE_HOST)
        if not idx:
            logging.error("Device does not support Change Host (0x1814)")
            return False
        # setCurrentHost: the device disconnects immediately, no reply expected
        h.write(build(idx, 1, slot - 1))
        return True
    finally:
        h.close()


# --------------------------------------------------------------------------- commands

def list_devices():
    found = False
    for product, path in hidpp_devices():
        found = True
        h = hid.device()
        try:
            h.open_path(path)
            info = host_info(h)
        except OSError as e:
            info = None
            print(f"{product!r}: could not open ({e})")
            continue
        finally:
            h.close()
        if info:
            print(f"{product!r}: Change Host supported, {info[0]} slots, "
                  f"currently on slot {info[1] + 1}")
        else:
            print(f"{product!r}: Change Host NOT supported")
    if not found:
        print("No Logitech HID++ device connected via Bluetooth.")


def follow(keyboard, mouse, target, poll):
    logging.info("Started: keyboard=%s mouse=%s target slot=%d", keyboard, mouse, target)
    kb_here = find_path(keyboard) is not None
    logging.info("Keyboard is %s", "here" if kb_here else "not here")
    while True:
        try:
            now_here = find_path(keyboard) is not None
            if kb_here and not now_here:
                logging.info("Keyboard left this host")
                path = find_path(mouse)
                if not path:
                    logging.info("Mouse is not connected here - nothing to do")
                elif send_to_host(path, target):
                    logging.info("Mouse sent to slot %d", target)
            elif not kb_here and now_here:
                logging.info("Keyboard is back")
            kb_here = now_here
        except Exception:
            # under pythonw a crash would go unnoticed, so log and keep running
            logging.exception("Unexpected error - continuing")
        time.sleep(poll)


def main():
    ap = argparse.ArgumentParser(
        description="Make a Logitech mouse follow a Logitech keyboard's Easy-Switch.")
    ap.add_argument("--list", action="store_true",
                    help="list connected Logitech HID++ devices and exit")
    ap.add_argument("--target", type=int, choices=[1, 2, 3],
                    help="slot the mouse should switch to when the keyboard leaves")
    ap.add_argument("--keyboard", default=DEFAULT_KEYBOARD,
                    help=f"keyboard product name (default: {DEFAULT_KEYBOARD})")
    ap.add_argument("--mouse", default=DEFAULT_MOUSE,
                    help=f"mouse product name (default: {DEFAULT_MOUSE})")
    ap.add_argument("--poll", type=float, default=0.25,
                    help="polling interval in seconds (default: 0.25)")
    ap.add_argument("--log", default=os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "mouse_follow.log"),
                    help="log file (default: mouse_follow.log next to the script)")
    args = ap.parse_args()

    if args.list:
        list_devices()
        return
    if args.target is None:
        ap.error("--target is required (or use --list)")

    handlers = [logging.FileHandler(args.log, encoding="utf-8")]
    if sys.stdout is not None:                      # pythonw has no stdout
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(message)s")
    follow(args.keyboard, args.mouse, args.target, args.poll)


if __name__ == "__main__":
    main()
