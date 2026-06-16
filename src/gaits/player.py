"""Shared keyframe-gait player.

Every keyframe gait (walk, turn, crawl, …) is the same machine fed different data:
take an OpenCat raw frame — eight angles in `poses.GAIT_CHANNELS` column order — map it
to commanded servo angles with ``commanded = 90 + rotationDirection * raw``, then play
the frames at a fixed delay, entering from the current pose and returning to stand.

This module holds that machinery so each gait file is just its frame table plus a few
tuning constants. The per-gait differences reduce to three knobs:

  * ``transform`` — optional ``f(index, raw) -> raw'`` applied before the 90+rd*raw
    mapping (e.g. walk's shoulder squeeze, pivot's leg cap/offset). ``None`` = faithful.
  * ``mirror_lr`` — swap left/right column pairs (the right-hand variant of a gait).
  * ``every`` — frame stride; ``2`` plays every second frame (keeps motion above the
    servo deadband on the longer sequences), ``1`` plays them all.

Conversion: ``commanded = 90 + rotationDirection[joint] * opencat_angle`` (commanded 90 =
OpenCat raw 0 = the calibration pose, at the corrected 270-degree servo scale where one
commanded degree is one physical degree).
"""

import time

from poses import GAIT_CHANNELS, ROTATION_DIRECTION, move_to, play_frame, stand

# Gait column channels and their rotation directions, in OpenCat column order.
CH = GAIT_CHANNELS
RD = tuple(ROTATION_DIRECTION[ch] for ch in CH)


def mirror(frame):
    """Swap the left/right column pairs of a frame (FL<->FR, RR<->RL, both leg pairs)."""
    f = frame
    return (f[1], f[0], f[3], f[2], f[5], f[4], f[7], f[6])


def to_commanded(raw, transform=None):
    """Convert a raw OpenCat frame to a {channel: commanded_angle} dict.

    transform: optional ``f(index, raw_value) -> adjusted_value`` applied per column
    before the 90 + rotDir * raw mapping. None = faithful OpenCat playback.
    """
    result = {}
    for i in range(8):
        r = raw[i] if transform is None else transform(i, raw[i])
        result[CH[i]] = 90 + RD[i] * r  # keep float — int() happens at the PWM level
    return result


def play(frames, frame_delay, steps, *, transform=None, mirror_lr=False, every=1, name="gait"):
    """Play a keyframe gait: ease into the first frame, loop, then return to stand.

    Args:
        frames:      sequence of raw OpenCat frames (8 columns each).
        frame_delay: seconds to sleep after each played frame.
        steps:       number of full cycles; None = run until KeyboardInterrupt.
        transform:   per-column adjustment, see to_commanded().
        mirror_lr:   play the left/right-mirrored frames (right-hand variant).
        every:       frame stride (1 = every frame, 2 = every second frame).
        name:        lower-case gait name used in status messages.
    """
    print("\nStarting " + name + "...")

    first = mirror(frames[0]) if mirror_lr else frames[0]
    move_to(to_commanded(first, transform), speed=2)

    count = 0
    try:
        while steps is None or count < steps:
            for i in range(0, len(frames), every):
                frame = mirror(frames[i]) if mirror_lr else frames[i]
                play_frame(to_commanded(frame, transform))
                time.sleep(frame_delay)
            count += 1
    except KeyboardInterrupt:
        print("\n\n" + name.capitalize() + " interrupted.")

    print("Returning to stand...")
    stand()
