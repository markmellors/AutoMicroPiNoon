#import sys
#import os
#sys.path.append('/usr/local/lib/python2.7/site-packages')
import picamera
import picamera.array 

import cv2
import numpy as np
import time
import os
from img_base_class import *

camera = picamera.PiCamera()
camera.resolution = (320, 240)
camera.framerate = 30
camera.exposure_compensation = -2
FRAME_TIME = 1.0 / camera.framerate
camera.iso = 800
video = picamera.array.PiRGBArray(camera)
i = 0
PURGE = 50
TIME_OUT = 10
END_TIME = time.clock() + TIME_OUT

file_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(file_path,'/images/')

class Robot():
#    angle = None
#    led_HSV = None, None, None
#    balloon_HSV = None, None, None
    def __init__(self, x = None, y = None, area = 0, contour = None):
        self.x = x
        self.y = y
        self.area = area
        self.contour = contour
    angle = None
    led = None
    balloon = None
    p1 = None
    p2 = None

class Marker():
    def __init__(self, coordinate = None):
        if coordinate:
            self.x, self.y = coordinate
        else:
            self.x, self.y = None, None
    hsv = None

robot_one = Robot()
robot_two = Robot()

print("setup complete, camera rolling but stabilising first")

def short_sleep(sleep_time):
  #function that reimplements time.sleep, but is more repeatable for less than 0.1second sleep times.
  start_time=time.clock()
  while time.clock()<start_time+sleep_time:
    pass

def find_robot_position(image, abs_diff):
    CHANGE_THRESHOLD = 30
    MIN_AREA = 400
    largest_object = Robot()
    mask = cv2.inRange(abs_diff, CHANGE_THRESHOLD, 255)
    MORPH_SIZE = 3
    kernel = np.ones((MORPH_SIZE,MORPH_SIZE),np.uint8) 
    opening = cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
    unknown_objects = find_objects(opening, MIN_AREA)
    for ufo in unknown_objects:
        ufo.balloon, ufo.led, ufo.p1, ufo.p2 = find_markers(image, ufo.contour)
    if len(unknown_objects)>0:
        largest_object = unknown_objects[0]
        largest_object.angle = atan2(unknown_objects[0].balloon.y - unknown_objects[0].led.y, unknown_objects[0].balloon.x - unknown_objects[0].led.x)
        cv2.arrowedLine(image, (unknown_objects[0].balloon.x, unknown_objects[0].balloon.y), (unknown_objects[0].led.x, unknown_objects[0].led.y), (255, 0, 255), 3, tipLength=0.3)
        cv2.rectangle(image, unknown_objects[0].p1, unknown_objects[0].p2, (0, 255, 0), 1)
        ball_img_name = os.path.join(file_path, str(i), "balloon.jpg")
        cv2.imwrite(ball_img_name, image)
    return largest_object

def find_objects(image, area_threshold):
    '''takes a binary image and returns coordinates, size and contourobject of largest contour'''
    contourimage, contours, hierarchy = cv2.findContours(
        image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    # Go through each contour
    objects  = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > area_threshold:
            m = cv2.moments(contour)
            found_x = int(m['m10']/m['m00'])
            found_y = int(m['m01']/m['m00'])
            objects.append(Robot(found_x, found_y, area, contour))
    return objects

def find_markers(image, contour):
     #function to find the distinguishing feature of a robot contour (currently location of an LED and balloon) 
     #and return the properties of those markers (as marker objects) along with the bounding box corners
     cropped_image, x_offset, y_offset, x_max, y_max = crop_to_contour(image, contour)
     hsv_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2HSV)
     h_crop, s_crop, v_crop = cv2.split(hsv_image)
     v_edges = cv2.Canny(v_crop,100,200) #100, 200 are unitless edge detection parameters not used elsewhere
     mask = numpy.full(v_edges.shape[:2], 255, dtype="uint8") #full white mask
     cv2.drawContours(mask, [contour], -1, 0, -1, offset=(-x_offset, -y_offset)) #make region of contour black
     masked_edges = cv2.add(mask, v_edges) #make region of contour equal to  the found edges
     EDGE_BLUR_SIZE = 21 #needs to be odd
     edges_blurred = cv2.GaussianBlur(masked_edges, (EDGE_BLUR_SIZE,EDGE_BLUR_SIZE),0) #smear edges around
     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(edges_blurred) #find darkest and lightest spots.
     balloon = Marker(min_loc) #balloon location assumed to be darkest region, ie. region within contour that is furthest from an edge.
     balloon.hsv = hsv_image[balloon.y, balloon.x]
     balloon.x += x_offset
     balloon.y += y_offset
     LED_BLUR_SIZE = 5 #must be odd
     v_blurred = cv2.GaussianBlur(v_crop, (LED_BLUR_SIZE, LED_BLUR_SIZE), 0) #blur value channel
     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(v_blurred) #find brightest and darkest spots again
     led = Marker(max_loc) # led assumed to be brightest spot within contour
     led.hsv = hsv_image[led.y, led.x]
     led.x += x_offset
     led.y += y_offset
     print ("balloon colour is: %s, led colour: %s" % (balloon.hsv, led.hsv))
     return balloon, led, (x_offset, y_offset), (x_max, y_max)
try:
    for frame_buf in camera.capture_continuous(video, format ="rgb", use_video_port=True):
        if time.clock() > END_TIME:
           raise KeyboardInterrupt
        frame = (frame_buf.array)
        video.truncate(0)
        # Our operations on the frame come here
        left_crop = 50
        right_crop = 250
        bottom_crop = 0
        top_crop =  210
        frame = frame[bottom_crop:top_crop, left_crop:right_crop]
        if i < PURGE:
          short_sleep(FRAME_TIME)
        elif i == PURGE:
          print ("finished stabilising, capturing baseline")
          frame_name = os.path.join(file_path, 'baseline.jpg')
          BASELINE = frame
          cv2.imwrite(frame_name, frame)
          print ("baseline saved, running, capturing frames")
        else:
          frame_diff = cv2.absdiff(frame, BASELINE)
          abs_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
          robot = find_robot_position (frame, abs_diff)

          frame_name = os.path.join(file_path, str(i)+ '.jpg')
          diff_name = os.path.join(file_path, str(i) + 'diff.jpg')
          if robot.area:
            print ("object found, x: %s,  y: %s, area: %s, angle: %.2f" % (robot.x , robot.y, robot.area, robot.angle*60))
            frame_name = os.path.join(file_path, str(i) + 'F.jpg')
            diff_name = os.path.join(file_path, str(i) + 'diffF.jpg')
          else:
              cv2.imwrite(frame_name, frame)
          cv2.imwrite(diff_name, frame_diff)
        i += 1

except KeyboardInterrupt:
    cv2.destroyAllWindows()
