import socket
import numpy as np

class ControlStream():
    """
    Class for sending robot control data over TCP.

    Parameters:
        host (str): Address of the receiving machine. (e.g. "70.224.3.88")
        port (int): Port which the receiving machine is listening to. (e.g. 5100)
    """
    server_socket = None
    client_socket = None

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def _wait_for_connection(self):
        """
        Waits for a client to connect to the server socket.
        """
        print("Waiting for connection...")
        if self.client_socket:
            self.client_socket.close()
        self.client_socket, _ = self.server_socket.accept()
        print("Client Connected!")

    def _before_starting(self):
        socket.timeout(0.01) # socket will stop waiting for packets after 10ms
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self._wait_for_connection()

    def _after_stopping(self):
        if self.client_socket:
            self.client_socket.close()

    def start(self):
        self._before_starting()

    def stop(self):
        self._after_stopping()

    def send_control(self, control_data):
        """
        Sends control data to the robot.
        """
        if self.client_socket is not None:
            byte_stream = np.array(control_data).tobytes()
            try:
                self.client_socket.sendall(byte_stream)
            except socket.error as e:
                print(f"Error '{e.args[0]}' occurred. Assuming connection was lost.")
                self._wait_for_connection()