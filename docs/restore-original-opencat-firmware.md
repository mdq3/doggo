# Restoring Original OpenCat Firmware

How to restore your BiBoard V1 back to the original Petoi OpenCat firmware.

## Why You Might Need This

- Want to go back to original Petoi functionality
- Need to use Petoi Mobile App or Desktop App
- Troubleshooting hardware issues
- Trying different approaches

**Don't worry!** It's easy to switch between MicroPython and OpenCat firmware.

---

## Quick Answer: Latest Firmware with esptool

**Where to get the latest Bittle X V2 firmware:**

Pre-compiled firmware binaries are **not publicly available** in GitHub releases. You have two options:

1. **Use Petoi Desktop App** (Easiest - recommended)
   - Download: https://github.com/PetoiCamp/DesktopAppRelease/releases
   - Latest: Version 1.2.7 (December 2025)
   - The app handles firmware download and flashing automatically

2. **Compile from source** (Advanced - for latest code or customization)
   - Clone: https://github.com/PetoiCamp/OpenCatEsp32
   - Latest commits on `main` branch contain newest features
   - See "Method 2, Option C" below for complete instructions

**Flash with esptool (if you have a .bin file):**

```bash
# Complete backup first!
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 biboard_backup_$(date +%Y%m%d).bin

# Erase and flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# If you have a complete 4MB backup/firmware file:
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 firmware.bin

# If you compiled from Arduino IDE (4 separate files):
# You need: .ino.bootloader.bin, .ino.partitions.bin, boot_app0.bin, .ino.bin
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z \
    --flash_mode dio --flash_freq 80m --flash_size 4MB \
    0x1000 OpenCatEsp32.ino.bootloader.bin \
    0x8000 OpenCatEsp32.ino.partitions.bin \
    0xe000 boot_app0.bin \
    0x10000 OpenCatEsp32.ino.bin
```

**Detailed instructions for each method below.**

---

## Method 1: Restore from Your Backup (RECOMMENDED)

If you followed the getting started guide, you backed up your original firmware before flashing MicroPython.

### Find Your Backup

The backup file is: `biboard_backup.bin` (4MB file)

Location: Wherever you ran the backup command (check your Downloads folder or project directory)

### Restore It

```bash
# Connect BiBoard via USB
# Find your port
ls /dev/cu.usbmodem5AA90272331  # macOS
ls /dev/ttyUSB0           # Linux
# Windows: Check Device Manager

# Erase flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# Write backup
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 biboard_backup.bin

# Wait for completion (~2 minutes)
# You'll see: "Hard resetting via RTS pin..."
```

**Done!** Your Bittle is back to original OpenCat firmware.

---

## Method 2: Download Fresh Firmware from Petoi

If you don't have a backup, download fresh firmware from Petoi.

### Option A: Use Petoi Desktop App (EASIEST)

1. **Download Petoi Desktop App**
   - Visit: https://www.petoi.com/pages/download-center
   - Download for your OS (Windows/macOS/Linux)

2. **Connect BiBoard**
   - Connect Bittle via USB Type-C

3. **Upload Firmware**
   - Open Petoi Desktop App
   - Go to "Firmware Uploader"
   - Product: **Bittle X V2**
   - Board: **BiBoard V1_0**
   - Mode: **Standard** (recommended)
   - Language: Your preference
   - Serial Port: Select your port
   - Click **Upload**

4. **Wait for Completion**
   - Takes 2-3 minutes
   - Do not disconnect during upload!

5. **Test**
   - Bittle should beep
   - Try basic commands in serial monitor
   - Or use Petoi Mobile App

**Success!** Original firmware restored.

### Option B: Extract Firmware from Desktop App (ADVANCED)

**Note:** Pre-compiled firmware binaries are NOT publicly available in GitHub releases. The firmware is bundled inside the Petoi Desktop App.

If you need the raw .bin files to flash with esptool:

1. **Download Petoi Desktop App**
   - Latest releases: https://github.com/PetoiCamp/DesktopAppRelease/releases
   - Version 1.2.7 (December 2025) is the latest as of Feb 2026

