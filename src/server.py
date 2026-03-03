"""HTTP command server for wireless Bittle control.

Routes:
  GET /stand
  GET /sit
  GET /rest
  GET /walk?steps=N
  GET /trot?steps=N
  GET /battery

Returns 200 OK on success, 404 for unknown routes.
Runs in a background _thread using raw sockets so the main thread
stays free for WebREPL / interactive REPL access.
"""
import socket
import _thread
from poses import stand, sit, rest
from battery import battery_voltage
from gaits.walk import walk
from gaits.trot import trot


def _parse_steps(qs):
    for part in (qs or "").split("&"):
        if part.startswith("steps="):
            try:
                return int(part[6:])
            except ValueError:
                pass
    return None


def _handle(conn):
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
        elif path == "/trot":
            trot(steps=_parse_steps(qs))
        elif path == "/battery":
            v = battery_voltage()
            body = f"{v:.2f}V".encode()
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
            return
        else:
            conn.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot found")
            return

        conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
    except Exception as e:
        print("Request error:", e)
    finally:
        conn.close()


def _serve(port):
    s = socket.socket()
    s.bind(("", port))
    s.listen(1)
    print("HTTP server on port", port)
    while True:
        try:
            conn, _ = s.accept()
            _handle(conn)
        except Exception as e:
            print("Server error:", e)


def run(port=80):
    _thread.start_new_thread(_serve, (port,))
