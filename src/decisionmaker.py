from time import sleep
import numpy as np
from threadedevent import ThreadedEvent
from videostreamhandler import VideoStreamHandler
from controlstream import ControlStream
from lidarstreamhandler import LidarStreamHandler
from audiostreamhandler import AudioStreamHandler


class DecisionMaker(ThreadedEvent):
    """
    Class for making decisions based on the input streams.

    Parameters:
        vsh (VideoStreamHandler): VideoStreamHandler object.
        lsh (LidarStreamHandler): LidarStreamHandler object.
        cs (ControlStream): ControlStream object (for output).
    """
    
    # angle range for the lidar scan to consider as the front of the robot (in degrees)
    LIDAR_START_ANGLE = 60
    LIDAR_END_ANGLE   = 120

    # distance of closest object for which the lidar should stop the robot (in cm)
    LIDAR_DISTANCE_THRESHOLD = 100

    def __init__(self, vsh:VideoStreamHandler, lsh:LidarStreamHandler, cs:ControlStream, ash:AudioStreamHandler):
        super().__init__()
        self.vsh = vsh
        self.lsh = lsh
        self.cs = cs
        self.ash = ash

        # holds current robot operating mode
        self.mode:str = 'voice'
        self.stopflag:bool = False

        # hold the most recent frame from video, control tuple from joystick, and lidar scan
        self.target_center = None
        self.lidar_scan = None

        # hold the control data to be sent to the robot
        self.control_data = [0.0, 0.0]
        
        # flag to indicate if the control data has been manually set using the joystick interface
        self.control_data_override = False

    def _handle_stream(self):
        """
        Updates the target_center, lidar_scan, and control_data attributes with the most recent data.
        """
        while not self.stop_event.is_set():

            if not self.control_data_override:

                self._make_audio_decision(self.ash.get_transcription())

                if not self.stopflag:

                    self.target_center = self.vsh.get_center()
                    self.lidar_scan = self.lsh.get_scan()
                    
                    # decide whether the robot is too close to an object based on the lidar scan
                    stop_robot = self._make_lidar_decision(self.lidar_scan)

                    if stop_robot:                  # if the robot is too close to an object, stop the robot
                        self.control_data = [0.0, 0.0]
                    else:                           # if the robot is not too close to an object
                        if self.mode == "search":
                            self.control_data = self._make_video_decision(self.target_center)
                        elif self.mode == "voice":
                            self.control_data = self._scan_audio_direction(self.ash.get_transcription())

            # send the control data to the ControlStream object
            self._send_control()
            sleep(0.1)


    def _make_video_decision(self, target_center:list) -> list:
        """
        Makes a decision based on the target_center attribute.

        Parameters:
            target_center (tuple): Tuple (x, y) containing the x and y coordinates of the target center.

        Returns:
            tuple: Tuple (x, y) containing the x and y joystick values.
        """
        # print(f"Target Center: {target_center}, making video decision...")

        if target_center[0] == 0 and target_center[1] == 0:
            return [0.0, 0.0]
        else:
            # if the target is to the right of the center, move right (divide by 960 not 480 max output of 0.5)
            if target_center[0] > 560:
                return [(target_center[0]-480)/960, 0]
            # if the target is to the left of the center, move left (divide by 960 not 480 max output of 0.5)
            elif target_center[0] <= 400:
                return [(target_center[0]-480)/960, 0]
            # if the target is at the center, move forward
            else:
                return [0.0, 0.4]
    
    def _make_lidar_decision(self, lidar_scan:list) -> bool:
        """
        Makes a decision based on the lidar_scan attribute.

        Parameters:
            lidar_scan: Tuple containing the lidar scan data.

        Returns:
            bool: True if the robot is too close to an object, False otherwise.
        """
        if len(lidar_scan) == 0:
            # print(f"No lidar scan data...")
            return False
        else:
            # print(f"Making lidar decision...")

            # only consider points within the front of the robot
            lidar_scan_narrow = [x for x in lidar_scan if x[1]
                                  >= self.LIDAR_START_ANGLE and x[1] <= self.LIDAR_END_ANGLE]
            
            # check if any point is too close to the robot
            for point in lidar_scan_narrow:
                # if the distance of the point is less than the threshold, it is too close to the robot
                if point[2] < self.LIDAR_DISTANCE_THRESHOLD:
                    print(f"Object detected at {point[2]} cm, stopping robot...")
                    return True
                
            # if no object is too close to the robot
            return False
        
    def _make_audio_decision(self, recent_audio:str):
        # print("Recent Audio:" + recent_audio)
        if recent_audio.__contains__("stop"):
            self.stopflag = True
        elif recent_audio.__contains__("start"):
            self.stopflag = False
        elif recent_audio.__contains__("search"):
            self.mode = "search"
        elif recent_audio.__contains__("voice"):
            self.mode = "voice"
        elif recent_audio.__contains__("green"):
            self.vsh.set_lower_upper("green")
        elif recent_audio.__contains__("red"):
            self.vsh.set_lower_upper("red")

    def _scan_audio_direction(self, recent_audio:str):
        if recent_audio.__contains__("forward"):
            return [0.0, 0.3]
        elif recent_audio.__contains__("left") and recent_audio.__contains__("turn"):
            return [0.3, 0.0]
        elif recent_audio.__contains__("right") and recent_audio.__contains__("turn"):
            return [-0.3, 0.0]
        elif recent_audio.__contains__("spin"):
            return [0.5, 0.0]

    def _send_control(self):
        """
        Sends the control data to the ControlStream object.
        """
        # print(f"Sending control data: {self.control_data}")
        if self.control_data is not None:
            nparr = np.array(self.control_data, dtype=np.float32)
            self.cs.send_control(nparr)


    def set_control_data(self, control_data):
        """
        Sets the control data attribute.

        Parameters:
            control_data: Tuple (x, y) containing the x and y joystick values.
        """
        if control_data[0] != 0 and control_data[1] != 0:
            self.control_data = control_data
            self.control_data_override = True
        else:
            self.control_data_override = False