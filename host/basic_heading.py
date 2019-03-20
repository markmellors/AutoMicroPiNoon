import math
import datetime

def path_planning(current_x, current_y, heading, target_x, target_y):
    """simple routine to head to a target position"""
    heading_offset = 0
    steering_p = 0.4
    speed_p = 0.003
    bearing_to_target = math.atan2((current_y-target_y) , (current_x-target_x))
    distance_to_target = math.sqrt((current_x-target_x)**2+(current_y-target_y)**2)
    heading_error = heading - bearing_to_target - heading_offset
    heading_error =  normalise_angle(heading_error)
    if distance_to_target > 30:
        speed = 0.1 + speed_p * distance_to_target
        steering = -steering_p * heading_error
    else:
        speed = 0
        steering = 0
#    print("%s, %s, %s, %s, %s" %(current_x, current_y, heading, bearing_to_target, distance_to_target))
    return speed, steering

def normalise_angle(angle):
    """should wrap the angle around and return it in the range +/-pi radians"""
    return math.atan2(math.sin(angle), math.cos(angle))

def target_maker():
    move_time = 8000
    now = datetime.datetime.now()
    now = now.second * 1000 + now.microsecond/1000
    if (now % move_time) > (move_time / 2):
        x , y = 140, 140
    else:
        x , y = 65, 65
    return x, y
