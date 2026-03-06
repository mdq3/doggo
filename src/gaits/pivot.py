"""Pivot Left / Pivot Right Gaits — ported from OpenCatEsp32 InstinctBittleESP.h (vtL array).

72 frames per cycle. Crawl-style in-place pivot: one foot at a time, three feet always grounded.
Unlike wkL (which arcs the body diagonally), vtL rotates the robot in place.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = ZERO_POS + rotationDirection[joint] * opencat_angle
  ZERO_POS: FL_sh=65, FR_sh=115, RR_sh=115, RL_sh=65
            FL_leg=80, FR_leg=100, RR_leg=100, RL_leg=80
  rotDir:   FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
            FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Leg values are capped at _LEG_CAP to prevent extreme servo positions. vtL has leg values
up to raw=46 which maps to commanded=146° (FR_leg: 100 + 1*46) or 34° (FL_leg: 80 + -1*46),
causing servo overextension and CoM shifts that topple the robot.

Right pivot: L/R column pairs are swapped before conversion:
  Index 0 (FL_sh) <-> 1 (FR_sh)
  Index 2 (RR_sh) <-> 3 (RL_sh)
  Index 4 (FL_leg) <-> 5 (FR_leg)
  Index 6 (RR_leg) <-> 7 (RL_leg)

Tuning:
  Falls backward      -> reduce _SHOULDER_CAP (e.g. 30) or make _LEG_OFFSET more negative
  Legs too bent       -> make _LEG_OFFSET more negative (e.g. -25)
  Legs too extended   -> make _LEG_OFFSET less negative (e.g. -15)
  Shuffles / no pivot -> raise _SHOULDER_CAP (e.g. 40) for more rotation
  Too slow            -> decrease _FRAME_DELAY (e.g. 0.020)
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

# Gait array index -> (channel, rotationDirection, zero_position)
_CH   = (CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER, CH_RL_SHOULDER,
         CH_FL_LEG,      CH_FR_LEG,      CH_RR_LEG,      CH_RL_LEG)
_RD   = (1, -1, -1, 1, -1, 1, 1, -1)
_ZERO = (65, 115, 115, 65, 80, 100, 100, 80)  # mechanical neutral per joint

_FRAME_DELAY = 0.025   # seconds between frames — tune if unstable
_SHOULDER_CAP = 35     # cap raw shoulder excursion; prevents rear foot tucking too far forward
_LEG_OFFSET = -20      # shift vtL legs toward standing neutral (vtL is all-positive = crouched)
_LEG_CAP = 20          # cap raw leg excursion after offset is applied

# Raw OpenCat angles from vtL in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
# Crawl-style in-place pivot: one foot lifted at a time, 3-point support.
_FRAMES = (
    ( 29,  26,  29,  26,  27,  22,  27,  22),
    ( 28,  26,  30,  26,  27,  21,  27,  24),
    ( 27,  26,  31,  25,  28,  22,  28,  25),
    ( 26,  26,  33,  24,  29,  23,  30,  26),
    ( 26,  25,  33,  23,  30,  24,  30,  27),
    ( 26,  25,  35,  23,  30,  25,  31,  27),
    ( 25,  25,  36,  23,  31,  24,  31,  27),
    ( 24,  25,  37,  24,  32,  22,  30,  26),
    ( 23,  25,  38,  24,  33,  22,  28,  26),
    ( 22,  25,  39,  26,  34,  20,  26,  24),
    ( 20,  23,  41,  29,  35,  21,  24,  20),
    ( 19,  20,  43,  31,  37,  23,  24,  17),
    ( 17,  17,  43,  34,  39,  27,  24,  14),
    ( 17,  13,  44,  37,  39,  31,  24,  12),
    ( 16,  11,  46,  39,  41,  35,  24,  13),
    ( 14,  10,  46,  42,  42,  38,  24,  16),
    ( 13,  10,  46,  42,  42,  38,  24,  16),
    ( 11,  10,  45,  44,  41,  39,  23,  20),
    ( 10,  10,  44,  45,  40,  40,  20,  23),
    ( 10,  11,  42,  46,  39,  41,  16,  24),
    ( 10,  13,  42,  46,  38,  42,  16,  24),
    ( 10,  14,  39,  46,  38,  42,  13,  24),
    ( 11,  16,  37,  44,  35,  41,  12,  24),
    ( 13,  17,  34,  43,  31,  39,  14,  24),
    ( 17,  17,  31,  43,  27,  39,  17,  24),
    ( 20,  19,  29,  41,  23,  37,  20,  24),
    ( 23,  20,  26,  39,  21,  35,  24,  26),
    ( 25,  22,  24,  38,  20,  34,  26,  28),
    ( 25,  23,  24,  37,  22,  33,  26,  30),
    ( 25,  24,  23,  36,  22,  32,  27,  31),
    ( 25,  25,  23,  35,  24,  31,  27,  31),
    ( 25,  26,  23,  33,  25,  30,  27,  30),
    ( 25,  26,  24,  33,  24,  30,  26,  30),
    ( 26,  26,  25,  31,  23,  29,  25,  28),
    ( 26,  27,  26,  30,  22,  28,  24,  27),
    ( 26,  28,  26,  29,  21,  27,  22,  27),
    ( 26,  29,  26,  28,  22,  27,  21,  27),
    ( 26,  30,  26,  27,  24,  27,  22,  28),
    ( 25,  31,  26,  26,  25,  28,  23,  29),
    ( 24,  33,  25,  26,  26,  30,  24,  30),
    ( 23,  33,  25,  26,  27,  30,  25,  30),
    ( 23,  35,  25,  25,  27,  31,  24,  31),
    ( 23,  36,  25,  24,  27,  31,  22,  32),
    ( 24,  37,  25,  23,  26,  30,  22,  33),
    ( 24,  38,  25,  22,  26,  28,  20,  34),
    ( 26,  39,  23,  20,  24,  26,  21,  35),
    ( 29,  41,  20,  19,  20,  24,  23,  37),
    ( 31,  43,  17,  17,  17,  24,  27,  39),
    ( 34,  43,  13,  17,  14,  24,  31,  39),
    ( 37,  44,  11,  16,  12,  24,  35,  41),
    ( 39,  46,  10,  14,  13,  24,  38,  42),
    ( 42,  46,  10,  13,  16,  24,  38,  42),
    ( 42,  46,  10,  11,  16,  24,  39,  41),
    ( 44,  45,  10,  10,  20,  23,  40,  40),
    ( 45,  44,  11,  10,  23,  20,  41,  39),
    ( 46,  42,  13,  10,  24,  16,  42,  38),
    ( 46,  42,  14,  10,  24,  16,  42,  38),
    ( 46,  39,  16,  11,  24,  13,  41,  35),
    ( 44,  37,  17,  13,  24,  12,  39,  31),
    ( 43,  34,  17,  17,  24,  14,  39,  27),
    ( 43,  31,  19,  20,  24,  17,  37,  23),
    ( 41,  29,  20,  23,  24,  20,  35,  21),
    ( 39,  26,  22,  25,  26,  24,  34,  20),
    ( 38,  24,  23,  25,  28,  26,  33,  22),
    ( 37,  24,  24,  25,  30,  26,  32,  22),
    ( 36,  23,  25,  25,  31,  27,  31,  24),
    ( 35,  23,  26,  25,  31,  27,  30,  25),
    ( 33,  23,  26,  25,  30,  27,  30,  24),
    ( 33,  24,  26,  26,  30,  26,  29,  23),
    ( 31,  25,  27,  26,  28,  25,  28,  22),
    ( 30,  26,  28,  26,  27,  24,  27,  21),
    ( 29,  26,  29,  26,  27,  22,  27,  22),
)


def _to_commanded(raw):
    result = {}
    for i in range(8):
        r = raw[i]
        if i < 4:           # shoulder joints
            r = min(r, _SHOULDER_CAP)
        else:               # leg joints: shift toward standing neutral then cap
            r = min(r + _LEG_OFFSET, _LEG_CAP)
        result[_CH[i]] = _ZERO[i] + _RD[i] * r
    return result


def _mirror(frame):
    """Swap L/R column pairs for right pivot."""
    f = frame
    return (f[1], f[0], f[3], f[2], f[5], f[4], f[7], f[6])


def pivot_left(steps=None):
    """
    Pivot left in place (72-frame crawl cycle, 3-point support).

    Args:
        steps: Number of full 72-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting pivot left...")

    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for frame in _FRAMES:
                play_frame(_to_commanded(frame))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nPivot left interrupted.")

    print("Returning to stand...")
    stand()


def pivot_right(steps=None):
    """
    Pivot right in place (72-frame crawl cycle, L/R mirrored from vtL).

    Args:
        steps: Number of full 72-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    print("\nStarting pivot right...")

    move_to(_to_commanded(_mirror(_FRAMES[0])), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for frame in _FRAMES:
                play_frame(_to_commanded(_mirror(frame)))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nPivot right interrupted.")

    print("Returning to stand...")
    stand()
