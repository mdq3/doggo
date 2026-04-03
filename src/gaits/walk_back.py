"""
Walk Back Gait — ported from OpenCatEsp32 InstinctBittleESP.h (bkF array).

43 frames per cycle. One-foot-at-a-time gait: three feet always on the ground,
body stays level.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = ZERO_POS + rotationDirection[joint] * opencat_angle
  ZERO_POS: FL_sh=65, FR_sh=115, RR_sh=115, RL_sh=65
            FL_leg=80, FR_leg=100, RR_leg=100, RL_leg=80
  rotDir:   FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
            FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Tuning:
  Too fast / unstable  → increase _FRAME_DELAY (e.g. 0.030)
  Too slow / shuffling → decrease _FRAME_DELAY (e.g. 0.015)
  Curves right         → increase _TRIM (lengthens left strides)
  Curves left          → decrease _TRIM (lengthens right strides)
"""

import time

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

_FRAME_DELAY = 0.020  # seconds between frames — tune if sliding or unstable
_SQUEEZE = 1.0  # shoulder sweep compression around _MID; 1.0 = no compression
_MID = 30  # OpenCat balance pose shoulder angle
_TRIM = 9  # raw degrees added to left shoulders (FL + RL); tune to correct curve:
#   positive → longer left strides (corrects curving right)
#   negative → longer right strides (corrects curving left)

# Raw OpenCat angles from bkF in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    (38, 42, 36, 64, 2, -6, 3, -3),
    (36, 45, 34, 65, 3, -6, 3, -2),
    (34, 48, 32, 65, 3, -7, 4, 0),
    (32, 51, 30, 64, 4, -7, 5, 2),
    (30, 53, 28, 62, 5, -7, 6, 6),
    (28, 56, 25, 60, 6, -6, 9, 7),
    (26, 58, 25, 60, 7, -6, 8, 7),
    (24, 58, 26, 59, 8, -4, 4, 6),
    (21, 59, 28, 58, 10, -2, 2, 5),
    (19, 57, 31, 57, 11, 2, -1, 3),
    (18, 55, 32, 55, 12, 5, -3, 3),
    (15, 54, 35, 54, 14, 5, -4, 2),
    (16, 54, 39, 52, 12, 2, -5, 2),
    (17, 52, 42, 51, 9, 2, -6, 2),
    (20, 51, 45, 49, 3, 2, -6, 1),
    (21, 49, 48, 48, 3, 1, -7, 2),
    (25, 48, 51, 46, 1, 2, -7, 1),
    (28, 46, 53, 44, -1, 1, -7, 1),
    (31, 44, 56, 43, -2, 1, -6, 1),
    (35, 43, 58, 41, -4, 1, -6, 2),
    (38, 41, 60, 39, -5, 2, -5, 2),
    (41, 39, 62, 37, -6, 2, -4, 2),
    (44, 37, 64, 35, -6, 2, -3, 3),
    (47, 35, 65, 33, -7, 3, -2, 4),
    (50, 33, 65, 31, -7, 4, 1, 5),
    (52, 31, 63, 29, -7, 5, 4, 6),
    (55, 29, 61, 27, -6, 6, 8, 7),
    (57, 27, 60, 24, -6, 7, 7, 9),
    (58, 25, 59, 26, -4, 8, 6, 6),
    (59, 23, 58, 27, -4, 9, 5, 3),
    (58, 21, 57, 30, 0, 10, 4, -1),
    (57, 18, 56, 31, 2, 12, 3, -1),
    (54, 16, 54, 35, 5, 13, 3, -4),
    (54, 16, 53, 38, 3, 12, 2, -5),
    (53, 16, 52, 41, 2, 10, 2, -6),
    (52, 18, 50, 44, 2, 7, 1, -6),
    (50, 21, 49, 47, 1, 3, 1, -7),
    (49, 22, 47, 50, 1, 2, 1, -7),
    (47, 26, 45, 52, 1, 1, 1, -7),
    (45, 29, 44, 55, 1, -2, 1, -6),
    (44, 32, 42, 57, 1, -3, 1, -6),
    (42, 35, 40, 60, 1, -4, 2, -5),
    (40, 39, 38, 62, 2, -5, 2, -4),
)


def _to_commanded(raw):
    result = {}
    for i in range(8):
        r = raw[i]
        if i < 4:  # shoulder
            if _TRIM and i in (0, 3):  # FL and RL — left side
                r += _TRIM
            r = _MID + (r - _MID) * _SQUEEZE
        result[_CH[i]] = _ZERO[i] + _RD[i] * r  # keep float — int() at PWM level
    return result


def walk_back(steps=None):
    """
    Walk backwards (one foot at a time, 3-point support).

    Uses the OpenCat bkF (back walk fast) keyframe sequence.

    Args:
        steps: Number of full 43-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting walk back...")

    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for frame in _FRAMES:
                play_frame(_to_commanded(frame))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nWalk back interrupted.")

    print("Returning to stand...")
    stand()
