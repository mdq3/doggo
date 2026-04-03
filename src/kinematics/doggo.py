"""Doggo-specific conversion between physical leg angles and servo commanded angles.

Physical angles (as used by kinematics/leg.py):
  alpha: shoulder pitch, 0 = vertical hang, positive = forward lean
  gamma: knee bend,      0 = straight,      positive = bent

Servo commanded angle mapping (verified against poses.py stand() values):
  Left legs  (FL, RL):  commanded_sh  = 90 + alpha   (rotDir +1)
                        commanded_leg = 90 - gamma   (rotDir -1)
  Right legs (FR, RR):  commanded_sh  = 90 - alpha   (rotDir -1)
                        commanded_leg = 90 + gamma   (rotDir +1)

Cross-check at stand pose (alpha=10, gamma=30):
  FL_sh  = 100  FR_sh  =  80  RR_sh  =  80  RL_sh  = 100  ✓ (poses.py)
  FL_leg =  60  FR_leg = 120  RR_leg = 120  RL_leg =  60  ✓
"""

from poses import (
    CH_FL_LEG,
    CH_FL_SHOULDER,
    CH_FR_LEG,
    CH_FR_SHOULDER,
    CH_RL_LEG,
    CH_RL_SHOULDER,
    CH_RR_LEG,
    CH_RR_SHOULDER,
)


def to_commanded(alpha, gamma, left_side):
    """Convert physical angles to (shoulder_commanded, leg_commanded) degrees.

    left_side: True for FL/RL legs, False for FR/RR legs.
    """
    if left_side:
        return 90.0 + alpha, 90.0 - gamma
    else:
        return 90.0 - alpha, 90.0 + gamma


def leg_frame(a_fl, g_fl, a_fr, g_fr, a_rr, g_rr, a_rl, g_rl):
    """Build a commanded-angle dict for all 8 leg joints.

    Args are (alpha, gamma) per leg in physical degrees.
    """
    fl_sh, fl_leg = to_commanded(a_fl, g_fl, left_side=True)
    fr_sh, fr_leg = to_commanded(a_fr, g_fr, left_side=False)
    rr_sh, rr_leg = to_commanded(a_rr, g_rr, left_side=False)
    rl_sh, rl_leg = to_commanded(a_rl, g_rl, left_side=True)
    return {
        CH_FL_SHOULDER: fl_sh,
        CH_FL_LEG: fl_leg,
        CH_FR_SHOULDER: fr_sh,
        CH_FR_LEG: fr_leg,
        CH_RR_SHOULDER: rr_sh,
        CH_RR_LEG: rr_leg,
        CH_RL_SHOULDER: rl_sh,
        CH_RL_LEG: rl_leg,
    }
