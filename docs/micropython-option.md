# MicroPython on BiBoard V1 - Alternative Approach

Running MicroPython directly on the BiBoard ESP32 for onboard Python control.

## Overview

**Yes, the BiBoard V1 can run MicroPython!** The BiBoard is based on ESP32, which has excellent MicroPython support. This allows you to run Python code **directly on the robot** without needing a Raspberry Pi.

```
┌──────────────────────────┐
│  BiBoard V1 (ESP32)      │
│  Running MicroPython     │  ← Python runs HERE
│  - Controls servos       │
│  - Reads sensors         │
│  - WiFi/Bluetooth        │
│  - Autonomous behavior   │
└──────────────────────────┘
```

## Pros and Cons

### ✅ Advantages

1. **True onboard Python** - No external computer needed
2. **No Raspberry Pi cost** - Save $30-50
3. **Less weight** - No extra hardware to mount
4. **Lower power** - One device instead of two
5. **Direct hardware access** - Control servos, read IMU directly
6. **WiFi/Bluetooth built-in** - ESP32 has both
7. **Real-time control** - No serial communication delay

### ❌ Disadvantages

1. **Lose OpenCat firmware** - All pre-built gaits gone
2. **Must reimplement everything**:
   - Servo control (PWM)
   - Gait algorithms
   - Inverse kinematics
   - IMU reading
   - Calibration
