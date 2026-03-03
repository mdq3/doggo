"""HTTP command server for wireless Bittle control.

Routes:
  GET /stand
  GET /sit
  GET /rest
  GET /walk?steps=N
  GET /battery
  GET /restart

Returns 200 OK on success, 404 for unknown routes.
Runs in a background _thread using raw sockets so the main thread
stays free for WebREPL / interactive REPL access.
"""
import machine
import socket
import time
import _thread
from poses import stand, sit, rest
from battery import battery_status
from gaits.walk import walk


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
            time.sleep_ms(100)
            machine.reset()  # never returns; finally block is not reached
        else:
            conn.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 10\r\n\r\nNot found\n")
            return

        conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nOK\n")
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
