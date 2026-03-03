# MicroPython on BiBoard - Getting Started Guide

Step-by-step guide to flash MicroPython and get your Bittle walking.

## What You'll Accomplish

1. Flash MicroPython firmware to BiBoard
2. Connect to MicroPython REPL
3. Upload the servo driver and verify all servos move
4. Identify which channel controls which joint
5. Calibrate servos to their neutral positions
6. Make Bittle stand up
7. Make Bittle walk

**Time estimate:** 1-2 hours

---

## Prerequisites

### Hardware
- Bittle X V2 with BiBoard V1.0
- USB Type-C cable
- Fully charged battery (required for servo steps)

### Software
```bash
# Install esptool (for flashing firmware)
pip install esptool

# Install mpremote (for REPL and file transfers)
pip install mpremote
```

---

## Step 1: Backup Current Firmware (IMPORTANT!)

Before erasing, back up your OpenCat firmware so you can restore it if needed.

```bash
# Find your port
ls /dev/cu.usbmodem*   # macOS — look for the BiBoard device
ls /dev/ttyUSB*        # Linux
# Windows: check Device Manager for the COM port

# Backup firmware (4MB, takes ~2 minutes)
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 biboard_backup.bin
```

**Keep `biboard_backup.bin` somewhere safe!** See `docs/restore-original-opencat-firmware.md` if you ever want to go back.

---

## Step 2: Download MicroPython Firmware

```bash
# Download latest stable ESP32 MicroPython firmware
# Check https://micropython.org/download/esp32/ for the latest version

# Direct link (v1.27.0, December 2025):
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin
```

---

## Step 3: Flash MicroPython

**Remove the battery before flashing — use USB power only.**

```bash
# Erase existing firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# Flash MicroPython (~30 seconds)
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin
```

Both commands should end with: `Hard resetting via RTS pin...`

---

## Step 4: Connect to REPL

REPL = Read-Eval-Print Loop (interactive Python shell on the device).

```bash
mpremote repl
# Press Enter if the prompt doesn't appear immediately
# Exit: Ctrl+]
```

### Verify MicroPython is working

```python
>>> print("Hello from MicroPython!")
Hello from MicroPython!

>>> import sys
>>> sys.platform
'esp32'
```

**Keep the battery disconnected for now.** Reconnect it in Step 6 when you're ready to test servos.

---

## Step 5: BiBoard Hardware Reference

BiBoard V1 controls servos **directly via ESP32 PWM (LEDC)** — there is no external servo controller chip.

### Servo channel mapping

| Channel | GPIO | Joint (Bittle) |
|---------|------|----------------|
| 0 | 18 | Head Pan |
| 1 | 5 | — unused — |
| 2 | 14 | — unused — |
| 3 | 27 | — unused — |
| 4 | 23 | Front Left Shoulder |
| 5 | 4 | Front Right Shoulder |
| 6 | 12 | Rear Right Shoulder |
| 7 | 33 | Rear Left Shoulder |
| 8 | 19 | Front Left Leg |
| 9 | 15 | Front Right Leg |
| 10 | 13 | Rear Right Leg |
| 11 | 32 | Rear Left Leg |

### I2C (IMU — optional)

```python
>>> from machine import Pin, I2C
>>> i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
>>> print([hex(d) for d in i2c.scan()])
# Expected: ['0x69']  — ICM20600 gyro/accelerometer
```

---

## Step 6: Upload Servo Driver and Verify Servos

**Reconnect the battery now.** Servos need more power than USB alone can provide.

### Upload the driver

```bash
mpremote fs cp src/drivers/servo.py :servo.py

# Verify upload
mpremote fs ls
# → servo.py
```

The driver (`src/drivers/servo.py`) uses 200Hz PWM via the ESP32 LEDC peripheral, giving 0.44°/step resolution across the servo range. It supports all 12 BiBoard channels.

### Verify all servos move

```bash
mpremote run src/configuration/verify_servos_working.py
```

The script moves channel 0 through a sweep, then briefly tests all 9 Bittle channels. Expected output ends with:

