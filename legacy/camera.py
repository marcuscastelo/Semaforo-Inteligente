# camera.py

import cv2
import os
import time


class VideoCamera(object):
    def __init__(self, video):
        self.video = cv2.VideoCapture(video)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        time.sleep(1/30.0)
        return jpeg.tobytes()