# MouseFollow

Make a Logitech mouse follow a Logitech keyboard when you press the keyboard's
**Easy-Switch** key.

Many Logitech keyboards and mice can be paired with up to three computers over
Bluetooth, but each device has its own Easy-Switch button. Switching the keyboard
to another computer leaves the mouse behind, so you have to flip it over and
press its button as well. Logitech's own answer, *Flow*, works the other way
round: the mouse moves across screen edges and the keyboard follows it.

MouseFollow keeps the keyboard in charge. You press the keyboard's Easy-Switch
key, and the mouse comes along.

## How it works

```
 Computer A (slot 2)                              Computer B (slot 1)
 ┌───────────────────────────┐                    ┌────────────────────┐
 │ mouse_follow.py --target 1│                    │ mouse_follow.py    │
 │                           │                    │        --target 2  │
 │ 1. keyboard disappears ◄──┼── Easy-Switch "1" ─┼──► keyboard        │
 │ 2. HID++ "Change Host 1" ─┼──► mouse ──────────┼──► mouse           │
 └───────────────────────────┘                    └────────────────────┘
```

1. Every computer runs `mouse_follow.py` in the background. It polls the list
   of HID devices and notices when the keyboard disconnects.
2. At that moment the mouse is still connected to the computer the keyboard
   just left. The script sends it the HID++ 2.0 command
   [`Change Host` (feature `0x1814`)](https://github.com/pwr-Solaar/Solaar/blob/master/docs/features.md),
   `setCurrentHost(target - 1)`.
3. The mouse disconnects and reconnects to the target slot, just as if you had
   pressed its own Easy-Switch button.

The script never writes to the keyboard. The computers don't talk to each other
and need no network. A switch typically takes well under a second.

## Requirements

- A Logitech keyboard and mouse that support Easy-Switch and HID++ 2.0 with
  feature `0x1814`. Most current MX, ERGO and Pebble devices do.
  `--list` tells you whether yours do.
- Both devices connected via **Bluetooth**. Logi Bolt and Unifying receivers
  use a different HID++ interface and are not supported yet.
- Python 3.8+ and [`hidapi`](https://pypi.org/project/hidapi/).

Tested with an **ERGO K860** keyboard and an **MX Vertical** mouse on
**Windows 11**. `hidapi` also runs on macOS and Linux, but MouseFollow hasn't
been tested there (see [Limitations](#limitations)).

## Installation

```bash
git clone https://github.com/DrOeti/MouseFollow.git
cd MouseFollow
python -m pip install -r requirements.txt
```

Pair the keyboard and the mouse with the **same slot number** on each computer.
For example, computer A uses slot 2 on both devices and computer B uses slot 1
on both. Then check that both devices are detected:

```bash
python mouse_follow.py --list
```

```
'MX_Vertical': Change Host supported, 3 slots, currently on slot 2
'ERGO_K860': Change Host supported, 3 slots, currently on slot 2
```

## Usage

On each computer, set `--target` to the slot of the *other* computer:

```bash
# on computer A (slot 2)
python mouse_follow.py --target 1

# on computer B (slot 1)
python mouse_follow.py --target 2
```

If your devices aren't the defaults, pass the names that `--list` shows:

```bash
python mouse_follow.py --target 1 --keyboard "MX Keys" --mouse "MX Master 3S"
```

| Option | Default | Meaning |
|---|---|---|
| `--target N` | required | Slot (1–3) the mouse switches to when the keyboard leaves |
| `--keyboard NAME` | `ERGO_K860` | Keyboard product name |
| `--mouse NAME` | `MX_Vertical` | Mouse product name |
| `--poll SEC` | `0.25` | How often the device list is checked |
| `--log FILE` | `mouse_follow.log` next to the script | Log file |
| `--list` | | List Logitech HID++ devices and exit |

### Start automatically (Windows)

Create a shortcut in the startup folder (`Win+R` → `shell:startup`) with this
target:

```
pythonw.exe "C:\path\to\MouseFollow\mouse_follow.py" --target 1
```

`pythonw` runs the script without a console window. Errors and every switch
are written to `mouse_follow.log`.

## Tools

| Script | Purpose |
|---|---|
| `tools/battery.py` | Prints the battery level of all connected Logitech HID++ devices |
| `tools/switch_host.py NAME SLOT` | Sends one device to a slot manually, e.g. `MX_Vertical 1` |

## Limitations

- **Two computers work out of the box.** With three, each computer has to know
  which slot the keyboard went to. The script can't tell that locally, because
  it only sees the keyboard disappear. `--target` is therefore one fixed slot
  per computer.
- **Any disconnect counts as a switch.** If the keyboard drops the connection
  for another reason, such as sleep, a weak battery or interference, the mouse
  is sent away too. The log shows when this happens.
- **Bluetooth only.** Devices connected through a receiver aren't detected.
- **Logi Options+** can usually run alongside the script. If switching fails,
  try quitting Options+ to rule it out.
- **macOS and Linux are untested.** On Linux you'll need a udev rule for access
  to `hidraw`. On macOS the terminal or Python needs the *Input Monitoring*
  permission.

## Acknowledgements

The HID++ protocol details come from
[Solaar](https://github.com/pwr-Solaar/Solaar) and Logitech's published HID++
2.0 specifications.

This project is not affiliated with or endorsed by Logitech.

## License

[MIT](LICENSE)