```
SUCCESS! All servos working!
```

**If a servo doesn't move:**
- Is the battery connected and charged?
- Is the servo plugged into the right connector?
- Try a different channel to rule out a bad servo

### Manual test

```python
>>> from servo import Servos
>>> s = Servos()
>>> s.set_servo(0, 90)   # center
>>> s.set_servo(0, 45)   # left
>>> s.set_servo(0, 135)  # right
```

---

## Step 7: Identify Servo Mapping

Before calibrating, wiggle each channel to map channel numbers to physical joints.

### Upload and run

```bash
mpremote fs cp src/configuration/identify_servos.py :identify_servos.py
mpremote repl
```

```python
>>> from identify_servos import *
>>> test(0)    # watch which joint moves
>>> test(4)
>>> test(5)
# ... test channels 0-11
```

### Record your mapping

```
Channel 0:  _____________ (e.g. "head")
Channel 4:  _____________ (e.g. "front left shoulder")
Channel 5:  _____________
Channel 6:  _____________
Channel 7:  _____________
Channel 8:  _____________
Channel 9:  _____________
Channel 10: _____________
Channel 11: _____________
```

The expected mapping for Bittle X V2 is shown in the table in Step 5.

---

## Step 8: Calibrate Servos

Find each servo's neutral angle (the position where the joint is mechanically centered).

### Upload calibration tool

```bash
mpremote fs cp src/configuration/calibrate.py :calibrate.py
mpremote repl
```

### Calibrate each channel

```python
>>> from calibrate import *

# Move servo to a starting position, adjust until neutral, save
>>> move(4, 90)     # start at 90°
>>> move(4, 87)     # adjust until front-left shoulder is centered
>>> save(4, 87)     # save — offset recorded as -3°

# Repeat for each channel (0, 4-11)
>>> move(5, 90)
>>> move(5, 93)
>>> save(5, 93)
# ... and so on
```

Shortcuts: `m()` and `s()` work the same as `move()` and `save()`.

### Generate config.py

When all channels are done:

```python
>>> done()
# Prints the full config.py content — copy it
```

1. Paste the output into `config.py` at the repo root
2. Upload to the device:

```bash
mpremote fs cp config.py :config.py
```

`config.py` is gitignored — it's specific to your robot.

---

## Step 9: Make Bittle Stand

Upload the pose library and run the stand demo.

**Device must have:** `servo.py`, `config.py` (uploaded in previous steps), and `poses.py` (uploaded now).

```bash
mpremote fs cp src/poses.py :poses.py
mpremote run src/demos/stand.py
```

Or upload everything at once:

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    run src/demos/stand.py
```

### What it does

stand → sit → stand → rest

**Expected output:**
```
✓ Loaded calibration data
Initializing hardware...
✓ Hardware ready

Standing up...
✓ Standing position

Sitting down...
✓ Sitting position
...
✓ Demo complete!
```

### Tuning

If the poses look wrong, edit angle values in `src/poses.py` and re-upload:

```bash
mpremote fs cp src/poses.py :poses.py
mpremote run src/demos/stand.py
```

Angles in `poses.py` are *commanded* values (before calibration). `move_to()` applies your `config.py` offsets automatically.

---

## Step 10: Make Bittle Walk

**Device must have:** `servo.py`, `poses.py`, `config.py` (from previous steps), plus `gaits/walk.py` (uploaded now).

```bash
mpremote fs mkdir :gaits
mpremote fs cp src/gaits/walk.py :gaits/walk.py
mpremote run src/demos/walk.py
```

Or upload everything at once from scratch:

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    run src/demos/walk.py
```

Note: `fs mkdir :gaits` will error if the directory already exists — safe to ignore on re-deploy.

### What it does

stand → walk (5 cycles, one foot at a time) → rest

---

## Step 11: Enable WiFi Control

Remove the USB tether. After this step you can run scripts and send commands wirelessly.

### 11a: Create your WiFi credentials file

