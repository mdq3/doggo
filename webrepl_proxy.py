#!/usr/bin/env python3
"""Bridge between mpremote and MicroPython WebREPL via a PTY.

Creates a pseudo-terminal (PTY) that mpremote connects to as if it were a
real serial port, and bridges it to the device WebREPL WebSocket. This avoids
any library patching — mpremote sees a proper tty device with a real fd.

Usage:
    python webrepl_proxy.py <host> <password> [ws_port=8266]

The proxy prints the PTY path on startup. Use that path with mpremote:
    mpremote connect /dev/ttys003 repl
    mpremote connect /dev/ttys003 run src/demos/walk.py
    mpremote connect /dev/ttys003 fs cp src/poses.py :poses.py

The proxy stays running; Ctrl+C to quit.
Each mpremote session gets a fresh PTY (path may change between sessions).
"""
import os
import socket
import struct
import threading
import sys
import time

_FRAME_TXT = 0x81
_FRAME_BIN = 0x82


class _WS:
    """Minimal buffered WebSocket client."""

    def __init__(self, sock):
        self._sock = sock
        self._buf = b""

    def _recv(self, n):
        while len(self._buf) < n:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("connection closed")
            self._buf += chunk
        data, self._buf = self._buf[:n], self._buf[n:]
        return data

    def handshake(self):
        self._sock.sendall(
            b"GET / HTTP/1.1\r\n"
            b"Host: echo.websocket.org\r\n"
            b"Connection: Upgrade\r\n"
            b"Upgrade: websocket\r\n"
            b"Sec-WebSocket-Key: foo\r\n"
            b"\r\n"
        )
        while b"\r\n\r\n" not in self._buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            self._buf += chunk
        idx = self._buf.index(b"\r\n\r\n")
        self._buf = self._buf[idx + 4:]

    def recv_frame(self):
        while True:
            fl, sz = struct.unpack(">BB", self._recv(2))
            if sz == 126:
                (sz,) = struct.unpack(">H", self._recv(2))
            data = self._recv(sz)
            if fl in (_FRAME_TXT, _FRAME_BIN):
                return data

    def send_frame(self, data):
        l = len(data)
        if l < 126:
            self._sock.sendall(struct.pack(">BB", _FRAME_TXT, l) + data)
        else:
            self._sock.sendall(struct.pack(">BBH", _FRAME_TXT, 126, l) + data)

    def login(self, password):
        buf = b""
        while b":" not in buf:
            buf += self.recv_frame()
        self.send_frame(password.encode() + b"\r\n")
        self._sock.settimeout(0.5)
        try:
            while True:
                self.recv_frame()
        except (socket.timeout, OSError):
            pass
        self._sock.settimeout(None)

    def settimeout(self, t):
        self._sock.settimeout(t)

    def close(self):
        self._sock.close()


def _bridge(ws, master_fd):
    """Forward bytes between PTY master fd and WebREPL WebSocket."""
    done = threading.Event()

    def ws_to_pty():
        while not done.is_set():
            try:
                data = ws.recv_frame()
                if data:
                    os.write(master_fd, data)
            except Exception:
                done.set()

    def pty_to_ws():
        while not done.is_set():
            try:
                data = os.read(master_fd, 256)
                if data:
                    ws.send_frame(data)
            except OSError:
                # EIO when mpremote closes the slave end
                done.set()

    t1 = threading.Thread(target=ws_to_pty, daemon=True)
    t2 = threading.Thread(target=pty_to_ws, daemon=True)
    t1.start()
    t2.start()
    done.wait()
    os.close(master_fd)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    password = sys.argv[2]
    ws_port = int(sys.argv[3]) if len(sys.argv) > 3 else 8266

    print(f"Connecting to WebREPL at {host}:{ws_port}...")
    ws = _WS(socket.socket())
    ws.settimeout(10)
    ws._sock.connect((host, ws_port))
    ws.handshake()
    print("Logging in...")
    ws.login(password)
    ws.settimeout(None)
    print(f"WebREPL connected: {host}:{ws_port}")

    try:
        while True:
            master_fd, slave_fd = os.openpty()
            slave_path = os.ttyname(slave_fd)
            os.close(slave_fd)
            print(f"\nPTY ready: {slave_path}")
            print(f"  mpremote connect {slave_path} repl")
            print(f"  mpremote connect {slave_path} run <script.py>")
            print(f"  mpremote connect {slave_path} fs cp <file> :<file>")
            _bridge(ws, master_fd)
            print("mpremote disconnected")
    except KeyboardInterrupt:
        print("\nProxy stopped")
    finally:
        ws.close()


if __name__ == "__main__":
    main()
