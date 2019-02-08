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

def find_robot_position(image, abs_diff):
    CHANGE_THRESHOLD = 30
    MIN_AREA = 100
    largest_object_x = None
    largest_object_y = None
    largest_object_area = 0
    largest_object_angle = None
    mask = cv2.inRange(abs_diff, CHANGE_THRESHOLD, 255)
    x, y, a, ctr = find_largest_contour(mask)
    if a > MIN_AREA and a > largest_object_area:
        largest_object_x = x
        largest_object_y = y
        largest_object_area = a
        largest_object_angle = getOrientation(ctr, abs_diff)
        balloon_x, balloon_y, x_min, x_max, y_min, y_max = find_balloon(image, ctr)
        cv2.circle(image, (balloon_x, balloon_y), 3, (255, 0, 0), 1)
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 1)
        ball_img_name = str(i) + "balloon.jpg"
        cv2.imwrite(ball_img_name, image)
    return largest_object_x, largest_object_y, largest_object_area, largest_object_angle

def find_balloon(image, contour):
     cropped_image, x_offset, y_offset, x_max, y_max = crop_to_contour(image, contour)
     HSV_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2HSV)
     H_crop, S_crop, V_crop = cv2.split(HSV_image)
     S_blurred = cv2.medianBlur(S_crop, 5)
     minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(S_blurred)
     x, y = maxLoc
     return x + x_offset, y + y_offset, x_offset, x_max, y_offset, y_max
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
          x, y, a, angle = find_robot_position (frame, abs_diff)

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
