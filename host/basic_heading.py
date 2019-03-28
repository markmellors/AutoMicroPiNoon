import math
import datetime, time

class Heading:
    def __init__(self):
        self.last_x = None
        self.last_y = None
        self.last_heading = None
        self.last_time = None
        self.last_target_x = None
        self.last_target_y = None
        self.v = 0
        self.w = 0
        self.target_v = 0

    def path_planning(self, current_x, current_y, current_heading, target_x, target_y):
        """simple routine to head to a target position"""
        if not target_x: #if no target spotted, use last times values
            if not self.last_time:
                target_x, target_y = 70, 70
            else:
                target_x = 0.01*70 + 0.99*self.last_target_x
                target_y = 0.01*70 + 0.99*self.last_target_y
        if self.last_time:
            self.v = math.sqrt((current_x-self.last_x)**2+(current_y-self.last_y)**2)
            self.w = (current_heading - self.last_heading)/(time.clock() - self.last_time)
            if target_x:
                self.target_v = math.sqrt((target_x-self.last_target_x)**2+(target_y-self.last_target_y)**2)
        heading_offset = 0
        steering_p = 0.9
        steering_d = -0.006
        speed_p = 0.01  #was 0.005 for square
        bearing_to_target = math.atan2((current_y-target_y) , (current_x-target_x))
        distance_to_target = math.sqrt((current_x-target_x)**2+(current_y-target_y)**2)
        heading_error = current_heading - bearing_to_target - heading_offset
        heading_error =  normalise_angle(heading_error)
        if distance_to_target > 30:
            speed = 0.1 + speed_p * distance_to_target
            steering = -steering_p * heading_error
            if self.last_time:
                steering += steering_d * self.w
        else:
            speed = 0
            steering = 0
        self.update_last_properties(current_x, current_y, current_heading, target_x, target_y)
        return speed, steering

    def update_last_properties(self, x, y, heading, t_x, t_y):
        self.last_x = x
        self.last_y = y
        self.last_heading = heading
        self.last_time = time.clock()
        self.last_target_x = t_x
        self.last_target_y = t_y

def normalise_angle(angle):
    """should wrap the angle around and return it in the range +/-pi radians"""
    return math.atan2(math.sin(angle), math.cos(angle))

def target_maker():
    move_time = 10000
    now = datetime.datetime.now()
    #convert now into milliseconds
    now = now.second * 1000 + now.microsecond/1000
    if (now % move_time) > (move_time * 3 / 4):
        x , y = 130, 130
    elif (now % move_time) > (move_time / 2):
        x , y = 130, 75
    elif (now % move_time) > (move_time / 4):
        x , y = 75, 75
    else:
        x , y = 75, 130
    return x, y

def circle_target():
    period = 3000.0
    radius = 40.0
    now = datetime.datetime.now()
    #convert now into milliseconds
    now = now.second * 1000 + now.microsecond/1000
    x = 100 + radius * math.sin(now / period)
    y = 100 + radius * math.cos(now / period)
    return x, y
