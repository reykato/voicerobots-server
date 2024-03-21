import pickle
import socket
import numpy as np
import cv2
from streamhandler import StreamHandler


class VideoStreamHandler(StreamHandler):
    MAX_PACKET_SIZE = 65540
    frame = None
    frame_is_new = False
    socket = None

    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    def _handle_stream(self):
        while not self.stop_event.is_set():
            data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)

            if len(data) < 100:
                frame_info = pickle.loads(data)

                if frame_info:
                    nums_of_packs = frame_info["packs"]
                    buffer = None

                    for i in range(nums_of_packs):
                        data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)

                        if i == 0:
                            buffer = data
                        else:
                            buffer += data

                    frame = np.frombuffer(buffer, dtype=np.uint8)
                    image = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                    if image is not None:
                        # process frame
                        # convert the frame to an image

                        # isolate red color
                        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
      
                        # Threshold of blue in HSV space 
                        lower_blue = np.array([60, 35, 140]) 
                        upper_blue = np.array([180, 255, 255]) 
                    
                        # preparing the mask to overlay 
                        mask = cv2.inRange(hsv, lower_blue, upper_blue) 

                        # find contours in the mask
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        cv2.drawContours(image, contours, -1, (0,255,0), 3)

                        if contours is None or len(contours) == 0:
                            print("No contours found")
                        
                        result = cv2.bitwise_and(image, image, mask = mask)
                        self.frame = result
                        self.frame_is_new = True

                        # # find the largest contour and its center
                        # max_contour = max(contours, key=cv2.contourArea)
                        # M = cv2.moments(max_contour)
                        # cX = int(M["m10"] / M["m00"])
                        # cY = int(M["m01"] / M["m00"])

                        # # store the center point
                        # self.center = (cX, cY)
                        
                        # # draw a white dot at the coordinates of the center_of_red
                        # cv2.circle(image, (cX, cY), 5, (255, 255, 255), -1)

    def _after_stopping(self):
        self.socket.close()

    def get_frame(self):
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
