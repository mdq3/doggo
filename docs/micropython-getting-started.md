# MicroPython on BiBoard - Getting Started Guide

Step-by-step guide to flash MicroPython and control your first servo.

## What You'll Accomplish

- [x] Flash MicroPython firmware to BiBoard
- [x] Connect to MicroPython REPL
- [x] Identify hardware pins
- [x] Control your first servo
- [x] Make Bittle stand up!

**Time estimate:** 1-2 hours

---

## Prerequisites

### Software
```bash
# Install esptool (for flashing firmware)
pip install esptool

# Install mpremote (for REPL and file transfers)
pip install mpremote
```

### Hardware
- Bittle X V2 with BiBoard V1.0
- USB Type-C cable
- Fully charged battery (important!)

---

## Step 1: Backup Current Firmware (IMPORTANT!)

Before erasing, let's backup your OpenCat firmware so you can restore if needed.

### Read Current Firmware

```bash
# Find your port
ls /dev/cu.usbmodem5AA90272331  # macOS
ls /dev/ttyUSB0           # Linux
# Windows: Check Device Manager for COM port

# Backup firmware (4MB)
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 biboard_backup.bin

# This takes ~2 minutes
# Save biboard_backup.bin somewhere safe!
```

**Keep this file!** You can restore OpenCat later if needed.

---

## Step 2: Download MicroPython Firmware

```bash
# Download latest ESP32 MicroPython firmware
# Visit: https://micropython.org/download/esp32/

# Or use direct link (latest stable as of Feb 2026):
wget https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin

# Or curl:
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin
```

**File:** `ESP32_GENERIC-20251209-v1.27.0.bin` (MicroPython v1.27.0, December 2025)

---

## Step 3: Flash MicroPython

### Erase Flash

```bash
# IMPORTANT: Remove battery before flashing (USB power only)
# Connect USB cable to BiBoard

# Erase existing firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# Wait for: "Hard resetting via RTS pin..."
# Takes ~10 seconds
```

### Flash MicroPython

```bash
# Flash MicroPython firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
--baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin

# Wait for completion (~30 seconds)
# You should see: "Hard resetting via RTS pin..."
```

**Success!** MicroPython is now installed.

**Note:** Keep the battery disconnected for now. You only need USB power for REPL testing. Reconnect the battery in Step 6 when you're ready to test servos.

---

## Step 4: Connect to REPL

REPL = Read-Eval-Print Loop (Python interactive shell)

```bash
mpremote repl
# Press ENTER if prompt doesn't appear
# Exit: Ctrl+]
```

### First Test

```python
>>> print("Hello from MicroPython!")
Hello from MicroPython!

>>> import sys
>>> sys.platform
'esp32'

>>> import machine
>>> machine.freq()
160000000  # 160MHz (default, can be set up to 240MHz)

# Success! MicroPython is working!
```

---

## Step 5: Understand BiBoard Hardware

BiBoard V1 controls servos **directly via ESP32 PWM** - there is no external servo controller chip.

### Servo Pin Mapping

BiBoard V1 has 12 servo channels connected directly to ESP32 GPIO pins:

| Channel | GPIO | Channel | GPIO |
|---------|------|---------|------|
| 0 | 18 | 6 | 12 |
| 1 | 5 | 7 | 33 |
| 2 | 14 | 8 | 19 |
| 3 | 27 | 9 | 15 |
| 4 | 23 | 10 | 13 |
| 5 | 4 | 11 | 32 |

### I2C Devices (Optional)

The I2C bus (GPIO 21/22) connects to the IMU only:

```python
>>> from machine import Pin, I2C
>>> i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
>>> print("I2C devices:", [hex(d) for d in i2c.scan()])
# Expected: [0x69] - ICM20600 IMU (gyro/accelerometer)
```

---

## Step 6: Upload Servo Driver

**IMPORTANT: Reconnect the battery now!** Servos require more power than USB can provide. The battery must be connected and charged for servos to move.

The repository includes a direct PWM servo driver at `src/drivers/servo.py`.

