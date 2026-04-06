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

## Resources

- [MicroPython ESP32 docs](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [OpenCat ESP32 source](https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot)
- [Petoi Forum](https://www.petoi.camp/forum)
