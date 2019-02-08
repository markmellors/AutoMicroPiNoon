
#!/usr/bin/env python
# coding: Latin

# this file contains all the common elements of a threaded image processing challenge
# Load library functions we want
import logging
import logging.config
import os
import time
#import sys
#sys.path.append('/usr/local/lib/python2.7/site-packages')

import threading
#import pygame
#from pygame.locals import*
import picamera
import picamera.array
import cv2
import numpy
from fractions import Fraction
from math import atan2, cos, sin, sqrt, pi

file_path = os.path.dirname(os.path.realpath(__file__))

def threshold_image(image, limits):
        '''function to find what parts of an image lie within limits.
        returns the parts of the original image within the limits, and the mask'''
        hsv_lower, hsv_upper = limits
       
        mask = wrapping_inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        return mask

def crop_to_contour(image, contour):
    x, y, w, h = cv2.boundingRect(contour)
    crop_x_max = x + w
    crop_y_max = y + h
    cropped_image = image[y:crop_y_max, x:crop_x_max]
    return cropped_image, x, y, crop_x_max, crop_y_max

def find_largest_contour(image):
    '''takes a binary image and returns coordinates, size and contourobject of largest contour'''
    contourimage, contours, hierarchy = cv2.findContours(
        image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    # Go through each contour
    found_area = 1
    found_x = -1
    found_y = -1
    biggest_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if found_area < area:
            found_area = area
            m = cv2.moments(contour)
            found_x = int(m['m10']/m['m00'])
            found_y = int(m['m01']/m['m00'])
            biggest_contour = contour
    return found_x, found_y, found_area, biggest_contour

def colour_of_contour(image, contour):
    '''Returns the mean of each channel of a given contour in an image'''
    image = cv2.cvtColor(image, cv2.COLOR_HSV2RGB)
    if contour is not None:
        mask = numpy.zeros(image.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [contour], -1, 255, -1)
        mask = cv2.dilate(mask, None, iterations=1) #erode makes smaller, dilate makes bigger
        mean, stddev = cv2.meanStdDev(image, mask=mask)
        lower = mean - 1.5 * stddev
        upper = mean + 1.5 * stddev
    else:
        lower = None
        upper = None
    return rgb2hsv(*lower), rgb2hsv(*upper)

def rgb2hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df/mx * 255
    v = mx * 255
    h = h * 180 / 360 #to covnert to opencv equivalent hue (0-180)
    return h, s, v

def wrapping_inRange(image, lower_limit, upper_limit):
    '''function to behave like opencv imrange, but allow hue to wrap around
    if hue in lower limit is higher than hue in upper limit, then it will use the wrapped range''' 
    h_lower, s_lower, v_lower = lower_limit
    h_upper, s_upper, v_upper = upper_limit
    if h_lower > h_upper:
        hsv_lower = (0, s_lower, v_lower)
        hsv_upper = (h_upper, s_upper, v_upper)
        imrange1 = cv2.inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        hsv_lower = (h_lower, s_lower, v_lower)
        hsv_upper = (180, s_upper, v_upper)
        imrange2 = cv2.inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        imrange =  cv2.bitwise_or(imrange1, imrange2)
    else:
        imrange = cv2.inRange(
            image,
            numpy.array(lower_limit),
            numpy.array(upper_limit)
        )
    return imrange


def marker_vector(corners):
    x_mid_bottom = (corners[0][0]+corners[1][0])/2
    y_mid_bottom = (corners[0][1]+corners[1][1])/2
    x_mid_top = (corners[2][0]+corners[3][0])/2
    y_mid_top = (corners[2][1]+corners[3][1])/2
    x_diff = x_mid_top - x_mid_bottom
    y_diff = y_mid_top - y_mid_bottom
    return x_diff, y_diff

def getOrientation(pts, img):
    ## [pca]
    # Construct a buffer used by the pca analysis
    sz = len(pts)
    data_pts = numpy.empty((sz, 2), dtype=numpy.float64)
    for i in range(data_pts.shape[0]):
        data_pts[i,0] = pts[i,0,0]
        data_pts[i,1] = pts[i,0,1]

    # Perform PCA analysis
    mean = numpy.empty((0))
    mean, eigenvectors, eigenvalues = cv2.PCACompute2(data_pts, mean)

    # Store the center of the object
    cntr = (int(mean[0,0]), int(mean[0,1]))
    ## [pca]

    ## [visualization]
    # Draw the principal components
#    cv2.circle(img, cntr, 3, (255, 0, 255), 2)
#    p1 = (cntr[0] + 0.02 * eigenvectors[0,0] * eigenvalues[0,0], cntr[1] + 0.02 * eigenvectors[0,1] * eigenvalues[0,0])
#    p2 = (cntr[0] - 0.02 * eigenvectors[1,0] * eigenvalues[1,0], cntr[1] - 0.02 * eigenvectors[1,1] * eigenvalues[1,0])
#    drawAxis(img, cntr, p1, (0, 255, 0), 1)
#    drawAxis(img, cntr, p2, (255, 255, 0), 5)

    angle = atan2(eigenvectors[0,1], eigenvectors[0,0]) # orientation in radians
    ## [visualization]

    return angle
