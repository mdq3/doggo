# MicroPython on BiBoard - Complete Technical Analysis

Deep dive into running MicroPython on BiBoard V1, porting OpenCat, and computer vision possibilities.

## Part 1: Porting OpenCat to MicroPython

### YES, You Can Port OpenCat Gaits!

The good news: **Gait algorithms and inverse kinematics are just math** - they work the same in any language. The OpenCat C++ code can absolutely be translated to Python.

### What Needs to Be Ported

```
OpenCat C++ Architecture:
├── Servo Control (PWM/I2C drivers)     ← Hardware layer
├── Calibration System                  ← Data storage
├── Inverse Kinematics                  ← Pure math ✓ Easy to port
├── Gait Generators                     ← Pure math ✓ Easy to port
├── Balance/IMU Integration             ← Sensor fusion
└── Skill Sequences                     ← State machines ✓ Easy to port
```

**Difficulty Breakdown:**

| Component | Difficulty | Why |
|-----------|-----------|-----|
| **Inverse Kinematics** | ⭐ Easy | Just trigonometry, pure math |
| **Gait Algorithms** | ⭐⭐ Moderate | State machines, timing |
| **Servo Control** | ⭐⭐⭐ Hard | Need to understand I2C protocol |
| **IMU Reading** | ⭐⭐ Moderate | I2C sensor, available libraries |
| **Calibration** | ⭐ Easy | Store offsets in flash |

### Example: Porting Inverse Kinematics

**Original C++ (OpenCat):**
```cpp
// From OpenCat firmware
float computeIK(float x, float y, float* angles) {
    float l1 = 40.0;  // Upper leg length (mm)
    float l2 = 40.0;  // Lower leg length (mm)

    float d = sqrt(x*x + y*y);
    float a1 = atan2(y, x);
    float a2 = acos((l1*l1 + d*d - l2*l2) / (2*l1*d));

    angles[0] = a1 + a2;  // Shoulder angle

    float k = (x*x + y*y - l1*l1 - l2*l2) / (2*l1*l2);
    angles[1] = atan2(sqrt(1-k*k), k);  // Knee angle

    return 0;
}
```

**Ported to MicroPython:**
```python
import math

class InverseKinematics:
    """Port of OpenCat IK to MicroPython"""

    def __init__(self, upper_leg=40.0, lower_leg=40.0):
        self.l1 = upper_leg  # mm
        self.l2 = lower_leg  # mm

    def compute_leg_angles(self, x, y):
        """
        Compute joint angles for desired foot position

        Args:
            x: Forward/backward position (mm)
            y: Up/down position (mm)

        Returns:
            (shoulder_angle, knee_angle) in radians
        """
        # Distance from shoulder to target
        d = math.sqrt(x*x + y*y)

        # Shoulder angle
        a1 = math.atan2(y, x)
        a2 = math.acos((self.l1**2 + d**2 - self.l2**2) / (2*self.l1*d))
        shoulder = a1 + a2

        # Knee angle (law of cosines)
        k = (x*x + y*y - self.l1**2 - self.l2**2) / (2*self.l1*self.l2)
        knee = math.atan2(math.sqrt(1-k*k), k)

        return shoulder, knee

    def angles_to_degrees(self, shoulder, knee):
        """Convert radians to servo degrees (0-180)"""
        shoulder_deg = math.degrees(shoulder) + 90  # Offset for servo
        knee_deg = math.degrees(knee) + 90
        return shoulder_deg, knee_deg

# Use it
ik = InverseKinematics(upper_leg=40.0, lower_leg=40.0)

# Want foot at position (50mm forward, -30mm down)
shoulder, knee = ik.compute_leg_angles(50, -30)
shoulder_deg, knee_deg = ik.angles_to_degrees(shoulder, knee)

print(f"Shoulder: {shoulder_deg}°, Knee: {knee_deg}°")
```

**See? It's just math!** The algorithms are language-agnostic.

### Example: Porting a Gait

**IK-based Gait Concept (simplified):**

