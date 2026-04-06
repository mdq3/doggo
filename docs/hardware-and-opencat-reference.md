# Hardware Reference and OpenCat Porting

Technical reference for the BiBoard V1 hardware and notes on porting OpenCat algorithms to Python.

---

## Hardware Reference

### BiBoard V1 Servo Pins (Direct PWM)

BiBoard V1 controls servos directly via ESP32 GPIO pins using the LEDC peripheral — no external servo controller chip.

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

```python
# Channel constants in src/poses.py:
CH_HEAD      = 0
CH_FL_SH     = 4   # Front Left Shoulder  (rotDir +1)
CH_FR_SH     = 5   # Front Right Shoulder (rotDir -1)
CH_RR_SH     = 6   # Rear Right Shoulder  (rotDir -1)
CH_RL_SH     = 7   # Rear Left Shoulder   (rotDir +1)
CH_FL_LEG    = 8   # Front Left Leg       (rotDir -1)
CH_FR_LEG    = 9   # Front Right Leg      (rotDir +1)
CH_RR_LEG    = 10  # Rear Right Leg       (rotDir +1)
CH_RL_LEG    = 11  # Rear Left Leg        (rotDir -1)
```

### I2C (IMU)

- **SDA:** GPIO 21
- **SCL:** GPIO 22
- **Address 0x69:** ICM20600 (gyro/accelerometer)

```python
>>> from machine import Pin, I2C
>>> i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
>>> [hex(d) for d in i2c.scan()]
['0x69']
```

### Servo PWM

`src/drivers/servo.py` uses **200Hz** via ESP32 LEDC:

| Frequency | Steps (10-bit) | Resolution |
|-----------|---------------|------------|
| 50Hz | 102 | 1.76°/step (jerky) |
| 100Hz | 204 | 0.88°/step |
| **200Hz** | **409** | **0.44°/step** ← used |

Bittle's digital servos support up to ~330Hz. 200Hz gives 409 steps across the servo range with no perceptible stepping.

---

## Porting OpenCat to Python

OpenCat algorithms (gaits, inverse kinematics) are pure math and translate directly to Python.

### Study OpenCat Source

```bash
git clone https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot.git

# Key files:
# - src/motion.h         → Gait algorithms
# - src/skill.h          → Skill sequences
# - InstinctBittleESP.h  → Skills data (gait keyframes)
```

### Angle Conversion

OpenCat uses two angle systems. The conversion formula for gait keyframes from `InstinctBittleESP.h`:

```
commanded_angle = ZERO_POS[joint] + rotationDirection[joint] * opencat_raw
```

Where `ZERO_POS` accounts for `middleShift[]` in OpenCat (mechanical neutral per joint):

```python
# From OpenCat middleShift[]:
ZERO_POS = {
    CH_FL_SH:  65,   CH_FR_SH: 115,
    CH_RR_SH: 115,   CH_RL_SH:  65,
    CH_FL_LEG: 80,   CH_FR_LEG: 100,
    CH_RR_LEG: 100,  CH_RL_LEG:  80,
}
```

For named poses (`stand`, `sit`, `rest`):

```
commanded_angle = 90 + rotationDirection[joint] * opencat_angle
```

### Translation Process

1. Find the algorithm in C++ (`InstinctBittleESP.h` for keyframes, `motion.h` for gait logic)
2. Understand the math — it's language-agnostic
3. Translate to Python (same logic, Python syntax)
4. Test and tune on hardware

### What's Already Ported

| OpenCat array | Python file | Notes |
|---------------|-------------|-------|
| `wkF` | `src/gaits/walk.py` | 116-frame one-foot-at-a-time gait |

### What's Not Ported Yet

- Inverse kinematics (`kinematics/` — not implemented)
- Crawl gait
- Bound / gallop gaits
- IMU balance control

---

## Restoring Original Firmware

### If You Made a Backup

```bash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 biboard_backup.bin
```

### Download Fresh Firmware

Use the **Petoi Desktop App → Firmware Uploader** to download and flash the stock firmware without needing a backup.

### Flashing Compiled Arduino Bins

If you compiled OpenCat from source with Arduino IDE and have multiple `.bin` files (`.ino.bin`, `.ino.bootloader.bin`, `.ino.partitions.bin`):

See `docs/restore-original-opencat-firmware.md` for the complete restoration guide.

---

## Why MicroPython?

### Advantages
- Python runs directly on the robot — no external computer needed
- True wireless autonomous operation
- Full control over all behaviour
- Learn robotics algorithms from the ground up
- Lightweight — no Raspberry Pi required

### Limitations
- OpenCat behaviour library not available — gaits must be ported individually
- Limited RAM (~520KB) vs Raspberry Pi
- No full OpenCV (use lightweight alternatives)
- No official Petoi support

### Perfect If You Want To
- Learn quadruped robotics algorithms
- Implement custom behaviours
- Have full control over the robot
- Minimise hardware cost and weight

---

**Last Updated:** 2026-02-28
