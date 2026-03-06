"""Turn Left / Turn Right Gaits — ported from OpenCatEsp32 InstinctBittleESP.h (wkL array).

116 frames per cycle. Crawl-style walk-left: one foot at a time, three feet always grounded.
The body walks diagonally to the left rather than pivoting in place. This is the same stable
3-point support pattern as wkF and bkF, adapted for leftward lateral movement.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = ZERO_POS + rotationDirection[joint] * opencat_angle
  ZERO_POS: FL_sh=65, FR_sh=115, RR_sh=115, RL_sh=65
            FL_leg=80, FR_leg=100, RR_leg=100, RL_leg=80
  rotDir:   FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
            FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Right turn: L/R column pairs are swapped before conversion:
  Index 0 (FL_sh) <-> 1 (FR_sh)
  Index 2 (RR_sh) <-> 3 (RL_sh)
  Index 4 (FL_leg) <-> 5 (FR_leg)
  Index 6 (RR_leg) <-> 7 (RL_leg)

Tuning:
  Too fast / unstable  -> increase _FRAME_DELAY (e.g. 0.025)
  Too slow / shuffling -> decrease _FRAME_DELAY (e.g. 0.012)
"""

import time
from poses import (play_frame, move_to, stand,
                   CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER, CH_RL_SHOULDER,
                   CH_FL_LEG, CH_FR_LEG, CH_RR_LEG, CH_RL_LEG)

# Gait array index -> (channel, rotationDirection, zero_position)
_CH   = (CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER, CH_RL_SHOULDER,
         CH_FL_LEG,      CH_FR_LEG,      CH_RR_LEG,      CH_RL_LEG)
_RD   = (1, -1, -1, 1, -1, 1, 1, -1)
_ZERO = (65, 115, 115, 65, 80, 100, 100, 80)  # mechanical neutral per joint

_FRAME_DELAY = 0.016  # seconds between frames — tune if unstable

