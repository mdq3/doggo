"""
Crawl Left / Crawl Right Turn Gaits — ported from OpenCatEsp32
InstinctBittleESP.h (crL array).

103 frames per cycle. Low-stance crawl that arcs to the side — the turning
counterpart of gaits/crawl.py. Right turn = L/R column-pair mirror of crL.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = 90 + rotationDirection[joint] * opencat_angle
  rotDir: FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
          FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Right turn: L/R column pairs are swapped before conversion:
  Index 0 (FL_sh) <-> 1 (FR_sh)
  Index 2 (RR_sh) <-> 3 (RL_sh)
  Index 4 (FL_leg) <-> 5 (FR_leg)
  Index 6 (RR_leg) <-> 7 (RL_leg)

Tuning:
  Too fast / unstable  -> increase _FRAME_DELAY (e.g. 0.024)
  Too slow / shuffling -> decrease _FRAME_DELAY (e.g. 0.012)
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

_FRAME_DELAY = 0.016  # seconds between frames — tune if sliding or unstable

# Raw OpenCat angles from crL in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    (63, 84, 85, 70, -47, -43, -52, -45),
    (63, 85, 83, 70, -47, -42, -52, -45),
    (62, 87, 80, 72, -47, -42, -52, -45),
    (62, 88, 78, 72, -47, -42, -52, -45),
    (60, 89, 74, 72, -47, -41, -52, -45),
    (60, 90, 72, 74, -47, -41, -52, -45),
    (60, 91, 70, 74, -47, -40, -52, -45),
    (58, 93, 67, 74, -45, -40, -52, -45),
    (58, 93, 65, 75, -45, -39, -52, -45),
    (58, 94, 63, 75, -45, -39, -51, -45),
    (58, 95, 59, 75, -45, -38, -51, -45),
    (58, 96, 57, 77, -45, -38, -50, -45),
    (57, 96, 53, 77, -44, -36, -49, -45),
    (57, 97, 51, 77, -44, -36, -48, -45),
    (57, 97, 49, 78, -44, -36, -48, -45),
    (57, 99, 46, 78, -44, -37, -47, -45),
    (59, 100, 44, 78, -44, -38, -46, -45),
    (59, 102, 41, 80, -44, -40, -44, -45),
    (59, 102, 39, 80, -44, -42, -43, -45),
    (61, 102, 37, 80, -45, -42, -41, -45),
    (61, 103, 36, 82, -45, -43, -40, -45),
    (61, 102, 36, 82, -45, -44, -40, -45),
    (62, 102, 36, 82, -45, -46, -38, -45),
    (62, 101, 36, 83, -45, -46, -37, -45),
    (62, 99, 36, 83, -45, -47, -36, -45),
    (64, 98, 37, 83, -45, -48, -36, -45),
    (64, 97, 37, 84, -45, -48, -36, -44),
    (64, 94, 39, 84, -45, -50, -38, -44),
    (65, 93, 41, 85, -45, -50, -38, -44),
    (65, 90, 42, 87, -45, -51, -39, -45),
    (65, 88, 44, 87, -45, -51, -39, -45),
    (67, 87, 45, 87, -45, -52, -40, -45),
    (67, 83, 47, 87, -45, -52, -40, -47),
    (67, 81, 49, 87, -45, -52, -41, -47),
    (69, 80, 50, 86, -45, -52, -41, -47),
    (69, 76, 52, 86, -45, -52, -42, -47),
    (69, 74, 54, 86, -45, -52, -42, -47),
    (70, 70, 55, 86, -45, -52, -42, -47),
    (70, 69, 57, 85, -45, -52, -43, -47),
    (70, 67, 58, 85, -45, -52, -43, -47),
    (72, 63, 60, 83, -45, -51, -43, -47),
    (72, 61, 62, 83, -45, -51, -44, -47),
    (72, 57, 64, 82, -45, -50, -44, -48),
    (74, 55, 65, 82, -45, -50, -44, -48),
    (74, 53, 67, 80, -45, -49, -44, -48),
    (74, 49, 68, 80, -45, -48, -44, -48),
    (75, 48, 70, 79, -45, -47, -44, -48),
    (75, 46, 71, 79, -45, -47, -44, -48),
    (75, 42, 73, 77, -45, -46, -44, -48),
    (77, 41, 75, 77, -45, -45, -44, -48),
    (77, 37, 76, 76, -45, -44, -44, -48),
    (77, 35, 78, 76, -45, -43, -44, -48),
    (78, 34, 79, 74, -45, -42, -44, -48),
    (78, 30, 80, 74, -45, -41, -44, -48),
    (78, 29, 81, 74, -45, -40, -43, -48),
    (80, 26, 83, 72, -45, -38, -43, -48),
    (80, 24, 84, 72, -45, -36, -43, -48),
    (80, 23, 85, 71, -45, -35, -42, -48),
    (82, 22, 87, 71, -45, -33, -42, -48),
    (82, 22, 88, 68, -45, -33, -42, -48),
    (82, 22, 89, 68, -45, -32, -41, -48),
    (83, 22, 90, 67, -45, -31, -41, -48),
    (83, 22, 91, 67, -45, -30, -40, -48),
    (83, 23, 93, 65, -45, -29, -40, -47),
    (84, 24, 93, 65, -44, -30, -39, -47),
    (84, 25, 94, 63, -44, -31, -39, -47),
    (85, 27, 95, 63, -44, -32, -38, -47),
    (85, 28, 96, 62, -44, -33, -38, -47),
    (85, 30, 97, 62, -44, -33, -37, -47),
    (87, 31, 97, 60, -45, -34, -36, -47),
    (87, 33, 98, 60, -45, -35, -36, -47),
    (87, 34, 99, 60, -45, -36, -35, -46),
    (85, 36, 99, 58, -46, -36, -34, -45),
    (85, 37, 100, 58, -46, -37, -33, -45),
    (85, 39, 101, 58, -46, -38, -33, -45),
    (85, 41, 101, 57, -46, -38, -32, -44),
    (85, 42, 101, 57, -47, -39, -31, -44),
    (85, 44, 102, 57, -47, -39, -30, -44),
    (83, 45, 103, 57, -47, -40, -29, -44),
    (83, 47, 104, 57, -47, -40, -30, -44),
    (82, 49, 105, 57, -48, -41, -31, -44),
    (82, 50, 107, 59, -48, -41, -32, -44),
    (80, 52, 108, 59, -48, -42, -33, -44),
    (80, 54, 109, 59, -48, -42, -35, -44),
    (79, 55, 109, 61, -48, -42, -36, -45),
    (79, 57, 108, 61, -48, -43, -37, -45),
    (77, 58, 110, 61, -48, -43, -38, -45),
    (77, 60, 109, 62, -48, -43, -39, -45),
    (76, 62, 109, 62, -48, -44, -40, -45),
    (76, 64, 107, 62, -48, -44, -41, -45),
    (74, 65, 107, 64, -48, -44, -42, -45),
    (74, 67, 106, 64, -48, -44, -43, -45),
    (74, 68, 104, 64, -48, -44, -44, -45),
    (72, 70, 104, 65, -48, -44, -45, -45),
    (72, 71, 101, 65, -48, -44, -46, -45),
    (71, 73, 101, 65, -48, -44, -47, -45),
    (71, 75, 99, 67, -48, -44, -47, -45),
    (68, 76, 97, 67, -48, -44, -48, -45),
    (68, 78, 96, 67, -48, -44, -50, -45),
    (67, 79, 94, 69, -48, -44, -50, -45),
    (67, 80, 91, 69, -48, -44, -51, -45),
    (65, 81, 90, 69, -47, -43, -51, -45),
    (65, 83, 87, 70, -47, -43, -52, -45),
)


def _to_commanded(raw):
    result = {}
    for i in range(8):
        result[_CH[i]] = 90 + _RD[i] * raw[i]
    return result


def _mirror(frame):
    """Swap L/R column pairs for right turn."""
    f = frame
    return (f[1], f[0], f[3], f[2], f[5], f[4], f[7], f[6])


def _run(steps, transform, label):
    print("\nStarting crawl " + label + "...")

    move_to(_to_commanded(transform(_FRAMES[0])), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for frame in _FRAMES:
                play_frame(_to_commanded(transform(frame)))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nCrawl " + label + " interrupted.")

    print("Returning to stand...")
    stand()


def crawl_left(steps=None):
    """
    Crawl in a leftward arc (103-frame cycle, low stance).

    Args:
        steps: Number of full 103-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    _run(steps, lambda f: f, "left")


def crawl_right(steps=None):
    """
    Crawl in a rightward arc (103-frame cycle, L/R mirrored from crL).

    Args:
        steps: Number of full 103-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    _run(steps, _mirror, "right")
