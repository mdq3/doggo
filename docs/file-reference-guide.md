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
mpremote fs mkdir :drivers
mpremote fs cp src/drivers/servo.py :drivers/servo.py
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

Device must already have `drivers/servo.py`, `poses.py`, and `config.py` uploaded.

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

### `src/gaits/turn.py`

Turn left and right gaits. Ported from OpenCat `wkL` (walk-left) array — same stable 3-point support pattern as `walk.py` and `walk_back.py`. Produces a wide arc turn rather than an in-place pivot. Right turn is derived by swapping L/R joint column pairs before conversion.

**What it provides:**
- `_FRAMES` — 116 raw OpenCat keyframes per cycle (every 2nd frame played)
- `turn_left(steps=None)` — arc turn left for N cycles (or indefinitely)
- `turn_right(steps=None)` — arc turn right (L/R mirrored from turn_left)

**Frame delay:** `_FRAME_DELAY = 0.016`, plays every 2nd frame for decisive steps above servo deadband.

**Upload to device:**
```bash
mpremote fs cp src/gaits/turn.py :gaits/turn.py
```

---

### `src/gaits/pivot.py`

In-place pivot left and right. Ported from OpenCat `vtL` (vturn-left) — 72-frame crawl that rotates the body in place rather than arcing. Right pivot = L/R column mirror.

**What it provides:**
- `pivot_left(steps=None)`, `pivot_right(steps=None)`

**Upload to device:**
```bash
mpremote fs cp src/gaits/pivot.py :gaits/pivot.py
```

---

### `src/gaits/bound_turn.py`

Tight arc turn left and right. Same `vtL` crawl sequence as `pivot.py` but with a higher shoulder cap, producing a tight-radius arc rather than in-place rotation. Use this for nimble turns; use `pivot.py` when turning on the spot.

**What it provides:**
- `bound_left(steps=None)`, `bound_right(steps=None)`

**Upload to device:**
```bash
mpremote fs cp src/gaits/bound_turn.py :gaits/bound_turn.py
```

---

### `src/gaits/trot.py`

Fast forward trot. Ported from OpenCat `trF` — 48-frame diagonal-pair gait (FL+RR, FR+RL move together). Faster than crawl gaits but dynamically less stable; IMU correction actively counteracts roll and pitch each frame.

**What it provides:**
- `trot_forward(steps=2)` — trot for N cycles (default 2)

**Tuning constants** (top of file):
- `_FRAME_DELAY` — 8ms/frame hard minimum; the gait needs dynamic momentum and falls at ≥10ms
- `_FRONT_SHOULDER_SQUEEZE` / `_REAR_SHOULDER_SQUEEZE` — compress stride around `_SHOULDER_MID=30`; 0.9 is the stable sweet spot (0.85 causes falls, 1.0 hobbles excessively)
- `_LEG_PUSH_SCALE` / `_LEG_LIFT_SCALE` — scale push stride vs lift height independently
- `_USE_IMU` — enable IMU roll/pitch correction (requires `imu.py` deployed)
- `_K_PITCH`, `_K_ROLL`, `_IMU_CLAMP` — IMU correction gains

**Timing:** Uses `ticks_us()` to measure per-frame compute time and subtracts it from the sleep, so servo commands fire at consistent 8ms intervals regardless of IMU read overhead (~0.5ms). This matters for foot contact consistency.

**IMU correction formula** groups legs by diagonal (not left/right side) and applies direct commanded-angle deltas without `_RD` multiplication:
- Diagonal 1 (FL+RR): `angle += pitch_adj + roll_adj`
- Diagonal 2 (FR+RL): `angle += -pitch_adj + roll_adj`

The hobbling in trot is primarily translational (CoM swaying between support diagonals), not rotational — so shoulder squeeze has more effect than IMU gain on reducing it.

**Upload to device:**
```bash
mpremote fs cp src/gaits/trot.py :gaits/trot.py
```

---

### `src/imu.py`

ICM-42670-P IMU driver with complementary filter. The BiBoard V1 IMU is labelled ICM-20600 in Petoi docs but the actual chip returns WHO_AM_I = 0x67 (ICM-42670-P) — different register map.

**Hardware:** I2C address 0x69, SDA=GPIO21, SCL=GPIO22, 400kHz.

**What it provides:**
- `init()` — configure chip, seed filter from accelerometer
- `read()` → `(pitch_deg, roll_deg)` — ~0.3ms per call; nose-up = +pitch, roll right = +roll

**Smoke test:**
```python
import imu; imu.init(); print(imu.read())
# Flat: (0±2, 0±2)
```

**Upload to device:**
```bash
mpremote fs cp src/imu.py :imu.py
```

---

### `src/demos/walk.py`

**Purpose:** Walk demo script. Runs stand → walk → rest sequence.

**What it does:** stand → `walk(steps=5)` → rest

**Run directly from host:**
```bash
mpremote run src/demos/walk.py
```

Device must already have `drivers/servo.py`, `poses.py`, `config.py`, and `gaits/walk.py` uploaded.

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

### `src/device_info.py`

**Purpose:** Device diagnostics for the `/info` HTTP endpoint.

**What it provides:**
- `device_info()` — returns a formatted multi-line string with:
  - `platform` — MicroPython platform identifier
  - `micropython` — version string
  - `cpu_freq` — CPU frequency in MHz
  - `chip_id` — unique ESP32 chip ID (hex)
  - `ram_used` / `ram_free` / `ram_total` — heap memory in KB
  - `flash_chip` — total ESP32 flash size (4096 KB for BiBoard)
  - `flash_total` — filesystem partition size (2048 KB)
  - `flash_used` / `flash_free` — filesystem usage in KB with percentage
  - `wifi_ip` — current IP address
  - `wifi_rssi` — WiFi signal strength in dBm
  - `uptime` — time since boot in h/m/s

