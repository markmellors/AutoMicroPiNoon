from time import sleep
import math
from approxeng.input.selectbinder import ControllerResource
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comms_codes import Colour, State
from host_comms import Host_comms
mode = State.STOPPED

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

comms = Host_comms()

def joystick_handler(button, comms):
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
    x_axis, y_axis = stick_position
    power_left, power_right = steering(x_axis, y_axis)
    comms.send_packet(State.SUPERVISOR.value, Colour.GREEN.value, power_left, power_right)
    sleep(0.05)


while True:
   if not comms.connected:
       comms.connect()
   else:
       try:
           with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
               print('Controller found, use right stick to drive.')
               while joystick.connected:
                   presses = joystick.check_presses()
                   if joystick.has_presses:
                       mode = joystick_handler(presses, comms)
                   if mode == State.SUPERVISOR.value:
                       supervisor(joystick['rx', 'ry'], comms)
       except IOError:
           # We get an IOError when using the ControllerResource if we don't have a controller yet,
           # so in this case we just wait a second and try again after printing a message.
           print('No controller found yet')
           sleep(0.03)
       except SystemExit:
           raise SystemExit
