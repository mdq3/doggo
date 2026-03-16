"""
Bittle Pose Library

Poses derived from OpenCatEsp32 InstinctBittleESP.h reference data.

Conversion formula (from espServo.h attachAllESPServos):
  BiBoard channels 4-7 map to OpenCat joint indices 8-11 (shoulder pitch).
  BiBoard channels 8-11 map to OpenCat joint indices 12-15 (knee).
  commanded_angle = 90 + rotationDirection[oc_joint] * opencat_angle

rotationDirection (indices 8-15):
  FL_SHOULDER(ch4)=+1  FR_SHOULDER(ch5)=-1  RR_SHOULDER(ch6)=-1  RL_SHOULDER(ch7)=+1
  FL_LEG(ch8)=-1       FR_LEG(ch9)=+1       RR_LEG(ch10)=+1      RL_LEG(ch11)=-1

Usage:
    from poses import stand, sit, rest, zero_position
"""

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

ALL_CHANNELS = [CH_HEAD, CH_FL_SHOULDER, CH_FR_SHOULDER, CH_RR_SHOULDER,
                CH_RL_SHOULDER, CH_FL_LEG, CH_FR_LEG, CH_RR_LEG, CH_RL_LEG]

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
# Angles reduced from the OpenCat reference (shoulder 75→50, knee -55→-50)
# to keep every channel's calibrated value inside [0, 180].  The limiting
# channels with this robot's calibration are:
#   FL_SHOULDER (+37 offset): commanded=140 → calibrated 177 (limit ~143)
#   FR_SHOULDER (-33 offset): commanded= 40 → calibrated   7 (limit  ~57)
#   FL_LEG      (+36 offset): commanded=140 → calibrated 176 (limit ~144)
_REST_COMMANDED = {
    CH_HEAD:        90,
    CH_FL_SHOULDER: 140,   # 90 + 1*50  → calibrated 177
    CH_FR_SHOULDER:  40,   # 90 - 1*50  → calibrated   7
    CH_RR_SHOULDER:  40,   # 90 - 1*50  → calibrated  82
    CH_RL_SHOULDER: 140,   # 90 + 1*50  → calibrated  99
    CH_FL_LEG:      135,   # rd=-1, opencat=-40: 90+40=130 → calibrated 166
    CH_FR_LEG:       45,   # rd=+1, opencat=-40: 90-40= 50 → calibrated  18
    CH_RR_LEG:       45,   # rd=+1, opencat=-40: 90-40= 50 → calibrated  16
    CH_RL_LEG:      135,   # rd=-1, opencat=-40: 90+40=130 → calibrated 162
}

# Track current positions (calibrated), initialised to rest state
current_pos = {ch: apply_calibration(_REST_COMMANDED.get(ch, 90), ch)
               for ch in ALL_CHANNELS}

def play_frame(targets):
    """
    Send commanded angles directly to servos with no software interpolation.
    Used for gait playback where frames are already a smooth trajectory.

    Args:
        targets: Dict of {channel: commanded_angle} (before calibration)
    """
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
    """
    print("\nStanding up...")
    move_to({
        CH_HEAD:        90,
        CH_FL_SHOULDER: 100,   # 90 + 1*10  (opencat=10° backward, tune ±5 as needed)
        CH_FR_SHOULDER:  80,   # 90 - 1*10
        CH_RR_SHOULDER:  80,   # 90 - 1*10
        CH_RL_SHOULDER: 100,   # 90 + 1*10
        CH_FL_LEG:       60,   # 90 - 1*30  (rd=-1, opencat=30)
        CH_FR_LEG:      120,   # 90 + 1*30  (rd=+1, opencat=30)
        CH_RR_LEG:      120,   # 90 + 1*30
        CH_RL_LEG:       60,   # 90 - 1*30  (rd=-1, opencat=30)
    }, speed=1)
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
    move_to({
        CH_HEAD:        90,
        CH_FL_SHOULDER: 100,   # stand value — front stable
        CH_FR_SHOULDER:  80,   # stand value — front stable
        CH_RR_SHOULDER:  40,   # rest value  — haunches down
        CH_RL_SHOULDER: 140,   # rest value  — haunches down
        CH_FL_LEG:       60,   # stand value — front extended
        CH_FR_LEG:      120,   # stand value — front extended
        CH_RR_LEG:       62,   # midpoint between rest(45) and neutral(90)
        CH_RL_LEG:      118,   # midpoint between rest(135) and neutral(90)
    }, speed=2)
    print("✓ Sitting position")

def rest():
    """
    Resting / lying-flat pose.
    OpenCat reference: rest[] — shoulder pitch = 75, knee = -55 (all joints).
    """
    print("\nLying down...")
    move_to(_REST_COMMANDED, speed=1)
    print("✓ Resting position")