2. **Extract Firmware Files**

   The Desktop App stores firmware internally. After downloading:

   **Windows:**
   - Extract the .zip file
   - Look in the app directory for firmware files (usually in a `resources/` or `firmware/` subdirectory)

   **macOS/Linux:**
   - Right-click the .app → Show Package Contents
   - Navigate to `Contents/Resources/` or similar
   - Look for .bin files for BiBoard_V1_0

3. **Flash with esptool**

   Once you have the .bin file:

   ```bash
   # Find your port
   ls /dev/cu.usbmodem5AA90272331  # macOS
   ls /dev/ttyUSB0           # Linux
   # Windows: Check Device Manager (COM3, COM4, etc.)

   # Erase flash completely
   esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

   # Flash firmware to address 0x0
   esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
       --baud 460800 write-flash 0x0 BiBoard_V1_0_Standard.bin

   # Wait for completion
   # You'll see: "Hash of data verified."
   # Then: "Hard resetting via RTS pin..."
   ```

   **Important:** If you have a full firmware backup (4MB), flash it at address `0x0`. If you have separate bootloader files, see Option C for proper flash addresses.

### Option C: Compile from Source (ADVANCED)

If you want the absolute latest firmware or need to customize the code:

1. **Install Arduino IDE**
   - Download from: https://www.arduino.cc/en/software
   - Version 2.x recommended

2. **Install ESP32 Board Support**
   - File → Preferences → Additional Boards Manager URLs:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager
   - Search "ESP32"
   - Install **"ESP32 by Espressif" version 2.0.12** (CRITICAL: newer versions may cause boot failures)

3. **Configure ESP32 Package**

   Add this line to your ESP32 package's `sdkconfig.h` file:
   ```cpp
   #define CONFIG_DISABLE_HAL_LOCKS 1
   ```

   Location (example):
   - Windows: `C:\Users\[username]\AppData\Local\Arduino15\packages\esp32\hardware\esp32\2.0.12\tools\sdk\esp32\include\config\sdkconfig.h`
   - macOS: `~/Library/Arduino15/packages/esp32/hardware/esp32/2.0.12/tools/sdk/esp32/include/config/sdkconfig.h`
   - Linux: `~/.arduino15/packages/esp32/hardware/esp32/2.0.12/tools/sdk/esp32/include/config/sdkconfig.h`

4. **Install Required Libraries**
   - Tools → Manage Libraries
   - Install: **ArduinoJson**, **WebSockets**

5. **Download OpenCat Firmware**
   ```bash
   git clone https://github.com/PetoiCamp/OpenCatEsp32.git
   cd OpenCatEsp32
   ```

6. **Open and Configure**
   - Open `OpenCatEsp32/OpenCatEsp32.ino` in Arduino IDE
   - In the code, uncomment these lines:
     ```cpp
     #define BITTLE      // Or BITTLE_X for Bittle X V2
     #define BiBoard_V1_0
     ```

7. **Select Board Settings**
   - **Board:** ESP32 Dev Module
   - **Upload Speed:** 921600 (or 460800 if issues)
   - **Flash Frequency:** 80MHz
   - **Flash Mode:** DIO
   - **Flash Size:** 4MB (32Mb)
   - **Partition Scheme:** Minimal SPIFFS (1.9MB APP with OTA/190KB SPIFFS)
   - **Core Debug Level:** None
   - **Port:** Select your port (e.g., /dev/cu.usbmodem5AA90272331)

8. **Compile and Upload**

   **Option 1: Direct Upload from Arduino IDE**
   - Click Upload button
   - Wait 2-3 minutes
   - Done!

   **Option 2: Export Binary and Flash with esptool**

   a. Export compiled binary:
      - Sketch → Export Compiled Binary
      - Or enable verbose output: File → Preferences → "Show verbose output during: compilation"

   b. Find the compiled files in the build directory (shown in verbose output):
      - `OpenCatEsp32.ino.bin` (main firmware)
      - `OpenCatEsp32.ino.bootloader.bin` (bootloader)
      - `OpenCatEsp32.ino.partitions.bin` (partition table)
      - `boot_app0.bin` (boot configuration - copy from ESP32 package)

   c. Flash with esptool (complete command):
      ```bash
      # Erase flash first
      esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

      # Flash all components at their correct addresses
      esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
          --baud 460800 \
          --before default_reset --after hard_reset \
          write-flash -z \
          --flash_mode dio \
          --flash_freq 80m \
          --flash_size 4MB \
          0x1000 OpenCatEsp32.ino.bootloader.bin \
          0x8000 OpenCatEsp32.ino.partitions.bin \
          0xe000 boot_app0.bin \
          0x10000 OpenCatEsp32.ino.bin
      ```

   **Flash Address Reference:**
   - `0x1000` - Bootloader
   - `0x8000` - Partition table
   - `0xe000` - Boot app configuration
   - `0x10000` - Main application firmware

   **For detailed instructions on locating and flashing these four files, see `FLASHING_ARDUINO_BINS.md`**

