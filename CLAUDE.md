# CLAUDE.md — Bittle MicroPython Project

## Project Overview

MicroPython control of a Petoi Bittle X V2 quadruped robot running on its BiBoard V1.0 (ESP32).
Replaces the stock OpenCat firmware with hand-written Python.

**Doggo Code Blocks** (`doggo-code-blocks/`) is an Electron desktop app that provides drag-and-drop block programming for the robot. It compiles Scratch-style blocks to MicroPython and sends scripts to the robot over Wi-Fi via `webrepl_proxy.py`.

## Architecture

### Layer separation

```
src/drivers/servo.py        — hardware only: PWM/GPIO, no calibration knowledge
src/poses.py                — poses layer: calibration, motion, named poses
src/behaviors.py            — behavior (trick) player + tricks: wave, high-five, handshake, pee, play dead, push-ups, moonwalk, boxing, recover (OpenCat behavior arrays)
src/battery.py              — battery voltage monitoring (GPIO 37, BiBoard V1.0)
src/device_info.py          — device diagnostics: RAM, flash, CPU, WiFi, uptime
src/gaits/player.py         — shared keyframe-gait player: 90+rotDir conversion, L/R mirror, frame-loop playback (enter-from-stand → loop → stand)
src/gaits/walk.py           — walk forward gait: 116-frame OpenCat wkF keyframe sequence
src/gaits/walk_back.py      — walk backward gait: 43-frame OpenCat bkF keyframe sequence
src/gaits/back_turn.py      — walk backward left/right arc gaits: 48-frame OpenCat bkL keyframe sequence
src/gaits/turn.py           — turn left/right gaits: 116-frame OpenCat wkL keyframe sequence
src/gaits/pivot.py          — pivot left/right in-place gaits: 72-frame OpenCat vtL keyframe sequence
src/gaits/bound_turn.py     — bound left/right arc-turn gaits: 42-frame OpenCat trL keyframe sequence
src/gaits/step.py           — step-in-place gait: 37-frame OpenCat vtF keyframe sequence
src/gaits/crawl.py          — crawl forward gait: 103-frame low-stance OpenCat crF keyframe sequence
src/gaits/crawl_turn.py     — crawl left/right arc gaits: 103-frame OpenCat crL keyframe sequence
src/gaits/trot.py           — trot forward gait: 48-frame OpenCat trF; IMU roll/pitch stabilization
src/gaits/trot_ik.py        — IK-based trot: parametric foot trajectories + 2-link IK each frame; IMU stabilization
src/imu.py                  — ICM-42670-P IMU driver (I2C 0x69, GPIO 21/22); complementary filter → pitch/roll; tilt() for flip detection
src/fall_watchdog.py        — auto-recovery thread: polls IMU tilt, plays recover() when flipped and idle (OpenCat IMU_EXCEPTION_FLIPPED reaction)
src/kinematics/__init__.py  — kinematics package
src/kinematics/leg.py       — 2-DOF planar leg IK/FK (L1=50mm, L2=55mm); fk(alpha, gamma) → (x,z); ik(x,z) → (alpha, gamma)
src/kinematics/doggo.py     — robot-specific angle conversion: physical (alpha, gamma) → servo commanded angles
src/demos/stand.py          — demo: stand → sit → stand → rest
src/demos/walk.py           — demo: stand → walk → rest
src/demos/trot.py           — demo: stand → trot (4 cycles, IMU on) → rest
src/server.py               — HTTP command server (_thread + raw sockets, port 80)
src/boot.py                 — WiFi connect + mDNS hostname + WebREPL start (runs on every boot)
src/main.py                 — HTTP server loop (runs after boot.py)
webrepl_proxy.py            — host-side PTY proxy: bridges mpremote ↔ WebREPL WebSocket; reads DOGGO_HOST/DOGGO_PASSWORD env vars (set by Doggo Code Blocks app) or falls back to wifi_config.py
src/configuration/wifi_config_template.py — credential template (copy → wifi_config.py)
doggo-code-blocks/                     — Electron desktop app: block programming UI → MicroPython → webrepl_proxy.py
doggo-code-blocks/src/main/main.ts     — Electron main process: menu, settings (userData/settings.json), spawns webrepl_proxy.py
doggo-code-blocks/src/preload/preload.ts — context-bridge preload exposing IPC to the renderer
doggo-code-blocks/src/renderer/components/App.tsx — React renderer root: Blockly workspace, splash screen, settings dialog, error popup
doggo-code-blocks/src/renderer/blocks.ts    — custom Scratch block definitions
doggo-code-blocks/src/renderer/generator.ts — Blockly MicroPython code generator
doggo-code-blocks/src/renderer/commands.ts  — command registry (pose/trick/motion defs): single source for blocks, imports, generated calls
doggo-code-blocks/forge.config.mjs     — electron-forge packaging config (lint/format/test run via Vite+ `vp`)
```

