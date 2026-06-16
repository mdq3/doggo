"""Query parsing and route table in the HTTP command server (server.py)."""

import server
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


def test_motion_routes_are_callable_with_valid_kind():
    valid = (server._KIND_NONE, server._KIND_STEPS, server._KIND_TROT)
    for fn, kind in server._MOTION.values():
        assert callable(fn)
        assert kind in valid


def test_trot_routes_use_trot_kind():
    assert server._MOTION["/trot"][1] == server._KIND_TROT
    assert server._MOTION["/trot-ik"][1] == server._KIND_TROT


def test_motion_paths_are_unique_across_groups():
    paths = [path for _, routes in server._MOTION_GROUPS for path, *_ in routes]
    assert len(paths) == len(set(paths))
    assert set(paths) == set(server._MOTION)


def test_index_lists_every_route():
    body = server._index_body().decode()
    for path in server._MOTION:
        assert path in body
    for path, _ in server._DIAG_ROUTES:
        assert path in body
