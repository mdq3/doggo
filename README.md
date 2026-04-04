# Doggo MicroPython

MicroPython control of a Petoi Bittle X V2 quadruped robot. Runs Python directly on the BiBoard ESP32 — no external computer required for autonomous operation.

Replaces the stock OpenCat firmware with hand-written Python. Gaits are ported from OpenCat keyframe arrays.

---

## Prerequisites

### Hardware
- Petoi Bittle X V2 with BiBoard V1.0
- USB Type-C cable

### Software

#### Python tooling
```bash
pip install esptool    # for flashing firmware
pip install mpremote   # for REPL and file transfers
pip install ruff       # for linting
```

#### Robot dependencies

* Micropython 1.27.0 for ESP32

#### Linting

Run `ruff check src/` to lint. Config is in `pyproject.toml`.

---

## Getting Started

### 1. Flash MicroPython

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

### 2. Calibrate Servos

```bash
mpremote fs mkdir :drivers
mpremote fs cp src/drivers/servo.py :drivers/servo.py
mpremote fs cp src/configuration/calibrate.py :calibrate.py
mpremote repl
```

```python
>>> from calibrate import *
>>> move(4, 90)   # adjust front-left shoulder to neutral
>>> save(4, 87)   # save when centered
>>> done()        # prints config.py content — copy it
```

Paste the output into `config.py` at repo root, then:

```bash
mpremote fs cp config.py :config.py
```

See `docs/micropython-getting-started.md` for the full calibration walkthrough.

### 3. Make Doggo Stand

```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    run src/demos/stand.py
```

### 4. Make Doggo Walk

```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    run src/demos/walk.py
```

---

## WiFi Control

Remove the USB tether and control Bittle wirelessly.

### 1. Set up credentials

```bash
cp src/configuration/wifi_config_template.py wifi_config.py
# edit wifi_config.py — fill in NETWORKS, WEBREPL_PASSWORD, and optionally HOSTNAME
```

`wifi_config.py` uses a `NETWORKS` list so the robot automatically connects wherever it is:

```python
NETWORKS = [
    ("home_network", "home_password"),
    ("office_network", "office_password"),
]
WEBREPL_PASSWORD = "doggo"
HOSTNAME = "doggo"
```

`boot.py` scans visible APs and connects to the first matching network in range — no need to manually switch networks when moving locations.

`wifi_config.py` is gitignored. Never commit it.

`HOSTNAME` defaults to `"doggo"` — the device will be reachable as `http://doggo.local/`. For faster responses, use the IP address directly or `curl -4` (skips IPv6 resolution timeout).

### 2. Upload WiFi files (USB, one-time)

Bootstrap WiFi by uploading just enough to get the robot onto the network:

```bash
mpremote fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/main.py :main.py
```

Reboot (press the reset button). Once WiFi is up, deploy everything else over the air:

```bash
python deploy.py
```

Press reset again to load the deployed files.

### 3. Find the robot's IP address

Reboot and read the serial output:

```bash
mpremote repl
# press Ctrl+D for soft reset
# output: WiFi connected: 192.168.1.x
```

Or after the robot is running, open a REPL and run:

```python
>>> import network; network.WLAN(network.STA_IF).ifconfig()
('192.168.1.x', '255.255.255.0', '192.168.1.1', '192.168.1.1')
```

### 4. Send commands

```bash
curl http://192.168.1.x/stand
curl http://192.168.1.x/sit
curl http://192.168.1.x/rest
curl http://192.168.1.x/walk?steps=3
curl http://192.168.1.x/walk_back?steps=3
curl http://192.168.1.x/turn_left?steps=1
curl http://192.168.1.x/turn_right?steps=1
curl http://192.168.1.x/pivot_left?steps=1   # in-place rotation
curl http://192.168.1.x/pivot_right?steps=1
curl http://192.168.1.x/bound_left?steps=1   # tight arc turn
curl http://192.168.1.x/bound_right?steps=1
curl http://192.168.1.x/trot?steps=2         # fast diagonal-pair trot with IMU stabilization
curl http://192.168.1.x/battery
curl http://192.168.1.x/info      # device diagnostics: RAM, flash, CPU freq, chip ID, WiFi IP/RSSI, uptime
```

Or use the hostname (may be slower — see note in WiFi Control section):
```bash
curl -4 http://doggo.local/stand
```

### 5. Run scripts and transfer files over WiFi

mpremote has no built-in WebREPL support. Use `webrepl_proxy.py` — it reads host and password from `wifi_config.py` automatically:

```bash
python webrepl_proxy.py repl
python webrepl_proxy.py run src/demos/walk.py
python webrepl_proxy.py fs cp src/poses.py :poses.py
```

A shell alias makes this even shorter:

```bash
alias dog='python webrepl_proxy.py'
dog repl
dog run src/demos/walk.py
dog fs cp src/poses.py :poses.py
```

### 6. Deploy code updates

Upload changed files over WiFi, then press the reset button on the robot:

```bash
dog fs cp src/poses.py :poses.py
dog fs cp src/server.py :server.py
```

Or use `deploy.py` to upload everything at once:

```bash
python deploy.py
```

---

## Documentation

- **[Getting Started Guide](docs/micropython-getting-started.md)** — full step-by-step setup
- **[File Reference Guide](docs/file-reference-guide.md)** — every file explained
- **[Hardware & OpenCat Reference](docs/hardware-and-opencat-reference.md)** — pinout, angle conversion, restoring firmware