```bash
cp src/configuration/wifi_config_template.py wifi_config.py
# edit wifi_config.py — fill in SSID, PASSWORD, WEBREPL_PASSWORD
```

`wifi_config.py` is gitignored. Never commit it.

### 11b: Upload WiFi files (USB, one-time)

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

Note: `fs mkdir :gaits` errors if the directory already exists — safe to ignore.

### 11c: Reboot and find the IP address

```bash
mpremote reset
# Serial output shows:
# WiFi connected: 192.168.1.x
# HTTP server on port 80
```

Or open a REPL to see the output:

```bash
mpremote repl
# press Ctrl+D for soft reset
```

### 11d: Send HTTP commands

```bash
curl http://192.168.1.x/stand
curl http://192.168.1.x/sit
curl http://192.168.1.x/rest
curl http://192.168.1.x/walk?steps=3
curl http://192.168.1.x/walk_back?steps=3
curl http://192.168.1.x/battery
```

### 11e: Run scripts and transfer files over WiFi

mpremote does not support WebREPL natively. Use `src/webrepl_proxy.py` — it connects to WebREPL, then runs `mpremote` for you, so the whole thing is a single command:

```bash
python src/webrepl_proxy.py 192.168.1.x doggo repl
python src/webrepl_proxy.py 192.168.1.x doggo run src/demos/walk.py
python src/webrepl_proxy.py 192.168.1.x doggo fs cp src/poses.py :poses.py
python src/webrepl_proxy.py 192.168.1.x doggo fs ls
```

The proxy exits when mpremote exits. For repeated use, a shell alias helps:

```bash
alias dog='python src/webrepl_proxy.py 192.168.1.x doggo'

dog repl
dog run src/demos/walk.py
dog fs cp src/poses.py :poses.py
```

For a persistent proxy (stays alive between mpremote invocations), omit the subcommand — the proxy prints the PTY path and loops:

```bash
# Terminal 1:
python src/webrepl_proxy.py 192.168.1.x doggo
# prints: PTY ready: /dev/ttys003

# Terminal 2:
mpremote connect /dev/ttys003 repl
mpremote connect /dev/ttys003 run src/demos/walk.py
```

### 11f: Deploy code updates over WiFi

After uploading new source files, use `/restart` to reload them without a hardware reset. Servo PWM keeps running throughout — the dog does not move.

```bash
# Upload a changed file
dog fs cp src/poses.py :poses.py
dog fs cp src/server.py :server.py

# Reload immediately — no power cycle, no servo movement
curl http://192.168.1.x/restart
```

`/restart` reloads these modules from flash:
- `server.py`
- `poses.py`
- `battery.py`
- `gaits/walk.py`

The following files require a **physical power cycle** because they run before the server starts:
- `servo.py`
- `boot.py`
- `main.py`

### Disconnect USB

Once verified, unplug the cable. `curl` and `webrepl_proxy.py` + mpremote both work over WiFi alone.

---

## Device Filesystem Reference

### Minimum for stand demo

```
BiBoard:/
├── servo.py       # src/drivers/servo.py
├── poses.py       # src/poses.py
└── config.py      # generated locally, gitignored
```

### For walk

```
BiBoard:/
├── servo.py
├── poses.py
├── config.py
└── gaits/
    └── walk.py    # src/gaits/walk.py
```

### With WiFi control

```
BiBoard:/
├── boot.py        # src/boot.py — WiFi connect + WebREPL
├── main.py        # src/main.py — HTTP server loop
├── server.py      # src/server.py — command routes
├── battery.py     # src/battery.py — voltage monitoring
├── servo.py       # src/drivers/servo.py — PWM driver
├── poses.py       # src/poses.py — pose library
├── config.py      # generated locally, gitignored
├── wifi_config.py # gitignored, credentials
└── gaits/
    └── walk.py    # src/gaits/walk.py — walk gait
```

---

## Development Workflow

### Run a script from host

```bash
mpremote run src/demos/stand.py
```

### Upload a file

```bash
mpremote fs cp src/poses.py :poses.py
```

### Interactive REPL

```bash
mpremote repl
# Exit: Ctrl+]
```

