"""2-DOF leg inverse kinematics for a 2-link planar leg.

Coordinate frame (origin at shoulder joint):
  x = forward (positive = in front of robot)
  z = downward (positive = toward ground)

Physical angles:
  alpha: shoulder pitch, degrees from vertical, positive = forward lean
  gamma: knee bend,      degrees, 0 = straight, positive = bent

At alpha=0, gamma=0: leg hangs straight down, foot at (0, L1+L2).

Verified against Doggo stand pose (alpha=10, gamma=30):
  foot = (-10mm, 101mm) — foot slightly behind shoulder, 101mm below.
  These physical angles map exactly to poses.py stand() commanded angles.
"""

import math

L1 = 50.0  # upper leg length mm (shoulder joint to knee joint)
L2 = 55.0  # lower leg length mm (knee joint to foot)


def fk(alpha_deg, gamma_deg):
    """Forward kinematics: (alpha, gamma) → (foot_x, foot_z) in mm.

    alpha_deg: shoulder pitch (0=vertical hang, positive=forward)
    gamma_deg: knee bend (0=straight, positive=bent)
    """
    a = math.radians(alpha_deg)
    g = math.radians(gamma_deg)
    x = L1 * math.sin(a) + L2 * math.sin(a - g)
    z = L1 * math.cos(a) + L2 * math.cos(a - g)
    return x, z


def ik(x, z):
    """Inverse kinematics: (foot_x, foot_z) → (alpha_deg, gamma_deg).

    Clamps to reachable workspace — never raises an error.
    Uses the "knee bent" (elbow-up) configuration.
    """
    r2 = x * x + z * z
    r = math.sqrt(r2)

    r_max = L1 + L2 - 1.0  # leave 1mm margin to avoid acos(1.0) edge case
    r_min = abs(L1 - L2) + 1.0
    if r > r_max:
        x = x * r_max / r
        z = z * r_max / r
        r2 = r_max * r_max
    elif r < r_min:
        x = x * r_min / r
        z = z * r_min / r
        r2 = r_min * r_min

    cos_g = (r2 - L1 * L1 - L2 * L2) / (2.0 * L1 * L2)
    cos_g = max(-1.0, min(1.0, cos_g))
    gamma = math.acos(cos_g)  # always >= 0 (knee bent, not hyper-extended)

    alpha = math.atan2(x, z) + math.atan2(L2 * math.sin(gamma), L1 + L2 * math.cos(gamma))

    return math.degrees(alpha), math.degrees(gamma)
