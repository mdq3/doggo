# Doggo

**Doggo** - a MicroPython SDK for control of a Petoi Bittle X V2 quadruped robot. Runs Python directly on the BiBoard ESP32 — no external computer required for autonomous operation.

**Doggo Code Blocks** - a blocks-based programming app for controlling the Petoi Bittle X V2.

Replaces the stock OpenCat firmware with Micropython and Python modules. Gaits are ported from OpenCat keyframe arrays.

---

## Prerequisites

### Hardware
- Petoi Bittle X V2 with BiBoard V1.0
- USB Type-C cable (charging and one-time setup only)

---

## Getting Started

USB is only needed to flash MicroPython and bootstrap WiFi. Everything after that runs over the air.

### 1. Install required tools

```bash
pip install esptool    # for flashing firmware
pip install mpremote   # for initial USB bootstrap
```

### 2. Flash MicroPython (USB)

## Find USB port of connected robot

```bash
ls /dev/cu.usbmodem*   # macOS
ls /dev/ttyUSB*        # Linux
```

Back up your original firmware first:

```bash
esptool --chip esp32 --port /dev/<doggo-usb-port> read-flash 0x0 0x400000 biboard_backup.bin
```

Download and flash MicroPython:

```bash
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin

esptool --chip esp32 --port /dev/<doggo-usb-port> erase-flash
esptool --chip esp32 --port /dev/<doggo-usb-port> --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin
```

### Verify MicroPython

```bash
mpremote repl
# Press Enter if the prompt doesn't appear immediately
# Exit: Ctrl+]
```

```python
>>> import sys; sys.platform
'esp32'
```

### 3. Configure WiFi credentials

```bash
cp src/configuration/wifi_config_template.py wifi_config.py
# edit wifi_config.py — fill in NETWORKS, WEBREPL_PASSWORD, and optionally HOSTNAME
```

`wifi_config.py` uses a `NETWORKS` list so the robot connects wherever it is:

```python
NETWORKS = [
    ("home_network", "home_password"),
    ("office_network", "office_password"),
]
WEBREPL_PASSWORD = "doggo"
HOSTNAME = "doggo"
```

`wifi_config.py` is gitignored. Never commit it.

### 4. Bootstrap WiFi (USB, one-time)

Upload just enough to get the robot onto the network:

```bash
mpremote fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/main.py :main.py
```

Press the reset button. The robot will connect to WiFi and start WebREPL. It will be reachable as `doggo.local` (or whatever `HOSTNAME` you set).

### 5. Deploy everything (WiFi)

Upload all source files in one shot:

```bash
python deploy.py
```

Press reset again to load the deployed files. You can unplug USB — the robot is now fully wireless.

### 6. Verify servos (WiFi)

Set up the `dog` shortcut first (used for all subsequent WiFi steps):

```bash
alias dog='python webrepl_proxy.py'
```

Confirm all servos respond before spending time on calibration:

```bash
dog run src/configuration/verify_servos_working.py
```

All 9 channels should sweep briefly. If any servo doesn't move, check wiring before continuing.

### 7. Identify servos (WiFi, optional)

If you're unsure which channel controls which joint, wiggle them interactively:

```bash
dog fs cp src/configuration/identify_servos.py :identify_servos.py

dog repl
```

```python
>>> from identify_servos import *
>>> all()       # step through each channel one by one
>>> test(4)     # or wiggle a single channel
```

### 8. Calibrate servos (WiFi)

```bash
dog fs cp src/configuration/calibrate.py :calibrate.py
dog repl
```

```python
>>> from calibrate import *

# Move a servo until the joint looks mechanically centered, then save
>>> move(4, 90)    # start at 90°
>>> move(4, 87)    # nudge until front-left shoulder is centered
>>> save(4, 87)    # records offset of -3°

# Shortcuts: m() and s() work the same as move() and save()
>>> m(5, 90)
>>> m(5, 93)
>>> s(5, 93)

# Repeat for all channels: 0, 4, 5, 6, 7, 8, 9, 10, 11

# When done, print the config.py content and copy it
>>> done()
```

Paste the output into `config.py` at the repo root, then upload it:

```bash
dog fs cp config.py :config.py
```

---

