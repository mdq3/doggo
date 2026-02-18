"""
Bittle Calibration Config
"""

# Channel to joint mapping
JOINTS = {
     0: "Head Pan",
     4: "Front Left Shoulder",
     5: "Front Right Shoulder",
     6: "Rear Right Shoulder",
     7: "Rear Left Shoulder",
     8: "Front Left Leg",
     9: "Front Right Leg",
    10: "Rear Right Leg",
    11: "Rear Left Leg",
}

# Calibration offsets (degrees from 90)
CALIBRATION = {
     0:  +0,  # Head Pan
     4: +37,  # Front Left Shoulder
     5: -33,  # Front Right Shoulder
     6: +42,  # Rear Right Shoulder
     7: -41,  # Rear Left Shoulder
     8: +36,  # Front Left Leg
     9: -32,  # Front Right Leg
    10: -34,  # Rear Right Leg
    11: +32,  # Rear Left Leg
}

def apply_calibration(angle, channel):
    return angle + CALIBRATION.get(channel, 0)