```python
class WalkGait:
    """Walk gait using IK — feet follow smooth arcs"""

    def __init__(self, ik, servo_controller):
        self.ik = ik
        self.servos = servo_controller
        self.step_height = 20  # mm
        self.step_length = 30  # mm
        self.phase = 0

    def update(self, dt):
        """Update gait (call periodically)"""
        freq = 1.0  # Hz
        self.phase += dt * freq * 2 * math.pi

        t = self.phase

        # Compute foot positions and IK angles for each leg
        fl_x = self.step_length * math.cos(t)
        fl_y = -40 + (self.step_height * math.sin(t) if math.sin(t) > 0 else 0)

        fl_shoulder, fl_knee = self.ik.compute_leg_angles(fl_x, fl_y)
        fl_s, fl_k = self.ik.angles_to_degrees(fl_shoulder, fl_knee)
        self.servos.set_servo(0, int(fl_s))  # FL shoulder
        self.servos.set_servo(1, int(fl_k))  # FL knee
        # ... repeat for other legs

# Use it
gait = WalkGait(ik, servo_controller)

# Main loop
while True:
    gait.update(0.02)  # 50Hz update rate
    time.sleep(0.02)
```

### Where to Get the Algorithms

**Option 1: Study OpenCat Source Code**

```bash
# Clone OpenCat ESP32 firmware
git clone https://github.com/PetoiCamp/OpenCatEsp32.git
cd OpenCatEsp32

# Key files to study:
# - src/motion.h - Gait algorithms
# - src/skill.h - Skill sequences
# - src/io.h - Servo control
# - InstinctX.h - Main skills file
```

Look for:
- Gait generators (walk, crawl)
- IK functions
- Servo mapping
- Calibration data

**Option 2: Use Existing Robotics Libraries**

MicroPython libraries for quadrupeds are rare, but concepts exist:

- **Spot Micro** - Open source quadruped (Python/ROS)
- **Stanford Pupper** - Similar robot (Python)
- **Research papers** on quadruped gaits

**Option 3: Start Simple, Build Up**

```python
# Phase 1: Static poses
def stand():
    """All legs at standing position"""
    set_all_servos([90, 45, 90, 45, 90, 45, 90, 45])

def sit():
    """Sitting position"""
    set_all_servos([90, 90, 90, 90, 90, 120, 90, 120])

# Phase 2: Simple movements
def walk_forward_simple():
    """Very basic walk - lift legs one at a time"""
    # Step 1: Lift FL
    # Step 2: Move FL forward
    # Step 3: Lower FL
    # Repeat for each leg...

# Phase 3: Add IK
def walk_with_ik():
    """Use IK for smooth movements"""
    # Move foot in arc
    # IK computes joint angles
    # Smoother motion

# Phase 4: Proper gaits
def smooth_walk():
    """IK-based smooth walking gait"""
    # Implement phase-based control
    # Like example above
```

---

## Part 2: Computer Vision on ESP32 - The FULL Story

### Why "No OpenCV" - RAM Constraints Explained

**OpenCV is MASSIVE:**
- Full OpenCV library: ~100-500 MB
- Single OpenCV image in memory: ~1-10 MB (for 640x480 RGB)
- Basic face detection model: ~5-10 MB
- YOLO object detection: ~50-200 MB

**ESP32 has:**
- **Total RAM: ~520 KB** (0.5 MB)
- Available RAM after MicroPython: ~100-200 KB
- That's **1/1000th** of what OpenCV needs!

**Example:**
```
640x480 RGB image = 640 × 480 × 3 bytes = 921,600 bytes ≈ 900 KB

ESP32 has only 520 KB total
Image alone won't fit!
```

### BUT... Computer Vision IS Possible!

The key: **Use lightweight alternatives designed for microcontrollers**

Here's what DOES work:

---

## Option 1: ESP32-CAM Module

**Hardware Upgrade: Add ESP32-CAM ($8)**

The ESP32-CAM is a separate module with:
- Same ESP32 chip
- 2MP camera (OV2640)
- PSRAM (4MB extra RAM for images)
- Still limited, but usable!

```
┌──────────────────┐
│   BiBoard ESP32  │  ← Main controller (servos, gaits)
│                  │
└────────┬─────────┘
         │ Serial/WiFi
         ↓
┌──────────────────┐
│   ESP32-CAM      │  ← Vision processing
│   - Camera       │
│   - 4MB PSRAM    │
│   - TensorFlow   │
│     Lite Micro   │
└──────────────────┘
```

