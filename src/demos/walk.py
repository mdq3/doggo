"""
Doggo Walk Demo

Usage:
    python webrepl_proxy.py run src/demos/walk.py
"""

import time

from gaits.walk import walk
from poses import rest, stand

print("\n" + "=" * 60)
print("Doggo Walk Demo")
print("=" * 60)

try:
    stand()
    time.sleep(1)

    walk(steps=5)
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
