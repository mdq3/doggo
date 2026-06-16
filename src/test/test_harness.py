"""Test harness: stub MicroPython-only modules so the firmware imports on host CPython.

The firmware targets MicroPython on an ESP32. Several modules (``machine``, ``utime``,
``esp``, ``network``, ``webrepl``) and the MicroPython ``time.ticks_*`` / ``sleep_us``
extensions do not exist on host CPython. ``install()`` registers lightweight stubs in
``sys.modules`` and prepends ``src/`` to the path so the firmware's absolute imports
(``poses``, ``gaits.*``, ``kinematics.*``) resolve. ``src/conftest.py`` calls ``install()``
once before any test is collected.

Tests live next to the source they cover, named ``<source>_test.py`` (e.g.
``src/kinematics/leg.py`` -> ``src/kinematics/leg_test.py``).

The stubs only need to make import succeed — the pure-logic functions under test never
touch hardware. Anything that does (servo PWM, I2C reads, ADC) is exercised on-device,
not here.
"""

import sys
import time
import types
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent  # this file lives at src/test/


class _Dummy:
    """No-op stand-in for hardware peripheral classes (PWM/Pin/I2C/ADC).

    Construction and any attribute access are silently accepted so that importing
    a module that instantiates these at load time (e.g. ``poses`` builds ``Servos()``)
    does not fail.
    """

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, _name):
        return lambda *a, **k: None


class _ADC(_Dummy):
    """ADC stub exposing the class-level attenuation constant battery.py reads."""

    ATTN_11DB = 3


def _install_stub(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


# Augment the real time module with the MicroPython tick/sleep extensions.
def _ticks_ms():
    return int(time.monotonic() * 1000)


def _ticks_us():
    return int(time.monotonic() * 1_000_000)


def _ticks_diff(a, b):
    return a - b


def _sleep_ms(ms):
    time.sleep(ms / 1000)


def _sleep_us(us):
    time.sleep(us / 1_000_000)


def install():
    """Install MicroPython stubs and put src/ on the import path. Idempotent."""
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))

    if not hasattr(time, "ticks_ms"):
        time.ticks_ms = _ticks_ms
        time.ticks_us = _ticks_us
        time.ticks_diff = _ticks_diff
        time.sleep_ms = _sleep_ms
        time.sleep_us = _sleep_us

    _install_stub(
        "machine",
        PWM=_Dummy,
        Pin=_Dummy,
        I2C=_Dummy,
        ADC=_ADC,
        freq=lambda *a: 240_000_000,
        unique_id=lambda: b"\x00\x00\x00\x00\x00\x00",
        reset=lambda: None,
    )
    _install_stub("esp", flash_size=lambda: 4 * 1024 * 1024)
    _install_stub("network", STA_IF=0, WLAN=_Dummy, hostname=lambda *a: None)
    _install_stub("webrepl", start=lambda *a, **k: None)
    _install_stub(
        "utime",
        ticks_ms=time.ticks_ms,
        ticks_us=time.ticks_us,
        ticks_diff=time.ticks_diff,
        sleep_ms=time.sleep_ms,
        sleep_us=time.sleep_us,
    )
