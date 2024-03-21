from threadedevent import ThreadedEvent
import numpy as np
import socket
import pyaudio

class AudioStreamHandler(ThreadedEvent):
    MAX_PACKET_SIZE = 65540

    def __init__(self, host, port):
        """
        Class for handling audio IP streams.

        Parameters:
        - host (str): Address of the receiving machine.
        (e.g. "70.224.3.88")
        - port (int): Port which the receiving machine is listening to.
        (e.g. 5100)
        """

        self.host = host
        self.port = port

    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.play=pyaudio.PyAudio()
        self.stream_play=self.play.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)

    def _handle_stream(self):
        while not self.stop_event.is_set():
            data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)

            self.frame = np.frombuffer(data, dtype=np.uint8)
            self.frame_is_new = True

            self.stream_play.write(data)
                
    def _after_stopping(self):
        self.stream_play.stop_stream()
        self.stream_play.close()
        self.play.terminate()
        self.socket.close()

    def get_audio(self):
        return_value = self.frame if self.frame_is_new else None
        self.frame_is_new = False
        return return_value                