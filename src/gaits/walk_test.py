"""Walk keyframe -> commanded-angle conversion (gaits/walk.py).

Guards the corrected 270-degree servo scale: the gait must convert OpenCat raw
angles with ``commanded = 90 + rotDir * raw``. The pre-2026-06 servo-scale bug came
from a different zero base (ZERO_POS = 65/115/...) compensating for a 1.5x error;
these tests fail if that scheme is reintroduced. They also assert no frame drives a
servo outside the driver's clamp.

A single identity test like this would have caught the original bug.
"""

import gaits.walk as walk

# Driver clamp from drivers/servo.py: 90 +/- 135.
_SERVO_MIN = -45
_SERVO_MAX = 225


def test_rotation_directions():
    assert walk._RD == (1, -1, -1, 1, -1, 1, 1, -1)


def test_zero_base_is_ninety():
    # The regression guard: commanded 90 == OpenCat raw 0, all eight joints.
    assert walk._ZERO == (90,) * 8


def test_squeeze_is_faithful():
    # The formula-equality test below assumes the shoulder squeeze is neutral.
    assert walk._SHOULDER_SQUEEZE == 1.0


def test_zero_frame_maps_to_centre():
    assert walk._to_commanded((0,) * 8) == {ch: 90 for ch in walk._CH}


def test_conversion_follows_formula():
    raw = (10, 20, 30, 40, 5, -5, 15, -15)
    got = walk._to_commanded(raw)
    expected = {walk._CH[i]: 90 + walk._RD[i] * raw[i] for i in range(8)}
    assert got == expected


def test_all_frames_within_servo_range():
    for raw in walk._FRAMES:
        for ch, angle in walk._to_commanded(raw).items():
            assert _SERVO_MIN <= angle <= _SERVO_MAX, (ch, angle, raw)
