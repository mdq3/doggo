"""Forward Trot Gait — ported from OpenCatEsp32 InstinctBittleESP.h (trF array).

48 frames per cycle. Trot: diagonal leg pairs (FL+RR, FR+RL) move together,
2-point support. Faster than crawl gaits but requires sufficient frame rate
for dynamic stability.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = ZERO_POS + rotationDirection[joint] * opencat_angle
  ZERO_POS: FL_sh=65, FR_sh=115, RR_sh=115, RL_sh=65
            FL_leg=80, FR_leg=100, RR_leg=100, RL_leg=80
  rotDir:   FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
            FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

IMU correction groups legs by diagonal, not left/right:
  Diagonal 1 (FL+RR): commanded += +pitch_adj + roll_adj
  Diagonal 2 (FR+RL): commanded += -pitch_adj + roll_adj
  No rotDir multiplication — these are direct commanded-angle deltas.

Tuning:
  Too fast / toppling   -> increase _FRAME_DELAY (e.g. 0.010 → 0.012)
  Too slow / shuffling  -> decrease _FRAME_DELAY or increase _LEG_PUSH_SCALE
  Feet catching on rug  -> increase _LEG_LIFT_SCALE
  Feet sliding on floor -> decrease _LEG_PUSH_SCALE
  Too much side wobble  -> reduce _FRONT/_REAR_SHOULDER_SQUEEZE or increase _K_ROLL
  Pitching nose-up/down -> tune _K_PITCH
  Rolling left/right    -> tune _K_ROLL
"""

import time

from utime import ticks_diff, ticks_us

from poses import (
    CH_FL_LEG,
    CH_FL_SHOULDER,
    CH_FR_LEG,
    CH_FR_SHOULDER,
    CH_RL_LEG,
    CH_RL_SHOULDER,
    CH_RR_LEG,
    CH_RR_SHOULDER,
    move_to,
    play_frame,
    stand,
)

# Gait array index → (channel, rotationDirection, zero_position)
_CH = (
    CH_FL_SHOULDER,
    CH_FR_SHOULDER,
    CH_RR_SHOULDER,
    CH_RL_SHOULDER,
    CH_FL_LEG,
    CH_FR_LEG,
    CH_RR_LEG,
    CH_RL_LEG,
)
_RD = (1, -1, -1, 1, -1, 1, 1, -1)
_ZERO = (65, 115, 115, 65, 80, 100, 100, 80)  # mechanical neutral per joint

_FRAME_DELAY = 0.008  # seconds per frame — this gait needs ~8ms for dynamic stability
_FRONT_SHOULDER_SQUEEZE = 0.87  # compress FL/FR sweep — reduce lateral CoM sway
_REAR_SHOULDER_SQUEEZE = 0.87  # compress RR/RL sweep — reduce lateral CoM sway
_SHOULDER_MID = 30  # OpenCat balance-pose shoulder angle (raw)
_LEG_PUSH_SCALE = 0.9  # scale push/stride (raw > 0) — reduce to cut sliding
_LEG_LIFT_SCALE = 1.0  # scale lift height (raw < 0) — increase for rug clearance
_TRIM = 2  # raw degrees added to left shoulders (FL+RL); positive corrects rightward curve

# IMU stabilization — actively corrects roll/pitch each frame
_K_PITCH = 0.2  # pitch correction gain
_K_ROLL = 0.4  # roll correction gain
_IMU_CLAMP = 8  # max correction degrees per axis

# Index constants for IMU correction (legs only, indices 4-7 in _CH).
# Grouped by diagonal pair — pitch correction alternates by diagonal, roll is uniform.
_FL_LEG_I = 4  # diagonal 1 (FL+RR): +pitch, +roll
_FR_LEG_I = 5  # diagonal 2 (FR+RL): -pitch, +roll
_RR_LEG_I = 6  # diagonal 1
_RL_LEG_I = 7  # diagonal 2

# Raw OpenCat angles from trF in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    (31, 35, 55, 61, 9, 0, 11, 2),
    (34, 32, 57, 60, 8, 0, 12, -1),
    (36, 27, 58, 56, 8, 3, 14, -3),
    (39, 21, 59, 52, 7, 5, 16, -3),
    (41, 17, 59, 49, 9, 9, 20, -4),
    (43, 11, 59, 44, 9, 13, 23, -3),
    (45, 5, 60, 39, 9, 18, 26, -3),
    (47, 4, 60, 38, 9, 19, 29, -2),
    (49, 2, 60, 36, 10, 22, 32, 0),
    (51, 1, 60, 36, 11, 23, 37, 0),
    (52, -1, 57, 35, 14, 26, 44, 2),
    (54, -2, 59, 34, 12, 29, 43, 3),
    (54, -2, 59, 33, 13, 30, 43, 6),
    (55, -1, 60, 32, 11, 31, 41, 7),
    (58, -1, 63, 34, 8, 31, 36, 7),
    (58, 2, 65, 36, 5, 27, 33, 6),
    (58, 6, 65, 39, 5, 24, 32, 6),
    (59, 9, 67, 42, 3, 21, 29, 5),
    (58, 13, 67, 44, 2, 18, 28, 5),
    (57, 16, 69, 47, -1, 16, 20, 5),
    (53, 19, 68, 49, -2, 13, 16, 6),
    (49, 21, 67, 50, -2, 14, 11, 8),
    (45, 25, 66, 52, -2, 12, 8, 9),
    (41, 28, 64, 54, -1, 10, 5, 10),
    (35, 31, 61, 55, 0, 9, 2, 11),
    (32, 34, 60, 57, 0, 8, -1, 12),
    (27, 36, 56, 58, 3, 8, -3, 14),
    (21, 39, 52, 59, 5, 7, -3, 16),
    (17, 41, 49, 59, 9, 9, -4, 20),
    (11, 43, 44, 59, 13, 9, -3, 23),
    (5, 45, 39, 60, 18, 9, -3, 26),
    (4, 47, 38, 60, 19, 9, -2, 29),
    (2, 49, 36, 60, 22, 10, 0, 32),
    (1, 51, 36, 60, 23, 11, 0, 37),
    (-1, 52, 35, 57, 26, 14, 2, 44),
    (-2, 54, 34, 59, 29, 12, 3, 43),
    (-2, 54, 33, 59, 30, 13, 6, 43),
    (-1, 55, 32, 60, 31, 11, 7, 41),
    (-1, 58, 34, 63, 31, 8, 7, 36),
    (2, 58, 36, 65, 27, 5, 6, 33),
    (6, 58, 39, 65, 24, 5, 6, 32),
    (9, 59, 42, 67, 21, 3, 5, 29),
    (13, 58, 44, 67, 18, 2, 5, 28),
    (16, 57, 47, 69, 16, -1, 5, 20),
    (19, 53, 49, 68, 13, -2, 6, 16),
    (21, 49, 50, 67, 14, -2, 8, 11),
    (25, 45, 52, 66, 12, -2, 9, 8),
    (28, 41, 54, 64, 10, -1, 10, 5),
)


