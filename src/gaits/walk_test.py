"""Walk gait transform and frame safety (gaits/walk.py).

The generic 90 + rotDir*raw conversion is covered in player_test.py; here we check
walk's own shoulder-squeeze transform and that no frame drives a servo out of range.
"""

import gaits.walk as walk
from gaits import player

# Driver clamp from drivers/servo.py: 90 +/- 135.
_SERVO_MIN = -45
_SERVO_MAX = 225


def test_squeeze_is_faithful():
    assert walk._SHOULDER_SQUEEZE == 1.0


def test_transform_is_identity_when_faithful():
    # With squeeze 1.0 the shoulder transform is a no-op; legs always pass through.
    for i in range(8):
        assert walk._transform(i, 37) == 37


def test_all_frames_within_servo_range():
    for raw in walk._FRAMES:
        for ch, angle in player.to_commanded(raw, walk._transform).items():
            assert _SERVO_MIN <= angle <= _SERVO_MAX, (ch, angle, raw)
