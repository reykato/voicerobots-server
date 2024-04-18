import pickle
import socket
import numpy as np
import cv2
from threadedevent import ThreadedEvent


class VideoStreamHandler(ThreadedEvent): 
    """
    Class for handling video IP streams.

    Parameters:
        host (str): Address of the receiving machine. (e.g. "70.224.3.88")
        port (int): Port which the receiving machine is listening to. (e.g. 5100)
    """

    MAX_PACKET_SIZE = 65540
    LOW_CONTOUR_AREA_THRESHOLD = 500 # target is too far to be considered, send [0, 0] as center
    HIGH_CONTOUR_AREA_THRESHOLD = 50000 # target is too close, send [0, 0] as center

    def __init__(self, host: str, port: int):
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
        self.lower = np.array([40, 30, 30])
        self.upper = np.array([90, 255, 255])

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
                    

    def _get_image(self, frame_info: dict):
        """
        Receive the frame data from the socket and return the frame as a numpy array.

        Parameters:
            frame_info (dict): Information about the frame to be received.
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
        """
        Process the image to detect the center of a green object. Also
        generates a new frame to be displayed on the webpage.

        Parameters:
            image (numpy.ndarray): The image to be processed.
        """
        # Blur the image to reduce noise
        image_blurred = cv2.GaussianBlur(image, (15, 15), 0)

        # Convert the image to HSV
        hsv = cv2.cvtColor(image_blurred, cv2.COLOR_BGR2HSV)
    
        # preparing the mask to overlay 
        mask = cv2.inRange(hsv, self.lower, self.upper)

        # find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST,
                                        cv2.CHAIN_APPROX_SIMPLE)

        # find the largest contour and its center
        if len(contours) > 0:
            # get the max size contour based on its area
            max_contour = max(contours, key=cv2.contourArea)

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

            # draw the contour on the image
            cv2.drawContours(image, max_contour, -1, (0,255,0), 3)

            if (cv2.contourArea(max_contour) >= self.LOW_CONTOUR_AREA_THRESHOLD) and (cv2.contourArea(max_contour) <= self.HIGH_CONTOUR_AREA_THRESHOLD):
                # print(f"Max size contour area: {cv2.contourArea(max_contour)}")

                # store the center point
                self.center = [cX, cY]
                
                # draw a white dot at the coordinates of the center
                cv2.circle(image, (cX, cY), 5, (255, 255, 255), -1)
            else:
                # target is too far, don't consider it
                self.center = [0, 0]

                # target is too close, set the center to an escape value to let DecisionMaker know
                if (cv2.contourArea(max_contour) > self.HIGH_CONTOUR_AREA_THRESHOLD):
                    self.center = [-1, -1]

                # draw a red dot at the coordinates of the center since target is too close/far
                cv2.circle(image, (cX, cY), 5, (0, 0, 255), -1)

        else:
            self.center = [0, 0]
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        _, processed_buffer = cv2.imencode('.jpg', image, encode_param)
        self.frame = np.frombuffer(processed_buffer, np.uint8)
        self.frame_is_new = True

    def get_center(self):
        """
        Returns the center (x, y) of the green object in the frame.
        """
        return self.center

    def _after_stopping(self):
        self.socket.close()

    def get_frame(self):
        """
        Returns the latest frame generated from the video stream.
        """
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
    
    def set_lower_upper(self, color:str):
        """
        Sets the lower and upper HSV values for the color to be detected.

        Parameters:
            color (str): The color to be detected. Ex: 'red', 'green'.
        """
        if color == 'red':
            # self.lower = np.array([0, 120, 70])
            # self.upper = np.array([10, 255, 255])
            self.lower = np.array([359, 50, 50])
            self.upper = np.array([20, 255, 255])
        elif color == 'blue':
            self.lower = np.array([110, 50, 50])
            self.upper = np.array([130, 255, 255])
        elif color == 'green':
            self.lower = np.array([40, 30, 30])
            self.upper = np.array([90, 255, 255])
        else:
            # raise ValueError("Invalid color. Available options are 'red', 'green', and 'blue'.")
            self.lower = np.array([255, 255, 255])
            self.upper = np.array([255, 255, 255])
            print("Invalid color. Available options are 'red', 'green', and 'blue'")
        
