# File Reference Guide

Quick reference for every file in the repo: what it does, where it lives, and how it's used.

---

## Source Files (`src/`)

### `src/drivers/servo.py`

**Purpose:** Hardware-only PWM servo driver. Controls servos directly via ESP32 LEDC peripheral — no external chip.

**What it provides:**
- `Servos` class with `set_servo(channel, angle)` and `set_servo_us(channel, pulse_us)`
- Lazy PWM initialisation per channel
- 200Hz PWM, 500–2500µs pulse range (0–180°), ~409 steps across servo range
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

### `src/gaits/walk.py`

**Purpose:** Walk gait — one foot at a time, three feet always on the ground. Body stays level. Ported from OpenCat `wkF` array in `InstinctBittleESP.h`.

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

### `src/gaits/walk_back.py`

Backward walk gait ported from OpenCat `bkF` (back walk fast). 43 frames per cycle.

**Tuning constants** (top of file):
- `_FRAME_DELAY` — seconds per frame; increase if feet slide
- `_SQUEEZE` — shoulder sweep compression (1.0 = none)
- `_TRIM` — left-side shoulder offset to correct sideways drift; positive corrects rightward curve

**Upload:**
```bash
mpremote fs cp src/gaits/walk_back.py :gaits/walk_back.py
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

### `src/server.py`

**Purpose:** HTTP command server for wireless Bittle control. Runs in a background `_thread` using raw sockets so the main thread stays free for WebREPL.

**Routes:**

| Route | Action |
|-------|--------|
| `GET /stand` | Call `stand()` |
| `GET /sit` | Call `sit()` |
| `GET /rest` | Call `rest()` |
| `GET /walk?steps=N` | Call `walk(steps=N)` |
| `GET /walk_back?steps=N` | Call `walk_back(steps=N)` |
| `GET /battery` | Report voltage, percentage, charge warning |
| `GET /restart` | Reload modules from flash (see below) |

Returns `200 OK` on success, `404 Not found` for unknown routes.

**`/restart` — software module reload**

Reloads `server.py`, `poses.py`, `battery.py`, `gaits/walk.py`, and `gaits/walk_back.py` from flash without a hardware reset. Servo PWM keeps running throughout — no movement, no spaz.

Use this after uploading updated files via `webrepl_proxy.py`:

```bash
# Upload a changed file, then reload it without touching the servos
python src/webrepl_proxy.py 192.168.1.x <password> fs cp src/poses.py :poses.py
curl http://192.168.1.x/restart
```

Files that `/restart` **cannot** reload (require a physical power cycle):
- `servo.py` — driver loaded before the server starts
- `boot.py` — runs before main.py
- `main.py` — starts the server; restart would need to restart itself

**What it provides:**
- `run(port)` — starts a background `_thread` that listens on port 80 (called by `main.py`, returns immediately)

**Upload to device:**
```bash
mpremote fs cp src/server.py :server.py
```

**Use from host:**
```bash
curl http://192.168.1.x/stand
curl http://192.168.1.x/walk?steps=3
```

---

## WiFi support files (`src/`)

### `src/boot.py`

**Purpose:** Runs on every device boot (before `main.py`). Connects to WiFi and starts WebREPL.

**Behaviour:**
- Reads credentials from `wifi_config.py` (gitignored)
- On success: prints `WiFi connected: <ip>`, starts WebREPL on port 8266
- On failure or missing file: prints status and continues (USB REPL still works)

**Upload to device:**
```bash
mpremote fs cp src/boot.py :boot.py
```

**Serial output after reboot:**
```
WiFi connected: 192.168.1.x
WebREPL daemon started on ws://0.0.0.0:8266
```

---

### `src/main.py`

**Purpose:** Runs after `boot.py`. Starts the HTTP command server.

**Behaviour:**
- Imports `server` and calls `server.run()` which starts a background `_thread` and returns immediately
- Main thread falls back to MicroPython REPL — WebREPL stays accessible
- If server import fails (e.g. file missing), exits silently — USB REPL unaffected

**Upload to device:**
```bash
mpremote fs cp src/main.py :main.py
```

---

### `src/configuration/wifi_config_template.py` (checked in)

**Purpose:** Template showing the format for WiFi credentials.

**Usage:**
```bash
cp src/configuration/wifi_config_template.py wifi_config.py
# edit wifi_config.py — fill in SSID, PASSWORD, WEBREPL_PASSWORD
```

`wifi_config.py` is gitignored. `src/configuration/wifi_config_template.py` is safe to commit (no real credentials).

---

### `src/webrepl_proxy.py`

**Purpose:** Host-side PTY bridge that lets `mpremote` talk to the device over WebREPL. mpremote has no built-in WebREPL transport; this proxy creates a pseudo-terminal (PTY) that mpremote treats as a normal serial port.

**Not deployed to device** — runs on the host machine.

**Usage:**
```bash
# Single command — proxy connects, runs mpremote, then exits:
python src/webrepl_proxy.py 192.168.1.x <password> repl
python src/webrepl_proxy.py 192.168.1.x <password> run src/demos/walk.py
python src/webrepl_proxy.py 192.168.1.x <password> fs cp src/poses.py :poses.py

# Daemon mode — stays running between mpremote invocations:
python src/webrepl_proxy.py 192.168.1.x <password>
# prints: PTY ready: /dev/ttys003
# then: mpremote connect /dev/ttys003 repl
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

Project description, prerequisites, quick start, WiFi control.

### `docs/hardware-and-opencat-reference.md`

BiBoard pinout, servo PWM details, OpenCat angle conversion, porting notes, restoring firmware, and why MicroPython.

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
    ├── walk.py         # from src/gaits/walk.py
    └── walk_back.py    # from src/gaits/walk_back.py
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
    ├── walk.py         # src/gaits/walk.py — walk forward gait
    └── walk_back.py    # src/gaits/walk_back.py — walk backward gait
```

```bash
# First-time USB upload (one-time setup):
mpremote fs cp src/drivers/servo.py :servo.py + \
    fs cp src/battery.py :battery.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/server.py :server.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    fs cp src/gaits/walk_back.py :gaits/walk_back.py + \
    fs cp src/main.py :main.py

# Reboot and read IP from serial:
mpremote reset

# Then wireless:
curl http://192.168.1.x/stand
curl http://192.168.1.x/battery
python src/webrepl_proxy.py 192.168.1.x <password> fs ls   # list device files
python src/webrepl_proxy.py 192.168.1.x <password> repl    # interactive REPL

# After uploading updated files, reload without touching servos:
curl http://192.168.1.x/restart
```

---

**Last Updated:** 2026-03-03
