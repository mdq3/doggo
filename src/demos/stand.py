"""
Bittle Stand Demo

Usage:
    mpremote run src/demos/stand.py
"""

import time

from poses import rest, sit, stand

print("\n" + "=" * 60)
print("Bittle Stand Demo")
print("=" * 60)

try:
    # Start from zero (smooth from rest since current_pos is initialised to rest)
    # zero_position()
    # time.sleep(1)

    # Stand up
    stand()
    time.sleep(2)

    # Sit down
    sit()
    time.sleep(2)

    # Stand again
    stand()
    time.sleep(2)

    # Rest
    rest()
    time.sleep(1)

    print("\n✓ Demo complete!")

except KeyboardInterrupt:
    print("\n\nInterrupted!")
    rest()

except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "=" * 60)
