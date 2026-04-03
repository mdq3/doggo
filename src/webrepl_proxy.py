#!/usr/bin/env python3
"""Bridge between mpremote and MicroPython WebREPL via a PTY.

Creates a pseudo-terminal (PTY) that mpremote connects to as if it were a
real serial port, and bridges it to the device WebREPL WebSocket. This avoids
any library patching — mpremote sees a proper tty device with a real fd.

mpremote is invoked with "resume" to disable its auto soft-reset. Without this,
mpremote sends Ctrl+D which causes MicroPython to soft-reboot and tear down the
WebSocket. The "resume" command sets _auto_soft_reset=False so raw REPL is
entered with Ctrl+A only — no Ctrl+D, no reboot.

File copies (fs cp) are handled directly via the WebREPL binary protocol,
bypassing mpremote entirely for faster transfers.

Usage:
    # File copy host → device (WebREPL binary protocol, no mpremote):
    python webrepl_proxy.py <host> <password> fs cp local.py :remote.py

    # Any mpremote command — all subcommands work (fs ls, fs tree, exec, etc.):
    python webrepl_proxy.py <host> <password> repl
    python webrepl_proxy.py <host> <password> run src/demos/walk.py
    python webrepl_proxy.py <host> <password> fs ls
    python webrepl_proxy.py <host> <password> fs tree

    # Daemon mode — proxy stays running, prints PTY path for manual mpremote:
    python webrepl_proxy.py <host> <password>

    # Custom WebREPL port (default 8266) — pass as a numeric third argument:
    python webrepl_proxy.py <host> <password> 8266 repl
"""

import os
import socket
import struct
import subprocess
import sys
import threading

_RESET = "\033[0m"
_GREEN = "\033[32m"

_FRAME_TXT = 0x81
_FRAME_BIN = 0x82

# WebREPL binary file-transfer protocol
_WR_REQ_S = "<2sBBQLH64s"
_WR_PUT = 1
_WR_GET = 2


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
        self._buf = self._buf[idx + 4 :]

    def recv_frame(self):
        while True:
            fl, sz = struct.unpack(">BB", self._recv(2))
            if sz == 126:
                (sz,) = struct.unpack(">H", self._recv(2))
            data = self._recv(sz)
            if fl in (_FRAME_TXT, _FRAME_BIN):
                return data

    def send_frame(self, data, binary=False):
        ft = _FRAME_BIN if binary else _FRAME_TXT
        n = len(data)
        if n < 126:
            self._sock.sendall(struct.pack(">BB", ft, n) + data)
        else:
            self._sock.sendall(struct.pack(">BBH", ft, 126, n) + data)

    def login(self, password):
        buf = b""
        while b":" not in buf:
            buf += self.recv_frame()
        self.send_frame(password.encode() + b"\r\n")
        # Wait for the REPL prompt rather than a fixed drain — boot messages
        # (e.g. "HTTP server on port 80") may arrive well after 0.5 s and
        # would otherwise leak into the bridge and confuse mpremote.
        self._sock.settimeout(5)
        buf = b""
        try:
            while b">>> " not in buf:
                buf += self.recv_frame()
        except (socket.timeout, OSError):
            pass
        self._sock.settimeout(None)

    def settimeout(self, t):
        self._sock.settimeout(t)

    def close(self):
        self._sock.close()


# ---------------------------------------------------------------------------
# WebREPL binary file-transfer protocol
# ---------------------------------------------------------------------------


def _wr_read_resp(ws):
    """Read a 4-byte WebREPL binary response; raise on non-zero status."""
    frame = ws.recv_frame()
    sig, code = struct.unpack("<2sH", frame[:4])
    if sig != b"WB" or code != 0:
        raise ConnectionError(f"WebREPL error response: sig={sig!r} code={code}")


