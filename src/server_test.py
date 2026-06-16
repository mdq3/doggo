"""Query-string parsing in the HTTP command server (server.py)."""

from server import _parse_imu, _parse_on, _parse_steps


def test_parse_steps_basic():
    assert _parse_steps("steps=5") == 5


def test_parse_steps_among_other_params():
    assert _parse_steps("imu=1&steps=3") == 3


def test_parse_steps_missing():
    assert _parse_steps("") is None
    assert _parse_steps(None) is None
    assert _parse_steps("foo=1") is None


def test_parse_steps_non_integer():
    assert _parse_steps("steps=abc") is None


def test_parse_imu_default_on():
    assert _parse_imu(None) is True
    assert _parse_imu("") is True
    assert _parse_imu("imu=1") is True


def test_parse_imu_off_values():
    assert _parse_imu("imu=0") is False
    assert _parse_imu("imu=false") is False
    assert _parse_imu("imu=off") is False


def test_parse_on():
    assert _parse_on(None) is None
    assert _parse_on("") is None
    assert _parse_on("on=1") is True
    assert _parse_on("on=0") is False
    assert _parse_on("on=off") is False
