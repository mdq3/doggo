"""ICM-42670-P IMU driver with complementary filter.

WHO_AM_I = 0x67 (not ICM-20600 which is 0x11 — different chip, different register map).
Hardware: I2C address 0x69, SDA=GPIO21, SCL=GPIO22, 400kHz.
BiBoard V1.0 (Doggo).

Register map (ICM-42670-P, bank 0):
  0x01  DEVICE_CONFIG    bit0 = soft reset
  0x1F  PWR_MGMT0        [3:2] gyro mode, [1:0] accel mode (0x0F = both LN)
  0x20  GYRO_CONFIG0     [6:4] FS, [3:0] ODR
  0x21  ACCEL_CONFIG0    [6:5] FS, [3:0] ODR
  0x0B  ACCEL_DATA_X1    MSB  } 12 bytes contiguous:
  ...                         } ax(2) ay(2) az(2) gx(2) gy(2) gz(2)
  0x16  GYRO_DATA_Z0     LSB  }

Sensitivity after config:
  Accel ±2g  → 16384 LSB/g   (ACCEL_CONFIG0 = 0x66)
  Gyro ±500dps → 65.5 LSB/dps (GYRO_CONFIG0  = 0x26)

Usage:
    from imu import IMU
    imu = IMU()
    pitch, roll = imu.read()  # degrees; 0 = level; ~0.3ms per call

Smoke test:
    from imu import IMU; imu = IMU(); print(imu.read())
    # Flat: (0±2, 0±2).  Nose-up → +pitch.  Roll right → +roll.
"""

import time
from math import atan2, sqrt

from machine import I2C, Pin
from utime import ticks_diff, ticks_ms

_ADDR = 0x69


def _s16(buf, offset):
    v = (buf[offset] << 8) | buf[offset + 1]
    return v - 65536 if v >= 32768 else v


def _accel_angles(buf):
    ax = _s16(buf, 0) / 16384.0
    ay = _s16(buf, 2) / 16384.0
    az = _s16(buf, 4) / 16384.0
    pitch = atan2(ax, sqrt(ay * ay + az * az)) * 57.2958
    roll = atan2(ay, sqrt(ax * ax + az * az)) * 57.2958
    return pitch, roll, _s16(buf, 6) / 65.5, _s16(buf, 8) / 65.5


class IMU:
    """ICM-42670-P driver. Instantiate once; call read() each frame."""

    def __init__(self):
        self._i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)

        self._i2c.writeto_mem(_ADDR, 0x1F, b"\x0f")  # accel + gyro, low-noise mode
        time.sleep_ms(60)  # gyro LN startup: ~60ms from off

        self._i2c.writeto_mem(_ADDR, 0x20, b"\x26")  # gyro  ±500 dps, 100 Hz
        self._i2c.writeto_mem(_ADDR, 0x21, b"\x66")  # accel ±2g,      100 Hz

        # Seed filter directly from accelerometer (skip 0.98^N convergence)
        raw = self._i2c.readfrom_mem(_ADDR, 0x0B, 10)
        self._pitch, self._roll, _, _ = _accel_angles(raw)
        self._last_t = ticks_ms()

    def read(self) -> tuple[float, float]:
        """Return (pitch_deg, roll_deg) via complementary filter.

        Nose-up    → positive pitch.
        Roll right → positive roll.
        """
        raw = self._i2c.readfrom_mem(_ADDR, 0x0B, 10)
        accel_pitch, accel_roll, gx, gy = _accel_angles(raw)

        now = ticks_ms()
        dt = ticks_diff(now, self._last_t) / 1000.0
        self._last_t = now

        self._pitch = 0.98 * (self._pitch + gy * dt) + 0.02 * accel_pitch
        self._roll = 0.98 * (self._roll - gx * dt) + 0.02 * accel_roll

        return self._pitch, self._roll
