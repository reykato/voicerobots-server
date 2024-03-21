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
        self.control_data = (0, 0)

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

    def _send_control(self):
        """
        Sends the control data to the ControlStream object.
        """
        self.cs.send_control(self.control_data)

    def set_control_data(self, control_data:tuple):
        """
        Sets the control data attribute.

        Parameters:
        - control_data (tuple): Tuple (x, y) containing the x and y joystick values.
        """

        self.control_data = control_data