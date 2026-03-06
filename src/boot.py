"""boot.py — runs on every device boot before main.py.

Scans visible APs and connects to the first network in NETWORKS that
is currently in range. Falls through gracefully if wifi_config.py is
missing or no configured network is found.
"""
import time

import network
import webrepl

NETWORKS = []
WEBREPL_PASSWORD = None
HOSTNAME = "doggo"

try:
    from wifi_config import HOSTNAME, NETWORKS, WEBREPL_PASSWORD
except ImportError:
    pass


def connect_wifi(timeout=20):
    wlan = network.WLAN(network.STA_IF)
    network.hostname(HOSTNAME)  # must be set before active() for mDNS
    wlan.active(True)

    visible = {e[0] if isinstance(e[0], str) else e[0].decode()
               for e in wlan.scan()}

    for ssid, password in NETWORKS:
        if ssid not in visible:
            continue
        print("Connecting to", ssid, "...")
        if not wlan.isconnected():
            wlan.connect(ssid, password)
        deadline = time.time() + timeout
        while not wlan.isconnected() and time.time() < deadline:
            time.sleep(0.5)
        if wlan.isconnected():
            return True, wlan.ifconfig()[0]
        wlan.disconnect()

    return False, None


if NETWORKS:
    ok, ip = connect_wifi()
    if ok:
        print("WiFi connected:", ip, f"({HOSTNAME}.local)")
        webrepl.start(password=WEBREPL_PASSWORD or "bittle")
    else:
        print("WiFi failed — no configured network in range")
else:
    print("No wifi_config.py — skipping WiFi")
