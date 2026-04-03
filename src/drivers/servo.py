"""
BiBoard V1 Servo Driver for MicroPython

Controls servos directly via ESP32 PWM (LEDC) - no external chip needed.
BiBoard V1 has 12 servo channels on specific GPIO pins.

Usage:
    from servo import Servos

    servos = Servos()

    # Move servo on channel 0 to 90 degrees
    servos.set_servo(0, 90)
"""

from machine import PWM, Pin

# BiBoard V1.0 PWM pin mapping (channel -> GPIO)
BIBOARD_V1_PINS = [18, 5, 14, 27, 23, 4, 12, 33, 19, 15, 13, 32]


class Servos:
    """BiBoard V1 Direct PWM Servo Driver"""

    def __init__(self, pins=None, freq=200):
        """
        Initialize servo driver

        Args:
            pins: List of GPIO pins (default: BiBoard V1 mapping)
            freq: PWM frequency in Hz (200Hz for digital servos — 8x finer duty
                  resolution than 50Hz within the same 10-bit LEDC timer;
                  drop to 100 or 50 if servos behave erratically)
        """
        self.pins = pins or BIBOARD_V1_PINS
        self.freq = freq
        self.num_channels = len(self.pins)

        # PWM objects for each channel
        self.pwm: list[PWM | None] = [None] * self.num_channels

        # Servo pulse range (microseconds)
        self.min_us = 500  # 0 degrees
        self.max_us = 2500  # 180 degrees

    def _init_channel(self, channel):
        """Initialize PWM for a channel if not already done"""
        if self.pwm[channel] is None:
            pin = Pin(self.pins[channel])
            self.pwm[channel] = PWM(pin, freq=self.freq)

    def _angle_to_duty_u16(self, angle):
        """
        Convert angle to 16-bit duty cycle value.

        At 50Hz, period = 20000us. duty_u16 range is 0-65535.
        Gives ~6500 steps across the servo range vs 103 with 10-bit duty().

        Args:
            angle: 0-180 degrees

        Returns:
            Duty cycle value (0-65535)
        """
        angle = max(0, min(180, angle))
        pulse_us = self.min_us + (angle / 180.0) * (self.max_us - self.min_us)
        period_us = 1000000 / self.freq  # 20000us at 50Hz
        return int(pulse_us / period_us * 65535)

    def set_servo(self, channel, angle):
        """
        Set servo angle

        Args:
            channel: Servo channel (0-11 for BiBoard V1)
            angle: Angle in degrees (0-180)
        """
        if channel < 0 or channel >= self.num_channels:
            raise ValueError(f"Channel must be 0-{self.num_channels - 1}")

        self._init_channel(channel)
        self.pwm[channel].duty_u16(self._angle_to_duty_u16(angle))

    def set_servo_us(self, channel, pulse_us):
        """
        Set servo pulse width in microseconds

        Args:
            channel: Servo channel (0-11)
            pulse_us: Pulse width in microseconds (typically 500-2500)
        """
        if channel < 0 or channel >= self.num_channels:
            raise ValueError(f"Channel must be 0-{self.num_channels - 1}")

        self._init_channel(channel)
        period_us = 1000000 / self.freq
        duty = int(pulse_us / period_us * 65535)
        duty = max(0, min(65535, duty))
        self.pwm[channel].duty_u16(duty)

    def off(self, channel):
        """Turn off a servo channel"""
        if channel < 0 or channel >= self.num_channels:
            return

        if self.pwm[channel] is not None:
            self.pwm[channel].duty(0)

    def all_off(self):
        """Turn off all servo channels"""
        for i in range(self.num_channels):
            self.off(i)

    def deinit(self):
        """Release all PWM resources"""
        for i in range(self.num_channels):
            pwm = self.pwm[i]
            if pwm is not None:
                pwm.deinit()
                self.pwm[i] = None

    # Compatibility methods for code written for PCA9685
    def set_pwm_freq(self, freq):
        """
        Set PWM frequency (for compatibility)

        Note: Changing frequency reinitializes all active channels
        """
        self.freq = freq
        for i in range(self.num_channels):
            pwm = self.pwm[i]
            if pwm is not None:
                pwm.freq(freq)
