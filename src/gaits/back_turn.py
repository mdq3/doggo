"""
Walk Back Left / Walk Back Right Gaits — ported from OpenCatEsp32
InstinctBittleESP.h (bkL array).

48 frames per cycle. Backward walk that arcs to the side — the steering
counterpart of gaits/walk_back.py. Like bkF, this is a purpose-built backward
sequence, not a reversed forward gait. Right turn = L/R column-pair mirror.

Naming note: bkL arcs the rear of the robot to the LEFT while reversing
(the OpenCat convention), i.e. the robot backs up and to its left.

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
  Too fast / unstable  -> increase _FRAME_DELAY (e.g. 0.026)
  Too slow / shuffling -> decrease _FRAME_DELAY (e.g. 0.014)
"""

from gaits.player import play

_FRAME_DELAY = 0.020  # seconds between frames — matches walk_back; tune if sliding

# Raw OpenCat angles from bkL in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    (47, 57, 49, 57, -5, -19, -2, -12),
    (46, 60, 47, 58, -5, -19, -2, -11),
    (45, 64, 45, 58, -5, -18, -2, -11),
    (45, 67, 43, 60, -5, -18, -2, -11),
    (44, 70, 42, 61, -5, -17, -2, -11),
    (43, 72, 39, 62, -5, -16, -1, -10),
    (43, 74, 38, 63, -5, -14, -1, -10),
    (42, 74, 35, 64, -4, -11, 0, -10),
    (41, 75, 34, 63, -4, -8, 1, -8),
    (41, 72, 32, 62, -4, -3, 1, -6),
    (40, 69, 29, 62, -4, 2, 2, -4),
    (39, 66, 27, 61, -4, 5, 3, -5),
    (38, 64, 25, 60, -3, 5, 5, -3),
    (38, 63, 22, 60, -5, 4, 5, -3),
    (36, 62, 22, 59, -4, 3, 2, -4),
    (38, 61, 24, 58, -6, 2, -2, -4),
    (39, 60, 27, 58, -8, 1, -7, -4),
    (41, 58, 31, 58, -10, 1, -11, -4),
    (42, 57, 34, 57, -10, 0, -14, -4),
    (43, 56, 38, 57, -10, -1, -15, -4),
    (44, 54, 41, 56, -11, -1, -17, -4),
    (45, 53, 46, 56, -11, -2, -18, -5),
    (46, 51, 50, 56, -11, -2, -19, -5),
    (47, 49, 54, 55, -11, -2, -19, -5),
    (48, 48, 57, 54, -11, -2, -19, -5),
    (49, 46, 60, 54, -12, -2, -19, -5),
    (50, 44, 64, 53, -12, -2, -18, -5),
    (51, 42, 67, 52, -12, -2, -18, -5),
    (53, 41, 70, 52, -12, -1, -17, -5),
    (54, 39, 72, 52, -12, -1, -16, -5),
    (55, 36, 74, 51, -12, 0, -14, -5),
    (56, 35, 74, 51, -12, 0, -11, -5),
    (56, 32, 75, 50, -10, 1, -8, -5),
    (55, 30, 72, 49, -9, 2, -3, -5),
    (54, 28, 69, 49, -7, 3, 2, -5),
    (54, 26, 66, 48, -7, 4, 5, -5),
    (53, 24, 64, 46, -5, 5, 5, -5),
    (53, 22, 63, 47, -5, 4, 4, -7),
    (52, 23, 62, 48, -5, 1, 3, -9),
    (52, 26, 61, 48, -5, -5, 2, -10),
    (52, 29, 60, 50, -5, -9, 1, -12),
    (51, 33, 58, 51, -5, -13, 1, -12),
    (50, 35, 57, 51, -5, -15, 0, -12),
    (50, 40, 56, 52, -5, -16, -1, -12),
    (49, 44, 54, 53, -5, -17, -1, -12),
    (48, 48, 53, 54, -5, -18, -2, -12),
    (48, 52, 51, 55, -5, -19, -2, -12),
    (47, 55, 49, 57, -5, -19, -2, -12),
)


def walk_back_left(steps=None):
    """
    Walk backward arcing left (48-frame cycle).

    Args:
        steps: Number of full 48-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    play(_FRAMES, _FRAME_DELAY, steps, name="walk back left")


def walk_back_right(steps=None):
    """
    Walk backward arcing right (48-frame cycle, L/R mirrored from bkL).

    Args:
        steps: Number of full 48-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    play(_FRAMES, _FRAME_DELAY, steps, mirror_lr=True, name="walk back right")
