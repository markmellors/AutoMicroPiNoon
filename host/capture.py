'''capture.py'''
import cv2, sys
import time

cap = cv2.VideoCapture(0)                    # 0 is for /dev/video0
time.sleep(2)
while True :
    ret, frm = cap.read()
    sys.stdout.write( str(frm.tostring()))
