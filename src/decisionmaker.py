from threadedevent import ThreadedEvent
from videostreamhandler import VideoStreamHandler
from controlstream import ControlStream
from lidarstreamhandler import LidarStreamHandler

class DecisionMaker(ThreadedEvent):
    def __init__(self, vsh:VideoStreamHandler, lsh:LidarStreamHandler, cs:ControlStream):
        """
        Class for making decisions based on the input streams.

        Parameters:
        - vsh (VideoStreamHandler): VideoStreamHandler object.
        - lsh (LidarStreamHandler): LidarStreamHandler object.
        - cs (ControlStream): ControlStream object (for output).
        """

        self.vsh = vsh
        self.lsh = lsh
        self.cs = cs

        # hold the most recent frame from video, control tuple from joystick, and lidar scan
        self.target_center = None
        self.lidar_scan = None
        self.control_data = None

    def _before_starting(self):
        pass

    def _after_stopping(self):
        pass

    def _handle_stream(self):
        """
        Updates the target_center, lidar_scan, and control_data attributes with the most recent data.
        """
        while not self.stop_event.is_set():
            self.target_center = self.vsh.get_center()
            self.lidar_scan = self.lsh.get_scan()
            # need to add a method to get the control data from the flask instance