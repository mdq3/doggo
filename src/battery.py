"""Battery voltage monitoring for BiBoard V1.0.

GPIO 37 is the battery voltage divider input (ADC1 channel 1).
Formula from OpenCat reaction.h (BiBoard_V1_0 branch).

2S LiPo range: 6.6V (empty, 3.3V/cell) → 8.4V (full, 4.2V/cell).
Charge warning threshold: 7.0V (3.5V/cell).
"""
from machine import ADC, Pin

_adc = ADC(Pin(37))
_adc.atten(ADC.ATTN_11DB)

_V_FULL  = 8.4   # 2S LiPo fully charged
_V_EMPTY = 6.6   # 2S LiPo safe minimum
_V_WARN  = 7.0   # suggest charging below this


def battery_voltage():
    """Return battery voltage in volts."""
    return _adc.read() / 515 + 1.9


def battery_status():
    """Return (voltage, percent, needs_charge) tuple."""
    v = battery_voltage()
    pct = int(max(0, min(100, (v - _V_EMPTY) / (_V_FULL - _V_EMPTY) * 100)))
    return v, pct, v < _V_WARN
