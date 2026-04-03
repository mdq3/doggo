#!/usr/bin/env python3
"""Deploy project source files to the Bittle over WebREPL.

Usage:
    python deploy.py <host> <password> [--port PORT]

Examples:
    python deploy.py doggo.local doggo
    python deploy.py 192.168.1.42 doggo

All source files are uploaded in a single WebREPL session (fast — one
connection, one login). Optional files (config.py, wifi_config.py) are
skipped if not present locally — the device keeps its existing copy.

After upload, press the reset button on the robot to load the new files.
"""
import argparse
import os
import socket
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from webrepl_proxy import _WS, _put_file  # noqa: E402

# ANSI colour helpers
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"

def _c(colour, text): return f"{colour}{text}{_RESET}"

# (local_path, remote_path) pairs — always deployed
MANIFEST = [
    ("src/drivers/servo.py",   "drivers/servo.py"),
    ("src/poses.py",           "poses.py"),
    ("src/battery.py",         "battery.py"),
    ("src/device_info.py",     "device_info.py"),
    ("src/server.py",          "server.py"),
    ("src/boot.py",            "boot.py"),
    ("src/main.py",            "main.py"),
    ("src/imu.py",             "imu.py"),
    ("src/gaits/walk.py",      "gaits/walk.py"),
    ("src/gaits/walk_back.py", "gaits/walk_back.py"),
    ("src/gaits/turn.py",      "gaits/turn.py"),
    ("src/gaits/pivot.py",     "gaits/pivot.py"),
    ("src/gaits/bound_turn.py","gaits/bound_turn.py"),
    ("src/gaits/trot.py",              "gaits/trot.py"),
    ("src/gaits/trot_ik.py",          "gaits/trot_ik.py"),
    ("src/kinematics/__init__.py",    "kinematics/__init__.py"),
    ("src/kinematics/leg.py",         "kinematics/leg.py"),
    ("src/kinematics/doggo.py",       "kinematics/doggo.py"),
]

# Deployed only if present locally (machine-specific, gitignored)
OPTIONAL = [
    ("config.py",      "config.py"),
    ("wifi_config.py", "wifi_config.py"),
]


def _connect(host, password, port):
    print(_c(_CYAN, f"Connecting to {host}:{port}..."))
    ws = _WS(socket.socket())
    ws.settimeout(10)
    ws._sock.connect((host, port))
    ws.handshake()
    ws.login(password)
    ws.settimeout(None)
    print(_c(_GREEN, "Connected."))
    return ws


def _repl_exec(ws, code):
    """Send a single-line expression to the REPL and drain through the next prompt."""
    ws.send_frame((code + "\r\n").encode())
    ws.settimeout(3)
    buf = b""
    try:
        while b">>> " not in buf:
            buf += ws.recv_frame()
    except (socket.timeout, OSError):
        pass
    ws.settimeout(None)


def main():
    parser = argparse.ArgumentParser(description="Deploy source files to the Bittle over WebREPL.")
    parser.add_argument("host",     help="Device hostname or IP (e.g. doggo.local or 192.168.1.x)")
    parser.add_argument("password", help="WebREPL password")
    parser.add_argument("--port",   type=int, default=8266, metavar="PORT",
                        help="WebREPL port (default: 8266)")
    args = parser.parse_args()

    files = list(MANIFEST)
    for local, remote in OPTIONAL:
        if os.path.exists(local):
            files.append((local, remote))
        else:
            print(_c(_YELLOW, f"  skipping {local} (not found locally — device keeps existing copy)"))

    ws = _connect(args.host, args.password, args.port)
    try:
        _repl_exec(ws, "import os; [os.mkdir(d) for d in ('drivers', 'gaits', 'kinematics') if d not in os.listdir()]")
        for local, remote in files:
            _put_file(ws, local, remote)
    finally:
        ws.close()

    print(_c(_BOLD + _GREEN, f"\n✓ Deployed {len(files)} file(s) to {args.host}."))
    print(_c(_CYAN, "  Press the reset button on the robot to load the new files."))


if __name__ == "__main__":
    main()