def _put_file(ws, local_path, remote_path):
    """Upload local_path to remote_path using WebREPL binary PUT protocol."""
    with open(local_path, "rb") as f:
        data = f.read()
    sz = len(data)
    fname = remote_path.encode()
    req = struct.pack(_WR_REQ_S, b"WA", _WR_PUT, 0, 0, sz, len(fname), fname)
    # The reference client splits the header into two sends to work around
    # firmware buffering issues; do the same.
    ws.send_frame(req[:10], binary=True)
    ws.send_frame(req[10:], binary=True)
    _wr_read_resp(ws)
    for i in range(0, sz, 1024):
        ws.send_frame(data[i : i + 1024], binary=True)
    _wr_read_resp(ws)
    print(f"{_GREEN}✓{_RESET} {local_path} → :{remote_path} ({sz} bytes)")
    return 0


def _get_file(ws, remote_path, local_path):
    """Download remote_path to local_path using WebREPL binary GET protocol."""
    fname = remote_path.encode()
    req = struct.pack(_WR_REQ_S, b"WA", _WR_GET, 0, 0, 0, len(fname), fname)
    ws.send_frame(req[:10], binary=True)
    ws.send_frame(req[10:], binary=True)
    _wr_read_resp(ws)
    with open(local_path, "wb") as f:
        while True:
            ws.send_frame(b"\x00", binary=True)  # trigger next chunk
            chunk = ws.recv_frame()
            (chunk_sz,) = struct.unpack("<H", chunk[:2])
            if chunk_sz == 0:
                break
            f.write(chunk[2 : 2 + chunk_sz])
    _wr_read_resp(ws)
    print(f"Copied :{remote_path} → {local_path}")
    return 0


def _handle_fs_cp(ws, args):
    """Dispatch a 'fs cp' command via WebREPL binary protocol.

    Returns an exit code (0 on success) or None if the pattern doesn't match
    (fall through to mpremote).
    """
    if len(args) < 4 or args[0] != "fs" or args[1] != "cp":
        return None
    src, dst = args[2], args[3]
    if not src.startswith(":") and dst.startswith(":"):
        return _put_file(ws, src, dst[1:])
    if src.startswith(":") and not dst.startswith(":"):
        return _get_file(ws, src[1:], dst)
    return None  # both or neither have ':', fall through to mpremote


# ---------------------------------------------------------------------------
# PTY bridge (for repl / run / other mpremote commands)
# ---------------------------------------------------------------------------


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


def _run_command(ws, cmd_args):
    """Open a PTY, run mpremote connect <pty> <cmd_args>, wait for exit."""
    master_fd, slave_fd = os.openpty()
    slave_path = os.ttyname(slave_fd)
    # Keep slave_fd open until mpremote exits: closing it prematurely causes
    # os.read(master_fd) to return EIO before mpremote opens the slave end,
    # which kills the bridge and prevents mpremote from entering raw REPL.
    bridge = threading.Thread(target=_bridge, args=(ws, master_fd), daemon=True)
    bridge.start()
    # "resume" disables mpremote's auto soft-reset, preventing the Ctrl+D that
    # would tear down the WebSocket connection (soft reboot goes to UART, not WS).
    returncode = subprocess.call(["mpremote", "connect", slave_path, "resume"] + cmd_args)
    os.close(slave_fd)  # now safe to close; signals bridge to stop via EIO
    bridge.join(timeout=2)
    return returncode


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    password = sys.argv[2]

    # Optional numeric third arg is the WebREPL port; everything after is cmd.
    if len(sys.argv) > 3 and sys.argv[3].isdigit():
        ws_port = int(sys.argv[3])
        cmd_args = sys.argv[4:]
    else:
        ws_port = 8266
        cmd_args = sys.argv[3:]

    print(f"Connecting to WebREPL at {host}:{ws_port}...")
    ws = _WS(socket.socket())
    ws.settimeout(10)
    ws._sock.connect((host, ws_port))
    ws.handshake()
    ws.login(password)
    ws.settimeout(None)
    print(f"WebREPL connected: {host}:{ws_port}")

    try:
        if cmd_args:
            rc = _handle_fs_cp(ws, cmd_args)
            if rc is not None:
                sys.exit(rc)
            sys.exit(_run_command(ws, cmd_args))
        else:
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
