"""
Identify which channel controls which servo.

Upload and run in REPL:
    mpremote fs cp src/drivers/servo.py :servo.py
    mpremote fs cp src/configuration/identify_servos.py :identify_servos.py
    mpremote repl
    >>> from identify_servos import *
    >>> test(0)   # Watch which servo moves
    >>> test(4)   # Next channel...
"""

import time

from servo import Servos

servos = Servos()

# BiBoard V1 GPIO mapping
PINS = [18, 5, 14, 27, 23, 4, 12, 33, 19, 15, 13, 32]

# Known Bittle channel mapping (discovered by testing)
KNOWN_JOINTS = {
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

# Channels used by Bittle
BITTLE_CHANNELS = [0, 4, 5, 6, 7, 8, 9, 10, 11]

def test(channel):
    """Wiggle a servo to identify it"""
    if channel < 0 or channel >= len(PINS):
        print(f"Channel must be 0-{len(PINS)-1}")
        return

    name = KNOWN_JOINTS.get(channel, "Unknown")
    print(f"Testing channel {channel} (GPIO {PINS[channel]}) - Expected: {name}")
    print("Watch which servo moves...")

    # Wiggle the servo
    for _ in range(3):
        servos.set_servo(channel, 70)
        time.sleep(0.3)
        servos.set_servo(channel, 110)
        time.sleep(0.3)

    servos.set_servo(channel, 90)
    print("Done.")

def t(channel):
    """Short alias"""
    test(channel)

def all():
    """Test all Bittle channels"""
    print("\nTesting all Bittle channels...")
    for ch in BITTLE_CHANNELS:
        name = KNOWN_JOINTS.get(ch, "Unknown")
        print(f"\n[{ch}] {name}")
        input("Press Enter to test...")
        test(ch)

def show():
    """Show known channel mapping"""
    print("\nBittle Channel Mapping:")
    print("-" * 40)
    for ch in BITTLE_CHANNELS:
        name = KNOWN_JOINTS.get(ch, "Unknown")
        print(f"  Channel {ch:2d}: {name}")
    print()

print("""
Servo Identifier Ready
======================
Commands:
  test(4)  - Wiggle channel 4 (Front Left Shoulder)
  t(4)     - Same (shortcut)
  all()    - Test all Bittle channels
  show()   - Show channel mapping

Known Bittle channels: 0, 4, 5, 6, 7, 8, 9, 10, 11
(Channels 1, 2, 3 are unused)
""")
show()