**Upload to device:**
```bash
mpremote fs cp src/device_info.py :device_info.py
```

**Use from host:**
```bash
curl http://192.168.1.x/info
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
| `GET /turn_left?steps=N` | Call `turn_left(steps=N)` |
| `GET /turn_right?steps=N` | Call `turn_right(steps=N)` |
| `GET /pivot_left?steps=N` | Call `pivot_left(steps=N)` — in-place rotation |
| `GET /pivot_right?steps=N` | Call `pivot_right(steps=N)` |
| `GET /bound_left?steps=N` | Call `bound_left(steps=N)` — tight arc turn |
| `GET /bound_right?steps=N` | Call `bound_right(steps=N)` |
| `GET /trot?steps=N` | Call `trot_forward(steps=N)` — default 2 cycles |
| `GET /battery` | Report voltage, percentage, charge warning |
| `GET /info` | Return device diagnostics from `device_info()` |

Returns `200 OK` on success, `404 Not found` for unknown routes.

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
- Reads `NETWORKS` list and hostname from `wifi_config.py`. On boot, scans visible APs and connects to the first network in `NETWORKS` that is currently in range — allows the robot to work at multiple locations without reconfiguration.
- Registers mDNS hostname via `network.hostname()` before WiFi activation — device reachable as `{hostname}.local`
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

**Purpose:** Template showing the format for WiFi credentials and hostname.

**Usage:**
```bash
cp src/configuration/wifi_config_template.py wifi_config.py
# edit wifi_config.py — fill in NETWORKS list, WEBREPL_PASSWORD, and optionally HOSTNAME
```

Example format:
```python
NETWORKS = [
    ("home_network",   "home_password"),
    ("office_network", "office_password"),
]
WEBREPL_PASSWORD = "doggo"
HOSTNAME = "doggo"
```

`wifi_config.py` is gitignored. `src/configuration/wifi_config_template.py` is safe to commit (no real credentials).

`HOSTNAME` defaults to `"doggo"` — device reachable as `http://doggo.local/`. `.local` resolution via mDNS may be slow on some networks; use `curl -4` to force IPv4 and avoid the IPv6 timeout.

---

### `webrepl_proxy.py`

**Purpose:** Host-side PTY bridge that lets `mpremote` talk to the device over WebREPL. mpremote has no built-in WebREPL transport; this proxy creates a pseudo-terminal (PTY) that mpremote treats as a normal serial port.

**Not deployed to device** — runs on the host machine.

**Usage:**
```bash
# Reads host + password from wifi_config.py automatically:
python webrepl_proxy.py repl
python webrepl_proxy.py run src/demos/walk.py
python webrepl_proxy.py fs cp src/poses.py :poses.py

# Daemon mode — stays running between mpremote invocations:
python webrepl_proxy.py
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

## Linting

### `pyproject.toml`

**Purpose:** Ruff linting configuration (host-side only, not deployed to device).

**Install:**
```bash
pip install ruff
```

**Run:**
```bash
ruff check src/          # show all issues
ruff check --fix src/    # auto-fix what can be fixed
```

Rules enabled: `E` (pycodestyle errors), `F` (pyflakes), `W` (warnings), `I` (import order). Line length: 100.

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
├── drivers/
│   └── servo.py   # from src/drivers/servo.py
├── poses.py       # from src/poses.py
└── config.py      # generated locally, gitignored
```

```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    run src/demos/stand.py
```

### Walk demo

```
BiBoard:/
├── drivers/
│   └── servo.py
├── poses.py
├── config.py
└── gaits/
    ├── walk.py         # from src/gaits/walk.py
    └── walk_back.py    # from src/gaits/walk_back.py
```

```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    run src/demos/walk.py
```

Note: `fs mkdir` will error if the directory already exists on the device — safe to ignore on re-deploy.

### With WiFi control

```
BiBoard:/
├── boot.py        # src/boot.py — WiFi connect + WebREPL
├── main.py        # src/main.py — HTTP server loop
├── server.py      # src/server.py — command routes
├── battery.py     # src/battery.py — voltage monitoring
├── device_info.py # src/device_info.py — device diagnostics
├── imu.py         # src/imu.py — ICM-42670-P IMU driver
├── poses.py       # src/poses.py — pose library
├── config.py      # generated locally, gitignored
├── wifi_config.py # gitignored, credentials
├── drivers/
│   └── servo.py   # src/drivers/servo.py — PWM driver
└── gaits/
    ├── walk.py         # src/gaits/walk.py — walk forward
    ├── walk_back.py    # src/gaits/walk_back.py — walk backward
    ├── turn.py         # src/gaits/turn.py — turn left/right arc
    ├── pivot.py        # src/gaits/pivot.py — pivot in-place
    ├── bound_turn.py   # src/gaits/bound_turn.py — tight arc turn
    └── trot.py         # src/gaits/trot.py — fast trot + IMU
```

```bash
# First-time USB bootstrap — uploads just enough to get WiFi up:
mpremote fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/main.py :main.py

# Press reset, then deploy everything over WiFi:
python deploy.py

# Then wireless:
curl http://192.168.1.x/stand
curl http://192.168.1.x/battery
python webrepl_proxy.py fs ls   # list device files
python webrepl_proxy.py repl    # interactive REPL
```