# Raw OpenCat angles from wkL in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
# Same crawl structure as wkF — one foot at a time, 3-point support.
_FRAMES = (
    ( 49,  58,  61,  52,  -4,   8,  -7,   0),
    ( 48,  59,  60,  52,  -4,   8,  -7,   0),
    ( 48,  59,  57,  52,  -4,   9,  -8,   0),
    ( 46,  60,  56,  52,  -2,   9,  -8,   0),
    ( 46,  60,  54,  54,  -2,  10,  -9,   0),
    ( 45,  60,  51,  54,   0,  11,  -7,   0),
    ( 45,  61,  49,  54,   0,  11,  -7,   0),
    ( 46,  61,  47,  54,   0,  12,  -7,   1),
    ( 46,  61,  44,  54,   0,  13,  -6,   1),
    ( 46,  62,  42,  54,   0,  13,  -6,   1),
    ( 46,  62,  40,  55,   0,  14,  -5,   1),
    ( 47,  62,  36,  55,   0,  15,  -4,   1),
    ( 47,  63,  35,  55,   0,  15,  -4,   1),
    ( 47,  63,  31,  55,   0,  16,  -2,   1),
    ( 48,  63,  30,  55,   0,  17,  -1,   1),
    ( 48,  64,  28,  55,   0,  18,   0,   1),
    ( 48,  64,  26,  56,   0,  19,   3,   1),
    ( 49,  64,  24,  56,   0,  20,   5,   1),
    ( 49,  64,  24,  56,   0,  21,   7,   1),
    ( 49,  64,  22,  57,   0,  22,  11,   2),
    ( 49,  64,  22,  57,   0,  23,  12,   2),
    ( 49,  63,  24,  57,   0,  26,  11,   2),
    ( 49,  63,  24,  58,   0,  27,  11,   2),
    ( 50,  64,  25,  58,   0,  26,   9,   2),
    ( 50,  66,  26,  58,   0,  24,   8,   2),
    ( 50,  69,  27,  58,   0,  20,   8,   2),
    ( 51,  70,  28,  58,   0,  18,   8,   2),
    ( 51,  71,  29,  58,   0,  14,   7,   2),
    ( 51,  71,  30,  59,   0,  13,   6,   3),
    ( 52,  71,  32,  59,   0,  13,   6,   3),
    ( 52,  71,  32,  59,   0,  10,   6,   3),
    ( 52,  71,  33,  59,   0,   8,   6,   3),
    ( 52,  70,  35,  59,   0,   6,   5,   3),
    ( 52,  70,  35,  59,   0,   3,   5,   3),
    ( 52,  69,  36,  60,   0,   2,   5,   4),
    ( 54,  68,  37,  60,   0,   0,   4,   4),
    ( 54,  67,  38,  60,   0,  -1,   4,   5),
    ( 54,  65,  39,  61,   0,  -2,   3,   5),
    ( 54,  64,  40,  61,   1,  -3,   3,   5),
    ( 54,  64,  41,  61,   1,  -6,   3,   5),
    ( 54,  62,  42,  62,   1,  -6,   3,   3),
    ( 55,  60,  42,  62,   1,  -7,   3,   2),
    ( 55,  58,  43,  62,   1,  -8,   3,   1),
    ( 55,  56,  44,  62,   1,  -8,   3,   1),
    ( 55,  54,  45,  62,   1,  -9,   3,   1),
    ( 55,  52,  46,  62,   1,  -9,   3,   1),
    ( 55,  49,  47,  62,   1,  -9,   3,   0),
    ( 56,  48,  48,  61,   1,  -9,   3,   0),
    ( 56,  45,  48,  61,   1,  -8,   4,  -1),
    ( 56,  43,  49,  60,   1,  -9,   3,  -1),
    ( 57,  41,  50,  60,   2,  -9,   4,  -1),
    ( 57,  39,  51,  60,   2,  -8,   3,  -1),
    ( 57,  36,  51,  59,   2,  -7,   4,  -2),
    ( 58,  34,  52,  58,   2,  -6,   4,  -2),
    ( 58,  31,  52,  58,   2,  -5,   5,  -2),
    ( 58,  28,  54,  58,   2,  -4,   5,  -2),
    ( 58,  26,  54,  57,   2,  -2,   5,  -2),
    ( 58,  22,  55,  56,   2,   0,   5,  -3),
    ( 58,  21,  57,  55,   2,   1,   3,  -3),
    ( 59,  20,  57,  55,   3,   2,   4,  -3),
    ( 59,  18,  58,  55,   3,   4,   5,  -3),
    ( 59,  17,  58,  54,   3,   6,   5,  -3),
    ( 59,  15,  59,  53,   3,  10,   6,  -3),
    ( 59,  14,  59,  52,   3,  12,   6,  -3),
    ( 59,  13,  60,  51,   3,  14,   7,  -4),
    ( 60,  15,  60,  51,   4,  14,   7,  -4),
    ( 60,  15,  61,  51,   4,  14,   8,  -4),
    ( 60,  16,  61,  50,   4,  13,   8,  -4),
    ( 60,  18,  62,  49,   5,  12,   9,  -4),
    ( 60,  18,  62,  48,   5,  12,  10,  -4),
    ( 60,  19,  62,  47,   5,  11,  10,  -4),
    ( 61,  21,  63,  47,   5,  10,  11,  -4),
    ( 61,  21,  63,  46,   5,  10,  12,  -4),
    ( 61,  23,  64,  44,   5,   9,  12,  -2),
    ( 61,  24,  64,  44,   5,   8,  13,  -2),
    ( 61,  25,  64,  43,   5,   8,  14,  -2),
    ( 61,  26,  64,  43,   5,   7,  15,   0),
    ( 62,  27,  65,  43,   6,   7,  15,   0),
    ( 62,  28,  65,  43,   6,   6,  16,   0),
    ( 61,  29,  65,  42,   8,   6,  17,   1),
    ( 61,  30,  65,  42,   8,   5,  18,   1),
    ( 61,  31,  65,  42,   8,   5,  19,   1),
    ( 62,  32,  66,  42,   6,   4,  20,   1),
    ( 62,  33,  65,  42,   6,   4,  21,   1),
    ( 62,  34,  65,  44,   6,   3,  22,   0),
    ( 64,  35,  65,  44,   5,   3,  24,   0),
    ( 63,  36,  66,  44,   4,   3,  24,   0),
    ( 63,  37,  65,  44,   4,   2,  26,   0),
    ( 63,  38,  65,  44,   4,   2,  27,   0),
    ( 64,  39,  65,  44,   2,   2,  28,   0),
    ( 63,  40,  66,  45,   1,   2,  29,   0),
    ( 62,  41,  65,  45,   1,   2,  31,   0),
    ( 62,  42,  65,  45,   1,   1,  32,   0),
    ( 62,  43,  65,  46,   0,   1,  33,   0),
    ( 61,  44,  66,  46,   0,   1,  33,   0),
    ( 61,  44,  67,  46,  -1,   1,  33,   0),
    ( 61,  45,  69,  47,  -1,   1,  31,   0),
    ( 60,  46,  70,  47,  -1,   1,  29,   0),
    ( 60,  47,  73,  47,  -1,   1,  22,   0),
    ( 59,  48,  73,  48,  -2,   2,  21,   0),
    ( 58,  49,  75,  48,  -2,   1,  18,   0),
    ( 58,  49,  75,  48,  -2,   1,  18,   0),
    ( 58,  49,  75,  49,  -2,   3,  16,   0),
    ( 57,  50,  75,  49,  -2,   4,  13,   0),
    ( 56,  51,  75,  49,  -3,   3,  10,   0),
    ( 56,  51,  74,  49,  -3,   4,   8,   0),
    ( 55,  52,  74,  49,  -3,   4,   7,   0),
    ( 55,  52,  73,  49,  -3,   5,   3,   0),
    ( 54,  54,  73,  50,  -3,   5,   2,   0),
    ( 53,  54,  72,  50,  -3,   5,   1,   0),
    ( 53,  55,  71,  50,  -3,   5,  -2,   0),
    ( 52,  55,  68,  51,  -3,   6,  -1,   0),
    ( 51,  56,  67,  51,  -4,   6,  -2,   0),
    ( 51,  56,  66,  51,  -4,   6,  -4,   0),
    ( 51,  57,  65,  52,  -4,   7,  -5,   0),
    ( 50,  58,  63,  52,  -4,   8,  -6,   0),
)


def _to_commanded(raw):
    result = {}
    for i in range(8):
        result[_CH[i]] = _ZERO[i] + _RD[i] * raw[i]
    return result


def _mirror(frame):
    """Swap L/R column pairs for right turn."""
    f = frame
    return (f[1], f[0], f[3], f[2], f[5], f[4], f[7], f[6])


def turn_left(steps=None):
    """
    Turn left (116-frame crawl cycle, 3-point support).

    Args:
        steps: Number of full 116-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting turn left...")

    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for i in range(0, len(_FRAMES), 2):  # every 2nd frame → larger steps, above servo deadband
                play_frame(_to_commanded(_FRAMES[i]))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nTurn left interrupted.")

    print("Returning to stand...")
    stand()


def turn_right(steps=None):
    """
    Turn right (116-frame crawl cycle, L/R mirrored from wkL).

    Args:
        steps: Number of full 116-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting turn right...")

    move_to(_to_commanded(_mirror(_FRAMES[0])), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for i in range(0, len(_FRAMES), 2):  # every 2nd frame → larger steps, above servo deadband
                play_frame(_to_commanded(_mirror(_FRAMES[i])))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nTurn right interrupted.")

    print("Returning to stand...")
    stand()
