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
file_path += "/images/"

class Robot(object):
#    angle = None
#    led_HSV = None, None, None
#    balloon_HSV = None, None, None
    def __init__(self, x = None, y = None, area = None, contour = None):
        self.x = x
        self.y = y
        self.area = area
        self.contour = contour
    angle = None
    led = None
    balloon = None
    p1 = None
    p2 = None

class marker(object):
    def __init__(self, coordinate = None):
        self.x, self.y = coordinate
    HSV = None

robot_one = Robot()
robot_two = Robot()

print("setup complete, camera rolling but stabilising first")

def short_sleep(sleep_time):
  start_time=time.clock()
  while time.clock()<start_time+sleep_time:
    pass

def find_robot_position(image, abs_diff):
    CHANGE_THRESHOLD = 10
    MIN_AREA = 400
    largest_object_x = None
    largest_object_y = None
    largest_object_area = 0
    largest_object_angle = None
    mask = cv2.inRange(abs_diff, CHANGE_THRESHOLD, 255)
    unknown_objects = find_objects(mask, MIN_AREA)
    print (len(unknown_objects))
    for ufo in unknown_objects:
        ufo.balloon, ufo.led, ufo.p1, ufo.p2 = find_markers(image, ufo.contour)
    if len(unknown_objects)>0:
        largest_object_x = unknown_objects[0].x
        largest_object_y = unknown_objects[0].y
        largest_object_area = unknown_objects[0].area
        largest_object_angle = atan2(unknown_objects[0].balloon.y - unknown_objects[0].led.y, unknown_objects[0].balloon.x - unknown_objects[0].led.x)
        cv2.arrowedLine(image, (unknown_objects[0].balloon.x, unknown_objects[0].balloon.y), (unknown_objects[0].led.x, unknown_objects[0].led.y), (255, 0, 255), 3, tipLength=0.3)
        cv2.rectangle(image, unknown_objects[0].p1, unknown_objects[0].p2, (0, 255, 0), 1)
        ball_img_name = file_path + str(i) + "balloon.jpg"
        cv2.imwrite(ball_img_name, image)
    return largest_object_x, largest_object_y, largest_object_area, largest_object_angle

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
     cropped_image, x_offset, y_offset, x_max, y_max = crop_to_contour(image, contour)
     HSV_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2HSV)
     H_crop, S_crop, V_crop = cv2.split(HSV_image)
     V_edges = cv2.Canny(V_crop,100,200)
     mask = numpy.full(V_edges.shape[:2], 255, dtype="uint8")
     cv2.drawContours(mask, [contour], -1, 0, -1, offset=(-x_offset, -y_offset))
     masked_edges = cv2.add(mask, V_edges)
     edges_blurred = cv2.GaussianBlur(masked_edges, (21,21),0)     
     minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(edges_blurred)
     balloon = marker(minLoc)
     balloon.HSV = HSV_image[balloon.y, balloon.x]
     balloon.x += x_offset
     balloon.y += y_offset
     V_blurred = cv2.GaussianBlur(V_crop, (5, 5), 0)
     minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(V_blurred)
     led = marker(maxLoc)
     led.HSV = HSV_image[led.y, led.x]
     led.x += x_offset
     led.y += y_offset
     print ("balloon colour is: %s, led colour: %s" % (balloon.HSV, led.HSV))
     return balloon, led, (x_offset, y_offset), (x_max, y_max)
try:
    for frameBuf in camera.capture_continuous(video, format ="rgb", use_video_port=True):
        if time.clock() > END_TIME:
           raise KeyboardInterrupt
        frame = (frameBuf.array)
        video.truncate(0)
        # Our operations on the frame come here
        frame = frame[0:210, 50:250]
        if i < PURGE:
          short_sleep(FRAME_TIME)
        elif i == PURGE:
          print ("finished stabilising, capturing baseline")
          frame_name = file_path + "baseline.jpg"
          BASELINE = frame
          cv2.imwrite(frame_name, frame)
          print ("baseline saved, running, capturing frames")
        else:
          frame_diff = cv2.absdiff(frame, BASELINE)
          abs_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
          x, y, a, angle = find_robot_position (frame, abs_diff)

          frame_name = file_path + str(i) + ".jpg"
          diff_name = file_path + str(i) + "diff.jpg"
          if a:
            print ("object found, x: %s,  y: %s, area: %s, angle: %.2f" % (x , y, a, angle*60))
            frame_name = file_path + str(i) + "F.jpg"
            diff_name = file_path + str(i) + "diffF.jpg"
          else:
              cv2.imwrite(frame_name, frame)
          cv2.imwrite(diff_name, frame_diff)
        i += 1

except KeyboardInterrupt:
    cv2.destroyAllWindows()
