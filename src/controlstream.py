from time import time
import socket
import threading
from stream import Stream

class ControlStream(Stream):
    socket = None

    def __init__(self, host, port, control_queue):
        super().__init__(host, port)
        self.control_queue = control_queue

    def _handle_stream(self):
        while not self.stop_event.is_set():
            # check if there is data in the queue
            if not self.control_queue.empty():
                # process the data from the queue
                data = self.control_queue.get()

                # Send data
                self.socket.sendall(data.encode())

                # Wait for a response
                received_data = self.socket.recv(1024)
                print(f"Received: {received_data.decode()}")

                # Wait for some time before sending the next message
                time.sleep(1)
            else:
                # sleep for a while to avoid busy-waiting
                time.sleep(1)

    def _before_starting(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    def _after_stopping(self):
        self.socket.close()

    def start(self):
        """
        Executes code in `_before_starting`, then opens thread on
        `_handle_stream`.
        """

        if not self.loop_thread.is_alive():
            self._before_starting()
            self.stop_event.clear()
            self.loop_thread = threading.Thread(
                target=self._handle_stream, args=(self.control_queue,))
            self.loop_thread.start()
            print("Loop started.")
        else:
            print("Loop is already running.")
