#import sys
#import os
#sys.path.append('/usr/local/lib/python2.7/site-packages')
import picamera
import picamera.array 

import cv2
import numpy as np
import time
from img_base_class import *

camera = picamera.PiCamera()
camera.resolution = (320, 240)
camera.framerate = 30
FRAME_TIME = 1.0 / camera.framerate
camera.iso = 800
video = picamera.array.PiRGBArray(camera)
i = 0
PURGE = 50
TIME_OUT = 5
END_TIME = time.clock() + TIME_OUT
#create small cust dictionary

print("setup complete, camera rolling but stabilising first")

def short_sleep(sleep_time):
  start_time=time.clock()
  while time.clock()<start_time+sleep_time:
    pass

def find_robot_position(image):
    CHANGE_THRESHOLD = 30
    MIN_AREA = 100
    largest_object_x = None
    largest_object_y = None
    largest_object_area = 0
    largest_object_angle = None
    mask = cv2.inRange(image, CHANGE_THRESHOLD, 255)
    x, y, a, ctr = find_largest_contour(mask)
    if a > MIN_AREA and a > largest_object_area:
        largest_object_x = x
        largest_object_y = y
        largest_object_area = a
        largest_object_angle = getOrientation(ctr,image)
    return largest_object_x, largest_object_y, largest_object_area, largest_object_angle

def find_balloon(image):
     return 0
try:
    for frameBuf in camera.capture_continuous(video, format ="rgb", use_video_port=True):
        if time.clock() > END_TIME:
           raise KeyboardInterrupt
        frame = (frameBuf.array)
        video.truncate(0)
        # Our operations on the frame come here
        if i < PURGE:
          short_sleep(FRAME_TIME)
        elif i == PURGE:
          print ("finished stabilising, capturing baseline")
          frame_name = "baseline.jpg"
          BASELINE = frame
          cv2.imwrite(frame_name, frame)
          print ("baseline saved, running, capturing frames")
        else:
          frame_diff = cv2.absdiff(frame, BASELINE)
          abs_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
          x, y, a, angle = find_robot_position (abs_diff)
          frame_name = str(i) + ".jpg"
          diff_name = str(i) + "diff.jpg"
          if a:
            print ("object found, x: %s,  y: %s, area: %s, angle: %.2f" % (x , y, a, angle*60))
            frame_name = str(i) + "F.jpg"
            diff_name = str(i) + "diffF.jpg"
          cv2.imwrite(diff_name, frame_diff)
          cv2.imwrite(frame_name, frame)
        i += 1

except KeyboardInterrupt:
    cv2.destroyAllWindows()
