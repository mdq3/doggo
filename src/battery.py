"""Battery voltage monitoring for BiBoard V1.0.

GPIO 37 is the battery voltage divider input (ADC1 channel 1).
Formula from OpenCat reaction.h (BiBoard_V1_0 branch).
"""
from machine import ADC, Pin

_adc = ADC(Pin(37))
_adc.atten(ADC.ATTN_11DB)


def battery_voltage():
    """Return battery voltage in volts."""
    return _adc.read() / 515 + 1.9
