from approxeng.input.selectbinder import ControllerResource
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comms_codes import Colour, State
from host_comms import Host_comms

def steering(self, x, y):
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

while True:
   if not comms.connected:
       comms.connected = comms.connect()
   else:
       try:
           with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
               print('Controller found, use right stick to drive.')
               # Loop until the joystick disconnects, or we deliberately stop by raising a
               # RobotStopException
               while joystick.connected:
                   # Get joystick values from the left analogue stick
                   x_axis, y_axis = joystick['rx', 'ry']
                   # Get power from mixer function
                   power_left, power_right = steering(x_axis, y_axis)
                   # Set motor speeds
                   comms.send_packet(1, 1, power_left, power_right)
       except IOError:
           # We get an IOError when using the ControllerResource if we don't have a controller yet,
           # so in this case we just wait a second and try again after printing a message.
           print('No controller found yet')
           sleep(1)