**What You Can Do:**
- Color blob detection
- Motion detection
- Simple edge detection
- Basic object recognition (tiny models)

**Example - Color Tracking:**
```python
# On ESP32-CAM
import camera

# Initialize camera
camera.init(framesize=camera.FRAME_QVGA)  # 320x240
camera.set_pixformat(camera.PIXFORMAT_RGB565)

def find_red_object():
    """Find largest red blob"""
    img = camera.capture()

    # Simple threshold (no OpenCV!)
    red_pixels = []
    for y in range(img.height()):
        for x in range(img.width()):
            r, g, b = img.get_pixel(x, y)

            # Is it red?
            if r > 150 and g < 100 and b < 100:
                red_pixels.append((x, y))

    if red_pixels:
        # Find centroid
        cx = sum(p[0] for p in red_pixels) // len(red_pixels)
        cy = sum(p[1] for p in red_pixels) // len(red_pixels)
        return cx, cy

    return None

# Track red ball
while True:
    pos = find_red_object()
    if pos:
        cx, cy = pos
        # Send to BiBoard to follow
        print(f"Red object at {cx}, {cy}")
```

---

## Option 2: TensorFlow Lite for Microcontrollers

**Yes, you can run neural networks on ESP32!**

TensorFlow Lite Micro is designed for tiny devices:
- Models: 10-100 KB (vs 50-200 MB for full models)
- RAM usage: 50-200 KB
- Works on ESP32!

**What You Can Recognize:**
- Person detection (basic)
- Simple objects (ball, cup, etc.)
- Gestures
- Basic image classification

**Example - Person Detection:**

```python
# Using TensorFlow Lite for Microcontrollers
# (Requires compiled model and C++ integration)

import tflite_micro

# Load tiny person detection model (~20KB)
model = tflite_micro.load_model('person_detect.tflite')

def detect_person():
    """Detect if person is in frame"""
    img = camera.capture()

    # Resize to model input (96x96 grayscale)
    img_small = resize_grayscale(img, 96, 96)

    # Run inference
    result = model.predict(img_small)

    # result[0] = confidence (0-255)
    person_detected = result[0] > 128

    return person_detected

# Follow person
while True:
    if detect_person():
        print("Person detected! Moving closer...")
        # Send command to BiBoard
    else:
        print("Searching...")
```

**Pre-trained Models Available:**
- Person detection
- Face detection
- Keyword spotting
- Gesture recognition

**Where to get:**
- TensorFlow Lite Model Zoo
- Edge Impulse (training platform)
- Community models

---

## Option 3: Edge Impulse

