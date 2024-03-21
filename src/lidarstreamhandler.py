import socket
import io
import queue
import time
from threadedevent import ThreadedEvent
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class LidarStreamHandler(ThreadedEvent):
    def __init__(self, host, port):
        """
        Class for handling lidar IP streams.

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
        # self.point_buffer = queue.Queue()
        self.scan = []
        self.bg = None
        self.frame_obj = io.BytesIO()
        self.frame = None
        self.frame_is_new = False
        self.prev_time = time.time()
        self._setup_mpl()

    def _after_stopping(self):
        self.socket.close()

    def _handle_stream(self):
        while not self.stop_event.is_set():
            time_elapsed = time.time() - self.prev_time
            try:
                received_data, _ = self.socket.recvfrom(8192)
                if not received_data is None:
                    try:
                        self.scan = np.frombuffer(received_data, dtype=np.float32).reshape((-1, 3))
                    except:
                        print("Exception in _handle_stream, LiDAR data received is bunk")
            except socket.error as e:
                received_data = None
                if not e.args[0] == 'timed out':
                    print(f"Error: '{e.args[0]}'")
            if time_elapsed > .5:
                self.prev_time = time.time()
                self._gen_frame()
                

    def _setup_mpl(self):
        self.figure = plt.figure(figsize=(6, 6), dpi=80, facecolor='black', edgecolor='black')
        self.ax = plt.subplot(111, projection='polar')
        self.line = self.ax.scatter([0, 0], [0, 0], s=8, c=[0, 8000], cmap='viridis', lw=0)
        self.ax.set_ylim(0,6000)
        self.ax.set_facecolor("black")
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.figure.canvas.draw()
        self.bg = self.figure.canvas.copy_from_bbox(self.ax.bbox)
        
    def _gen_frame(self):
        if self.scan is not None and len(self.scan) > 0:
            offsets = np.array([(np.radians(meas[1]), meas[2]) for meas in self.scan])
            self.line.set_offsets(offsets)
            dist = np.array([meas[2] for meas in self.scan])
            self.line.set_array(dist)

            # add generated background (axes and such)
            self.figure.canvas.restore_region(self.bg)

            self.frame_obj.seek(0)

            # redraw the rest of the scatter plot (new points)
            self.ax.draw_artist(self.line)

            # save figure as a png image
            plt.savefig(self.frame_obj, format='png')
            self.frame_obj.seek(0)

            self.frame = self.frame_obj.read()
            self.frame_is_new = True
            print("lidar frame generated!!")

    def get_scan(self):
        return self.scan

    def get_frame(self):
        return_value = np.asarray(self.frame) if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
        