`servo.py` is a clean hardware abstraction. Calibration and robot-specific geometry belong to `poses.py`, not the driver.

### Key files

| File | Role | Lives on device as |
|------|------|--------------------|
| `src/drivers/servo.py` | Direct PWM servo driver (ESP32 LEDC, 200Hz) | `drivers/servo.py` |
| `src/poses.py` | Pose library — channel consts, `GAIT_CHANNELS`/`ROTATION_DIRECTION`, calibration, `move_to`, `play_frame`, `stand`, `sit`, `rest`, `stretch`, `zero_position` | `poses.py` |
| `src/behaviors.py` | Behavior (trick) player — per-frame speed/delay + loop section playback of OpenCat behavior arrays; `wave`, `high_five`, `handshake`, `pee`, `play_dead`, `push_ups`, `moonwalk`, `boxing`, `recover` (get up after falling) | `behaviors.py` |
| `src/battery.py` | Battery voltage monitoring — GPIO 37 ADC, BiBoard V1.0 formula | `battery.py` |
| `src/device_info.py` | Device diagnostics — RAM, flash, CPU freq, chip ID, WiFi, uptime | `device_info.py` |
| `src/gaits/player.py` | Shared keyframe-gait player — `to_commanded` (90 + rotDir·raw), `mirror` (L/R swap), `play` (enter-from-stand → frame loop → stand); per-gait `transform`/`mirror_lr`/`every` knobs | `gaits/player.py` |
| `src/gaits/walk.py` | Walk gait — 116-frame one-foot-at-a-time sequence from OpenCat `wkF` | `gaits/walk.py` |
| `src/gaits/walk_back.py` | Walk backward gait — 43-frame one-foot-at-a-time sequence from OpenCat `bkF` | `gaits/walk_back.py` |
| `src/gaits/back_turn.py` | Walk backward left/right arc — 48-frame sequence from OpenCat `bkL`; right = L/R mirror | `gaits/back_turn.py` |
| `src/gaits/turn.py` | Turn left/right gaits — 116-frame arc-turn sequence from OpenCat `wkL`; right = L/R mirror | `gaits/turn.py` |
| `src/gaits/pivot.py` | Pivot left/right in-place — 72-frame crawl from OpenCat `vtL`; right = L/R mirror | `gaits/pivot.py` |
| `src/gaits/bound_turn.py` | Bound left/right arc turn — 42-frame `vtL` variant with wider shoulder cap | `gaits/bound_turn.py` |
| `src/gaits/step.py` | Step in place — 37-frame marching sequence from OpenCat `vtF` | `gaits/step.py` |
| `src/gaits/crawl.py` | Crawl forward — 103-frame low-stance sequence from OpenCat `crF` | `gaits/crawl.py` |
| `src/gaits/crawl_turn.py` | Crawl left/right arc — 103-frame sequence from OpenCat `crL`; right = L/R mirror | `gaits/crawl_turn.py` |
| `src/gaits/trot.py` | Trot forward — 48-frame diagonal-pair gait from OpenCat `trF`; IMU roll/pitch correction | `gaits/trot.py` |
| `src/gaits/trot_ik.py` | IK-based trot — parametric foot trajectories, 2-link IK per frame, IMU stabilization | `gaits/trot_ik.py` |
| `src/imu.py` | ICM-42670-P IMU driver — I2C 0x69, SDA=GPIO21, SCL=GPIO22; complementary filter → `(pitch, roll)`; `tilt()` = accel-only angle from upright (flip detection) | `imu.py` |
| `src/fall_watchdog.py` | Auto-recovery thread — plays `recover()` when tilt > 75° sustained 1s while no motion for 2s and `poses.motion_lock` free; 3 attempts then gives up until righted | `fall_watchdog.py` |
| `src/kinematics/leg.py` | 2-DOF planar leg IK/FK — `fk(alpha, gamma)→(x,z)`, `ik(x,z)→(alpha, gamma)`; L1=50mm, L2=55mm | `kinematics/leg.py` |
| `src/kinematics/doggo.py` | Servo angle conversion — physical `(alpha, gamma)` → commanded angles; `leg_frame()` builds 8-joint dict | `kinematics/doggo.py` |
| `src/server.py` | HTTP command server — routes `/stand` `/sit` `/rest` `/stretch` `/walk` `/walk-back` `/walk-back-left` `/walk-back-right` `/turn-left` `/turn-right` `/pivot-left` `/pivot-right` `/bound-left` `/bound-right` `/step` `/crawl` `/crawl-left` `/crawl-right` `/trot` `/trot-ik` `/wave` `/high-five` `/handshake` `/pee` `/play-dead` `/push-ups` `/moonwalk` `/boxing` `/recover` `/watchdog` `/battery` `/info`; motion routes hold `poses.motion_lock` | `server.py` |
| `src/boot.py` | Runs on boot: WiFi connect + mDNS hostname registration + WebREPL start | `boot.py` |
| `src/main.py` | Runs after boot: starts HTTP server loop + fall watchdog | `main.py` |
| `webrepl_proxy.py` | Host-side PTY proxy bridging mpremote ↔ WebREPL; reads `DOGGO_HOST`/`DOGGO_PASSWORD` env vars (from Doggo Code Blocks) or falls back to `wifi_config.py` | n/a (host only) |
| `src/configuration/wifi_config_template.py` | Credential + hostname template (checked in; copy to `wifi_config.py`) | n/a (host only) |
| `doggo-code-blocks/src/main/main.ts` | Electron main process — menu, settings persistence (`userData/settings.json`), spawns `webrepl_proxy.py` with env vars | n/a (host only) |
| `doggo-code-blocks/src/preload/preload.ts` | Context-bridge preload — exposes IPC channels to the renderer | n/a (host only) |
| `doggo-code-blocks/src/renderer/components/App.tsx` | React renderer root — splash screen, Blockly workspace, toolbar (Run/Code/Settings), error popup, settings dialog | n/a (host only) |
| `doggo-code-blocks/src/renderer/blocks.ts` | Custom Scratch block type definitions | n/a (host only) |
| `doggo-code-blocks/src/renderer/generator.ts` | Blockly → MicroPython code generator | n/a (host only) |
| `doggo-code-blocks/src/renderer/commands.ts` | Command registry — pose/trick/motion defs (block type, label, import, function) shared by blocks, toolbox and generator | n/a (host only) |
| `doggo-code-blocks/forge.config.mjs` | electron-forge packaging config; lint/format/test via Vite+ (`vp`) | n/a (host only) |
| `src/demos/stand.py` | Stand demo script | run via `python webrepl_proxy.py run` |
| `src/demos/walk.py` | Walk demo script | run via `python webrepl_proxy.py run` |
| `src/demos/trot.py` | Trot demo script (uses keyframe trot, not IK) | run via `python webrepl_proxy.py run` |
| `config.py` | Calibration offsets — **gitignored**, generated by `src/configuration/calibrate.py` | `config.py` |
| `src/configuration/calibrate.py` | Interactive REPL calibration tool | `calibrate.py` |
| `src/configuration/identify_servos.py` | Wiggles each channel to map channel→joint | `identify_servos.py` |
| `src/configuration/verify_servos_working.py` | Quick servo sanity check | run via `python webrepl_proxy.py run` |