### Install mpremote

```bash
pip install mpremote
```

### Upload the Driver

```bash
# Upload the servo driver from the repo
mpremote fs cp src/drivers/servo.py :servo.py

# Verify it uploaded
mpremote fs ls
# You should see: servo.py
```

**How it works:**
- Uses ESP32's built-in PWM (LEDC) peripheral
- Controls servos directly on GPIO pins (no external chip)
- 50Hz PWM signal with 500-2500μs pulse width
- Supports all 12 BiBoard servo channels

### Verify Servos Are Working

The repository includes `src/configuration/verify_servos_working.py` for testing.

```bash
# Run the test script directly from your computer
mpremote run src/configuration/verify_servos_working.py
```

The script will:
1. Initialize the PWM servo driver
2. Move servo on channel 0 through different positions
3. Test all 9 Bittle servos with a quick sweep

**If servo doesn't move:**
- Check battery is connected and charged
- Verify servo is plugged into correct channel
- Try a different channel

**To test manually:**
```python
>>> from servo import Servos
>>> servos = Servos()
>>> servos.set_servo(0, 90)  # Move servo 0 to center
>>> servos.set_servo(0, 45)  # Move to 45 degrees
>>> servos.set_servo(0, 135) # Move to 135 degrees
```

---

## Step 7: Identify Servo Mapping

Before calibrating, you need to identify which channel controls which joint. The GPIO-to-servo wiring may vary.

### Upload Identification Script

```bash
mpremote fs cp src/configuration/identify_servos.py :identify_servos.py
mpremote repl
```

### Test Each Channel

```python
>>> from identify_servos import *

Servo Identifier Ready
======================
Commands:
  test(0)  - Wiggle channel 0
  t(0)     - Same (shortcut)

>>> test(0)    # Watch which servo moves
>>> test(1)    # Next channel...
>>> test(2)
# ... test channels 0-11
```

### Record Your Mapping

Write down which joint moves for each channel:

```
Channel 0: _____________ (e.g., "head")
Channel 4: _____________ (e.g., "front left shoulder")
Channel 5: _____________
Channel 6: _____________
Channel 7: _____________
Channel 8: _____________
Channel 9: _____________
Channel 10: _____________
Channel 11: _____________
```

You'll need this mapping for calibration.

---

## Step 8: Calibration

Use the channel mapping you identified in Step 7 to calibrate each servo to its neutral position.

### Upload Calibration Helper

```bash
# Upload the calibration helper to BiBoard
mpremote fs cp src/configuration/calibrate.py :calibrate.py
```

### Connect to REPL

```bash
mpremote repl
```

### Calibration Process

Load the calibration helper and use simple commands:

```python
>>> from calibrate import *

==================================================
Calibration Helper Ready
==================================================

Type help() for commands

Quick start:
  >>> move(0, 90)
  >>> save(0, 90)
  >>> done()
```

**For each servo:**

```python
# 1. Move servo to starting position
>>> move(4, 90)
[4] Front Left Shoulder -> 90°

# 2. Adjust until the joint is in neutral position
>>> move(4, 85)
>>> move(4, 87)

# 3. Save when it looks right
>>> save(4, 87)
Saved: [4] Front Left Shoulder = 87° (offset: -3°)

# 4. Move to next servo
>>> move(5, 90)
# ... repeat for all channels ...
```

**Shortcut commands:** `m(4, 90)` and `s(4, 90)` work the same as `move()` and `save()`.

### Generate config.py

When all servos are calibrated:

```python
>>> done()

==================================================
Copy everything below into config.py:
==================================================

"""
Bittle Calibration Config
"""

CALIBRATION = {
     0:  +0,  # Head Pan
     4: +37,  # Front Left Shoulder
    ...
}

def apply_calibration(angle, channel):
    return angle + CALIBRATION.get(channel, 0)

==================================================
```

### Save to BiBoard

