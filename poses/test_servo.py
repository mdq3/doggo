"""
Test servo control - Run this first!

Tests direct PWM servo control on BiBoard V1.

Usage:
    mpremote fs cp drivers/servo.py :servo.py
    mpremote run poses/test_servo.py
"""

import time

# Import servo driver
try:
    from servo import Servos
except ImportError:
    print("ERROR: servo.py not found!")
    print("Upload it first: mpremote fs cp drivers/servo.py :servo.py")
    import sys
    sys.exit(1)

print("=" * 50)
print("Servo Test Script (BiBoard V1 Direct PWM)")
print("=" * 50)

# Bittle channel mapping
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

BITTLE_CHANNELS = [0, 4, 5, 6, 7, 8, 9, 10, 11]

print("\nBittle servo channel mapping:")
for ch in BITTLE_CHANNELS:
    print(f"  Channel {ch:2d}: {JOINTS[ch]}")

# Step 1: Initialize servos
print("\n1. Initializing servo driver...")
try:
    servos = Servos()
    print("✓ Servo driver initialized")
except Exception as e:
    print(f"✗ Init failed: {e}")
    import sys
    sys.exit(1)

# Step 2: Test head servo (channel 0)
print("\n2. Testing head servo (channel 0)...")
print("   CAUTION: Servo will move!")
time.sleep(2)

try:
    print("   → Center (90°)")
    servos.set_servo(0, 90)
    time.sleep(1)

    print("   → Left (45°)")
    servos.set_servo(0, 45)
    time.sleep(1)

    print("   → Right (135°)")
    servos.set_servo(0, 135)
    time.sleep(1)

    print("   → Back to center (90°)")
    servos.set_servo(0, 90)
    time.sleep(1)

    print("✓ Head servo test completed!")

except Exception as e:
    print(f"✗ Servo test failed: {e}")
    import sys
    sys.exit(1)

# Step 3: Test all Bittle channels
print("\n3. Testing all Bittle channels (quick sweep)...")
print("   This will move all 9 servos briefly")
time.sleep(2)

for channel in BITTLE_CHANNELS:
    name = JOINTS[channel]
    print(f"   Channel {channel:2d} ({name})...", end=" ")
    servos.set_servo(channel, 90)
    time.sleep(0.3)
    servos.set_servo(channel, 70)
    time.sleep(0.3)
    servos.set_servo(channel, 110)
    time.sleep(0.3)
    servos.set_servo(channel, 90)
    print("✓")

print("\n" + "=" * 50)
print("SUCCESS! All servos working!")
print("=" * 50)
print("\nNext steps:")
print("1. Calibrate servos: mpremote run poses/calibrate.py")
print("2. Make Bittle stand: mpremote run poses/stand.py")
