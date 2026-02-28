"""
Bittle Trot Demo

Usage:
    mpremote run src/demos/trot.py

Deploy:
    mpremote fs cp src/drivers/servo.py :servo.py + \
        fs cp src/poses.py :poses.py + \
        fs cp config.py :config.py + \
        fs mkdir :gaits + \
        fs cp src/gaits/trot.py :gaits/trot.py + \
        run src/demos/trot.py
"""

import time
from poses import stand, rest
from gaits.trot import trot

print("\n" + "=" * 60)
print("Bittle Trot Demo")
print("=" * 60)

try:
    stand()
    time.sleep(1)

    trot(steps=5)
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
