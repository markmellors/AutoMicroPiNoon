
from bluetooth import *
import sys
import os
from approxeng.input.selectbinder import ControllerResource
from time import sleep
import math
import struct
import binascii
from enum import Enum
from tendo.singleton import SingleInstance
from  comms_codes import Colour, State

addr = "B8:27:EB:51:3C:F9"

class Sendremotecontrol():
    def __init__(self):
        self.connected = False

    def connect(self):
        # search for the SampleServer service
        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            print ("couldn't find the SampleServer service")
            return False

        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]

        print ("connecting to \"%s\" on %s" % (name, host))

               # Create the client socket
        self.sock=BluetoothSocket( RFCOMM )
        self.sock.connect((host, port))
        print ("bluetooth connected")
        return True


    def set_speeds(self, power_left, power_right):
        """
        As we have an motor hat, we can use the motors
        :param power_left:
            Power to send to left motor
        :param power_right:
            Power to send to right motor, will be inverted to reflect chassis layout
        """
        data = (State.AUTO.value, Colour.RED.value, power_left, power_right)
        s = struct.Struct('iiff')
        packed_data = s.pack(*data)
        self.sock.send(packed_data)
        sleep(0.03)

    def stop_motors(self):
        """
        As we have an motor hat, stop the motors using their motors call
        """
        self.sock.send("0,0")


# All we need, as we don't care which controller we bind to, is the ControllerResource


    class RobotStopException(Exception):
        """
        The simplest possible subclass of Exception, we'll raise this if we want to stop the robot
        for any reason. Creating a custom exception like this makes the code more readable later.
        """
        pass

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
        left = 100 * max(-1, min(left, 1))
        right = 100* max(-1, min(right, 1))

        return left, right

    def run(self):
        # Outer try / except catches the RobotStopException we just defined, which we'll raise when we want to
       # bail out of the loop cleanly, shutting the motors down. We can raise this in response to a button press
       try:
           while True:
	        # Inner try / except is used to wait for a controller to become available, at which point we
               # bind to it and enter a loop where we read axis values and send commands to the motors.
               try:
                   # Bind to any available joystick, this will use whatever's connected as long as the library
                   # supports it.
                   if not self.connected:
                       self.connected = self.connect()
                   else:
                       with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
                           print('Controller found, use right stick to drive.')
                           # Loop until the joystick disconnects, or we deliberately stop by raising a
                           # RobotStopException
                           while joystick.connected:
                               # Get joystick values from the left analogue stick
                               x_axis, y_axis = joystick['rx', 'ry']
                               # Get power from mixer function
                               power_left, power_right = self.steering(x_axis, y_axis)
                               # Set motor speeds
                               self.set_speeds(power_left, power_right)
               except IOError:
                   # We get an IOError when using the ControllerResource if we don't have a controller yet,
                   # so in this case we just wait a second and try again after printing a message.
                   if joystick.connected:
                       print('No controller found yet')
                       sleep(1)
                   else:
                       self.connected = False
                       self.connect()



       except RobotStopException:
           # This exception will be raised when the home button is pressed, at which point we should
           # sop the motors.
           # stop_motors()
           pass

if __name__ == "__main__":
    # Prevent the script from running in parallel by instantiatinh SingleInstance() class.
    # If is there another instance already running it will throw a `SingleInstanceException`.

    me = SingleInstance()
    sendremotecontrol = Sendremotecontrol()
    sendremotecontrol.run()
