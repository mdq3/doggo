"""Fall watchdog — automatically get back up when flipped over.

Mirrors the stock firmware's IMU_EXCEPTION_FLIPPED reaction (OpenCat imu.h
getImuException() + reaction.h): OpenCat plays the rc skill whenever
|roll| > 85 degrees. Here a background thread polls the IMU and plays
behaviors.recover() when all of:

  - body tilt > _FALLEN_DEG sustained for _FALLEN_HOLD_MS (a real fall,
    not a bounce mid-motion), and
  - no motion path has commanded the servos for _IDLE_MS (a gait/trick is
    not mid-play — poses.note_motion() timestamps every servo command), and
  - poses.motion_lock is free (the HTTP server is not running a command).

Tilt comes from IMU.tilt(): 0 = upright, 90 = on a side, 180 = upside down.

After _MAX_ATTEMPTS consecutive recoveries that leave the robot still fallen
it gives up until righted manually, so a weak battery doesn't cause endless
flailing. The attempt counter resets once the robot is seen upright.

Usage (started automatically by main.py):
    import fall_watchdog
    fall_watchdog.start()
    fall_watchdog.enabled = False  # pause detection; thread keeps running
"""

import _thread
import time

import poses

_POLL_S = 0.2
_FALLEN_DEG = 75  # tilt beyond this = fallen (OpenCat trips at |roll| > 85)
_UPRIGHT_DEG = 40  # tilt below this = upright; resets the attempt counter
_FALLEN_HOLD_MS = 1000
_IDLE_MS = 2000  # must exceed the longest behavior frame delay (1000ms)
_MAX_ATTEMPTS = 3

enabled = True
_running = False


def _watch(imu):
    from behaviors import recover

    fallen_since = None
    attempts = 0
    while _running:
        time.sleep(_POLL_S)
        if not enabled or poses.idle_ms() < _IDLE_MS:
            fallen_since = None
            continue
        try:
            tilt = imu.tilt()
        except OSError:
            continue  # transient I2C error (e.g. a gait just started reading)
        if tilt < _FALLEN_DEG:
            fallen_since = None
            if tilt < _UPRIGHT_DEG:
                attempts = 0
            continue
        now = time.ticks_ms()
        if fallen_since is None:
            fallen_since = now
            continue
        if time.ticks_diff(now, fallen_since) < _FALLEN_HOLD_MS:
            continue
        fallen_since = None
        if attempts > _MAX_ATTEMPTS:
            continue  # already gave up; wait to be righted manually
        attempts += 1
        if attempts > _MAX_ATTEMPTS:
            print(
                "Fall watchdog: still flipped after %d attempts - giving up "
                "until righted manually" % _MAX_ATTEMPTS
            )
            continue
        print(
            "Fall watchdog: flipped (tilt %d deg), recovering (attempt %d/%d)"
            % (tilt, attempts, _MAX_ATTEMPTS)
        )
        if not poses.motion_lock.acquire(0):
            continue  # an HTTP command started in the meantime
        try:
            recover()
        except Exception as e:
            print("Fall watchdog: recover failed:", e)
        finally:
            poses.motion_lock.release()


def start():
    """Start the watchdog thread (no-op if already running)."""
    global _running
    if _running:
        return
    try:
        from imu import IMU

        imu = IMU()
    except Exception as e:
        print("Fall watchdog: IMU unavailable:", e)
        return
    _running = True
    _thread.start_new_thread(_watch, (imu,))
    print("Fall watchdog running")


def stop():
    """Ask the watchdog thread to exit after its next poll."""
    global _running
    _running = False


def running():
    return _running
