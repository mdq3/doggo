"""IK-based forward trot gait.

Generates smooth foot trajectories via parametric curves and solves
2-link IK each frame — no fixed keyframes.

Foot trajectory (per leg, phase 0→1):
  Stance [0, 0.5):  foot on ground, sweeps backward (body moves forward)
  Swing  [0.5, 1):  foot raised in a sin arc, sweeps forward to re-plant

Diagonal pairing (trot): FL+RR and FR+RL are 180° out of phase.
At any moment one diagonal is in stance, the other is in swing.

Tuning:
  Body drifts backward / no forward progress  → increase _STEP_LENGTH
  Feet catching on floor / colliding          → increase _STEP_HEIGHT
  Feet sliding on landing                     → decrease _STEP_LENGTH
  Too fast / unstable                         → increase _FRAME_DELAY (min 0.008)
  Too slow                                    → decrease _FRAME_DELAY
  Body height too low / servos straining      → decrease _BODY_HEIGHT
  Body height too high / tippy                → increase _BODY_HEIGHT
  Pitches forward on start                    → decrease _X_OFFSET (more negative)
  Pitches backward / no forward progress      → increase _X_OFFSET (toward 0)
  Curves left or right                        → adjust _TRIM (positive = corrects rightward drift)
  Pitching nose-up/down during gait          → tune _K_PITCH
  Rolling left/right                          → tune _K_ROLL
"""

import math
import time

from utime import ticks_diff, ticks_us

from kinematics.doggo import leg_frame
from kinematics.leg import ik
from poses import move_to, play_frame, stand

# --- Trajectory parameters -------------------------------------------------
# NOTE: retuned analytically for the corrected 270-degree servo scale
# (1 commanded degree = 1 physical degree) — needs hardware re-verification.
# The old constants (and the violent-stall warnings that shaped them) were
# artifacts of the 1.5x scale error: the IK demanded excursions that came out
# 1.5x too large physically and hit servo stops early.
_BODY_HEIGHT = 98.0  # mm: foot z during stance (FK at corrected stand: alpha=30, gamma=30)
_STEP_LENGTH = 12.0  # mm: foot sweeps ±this value in x each half-cycle
_STEP_HEIGHT = 12.0  # mm: foot clearance above ground during swing
_X_OFFSET = -5.0  # mm: shifts entire foot trajectory backward of shoulder
_CYCLE_FRAMES = 48  # frames per full cycle
_FRAME_DELAY = 0.008  # seconds per frame (8ms minimum for dynamic stability)

# Safety bounds: commanded angles are clamped before dispatch to prevent
# servo stall at physical stops. Physical equivalents of the old empirical
# bounds (45/150 in old 180-degree-mapped units → 90 + 1.5x the excursion).
_CMD_MIN = 25.0
_CMD_MAX = 180.0

# Left/right trim: small alpha offset applied to left-side shoulders (FL, RL).
# Positive corrects rightward drift (same convention as trot.py _TRIM).
_TRIM = 0.0

# --- IMU stabilization -----------------------------------------------------
_K_PITCH = 0.2
_K_ROLL = 0.3
_IMU_CLAMP = 8.0

_FRAME_US = int(_FRAME_DELAY * 1_000_000)

# Stand pose physical angles (alpha=30°, gamma=30° → OpenCat balance, matches poses.py stand)
_ALPHA_STAND = 30.0
_GAMMA_STAND = 30.0


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def _foot_pos(phase):
    """Foot (x, z) for a given phase in [0, 1).

    phase 0.0 → 0.5: stance — foot at ground, moving backward
    phase 0.5 → 1.0: swing  — foot raised, moving forward
    """
    if phase < 0.5:
        t = phase * 2.0  # 0 → 1 over stance
        x = _STEP_LENGTH * (1.0 - 2.0 * t) + _X_OFFSET  # +step_length → -step_length
        z = _BODY_HEIGHT
    else:
        t = (phase - 0.5) * 2.0  # 0 → 1 over swing
        x = _STEP_LENGTH * (2.0 * t - 1.0) + _X_OFFSET  # -step_length → +step_length
        z = _BODY_HEIGHT - _STEP_HEIGHT * math.sin(t * math.pi)
    return x, z


def _stand_frame():
    return leg_frame(
        _ALPHA_STAND,
        _GAMMA_STAND,
        _ALPHA_STAND,
        _GAMMA_STAND,
        _ALPHA_STAND,
        _GAMMA_STAND,
        _ALPHA_STAND,
        _GAMMA_STAND,
    )


def trot_forward(steps=None, use_imu=True):
    """IK-based forward trot.

    Args:
        steps:   number of full cycles, or None to run until KeyboardInterrupt.
        use_imu: Enable IMU roll/pitch stabilization (default True).
    """
    print("\nStarting IK trot forward...")

    imu = None
    if use_imu:
        try:
            from imu import IMU

            imu = IMU()
        except Exception as e:
            print("IMU init failed:", e)

    def _frame_at(fi, p_adj=0.0, r_adj=0.0):
        phase1 = fi / _CYCLE_FRAMES
        phase2 = (fi + _CYCLE_FRAMES // 2) / _CYCLE_FRAMES % 1.0
        x1, z1 = _foot_pos(phase1)
        x2, z2 = _foot_pos(phase2)
        if phase1 < 0.5:
            z1 += p_adj + r_adj
        if phase2 < 0.5:
            z2 += -p_adj + r_adj
        a_fl, g_fl = ik(x1, z1)
        a_rr, g_rr = ik(x1, z1)
        a_fr, g_fr = ik(x2, z2)
        a_rl, g_rl = ik(x2, z2)
        a_fl += _TRIM
        a_rl += _TRIM
        raw = leg_frame(a_fl, g_fl, a_fr, g_fr, a_rr, g_rr, a_rl, g_rl)
        return {ch: _clamp(a, _CMD_MIN, _CMD_MAX) for ch, a in raw.items()}

    # Interpolate to frame 0 before starting — avoids a jerk from stand pose
    move_to(_frame_at(0), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for fi in range(_CYCLE_FRAMES):
                t0 = ticks_us()

                if imu is not None:
                    try:
                        pitch, roll = imu.read()
                        p_adj = _clamp(_K_PITCH * pitch, -_IMU_CLAMP, _IMU_CLAMP)
                        r_adj = _clamp(_K_ROLL * roll, -_IMU_CLAMP, _IMU_CLAMP)
                    except Exception:
                        p_adj = r_adj = 0.0
                else:
                    p_adj = r_adj = 0.0

                frame = _frame_at(fi, p_adj, r_adj)
                play_frame(frame)

                remaining = _FRAME_US - ticks_diff(ticks_us(), t0)
                if remaining > 0:
                    time.sleep_us(remaining)

            count += 1

    except KeyboardInterrupt:
        print("\n\nTrot interrupted.")

    print("Returning to stand...")
    stand()
