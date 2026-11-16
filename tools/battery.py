"""Print the battery level of all Logitech HID++ Bluetooth devices (read-only)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import hid  # noqa: E402
from mouse_follow import hidpp_devices, feature_index, request  # noqa: E402

LEVELS = {1: "critical", 2: "low", 4: "good", 8: "full"}

for product, path in hidpp_devices():
    h = hid.device()
    h.open_path(path)
    try:
        idx = feature_index(h, 0x1004)              # Unified Battery
        if idx and (r := request(h, idx, 1)):
            print(f"{product}: {r[4]}% ({LEVELS.get(r[5], r[5])})")
            continue
        idx = feature_index(h, 0x1000)              # Battery Level Status
        if idx and (r := request(h, idx, 0)):
            print(f"{product}: {r[4]}% (next level {r[5]}%)")
            continue
        print(f"{product}: battery level not available")
    finally:
        h.close()
