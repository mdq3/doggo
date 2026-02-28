# File Reference Guide

Quick reference for every file in the repo: what it does, where it lives, and how it's used.

---

## Source Files (`src/`)

### `src/drivers/servo.py`

**Purpose:** Hardware-only PWM servo driver. Controls servos directly via ESP32 LEDC peripheral — no external chip.

**What it provides:**
- `Servos` class with `set_servo(channel, angle)` and `set_servo_us(channel, pulse_us)`
- Lazy PWM initialisation per channel
- 50Hz PWM, 500–2500µs pulse range (0–180°)
- Supports all 12 BiBoard channels

**No calibration knowledge** — it takes raw angles and sends them to hardware.

**Upload to device:**
```bash
mpremote fs cp src/drivers/servo.py :servo.py
```

**Referenced in:** `src/poses.py`, `src/configuration/calibrate.py`, `src/configuration/identify_servos.py`, `src/configuration/verify_servos_working.py`

---

### `src/poses.py`

**Purpose:** Pose library. The main reusable module for robot motion.

**What it provides:**
- Channel constants (`CH_HEAD`, `CH_FL_SHOULDER`, etc.)
- Calibration loading from `config.py` (with fallback to identity)
- `Servos` instance (hardware initialised on import)
- `_REST_COMMANDED` — lying-flat pose in commanded angles
- `current_pos` — tracks calibrated position for smooth interpolation
- `move_to(targets, speed, delay)` — interpolated multi-servo motion
- `zero_position()`, `stand()`, `sit()`, `rest()` — named poses

**Upload to device:**
```bash
mpremote fs cp src/poses.py :poses.py
```

**Import in scripts:**
```python
from poses import stand, sit, rest, zero_position
```

---

### `src/demos/stand.py`

**Purpose:** Stand demo script. Imports from `poses.py` and runs a fixed sequence.

**What it does:** stand → sit → stand → rest

**Run directly from host:**
```bash
mpremote run src/demos/stand.py
```

Device must already have `servo.py`, `poses.py`, and `config.py` uploaded.

---

### `src/gaits/trot.py`

**Purpose:** Trot gait — diagonal leg pairs (FL+RR, FR+RL) move simultaneously. Ported directly from OpenCat `trF` array in `InstinctBittleESP.h`.

**What it provides:**
- `_FRAMES` — 48 raw OpenCat keyframes per cycle
- `_ZERO` — per-joint mechanical neutral positions (accounts for OpenCat `middleShift[]`)
- `trot(steps=None)` — runs the gait for a fixed number of 48-frame cycles, or indefinitely until `KeyboardInterrupt`; returns to stand on completion

**Conversion formula:**
```
commanded = ZERO_POS[joint] + rotDir[joint] * opencat_raw
```

**Frame delay:** `_FRAME_DELAY = 0.012` (~1.7 Hz cycle at 48 frames)

**Upload to device:**
```bash
mpremote fs mkdir :gaits
mpremote fs cp src/gaits/trot.py :gaits/trot.py
```

**Import in scripts:**
```python
from gaits.trot import trot
trot(steps=10)
```

---

### `src/gaits/walk.py`

**Purpose:** Walk gait — one foot at a time, three feet always on the ground. Much more stable than trot; body stays level. Ported from OpenCat `wkF` array in `InstinctBittleESP.h`.

**What it provides:**
- `_FRAMES` — 116 raw OpenCat keyframes per cycle
- `_SHOULDER_SQUEEZE = 0.85` — compresses shoulder sweep around the balance pose to prevent front/rear foot clash
- `walk(steps=None)` — runs the gait for a fixed number of cycles, or indefinitely until `KeyboardInterrupt`; returns to stand on completion

**Frame delay:** `_FRAME_DELAY = 0.016`, plays every 2nd frame (~0.9s cycle at 58 effective frames)

**Upload to device:**
```bash
mpremote fs mkdir :gaits
mpremote fs cp src/gaits/walk.py :gaits/walk.py
```

