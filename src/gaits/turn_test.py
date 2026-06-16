"""Turn-left/right mirroring via the shared player (gaits/turn.py)."""

import gaits.turn as turn
import poses
from gaits import player


def test_right_is_mirror_of_left():
    # turn_right plays the L/R-mirrored frames (turn uses no per-column transform).
    # Because mirrored left/right joints carry opposite rotation directions, their
    # commanded angles are symmetric about the 90 centre, i.e. they sum to 180.
    frame = turn._FRAMES[10]
    left = player.to_commanded(frame)
    right = player.to_commanded(player.mirror(frame))
    assert right[poses.CH_FL_SHOULDER] + left[poses.CH_FR_SHOULDER] == 180
    assert right[poses.CH_RL_SHOULDER] + left[poses.CH_RR_SHOULDER] == 180
