"""Physical-angle -> servo-commanded-angle conversion (kinematics/doggo.py).

These assertions pin the conversion to 1 commanded degree = 1 physical degree
(the corrected 270-degree servo scale). A regression to the old 1.5x scale, or
to per-leg zero offsets other than 90, would fail here.
"""

import poses
from kinematics.doggo import leg_frame, to_commanded


def test_to_commanded_neutral():
    assert to_commanded(0, 0, left_side=True) == (90.0, 90.0)
    assert to_commanded(0, 0, left_side=False) == (90.0, 90.0)


def test_to_commanded_stand_left():
    # alpha=30, gamma=30 -> left leg: sh=90+30, leg=90-30.
    assert to_commanded(30, 30, left_side=True) == (120.0, 60.0)


def test_to_commanded_stand_right():
    # Right legs mirror: sh=90-30, leg=90+30.
    assert to_commanded(30, 30, left_side=False) == (60.0, 120.0)


def test_leg_frame_matches_stand_pose():
    # leg_frame at the balance pose must reproduce poses.stand()'s leg commands.
    frame = leg_frame(30, 30, 30, 30, 30, 30, 30, 30)
    assert frame == {
        poses.CH_FL_SHOULDER: 120.0,
        poses.CH_FL_LEG: 60.0,
        poses.CH_FR_SHOULDER: 60.0,
        poses.CH_FR_LEG: 120.0,
        poses.CH_RR_SHOULDER: 60.0,
        poses.CH_RR_LEG: 120.0,
        poses.CH_RL_SHOULDER: 120.0,
        poses.CH_RL_LEG: 60.0,
    }
