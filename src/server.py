"""HTTP command server for wireless Bittle control.

Routes:
  GET /stand
  GET /sit
  GET /rest
  GET /walk?steps=N
  GET /walk_back?steps=N
  GET /battery
  GET /restart

Returns 200 OK on success, 404 for unknown routes.
Runs in a background _thread using raw sockets so the main thread
stays free for WebREPL / interactive REPL access.

/restart reloads all modules from flash without a hardware reset.
machine.reset() is intentionally avoided: the ESP32 reset clears the
GPIO output-enable register so pins go to INPUT, pull-ups drive them
HIGH, and servos interpret that as a max-position command — violent
movement. A software reload keeps servo PWM running throughout.
"""
import socket
import sys
import _thread
from poses import stand, sit, rest
from battery import battery_status
from gaits.walk import walk, walk_back

_reload_flag = False


def _parse_steps(qs):
    for part in (qs or "").split("&"):
        if part.startswith("steps="):
            try:
                return int(part[6:])
            except ValueError:
                pass
    return None


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
        elif path == "/battery":
            v, pct, low = battery_status()
            body = f"{v:.2f}V ({pct}%)"
            if low:
                body += " - please charge"
            body = (body + "\n").encode()
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
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

    Servo PWM keeps running throughout — no GPIO disruption, no spaz.
    The live servos object and current_pos are transplanted into the
    freshly-imported poses module so motion state is preserved.
    """
    import poses as _old
    saved_servos = _old.servos
    saved_pos = dict(_old.current_pos)

    for mod in ("server", "poses", "battery", "gaits.walk", "gaits"):
        sys.modules.pop(mod, None)

    # Reimport poses; immediately replace the new empty Servos object
    # (no channels initialised, safe to discard) with the live one.
    import poses as _new
    _new.servos = saved_servos
    _new.current_pos = saved_pos

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
