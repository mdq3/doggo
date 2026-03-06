"""Device information for the /info endpoint."""

import gc
import os
import sys
import time

import esp
import machine
import network


def device_info():
    """Return a human-readable string of device diagnostics."""
    gc.collect()
    mem_used = gc.mem_alloc()
    mem_free = gc.mem_free()

    fs = os.statvfs('/')
    bsz = fs[0]
    flash_total = bsz * fs[2]
    flash_free  = bsz * fs[3]
    flash_used  = flash_total - flash_free

    uid = ''.join('{:02x}'.format(b) for b in machine.unique_id())

    wlan = network.WLAN(network.STA_IF)
    ip = wlan.ifconfig()[0]
    try:
        rssi = str(wlan.status('rssi')) + ' dBm'
    except Exception:
        rssi = 'N/A'

    uptime_s = time.ticks_ms() // 1000
    used_pct = flash_used * 100 // flash_total
    lines = [
        'platform:    ' + sys.platform,
        'micropython: ' + sys.version,
        'cpu_freq:    ' + str(machine.freq() // 1000000) + ' MHz',
        'chip_id:     ' + uid,
        'ram_used:    ' + str(mem_used // 1024) + ' KB',
        'ram_free:    ' + str(mem_free // 1024) + ' KB',
        'ram_total:   ' + str((mem_used + mem_free) // 1024) + ' KB',
        'flash_chip:  ' + str(esp.flash_size() // 1024) + ' KB  (total ESP32 flash)',
        'flash_total: ' + str(flash_total // 1024) + ' KB  (filesystem partition)',
        'flash_used:  ' + str(flash_used // 1024) + ' KB (' + str(used_pct) + '%)',
        'flash_free:  ' + str(flash_free // 1024) + ' KB (' + str(100 - used_pct) + '%)',
        'wifi_ip:     ' + ip,
        'wifi_rssi:   ' + rssi,
        'uptime:      ' + str(uptime_s // 3600) + 'h '
                        + str((uptime_s % 3600) // 60) + 'm '
                        + str(uptime_s % 60) + 's',
    ]
    return '\n'.join(lines) + '\n'
