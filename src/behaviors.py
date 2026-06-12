"""
Behavior (trick) player — ported from OpenCatEsp32 InstinctBittleESP.h behavior arrays.

Behaviors differ from gaits: each frame carries its own transition speed and
post-frame delay, and an optional loop section replays a sub-range of frames.
Playback follows OpenCat skill.h perform() + motion.h transform():
  - per-frame target reached with cosine-eased interpolation,
    degrees-per-step = speed_byte / 8, one step every 8 ms
  - speed_byte 0 → snap instantly to the frame target
  - after each frame: sleep(delay_byte × 50 ms)
  - loop spec (loop_from, loop_to, repeat): after playing frame loop_to, jump
    back to loop_from until the section has played `repeat` times in total

Frame tuple (raw OpenCat degrees; commanded = 90 + rotDir * raw):
  (head, FL_sh, FR_sh, RR_sh, RL_sh, FL_leg, FR_leg, RR_leg, RL_leg,
   speed_byte, delay_byte)

The original 16-joint rows also carry head-tilt, tail and shoulder-roll columns
(joints Bittle doesn't have — dropped) and per-frame IMU trigger bytes (zero in
every trick here — not implemented). All tricks below use angleDataRatio=1 and
both start and end near the balance (stand) pose.

Usage:
    from behaviors import wave, high_five, handshake, pee
    wave()
"""

import math
import time

from poses import (
    CH_FL_LEG,
    CH_FL_SHOULDER,
    CH_FR_LEG,
    CH_FR_SHOULDER,
    CH_HEAD,
    CH_RL_LEG,
    CH_RL_SHOULDER,
    CH_RR_LEG,
    CH_RR_SHOULDER,
    apply_calibration,
    current_pos,
    servos,
    stand,
)

# Frame column index -> channel / rotationDirection (head first, then OpenCat 8-15)
_CH = (
    CH_HEAD,
    CH_FL_SHOULDER,
    CH_FR_SHOULDER,
    CH_RR_SHOULDER,
    CH_RL_SHOULDER,
    CH_FL_LEG,
    CH_FR_LEG,
    CH_RR_LEG,
    CH_RL_LEG,
)
_RD = (1, 1, -1, -1, 1, -1, 1, 1, -1)

_HEAD_LIMIT = 85  # OpenCat Bittle head-pan angleLimit is ±85°
_STEP_DELAY = 0.008  # seconds per interpolation step (OpenCat: delay(DOF/2) ms)


def _to_commanded(frame):
    result = {}
    for i in range(9):
        raw = frame[i]
        if i == 0:
            raw = max(-_HEAD_LIMIT, min(_HEAD_LIMIT, raw))
        result[_CH[i]] = 90 + _RD[i] * raw
    return result


def _transform(targets, speed):
    """Move all joints to targets together, cosine-eased, finishing simultaneously.

    speed is the OpenCat per-frame speed byte (degrees-per-step = speed/8).
    speed <= 0 snaps straight to the target (used for rapid moves like moonwalk).
    """
    calibrated = {ch: apply_calibration(angle, ch) for ch, angle in targets.items()}

    steps = 0
    if speed > 0:
        max_diff = max(abs(calibrated[ch] - current_pos[ch]) for ch in calibrated)
        steps = round(max_diff * 8.0 / speed)

    if steps < 1:  # speed byte 0, or the move is too small to interpolate — snap
        for ch, angle in calibrated.items():
            servos.set_servo(ch, int(angle))
            current_pos[ch] = angle
        return

    start = {ch: current_pos[ch] for ch in calibrated}
    diff = {ch: calibrated[ch] - start[ch] for ch in calibrated}

    for s in range(1, steps + 1):
        frac = (1 - math.cos(math.pi * s / steps)) / 2
        for ch in calibrated:
            angle = start[ch] + diff[ch] * frac
            servos.set_servo(ch, int(angle))
            current_pos[ch] = angle
        time.sleep(_STEP_DELAY)


