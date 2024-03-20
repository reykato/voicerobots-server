class DecisionMaker:
    def __init__(self, buffer):
        self.buffer = buffer

    def process_data(self):
        raise NotImplementedError("Subclasses must implement this method")

    def get_movement(self):
        raise NotImplementedError("Subclasses must implement this method")


class VideoDecisionMaker(DecisionMaker):
    def __init__(self, video_buffer):
        super().__init__(video_buffer)

    def process_data(self):
        # Process video data from the buffer
        pass

    def get_movement(self):
        # Return a tuple for movement based on the video data
        return (0, 0)


class LidarDecisionMaker(DecisionMaker):
    def __init__(self, lidar_buffer):
        super().__init__(lidar_buffer)

    def process_data(self):
        # Process lidar data from the buffer
        pass

    def get_movement(self):
        # Return a tuple for movement based on the lidar data
        return (0, 0)
