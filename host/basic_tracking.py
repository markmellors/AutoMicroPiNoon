import picamera
import picamera.array

import cv2
import numpy as np
import time
import os
from img_base_class import *
from tendo.singleton import SingleInstance

class VideoTimeExceeded(Exception):
    pass

class Robot:
    #class for storing the properties of detected robots
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

class Marker():
    #class for storing the properties of detected robot markers
    def __init__(self, coordinate = None):
        if coordinate:
            self.x, self.y = coordinate
        else:
            self.x, self.y = None, None
    hsv = None

def short_sleep(sleep_time):
  #function that reimplements time.sleep, but is more repeatable for less than 0.1second sleep times.
  start_time=time.clock()
  while time.clock()<start_time+sleep_time:
    pass

class Tracking:
    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        self.camera.framerate = 30
        self.camera.exposure_compensation = -2
        self.FRAME_TIME = 1.0 / self.camera.framerate
        self.camera.iso = 800
        self.video = picamera.array.PiRGBArray(self.camera)
        self.saving_images = True
        self.frame_number = 0
        self.PURGE = 50
        TIME_OUT = 10
        self.END_TIME = time.clock() + TIME_OUT
        base_path = os.path.dirname(os.path.realpath(__file__))
        self.image_dir_path = os.path.join(base_path, "images")
        self.robot_one = Robot()
        self.robot_two = Robot()
        print("setup complete, camera rolling but stabilising first")


    def find_robot_position(self, image, abs_diff):
        CHANGE_THRESHOLD = 30
        MIN_AREA = 400
        largest_object = Robot()
        mask = cv2.inRange(abs_diff, CHANGE_THRESHOLD, 255)
        MORPH_SIZE = 3
        kernel = np.ones((MORPH_SIZE,MORPH_SIZE),np.uint8) 
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        unknown_objects = self.find_objects(opening, MIN_AREA)
        for ufo in unknown_objects:
            ufo.balloon, ufo.led, ufo.p1, ufo.p2 = self.find_markers(image, ufo.contour)
        if len(unknown_objects) > 0:
            obj = unknown_objects[0]
            largest_object = obj
            largest_object.angle = atan2(obj.balloon.y - obj.led.y, obj.balloon.x - obj.led.x)
            cv2.arrowedLine(image, (obj.balloon.x, obj.balloon.y),
                            (obj.led.x, obj.led.y), (255, 0, 255), 3, tipLength=0.3)
            cv2.rectangle(image, obj.p1, obj.p2, (0, 255, 0), 1)
            self.save_image(image, "balloon")
        return largest_object

    def save_image(self, image, name):
        img_name = os.path.join(self.image_dir_path, str(self.frame_number)+name+".jpg")
        if self.saving_images: cv2.imwrite(img_name, image)

    def find_objects(self, image, area_threshold):
        '''takes a binary image and returns coordinates, size and contourobject of largest contour'''
        contourimage, contours, hierarchy = cv2.findContours(
            image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        # Go through each contour
        objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > area_threshold:
                m = cv2.moments(contour)
                found_x = int(m['m10']/m['m00'])
                found_y = int(m['m01']/m['m00'])
                objects.append(Robot(found_x, found_y, area, contour))
        return objects


    def find_markers(self, image, contour):
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

    def run(self):
        try:
            for frame_buf in self.camera.capture_continuous(self.video, format ="rgb", use_video_port=True):
                if time.clock() > self.END_TIME:
                    raise VideoTimeExceeded("Max time exceeded")
                frame = (frame_buf.array)
                self.video.truncate(0)
                # Our operations on the frame come here
                left_crop = 50
                right_crop = 250
                bottom_crop = 0
                top_crop =  210
                frame = frame[bottom_crop:top_crop, left_crop:right_crop]
                if self.frame_number < self.PURGE:
                    short_sleep(self.FRAME_TIME)
                elif self.frame_number == self.PURGE:
                    print("finished stabilising, capturing baseline")
                    BASELINE = frame
                    self.save_image(frame, "baseline")
                    print("baseline saved, running, capturing frames")
                else:
                    frame_diff = cv2.absdiff(frame, BASELINE)
                    abs_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
                    robot = self.find_robot_position(frame, abs_diff)

                    frame_name = "frame"
                    diff_name = "diff"
                    if robot.area:
                        print ("object found, x: %s,  y: %s, area: %s, angle: %.2f" % (robot.x , robot.y, robot.area, robot.angle*60))
                        frame_name = "frameF"
                        diff_name = "diffF"
                    else:
                        self.save_image(frame, frame_name)
                    self.save_image(frame_diff, diff_name)
                self.frame_number += 1

        except (KeyboardInterrupt, VideoTimeExceeded) as exc:
            print(exc)
            cv2.destroyAllWindows()

if __name__ == "__main__":
    # Prevent the script from running in parallel by instantiatinh SingleInstance() class.
    # If is there another instance already running it will throw a `SingleInstanceException`.

    me = SingleInstance()
    tracking = Tracking()
    tracking.run()
