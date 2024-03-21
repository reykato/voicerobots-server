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
        - cs (ControlStream): ControlStream object.
        """

        self.vsh = vsh
        self.lsh = lsh
        self.cs = cs

        # declare variables to hold the most recent data from video, control, and lidar streams
        self.target_center = None
        self.lidar_scan = None
        self.control_data = None

    def _before_starting(self):
        pass

    def _after_stopping(self):
        pass

    def _handle_stream(self):
        self.target_center = self.vsh.get_center()
        self.lidar_scan = self.lsh.get_scan()
        # need to add a method to get the control data from the flask instance