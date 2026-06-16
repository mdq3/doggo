"""Pivot Left / Pivot Right Gaits — ported from OpenCatEsp32 InstinctBittleESP.h (vtL array).

72 frames per cycle. Crawl-style in-place pivot: one foot at a time, three feet always grounded.
Unlike wkL (which arcs the body diagonally), vtL rotates the robot in place.

Gait array column order (OpenCat joint indices 8-15):
  [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]

Conversion: commanded = 90 + rotationDirection[joint] * opencat_angle
  (commanded 90 = OpenCat raw 0 = calibration pose, at the corrected 270-degree
   servo scale where 1 commanded degree = 1 physical degree)
  rotDir:   FL_sh=+1, FR_sh=-1, RR_sh=-1, RL_sh=+1
            FL_leg=-1, FR_leg=+1, RR_leg=+1, RL_leg=-1

Leg values are capped at _LEG_CAP to prevent extreme servo positions. vtL has leg values
up to raw=46 which maps to commanded=136° (FR_leg: 90 + 1*46) or 44° (FL_leg: 90 + -1*46),
causing servo overextension and CoM shifts that topple the robot.

Right pivot: L/R column pairs are swapped before conversion:
  Index 0 (FL_sh) <-> 1 (FR_sh)
  Index 2 (RR_sh) <-> 3 (RL_sh)
  Index 4 (FL_leg) <-> 5 (FR_leg)
  Index 6 (RR_leg) <-> 7 (RL_leg)

Tuning:
  Falls backward      -> raise _SHOULDER_CAP (e.g. 45) so rear legs plant further forward
                         OR make _LEG_OFFSET more negative (e.g. -25) to raise body height
  Legs too bent       -> make _LEG_OFFSET more negative (e.g. -25)
  Legs too extended   -> make _LEG_OFFSET less negative (e.g. -15)
  Shuffles / no pivot -> raise _SHOULDER_CAP (e.g. 45) for more rotation
  Hobbling / uneven   -> reduce _LEG_CAP (e.g. 6) to keep body height more constant
                         OR raise _LEG_MIN (e.g. 2) to reduce swing-leg fold
  Too slow            -> decrease _FRAME_DELAY (e.g. 0.010)
"""

from gaits.player import play

# NOTE: _SHOULDER_CAP/_LEG_OFFSET/_LEG_CAP below were tuned against the old 1.5x
# servo scale error; vtL's "extreme extension" problem may not exist at true scale.
# Worth re-testing with offset/caps relaxed.

_FRAME_DELAY = 0.014  # seconds between frames — tune if unstable
_SHOULDER_CAP = 28  # tight cap → small step arc → in-place rotation (raise for wider pivot circle)
_LEG_OFFSET = -20  # shift vtL legs toward standing neutral (vtL is all-positive = crouched)
_LEG_CAP = 10  # cap raw leg excursion after offset; tighter = less body-height bobbing
_LEG_MIN = 0  # floor after offset; 0 = swing leg stays at neutral height (no over-folding)