_FRAME_US = int(_FRAME_DELAY * 1_000_000)


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def _to_commanded(raw):
    """Convert a raw frame to commanded-angle dict. Used only for the startup move_to."""
    result = {}
    for i in range(8):
        r = raw[i]
        if i < 4:
            sq = _FRONT_SHOULDER_SQUEEZE if i < 2 else _REAR_SHOULDER_SQUEEZE
            r = _SHOULDER_MID + (r - _SHOULDER_MID) * sq
        else:
            r = r * (_LEG_LIFT_SCALE if r < 0 else _LEG_PUSH_SCALE)
        result[_CH[i]] = _ZERO[i] + _RD[i] * r
    return result


# Lazy pre-computed base frames: populated on first trot_forward() call, not at
# module load (avoids crashing the server if computation fails).
# Each entry: (commanded_angles_tuple, raw_leg_values_tuple)
# raw_legs is raw[4:] — used to detect stance (>= 0) vs swing (< 0).
_BASE: tuple | None = None
_frame_buf = {ch: 0.0 for ch in _CH}  # reusable — avoids dict allocation in the hot loop


def _ensure_base():
    global _BASE
    if _BASE is not None:
        return
    frames = []
    for raw in _FRAMES:
        base = []
        for i in range(8):
            r = raw[i]
            if i < 4:
                sq = _FRONT_SHOULDER_SQUEEZE if i < 2 else _REAR_SHOULDER_SQUEEZE
                r = _SHOULDER_MID + (r - _SHOULDER_MID) * sq
                if i == 0 or i == 3:  # FL_sh, RL_sh — left side trim
                    r += _TRIM
            else:
                r = r * (_LEG_LIFT_SCALE if r < 0 else _LEG_PUSH_SCALE)
            base.append(_ZERO[i] + _RD[i] * r)
        frames.append((tuple(base), raw[4:]))
    _BASE = tuple(frames)


def _play_base_frame(base, raw_legs, p_adj, r_adj):
    """Fill _frame_buf from pre-computed base angles + IMU correction, then dispatch.

    IMU correction is applied only to stance legs (raw >= 0 = foot on ground).
    Swing legs (foot in air) are unaffected — correction there has no physical effect.
    """
    for i in range(8):
        a = base[i]
        if i >= 4 and raw_legs[i - 4] >= 0:  # stance leg
            if i == _FL_LEG_I or i == _RR_LEG_I:  # diagonal 1
                a += p_adj + r_adj
            else:  # diagonal 2 (FR, RL)
                a += -p_adj + r_adj
        _frame_buf[_CH[i]] = a
    play_frame(_frame_buf)


def trot_forward(steps=None, use_imu=True):
    """
    Trot forward (48-frame diagonal-pair cycle).

    Args:
        steps:   Number of full 48-frame cycles to run.
                 None = run until KeyboardInterrupt.
        use_imu: Enable IMU roll/pitch stabilization (default True).
    """
    print("\nStarting trot forward...")

    imu = None
    if use_imu:
        try:
            from imu import IMU

            imu = IMU()
        except Exception as e:
            print("IMU init failed:", e)

    _ensure_base()
    assert _BASE is not None
    frames = _BASE
    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for base, raw_legs in frames:
                t0 = ticks_us()
                if imu is not None:
                    try:
                        pitch, roll = imu.read()
                        p_adj = _clamp(_K_PITCH * pitch, -_IMU_CLAMP, _IMU_CLAMP)
                        r_adj = _clamp(_K_ROLL * roll, -_IMU_CLAMP, _IMU_CLAMP)
                    except Exception:
                        p_adj = r_adj = 0.0
                else:
                    p_adj = r_adj = 0.0
                _play_base_frame(base, raw_legs, p_adj, r_adj)
                remaining = _FRAME_US - ticks_diff(ticks_us(), t0)
                if remaining > 0:
                    time.sleep_us(remaining)
            count += 1
    except KeyboardInterrupt:
        print("\n\nTrot interrupted.")

    print("Returning to stand...")
    stand()
