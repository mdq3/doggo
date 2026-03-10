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

import time

from gaits.pivot import _CH, _FRAMES, _RD, _ZERO, _mirror
from poses import move_to, play_frame, stand

_FRAME_DELAY = 0.014
_SHOULDER_CAP = 42
_LEG_OFFSET = -20
_LEG_CAP = 10
_LEG_MIN = 0


def _to_commanded(raw):
    result = {}
    for i in range(8):
        r = raw[i]
        if i < 4:
            r = min(r, _SHOULDER_CAP)
        else:
            r = max(_LEG_MIN, min(r + _LEG_OFFSET, _LEG_CAP))
        result[_CH[i]] = _ZERO[i] + _RD[i] * r
    return result


def bound_left(steps=None):
    """
    Bound left in a tight arc (vtL crawl, wide shoulder reach).

    Args:
        steps: Number of full cycles to run. None = run until KeyboardInterrupt.
    """
    print("\nStarting bound left...")

    move_to(_to_commanded(_FRAMES[0]), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for i in range(0, len(_FRAMES), 2):
                play_frame(_to_commanded(_FRAMES[i]))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nBound left interrupted.")

    print("Returning to stand...")
    stand()


def bound_right(steps=None):
    """
    Bound right in a tight arc (vtL crawl, L/R mirrored, wide shoulder reach).

    Args:
        steps: Number of full cycles to run. None = run until KeyboardInterrupt.
    """
    print("\nStarting bound right...")

    move_to(_to_commanded(_mirror(_FRAMES[0])), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for i in range(0, len(_FRAMES), 2):
                play_frame(_to_commanded(_mirror(_FRAMES[i])))
                time.sleep(_FRAME_DELAY)
            count += 1
    except KeyboardInterrupt:
        print("\n\nBound right interrupted.")

    print("Returning to stand...")
    stand()