---

## Verification

After restoring firmware, verify it works:

### Test 1: Serial Monitor

```bash
# Connect to serial port
screen /dev/cu.usbmodem5AA90272331 115200

# Send command
kup

# Bittle should stand up
# Success!
```

Exit: `Ctrl+A` then `K` then `Y`

### Test 2: Petoi Mobile App

1. Download Petoi Mobile App (iOS/Android)
2. Connect via Bluetooth
3. Try basic controls
4. Should work normally

### Test 3: Desktop App

1. Open Petoi Desktop App
2. Connect to Bittle
3. Try calibration or control functions

---

## Switching Between Firmwares

You can switch back and forth anytime:

### OpenCat → MicroPython

```bash
# Backup OpenCat first!
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 opencat_backup.bin

# Flash MicroPython
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20251209-v1.27.0.bin
```

### MicroPython → OpenCat

```bash
# Restore OpenCat
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 opencat_backup.bin
```

**Keep both backup files!** Then you can switch anytime.

---

## Troubleshooting

### "esptool: command not found"

Install esptool:
```bash
pip install esptool
```

### "Failed to connect to ESP32"

1. Unplug and replug USB
2. Try different USB cable
3. Check port name is correct
4. Hold BOOT button while connecting (if available)

### "Brownout detector was triggered"

- Power issue
- Use USB power (disconnect battery)
- Try different USB port
- Use powered USB hub

### Firmware won't boot after restore

1. Erase flash completely:
   ```bash
   esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
   ```

2. Flash again with slower baud:
   ```bash
   esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
       --baud 115200 write-flash 0x0 firmware.bin
   ```

3. Power cycle (unplug everything, wait 10 seconds, reconnect)

### Lost original backup

No problem! Use Method 2 to get fresh firmware from Petoi.

---

## Important Notes

### Calibration Required

After restoring OpenCat firmware, you'll need to recalibrate servos:

1. Use Petoi Desktop App → Calibration
2. Or follow: https://docs.petoi.com/

The calibration is stored separately and may need to be redone.

### Settings Lost

Switching firmware erases:
- WiFi credentials
- Calibration data (sometimes)
- Custom configurations

But it's easy to reconfigure using Petoi Desktop App.

### No Risk to Hardware

Flashing firmware **only** changes software. It cannot damage:
- BiBoard hardware
- Servos
- Sensors
- Other components

Safe to experiment!

---

## Which Firmware Should You Use?

### Use OpenCat If You Want:
- ✓ Pre-built gaits (walk, crawl, etc.)
- ✓ Petoi Mobile App control
- ✓ Easy calibration via Desktop App
- ✓ Official support
- ✓ Quick demos without coding

### Use MicroPython If You Want:
- ✓ Learn robotics from scratch
- ✓ Full control over robot
- ✓ Python development
- ✓ Custom gaits and behaviors
- ✓ Autonomous operation
- ✓ Educational project

**You can try both!** Just keep backups and switch anytime.

---

## Quick Reference

### Backup Current Firmware
```bash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 backup_$(date +%Y%m%d).bin
```

### Restore from Backup
```bash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    --baud 460800 write-flash 0x0 backup.bin
```

### Get Fresh OpenCat
Use Petoi Desktop App → Firmware Uploader

---

## Support

### Petoi Support
- Website: https://www.petoi.com/
- Forum: https://www.petoi.camp/forum
- Docs: https://docs.petoi.com/
- Email: support@petoi.com

### MicroPython Project
- This repository: Issues and PRs welcome
- MicroPython forum: https://forum.micropython.org/

---

**Remember:** Always backup before flashing! Keep multiple backups in different locations.

**Last Updated:** 2026-02-11
