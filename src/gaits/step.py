"""
Step-In-Place Gait — ported from OpenCatEsp32 InstinctBittleESP.h (vtF array).

37 frames per cycle. Marching on the spot: diagonal legs alternate lifting
while the body stays in place. Same vt family as the pivot gait, but with no
net rotation or translation.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = 90 + rotationDirection[joint] * opencat_angle
  rotDir: FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
          FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Tuning:
  Too fast / unstable  → increase _FRAME_DELAY (e.g. 0.020)
  Too slow / shuffling → decrease _FRAME_DELAY (e.g. 0.010)
"""

from gaits.player import play

_FRAME_DELAY = 0.014  # seconds between frames — tune if unstable

# Raw OpenCat angles from vtF in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
_FRAMES = (
    (48, 39, 63, 52, -10, 7, -8, 9),
    (46, 39, 61, 52, -6, 7, -5, 9),
    (44, 39, 59, 52, -3, 7, -2, 9),
    (43, 39, 57, 52, 0, 7, 2, 9),
    (41, 39, 55, 52, 3, 7, 5, 9),
    (39, 41, 52, 55, 7, 3, 9, 5),
    (39, 43, 52, 57, 7, 0, 9, 2),
    (39, 44, 52, 59, 7, -3, 9, -2),
    (39, 46, 52, 61, 7, -6, 9, -5),
    (39, 48, 52, 63, 7, -10, 9, -8),
    (39, 49, 52, 65, 7, -13, 9, -11),
    (39, 51, 52, 67, 7, -16, 9, -14),
    (39, 52, 52, 69, 7, -19, 9, -17),
    (39, 53, 52, 72, 7, -22, 9, -20),
    (39, 53, 52, 72, 7, -22, 9, -20),
    (39, 52, 52, 69, 7, -19, 9, -17),
    (39, 51, 52, 67, 7, -16, 9, -14),
    (39, 49, 52, 65, 7, -13, 9, -11),
    (39, 48, 52, 63, 7, -10, 9, -8),
    (39, 46, 52, 61, 7, -6, 9, -5),
    (39, 44, 52, 59, 7, -3, 9, -2),
    (39, 43, 52, 57, 7, 0, 9, 2),
    (39, 41, 52, 55, 7, 3, 9, 5),
    (39, 39, 52, 52, 7, 7, 9, 9),
    (41, 39, 55, 52, 3, 7, 5, 9),
    (43, 39, 57, 52, 0, 7, 2, 9),
    (44, 39, 59, 52, -3, 7, -2, 9),
    (46, 39, 61, 52, -6, 7, -5, 9),
    (48, 39, 63, 52, -10, 7, -8, 9),
    (49, 39, 65, 52, -13, 7, -11, 9),
    (51, 39, 67, 52, -16, 7, -14, 9),
    (52, 39, 69, 52, -19, 7, -17, 9),
    (53, 39, 72, 52, -22, 7, -20, 9),
    (53, 39, 72, 52, -22, 7, -20, 9),
    (52, 39, 69, 52, -19, 7, -17, 9),
    (51, 39, 67, 52, -16, 7, -14, 9),
    (49, 39, 65, 52, -13, 7, -11, 9),
)


def step_in_place(steps=None):
    """
    March on the spot (37-frame cycle, alternating diagonal legs).

    Args:
        steps: Number of full 37-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    play(_FRAMES, _FRAME_DELAY, steps, name="step in place")
