"""
Doggo Pose Library

Poses derived from OpenCatEsp32 InstinctBittleESP.h reference data.

Conversion formula (from espServo.h attachAllESPServos):
  BiBoard channels 4-7 map to OpenCat joint indices 8-11 (shoulder pitch).
  BiBoard channels 8-11 map to OpenCat joint indices 12-15 (knee).
  commanded_angle = 90 + rotationDirection[oc_joint] * opencat_angle

rotationDirection (indices 8-15):
  FL_SHOULDER(ch4)=+1  FR_SHOULDER(ch5)=-1  RR_SHOULDER(ch6)=-1  RL_SHOULDER(ch7)=+1
  FL_LEG(ch8)=-1       FR_LEG(ch9)=+1       RR_LEG(ch10)=+1      RL_LEG(ch11)=-1

Usage:
    from poses import stand, sit, rest, stretch, zero_position
"""

import _thread
import time

from drivers.servo import Servos

# BiBoard V1 channel mapping
CH_HEAD = 0
CH_FL_SHOULDER = 4
CH_FR_SHOULDER = 5
CH_RR_SHOULDER = 6
CH_RL_SHOULDER = 7
CH_FL_LEG = 8
CH_FR_LEG = 9
CH_RR_LEG = 10
CH_RL_LEG = 11

ALL_CHANNELS = [
    CH_HEAD,
    CH_FL_SHOULDER,
    CH_FR_SHOULDER,
    CH_RR_SHOULDER,
    CH_RL_SHOULDER,
    CH_FL_LEG,
    CH_FR_LEG,
    CH_RR_LEG,
    CH_RL_LEG,
]

# Try to load calibration
try:
    from config import CALIBRATION, apply_calibration

    print("✓ Loaded calibration data")
except ImportError:
    print("⚠ No calibration data found - using defaults")
    CALIBRATION = {}

    def apply_calibration(angle, channel):
        return angle


# Initialize hardware
print("Initializing hardware...")
servos = Servos()
print("✓ Hardware ready")

# OpenCat "rest" pose commands (normal end-state of a run).
# Used to initialise current_pos so zero_position() transitions smoothly
# from lying-flat rather than from an assumed neutral that may be wrong.
#
# Full OpenCat rest[] values: shoulder = 75, knee = -55. With the corrected
# 270-degree servo scale the commandable range is -45..225, so no reduction
# is needed (worst calibrated extreme: FL_SHOULDER 165 + 55.5 = 220.5).
_REST_COMMANDED = {
    CH_HEAD: 90,
    CH_FL_SHOULDER: 165,  # 90 + 1*75
    CH_FR_SHOULDER: 15,  # 90 - 1*75
    CH_RR_SHOULDER: 15,  # 90 - 1*75
    CH_RL_SHOULDER: 165,  # 90 + 1*75
    CH_FL_LEG: 145,  # rd=-1, opencat=-55: 90+55
    CH_FR_LEG: 35,  # rd=+1, opencat=-55: 90-55
    CH_RR_LEG: 35,  # rd=+1, opencat=-55: 90-55
    CH_RL_LEG: 145,  # rd=-1, opencat=-55: 90+55
}

# Track current positions (calibrated), initialised to rest state
current_pos = {ch: apply_calibration(_REST_COMMANDED.get(ch, 90), ch) for ch in ALL_CHANNELS}

# Cross-thread motion coordination. motion_lock serialises servo access between
# the HTTP server thread and the fall watchdog thread; _last_motion_ms lets the
# watchdog tell "lying still" apart from "mid-behavior pause" (every motion path
# calls note_motion() each time it commands the servos).
motion_lock = _thread.allocate_lock()
_last_motion_ms = time.ticks_ms()


def note_motion():
    """Record that a servo command was just sent (called by all motion paths)."""
    global _last_motion_ms
    _last_motion_ms = time.ticks_ms()


def idle_ms():
    """Milliseconds since the last servo command from any motion path."""
    return time.ticks_diff(time.ticks_ms(), _last_motion_ms)


def play_frame(targets):
    """
    Send commanded angles directly to servos with no software interpolation.
    Used for gait playback where frames are already a smooth trajectory.

    Args:
        targets: Dict of {channel: commanded_angle} (before calibration)
    """
    note_motion()
    for ch, angle in targets.items():
        cal = apply_calibration(angle, ch)
        servos.set_servo(ch, cal)
        current_pos[ch] = cal


