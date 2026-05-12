import threading


class LamportClock:
    def __init__(self):
        self.time = 0
        self._lock = threading.Lock()

    def tick(self):  # Increment the clock for internal events
        with self._lock:
            self.time += 1
            return self.time

    def send_event(self):  # Increment the clock for sending events
        with self._lock:
            self.time += 1
            return self.time

    def receive_event(self, received_time):  # Update the clock based on received event
        with self._lock:
            self.time = max(self.time, received_time) + 1
            return self.time

    def get_time(self):
        with self._lock:
            return self.time
    
    