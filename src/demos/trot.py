"""
Doggo Trot Demo

Usage:
    mpremote run src/demos/trot.py

Deploy:
    mpremote fs mkdir :drivers + \
        fs cp src/drivers/servo.py :drivers/servo.py + \
        fs cp src/poses.py :poses.py + \
        fs cp config.py :config.py + \
        fs cp src/imu.py :imu.py + \
        fs mkdir :gaits + \
        fs cp src/gaits/trot.py :gaits/trot.py + \
        run src/demos/trot.py
"""

import time

from gaits.trot import trot_forward
from poses import rest, stand

print("\n" + "=" * 60)
print("Doggo Trot Demo")
print("=" * 60)

try:
    stand()
    time.sleep(1)

    trot_forward(steps=4, use_imu=True)
    time.sleep(1)

    rest()
    time.sleep(1)

    print("\n✓ Demo complete!")

except KeyboardInterrupt:
    print("\n\nInterrupted!")
    rest()

except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "=" * 60)