Use the docs directory for information on design decisions, documented plan, and setup guide.

### BiBoard V1 servo channels (Bittle)

```
CH 0  → Head pan
CH 4  → Front Left Shoulder   (rotDir +1)
CH 5  → Front Right Shoulder  (rotDir -1)
CH 6  → Rear Right Shoulder   (rotDir -1)
CH 7  → Rear Left Shoulder    (rotDir +1)
CH 8  → Front Left Leg        (rotDir -1)
CH 9  → Front Right Leg       (rotDir +1)
CH 10 → Rear Right Leg        (rotDir +1)
CH 11 → Rear Left Leg         (rotDir -1)
Channels 1, 2, 3 unused.
```

GPIO pin mapping (channel → GPIO): `[18, 5, 14, 27, 23, 4, 12, 33, 19, 15, 13, 32]`

### Servo PWM

`servo.py` runs at **200Hz** (default). The ESP32 LEDC peripheral is 10-bit at this frequency,
giving ~409 steps across the servo range (0.44°/step). At 50Hz it is only 102 steps (1.76°/step)
which produces visible stepping/jerkiness. Bittle's digital servos support up to ~330Hz.

**Servo scale (critical):** Bittle X servos are Petoi P1L — **270° of travel across
500–2500µs** (OpenCat `espServo.h`). `servo.py` maps angles accordingly: 90 = centre
(1500µs), valid range −45..225, **1 commanded degree = 1 physical degree**. The driver
originally mapped 180° onto this pulse range, making every commanded degree 1.5 physical
degrees — all gait instability, the too-tall posture, and the IK servo stalls traced back
to this. Verified on hardware 2026-06-10 (`src/configuration/check_servo_scale.py`).

