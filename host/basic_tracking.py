import picamera
import picamera.array

import cv2
import numpy as np
import time
import os
from img_base_class import *
from tendo.singleton import SingleInstance
import main
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
    dist = None

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
  start_time = time.clock()
  while time.clock() < start_time + sleep_time:
    pass

class Tracking():
    def __init__(self):
        image_server_thread = threading.Thread(target=main.launch_video_feed)
        image_server_thread.daemon = True
        image_server_thread.start()
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        self.camera.framerate = 30
        self.camera.exposure_compensation = -16
        self.FRAME_TIME = 1.0 / self.camera.framerate
        self.camera.iso = 800
        self.video = picamera.array.PiRGBArray(self.camera)
        self.saving_images = False
        self.frame_number = 0
        self.PURGE = 50
        self.baselined = False
        TIME_OUT = 1000
        self.END_TIME = time.clock() + TIME_OUT
        base_path = os.path.dirname(os.path.realpath(__file__))
        self.image_dir_path = os.path.join(base_path, "images")
        self.auto_bot = Robot()
        self.user_bot = Robot()
        print("setup complete, camera rolling but stabilising first")

    def calc_ufo_distance(self, image, ufo, target):
        SHADOW_DIST_K = -0.01   #max theoretical dist is ~360, max in practice is?. more diff better
        TRANSLATION_K = 0.1  #theoretical max dist is ~400, typical will be 100. less diff better
        LED_K = 0.1 #theoretical max is ~360, typical will be 100 for opponent, 400 for shadow. less diff better
        shadow_rgb = 120, 180, 150
        ufo_rgb_range = colour_of_contour(image, ufo.contour) #returns 6 values, rgb, 1 S.D. above and below mean 
        ufo_upper_rgb = ufo_rgb_range[1] #takes upper S.D. values
        try:
            ufo_rgb = ufo_upper_rgb[0][0], ufo_upper_rgb[1][0], ufo_upper_rgb[2][0] #converts single element arrays to values
        except:
            print("weird index error:")
            print(ufo_rgb_range)
            print(ufo_upper_rgb)
            ufo_rgb = 120, 180, 150 
        shadow_dist = cv2.norm(ufo_rgb, shadow_rgb)
        if target.area:
            trans_dist = cv2.norm((ufo.x, ufo.y),(target.x, target.y))
        else:
            trans_dist = 100 #no previous position, so use average
        ufo_led = 1.0*ufo.led.hsv[0], 1.0*ufo.led.hsv[1], 1.0*ufo.led.hsv[2]
        if target == self.auto_bot:
            nominal_led_value = 30, 120, 255
        else:
            nominal_led_value = 125, 50, 180
        led_dist = cv2.norm(ufo_led, nominal_led_value)
        weighted_distance = SHADOW_DIST_K * shadow_dist + TRANSLATION_K * trans_dist + LED_K * led_dist
        return weighted_distance

    def find_robot_position(self, image, abs_diff):
        CHANGE_THRESHOLD = 25
        MIN_AREA = 200
        auto_bot, user_bot = Robot(), Robot()
        mask = cv2.inRange(abs_diff, CHANGE_THRESHOLD, 255)
        unknown_objects = self.find_objects(mask, MIN_AREA)
        closest_to_auto_bot, closest_to_user_bot = 1000, 1000
        for num, ufo in enumerate(unknown_objects, start =0):
            ufo.balloon, ufo.led, ufo.p1, ufo.p2 = self.find_markers(image, ufo.contour)
            dist_to_auto_bot = self.calc_ufo_distance(image, ufo, self.auto_bot)
            if dist_to_auto_bot < closest_to_auto_bot:
                auto_bot_index = num
                closest_to_auto_bot = dist_to_auto_bot 
        if len(unknown_objects) > 0:
            obj = unknown_objects[auto_bot_index]
            auto_bot = obj
            auto_bot.angle = atan2(obj.balloon.y - obj.led.y, obj.balloon.x - obj.led.x)
            cv2.arrowedLine(image, (obj.balloon.x, obj.balloon.y),
                            (obj.led.x, obj.led.y), (255, 0, 255), 3, tipLength=0.3)
            cv2.rectangle(image, obj.p1, obj.p2, (0, 255, 0), 1)
            if len(unknown_objects) > 1:
                for num, ufo in enumerate(unknown_objects, start =0):
                    ufo.balloon, ufo.led, ufo.p1, ufo.p2 = self.find_markers(image, ufo.contour)
                    dist_to_user_bot = self.calc_ufo_distance(image, ufo, self.user_bot)
                    if dist_to_user_bot < closest_to_user_bot and not num == auto_bot_index:
                        user_bot_index = num
                        closest_to_user_bot = dist_to_user_bot
                obj = unknown_objects[user_bot_index]
                user_bot = obj
                user_bot.angle = atan2(obj.balloon.y - obj.y, obj.balloon.x - obj.x)
                cv2.arrowedLine(image, (obj.balloon.x, obj.balloon.y),
                                (obj.x, obj.y), (255, 0, 0), 3, tipLength=0.3)
                cv2.rectangle(image, obj.p1, obj.p2, (0, 0, 255), 1)
                target_x = obj.x + int(15*cos(user_bot.angle))
                target_y = obj.y + int(15*sin(user_bot.angle))
                cv2.circle(image, (target_x, target_y), 4, (0, 0, 255), 1)
            self.save_image(image, "balloon")
        return auto_bot, user_bot

    def save_image(self, image, name):
        img_name = os.path.join(self.image_dir_path, str(self.frame_number)+name+".jpg")
        if self.saving_images: cv2.imwrite(img_name, image)
        if name == "balloon": main.update_video(image)


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
         LED_BLUR_SIZE = 3 #must be odd
         v_blurred = cv2.GaussianBlur(v_crop, (LED_BLUR_SIZE, LED_BLUR_SIZE), 0) #blur value channel
         min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(v_blurred) #find brightest and darkest spots again
         led = Marker(max_loc) # led assumed to be brightest spot within contour
         led.hsv = hsv_image[led.y, led.x]
         led.x += x_offset
         led.y += y_offset