def move_to(targets, speed=2, delay=0.015):
    """
    Move multiple servos simultaneously to target positions.

    Args:
        targets: Dict of {channel: commanded_angle} (before calibration)
        speed:   Max degrees per step (lower = smoother)
        delay:   Seconds between steps
    """
    calibrated = {ch: apply_calibration(angle, ch) for ch, angle in targets.items()}

    while True:
        note_motion()
        all_done = True

        for ch, target in calibrated.items():
            current = current_pos[ch]

            if abs(current - target) <= speed:
                if current != target:
                    servos.set_servo(ch, target)
                    current_pos[ch] = target
            else:
                all_done = False
                new_pos = current + speed if current < target else current - speed
                servos.set_servo(ch, int(new_pos))
                current_pos[ch] = new_pos

        if all_done:
            break

        time.sleep(delay)


def zero_position():
    """All servos to calibrated neutral (90° commanded)."""
    print("\nMoving to zero position...")
    move_to({ch: 90 for ch in ALL_CHANNELS}, speed=3)
    print("✓ Zero position")


def stand():
    """
    Standing pose.
    OpenCat reference: balance[] — shoulder pitch = 30, knee = 30 (all joints).
    With the corrected servo scale these are the true OpenCat values (the old
    shoulder fudge of 10 compensated for the 1.5x scale error).
    """
    print("\nStanding up...")
    move_to(
        {
            CH_HEAD: 90,
            CH_FL_SHOULDER: 120,  # 90 + 1*30  (opencat=30)
            CH_FR_SHOULDER: 60,  # 90 - 1*30
            CH_RR_SHOULDER: 60,  # 90 - 1*30
            CH_RL_SHOULDER: 120,  # 90 + 1*30
            CH_FL_LEG: 60,  # 90 - 1*30  (rd=-1, opencat=30)
            CH_FR_LEG: 120,  # 90 + 1*30  (rd=+1, opencat=30)
            CH_RR_LEG: 120,  # 90 + 1*30
            CH_RL_LEG: 60,  # 90 - 1*30  (rd=-1, opencat=30)
        },
        speed=1,
    )
    print("✓ Standing position")


def sit():
    """
    Sitting pose.
    Front legs stay at stand values (keep front body up).
    Rear legs move to rest values (drop haunches to ground).
    On this robot positive shoulder angle = backward rotation, so the
    rest rear-shoulder value (+50°) is what lowers the haunches — the
    opposite direction to the OpenCat sit convention.
    """
    print("\nSitting down...")
    move_to(
        {
            CH_HEAD: 90,
            CH_FL_SHOULDER: 120,  # stand value — front stable
            CH_FR_SHOULDER: 60,  # stand value — front stable
            CH_RR_SHOULDER: 15,  # rest value  — haunches down
            CH_RL_SHOULDER: 165,  # rest value  — haunches down
            CH_FL_LEG: 60,  # stand value — front extended
            CH_FR_LEG: 120,  # stand value — front extended
            CH_RR_LEG: 62,  # midpoint between rest(35) and neutral(90)
            CH_RL_LEG: 118,  # midpoint between rest(145) and neutral(90)
        },
        speed=2,
    )
    print("✓ Sitting position")


def stretch():
    """
    Stretching pose (downward dog): front legs extended forward, chest
    lowered, haunches up.
    OpenCat reference: str[] — front shoulders = -75, rear shoulders = 30,
    front knees = 60, rear knees = 0.
    """
    print("\nStretching...")
    move_to(
        {
            CH_HEAD: 90,
            CH_FL_SHOULDER: 15,  # 90 + 1*(-75)
            CH_FR_SHOULDER: 165,  # 90 - 1*(-75)
            CH_RR_SHOULDER: 60,  # 90 - 1*30
            CH_RL_SHOULDER: 120,  # 90 + 1*30
            CH_FL_LEG: 30,  # 90 - 1*60  (rd=-1, opencat=60)
            CH_FR_LEG: 150,  # 90 + 1*60
            CH_RR_LEG: 90,  # opencat=0
            CH_RL_LEG: 90,  # opencat=0
        },
        speed=2,
    )
    print("✓ Stretching position")


def rest():
    """
    Resting / lying-flat pose.
    OpenCat reference: rest[] — shoulder pitch = 75, knee = -55 (all joints).
    """
    print("\nLying down...")
    move_to(_REST_COMMANDED, speed=1)
    print("✓ Resting position")