**Edge Impulse** (https://www.edgeimpulse.com/) lets you train custom tiny models:

1. **Collect training data** (images of what you want to recognize)
2. **Train in cloud** (free tier available)
3. **Export TFLite model** optimized for ESP32
4. **Deploy to ESP32**

**Example Use Cases:**
- "Detect my cat" - train on cat photos
- "Recognize hand gestures" - train on gesture videos
- "Find tennis ball" - train on ball images

**Model sizes:** 10-50 KB typically

---

## Option 4: Simple Computer Vision (No ML)

You don't always need machine learning! Classic CV works:

### A. Color Detection
```python
def find_orange_ball():
    """Find orange ball (no ML needed)"""
    img = camera.capture()

    # HSV color space better for color detection
    hsv = rgb_to_hsv(img)

    # Orange color range
    orange_pixels = []
    for y in range(img.height()):
        for x in range(img.width()):
            h, s, v = hsv[y][x]
            if 10 < h < 25 and s > 100:  # Orange hue
                orange_pixels.append((x, y))

    # Find largest blob (simple clustering)
    if len(orange_pixels) > 100:
        return get_blob_center(orange_pixels)

    return None
```

### B. Edge Detection (Simplified Sobel)
```python
def detect_edges(img):
    """Simple edge detection"""
    edges = []
    for y in range(1, img.height()-1):
        for x in range(1, img.width()-1):
            # Sobel operator (simplified)
            gx = abs(img[y][x+1] - img[y][x-1])
            gy = abs(img[y+1][x] - img[y-1][x])
            if gx + gy > threshold:
                edges.append((x, y))
    return edges
```

### C. Motion Detection
```python
prev_frame = None

def detect_motion():
    """Detect moving objects"""
    global prev_frame

    current = camera.capture_grayscale()

    if prev_frame is None:
        prev_frame = current
        return None

    # Find differences
    diff = []
    for y in range(current.height()):
        for x in range(current.width()):
            if abs(current[y][x] - prev_frame[y][x]) > 30:
                diff.append((x, y))

    prev_frame = current

    if len(diff) > 500:  # Significant motion
        return get_blob_center(diff)

    return None
```

---

## Option 5: Hybrid Approach - WiFi + Computer Vision

**Best of both worlds:**

```
┌─────────────────────┐
│   Your Computer     │  ← Heavy CV processing
│   OpenCV, YOLO, etc │     (Full power!)
│   Camera connected  │
└─────────┬───────────┘
          │ WiFi
          ↓ (Send commands)
┌─────────────────────┐
│   BiBoard ESP32     │  ← Execute movements
│   MicroPython       │
│   Gaits, Control    │
└─────────────────────┘
```

**How it works:**
1. Camera on your computer/laptop
2. Run full OpenCV/YOLO for detection
3. Send high-level commands via WiFi: "ball at 30° left"
4. BiBoard executes motion to track

**Example:**

**On Computer:**
```python
import cv2
import socket

# Connect to BiBoard
bittle = socket.socket()
bittle.connect(('192.168.1.100', 8888))

# Camera
cap = cv2.VideoCapture(0)

# YOLO or any CV you want
while True:
    ret, frame = cap.read()

    # Run object detection (full power!)
    objects = detect_objects(frame)  # Your favorite CV

    if 'ball' in objects:
        ball_x, ball_y = objects['ball']

        # Compute angle
        angle = compute_angle_from_center(ball_x, frame.width)

        # Send to Bittle
        if angle > 10:
            bittle.send(b'turn_left\n')
        elif angle < -10:
            bittle.send(b'turn_right\n')
        else:
            bittle.send(b'walk_forward\n')
```

**On BiBoard:**
```python
# Receive commands and execute
def command_server():
    while True:
        cmd = receive_command()

        if cmd == 'turn_left':
            execute_turn(-15)  # degrees
        elif cmd == 'turn_right':
            execute_turn(15)
        elif cmd == 'walk_forward':
            walk_gait.step()
```

**Advantages:**
- ✓ Full OpenCV power
- ✓ Any ML models you want
- ✓ BiBoard just does motion
- ✗ Requires computer running nearby

**For demos/development, this works great!**

---

## Option 6: Future - Raspberry Pi Pico 2 or ESP32-S3

Newer microcontrollers have more RAM:

- **ESP32-S3**: Up to 8MB PSRAM
- **Raspberry Pi Pico 2**: 520KB SRAM, ARM Cortex-M33

More RAM = Better CV possibilities

---

## Realistic CV Capabilities Summary

### What ESP32 CAN Do:

| Task | Feasible? | Method | RAM Needed |
|------|-----------|--------|------------|
| **Color tracking** | ✅ Yes | Pixel thresholding | ~50 KB |
| **Motion detection** | ✅ Yes | Frame differencing | ~50 KB |
| **Simple edge detection** | ✅ Yes | Sobel filter | ~50 KB |
| **Person detection** | ✅ Yes | TFLite Micro model | ~100 KB |
| **Face detection** | ⚠️ Basic | TFLite Micro model | ~150 KB |
| **Object classification** | ⚠️ Limited | TFLite Micro (few classes) | ~100 KB |
| **QR code reading** | ✅ Yes | Specialized library | ~100 KB |
| **Line following** | ✅ Yes | Edge detection | ~50 KB |
| **Blob detection** | ✅ Yes | Connected components | ~100 KB |

### What ESP32 CANNOT Do:

| Task | Why Not? |
|------|----------|
| **Full OpenCV** | Needs 100+ MB RAM |
| **YOLO object detection** | Models are 50-200 MB |
| **Real-time SLAM** | Needs GB of RAM |
| **High-res video** | RAM + processing power |
| **Multiple complex models** | Not enough RAM |

### Workarounds:

1. **Use computer** for heavy CV → Send commands to ESP32
2. **Add ESP32-CAM** with PSRAM for better capability
3. **Use tiny models** (TFLite Micro)
4. **Classic CV** instead of ML (color, edges, motion)

---

## Complete Vision-Enabled System Architecture

### Architecture 1: ESP32-Only (Basic CV)

```
┌────────────────────────────────────┐
│      BiBoard V1 ESP32              │
│  ┌──────────────┐ ┌─────────────┐ │
│  │ MicroPython  │ │ Servo       │ │
│  │ - Gaits      │→│ Control     │ │
│  │ - IK         │ └─────────────┘ │
│  │ - Balance    │                 │
│  └──────────────┘                 │
└────────────────────────────────────┘
        ↑ Serial
┌────────────────────────────────────┐
│      ESP32-CAM ($8)                │
│  ┌──────────────┐                  │
│  │ Camera       │ ← OV2640 2MP     │
│  │ Vision       │                  │
│  │ - TFLite     │                  │
│  │ - Color track│                  │
│  └──────────────┘                  │
└────────────────────────────────────┘
```

**Capabilities:**
- Color tracking (follow ball)
- Person detection (follow person)
- Motion detection
- Basic gestures

**Cost:** ~$8 for ESP32-CAM

### Architecture 2: Hybrid (Best CV)

```
┌────────────────────────────────────┐
│   Computer/Laptop                  │
│  ┌──────────────┐                  │
│  │ Full OpenCV  │ ← Webcam         │
│  │ YOLO, etc    │                  │
│  └──────┬───────┘                  │
└─────────│───────────────────────────┘
          │ WiFi
          ↓
┌────────────────────────────────────┐
│      BiBoard ESP32 + MicroPython   │
│  - Receives high-level commands    │
│  - Executes gaits                  │
│  - Returns status                  │
└────────────────────────────────────┘
```

**Capabilities:**
- ANY computer vision you want
- Full OpenCV
- Deep learning
- Real-time tracking

**Cost:** $0 (use existing computer)

---

## Recommendations for Your Project

### Phase 1: Get MicroPython Running (Week 1)
1. Flash MicroPython
2. Test servo control
3. Implement basic poses (stand, sit)

### Phase 2: Port Gaits ✅
1. ~~Study OpenCat source~~ ✅
2. Port IK functions (TODO — `kinematics/`)
3. ~~Implement simple walk~~ ✅ (`src/gaits/walk.py`)

### Phase 3: Add Basic Vision (Week 4)
**Choose ONE:**

**Option A: ESP32-CAM ($8)**
- Add ESP32-CAM module
- Start with color tracking
- Follow colored ball
- Simple and effective

**Option B: Computer Vision**
- Use laptop webcam
- Full OpenCV power
- Send commands via WiFi
- Great for demos

**Option C: TensorFlow Lite**
- Person detection
- Follow person around
- Requires model training

### Phase 4: Advanced Features (Ongoing)
- Better gaits (crawl, bound)
- IMU integration for balance
- Obstacle avoidance
- Autonomous behaviors

---

## Final Verdict

### Can you port OpenCat to MicroPython?
**YES!** ✅ The math is language-agnostic. It's work, but totally doable.

### Can you do computer vision on ESP32?
**YES, but limited** ⚠️

- **Can do:** Color tracking, motion detection, person detection (basic), simple object recognition
- **Cannot do:** Full OpenCV, YOLO, complex deep learning
- **Best approach:** Hybrid (heavy CV on computer, motion on ESP32)

### Is this worth it?
**If you enjoy the challenge:** Absolutely! ✅

You'll learn:
- Robotics algorithms
- Inverse kinematics
- Gait generation
- Embedded systems
- MicroPython
- Computer vision fundamentals

**If you just want it working:** Consider Raspberry Pi 🤔

Raspberry Pi gives you:
- Full Python
- Full OpenCV
- All the RAM you need
- Keep OpenCat firmware

---

## I'm Ready to Help!

Want to proceed with MicroPython? I can help you:

1. **Flash MicroPython** and test
2. **Reverse engineer BiBoard** pin mappings
3. **Port OpenCat IK** to Python
4. **Implement gaits** step by step
5. **Add ESP32-CAM** for vision
6. **Train TFLite models** for recognition

**Or want to try Raspberry Pi instead?** That's great too!

**What sounds most interesting to you?**

---

**Last Updated:** 2026-02-19
