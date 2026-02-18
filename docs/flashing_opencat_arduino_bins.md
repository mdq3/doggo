# Flashing Arduino IDE Compiled Firmware

When you compile OpenCat firmware in Arduino IDE, it generates **multiple .bin files** that need to be flashed at specific memory addresses.

## The Four Required Files

After compilation, Arduino IDE creates these files:

1. **`OpenCatEsp32.ino.bootloader.bin`** - ESP32 bootloader
   - Flash address: `0x1000`
   - Size: ~20-30KB

2. **`OpenCatEsp32.ino.partitions.bin`** - Partition table
   - Flash address: `0x8000`
   - Size: ~3KB

3. **`boot_app0.bin`** - Boot configuration (tells ESP32 which partition to boot)
   - Flash address: `0xe000`
   - Size: 4KB
   - **This file is NOT in your build directory - see below**

4. **`OpenCatEsp32.ino.bin`** - Your compiled application (the main firmware)
   - Flash address: `0x10000`
   - Size: ~1-2MB

## Where to Find the Files

### Files 1, 2, and 4 (from Arduino IDE)

When you compile, Arduino IDE shows the build directory path in the console output (if verbose mode is enabled).

**Find them:**

**macOS/Linux:**
```bash
# Look in Arduino's temp directory
ls /var/folders/*/T/arduino_build_*/OpenCatEsp32.ino.*
```

**Windows:**
```bash
# Look in temp directory
dir %TEMP%\arduino_build_*\OpenCatEsp32.ino.*
```

Or enable verbose output to see exact path:
- Arduino IDE → Preferences → "Show verbose output during: compilation"
- The console will show: "Writing output files to /path/to/build/directory"

### File 3: boot_app0.bin (from ESP32 Package)

This file is part of the ESP32 Arduino package, not your build.

**Location:**

**macOS:**
```bash
~/Library/Arduino15/packages/esp32/hardware/esp32/2.0.12/tools/partitions/boot_app0.bin
```

**Linux:**
```bash
~/.arduino15/packages/esp32/hardware/esp32/2.0.12/tools/partitions/boot_app0.bin
```

**Windows:**
```
C:\Users\[YourUsername]\AppData\Local\Arduino15\packages\esp32\hardware\esp32\2.0.12\tools\partitions\boot_app0.bin
```

**Copy it to your build directory:**
```bash
# macOS/Linux
cp ~/Library/Arduino15/packages/esp32/hardware/esp32/2.0.12/tools/partitions/boot_app0.bin .

# Windows (PowerShell)
copy $env:LOCALAPPDATA\Arduino15\packages\esp32\hardware\esp32\2.0.12\tools\partitions\boot_app0.bin .
```

## Flash All Four Files with esptool

Once you have all four files in the same directory:

```bash
# 1. Check your port
ls /dev/cu.*                    # macOS
ls /dev/ttyUSB*                 # Linux
# Windows: Check Device Manager (COM3, COM4, etc.)

# 2. Erase flash (important!)
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# 3. Flash all four files at their correct addresses
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

**Windows users:** Change the port to your COM port:
```bash
esptool --chip esp32 --port COM3 ^
    --baud 460800 ^
    --before default_reset --after hard_reset ^
    write-flash -z ^
    --flash_mode dio ^
    --flash_freq 80m ^
    --flash_size 4MB ^
    0x1000 OpenCatEsp32.ino.bootloader.bin ^
    0x8000 OpenCatEsp32.ino.partitions.bin ^
    0xe000 boot_app0.bin ^
    0x10000 OpenCatEsp32.ino.bin
```

## Understanding Flash Addresses

The ESP32 memory layout for BiBoard V1.0:

```
0x0000   - Reserved
0x1000   - Bootloader (stage 2 bootloader)
0x8000   - Partition table (defines memory layout)
0xe000   - OTA data / boot_app0 (which partition to boot)
0x10000  - Main application (your firmware starts here)
...
0x400000 - End of 4MB flash
```

## Verification

After flashing, you should see:

```
Hash of data verified.
Leaving...
Hard resetting via RTS pin...
```

Then test the firmware:

```bash
# Connect to serial monitor
screen /dev/cu.usbmodem5AA90272331 115200

# You should see:
# - Boot messages
# - Bittle firmware version
# - "Calibrated" or ready message

# Test a command
kup

# Bittle should stand up!
```

Exit screen: `Ctrl+A` then `K` then `Y`

## Troubleshooting

### "A fatal error occurred: Failed to connect"

1. Make sure BiBoard is connected via USB
2. Try unplugging and replugging
3. Check the port name is correct
4. Try a different USB cable
5. On some boards, hold BOOT button while connecting

### "A fatal error occurred: Invalid head of packet"

- The board is sending data while esptool is trying to connect
- Unplug battery if connected
- Use only USB power during flashing
- Try again

### "File not found: boot_app0.bin"

- You need to copy this file from your ESP32 package (see "File 3" section above)
- Make sure all four files are in the same directory

### Firmware boots but doesn't work

1. Double-check you flashed all four files
2. Verify the flash addresses are correct
3. Make sure you used the correct partition scheme when compiling (Minimal SPIFFS)
4. Recalibrate servos using Petoi Desktop App

### "Hash of data failed"

- Flash corruption
- Try slower baud rate: `--baud 115200` instead of `460800`
- Try different USB port or cable
- Erase flash and try again

## Quick Reference

**Essential esptool commands:**

```bash
# Backup current firmware
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 \
    read-flash 0x0 0x400000 backup.bin

# Erase everything
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 erase-flash

# Flash four files
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 --baud 460800 \
    write-flash -z --flash_mode dio --flash_freq 80m --flash_size 4MB \
    0x1000 bootloader.bin 0x8000 partitions.bin \
    0xe000 boot_app0.bin 0x10000 firmware.bin

# Check chip info
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 chip_id
esptool --chip esp32 --port /dev/cu.usbmodem5AA90272331 flash_id
```

---

**Last Updated:** 2026-02-11
