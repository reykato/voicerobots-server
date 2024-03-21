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

                    # Convert the JPEG buffer to a numpy array
                    frame = np.frombuffer(buffer, np.uint8)
                    
                    # Decode the JPEG buffer into an OpenCV image
                    image = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                    if image is not None:
                        # isolate red color
                        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
      
                        # Threshold of blue in HSV space 
                        # Defining the range of red color in HSV space
                        lower_red = np.array([0, 120, 70])
                        upper_red = np.array([10, 255, 255])
                    
                        # preparing the mask to overlay 
                        mask = cv2.inRange(hsv, lower_red, upper_red) 

                        # find contours in the mask
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        cv2.drawContours(image, contours, -1, (0,255,0), 3)

                        if contours is None or len(contours) == 0:
                            print("No contours found")
                        
                        _, processed_buffer = cv2.imencode('.jpg', image)
                        self.frame = np.frombuffer(processed_buffer, np.uint8)
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
