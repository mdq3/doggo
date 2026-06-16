"""Pure decoding/trig in the IMU driver (imu.py): _s16 and _accel_angles.

The I2C transport is hardware; these cover the byte unpacking and the
accel-to-angle trig that run on every read().
"""

import struct

import pytest

from imu import _accel_angles, _s16

_ACCEL_LSB = 16384.0  # LSB/g at +/-2g
_GYRO_LSB = 65.5  # LSB/dps at +/-500dps


def _buf(ax, ay, az, gx=0, gy=0):
    # Big-endian signed 16-bit, matching the ICM-42670-P data registers.
    return struct.pack(">hhhhh", ax, ay, az, gx, gy)


def test_s16_two_complement():
    assert _s16(bytes([0x00, 0x00]), 0) == 0
    assert _s16(bytes([0x7F, 0xFF]), 0) == 32767
    assert _s16(bytes([0x80, 0x00]), 0) == -32768
    assert _s16(bytes([0xFF, 0xFF]), 0) == -1


def test_s16_honours_offset():
    buf = bytes([0x00, 0x00, 0x12, 0x34])
    assert _s16(buf, 2) == 0x1234


def test_accel_angles_level():
    pitch, roll, gx, gy = _accel_angles(_buf(0, 0, int(_ACCEL_LSB)))
    assert pitch == pytest.approx(0.0, abs=1e-6)
    assert roll == pytest.approx(0.0, abs=1e-6)


def test_accel_angles_nose_up_45():
    # ax = az = 1g -> pitch = atan2(1, 1) = 45 degrees, roll = 0.
    pitch, roll, _, _ = _accel_angles(_buf(int(_ACCEL_LSB), 0, int(_ACCEL_LSB)))
    assert pitch == pytest.approx(45.0, abs=1e-3)
    assert roll == pytest.approx(0.0, abs=1e-6)


def test_accel_angles_roll_right_45():
    pitch, roll, _, _ = _accel_angles(_buf(0, int(_ACCEL_LSB), int(_ACCEL_LSB)))
    assert roll == pytest.approx(45.0, abs=1e-3)
    assert pitch == pytest.approx(0.0, abs=1e-6)


def test_accel_angles_gyro_scaling():
    buf = _buf(0, 0, int(_ACCEL_LSB), gx=int(_GYRO_LSB * 10), gy=int(_GYRO_LSB * -5))
    _, _, gx, gy = _accel_angles(buf)
    assert gx == pytest.approx(10.0, abs=0.1)
    assert gy == pytest.approx(-5.0, abs=0.1)
