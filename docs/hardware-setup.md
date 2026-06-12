# Hardware Setup and Calibration


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

## Gait tuning

> **2026-06-10 servo scale fix:** the servo driver originally mapped 180° onto the
> P1L's 270° pulse range, so every commanded degree moved 1.5 physical degrees. All
> gaits now play OpenCat keyframes faithfully (`commanded = 90 + rotDir × raw`) and
> the squeeze/trim/scale fudges below are reset to neutral. The tuning observations
> recorded here predate the fix — re-tune from the neutral defaults.

Each gait has tuning constants at the top of its file. Notes on the non-obvious ones:

### Walk (`src/gaits/walk.py`)

- `_FRAME_DELAY = 0.016` — plays every 2nd frame (~0.9s cycle). Too fast causes sliding; too slow looks sluggish.
- `_SHOULDER_SQUEEZE = 1.0` — compresses the shoulder sweep around the balance midpoint (`_SHOULDER_MID = 30`) if reduced. Must be centred on `_SHOULDER_MID`, not zero — scaling toward zero causes forward/backward lean. (0.85 was needed pre-scale-fix to stop foot clash.)

### Walk back (`src/gaits/walk_back.py`)

- `_TRIM` — raw degree offset added to left-side shoulders (FL, RL) to correct sideways drift. Positive corrects rightward curve. Tune until the robot goes straight. (Was 9 pre-scale-fix; reset to 0.)

### Behaviors / tricks (`src/behaviors.py`)

Tricks (wave, high-five, push-ups, …) don't use a fixed frame delay. Each OpenCat behavior
frame carries its own transition speed and pause, replayed per OpenCat `skill.h`/`motion.h`:

- transition: cosine-eased interpolation at `speed_byte / 8` degrees per 8 ms step, all
  joints arriving together; a speed byte of 0 snaps instantly (used mid-moonwalk/boxing)
- pause: `delay_byte × 50 ms` after the frame lands
- loop spec `(loop_from, loop_to, count)` replays a frame sub-range, e.g. each push-up rep

A trick that looks too violent or too sluggish on hardware means the frame data needs
checking against `InstinctBittleESP.h`, not a constant tweak — there are no per-trick fudges.

### Trot (`src/gaits/trot.py`)

- `_FRAME_DELAY = 0.008` — matches OpenCat's ~8ms gait frame rate. (Pre-scale-fix, ≥10ms caused falls; re-test at the corrected scale.)
- `_SHOULDER_SQUEEZE` — compresses stride around `_SHOULDER_MID = 30` if reduced; neutral 1.0 plays trF faithfully.
- `_K_ROLL`, `_K_PITCH` — IMU knee correction gains. The trot wobble is primarily translational (CoM swaying between support diagonals), so shoulder squeeze has more effect than IMU gain on reducing it.
- Knee correction is grouped by diagonal, not by side: diagonal 1 (FL+RR) gets `+pitch_adj + roll_adj`, diagonal 2 (FR+RL) gets `-pitch_adj + roll_adj`. Stance legs only.
- `_K_SHOULDER_PITCH` — shoulder pitch correction (OpenCat `uPF` equivalent): sweeps all four feet fore/aft to re-centre the body over the support feet. Applied to swing legs too, so the next foothold lands shifted.
- `_DEAD_PITCH` / `_DEAD_ROLL` — dead zones (OpenCat `levelTolerance`): deviations inside the band are the gait's own rhythmic sway and are *not* corrected. Without this the correction fights the gait at its own frequency and amplifies wobble. Widen if correction looks twitchy.
- `_ADJ_SLEW` — max change in each correction per frame (OpenCat `ADJUSTMENT_DAMPER`): corrections ramp instead of step-jumping when the IMU reading swings.
- `_DEV_CLAMP` — deviation is capped at ±15° before gains, so a big stumble produces a bounded response.
- Timing uses `ticks_us()` to measure per-frame compute time and subtracts it from the sleep — servo commands fire at consistent 8ms intervals regardless of IMU read overhead (~0.5ms).

---

## Resources

- [MicroPython ESP32 docs](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [OpenCat ESP32 source](https://github.com/PetoiCamp/OpenCatEsp32-Quadruped-Robot)
- [Petoi Forum](https://www.petoi.camp/forum)
