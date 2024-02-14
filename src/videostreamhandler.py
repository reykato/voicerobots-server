from streamhandler import StreamHandler
import pickle
import numpy as np
import socket

class VideoStreamHandler(StreamHandler):
    MAX_PACKET_SIZE = 65540
    frame = None
    frame_is_new = False
    sock = None

    def __init__(self, host, port):
        return super().__init__(host, port)
    
    def _before_starting(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.HOST, self.PORT))

    def _handle_stream(self):
        while not self.stop_event.is_set():
            data, address = self.sock.recvfrom(self.MAX_PACKET_SIZE)
        
            if len(data) < 100:
                frame_info = pickle.loads(data)

                if frame_info:
                    nums_of_packs = frame_info["packs"]
                    buffer = None

                    for i in range(nums_of_packs):
                        data, address = self.sock.recvfrom(self.MAX_PACKET_SIZE)

                        if i == 0:
                            buffer = data
                        else:
                            buffer += data

                    self.frame_is_new = True
                    self.frame = np.frombuffer(buffer, dtype=np.uint8)
    
    def get_frame(self):
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
                    
                    