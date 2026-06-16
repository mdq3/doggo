"""Bound Turn Left / Bound Turn Right — vtL array with wide shoulder cap.

Same vtL crawl sequence as pivot.py but with a higher shoulder cap (42 vs 28).
Each foot reaches further per step, producing a tight arc rather than in-place rotation.
Use for nimble tight-radius turning; use pivot_left/pivot_right for in-place rotation.

Right turn: L/R column pairs are swapped — see pivot.py for full column documentation.

Tuning:
  Arc too wide        -> reduce _SHOULDER_CAP (e.g. 36)
  Arc too tight       -> raise _SHOULDER_CAP (e.g. 46)
  Hobbling            -> reduce _LEG_CAP (e.g. 6)
  Too slow            -> decrease _FRAME_DELAY (e.g. 0.010)
"""

from gaits.pivot import _FRAMES
from gaits.player import play

_FRAME_DELAY = 0.014
_SHOULDER_CAP = 42
_LEG_OFFSET = -20
_LEG_CAP = 10
_LEG_MIN = 0


def _transform(i, r):
    """Like pivot, but a wider shoulder cap so each foot reaches further (tight arc)."""
    if i < 4:
        return min(r, _SHOULDER_CAP)
    return max(_LEG_MIN, min(r + _LEG_OFFSET, _LEG_CAP))


def bound_left(steps=None):
    """
    Bound left in a tight arc (vtL crawl, wide shoulder reach).

    Args:
        steps: Number of full cycles to run. None = run until KeyboardInterrupt.
    """
    play(_FRAMES, _FRAME_DELAY, steps, transform=_transform, every=2, name="bound left")


def bound_right(steps=None):
    """
    Bound right in a tight arc (vtL crawl, L/R mirrored, wide shoulder reach).

    Args:
        steps: Number of full cycles to run. None = run until KeyboardInterrupt.
    """
    play(
        _FRAMES, _FRAME_DELAY, steps, transform=_transform, mirror_lr=True, every=2,
        name="bound right",
    )
