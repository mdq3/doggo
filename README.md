# Doggo MicroPython

MicroPython control of a Petoi Bittle X V2 quadruped robot. Runs Python directly on the BiBoard ESP32 — no external computer required for autonomous operation.

Replaces the stock OpenCat firmware with hand-written Python. Gaits are ported from OpenCat keyframe arrays.

---

## Prerequisites

### Hardware
- Petoi Bittle X V2 with BiBoard V1.0
- USB Type-C cable (one-time setup only)

### Software

```bash
pip install esptool    # for flashing firmware
pip install mpremote   # for initial USB bootstrap
pip install ruff       # for linting
```

Run `ruff check src/` to lint. Config is in `pyproject.toml`.

---

## Getting Started

USB is only needed to flash MicroPython and bootstrap WiFi. Everything after that runs over the air.

### 1. Flash MicroPython (USB)

Back up your original firmware first:

```bash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 biboard_backup.bin
```

Download and flash MicroPython:

```bash
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin

esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin
```

### 2. Configure WiFi credentials

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

### 3. Bootstrap WiFi (USB, one-time)

Upload just enough to get the robot onto the network:

```bash
mpremote fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/main.py :main.py
```

Press the reset button. The robot will connect to WiFi and start WebREPL. It will be reachable as `doggo.local` (or whatever `HOSTNAME` you set).

### 4. Deploy everything (WiFi)

Upload all source files in one shot:

```bash
python deploy.py
```

Press reset again to load the deployed files. You can unplug USB — the robot is now fully wireless.

### 5. Calibrate servos (WiFi)

```bash
alias dog='python webrepl_proxy.py'

dog fs mkdir :drivers
dog fs cp src/drivers/servo.py :drivers/servo.py
dog fs cp src/configuration/calibrate.py :calibrate.py
dog repl
```

```python
>>> from calibrate import *
>>> move(4, 90)   # adjust front-left shoulder to neutral
>>> save(4, 87)   # save when centered
>>> done()        # prints config.py content — copy it
```

Paste the output into `config.py` at the repo root, then upload it:

```bash
dog fs cp config.py :config.py
```

See `docs/micropython-getting-started.md` for the full calibration walkthrough.

---

## Control

The robot can be controlled via REST API or by sending a Python script over the air to the robot.

### Send commands via REST API

```bash
curl http://doggo.local/stand
curl http://doggo.local/sit
curl http://doggo.local/rest
curl http://doggo.local/walk?steps=3
curl http://doggo.local/walk_back?steps=3
curl http://doggo.local/turn_left?steps=1
curl http://doggo.local/turn_right?steps=1
curl http://doggo.local/pivot_left?steps=1   # in-place rotation
curl http://doggo.local/pivot_right?steps=1
curl http://doggo.local/bound_left?steps=1   # tight arc turn
curl http://doggo.local/bound_right?steps=1
curl http://doggo.local/trot?steps=2         # fast diagonal-pair trot with IMU stabilization
curl http://doggo.local/battery
curl http://doggo.local/info
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

- **[Getting Started Guide](docs/micropython-getting-started.md)** — full step-by-step setup
- **[File Reference Guide](docs/file-reference-guide.md)** — every file explained
- **[Hardware & OpenCat Reference](docs/hardware-and-opencat-reference.md)** — pinout, angle conversion, restoring firmware
