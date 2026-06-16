"""HTTP command server for wireless Doggo control.

All routes are defined once, in the tables below: the pose/gait/trick motion routes
(_POSE_ROUTES / _GAIT_ROUTES / _TRICK_ROUTES) and the diagnostics (_DIAG_ROUTES).
`GET /` serves an index generated from those tables, so the route list is never
duplicated. Returns 200 OK on success, 404 for unknown routes.

Runs in a background _thread using raw sockets so the main thread stays free for
WebREPL / interactive REPL access.

Motion routes hold poses.motion_lock while they run, so the fall watchdog never drives
the servos at the same time as a command.
"""

import _thread
import socket

from battery import battery_status
from behaviors import (
    boxing,
    handshake,
    high_five,
    moonwalk,
    pee,
    play_dead,
    push_ups,
    recover,
    wave,
)
from device_info import device_info
from gaits.back_turn import walk_back_left, walk_back_right
from gaits.bound_turn import bound_left, bound_right
from gaits.crawl import crawl
from gaits.crawl_turn import crawl_left, crawl_right
from gaits.pivot import pivot_left, pivot_right
from gaits.step import step_in_place
from gaits.trot import trot_forward
from gaits.trot_ik import trot_forward as trot_ik_forward
from gaits.turn import turn_left, turn_right
from gaits.walk import walk
from gaits.walk_back import walk_back
from poses import motion_lock, rest, sit, stand, stretch

# --- query-string parsing ---


def _qget(qs, key):
    """Return the raw string value of `key` in the query string, or None."""
    prefix = key + "="
    for part in (qs or "").split("&"):
        if part.startswith(prefix):
            return part[len(prefix):]
    return None


def _parse_steps(qs):
    v = _qget(qs, "steps")
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _parse_bool(qs, key, default):
    v = _qget(qs, key)
    return default if v is None else v not in ("0", "false", "off")


def _parse_imu(qs):
    return _parse_bool(qs, "imu", True)


def _parse_on(qs):
    return _parse_bool(qs, "on", None)


# --- motion route tables ---
# Each entry: (path, function, kind, help). `kind` selects how the function is invoked:
_KIND_NONE = 0  # fn()                                                   — poses, tricks
_KIND_STEPS = 1  # fn(steps=_parse_steps(qs))                            — gaits
_KIND_TROT = 2  # fn(steps=_parse_steps(qs) or 2, use_imu=_parse_imu(qs)) — trot

_POSE_ROUTES = (
    ("/stand", stand, _KIND_NONE, "Stand up"),
    ("/sit", sit, _KIND_NONE, "Sit down"),
    ("/rest", rest, _KIND_NONE, "Lie flat"),
    ("/stretch", stretch, _KIND_NONE, "Downward-dog stretch"),
)

_GAIT_ROUTES = (
    ("/walk", walk, _KIND_STEPS, "Walk forward"),
    ("/walk-back", walk_back, _KIND_STEPS, "Walk backward"),
    ("/walk-back-left", walk_back_left, _KIND_STEPS, "Walk backward arcing left"),
    ("/walk-back-right", walk_back_right, _KIND_STEPS, "Walk backward arcing right"),
    ("/turn-left", turn_left, _KIND_STEPS, "Arc turn left"),
    ("/turn-right", turn_right, _KIND_STEPS, "Arc turn right"),
    ("/pivot-left", pivot_left, _KIND_STEPS, "Rotate in place left"),
    ("/pivot-right", pivot_right, _KIND_STEPS, "Rotate in place right"),
    ("/bound-left", bound_left, _KIND_STEPS, "Tight arc turn left"),
    ("/bound-right", bound_right, _KIND_STEPS, "Tight arc turn right"),
    ("/step", step_in_place, _KIND_STEPS, "March in place"),
    ("/crawl", crawl, _KIND_STEPS, "Low-stance crawl forward"),
    ("/crawl-left", crawl_left, _KIND_STEPS, "Low-stance crawl arcing left"),
    ("/crawl-right", crawl_right, _KIND_STEPS, "Low-stance crawl arcing right"),
    ("/trot", trot_forward, _KIND_TROT, "Diagonal trot (?imu=0/1, default steps=2)"),
    ("/trot-ik", trot_ik_forward, _KIND_TROT, "IK-based trot (?imu=0/1, default steps=2)"),
)

