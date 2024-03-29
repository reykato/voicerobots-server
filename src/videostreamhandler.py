import pickle
import socket
import numpy as np
import cv2
from threadedevent import ThreadedEvent


class VideoStreamHandler(ThreadedEvent):
    MAX_PACKET_SIZE = 65540

    def __init__(self, host, port):
        """
        Class for handling video IP streams.

        Parameters:
        - host (str): Address of the receiving machine.
        (e.g. "70.224.3.88")
        - port (int): Port which the receiving machine is listening to.
        (e.g. 5100)
        """

        super().__init__()
        self.host = host
        self.port = port

    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.socket.settimeout(0.2)
        self.frame = None
        self.frame_is_new = False
        self.center = (0, 0)

    def _handle_stream(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)
            except TimeoutError:
                continue

            if len(data) < 100:
                frame_info = pickle.loads(data)
                frame = self._get_image(frame_info)

                if frame is not None:
                    self._process_image(frame)
                    

    def _get_image(self, frame_info):
        """
        Receive the frame data from the socket and return the frame as a numpy array.

        Parameters:
        - frame_info (dict): Information about the frame to be received.
        """
        if frame_info is not None:
            # Get the number of packets to be received
            packs_incoming = frame_info["packs"]

            buffer = None

            # Receive the packets
            for i in range(packs_incoming):
                try:
                    data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)
                except TimeoutError:
                    continue

                if i == 0:
                    buffer = data
                else:
                    buffer += data

            if buffer is not None:
                # Convert the JPEG buffer to a numpy array
                frame = np.frombuffer(buffer, np.uint8)
                
                # Decode the JPEG buffer into an OpenCV image
                return cv2.imdecode(frame, cv2.IMREAD_COLOR)

    def _process_image(self, image):
        # Blur the image to reduce noise
        image_blurred = cv2.GaussianBlur(image, (15, 15), 0)

        # Convert the image to HSV
        hsv = cv2.cvtColor(image_blurred, cv2.COLOR_BGR2HSV)

        # Defining the range of red color in HSV space
        # lower_red = np.array([0, 120, 70])
        # upper_red = np.array([10, 255, 255])

        # Defining the range of green color in HSV space
        lower_green = np.array([36, 0, 0])
        upper_green = np.array([86, 255, 255])
    
        # preparing the mask to overlay 
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST,
                                        cv2.CHAIN_APPROX_SIMPLE)

        # find the largest contour and its center
        if len(contours) > 0:
            # get the max size contour based on its area
            max_contour = max(contours, key=cv2.contourArea)

            # draw the contour on the image
            cv2.drawContours(image, max_contour, -1, (0,255,0), 3)

            # get the center of the contour
            M = cv2.moments(max_contour)
            if M["m00"] != 0: # prevent division by zero
                # divide the first moment (m10, m01) by the zeroth moment
                # (which is the area of the contour) to get the center
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX = 0
                cY = 0                            

            # store the center point
            self.center = [cX, cY]
            
            # draw a white dot at the coordinates of the center
            cv2.circle(image, (cX, cY), 5, (255, 255, 255), -1)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        _, processed_buffer = cv2.imencode('.jpg', image, encode_param)
        self.frame = np.frombuffer(processed_buffer, np.uint8)
        self.frame_is_new = True

    def get_center(self):
        return self.center

    def _after_stopping(self):
        self.socket.close()

    def get_frame(self):
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
