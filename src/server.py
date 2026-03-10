"""HTTP command server for wireless Bittle control.

Routes:
  GET /stand
  GET /sit
  GET /rest
  GET /walk?steps=N
  GET /walk_back?steps=N
  GET /turn_left?steps=N
  GET /turn_right?steps=N
  GET /pivot_left?steps=N
  GET /pivot_right?steps=N
  GET /bound_left?steps=N
  GET /bound_right?steps=N
  GET /battery
  GET /info
  GET /restart

Returns 200 OK on success, 404 for unknown routes.
Runs in a background _thread using raw sockets so the main thread
stays free for WebREPL / interactive REPL access.

/restart reloads server.py, battery.py, gaits/walk.py,
gaits/walk_back.py, gaits/turn.py, gaits/pivot.py, and gaits/bound_turn.py from flash
without a hardware reset. poses.py is intentionally kept loaded —
reimporting it disrupts LEDC state. Changes to poses.py or servo.py
require a power cycle.
"""
import _thread
import socket
import sys

from battery import battery_status
from device_info import device_info
from gaits.bound_turn import bound_left, bound_right
from gaits.pivot import pivot_left, pivot_right
from gaits.turn import turn_left, turn_right
from gaits.walk import walk
from gaits.walk_back import walk_back
from poses import rest, sit, stand

_reload_flag = False


def _parse_steps(qs):
    for part in (qs or "").split("&"):
        if part.startswith("steps="):
            try:
                return int(part[6:])
            except ValueError:
                pass
    return None


def _send_body(conn, body):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


def _handle(conn):
    global _reload_flag
    try:
        line = conn.recv(256).decode().split("\r\n")[0]
        parts = line.split(" ")
        if len(parts) < 2:
            return
        path, _, qs = parts[1].partition("?")

        if path == "/stand":
            stand()
        elif path == "/sit":
            sit()
        elif path == "/rest":
            rest()
        elif path == "/walk":
            walk(steps=_parse_steps(qs))
        elif path == "/walk_back":
            walk_back(steps=_parse_steps(qs))
        elif path == "/turn_left":
            turn_left(steps=_parse_steps(qs))
        elif path == "/turn_right":
            turn_right(steps=_parse_steps(qs))
        elif path == "/pivot_left":
            pivot_left(steps=_parse_steps(qs))
        elif path == "/pivot_right":
            pivot_right(steps=_parse_steps(qs))
        elif path == "/bound_left":
            bound_left(steps=_parse_steps(qs))
        elif path == "/bound_right":
            bound_right(steps=_parse_steps(qs))
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
        elif path == "/restart":
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nRestarting\n")
            conn.close()
            _reload_flag = True  # signals _serve to exit and reload modules
            return
        else:
            conn.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 10\r\n\r\nNot found\n")
            return

        conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nOK\n")
    except Exception as e:
        print("Request error:", e)
    finally:
        conn.close()


def _reload(port):
    """Reload changed modules from flash without touching hardware.

    poses is intentionally NOT reloaded — it holds the live Servos object
    and current_pos. Reimporting it (even with a no-op Servos.__init__)
    disrupts LEDC state and causes servo spaz. poses.py changes require
    a power cycle.

    Reloads: server.py, battery.py, gaits/walk.py, gaits/walk_back.py
    Gait modules import from the already-loaded poses, so they get the live
    servos automatically.
    """
    for mod in ("server", "battery", "device_info",
                "gaits.walk", "gaits.walk_back", "gaits.turn", "gaits.pivot", "gaits.bound_turn", "gaits"):
        sys.modules.pop(mod, None)

    try:
        import server as _new_srv
        _thread.start_new_thread(_new_srv._serve, (port,))
        print("Server reloaded")
    except Exception as e:
        print("Reload failed:", e)


def _serve(port):
    global _reload_flag
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError:
        pass
    s.bind(("", port))
    s.listen(1)
    s.settimeout(1.0)  # allows _reload_flag to be checked each second
    print("HTTP server on port", port)
    while not _reload_flag:
        try:
            conn, _ = s.accept()
            _handle(conn)
        except OSError:
            pass  # timeout — loop and check flag
    _reload_flag = False
    s.close()
    _reload(port)


def run(port=80):
    _thread.start_new_thread(_serve, (port,))
