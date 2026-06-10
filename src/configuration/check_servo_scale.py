"""Servo scale check — is one commanded degree one physical degree?

OpenCat defines Bittle X servos as P1L: 270 degrees of travel over the
500-2500us pulse range (P1S variant: 290 degrees). Our servo.py maps that
same pulse range to 180 degrees. If the servos really are P1L, every
commanded degree moves the horn 1.5 physical degrees.

Run with the robot on a stand or resting (uses only the head pan servo):
    python webrepl_proxy.py run src/configuration/check_servo_scale.py

Watch the head:
  commanded 90 -> 150 is a 60 degree command.
  - head turns ~60 degrees (2/3 of a right angle) -> scale is 1:1, servo.py is fine
  - head turns ~90 degrees (a full right angle)   -> P1L confirmed, scale = 1.5
  - head turns ~97 degrees                        -> P1S, scale = 1.61
"""

import time

from drivers.servo import Servos

CH_HEAD = 0

servos = Servos()

print("Head to commanded 90 (center)...")
servos.set_servo(CH_HEAD, 90)
time.sleep(2)

print("Head to commanded 150 (a 60-degree command)...")
print("If the head sweeps a FULL RIGHT ANGLE, the servo is 270-degree (P1L).")
servos.set_servo(CH_HEAD, 150)
time.sleep(3)

print("Back to commanded 90.")
servos.set_servo(CH_HEAD, 90)
time.sleep(1)
servos.off(CH_HEAD)
