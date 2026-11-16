"""Switch a Logitech HID++ device to another Easy-Switch slot.

Example:  python tools/switch_host.py MX_Vertical 1
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from mouse_follow import find_path, send_to_host  # noqa: E402

if len(sys.argv) != 3 or sys.argv[2] not in ("1", "2", "3"):
    sys.exit("usage: switch_host.py <product name> <slot 1-3>")

path = find_path(sys.argv[1])
if not path:
    sys.exit(f"{sys.argv[1]!r} is not connected to this host")
if send_to_host(path, int(sys.argv[2])):
    print(f"{sys.argv[1]} sent to slot {sys.argv[2]}")