3. **Limited resources**:
   - ~520KB RAM (vs RPi's 512MB-8GB)
   - No OpenCV (too large)
   - Limited for AI/ML
4. **More complex setup** - Lower-level programming
5. **No official Petoi support** - You're on your own

## When to Use MicroPython on BiBoard

### ✅ Good fit if you want to:
- Learn robotics from the ground up
- Implement custom gaits/behaviors
- Have full control over the robot
- Minimize hardware/cost/weight
- Run simple autonomous behaviors
- Don't need computer vision

### ❌ Not good fit if you want to:
- Use existing OpenCat gaits (they'll be gone)
- Run computer vision (use RPi instead)
- Quick prototyping (OpenCat is easier)
- Run complex AI/ML (need more RAM)

---

## Architecture Comparison

### Option A: OpenCat Firmware + Python Control (Current)
```
Computer/RPi  →  [Serial]  →  BiBoard (OpenCat)  →  Servos
Python here        USB           C++ firmware        Controls
```

### Option B: MicroPython on BiBoard (This approach)
```
BiBoard (MicroPython)  →  Servos
Python runs here           Direct control
```

---

## How to Flash MicroPython

### Prerequisites

1. **Backup first!** Save your current OpenCat firmware
2. **Install esptool:**
   ```bash
   pip install esptool
   ```

### Step 1: Download MicroPython Firmware

```bash
# Download ESP32 MicroPython firmware
# Visit: https://micropython.org/download/esp32/
# Get latest stable release (v1.27.0 as of Feb 2026)

wget https://micropython.org/resources/firmware/ESP32_GENERIC-20251209-v1.27.0.bin
```

### Step 2: Erase Flash

```bash
# Connect BiBoard via USB
# Find port (macOS example)
ls /dev/cu.usbmodem5AA90272331

# Erase existing firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
```

### Step 3: Flash MicroPython

```bash
# Flash MicroPython firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin

# Wait for completion (~30 seconds)
```

### Step 4: Test Connection

```bash
# Install screen or use a serial terminal
screen /dev/cu.usbmodem5AA90272331 115200

# You should see Python REPL:
# >>>

# Test:
# >>> print("Hello from MicroPython!")
# >>> import sys
# >>> sys.platform
# 'esp32'
```

---

## Basic Servo Control with MicroPython

### Understanding the Hardware

BiBoard V1 uses a **servo controller chip** (likely PCA9685 or similar) connected via I2C to control the 12+ servo channels.

### Method 1: Using PWM (If Direct Connection)

```python
from machine import Pin, PWM
import time

# Create PWM for servo (example pin)
servo = PWM(Pin(2), freq=50)  # 50Hz for servos

def set_angle(angle):
    """Set servo angle (0-180 degrees)"""
    # Convert angle to duty cycle
    # Typical: 1ms (0°) to 2ms (180°) pulse
    min_duty = 40   # ~1ms at 50Hz
    max_duty = 115  # ~2ms at 50Hz

    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty(duty)

# Test
set_angle(90)  # Center
time.sleep(1)
set_angle(0)   # Min
time.sleep(1)
set_angle(180) # Max
```

### Method 2: Using I2C Servo Controller (More Likely)

BiBoard probably uses PCA9685 or similar:

```python
from machine import I2C, Pin
import time

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust pins for BiBoard

# PCA9685 address (usually 0x40)
PCA9685_ADDR = 0x40

class ServoController:
    def __init__(self, i2c, address=0x40):
        self.i2c = i2c
        self.address = address
        self.init_pca9685()

    def init_pca9685(self):
        """Initialize PCA9685"""
        # Set to sleep
        self.i2c.writeto_mem(self.address, 0x00, b'\x10')
        time.sleep(0.005)
        # Set prescale for 50Hz
        self.i2c.writeto_mem(self.address, 0xFE, b'\x79')
        # Wake up
        self.i2c.writeto_mem(self.address, 0x00, b'\x20')
        time.sleep(0.005)

    def set_servo(self, channel, angle):
        """Set servo angle (0-180) on channel (0-15)"""
        # Convert angle to pulse width
        pulse = int(150 + (angle / 180) * 600)  # Adjust range

        # Set PWM
        reg = 0x06 + 4 * channel
        self.i2c.writeto_mem(self.address, reg, bytes([0, 0]))
        self.i2c.writeto_mem(self.address, reg + 2,
                            bytes([pulse & 0xFF, pulse >> 8]))

# Use it
servos = ServoController(i2c)

# Control joint 0
servos.set_servo(0, 90)   # Center
time.sleep(1)
servos.set_servo(0, 45)   # Move
time.sleep(1)
servos.set_servo(0, 135)  # Move
```

---

## Complete Example: Basic Walk Gait

**Warning:** This is simplified. Real walking requires inverse kinematics and careful tuning!

```python
"""
Simple walking gait for Bittle using MicroPython
This is a basic example - real gaits are much more complex!
"""

from machine import I2C, Pin
import time
import math

class Bittle:
    """Simple Bittle controller"""

    # Joint mapping (example - verify with your BiBoard)
    JOINTS = {
        'front_left_shoulder': 0,
        'front_left_leg': 1,
        'front_right_shoulder': 2,
        'front_right_leg': 3,
        'rear_left_shoulder': 4,
        'rear_left_leg': 5,
        'rear_right_shoulder': 6,
        'rear_right_leg': 7,
        'head': 8,
    }

    def __init__(self):
        # Initialize I2C
        self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        self.servo_controller = ServoController(self.i2c)

    def stand(self):
        """Stand up position"""
        # Set all joints to standing pose
        # These values need calibration!
        self.servo_controller.set_servo(0, 90)  # FL shoulder
        self.servo_controller.set_servo(1, 45)  # FL leg
        self.servo_controller.set_servo(2, 90)  # FR shoulder
        self.servo_controller.set_servo(3, 45)  # FR leg
        self.servo_controller.set_servo(4, 90)  # RL shoulder
        self.servo_controller.set_servo(5, 45)  # RL leg
        self.servo_controller.set_servo(6, 90)  # RR shoulder
        self.servo_controller.set_servo(7, 45)  # RR leg

    def sit(self):
        """Sit down position"""
        self.servo_controller.set_servo(0, 90)
        self.servo_controller.set_servo(1, 90)  # Bend
        self.servo_controller.set_servo(2, 90)
        self.servo_controller.set_servo(3, 90)
        self.servo_controller.set_servo(4, 90)
        self.servo_controller.set_servo(5, 120) # Bend more
        self.servo_controller.set_servo(6, 90)
        self.servo_controller.set_servo(7, 120)

    def walk_forward(self, steps=4):
        """Simple walking - VERY basic!"""
        for step in range(steps):
            # Lift and move front-left & rear-right
            self.servo_controller.set_servo(1, 30)  # Lift FL
            self.servo_controller.set_servo(7, 30)  # Lift RR
            time.sleep(0.2)
            self.servo_controller.set_servo(0, 80)  # Move FL forward
            self.servo_controller.set_servo(6, 100) # Move RR forward
            time.sleep(0.2)
            self.servo_controller.set_servo(1, 45)  # Lower FL
            self.servo_controller.set_servo(7, 45)  # Lower RR
            time.sleep(0.2)

            # Lift and move front-right & rear-left
            self.servo_controller.set_servo(3, 30)  # Lift FR
            self.servo_controller.set_servo(5, 30)  # Lift RL
            time.sleep(0.2)
            self.servo_controller.set_servo(2, 100) # Move FR forward
            self.servo_controller.set_servo(4, 80)  # Move RL forward
            time.sleep(0.2)
            self.servo_controller.set_servo(3, 45)  # Lower FR
            self.servo_controller.set_servo(5, 45)  # Lower RL
            time.sleep(0.2)

# Main program
bittle = Bittle()
bittle.stand()
time.sleep(2)
bittle.walk_forward(steps=3)
time.sleep(1)
bittle.sit()
```

---

## WiFi Control with MicroPython

One big advantage: Built-in WiFi for remote control!

```python
"""
WiFi-controlled Bittle with MicroPython
"""

import network
import socket
from machine import Pin

# Connect to WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)

        while not wlan.isconnected():
            pass

    print('Connected! IP:', wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

# Simple command server
def run_server(bittle):
    # Connect WiFi
    ip = connect_wifi('YourWiFi', 'YourPassword')

    # Create socket
    addr = socket.getaddrinfo('0.0.0.0', 8888)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print(f'Listening on {ip}:8888')

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)

        request = cl.recv(1024).decode()
        command = request.strip()

        print(f'Command: {command}')

        # Execute commands
        if command == 'kup':
            bittle.stand()
        elif command == 'ksit':
            bittle.sit()
        elif command == 'kwkF':
            bittle.walk_forward(steps=3)

        cl.send('OK\n')
        cl.close()

# Run it
bittle = Bittle()
run_server(bittle)
```

Control from your computer:
```python
import socket

def send_command(ip, command):
    sock = socket.socket()
    sock.connect((ip, 8888))
    sock.send(command.encode())
    response = sock.recv(100)
    sock.close()
    return response

# Use it
send_command('192.168.1.100', 'kup')
send_command('192.168.1.100', 'kwkF')
send_command('192.168.1.100', 'ksit')
```

---

## Development Workflow

### Option 1: WebREPL (Wireless)

```python
# On BiBoard, enable WebREPL
import webrepl_setup
# Follow prompts to set password

# From computer, connect via browser:
# http://micropython.org/webrepl/
# Connect to ws://192.168.1.100:8266
```

### Option 2: File Sync Tools

```bash
# Install ampy or mpremote
pip install adafruit-ampy

# Upload files
ampy --port /dev/cu.usbmodem5AA90272331 put main.py
ampy --port /dev/cu.usbmodem5AA90272331 put servo_controller.py

# Run
ampy --port /dev/cu.usbmodem5AA90272331 run main.py
```

### Option 3: Thonny IDE

- Download Thonny: https://thonny.org/
- Configure for MicroPython ESP32
- Direct code upload and execution

---

## Challenges You'll Face

### 1. **Finding Pin Mappings**

You need to know:
- Which ESP32 pins connect to servo controller?
- I2C pins (SDA/SCL)?
- IMU pins?
- Other peripherals?

**Solution:** Reverse engineer from OpenCat firmware source code or BiBoard schematic.

### 2. **Calibration**

Each servo needs calibration (zero offset):
- OpenCat does this automatically
- You'll need to implement calibration routine
- Store calibration in non-volatile memory

### 3. **Gait Algorithms**

OpenCat has sophisticated gaits:
- Trot, crawl, walk, bound
- Inverse kinematics
- Balance control

You'll need to:
- Study robotics/kinematics
- Implement from scratch
- Or find existing libraries

### 4. **IMU Integration**

Read gyroscope/accelerometer:
- Likely MPU6050 or similar
- Connect via I2C
- Read and filter data
- Use for balance

```python
from machine import I2C
from mpu6050 import MPU6050  # Need library

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
imu = MPU6050(i2c)

accel = imu.get_accel_data()
gyro = imu.get_gyro_data()
```

---

## Resources

### MicroPython Docs
- https://docs.micropython.org/en/latest/esp32/quickref.html
- https://micropython.org/download/esp32/

### Libraries
- **servo-controller:** Search GitHub for PCA9685 MicroPython
- **mpu6050:** IMU library for MicroPython
- **kinematics:** Limited options, may need to write your own

### Hardware Info
- OpenCat firmware source: https://github.com/PetoiCamp/OpenCatEsp32
- Study this to understand pin mappings and hardware

---

## My Recommendation

### For Your Use Case (Wireless Without Tether):

**🤔 MicroPython is interesting but challenging:**

**Pros:**
- ✓ Achieves your goal (wireless, no tether)
- ✓ No extra hardware needed
- ✓ Python onboard
- ✓ Learning experience

**Cons:**
- ✗ Lose all OpenCat features
- ✗ Must reimplement everything
- ✗ Steep learning curve
- ✗ Time-consuming

### Better Alternatives:

**Option 1: Raspberry Pi (Still Best)**
- ✓ Keep OpenCat firmware (all gaits work)
- ✓ Full Python environment
- ✓ Can add camera/AI
- ✓ Proven solution
- Cost: $30-50

**Option 2: Fix Bluetooth**
- ✓ Keep OpenCat firmware
- ✓ No extra hardware
- ✓ May just need firmware update
- Cost: $0

**Option 3: WiFi Control**
- ✓ Keep OpenCat firmware
- ✓ Better range than Bluetooth
- ✓ Built-in capability
- Cost: $0

### Suggested Path:

1. **First:** Try fixing Bluetooth
   - Run diagnostic: `python examples/bluetooth_diagnostic.py`
   - Upload Standard firmware via Petoi Desktop App
   - Should take 30 minutes

2. **If Bluetooth fails:** Try WiFi
   - Configure via Petoi Desktop App
   - See `docs/wifi_control.md`

3. **For true autonomy:** Get Raspberry Pi
   - Best long-term solution
   - See `docs/onboard_setup.md`

4. **For learning:** Try MicroPython
   - Fun project!
   - But significant time investment
   - Start simple (just stand/sit)

---

## Conclusion

**Yes, you CAN run MicroPython on BiBoard V1**, but it's a significant project that requires:
- Hardware reverse engineering
- Gait algorithm implementation
- Calibration system
- Inverse kinematics

**It's doable if you:**
- Want to learn low-level robotics
- Have time for the project
- Don't mind starting from scratch

**But for practical wireless control:**
- Fix Bluetooth (easiest)
- Use WiFi (built-in)
- Add Raspberry Pi (most capable)

---

**Want to proceed with MicroPython anyway?** I can help you:
1. Reverse engineer BiBoard pin mappings
2. Create servo control library
3. Implement basic gaits
4. Set up development workflow

**Or want to try the practical solutions first?**
Let me know which direction you want to go!

---

**Last Updated:** 2026-02-10