1. Copy the config content from the terminal
2. Save to `config.py` at the repo root (`config.py` is gitignored — it's specific to your robot)
3. Upload to BiBoard:

```bash
mpremote fs cp config.py :config.py
```

### Joint Reference

| Channel | Joint |
|---------|-------|
| 0 | Head Pan |
| 4 | Front Left Shoulder |
| 5 | Front Right Shoulder |
| 6 | Rear Right Shoulder |
| 7 | Rear Left Shoulder |
| 8 | Front Left Leg |
| 9 | Front Right Leg |
| 10 | Rear Right Leg |
| 11 | Rear Left Leg |

**Note:** Channels 1, 2, 3 are unused on Bittle.

**Goal:** Find the angle where each joint is in "neutral" position (legs straight down, head centered).

---

## Step 9: Make Bittle Stand

Now that you've calibrated the servos, let's make Bittle stand!

The demo script is at `src/demos/stand.py`. It imports pose functions from `src/poses.py`.

### Upload Pose Library and Run Demo

```bash
mpremote fs cp src/poses.py :poses.py
mpremote run src/demos/stand.py
```

### What It Does

The script will automatically:
1. Load your calibration data from `config.py` (if available)
2. Stand up
3. Sit down
4. Stand again
5. Rest (lie flat)

**Expected output:**
```
============================================================
Bittle Stand Demo
============================================================
✓ Loaded calibration data
Initializing hardware...
✓ Hardware ready

Standing up...
✓ Standing position

Sitting down...
✓ Sitting position

Lying down...
✓ Resting position

✓ Demo complete!
============================================================
```

### Servo Mapping Reference

**Bittle X V2 has 9 DOF (Degrees of Freedom):**

| Channel | Joint |
|---------|-------|
| 0 | Head Pan |
| 4 | Front Left Shoulder |
| 5 | Front Right Shoulder |
| 6 | Rear Right Shoulder |
| 7 | Rear Left Shoulder |
| 8 | Front Left Leg |
| 9 | Front Right Leg |
| 10 | Rear Right Leg |
| 11 | Rear Left Leg |

**Note:** Channels 1, 2, 3 are unused on Bittle.

### Customizing Poses

The pose functions live in `src/poses.py`. To adjust angles for your Bittle:

1. Edit `src/poses.py` on your computer
2. Modify the angle values in `stand()`, `sit()`, or `rest()`
3. Re-upload and run:

```bash
mpremote fs cp src/poses.py :poses.py
mpremote run src/demos/stand.py
```

**Example adjustment:**
```python
def stand():
    move_to({
        CH_FL_LEG: 65,   # was 60 — tune this per robot
        CH_FR_LEG: 115,  # was 120
        # ... etc
    }, speed=2)
```

Angles are *commanded* values (before calibration). `move_to` applies `apply_calibration` internally.

---

## Development Workflow

### Option 1: REPL (Quick Testing)

```bash
mpremote repl
# Exit: Ctrl+]

>>> servos.set_servo(0, 45)
```

### Option 2: mpremote (File Upload)

```bash
# Install mpremote
pip install mpremote

# Upload a file
mpremote fs cp src/poses.py :poses.py

# Run a script directly from host
mpremote run src/demos/stand.py
```

### Option 3: WebREPL (Wireless!)

```python
# On BiBoard REPL:
>>> import webrepl_setup

# Follow prompts:
# - Enable WebREPL: yes
# - Set password: yourpassword
# - Restart

# On computer, open browser:
# http://micropython.org/webrepl/

# Connect to ws://192.168.4.1:8266 (if AP mode)
# Or ws://<bittle-ip>:8266 (if connected to WiFi)
```

### Option 4: Thonny IDE (Easiest!)

1. Download Thonny: https://thonny.org/
2. Run Thonny
3. Tools → Options → Interpreter
4. Select: MicroPython (ESP32)
5. Port: /dev/cu.usbmodem5AA90272331
6. Click OK

Now you can:
- Write code in editor
- Click "Run" to execute on BiBoard
- See output in shell
- Upload/download files

---

## Project Structure

**Current repository structure:**

```
doggo/
├── src/
│   ├── drivers/
│   │   └── servo.py                # ✅ Direct PWM servo driver (ESP32 LEDC)
│   │
│   ├── configuration/
│   │   ├── identify_servos.py      # ✅ Identify channel-to-joint mapping
│   │   └── verify_servos_working.py # ✅ Verify all servos move correctly
│   │
│   ├── demos/
│   │   └── stand.py                # ✅ Stand demo script
│   │
│   ├── calibrate.py                # ✅ Interactive REPL calibration tool
│   └── poses.py                    # ✅ Pose library (move_to, stand, sit, rest)
│
├── docs/
│   ├── file_reference_guide.md
│   ├── flashing_opencat_arduino_bins.md
│   ├── micropython_detailed_plan.md
│   ├── micropython_option.md
│   ├── pico_2_w_vs_esp32_comparison.md
│   └── restore_original_opencat_firmware.md
│
├── config.py                   # ⚙️ Gitignored — generate with calibrate.py
├── CLAUDE.md                   # Project notes for Claude Code
├── MICROPYTHON_GETTING_STARTED.md
└── README.md
```

**Files uploaded to BiBoard:**
```
BiBoard:/
├── servo.py       # from src/drivers/servo.py
├── poses.py       # from src/poses.py
└── config.py      # generated locally, gitignored
```

---

## Next Steps

### Phase 1: Basic Control (✅ Complete!)
1. ✅ Flash MicroPython
2. ✅ Upload servo driver (`src/drivers/servo.py`)
3. ✅ Verify servos (`src/configuration/verify_servos_working.py`)
4. ✅ Calibrate all servos (`src/configuration/calibrate.py`)
5. ✅ Make Bittle stand (`src/demos/stand.py`)

### Phase 2: Kinematics (In Progress)
1. ⬜ Study OpenCat IK algorithms
2. ⬜ Port inverse kinematics to Python
3. ⬜ Create `Leg` class for leg control
4. ⬜ Test foot positioning with IK
5. ⬜ Add `src/kinematics/ik.py` and `src/kinematics/leg.py`

### Phase 3: Gaits (Next)
1. ⬜ Implement simple sequential walk
2. ⬜ Add trot gait (diagonal pairs)
3. ⬜ Add crawl gait
4. ⬜ Tune gait parameters for smooth motion
5. ⬜ Create `src/gaits/walk.py`, `src/gaits/trot.py`, `src/gaits/crawl.py`

### Phase 4: Advanced (Future)
1. ⬜ IMU integration (ICM20600 gyro/accelerometer)
2. ⬜ Balance improvements using IMU feedback
3. ⬜ WiFi control interface
4. ⬜ Autonomous behaviors
5. ⬜ Computer vision (ESP32-CAM module)

---

## Troubleshooting

### "No module named 'machine'"
- MicroPython not installed correctly
- Wrong board selected
- Re-flash firmware

### "No module named 'servo'"
- servo.py not uploaded to BiBoard
- Run: `mpremote fs cp src/drivers/servo.py :servo.py`

### "No module named 'poses'"
- poses.py not uploaded to BiBoard
- Run: `mpremote fs cp src/poses.py :poses.py`

### Servo doesn't move
- Battery connected and charged?
- Correct channel number?
- Check servo is plugged into the right connector
- Try running `src/configuration/verify_servos_working.py`

### Can't connect to REPL
- Try unplugging/replugging USB
- Run `mpremote repl` and press `Ctrl+C` then `Enter` if prompt doesn't appear

---

## Resources

### MicroPython Docs
- https://docs.micropython.org/en/latest/esp32/quickref.html
- https://micropython.org/

### OpenCat Source (for porting)
- https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot

### Community
- MicroPython Forum: https://forum.micropython.org/
- Petoi Forum: https://www.petoi.camp/forum

---

## Ready to Start!

**Run this command to begin:**

```bash
# Download MicroPython (latest stable)
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin

# Flash it
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin

# Connect
mpremote repl

# Test
>>> print("Let's build a robot!")
```

**You're about to control a quadruped robot with pure Python!** 🚀

---

**Last Updated:** 2026-02-18
