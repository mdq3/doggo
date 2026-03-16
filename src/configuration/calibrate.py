"""
Servo Calibration Helper

Use interactively in REPL to calibrate servos and generate config.py

Usage:
    1. Upload: mpremote fs mkdir :drivers && mpremote fs cp src/drivers/servo.py :drivers/servo.py
    2. Upload: mpremote fs cp src/configuration/calibrate.py :calibrate.py
    3. Connect: mpremote repl
    4. Run:
       >>> from calibrate import *
       >>> move(0, 90)      # Move head to center
       >>> move(4, 90)      # Move front left shoulder
       >>> save(4, 87)      # Save when it looks right
       >>> done()           # Print config.py content
"""


from drivers.servo import Servos

# Initialize
servos = Servos()
calibration = {}

# BiBoard V1 channel to joint mapping (discovered by testing)
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

# Channels used by Bittle
BITTLE_CHANNELS = [0, 4, 5, 6, 7, 8, 9, 10, 11]

def move(channel, angle):
    """Move a servo to an angle"""
    servos.set_servo(channel, angle)
    name = JOINTS.get(channel, f"Channel {channel}")
    print(f"[{channel}] {name} -> {angle}°")

def m(channel, angle):
    """Short alias for move()"""
    move(channel, angle)

def save(channel, neutral_angle):
    """Save the neutral angle for a servo"""
    offset = neutral_angle - 90
    name = JOINTS.get(channel, f"Channel {channel}")
    calibration[channel] = offset
    print(f"Saved: [{channel}] {name} = {neutral_angle}° (offset: {offset:+d}°)")

def s(channel, neutral_angle):
    """Short alias for save()"""
    save(channel, neutral_angle)

def show():
    """Show current calibration data"""
    print("\nCurrent calibration:")
    print("-" * 40)
    for ch in sorted(calibration.keys()):
        name = JOINTS.get(ch, f"Channel {ch}")
        offset = calibration[ch]
        neutral = 90 + offset
        print(f"  [{ch:2d}] {name}: {neutral}° (offset: {offset:+d}°)")
    if not calibration:
        print("  (none saved yet)")
    print()

def done():
    """Generate and print config.py content"""
    print("\n" + "=" * 50)
    print("Copy everything below into config.py:")
    print("=" * 50 + "\n")

    content = '"""\nBittle Calibration Config\n"""\n\n'
    content += "# Channel to joint mapping\n"
    content += "JOINTS = {\n"
    for ch in BITTLE_CHANNELS:
        name = JOINTS.get(ch, f"Channel {ch}")
        content += f"    {ch:2d}: \"{name}\",\n"
    content += "}\n\n"

    content += "# Calibration offsets (degrees from 90)\n"
    content += "CALIBRATION = {\n"

    for ch in BITTLE_CHANNELS:
        offset = calibration.get(ch, 0)
        name = JOINTS.get(ch, f"Channel {ch}")
        content += f"    {ch:2d}: {offset:+3d},  # {name}\n"

    content += "}\n\n"
    content += """def apply_calibration(angle, channel):
    return angle + CALIBRATION.get(channel, 0)
"""

    print(content)
    print("=" * 50)
    print("\nTo save on BiBoard:")
    print("1. Copy the text above")
    print("2. Create config.py on your computer")
    print("3. Run: mpremote fs cp config.py :config.py")
    print("=" * 50)

def help():
    """Show available commands"""
    print("""
Calibration Commands:
---------------------
  move(channel, angle)  - Move servo to angle (0-180)
  m(channel, angle)     - Same as move() (shortcut)

  save(channel, angle)  - Save neutral angle for servo
  s(channel, angle)     - Same as save() (shortcut)

  show()                - Show saved calibration
  done()                - Generate config.py content
  help()                - Show this help

Bittle Channels:
----------------""")
    for ch in BITTLE_CHANNELS:
        name = JOINTS.get(ch, f"Channel {ch}")
        print(f"  {ch:2d}: {name}")
    print()

# Show help on import
print("\n" + "=" * 50)
print("Calibration Helper Ready")
print("=" * 50)
print("\nBittle servo channels:")
for ch in BITTLE_CHANNELS:
    name = JOINTS.get(ch, f"Channel {ch}")
    print(f"  {ch:2d}: {name}")
print("\nType help() for commands")
print("\nQuick start:")
print("  >>> move(4, 90)   # Front left shoulder")
print("  >>> save(4, 90)")
print("  >>> done()")
print()
