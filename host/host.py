from time import sleep
import math
from approxeng.input.selectbinder import ControllerResource
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comms_codes import Colour, State
from host_comms import Host_comms

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


def joystick_handler(button, comms):
    """function usess button presses to change mode. also updates the rover appropriately"""
    if button['home']:
        print("exiting")
        comms.send_packet(State.STOPPED.value, Colour.BLACK.value, 0, 0)
        raise SystemExit
    if button['cross']:
        print("stopped mode selected")
        comms.send_packet(State.STOPPED.value, Colour.BLACK.value, 0, 0)
        return State.STOPPED.value
    if button['triangle']:
        print("RC mode selected")
        comms.send_packet(State.RC.value, Colour.BLUE.value, 0, 0)
        return State.RC.value
    if button['circle']:
        print("supervisor mode selected")
        comms.send_packet(State.SUPERVISOR.value, Colour.GREEN.value, 0, 0)
        return State.SUPERVISOR.value
    if button['square']:
        print("auto mode selected")
        comms.send_packet(State.AUTO.value, Colour.RED.value, 0, 0)
        return State.AUTO.value

def supervisor(stick_position, comms):
    """function takes the current joystick position, mixes it and sends it to the rover"""
    x_axis, y_axis = stick_position
    power_left, power_right = steering(x_axis, y_axis)
    comms.send_packet(State.SUPERVISOR.value, Colour.GREEN.value, power_left, power_right)
    sleep(0.05)

def auto(comms):
    """placeholder for future"""
    comms.send_packet(State.AUTO.value, Colour.RED.value, 0, 0)


mode = State.STOPPED
comms = Host_comms()

while True:
   if not comms.connected:
       comms.connect()
   else:
       try:
           with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
               print('Controller found, use right stick to drive when in supervisor mode.')
               print('mode key: triangle = user (RC) mode, circle = supervisor, square = auto, cross = stop. home exits')
               while joystick.connected:
                   presses = joystick.check_presses()
                   if joystick.has_presses:
                       mode = joystick_handler(presses, comms)
                   if mode == State.SUPERVISOR.value:
                       supervisor(joystick['rx', 'ry'], comms)
                   if mode == State.AUTO.value:
                       auto(comms)
                   if not comms.connected:
                       comms.connect()

       except IOError as err:
           # We get an IOError when using the ControllerResource if we don't have a controller yet,
           # so in this case we just wait a second and try again after printing a message.
           print('No controller found yet')
           sleep(1)
       except SystemExit:
           raise SystemExit
