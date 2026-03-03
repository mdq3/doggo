# Bittle MicroPython

MicroPython control of a Petoi Bittle X V2 quadruped robot. Runs Python directly on the BiBoard ESP32 — no external computer required for autonomous operation.

Replaces the stock OpenCat firmware with hand-written Python. Gaits are ported from OpenCat keyframe arrays.

---

## Prerequisites

### Hardware
- Petoi Bittle X V2 with BiBoard V1.0
- USB Type-C cable
- Fully charged battery (required for servo steps)

### Software
```bash
pip install esptool    # for flashing firmware
pip install mpremote   # for REPL and file transfers
```

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
mpremote fs cp src/drivers/servo.py :servo.py
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

### 3. Make Bittle Stand

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    run src/demos/stand.py
```

### 4. Make Bittle Walk

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
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
# edit wifi_config.py — fill in SSID, PASSWORD, WEBREPL_PASSWORD
```

`wifi_config.py` is gitignored. Never commit it.

### 2. Upload WiFi files (USB, one-time)

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/battery.py :battery.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/server.py :server.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    fs cp src/main.py :main.py
```

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
curl http://192.168.1.x/battery
curl http://192.168.1.x/restart   # reload code without touching servos
```

### 5. Run scripts and transfer files over WiFi

mpremote has no built-in WebREPL support. Use `src/webrepl_proxy.py` — pass the mpremote subcommand directly and it handles everything:

```bash
python src/webrepl_proxy.py 192.168.1.x doggo repl
python src/webrepl_proxy.py 192.168.1.x doggo run src/demos/walk.py
python src/webrepl_proxy.py 192.168.1.x doggo fs cp src/poses.py :poses.py
```

A shell alias makes this even shorter:

```bash
alias dog='python src/webrepl_proxy.py 192.168.1.x doggo'
dog repl
dog run src/demos/walk.py
dog fs cp src/poses.py :poses.py
```

### 6. Deploy code updates

After uploading new files, reload them without a hardware reset (servos stay still):

```bash
# Upload changed files, then reload
dog fs cp src/poses.py :poses.py
dog fs cp src/server.py :server.py
curl http://192.168.1.x/restart
```

`/restart` reloads `server.py`, `poses.py`, `battery.py`, and `gaits/walk.py` from flash. Servo PWM stays running throughout — no movement.

Changes to `servo.py`, `boot.py`, or `main.py` require a physical power cycle.

---

## Project Structure

```
doggo/
├── src/
│   ├── drivers/
│   │   └── servo.py                # PWM servo driver (ESP32 LEDC, 200Hz)
│   ├── configuration/
│   │   ├── calibrate.py            # Interactive REPL calibration tool
│   │   ├── identify_servos.py      # Map channel numbers to joints
│   │   ├── verify_servos_working.py # Quick servo sanity check
│   │   └── wifi_config_template.py # Copy → wifi_config.py
│   ├── gaits/
│   │   └── walk.py                 # Walk gait (one foot at a time, 116 frames)
│   ├── battery.py                  # Battery voltage monitoring (GPIO 37, BiBoard formula)
│   ├── demos/
│   │   ├── stand.py                # stand → sit → stand → rest
│   │   └── walk.py                 # stand → walk → rest
│   ├── boot.py                     # WiFi connect + WebREPL (deployed as :boot.py)
│   ├── main.py                     # HTTP server start (deployed as :main.py)
│   ├── server.py                   # HTTP command server (port 80)
│   ├── webrepl_proxy.py            # Host-side PTY bridge for mpremote over WiFi
│   └── poses.py                    # Pose library (stand, sit, rest, move_to)
├── docs/
│   ├── micropython-getting-started.md   # Full step-by-step setup guide
│   ├── file-reference-guide.md          # Every file: what it does, how to use it
│   ├── hardware-and-opencat-reference.md # Hardware pinout, porting OpenCat, restoring firmware
│   └── ...
├── config.py                       # Servo calibration offsets (gitignored — generate locally)
└── README.md
```

---

## Documentation

- **[Getting Started Guide](docs/micropython-getting-started.md)** — full step-by-step setup
- **[File Reference Guide](docs/file-reference-guide.md)** — every file explained
- **[Hardware & OpenCat Reference](docs/hardware-and-opencat-reference.md)** — pinout, angle conversion, restoring firmware

---

**Last Updated:** 2026-03-03
