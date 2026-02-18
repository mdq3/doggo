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
     4: +55,  # Front Left Shoulder
     5: -52,  # Front Right Shoulder
     6: +25,  # Rear Right Shoulder
     7: -20,  # Rear Left Shoulder
     8: +35,  # Front Left Leg
     9: -30,  # Front Right Leg
    10: -30,  # Rear Right Leg
    11: +31,  # Rear Left Leg
}

def apply_calibration(angle, channel):
    return angle + CALIBRATION.get(channel, 0)
