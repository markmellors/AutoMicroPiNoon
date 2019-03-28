from time import sleep
import math, random
from approxeng.input.selectbinder import ControllerResource
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comms_codes import Colour, State
from host_comms import Host_comms
from basic_tracking import Tracking
from basic_heading import Heading, target_maker, circle_target
import threading

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
        comms.send_packet(State.SUPERVISOR.value, Colour.RED.value, 0, 0)
        return State.SUPERVISOR.value
    if button['square']:
        print("auto mode selected")
        comms.send_packet(State.AUTO.value, Colour.GREEN.value, 0, 0)
        return State.AUTO.value

def supervisor(stick_position, comms):
    """function takes the current joystick position, mixes it and sends it to the rover"""
    x_axis, y_axis = stick_position
    power_left, power_right = steering(x_axis, y_axis)
    comms.send_packet(State.SUPERVISOR.value, Colour.RED.value, power_left, power_right)

def auto(comms):
    """placeholder for future"""
    #set speed to a random value just in case we can't figure out what to do:
    RAND_SPEED = 1
    power_left, power_right = random.choice((-RAND_SPEED, RAND_SPEED)), random.choice((-RAND_SPEED, RAND_SPEED))
    if tracking.baselined and tracking.auto_bot.area:
        current_x = tracking.auto_bot.x
        current_y = tracking.auto_bot.y
        current_heading = tracking.auto_bot.angle
        if tracking.user_bot.area:
            target_x, target_y = tracking.user_bot.x, tracking.user_bot.y
        else:
            target_x, target_y = None, None
        speed, turning = planning.path_planning(current_x, current_y, current_heading, target_x, target_y)
        power_left, power_right = steering(turning, speed)
    comms.send_packet(State.AUTO.value, Colour.GREEN.value, power_left, power_right)
    GO_WILD_PROBABILITY = 0.01 if not tracking.auto_bot.area else 0.0003
    GO_WILD_TIME = 0.5
    if random.random() < GO_WILD_PROBABILITY:
        power_left, power_right = random.choice((-RAND_SPEED, RAND_SPEED)), random.choice((-RAND_SPEED, RAND_SPEED))
        comms.send_packet(State.AUTO.value, Colour.YELLOW.value, power_left, power_right)
        print("GOING  WIIILLLLLD!!")
        sleep(GO_WILD_TIME)

mode = State.STOPPED
comms = Host_comms()
planning = Heading()
tracking = Tracking()
tracking_thread = threading.Thread(target=tracking.run)
tracking_thread.daemon = True
tracking_thread.start()



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

if __name__ == "__main__":

    run()
