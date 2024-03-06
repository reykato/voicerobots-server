import socket
import io
import queue
import time
from streamhandler import StreamHandler
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class LidarStreamHandler(StreamHandler):
    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.point_buffer = queue.Queue()
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
                if self.point_buffer.qsize() > 300:
                    self.point_buffer = queue.Queue()
                if not received_data is None:
                    try:
                        decoded_data = np.frombuffer(received_data, dtype=np.float32).reshape((-1, 3))
                    except:
                        continue
                    for point in decoded_data:
                        self.point_buffer.put(point)
            except socket.error as e:
                received_data = None
                if not e.args[0] == 'timed out':
                    print(f"Error: '{e.args[0]}'")
            if time_elapsed > .5:
                self.prev_time = time.time()
                self._gen_frame()

    def _setup_mpl(self):
        self.figure = plt.figure(figsize=(6, 6))
        self.ax = plt.subplot(111, projection='polar')
        self.line1 = self.ax.scatter([0, 0], [0, 0], s=8, c=[0, 8000], cmap='viridis', lw=0)
        self.ax.set_ylim(0,6000)
        self.ax.set_facecolor("black")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
    def _gen_frame(self):
        scan = []
        while not self.point_buffer.empty():
            scan.append(self.point_buffer.get())

        if scan != []:
            offsets = np.array([(np.radians(meas[1]), meas[2]) for meas in scan])
            self.line1.set_offsets(offsets)
            dist = np.array([meas[2] for meas in scan])
            self.line1.set_array(dist)

            frame_obj = io.BytesIO()
        
            # drawing updated values
            self.figure.canvas.draw()

            # save figure as a jpeg image
            plt.savefig(frame_obj, format='jpeg')
            frame_obj.seek(0)

            self.frame = frame_obj.read()
            self.frame_is_new = True
            print("lidar frame generated!!")

    def get_frame(self):
        return_value = np.asarray(self.frame) if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
        
