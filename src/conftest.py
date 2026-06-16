"""Pytest loader for the test harness.

The harness logic (MicroPython module stubs + src/ path setup) lives in
test/test_harness.py. pytest only auto-loads files named conftest.py, and a conftest
applies to tests at or below its own directory — the co-located ``*_test.py`` files are
spread across gaits/, kinematics/, etc., so this loader sits at the src/ root to cover
them all. It runs once before any test is collected.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "test"))

import test_harness  # noqa: E402  (path to test/ must be set up first)

test_harness.install()
