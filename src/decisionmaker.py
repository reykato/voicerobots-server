from time import sleep, time
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
    LIDAR_START_ANGLE = 330
    LIDAR_END_ANGLE   = 30

    # distance of closest object for which the lidar should stop the robot (in mm)
    LIDAR_DISTANCE_THRESHOLD = 250

    # time to search for a target before moving (in seconds)
    SEARCH_TIME = 11.5

    # time that the robot will wait for an object to move before giving up (in seconds)
    GIVE_UP_TIME = 5

    def __init__(self, vsh:VideoStreamHandler, lsh:LidarStreamHandler, cs:ControlStream, ash:AudioStreamHandler):
        super().__init__()
        self.vsh = vsh
        self.lsh = lsh
        self.cs = cs
        self.ash = ash

        # holds current robot operating mode
        self.mode:str = 'search'
        
        self.stopflag:bool = True

        # hold the most recent frame from video, control tuple from joystick, and lidar scan
        self.target_center = None
        self.lidar_scan = None

        # hold the control data to be sent to the robot
        self.control_data = [0.0, 0.0]
        
        # flag to indicate if the control data has been manually set using the joystick interface
        self.control_data_override = False

        self.giveup_start_time = time()
        self.giveup_started = False

        self.search_start_time = time()
        self.search_started = False

        self.move_start_time = time()
        self.move_started = False
        self.move_and_turn_done = False

        self.prev_control_data = [0.0, 0.0]
        
        self.fullcommand = ""
        

    def _handle_stream(self):
        while not self.stop_event.is_set():
            if not self.control_data_override:
                if not self.stopflag:

                    self.target_center = self.vsh.get_center()
                    self.lidar_scan = self.lsh.get_scan()
                    
                    # decide whether the robot is too close to an object based on the lidar scan
                    stop_robot = self._make_lidar_decision(self.lidar_scan)

                    if self.mode == "search":
                        # print("Search mode...")
                        search_timed_out = self._search_for_target()
                        if search_timed_out:
                            # if no contour found during search, move the robot in a direction for x seconds
                            # assuming robot turned 450 degrees and is ready to move
                            self.mode = "search_move"
                    elif self.mode == "search_move":
                        # print("Search move mode...")
                        self._move_seconds(2.3, "forward")
                        if stop_robot:
                            # if the robot is too close to an object while moving, stop the robot and search immediately
                            self.control_data = [0.0, 0.0]
                    elif self.mode == "search_turn":
                        # print("Search turn mode...")
                        self._turn_seconds(1.5, "left")
                        if stop_robot:
                            # if the robot is too close to an object while turning, stop the robot and search immediately
                            self.control_data = [0.0, 0.0]
                    elif self.mode == "voice":
                        self.control_data = self._scan_audio_direction(self.fullcommand)
                        if stop_robot: # if the robot is too close to an object, stop the robot
                            self.control_data = [0.0, 0.0]
                    elif self.mode == "track":
                        print("track mode...")
                        video_decision = self._make_video_decision(self.target_center)

                        if video_decision[0] == -1: # if the target is too close
                            self.control_data = [0.0, 0.0]
                            self.stopflag = True
                            self.mode = "search"
                            self.search_started = False
                            stop_robot = True

                        # if the robot is too close to an object, wait giveup time before moving and searching again
                        if stop_robot or (not stop_robot and video_decision == [0.0, 0.0]): 
                            if not self.giveup_started:
                                self.giveup_start_time = time()
                                self.giveup_started = True
                            else:
                                if time() - self.giveup_start_time < self.GIVE_UP_TIME:
                                    self.control_data = [0.0, 0.0] # wait
                                else:
                                    self.mode = "search"
                                    self.control_data = [0.0, 0.0]
                                    self.giveup_started = False
                                    self.search_started = False
                        else: # if the robot is not too close to an object and the target is found
                            self.control_data = video_decision
                            self.search_started = False
                            self.giveup_started = False

                else: # if the stop flag is set, stop the robot
                    self.control_data = [0.0, 0.0]
            
            # send the control data to the robot using the control stream
            self._send_control()

            # limit the rate of the decision loop to 10 Hz
            sleep(0.1)

    def _search_for_target(self):
        """
        Searches for a target for a set amount of time before moving the robot to try again.

        Parameters:
            video_decision (tuple): Tuple (x, y) containing the movement controls to move to the target.

        Returns:
            bool: True if the search time has elapsed, False otherwise.
        """

        if not self.search_started:
            # print("Starting search...")
            self.search_start_time = time()
            self.search_started = True

        if time() - self.search_start_time < self.SEARCH_TIME: # if the search time has not elapsed, keep searching
            video_decision = self._make_video_decision(self.target_center)
            if video_decision[0] == -1: # if the target is too close, stop robot
                self.control_data = [0.0, 0.0]
                self.stopflag = True
                self.mode = "search"
                self.search_started = False
                return False
            if video_decision == [0.0, 0.0]: # if no target is found
                self.control_data = [0.4, 0.0]
                return False
            else: # if the target is found, go into tracking mode
                self.mode = "track"
                return False
        else: # if the search time has elapsed
            # print("Search timed out, moving forward...")
            return True
        
    def _move_seconds(self, seconds:int, direction:str):
        """
        Moves the robot forward for a set amount of time.

        Parameters:
            seconds (int): Number of seconds to move the robot.
        """
        if not self.move_started:
            # print("Starting move...")
            self.move_start_time = time()
            self.move_started = True

        if time() - self.move_start_time < seconds: # if the move time has not elapsed, keep moving
            if direction == "forward":
                self.control_data = [0, 1]
            elif direction == "backward":
                self.control_data = [0, -1]
        else: # if the move time has elapsed, turn the robot left
            self.search_started = False
            self.move_started = False
            if not self.move_and_turn_done:
                self.mode = "search_turn"
            else:
                self.mode = "search"
                self.move_and_turn_done = False

    def _turn_seconds(self, seconds:int, direction:str):
        """
        Turns the robot for a set amount of time.

        Parameters:
            seconds (int): Number of seconds to turn the robot.
            direction (str): Direction to turn the robot ('left' or 'right').
        """
        if not self.move_started:
            # print("Starting turn...")
            self.move_start_time = time()
            self.move_started = True

        if time() - self.move_start_time < seconds: # if the move time has not elapsed, keep moving
            if direction == "left":
                self.control_data = [-0.6, 0.0]
            elif direction == "right":
                self.control_data = [0.6, 0.0]
        else: # if the move time has elapsed, search
            self.mode = "search_move"
            self.move_and_turn_done = True
            self.search_started = False
            self.move_started = False

    def _make_video_decision(self, target_center:list) -> list:
        """
        Makes a decision based on the target_center attribute.

        Parameters:
            target_center (tuple): Tuple (x, y) containing the x and y coordinates of the target center.

        Returns:
            tuple: Tuple (x, y) containing the x and y joystick values.
        """
        # print(f"Target Center: {target_center}, making video decision...")

        if target_center[0] == 0 and target_center[1] == 0: # if no target is found
            return [0.0, 0.0]
        elif target_center[0] == -1: # target is too close, pass through escape value
            return [-1, -1]
        else:
            # if the target is to the right of the center, move right (limit output by dividing by 600)
            if target_center[0] > 460:
                return [(target_center[0]-400)/600, 0.2]
            # if the target is to the left of the center, move left (limit output by dividing by 600)
            elif target_center[0] <= 340:
                return [(target_center[0]-400)/600, 0.2]
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
            lidar_scan_narrow = [x for x in lidar_scan if (x[1]
                                  >= self.LIDAR_START_ANGLE and x[1] < 360) or x[1] <= self.LIDAR_END_ANGLE]
            
            # check if any point is too close to the robot
            for point in lidar_scan_narrow:
                # if the distance of the point is less than the threshold, it is too close to the robot
                if point[2] < self.LIDAR_DISTANCE_THRESHOLD:
                    print(f"Object detected at {point[2]} mm, stopping robot...")
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


    def set_control_data(self, control_data:list):
        """
        Sets the control data attribute.

        Parameters:
            control_data: Tuple (x, y) containing the x and y joystick values.
        """
        if not (self.prev_control_data[0] == 0.0 and self.prev_control_data[1] == 0.0 and control_data[0] == 0.0 and control_data[1] == 0.0):
            self.control_data = control_data
            self.control_data_override = True
        self.prev_control_data = control_data