def _play(name):
    loop_from, loop_to, loop_count, frames = _BEHAVIORS[name]
    repeat = loop_count - 1 if loop_count >= 2 else 0

    try:
        c = 0
        while c < len(frames):
            frame = frames[c]
            _transform(_to_commanded(frame), frame[9])
            if frame[10]:
                time.sleep(abs(frame[10]) * 0.05)
            if repeat and c != 0 and c == loop_to:
                c = loop_from - 1
                repeat -= 1
            c += 1
    except KeyboardInterrupt:
        print("\n\nBehavior interrupted.")
        print("Returning to stand...")
        stand()


# {name: (loop_from, loop_to, loop_count, frames)}
_BEHAVIORS = {
    # hi — wave a front paw
    "hi": (1, 2, 3, (
        (0, 35, 30, 120, 105, 75, 60, -40, -30, 4, 2),
        (35, -99, 30, 125, 95, 40, 75, -45, -30, 10, 0),
        (40, -90, 30, 125, 95, 62, 75, -45, -30, 10, 0),
        (0, 45, 45, 105, 105, 45, 45, -45, -45, 8, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 5, 0),
    )),
    # fiv — high five
    "fiv": (0, 0, 0, (
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
        (18, 10, 24, 42, 28, 75, 46, 15, 38, 12, 0),
        (26, 21, 33, 28, 12, 49, 17, 15, 54, 16, 0),
        (26, 21, 33, 28, 7, 49, 17, 22, 39, 8, 0),
        (32, 30, 21, 62, 25, 72, 69, -23, 16, 16, 4),
        (15, -125, 21, 62, 25, 28, 69, -23, 16, 16, 2),
        (23, -109, 24, 62, 25, 59, 64, -23, 19, 12, 20),
        (0, 45, 38, 105, 105, 45, 45, -45, -45, 8, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
    )),
    # hsk — handshake
    "hsk": (2, 3, 3, (
        (36, 31, 30, 120, 50, 96, 60, -40, -12, 12, 2),
        (40, -60, 30, 125, 50, 47, 75, -45, -10, 16, 10),
        (35, -47, 30, 125, 50, 59, 75, -45, -9, 8, 1),
        (43, -60, 30, 125, 50, 47, 75, -45, -5, 8, 1),
        (35, -47, 30, 125, 50, 59, 75, -45, -12, 8, 20),
        (14, 45, 45, 105, 105, 45, 45, -45, -45, 12, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 12, 0),
    )),
    # pee — lift rear leg
    "pee": (2, 3, 3, (
        (30, 40, 40, 90, 45, 10, 60, 70, 45, 6, 0),
        (45, 60, 53, 115, 60, -30, 40, 50, 21, 2, 10),
        (30, 40, 40, 90, 45, 10, 50, 70, 45, 32, 0),
        (30, 40, 40, 103, 45, 10, 50, 80, 45, 32, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
    )),
    # pd — play dead (rolls onto side, twitches, recovers)
    "pd": (4, 5, 2, (
        (0, 45, 45, 105, 105, 45, 45, -45, -45, 8, 0),
        (0, 30, -80, 105, 15, 45, 80, -45, 80, 8, 0),
        (45, 30, 6, 6, 6, -60, 79, 79, 56, 16, 0),
        (45, 45, -75, 90, 6, -60, 0, -60, 56, 8, 20),
        (45, 45, -75, 90, 25, -60, 0, -60, 45, 30, 0),
        (45, 45, -75, 90, 25, -60, 0, -60, 30, 30, 0),
        (45, 45, -75, 90, 25, -60, 0, -60, 45, 16, 20),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
    )),
    # pu — push-ups
    "pu": (7, 8, 3, (
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
        (15, 30, 35, 40, 21, 50, 15, 15, 41, 8, 0),
        (15, 30, 35, 40, 30, 50, 15, 15, 14, 16, 0),
        (30, 27, 35, 40, 60, 50, 15, 20, 45, 16, 0),
        (15, 42, 35, 40, 60, 25, 20, 20, 60, 8, 0),
        (0, 48, 45, 75, 60, 20, 37, 20, 60, 12, 0),
        (-15, 60, 60, 70, 70, 15, 15, 60, 60, 16, 0),
        (0, 30, 30, 110, 110, 60, 60, 60, 60, 12, 1),
        (30, 70, 70, 85, 85, -50, -50, 60, 60, 16, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
    )),
    # mw — moonwalk
    "mw": (3, 10, 5, (
        (0, 51, 51, 51, 51, -12, -12, -12, -12, 8, 0),
        (0, 20, 20, 20, 20, 50, 50, 50, 50, 64, 0),
        (0, 49, 23, 61, 33, 10, 9, 6, 9, 16, 12),
        (0, 49, 23, 61, 33, 10, 9, 6, 9, 32, 4),
        (0, 38, 18, 50, 24, 30, 27, 24, 27, 0, 1),
        (0, 50, 29, 60, 42, 3, 34, -12, 24, 0, 0),
        (0, 23, 49, 33, 57, 12, 10, 9, 12, 0, 0),
        (0, 21, 52, 29, 52, 3, -8, 6, 7, 32, 4),
        (0, 17, 40, 27, 54, 30, 25, 21, 17, 0, 1),
        (0, 31, 50, 42, 60, 34, 0, 24, -15, 0, 0),
        (0, 38, 15, 50, 21, 30, 27, 24, 27, 0, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 32, 0),
    )),
    # bx — boxing
    "bx": (6, 7, 5, (
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 8, 0),
        (39, 30, 30, 74, 74, 74, 74, -14, -14, 12, 0),
        (26, 30, 30, 31, 3, 91, 74, -14, 32, 12, 0),
        (9, 35, 35, 3, 3, 85, 85, 43, 43, 12, 10),
        (9, 35, 35, 44, 44, 85, 85, 18, 18, 8, 4),
        (0, 53, 44, 44, 44, -47, -53, 18, 18, 12, 4),
        (13, -34, 62, 45, 47, 71, -53, 22, 22, 64, 1),
        (-13, 62, -34, 47, 45, -53, 71, 22, 22, 64, 1),
        (17, 65, 65, 30, 30, 65, 65, 26, 26, 16, 4),
        (17, 23, 23, -12, -12, 3, 3, 30, 30, 16, 0),
        (0, 23, 23, 50, 50, 59, 59, -32, -32, 16, 0),
        (0, 30, 30, 30, 30, 30, 30, 30, 30, 12, 0),
    )),
}


def wave():
    """Wave a front paw (OpenCat hi)."""
    print("\nWaving...")
    _play("hi")
    print("✓ Wave")


def high_five():
    """Offer a high five (OpenCat fiv)."""
    print("\nHigh five...")
    _play("fiv")
    print("✓ High five")


def handshake():
    """Shake hands with a front paw (OpenCat hsk)."""
    print("\nShaking hands...")
    _play("hsk")
    print("✓ Handshake")


def pee():
    """Lift a rear leg (OpenCat pee)."""
    print("\nLifting leg...")
    _play("pee")
    print("✓ Pee")


def play_dead():
    """Roll onto the side and play dead, then recover (OpenCat pd)."""
    print("\nPlaying dead...")
    _play("pd")
    print("✓ Play dead")


def push_ups():
    """Do push-ups (OpenCat pu)."""
    print("\nPush-ups...")
    _play("pu")
    print("✓ Push-ups")


def moonwalk():
    """Moonwalk shuffle (OpenCat mw)."""
    print("\nMoonwalking...")
    _play("mw")
    print("✓ Moonwalk")


def boxing():
    """Boxing jabs with the front paws (OpenCat bx)."""
    print("\nBoxing...")
    _play("bx")
    print("✓ Boxing")
