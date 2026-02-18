# Bittle MicroPython Project

Run Python directly on your Petoi Bittle X V2 robot using MicroPython on the BiBoard ESP32.

## What is This?

This project replaces the stock OpenCat firmware with MicroPython, allowing you to:
- Write and run Python code **directly on the robot**
- Create custom gaits and behaviors from scratch
- Learn robotics, inverse kinematics, and control systems
- Achieve true wireless autonomous operation
- Port and modify OpenCat algorithms in Python

**No external computer or Raspberry Pi required for autonomous operation!**

---

## Quick Start

### 1. Flash MicroPython (15 minutes)

```bash
# Download MicroPython firmware (latest stable version)
curl -O https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin

# IMPORTANT: Backup your original firmware first!
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 read-flash 0x0 0x400000 biboard_backup.bin

# Erase and flash MicroPython
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin

# Connect and test
screen /dev/cu.usbmodem5AA90272331 115200
>>> print("Python on Bittle!")
```

### 2. Upload Code and Test Servo (10 minutes)

```bash
# Install upload tool
pip install mpremote

# Upload servo driver
mpremote fs cp drivers/servo.py :servo.py

# Test servos
mpremote run poses/test_servo.py
```

### 3. Identify Servo Mapping (10 minutes)

```bash
mpremote fs cp poses/identify_servos.py :identify_servos.py
mpremote repl

>>> from identify_servos import *
>>> test(0)    # Watch which joint moves
>>> test(1)    # Test each channel 0-8
# Write down which channel controls which joint
```

### 4. Calibrate Servos (30 minutes)

```bash
mpremote fs cp poses/calibrate.py :calibrate.py
mpremote repl

>>> from calibrate import *
>>> move(0, 90)    # Adjust servo 0
>>> save(0, 87)    # Save when neutral
>>> done()         # Generate config.py
```

Copy the output to `config.py` and upload:
```bash
mpremote fs cp config.py :config.py
```

### 5. Make Bittle Stand! (5 minutes)

```bash
mpremote run poses/stand.py
# Bittle will stand up!
```

**See `MICROPYTHON_GETTING_STARTED.md` for detailed step-by-step guide.**

---

## Project Structure

```
doggo/
├── drivers/
│   └── servo.py                # Direct PWM servo driver
│
├── kinematics/
│   └── (TODO: inverse kinematics)
│
├── gaits/
│   └── (TODO: walking gaits)
│
├── poses/
│   ├── calibrate.py            # Servo calibration helper
│   ├── identify_servos.py      # Identify channel-to-joint mapping
│   ├── stand.py                # Basic poses (stand, sit, rest)
│   └── test_servo.py           # Test servo control
│
├── docs/
│   ├── micropython_detailed_plan.md    # Full technical analysis
│   └── micropython_option.md           # Pros/cons discussion
│
├── config.py                   # Configuration (auto-generated)
│
├── MICROPYTHON_GETTING_STARTED.md      # Complete setup guide
├── RESTORE_ORIGINAL_FIRMWARE.md        # How to restore OpenCat
└── README.md                           # This file
```

---

## Prerequisites

### Hardware
- Petoi Bittle X V2 with BiBoard V1.0
- USB Type-C cable
- Fully charged battery

### Software
```bash
# Install esptool for flashing
pip install esptool

# Install mpremote for file upload
pip install mpremote

# macOS/Linux: screen (usually pre-installed)
# Windows: Download PuTTY
```

---

## Development Workflow

### Upload and Run Scripts

```bash
# Run a script
mpremote run test_servo.py

# Upload a file
mpremote fs cp myfile.py :myfile.py

# Interactive REPL
mpremote repl

# List files on BiBoard
mpremote fs ls
```

### Using Thonny IDE (Recommended for Beginners)

1. Download Thonny: https://thonny.org/
2. Tools → Options → Interpreter
3. Select: MicroPython (ESP32)
4. Port: /dev/cu.usbmodem5AA90272331
5. Write code and click Run!

### Direct REPL (Advanced)

```bash
screen /dev/cu.usbmodem5AA90272331 115200
>>> # Type Python directly
>>> from machine import Pin
>>> Pin(2, Pin.OUT).on()
```

Exit: `Ctrl+A` then `K` then `Y`

---

## Development Roadmap

### ✅ Phase 1: Basic Control (Complete)
- [x] Flash MicroPython
- [x] Servo control via direct PWM
- [x] Calibration helper
- [x] Basic poses (stand, sit, rest)

### 🔄 Phase 2: Kinematics (In Progress)
- [ ] Port inverse kinematics from OpenCat
- [ ] Create Leg class
- [ ] Test IK with foot positions

### 📋 Phase 3: Gaits (Next)
- [ ] Simple sequential walk
- [ ] Trot gait (diagonal pairs)
- [ ] Crawl gait
- [ ] Balance improvements

### 🚀 Phase 4: Advanced Features (Future)
- [ ] IMU integration (gyro/accelerometer)
- [ ] WiFi control interface
- [ ] Autonomous behaviors
- [ ] Computer vision (ESP32-CAM)
- [ ] Sensor fusion

---

## Porting OpenCat to Python

OpenCat algorithms (gaits, inverse kinematics) are pure math and can be ported to Python:

### Study OpenCat Source
```bash
git clone https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot.git
cd OpenCatEsp32-Quadruped-Robot

# Key files:
# - src/motion.h         → Gait algorithms
# - src/skill.h          → Skill sequences
# - InstinctX.h          → Skills data
```

### Translation Process
1. **Find algorithm** in C++ code
2. **Understand the math** (language-agnostic)
3. **Translate to Python** (same logic, Python syntax)
4. **Test and tune** with hardware

**Example:** See inverse kinematics example in `docs/micropython_detailed_plan.md`

---

## Restoring Original Firmware

Want to go back to OpenCat? Easy!

### If You Made a Backup
```bash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 biboard_backup.bin
```

### Download Fresh Firmware
Use Petoi Desktop App → Firmware Uploader

**See `RESTORE_ORIGINAL_FIRMWARE.md` for complete guide.**

### Flashing Compiled Firmware from Arduino IDE
If you compiled OpenCat from source and have multiple `.bin` files (`.ino.bin`, `.ino.bootloader.bin`, `.ino.partitions.bin`):

**See `FLASHING_ARDUINO_BINS.md` for step-by-step instructions.**

---

## Hardware Reference

### BiBoard V1 Servo Pins (Direct PWM)

BiBoard V1 controls servos directly via ESP32 GPIO pins (no external chip):

| Channel | GPIO | Channel | GPIO |
|---------|------|---------|------|
| 0 | 18 | 6 | 12 |
| 1 | 5 | 7 | 33 |
| 2 | 14 | 8 | 19 |
| 3 | 27 | 9 | 15 |
| 4 | 23 | 10 | 13 |
| 5 | 4 | 11 | 32 |

### I2C (for IMU)
- **SDA:** GPIO 21
- **SCL:** GPIO 22
- **0x69:** ICM20600 IMU (gyro/accelerometer)

### Servo Mapping (Bittle)
```python
JOINTS = {
    0:  'head_pan',
    4:  'front_left_shoulder',
    5:  'front_right_shoulder',
    6:  'rear_right_shoulder',
    7:  'rear_left_shoulder',
    8:  'front_left_leg',
    9:  'front_right_leg',
    10: 'rear_right_leg',
    11: 'rear_left_leg',
}
# Note: Channels 1, 2, 3 are unused
```

---

## Tips and Best Practices

### Servo Angles
- Range: 0-180°
- Neutral: ~90° (varies per servo)
- Some servos may be reversed
- Always calibrate first!

### Safety
- Start with small movements
- Test one servo at a time
- Keep battery charged
- Have emergency stop ready (unplug battery)

### Memory Management
- ESP32 has ~520KB RAM
- MicroPython uses ~200-300KB
- Keep algorithms simple
- Use generators over lists
- Delete unused imports

---

## Troubleshooting

### Servo doesn't move
- Battery connected and charged?
- Correct channel number (0-8 for Bittle)?
- Try running `poses/test_servo.py`
- Check servo is plugged into right connector

### Can't upload files
```bash
# Reset and try again
mpremote soft-reset
mpremote fs ls
```

### Out of memory
- Simplify code
- Use generators
- Delete unused variables
- Import only what you need

### Need more help?
See `MICROPYTHON_GETTING_STARTED.md` for detailed troubleshooting.

---

## Resources

### Documentation
- [Getting Started Guide](MICROPYTHON_GETTING_STARTED.md) - Complete setup
- [Firmware Restoration](RESTORE_ORIGINAL_FIRMWARE.md) - Restore OpenCat
- [Technical Deep Dive](docs/micropython_detailed_plan.md) - Full analysis
- [Pico 2 W vs ESP32 Comparison](docs/pico_2_w_vs_esp32_comparison.md) - Platform comparison
- [MicroPython Docs](https://docs.micropython.org/en/latest/esp32/) - Official reference

### Source Code
- [OpenCat ESP32](https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot) - Original firmware
- [MicroPython](https://github.com/micropython/micropython) - MicroPython project

### Community
- [Petoi Forum](https://www.petoi.camp/forum) - Bittle community
- [MicroPython Forum](https://forum.micropython.org/) - MicroPython help
- This repository - Issues and PRs welcome!

---

## Why MicroPython?

### ✅ Advantages
- Python runs directly on robot (no external computer)
- True wireless autonomous operation
- Learn robotics from the ground up
- Full control over all behavior
- Lightweight (no Raspberry Pi needed)
- Educational and fun!

### ⚠️ Limitations
- Must reimplement gaits (OpenCat gaits gone)
- Limited RAM (~520KB) vs Raspberry Pi
- No full OpenCV (use lightweight alternatives)
- Steeper learning curve
- No official Petoi support

### 💡 Perfect If You Want To:
- Learn robotics algorithms
- Implement custom behaviors
- Understand how quadrupeds work
- Have full control
- Educational project
- Minimize hardware/cost/weight

---

## Contributing

Contributions welcome! Ideas:
- Port OpenCat gaits to Python
- Implement inverse kinematics
- Add IMU balance control
- Create new gaits
- Improve documentation
- Share your projects

---

## License

This project uses MicroPython (MIT License) and builds on concepts from Petoi's OpenCat (Apache 2.0). Check respective licenses for details.

---

**You're building a quadruped robot with Python!** 🤖🐍

Happy hacking!

**Last Updated:** 2026-02-11