### Calibration system

`config.py` stores per-channel offsets (degrees from 90°). It is **gitignored** — each robot has different offsets. Generate it by running `src/configuration/calibrate.py` in the REPL and copying the `done()` output.

`apply_calibration(angle, ch)` adds the offset before sending to hardware.
`_REST_COMMANDED` in `poses.py` uses *commanded* (pre-calibration) angles.
`current_pos` in `poses.py` tracks *calibrated* angles for smooth interpolation.

### Angle conventions

With the corrected 270° servo scale, **one formula covers everything** — named poses
and gait keyframes alike:
```
commanded_angle = 90 + rotationDirection[joint] * opencat_raw
```
Commanded 90 = OpenCat raw 0 = the calibration pose. OpenCat's `middleShift[]` does not
appear: it is part of the servo-centre definition, which calibration (`config.py`) already
encodes. The per-robot calibration offsets ≈ `middleShift × rotationDirection` + true
per-servo error (this robot: +55.5/−49.5/+63/−61.5 shoulders, +54/−48/−51/+48 legs).

The old two-formula scheme (`ZERO_POS = 65/115/80/100`) and the gait squeeze/trim/scale
fudges were empirical compensations for the 1.5× servo scale error — do not reintroduce
them. Gait tuning constants are reset to neutral and need re-tuning on hardware.

## Deployment with mpremote

Scripts run with `python webrepl_proxy.py run` execute in device context — imports resolve against the device filesystem.

### Stand demo
```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    run src/demos/stand.py
```

### Walk demo
```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/player.py :gaits/player.py + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    run src/demos/walk.py
```

### Trot demo
```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp config.py :config.py + \
    fs cp src/imu.py :imu.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/trot.py :gaits/trot.py + \
    run src/demos/trot.py
```

Note: `fs mkdir` will error if the directory already exists — safe to ignore.

### WiFi setup (one-time USB upload)
```bash
mpremote fs mkdir :drivers + \
    fs cp src/drivers/servo.py :drivers/servo.py + \
    fs cp src/poses.py :poses.py + \
    fs cp src/behaviors.py :behaviors.py + \
    fs cp src/battery.py :battery.py + \
    fs cp src/device_info.py :device_info.py + \
    fs cp config.py :config.py + \
    fs cp wifi_config.py :wifi_config.py + \
    fs cp src/boot.py :boot.py + \
    fs cp src/server.py :server.py + \
    fs cp src/imu.py :imu.py + \
    fs cp src/fall_watchdog.py :fall_watchdog.py + \
    fs mkdir :gaits + \
    fs cp src/gaits/player.py :gaits/player.py + \
    fs cp src/gaits/walk.py :gaits/walk.py + \
    fs cp src/gaits/walk_back.py :gaits/walk_back.py + \
    fs cp src/gaits/back_turn.py :gaits/back_turn.py + \
    fs cp src/gaits/turn.py :gaits/turn.py + \
    fs cp src/gaits/pivot.py :gaits/pivot.py + \
    fs cp src/gaits/bound_turn.py :gaits/bound_turn.py + \
    fs cp src/gaits/step.py :gaits/step.py + \
    fs cp src/gaits/crawl.py :gaits/crawl.py + \
    fs cp src/gaits/crawl_turn.py :gaits/crawl_turn.py + \
    fs cp src/gaits/trot.py :gaits/trot.py + \
    fs cp src/gaits/trot_ik.py :gaits/trot_ik.py + \
    fs mkdir :kinematics + \
    fs cp src/kinematics/__init__.py :kinematics/__init__.py + \
    fs cp src/kinematics/leg.py :kinematics/leg.py + \
    fs cp src/kinematics/doggo.py :kinematics/doggo.py + \
    fs cp src/main.py :main.py
```

