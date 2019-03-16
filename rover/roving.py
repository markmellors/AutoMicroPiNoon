import explorerhat
from approxeng.input.selectbinder import ControllerResource
from time import sleep
import math

from bluetooth_comms import Comms
import threading
import time
from comm_codes import Colour, State
comm_link = Comms()
comm_thread = threading.Thread(target=comm_link.run)
comm_thread.daemon = True
comm_thread.start()

#explorer output pin mapping to RGB led legs                   
BLUE_PIN = 2
RED_PIN = 0
GREEN_PIN = 1

#brightness (0-100) mapping for different colours
BLUE = [0, 0, 100]
RED = [100, 0, 0]
GREEN = [0, 100, 0]
CYAN = [0, 50, 50]
MAGENTA = [50, 0, 50]
YELLOW = [100, 40, 0]
brightness = 0.25
colour = BLUE
explorerhat.output[RED_PIN].brightness(brightness*colour[0])
explorerhat.output[GREEN_PIN].brightness(brightness*colour[1])
explorerhat.output[BLUE_PIN].brightness(brightness*colour[2])


def steering(x, y):
    """Steering algorithm taken from
    https://electronics.stackexchange.com/a/293108"""
    # convert to polar
    r = math.hypot(x, y)
    t = math.atan2(y, x)

    # rotate by 45 degrees
    t += math.pi / 4

    # back to cartesian
    left = r * math.cos(t)
    right = r * math.sin(t)

    # rescale the new coords
    left = left * math.sqrt(2)
    right = right * math.sqrt(2)

    # clamp to -1/+1
    left = max(-1, min(left, 1))
    right = max(-1, min(right, 1))

    return left, right

def rc_mode:
    if joystick.connected:
         x, y = joystick['rx','ry']
         motor_left, motor_right = steering(x, y)
    else:
        motor_left, motor_right = 0, 0
    explorerhat.motor.one.speed(int(motor_left * 100))
    explorerhat.motor.two.speed(int(motor_right * 100))


while True:
    try:
        if comm_link.connected:
            rc_mode()
        with ControllerResource() as joystick:
            print('Found a joystick and connected')
            while joystick.connected:
                # ....
                # ....
        # Joystick disconnected...
        print('Connection to joystick lost')
    except IOError:
        # No joystick found, wait for a bit before trying again
        print('Unable to find any joysticks')
        sleep(1.0)
