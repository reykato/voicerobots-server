from threadedevent import ThreadedEvent

class DecisionMaker(ThreadedEvent):
    class DecisionMaker:
        def __init__(self, vsh, lsh, csh):
            """
            Class for making decisions based on the input streams.

            Parameters:
            - vsh (VideoStreamHandler): VideoStreamHandler object.
            - lsh (LidarStreamHandler): LidarStreamHandler object.
            - csh (ControlStream): ControlStream object.
            """

            self.vsh = vsh
            self.lsh = lsh
            self.csh = csh

    def _before_starting(self):
        pass

    def _after_stopping(self):
        pass

    def _handle_stream(self):
        pass