import threading

class ThreadedEvent():
    def __init__(self):
        self.stop_event = threading.Event()
        self.loop_thread = threading.Thread(target=self._handle_stream)
    
    def _handle_stream(self):
        """
        Processes packets into data and calls functions for additional processing.
        """
        pass
    def _after_stopping(self):
        """
        Code to execute after stopping the loop `_handle_stream`.
        """
        pass
    def _before_starting(self):
        """
        Code to execute before starting the loop `_handle_stream`.
        """   
        pass
    def start(self):
        """
        Executes code in `_before_starting`, then opens thread on
        `_handle_stream`.
        """

        if not self.loop_thread.is_alive():
            self._before_starting()
            self.stop_event.clear()
            self.loop_thread = threading.Thread(target=self._handle_stream)
            self.loop_thread.start()
            print("Loop started.")
        else:
            print("Loop is already running.")

    def stop(self):
        """
        Stops the loop started using `start()` and runs code at `_after_stopping`.
        """
        if self.loop_thread:
            if self.loop_thread.is_alive():
                self.stop_event.set()
                self._after_stopping()
                self.loop_thread.join()
                print("Loop stopped.")
            else:
                print("Loop is not running.")
        else:
            print("Loop has not been started.")

    