**Import in scripts:**
```python
from gaits.walk import walk
walk(steps=5)
```

---

### `src/demos/walk.py`

**Purpose:** Walk demo script. Runs stand → walk → rest sequence.

**What it does:** stand → `walk(steps=5)` → rest

**Run directly from host:**
```bash
mpremote run src/demos/walk.py
```

Device must already have `servo.py`, `poses.py`, `config.py`, and `gaits/walk.py` uploaded.

---

### `src/configuration/calibrate.py`

**Purpose:** Interactive REPL calibration tool. Use once to find each servo's neutral position.

**What it provides:**
- `move(channel, angle)` / `m(channel, angle)` — move a servo
- `save(channel, neutral_angle)` / `s(channel, angle)` — record neutral
- `show()` — display saved calibration
- `done()` — print `config.py` content to copy

**Workflow:**
```bash
mpremote fs cp src/configuration/calibrate.py :calibrate.py
mpremote repl
>>> from calibrate import *
>>> move(4, 90)     # front left shoulder to center
>>> save(4, 87)     # actual neutral was 87°
>>> done()          # prints config.py content
```

---

### `src/configuration/identify_servos.py`

**Purpose:** Wiggles each channel so you can map channel numbers to physical joints.

**Workflow:**
```bash
mpremote fs cp src/configuration/identify_servos.py :identify_servos.py
mpremote repl
>>> from identify_servos import *
>>> test(0)    # watch which joint moves
>>> test(4)
# ... test all channels
```

---

### `src/configuration/verify_servos_working.py`

**Purpose:** Sanity check — moves channel 0 through a sweep, then briefly tests all Bittle channels.

```bash
mpremote run src/configuration/verify_servos_working.py
```

---

## Configuration File: `config.py`

**Purpose:** Store servo calibration offsets for this specific robot.

**Location:** Repo root (`config.py`). **Gitignored** — offsets are robot-specific and must be generated locally.

**Auto-generated by:** `src/configuration/calibrate.py` (`done()` command)

**Format:**
```python
CALIBRATION = {
     0:  +0,   # Head Pan
     4: +37,   # Front Left Shoulder
     # ...
}

def apply_calibration(angle, channel):
    return angle + CALIBRATION.get(channel, 0)
```

**Upload to device:**
```bash
mpremote fs cp config.py :config.py
```

---

## Documentation Files

### `docs/micropython-getting-started.md`

Step-by-step setup guide (flash firmware → REPL → calibrate → stand).

### `README.md`

Quick-start overview, project structure, development roadmap, hardware reference.

### `CLAUDE.md`

Architecture notes and project conventions for Claude Code sessions.

### `docs/restore-original-opencat-firmware.md`

How to restore the stock OpenCat firmware (from backup or Petoi Desktop App).

### `docs/flashing-opencat-arduino-bins.md`

How to flash compiled Arduino `.bin` files when you have multiple binary parts.

### `docs/micropython-detailed-plan.md`

Full technical analysis of the MicroPython approach, IK examples, roadmap details.

### `docs/micropython-option.md`

Pros/cons of MicroPython vs other approaches (historical planning doc).

### `docs/pico-2-w-vs-esp32-comparison.md`

Platform comparison between Raspberry Pi Pico 2 W and ESP32 (historical planning doc).

---

## Device Filesystem Layout

### Stand demo

```
BiBoard:/
├── servo.py       # from src/drivers/servo.py
├── poses.py       # from src/poses.py
└── config.py      # generated locally, gitignored
```

```bash
mpremote cp src/drivers/servo.py :servo.py + cp src/poses.py :poses.py + cp config.py :config.py
```

### Walk demo

```
BiBoard:/
├── servo.py
├── poses.py
├── config.py
└── gaits/
    ├── walk.py    # from src/gaits/walk.py
    └── trot.py    # from src/gaits/trot.py (optional)
```

```bash
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    run src/demos/walk.py
```

Note: `fs mkdir :gaits` will error if the directory already exists on the device — safe to ignore on re-deploy.

---

**Last Updated:** 2026-02-28
