from streamhandler import StreamHandler
import pickle
import numpy as np
import socket

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

                    self.frame_is_new = True
                    self.frame = np.frombuffer(buffer, dtype=np.uint8)

    def _after_stopping(self):
        self.socket.close()

    def get_frame(self):
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
