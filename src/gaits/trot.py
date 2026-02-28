"""
Trot Gait — ported from OpenCatEsp32 InstinctBittleESP.h (trF array).

48 frames per cycle. Frame data is a smooth trajectory computed by Petoi;
frames are played directly to servos (no software interpolation between them).

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = ZERO_POS + rotationDirection[joint] * opencat_angle
  ZERO_POS accounts for each joint's mechanical neutral (middleShift in OpenCat):
    FL_sh=65,  FR_sh=115, RR_sh=115, RL_sh=65
    FL_leg=80, FR_leg=100, RR_leg=100, RL_leg=80
  rotDir: FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
          FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

  Verified against OpenCat rest[] (shoulders=75, legs=-55) vs _REST_COMMANDED:
    FL_sh:  65 + 1*75  = 140 ✓   FR_sh:  115 + (-1)*75  = 40 ✓
    FL_leg: 80 + (-1)*(-55) = 135 ✓  FR_leg: 100 + 1*(-55) = 45 ✓

Tuning:
  Too fast / unstable → increase _FRAME_DELAY (e.g. 0.025)
  Too slow / shuffling → decrease _FRAME_DELAY (e.g. 0.015)
"""

import time
from poses import (play_frame, move_to, stand,
                   CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER, CH_RL_SHOULDER,
                   CH_FL_LEG, CH_FR_LEG, CH_RR_LEG, CH_RL_LEG)

# Gait array index → (channel, rotationDirection, zero_position)
_CH   = (CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER, CH_RL_SHOULDER,
         CH_FL_LEG,      CH_FR_LEG,      CH_RR_LEG,      CH_RL_LEG)
_RD   = (1, -1, -1, 1, -1, 1, 1, -1)
_ZERO = (65, 115, 115, 65, 80, 100, 100, 80)  # mechanical neutral per joint

_FRAME_DELAY = 0.012  # seconds between frames (~1.7 Hz cycle at 48 frames)

# Raw OpenCat angles from trF in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    ( 31,  35,  55,  61,   9,   0,  11,   2),
    ( 34,  32,  57,  60,   8,   0,  12,  -1),
    ( 36,  27,  58,  56,   8,   3,  14,  -3),
    ( 39,  21,  59,  52,   7,   5,  16,  -3),
    ( 41,  17,  59,  49,   9,   9,  20,  -4),
    ( 43,  11,  59,  44,   9,  13,  23,  -3),
    ( 45,   5,  60,  39,   9,  18,  26,  -3),
    ( 47,   4,  60,  38,   9,  19,  29,  -2),
    ( 49,   2,  60,  36,  10,  22,  32,   0),
    ( 51,   1,  60,  36,  11,  23,  37,   0),
    ( 52,  -1,  57,  35,  14,  26,  44,   2),
    ( 54,  -2,  59,  34,  12,  29,  43,   3),
    ( 54,  -2,  59,  33,  13,  30,  43,   6),
    ( 55,  -1,  60,  32,  11,  31,  41,   7),
    ( 58,  -1,  63,  34,   8,  31,  36,   7),
    ( 58,   2,  65,  36,   5,  27,  33,   6),
    ( 58,   6,  65,  39,   5,  24,  32,   6),
    ( 59,   9,  67,  42,   3,  21,  29,   5),
    ( 58,  13,  67,  44,   2,  18,  28,   5),
    ( 57,  16,  69,  47,  -1,  16,  20,   5),
    ( 53,  19,  68,  49,  -2,  13,  16,   6),
    ( 49,  21,  67,  50,  -2,  14,  11,   8),
    ( 45,  25,  66,  52,  -2,  12,   8,   9),
    ( 41,  28,  64,  54,  -1,  10,   5,  10),
    ( 35,  31,  61,  55,   0,   9,   2,  11),
    ( 32,  34,  60,  57,   0,   8,  -1,  12),
    ( 27,  36,  56,  58,   3,   8,  -3,  14),
    ( 21,  39,  52,  59,   5,   7,  -3,  16),
    ( 17,  41,  49,  59,   9,   9,  -4,  20),
    ( 11,  43,  44,  59,  13,   9,  -3,  23),
    (  5,  45,  39,  60,  18,   9,  -3,  26),
    (  4,  47,  38,  60,  19,   9,  -2,  29),
    (  2,  49,  36,  60,  22,  10,   0,  32),
    (  1,  51,  36,  60,  23,  11,   0,  37),
    ( -1,  52,  35,  57,  26,  14,   2,  44),
    ( -2,  54,  34,  59,  29,  12,   3,  43),
    ( -2,  54,  33,  59,  30,  13,   6,  43),
    ( -1,  55,  32,  60,  31,  11,   7,  41),
    ( -1,  58,  34,  63,  31,   8,   7,  36),
    (  2,  58,  36,  65,  27,   5,   6,  33),
    (  6,  58,  39,  65,  24,   5,   6,  32),
    (  9,  59,  42,  67,  21,   3,   5,  29),
    ( 13,  58,  44,  67,  18,   2,   5,  28),
    ( 16,  57,  47,  69,  16,  -1,   5,  20),
    ( 19,  53,  49,  68,  13,  -2,   6,  16),
    ( 21,  49,  50,  67,  14,  -2,   8,  11),
    ( 25,  45,  52,  66,  12,  -2,   9,   8),
    ( 28,  41,  54,  64,  10,  -1,  10,   5),
)


def _to_commanded(raw):
    return {_CH[i]: _ZERO[i] + _RD[i] * raw[i] for i in range(8)}  # float, no int()


def trot(steps=None):
    """
    Trot gait.

    Args:
        steps: Number of full 48-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting trot...")

    # Smooth entry from stand to first gait frame
    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for raw in _FRAMES:
                play_frame(_to_commanded(raw))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nTrot interrupted.")

    print("Returning to stand...")
    stand()
