"""Shared keyframe-gait player: angle conversion and mirroring (gaits/player.py).

The servo-scale regression guard lives here, since every keyframe gait now converts
through player.to_commanded with ``commanded = 90 + rotDir * raw``. A return to the old
ZERO_POS = 65/115/... scheme (the 1.5x-scale compensation) would fail these tests.
"""

import poses
from gaits import player


def test_rotation_directions():
    assert player.RD == (1, -1, -1, 1, -1, 1, 1, -1)


def test_channels_match_poses():
    assert player.CH == poses.GAIT_CHANNELS


def test_to_commanded_zero_base_is_ninety():
    # The regression guard: commanded 90 == OpenCat raw 0, all eight joints.
    assert player.to_commanded((0,) * 8) == {ch: 90 for ch in player.CH}


def test_to_commanded_follows_formula():
    raw = (10, 20, 30, 40, 5, -5, 15, -15)
    expected = {player.CH[i]: 90 + player.RD[i] * raw[i] for i in range(8)}
    assert player.to_commanded(raw) == expected


def test_to_commanded_applies_transform_before_mapping():
    raw = (10, 20, 30, 40, 5, -5, 15, -15)
    got = player.to_commanded(raw, lambda i, r: r / 2)
    expected = {player.CH[i]: 90 + player.RD[i] * (raw[i] / 2) for i in range(8)}
    assert got == expected


def test_mirror_swaps_lr_column_pairs():
    assert player.mirror((0, 1, 2, 3, 4, 5, 6, 7)) == (1, 0, 3, 2, 5, 4, 7, 6)
