"""boot.py — runs on every device boot before main.py.

Connects to WiFi and starts WebREPL if wifi_config.py is present.
Falls through gracefully without WiFi if not configured or connection fails.
"""
import network
import time
import webrepl

try:
    from wifi_config import SSID, PASSWORD, WEBREPL_PASSWORD
except ImportError:
    SSID = PASSWORD = WEBREPL_PASSWORD = None


def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        deadline = time.time() + timeout
        while not wlan.isconnected() and time.time() < deadline:
            time.sleep(0.5)
    if wlan.isconnected():
        return True, wlan.ifconfig()[0]
    return False, None


if SSID:
    ok, ip = connect_wifi(SSID, PASSWORD)
    if ok:
        print("WiFi connected:", ip)
        webrepl.start(password=WEBREPL_PASSWORD or "bittle")
    else:
        print("WiFi failed — continuing without network")
else:
    print("No wifi_config.py — skipping WiFi")