After first-time USB setup, subsequent deploys are easier with:
```bash
python deploy.py doggo.local <password>
```

### mpremote over WiFi (after WiFi setup)
```bash
# Terminal 1
python webrepl_proxy.py
# Terminal 2 — use the PTY path printed by the proxy
mpremote connect /dev/ttysNNN repl
mpremote connect /dev/ttysNNN run src/demos/walk.py
```

## Documentation maintenance

When making code changes, keep `README.md` and `docs/` in sync:

- **Route changes** (add/remove/rename) → update the routes table in `README.md` and the route tables in `src/server.py` (`_POSE_ROUTES`/`_GAIT_ROUTES`/`_TRICK_ROUTES`/`_DIAG_ROUTES`; `GET /` serves a generated index from them)
- **New files or modules** → add to the layer separation diagram and key files table in this file (`CLAUDE.md`)
- **New gaits or demos** → add to the relevant deployment commands in `CLAUDE.md`
- **Tuning constants or behaviour changes** → update `docs/hardware-setup.md` if that gait is documented there

## Linting

Ruff is configured in `pyproject.toml` (E/F/W/I rules, 100-char line limit).

```bash
ruff check src/          # show issues
ruff check --fix src/    # auto-fix import ordering etc.
```

## Testing

Host-side unit tests for the pure-logic parts of the firmware run on desktop CPython —
no device needed. Each test file sits **next to the source it covers**, named
`<source>_test.py` (e.g. `kinematics/leg.py` → `kinematics/leg_test.py`). `src/conftest.py`
is a thin loader for `src/test/test_harness.py`, which stubs the MicroPython-only modules
(`machine`, `utime`, `esp`, `network`, `webrepl`) and the `time.ticks_*` / `sleep_us`
extensions, then puts `src/` on the path, so the firmware modules import unchanged. Tests cover what is safe to verify off-hardware: leg
IK/FK round-trips, the OpenCat→commanded angle conversion (a regression guard against the
old 1.5x servo scale), gait L/R mirroring, IMU byte/trig decoding, and the HTTP query
parsers.

`*_test.py` are never deployed — `deploy.py` and the mpremote commands copy an explicit
file list, not a glob.

```bash
pip install --group dev   # one-time: install pytest
python -m pytest          # run the suite
```

Hardware-dependent code (servo PWM, I2C/ADC reads, gait playback timing) is exercised
on-device, not here.

## What's not implemented yet

- IK-based gaits beyond trot (walk, turn, etc. still use OpenCat keyframes)
- Remaining OpenCat gaits: `gpF`/`gpL` (gap-crossing), `hlw` (Halloween walk), `jpF` (jump
  forward), `lftF`/`lftL`, `phF`/`phL` (push walk), `carpetF`/`carpetL` (high-step carpet walk;
  newer versions in OpenCat `SkillLibrary/*.md`)
- Acrobatic behaviors (`bf`/`ff`/`flip` flips, `jmp` jump, `hds` handstand, `lpov` leap-over,
  `rl` roll) — use `angleDataRatio=2` and ballistic timing; deliberately skipped until the
  behavior player is proven on gentle tricks. (`rc` recover is ported — its frames are stored
  pre-doubled in `behaviors.py` since the player has no `angleDataRatio` support.)
- Other IMU exceptions from OpenCat's `getImuException()` (`lifted`, `dropped`/free-fall,
  `knocked`, `pushed`) — only the flipped exception is handled (`fall_watchdog.py`)
- Per-frame IMU trigger bytes in behavior arrays (zero in all ported tricks) are not supported
  by `behaviors.py`

## IMU notes

The BiBoard V1 IMU is an **ICM-42670-P** (WHO_AM_I = 0x67), not ICM-20600 as labelled in Petoi docs.
Different register map — driver is in `src/imu.py`. I2C address 0x69, SDA=GPIO21, SCL=GPIO22.

Orientation: raw accel **z > 0 means upright** on the BiBoard (OpenCat's
`petoi_icm42670p.cpp` treats `az < 0` as the flipped hemisphere when unfolding pitch).
`IMU.tilt()` uses `acos(az/|a|)` — 0° upright, 90° on side, 180° upside down — which is
what `fall_watchdog.py` polls for flip detection.
