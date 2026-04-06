# Hardware Setup and Calibration

Detailed guide for the one-time hardware setup steps. The README covers the overall workflow — this document goes deeper on the parts that need it: flashing, servo verification, channel identification, and calibration.

---

## Finding your USB port

```bash
ls /dev/cu.usbmodem*   # macOS
ls /dev/ttyUSB*        # Linux
# Windows: Device Manager → COM ports
```

---

## Flashing MicroPython

**Remove the battery before flashing — use USB power only.**

```bash
# Back up existing firmware first (4MB, ~2 minutes)
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 biboard_backup.bin

# Erase and flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin
```

Both commands should end with `Hard resetting via RTS pin...`

To restore the original OpenCat firmware, see `docs/hardware-and-opencat-reference.md`.

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

---

## BiBoard V1 hardware reference

BiBoard V1 drives servos directly via ESP32 PWM (LEDC) — no external servo controller.

### Servo channel mapping

| Channel | GPIO | Joint |
|---------|------|-------|
| 0 | 18 | Head pan |
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

### IMU (ICM-42670-P)

The IMU is labelled ICM-20600 in Petoi docs but the actual chip is ICM-42670-P (WHO_AM_I = 0x67). It has a different register map — the driver in `src/imu.py` accounts for this.

```python
>>> from machine import Pin, I2C
>>> i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
>>> [hex(d) for d in i2c.scan()]
['0x69']
```

---

## Verifying servos

**Reconnect the battery.** Servos need more power than USB alone provides.

Upload the driver and run the verification script:

```bash
mpremote fs mkdir :drivers
mpremote fs cp src/drivers/servo.py :drivers/servo.py
mpremote run src/configuration/verify_servos_working.py
```

Expected output ends with `SUCCESS! All servos working!`

If a servo doesn't move: check battery charge, check the connector is seated, try a neighbouring channel to rule out a dead servo.

Manual test from the REPL:

```python
>>> from drivers.servo import Servos
>>> s = Servos()
>>> s.set_servo(4, 90)   # front-left shoulder to center
>>> s.set_servo(4, 60)
>>> s.set_servo(4, 120)
```

---

## Identifying servo channels

Wiggle each channel to confirm which channel controls which joint — useful if you're unsure about the mapping or have a non-standard assembly.

```bash
mpremote fs cp src/configuration/identify_servos.py :identify_servos.py
mpremote repl
```

```python
>>> from identify_servos import *
>>> test(4)    # watch which joint moves
>>> test(5)
# ... repeat for channels 0, 4-11
```

---

## Calibration

Each robot has slightly different servo neutral positions. Calibration finds the offset for each channel and saves it to `config.py`.

```bash
mpremote fs cp src/configuration/calibrate.py :calibrate.py
mpremote repl
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

Paste the output into `config.py` at the repo root. The file looks like:

```python
OFFSETS = {0: 0, 4: -3, 5: 3, 6: 0, 7: 2, 8: -1, 9: 1, 10: 0, 11: -2}
```

Upload it to the device:

```bash
mpremote fs cp config.py :config.py
```

`config.py` is gitignored — it's specific to your robot. Keep a local copy.

---

## Gait tuning

Each gait has tuning constants at the top of its file. Notes on the non-obvious ones:

### Walk (`src/gaits/walk.py`)

- `_FRAME_DELAY = 0.016` — plays every 2nd frame (~0.9s cycle). Too fast causes sliding; too slow looks sluggish.
- `_SHOULDER_SQUEEZE = 0.85` — compresses the shoulder sweep around the balance midpoint (`_SHOULDER_MID = 30`). Prevents front/rear foot clash. Must be centred on `_SHOULDER_MID`, not zero — scaling toward zero causes forward/backward lean.

### Walk back (`src/gaits/walk_back.py`)

- `_TRIM` — raw degree offset added to left-side shoulders (FL, RL) to correct sideways drift. Positive corrects rightward curve. Tune until the robot goes straight.

### Trot (`src/gaits/trot.py`)

- `_FRAME_DELAY = 0.008` — 8ms/frame is the hard minimum. The trot relies on dynamic momentum; at ≥10ms the robot falls.
- `_SHOULDER_SQUEEZE` — compresses stride around `_SHOULDER_MID = 30`. 0.87 is the stable value; 0.85 causes falls, 1.0 hobbles excessively.
- `_K_ROLL`, `_K_PITCH` — IMU correction gains. The trot wobble is primarily translational (CoM swaying between support diagonals), so shoulder squeeze has more effect than IMU gain on reducing it.
- IMU correction is grouped by diagonal, not by side: diagonal 1 (FL+RR) gets `+pitch_adj + roll_adj`, diagonal 2 (FR+RL) gets `-pitch_adj + roll_adj`.
- Timing uses `ticks_us()` to measure per-frame compute time and subtracts it from the sleep — servo commands fire at consistent 8ms intervals regardless of IMU read overhead (~0.5ms).

---

## Resources

- [MicroPython ESP32 docs](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [OpenCat ESP32 source](https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot)
- [Petoi Forum](https://www.petoi.camp/forum)
