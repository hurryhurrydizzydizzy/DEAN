class LamportClock:
    
    def __init__(self):
        self.time = 0
        
    def tick(self):         # Increment the clock for internal events
        self.time += 1
        return self.time
    
    def send_event(self):   # Increment the clock for sending events
        self.time += 1
        return self.time
    
    def receive_event(self, received_time):     # Update the clock based on received event
        self.time = max(self.time, received_time) + 1
        return self.time
    
    def get_time(self):
        return self.time
    
    