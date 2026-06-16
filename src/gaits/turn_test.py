"""Turn-left/right L/R mirroring and conversion (gaits/turn.py)."""

import gaits.turn as turn


def test_mirror_swaps_lr_column_pairs():
    assert turn._mirror((0, 1, 2, 3, 4, 5, 6, 7)) == (1, 0, 3, 2, 5, 4, 7, 6)


def test_zero_base_is_ninety():
    # Same servo-scale regression guard as walk: commanded 90 == OpenCat raw 0.
    assert turn._ZERO == (90,) * 8


def test_right_is_mirror_of_left():
    # turn_right plays the L/R-mirrored frames. Because mirrored left/right joints
    # carry opposite rotation directions, their commanded angles are symmetric
    # about the 90 centre, i.e. they sum to 180.
    frame = turn._FRAMES[10]
    left = turn._to_commanded(frame)
    right = turn._to_commanded(turn._mirror(frame))
    assert right[turn.CH_FL_SHOULDER] + left[turn.CH_FR_SHOULDER] == 180
    assert right[turn.CH_RL_SHOULDER] + left[turn.CH_RR_SHOULDER] == 180
