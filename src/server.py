"""HTTP command server for wireless Doggo control.

Routes:
  GET /stand
  GET /sit
  GET /rest
  GET /stretch
  GET /walk?steps=N
  GET /walk-back?steps=N
  GET /walk-back-left?steps=N
  GET /walk-back-right?steps=N
  GET /turn-left?steps=N
  GET /turn-right?steps=N
  GET /pivot-left?steps=N
  GET /pivot-right?steps=N
  GET /bound-left?steps=N
  GET /bound-right?steps=N
  GET /step?steps=N
  GET /crawl?steps=N
  GET /crawl-left?steps=N
  GET /crawl-right?steps=N
  GET /trot?steps=N&imu=0
  GET /trot-ik?steps=N&imu=0
  GET /wave
  GET /high-five
  GET /handshake
  GET /pee
  GET /play-dead
  GET /push-ups
  GET /moonwalk
  GET /boxing
  GET /recover
  GET /watchdog?on=0|1
  GET /battery
  GET /info

Returns 200 OK on success, 404 for unknown routes.
Runs in a background _thread using raw sockets so the main thread
stays free for WebREPL / interactive REPL access.

Motion routes hold poses.motion_lock while they run, so the fall watchdog
never drives the servos at the same time as a command.
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


def _parse_steps(qs):
    for part in (qs or "").split("&"):
        if part.startswith("steps="):
            try:
                return int(part[6:])
            except ValueError:
                pass
    return None


def _parse_imu(qs):
    for part in (qs or "").split("&"):
        if part.startswith("imu="):
            return part[4:] not in ("0", "false", "off")
    return True


def _parse_on(qs):
    for part in (qs or "").split("&"):
        if part.startswith("on="):
            return part[3:] not in ("0", "false", "off")
    return None


def _send_body(conn, body):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


def _handle(conn):
    try:
        line = conn.recv(256).decode().split("\r\n")[0]
        parts = line.split(" ")
        if len(parts) < 2:
            return
        path, _, qs = parts[1].partition("?")

        if path == "/":
            _send_body(
                conn,
                b"Doggo HTTP API\n\n"
                b"Poses:\n"
                b"  GET /stand\n"
                b"  GET /sit\n"
                b"  GET /rest\n"
                b"  GET /stretch\n\n"
                b"Gaits (optional ?steps=N):\n"
                b"  GET /walk\n"
                b"  GET /walk-back\n"
                b"  GET /walk-back-left\n"
                b"  GET /walk-back-right\n"
                b"  GET /turn-left\n"
                b"  GET /turn-right\n"
                b"  GET /pivot-left\n"
                b"  GET /pivot-right\n"
                b"  GET /bound-left\n"
                b"  GET /bound-right\n"
                b"  GET /step\n"
                b"  GET /crawl\n"
                b"  GET /crawl-left\n"
                b"  GET /crawl-right\n"
                b"  GET /trot          (default steps=2, imu=1)\n"
                b"  GET /trot-ik       (default steps=2, imu=1)\n\n"
                b"Tricks:\n"
                b"  GET /wave\n"
                b"  GET /high-five\n"
                b"  GET /handshake\n"
                b"  GET /pee\n"
                b"  GET /play-dead\n"
                b"  GET /push-ups\n"
                b"  GET /moonwalk\n"
                b"  GET /boxing\n"
                b"  GET /recover     (get up after falling over)\n\n"
                b"Diagnostics:\n"
                b"  GET /battery\n"
                b"  GET /info\n"
                b"  GET /watchdog    (?on=0|1 toggles auto-recovery)\n",
            )
            return
        elif path == "/battery":
            v, pct, low = battery_status()
            body = f"{v:.2f}V ({pct}%)"
            if low:
                body += " - please charge"
            body = (body + "\n").encode()
            _send_body(conn, body)
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

        # Everything below moves the robot — hold the lock so the fall
        # watchdog never plays recover() mid-command.
        motion_lock.acquire()
        try:
            if path == "/stand":
                stand()
            elif path == "/sit":
                sit()
            elif path == "/rest":
                rest()
            elif path == "/stretch":
                stretch()
            elif path == "/walk":
                walk(steps=_parse_steps(qs))
            elif path == "/walk-back":
                walk_back(steps=_parse_steps(qs))
            elif path == "/walk-back-left":
                walk_back_left(steps=_parse_steps(qs))
            elif path == "/walk-back-right":
                walk_back_right(steps=_parse_steps(qs))
            elif path == "/turn-left":
                turn_left(steps=_parse_steps(qs))
            elif path == "/turn-right":
                turn_right(steps=_parse_steps(qs))
            elif path == "/pivot-left":
                pivot_left(steps=_parse_steps(qs))
            elif path == "/pivot-right":
                pivot_right(steps=_parse_steps(qs))
            elif path == "/bound-left":
                bound_left(steps=_parse_steps(qs))
            elif path == "/bound-right":
                bound_right(steps=_parse_steps(qs))
            elif path == "/step":
                step_in_place(steps=_parse_steps(qs))
            elif path == "/crawl":
                crawl(steps=_parse_steps(qs))
            elif path == "/crawl-left":
                crawl_left(steps=_parse_steps(qs))
            elif path == "/crawl-right":
                crawl_right(steps=_parse_steps(qs))
            elif path == "/wave":
                wave()
            elif path == "/high-five":
                high_five()
            elif path == "/handshake":
                handshake()
            elif path == "/pee":
                pee()
            elif path == "/play-dead":
                play_dead()
            elif path == "/push-ups":
                push_ups()
            elif path == "/moonwalk":
                moonwalk()
            elif path == "/boxing":
                boxing()
            elif path == "/recover":
                recover()
            elif path == "/trot":
                trot_forward(steps=_parse_steps(qs) or 2, use_imu=_parse_imu(qs))
            elif path == "/trot-ik":
                trot_ik_forward(steps=_parse_steps(qs) or 2, use_imu=_parse_imu(qs))
            else:
                conn.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 10\r\n\r\nNot found\n")
                return
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
