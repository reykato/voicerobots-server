import socket
from streamhandler import StreamHandler
import numpy as np

class LidarStreamHandler(StreamHandler):
    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    def _after_stopping(self):
        self.socket.close()

    def _handle_stream(self):
        while not self.stop_event.is_set():
            try:
                received_data = self.socket.recv(4096)
                if not received_data is None:
                    decoded_data = np.frombuffer(received_data, dtype=np.float32).reshape((-1, 3))
                    for point in decoded_data:
                        print(f"quality: {point[0]}, angle: {point[1]}, distance: {point[2]}")
            except socket.error as e:
                received_data = None
                if not e.args[0] == 'timed out':
                    print(f"Error: '{e.args[0]}', reconnecting...")
                    self._connect_to_server()

