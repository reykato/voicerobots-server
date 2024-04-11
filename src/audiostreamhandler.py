from threadedevent import ThreadedEvent
import numpy as np
import socket
import whisper
import torch
# import pyaudio
import pickle

class AudioStreamHandler(ThreadedEvent):
    """
    Class for handling audio IP streams.

    Parameters:
        host (str): Address of the receiving machine. (e.g. "70.224.3.88")
        port (int): Port which the receiving machine is listening to. (e.g. 5100)
    """
    MAX_PACKET_SIZE = 65540

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self.model = whisper.load_model("tiny.en")
        self.text = ""


    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        # self.play=pyaudio.PyAudio()
        # self.stream_play=self.play.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=1024)

    def _handle_stream(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)
            except TimeoutError:
                continue
            if len(data) < 100:
                print("receiving audio packets")
                self._transcribe_audio(data)
                
    def _transcribe_audio(self, data):
        """
        Receive the audio data from the socket and transcribe it using the whisper model.

        Parameters:
            data (bytes): Audio data to be transcribed.
        """
        frame_info = pickle.loads(data)
        packs_incoming = frame_info["packs"]
        self.buffer = None
        for i in range(packs_incoming):
            try:
                data, _ = self.socket.recvfrom(self.MAX_PACKET_SIZE)
            except TimeoutError:
                continue
            if i == 0:
                self.buffer = data
            else:
                self.buffer += data
        
        try:
            frame = np.frombuffer(self.buffer, dtype=np.uint16).astype(np.float32) / 32768.0
            result = self.model.transcribe(frame, fp16=torch.cuda.is_available())
            # print(result['text'].strip())
            self.text = result['text'].strip()
            # self.stream_play.write(buffer)
        except ValueError:
            pass
                
    def _after_stopping(self):
        # self.stream_play.stop_stream()
        # self.stream_play.close()
        # self.play.terminate()
        self.socket.close()

    def get_transcription(self):
        return self.text

    def get_raw_audio(self):
        return self.buffer    