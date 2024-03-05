import socket
import io
import queue
from streamhandler import StreamHandler
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plot
import matplotlib.animation as animation

class LidarStreamHandler(StreamHandler):
    

    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.point_buffer = queue.Queue()
        self.frame = None
        self.frame_is_new = False
        self._setup_mpl()

    def _after_stopping(self):
        self.socket.close()

    def _handle_stream(self):
        while not self.stop_event.is_set():
            try:
                received_data, _ = self.socket.recvfrom(8192)
                if not received_data is None:
                    try:
                        decoded_data = np.frombuffer(received_data, dtype=np.float32).reshape((-1, 3))
                    except:
                        continue
                    for point in decoded_data:
                        # print(f"quality: {point[0]}, angle: {point[1]}, distance: {point[2]}")
                        self.point_buffer.put(point)
            except socket.error as e:
                received_data = None
                if not e.args[0] == 'timed out':
                    print(f"Error: '{e.args[0]}', reconnecting...")
                    self._connect_to_server()
            self._gen_frame()

    def _draw_line(self, line):
        print("draw line called")
        scan = []
        for _ in range(137):
            scan += self.point_buffer.get()
        offsets = np.array([(np.radians(meas[1]), meas[2]) for meas in scan])
        line.set_offsets(offsets)
        intens = np.array([meas[0] for meas in scan])
        line.set_array(intens)
        return line,

    def _setup_mpl(self):
        self.fig = plot.figure()
        ax = plot.subplot(111, projection="polar")
        line = ax.scatter([0, 0], [0, 0], s=5, c=[0, 50],
                           cmap=plot.cm.Greys_r, lw=0)
        ani = animation.FuncAnimation(self.fig, self._draw_line, fargs=(line), interval=40, cache_frame_data=False)

    def _gen_frame(self):
        print("gen frame called")
        self.fig.canvas.draw()
        self.frame = np.fromstring(self.fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        # img = img.reshape(self.fig.canvas.get_width_height()[::1] + (3,))
        # self.frame = plot.plot(img, format='jpeg')
        self.frame_is_new = True
        print("generated frame")

    def get_frame(self):
        return_value = self.frame if self.frame_is_new else None
        if self.frame is None:
            print("frame is none")
        self.frame_is_new = False
        return return_value
