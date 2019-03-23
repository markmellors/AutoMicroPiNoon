import explorerhat
from approxeng.input.selectbinder import ControllerResource
from time import sleep
import math

from bluetooth_comms import Comms
import threading
import time

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comms_codes import Colour, State

comm_link = Comms()
comm_thread = threading.Thread(target=comm_link.run)
comm_thread.daemon = True
comm_thread.start()

#explorer output pin mapping to RGB led legs                   
BLUE_PIN = 2
RED_PIN = 0
GREEN_PIN = 1

#brightness (0-100) mapping for different colours
colour_values = dict({
    "BLUE": [0, 0, 100],
    "RED": [100, 0, 0],
    "GREEN": [0, 100, 0],
    "CYAN": [0, 50, 50],
    "MAGENTA": [50, 0, 50],
    "YELLOW": [100, 40, 0],
    "BLACK": [0, 0, 0]
})
brightness = 0.25


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

def rc_mode(joystick):
    if joystick:
        x, y = joystick['rx','ry']
        motor_left, motor_right = steering(x, y)
    else:
        motor_left, motor_right = 0, 0
    set_motor_speeds(motor_left, motor_right)

def host_mode(joystick):
    """function called if in a mode where motor speeds set by host,
        just passess received speeds straight out"""
    set_motor_speeds(comm_link.motor_one, comm_link.motor_two)

def set_motor_speeds(left, right):
    """function to set motor speeds, accepts left and right as -1 to 1"""
    explorerhat.motor.one.speed(int(left * 100))
    explorerhat.motor.two.speed(int(right * 100))

def stop_motors():
    explorerhat.motor.one.speed(0)
    explorerhat.motor.two.speed(0)

def set_led(colour_name):
    colour = colour_values.get(colour_name, [0, 0, 0])
    explorerhat.output[RED_PIN].brightness(brightness*colour[0])
    explorerhat.output[GREEN_PIN].brightness(brightness*colour[1])
    explorerhat.output[BLUE_PIN].brightness(brightness*colour[2])
    

state_to_mode_map = dict({
    "STOPPED": stop_motors,
    "OFFLINE": rc_mode,
    "RC": rc_mode,
    "SUPERVISOR": host_mode,
    "AUTO": host_mode
})

def main_loop(joystick):
    if comm_link.connected:
        if comm_link.state:
            state = State(comm_link.state).name
        else:
            state = "RC"
        mode = state_to_mode_map.get(state, rc_mode)
        mode(joystick)
        if comm_link.colour:
            set_led(Colour(comm_link.colour).name)
        else:
           colour = "BLACK"
    else:
        rc_mode(joystick)
    time.sleep(0.001)

while True:
    try:
        with ControllerResource() as joystick:
            print("joystick connected")
            while joystick.connected:
                main_loop(joystick)
    except ValueError:
        print("Could not convert data to an integer.")
    except IOError:
        joystick = None
        main_loop(joystick)
    except OSError as err:
        print("OS error: {0}")
        print(err)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        comm_link.stop()
        break
