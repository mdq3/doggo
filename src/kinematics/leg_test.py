"""Forward/inverse kinematics for the 2-link planar leg (kinematics/leg.py)."""

import math

import pytest

from kinematics.leg import L1, L2, fk, ik

_R_MAX = L1 + L2 - 1.0  # ik leaves a 1mm margin off full extension
_R_MIN = abs(L1 - L2) + 1.0


def test_fk_straight_hang():
    # alpha=0, gamma=0: leg straight down, foot at (0, L1+L2).
    x, z = fk(0, 0)
    assert x == pytest.approx(0.0, abs=1e-9)
    assert z == pytest.approx(L1 + L2)


def test_fk_stand_pose_matches_docstring():
    # Documented stand pose (OpenCat balance): alpha=30, gamma=30 -> ~(+25mm, 98mm).
    x, z = fk(30, 30)
    assert x == pytest.approx(25.0, abs=0.5)
    assert z == pytest.approx(98.0, abs=0.5)


@pytest.mark.parametrize("alpha", range(-30, 61, 15))
@pytest.mark.parametrize("gamma", range(20, 151, 10))
def test_ik_inverts_fk(alpha, gamma):
    # gamma in [20,150] keeps the foot strictly inside the reachable annulus,
    # so ik recovers the exact (alpha, gamma) fed into fk (elbow-up branch).
    a, g = ik(*fk(alpha, gamma))
    assert a == pytest.approx(alpha, abs=1e-4)
    assert g == pytest.approx(gamma, abs=1e-4)


def test_ik_clamps_beyond_reach():
    # Far past full extension: foot is pulled back onto the max-reach circle.
    a, g = ik(0.0, 1000.0)
    assert 0 <= g <= 180
    x, z = fk(a, g)
    assert math.hypot(x, z) == pytest.approx(_R_MAX, abs=0.5)


def test_ik_clamps_inside_minimum():
    # Foot demanded closer than the legs can fold: pushed out to the min-reach circle.
    a, g = ik(0.0, 1.0)
    assert 0 <= g <= 180
    x, z = fk(a, g)
    assert math.hypot(x, z) == pytest.approx(_R_MIN, abs=0.5)
