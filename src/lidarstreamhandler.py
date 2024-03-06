import socket
import io
import queue
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

    # def _setup_mpl(self):
    #     self.fig = plot.figure()
    #     ax = plot.subplot(111, projection="polar")
    #     line = ax.scatter([0, 0], [0, 0], s=5, c=[0, 50],
    #                        cmap=plot.cm.Greys_r, lw=0)
    #     self.ani = animation.FuncAnimation(self.fig, self._draw_line, fargs=(line), interval=40, cache_frame_data=False)

    def _setup_mpl(self):
        plt.ion()

        self.figure = plt.figure(figsize=(6, 6))
        self.ax = plt.subplot(111, projection='polar')
        self.line1 = self.ax.scatter([0, 0], [0, 0], s=5, c=[0, 50], cmap=plt.cm.Greys_r, lw=0)

    # def _gen_frame(self):
    #     print("gen frame called")
    #     self.fig.canvas.draw()
    #     img = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    #     self.frame = img.reshape(*reversed(self.fig.canvas.get_width_height()), 3)

    #     self.frame_is_new = True
    #     print("generated frame")
        
    def _gen_frame(self):
        scan = []
        while not self.point_buffer.empty():
            scan.append(self.point_buffer.get())

        if scan != []:
            offsets = np.array([(np.radians(meas[1]), meas[2]) for meas in scan])
            self.line1.set_offsets(offsets)
            intens = np.array([meas[0] for meas in scan])
            self.line1.set_array(intens)
        
            # updating data values
            # self.line1.set_xdata(new_x)
            # self.line1.set_ydata(new_y)

            frame_obj = io.BytesIO()
        
            # drawing updated values
            self.figure.canvas.draw()

            # save figure as a jpeg image
            plt.savefig(frame_obj, format='jpeg')
            frame_obj.seek(0)
            frame = frame_obj.read()
            # This will run the GUI event
            # loop until all UI events
            # currently waiting have been processed
            self.figure.canvas.flush_events()

            self.frame = frame
            self.frame_is_new = True

    def get_frame(self):
        return_value = np.asarray(self.frame) if self.frame_is_new else None
        self.frame_is_new = False
        return return_value
        