#         print ("balloon colour is: %s, led colour: %s" % (balloon.hsv, led.hsv))
         return balloon, led, (x_offset, y_offset), (x_max, y_max)

    def update_baseline(self, current_baseline, latest_image, diff):
        MERGE_FRACTION = 0.01 #fraction of unchanged portion of image to merge into baseline
        KEEP_FRACTION = 1 - MERGE_FRACTION
        DUMB_MERGE_FRACTION = 0.1 #fraction of changed portion of image to merge into baseline
        SANE_FRACTION = 1 - DUMB_MERGE_FRACTION
        CHANGE_THRESHOLD = 15  #think this should be more discriminating than the object detection
        mask = cv2.inRange(diff, 0, CHANGE_THRESHOLD)
        locs = np.where(mask != 0) # Get the non-zero mask locations
        modified_image = latest_image.copy()
        if len(latest_image.shape) == 3 and len(current_baseline.shape) != 3:
            modified_image[locs[0], locs[1]] = current_baseline[locs[0], locs[1], None]
        # Case #2 - Both images are colour or grayscale
        elif (len(latest_image.shape) == 3 and len(current_baseline.shape) == 3) or \
           (len(latest_image.shape) == 1 and len(current_baseline.shape) == 1):
            modified_image[locs[0], locs[1]] = current_baseline[locs[0], locs[1]]
        # Otherwise, we can't do this
        else:
            raise Exception("Incompatible input and output dimensions")
        modified_image = cv2.addWeighted(modified_image, SANE_FRACTION, latest_image, DUMB_MERGE_FRACTION, 0)
        return cv2.addWeighted(current_baseline, KEEP_FRACTION, modified_image, MERGE_FRACTION, 0)

    def run(self):
        try:
            for frame_buf in self.camera.capture_continuous(self.video, format ="bgr", use_video_port=True):
                if time.clock() > self.END_TIME:
                    raise VideoTimeExceeded("Max time exceeded")
                frame = (frame_buf.array)
                self.video.truncate(0)
                # Our operations on the frame come here
                left_crop = 0 #50
                right_crop = 280 #250
                bottom_crop = 0
                top_crop =  240 #210
                frame = frame[bottom_crop:top_crop, left_crop:right_crop]
                if self.frame_number < self.PURGE:
                    short_sleep(self.FRAME_TIME)
                elif self.frame_number == self.PURGE:
                    print("finished stabilising, capturing baseline")
                    BASELINE = frame
                    self.save_image(frame, "baseline")
                    print("baseline saved, running, capturing frames")
                    self.baselined = True
                else:
                    frame_diff = cv2.absdiff(frame, BASELINE)
                    abs_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
                    self.auto_bot, self.user_bot = self.find_robot_position(frame, abs_diff)
                    frame_name = "frame"
                    diff_name = "diff"
                    if self.auto_bot.area:
#                        print ("object found, x: %s,  y: %s, area: %s, angle: %.2f" % 
 #                               (self.robot_one.x , self.robot_one.y, self.robot_one.area, self.robot_one.angle*60))
                        frame_name = "frameF"
                        diff_name = "diffF"
                    else:
                        self.save_image(frame, frame_name)
                    self.save_image(frame_diff, diff_name)
                    BASELINE =  self.update_baseline(BASELINE, frame, abs_diff)
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