_TRICK_ROUTES = (
    ("/wave", wave, _KIND_NONE, "Wave a front paw"),
    ("/high-five", high_five, _KIND_NONE, "Offer a high five"),
    ("/handshake", handshake, _KIND_NONE, "Shake hands"),
    ("/pee", pee, _KIND_NONE, "Lift a rear leg"),
    ("/play-dead", play_dead, _KIND_NONE, "Roll over and play dead"),
    ("/push-ups", push_ups, _KIND_NONE, "Do push-ups"),
    ("/moonwalk", moonwalk, _KIND_NONE, "Moonwalk shuffle"),
    ("/boxing", boxing, _KIND_NONE, "Boxing jabs"),
    ("/recover", recover, _KIND_NONE, "Get up after falling over"),
)

# Ordered groups for the generated GET / index (MicroPython dicts are unordered,
# so the listing is driven by these tuples, not by _MOTION).
_MOTION_GROUPS = (
    ("Poses", _POSE_ROUTES),
    ("Gaits (optional ?steps=N)", _GAIT_ROUTES),
    ("Tricks", _TRICK_ROUTES),
)

# Diagnostics are handled individually (custom bodies, no motion lock); listed here
# only so GET / can advertise them.
_DIAG_ROUTES = (
    ("/battery", "Battery voltage and charge level"),
    ("/info", "Device diagnostics (RAM, flash, CPU, WiFi, uptime)"),
    ("/watchdog", "Show or toggle auto-recovery (?on=0/1)"),
)

# Flat path -> (function, kind) lookup for dispatch.
_MOTION = {}
for _, _routes in _MOTION_GROUPS:
    for _path, _fn, _kind, _ in _routes:
        _MOTION[_path] = (_fn, _kind)


def _index_body():
    """Render the GET / help text from the route tables (single source of truth)."""
    lines = ["Doggo HTTP API", ""]
    for title, routes in _MOTION_GROUPS:
        lines.append(title + ":")
        for path, _fn, _kind, help_text in routes:
            lines.append("  GET %-18s %s" % (path, help_text))
        lines.append("")
    lines.append("Diagnostics:")
    for path, help_text in _DIAG_ROUTES:
        lines.append("  GET %-18s %s" % (path, help_text))
    lines.append("")
    return "\n".join(lines).encode()


def _send_body(conn, body):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


def _handle(conn):
    try:
        line = conn.recv(256).decode().split("\r\n")[0]
        parts = line.split(" ")
        if len(parts) < 2:
            return
        path, _, qs = parts[1].partition("?")

        # Diagnostics — no motion lock, custom response bodies.
        if path == "/":
            _send_body(conn, _index_body())
            return
        elif path == "/battery":
            v, pct, low = battery_status()
            body = f"{v:.2f}V ({pct}%)"
            if low:
                body += " - please charge"
            _send_body(conn, (body + "\n").encode())
            return
        elif path == "/info":
            _send_body(conn, device_info().encode())
            return
        elif path == "/watchdog":
            import fall_watchdog

            on = _parse_on(qs)
            if on is not None:
                fall_watchdog.enabled = on
            state = "on" if fall_watchdog.enabled else "off"
            if not fall_watchdog.running():
                state += " (thread not running)"
            _send_body(conn, ("fall watchdog " + state + "\n").encode())
            return

        # Everything else moves the robot — hold the lock so the fall watchdog
        # never plays recover() mid-command.
        entry = _MOTION.get(path)
        if entry is None:
            conn.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 10\r\n\r\nNot found\n")
            return
        fn, kind = entry
        motion_lock.acquire()
        try:
            if kind == _KIND_NONE:
                fn()
            elif kind == _KIND_STEPS:
                fn(steps=_parse_steps(qs))
            else:  # _KIND_TROT
                fn(steps=_parse_steps(qs) or 2, use_imu=_parse_imu(qs))
        finally:
            motion_lock.release()

        conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nOK\n")
    except Exception as e:
        print("Request error:", e)
    finally:
        conn.close()


def _serve(port):
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError:
        pass
    s.bind(("", port))
    s.listen(1)
    print("HTTP server on port", port)
    while True:
        try:
            conn, _ = s.accept()
            _handle(conn)
        except OSError:
            pass


def run(port=80):
    _thread.start_new_thread(_serve, (port,))