# Raw OpenCat angles from vtL in InstinctBittleESP.h.
# Columns: [FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg]
# Crawl-style in-place pivot: one foot lifted at a time, 3-point support.
_FRAMES = (
    (29, 26, 29, 26, 27, 22, 27, 22),
    (28, 26, 30, 26, 27, 21, 27, 24),
    (27, 26, 31, 25, 28, 22, 28, 25),
    (26, 26, 33, 24, 29, 23, 30, 26),
    (26, 25, 33, 23, 30, 24, 30, 27),
    (26, 25, 35, 23, 30, 25, 31, 27),
    (25, 25, 36, 23, 31, 24, 31, 27),
    (24, 25, 37, 24, 32, 22, 30, 26),
    (23, 25, 38, 24, 33, 22, 28, 26),
    (22, 25, 39, 26, 34, 20, 26, 24),
    (20, 23, 41, 29, 35, 21, 24, 20),
    (19, 20, 43, 31, 37, 23, 24, 17),
    (17, 17, 43, 34, 39, 27, 24, 14),
    (17, 13, 44, 37, 39, 31, 24, 12),
    (16, 11, 46, 39, 41, 35, 24, 13),
    (14, 10, 46, 42, 42, 38, 24, 16),
    (13, 10, 46, 42, 42, 38, 24, 16),
    (11, 10, 45, 44, 41, 39, 23, 20),
    (10, 10, 44, 45, 40, 40, 20, 23),
    (10, 11, 42, 46, 39, 41, 16, 24),
    (10, 13, 42, 46, 38, 42, 16, 24),
    (10, 14, 39, 46, 38, 42, 13, 24),
    (11, 16, 37, 44, 35, 41, 12, 24),
    (13, 17, 34, 43, 31, 39, 14, 24),
    (17, 17, 31, 43, 27, 39, 17, 24),
    (20, 19, 29, 41, 23, 37, 20, 24),
    (23, 20, 26, 39, 21, 35, 24, 26),
    (25, 22, 24, 38, 20, 34, 26, 28),
    (25, 23, 24, 37, 22, 33, 26, 30),
    (25, 24, 23, 36, 22, 32, 27, 31),
    (25, 25, 23, 35, 24, 31, 27, 31),
    (25, 26, 23, 33, 25, 30, 27, 30),
    (25, 26, 24, 33, 24, 30, 26, 30),
    (26, 26, 25, 31, 23, 29, 25, 28),
    (26, 27, 26, 30, 22, 28, 24, 27),
    (26, 28, 26, 29, 21, 27, 22, 27),
    (26, 29, 26, 28, 22, 27, 21, 27),
    (26, 30, 26, 27, 24, 27, 22, 28),
    (25, 31, 26, 26, 25, 28, 23, 29),
    (24, 33, 25, 26, 26, 30, 24, 30),
    (23, 33, 25, 26, 27, 30, 25, 30),
    (23, 35, 25, 25, 27, 31, 24, 31),
    (23, 36, 25, 24, 27, 31, 22, 32),
    (24, 37, 25, 23, 26, 30, 22, 33),
    (24, 38, 25, 22, 26, 28, 20, 34),
    (26, 39, 23, 20, 24, 26, 21, 35),
    (29, 41, 20, 19, 20, 24, 23, 37),
    (31, 43, 17, 17, 17, 24, 27, 39),
    (34, 43, 13, 17, 14, 24, 31, 39),
    (37, 44, 11, 16, 12, 24, 35, 41),
    (39, 46, 10, 14, 13, 24, 38, 42),
    (42, 46, 10, 13, 16, 24, 38, 42),
    (42, 46, 10, 11, 16, 24, 39, 41),
    (44, 45, 10, 10, 20, 23, 40, 40),
    (45, 44, 11, 10, 23, 20, 41, 39),
    (46, 42, 13, 10, 24, 16, 42, 38),
    (46, 42, 14, 10, 24, 16, 42, 38),
    (46, 39, 16, 11, 24, 13, 41, 35),
    (44, 37, 17, 13, 24, 12, 39, 31),
    (43, 34, 17, 17, 24, 14, 39, 27),
    (43, 31, 19, 20, 24, 17, 37, 23),
    (41, 29, 20, 23, 24, 20, 35, 21),
    (39, 26, 22, 25, 26, 24, 34, 20),
    (38, 24, 23, 25, 28, 26, 33, 22),
    (37, 24, 24, 25, 30, 26, 32, 22),
    (36, 23, 25, 25, 31, 27, 31, 24),
    (35, 23, 26, 25, 31, 27, 30, 25),
    (33, 23, 26, 25, 30, 27, 30, 24),
    (33, 24, 26, 26, 30, 26, 29, 23),
    (31, 25, 27, 26, 28, 25, 28, 22),
    (30, 26, 28, 26, 27, 24, 27, 21),
    (29, 26, 29, 26, 27, 22, 27, 22),
)


def _transform(i, r):
    """Cap the shoulder reach (in-place rotation) and pull legs toward standing neutral."""
    if i < 4:  # shoulder joints
        return min(r, _SHOULDER_CAP)
    # leg joints: shift toward standing neutral then clamp both ends
    return max(_LEG_MIN, min(r + _LEG_OFFSET, _LEG_CAP))


def pivot_left(steps=None):
    """
    Pivot left in place (72-frame crawl cycle, 3-point support).

    Args:
        steps: Number of full 72-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    play(_FRAMES, _FRAME_DELAY, steps, transform=_transform, every=2, name="pivot left")


def pivot_right(steps=None):
    """
    Pivot right in place (72-frame crawl cycle, L/R mirrored from vtL).

    Args:
        steps: Number of full 72-frame cycles to run.
               None = run until KeyboardInterrupt.
    """
    play(
        _FRAMES, _FRAME_DELAY, steps, transform=_transform, mirror_lr=True, every=2,
        name="pivot right",
    )