## Control

The robot can be controlled via the [**Doggo Code Blocks**](./doggo-code-blocks/README.md) desktop app, the REST API, or by sending Python scripts directly over the air.

### Doggo Code Blocks app

[Doggo Code Blocks](doggo-code-blocks/) is a drag-and-drop block programming app (built with Electron and Scratch Blocks). Drag motion and pose blocks into the workspace, hit **Run**, and the app compiles the program to MicroPython and sends it to the robot over Wi-Fi — no terminal needed.

```bash
cd doggo-code-blocks
npm install
npm start
```

Enter the robot's hostname and WebREPL password in the gear ⚙ settings menu. See [doggo-code-blocks/README.md](doggo-code-blocks/README.md) for full details.

### Send commands via REST API

| Route | Parameters | Action |
|-------|-----------|--------|
| `/stand` | | Stand up |
| `/sit` | | Sit down |
| `/rest` | | Lie flat |
| `/stretch` | | Downward-dog stretch |
| `/walk` | `steps=N` | Walk forward N cycles |
| `/walk-back` | `steps=N` | Walk backward N cycles |
| `/walk-back-left` | `steps=N` | Walk backward arcing left |
| `/walk-back-right` | `steps=N` | Walk backward arcing right |
| `/turn-left` | `steps=N` | Arc turn left |
| `/turn-right` | `steps=N` | Arc turn right |
| `/pivot-left` | `steps=N` | Rotate in place left |
| `/pivot-right` | `steps=N` | Rotate in place right |
| `/bound-left` | `steps=N` | Tight arc turn left |
| `/bound-right` | `steps=N` | Tight arc turn right |
| `/step` | `steps=N` | March in place |
| `/crawl` | `steps=N` | Low-stance crawl forward |
| `/crawl-left` | `steps=N` | Low-stance crawl arcing left |
| `/crawl-right` | `steps=N` | Low-stance crawl arcing right |
| `/trot` | `steps=N` `imu=0/1` | Diagonal trot (IMU stabilization on by default) |
| `/trot-ik` | `steps=N` `imu=0/1` | IK-based trot with parametric foot trajectories |
| `/wave` | | Wave a front paw |
| `/high-five` | | Offer a high five |
| `/handshake` | | Shake hands |
| `/pee` | | Lift a rear leg |
| `/play-dead` | | Roll over and play dead |
| `/push-ups` | | Do push-ups |
| `/moonwalk` | | Moonwalk shuffle |
| `/boxing` | | Boxing jabs |
| `/battery` | | Battery voltage and charge level |
| `/info` | | Device diagnostics (RAM, flash, CPU, WiFi, uptime) |

```bash
curl http://doggo.local/walk?steps=3
curl http://doggo.local/trot?steps=2
curl http://doggo.local/battery
```

If mDNS is slow, use the IP directly or pass `-4` to skip IPv6 resolution:

```bash
curl -4 http://doggo.local/stand
curl http://192.168.1.x/stand
```

### Running Python scripts

Run a script directly — it executes on the device and streams output back:

```bash
dog run src/demos/walk.py
dog run src/demos/trot.py
```

Write your own script and run it the same way. Scripts import from the device filesystem, so all deployed modules are available:

```python
# my_sequence.py
from poses import stand, rest
from gaits.walk import walk_forward
from gaits.trot import trot_forward
import time

stand()
time.sleep(1)
walk_forward(steps=4)
trot_forward(steps=2)
rest()
```

```bash
dog run my_sequence.py
```

### Interactive REPL

For one-off commands or exploring behaviour interactively:

```bash
dog repl
```

```python
>>> from poses import stand, sit, rest
>>> stand()
>>> sit()
>>> from gaits.walk import walk_forward
>>> walk_forward(steps=3)
>>> rest()
```

### Deploy code updates

```bash
python deploy.py        # upload everything, then press reset
dog fs cp src/poses.py :poses.py   # upload a single file
```

---

## Documentation

- **[Hardware Setup & Calibration](docs/micropython-getting-started.md)** — flashing, servo verification, channel identification, calibration
- **[Hardware & OpenCat Reference](docs/hardware-and-opencat-reference.md)** — pinout, angle conversion, restoring firmware
