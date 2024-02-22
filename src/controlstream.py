import time
import socket
import threading
from stream import Stream

class ControlStream(Stream):
    server_socket = None
    client_socket = None

    def __init__(self, host, port, control_queue):
        self.host = host
        self.port = port
        self.control_queue = control_queue

        self.stop_event = threading.Event()
        self.loop_thread = threading.Thread(target=self._handle_stream, args=(control_queue,))

    def _handle_stream(self, control_queue):
        while not self.stop_event.is_set():
            # check if there is data in the queue
            if not control_queue.empty():
                # process the data from the queue
                data = control_queue.get()
                byte_stream = data.tobytes()
                try:
                    self.client_socket.sendall(byte_stream)
                except socket.error as e:
                    print(f"Error '{e.args[0]}' occurred. Assuming connection was lost.")
                    self._wait_for_connection()
            else:
                time.sleep(0.01)

    def _wait_for_connection(self):
        print("Waiting for connection...")
        self.client_socket, _ = self.server_socket.accept()

    def _before_starting(self):
        socket.timeout(0.01) # socket will stop waiting for packets after 10ms
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.client_socket, _ = self.server_socket.accept()
        print("Client Connected!")

    def _after_stopping(self):
        self.server_socket.close()

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