### List files on device

```bash
mpremote fs ls
mpremote fs ls :gaits
```

### Thonny IDE (alternative)

1. Download: https://thonny.org/
2. Tools → Options → Interpreter → MicroPython (ESP32)
3. Port: your BiBoard port
4. Write code in editor, click Run

---

## Project Structure

```
doggo/
├── src/
│   ├── drivers/
│   │   └── servo.py                # Direct PWM servo driver (ESP32 LEDC, 200Hz)
│   ├── configuration/
│   │   ├── calibrate.py            # Interactive REPL calibration tool
│   │   ├── identify_servos.py      # Identify channel-to-joint mapping
│   │   ├── verify_servos_working.py # Verify all servos move correctly
│   │   └── wifi_config_template.py # Copy → wifi_config.py, fill in credentials
│   ├── gaits/
│   │   └── walk.py                 # Walk gait (one foot at a time, 116 frames)
│   ├── demos/
│   │   ├── stand.py                # Stand demo: stand → sit → stand → rest
│   │   └── walk.py                 # Walk demo: stand → walk → rest
│   ├── boot.py                     # WiFi connect + WebREPL start (deployed as :boot.py)
│   ├── main.py                     # HTTP server start (deployed as :main.py)
│   ├── server.py                   # HTTP command server (_thread, port 80)
│   ├── webrepl_proxy.py            # Host-side PTY bridge for mpremote over WiFi
│   └── poses.py                    # Pose library (move_to, stand, sit, rest)
├── docs/
│   ├── micropython-getting-started.md   # This file
│   ├── file-reference-guide.md
│   ├── micropython-detailed-plan.md
│   └── restore-original-opencat-firmware.md
├── config.py                       # Calibration offsets (gitignored — generate locally)
├── CLAUDE.md                       # Architecture notes for Claude Code
└── README.md
```

---

## Next Steps

### ✅ Phase 1: Basic Control (Complete)
- Flash MicroPython
- Servo driver (200Hz PWM, direct LEDC)
- Calibration
- Stand, sit, rest poses

### ✅ Phase 2: Gaits (Complete)
- Walk gait — one foot at a time, 116 frames from OpenCat `wkF`
- Trot gait — diagonal pairs, 48 frames from OpenCat `trF`

### ✅ Phase 3: WiFi Control (Complete)
- WebREPL — wireless REPL + file transfer via `src/webrepl_proxy.py` PTY bridge
- HTTP command server — `curl /stand`, `/walk?steps=N`, etc.
- `src/boot.py` + `src/main.py` + `src/server.py`

### 📋 Phase 4: Advanced Motion (Next)
- Inverse kinematics
- Crawl gait
- IMU-assisted balance (ICM20600 at I2C 0x69)

### 🚀 Phase 5: Autonomy (Future)
- Autonomous behaviours
- Computer vision (ESP32-CAM)

---

## Troubleshooting

### `No module named 'servo'`
`servo.py` not uploaded — run `mpremote fs cp src/drivers/servo.py :servo.py`

### `No module named 'poses'`
`poses.py` not uploaded — run `mpremote fs cp src/poses.py :poses.py`

### `No module named 'gaits.walk'`
`gaits/walk.py` not uploaded:
```bash
mpremote fs mkdir :gaits
mpremote fs cp src/gaits/walk.py :gaits/walk.py
```

### Servo doesn't move
- Battery connected and charged?
- Correct channel number?
- Run `mpremote run src/configuration/verify_servos_working.py`

### Can't connect to REPL
- Unplug/replug USB
- Run `mpremote repl`, press `Ctrl+C` then `Enter` if prompt doesn't appear

### `⚠ No calibration data found`
`config.py` not uploaded — run `mpremote fs cp config.py :config.py`

---

## Resources

- [MicroPython ESP32 docs](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [OpenCat ESP32 source](https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot)
- [Petoi Forum](https://www.petoi.camp/forum)
- [MicroPython Forum](https://forum.micropython.org/)

---

**Last Updated:** 2026-03-03
