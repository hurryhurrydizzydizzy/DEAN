import json, time, random, socket, threading
from config import (
    NAMING_SERVER_HOST,
    NAMING_SERVER_PORT,
    SENSOR_DELAY_BY_ID,
)
from lamport import LamportClock

clock = LamportClock() # Initialize the Lamport clock

def get_monitoring_server():        # Query the naming server to get the address of the monitoring server
    
    ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ns.connect((NAMING_SERVER_HOST, NAMING_SERVER_PORT))
    
    lookup_msg = {
        "type": "lookup",
        "name": "monitoring.server.main"
    }
    
    ns.send(json.dumps(lookup_msg).encode())
    response = json.loads(ns.recv(1024).decode())
    ns.close()
    
    return response["host"], response["port"]

def connect_to_monitoring_server():         # Connect to the monitoring server using the address obtained from the naming server
    
    host, port = get_monitoring_server()
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    
    client.connect((host, port))
    
    print(f"Connected to monitoring server at {host}:{port}")
    
    return client

def listen_for_updates(client_socket):      # Listen for updates from the monitoring server and print them out
    while True:
        try:
            data = client_socket.recv(1024) # Receive data from the monitoring server
            
            if not data:
                break
            
            message = json.loads(data.decode())
            
            if message["type"] == "emergency_update":
                
                clock.receive_event(message["lamport_time"])    # Update the Lamport clock based on the received event's Lamport time
                
                print(f"EMERGENCY UPDATE: {message}")
                
        except Exception as e:
            print("Error:", e)
            break
        
def send_alerts(client_socket, sensor_id):      # Simulate sending alerts to the monitoring server with Lamport timestamps and optional delays based on sensor ID
    while True:
        
        input("\nPress Enter to send an alert...\n\n")  # Wait for user input to send an alert
        
        event = random.choice([
            "fire_detected",
            "smoke_detected",
            "heat_detected"
        ])

        # Capture when the event was detected and stamp with Lamport time immediately.
        detected_at_ns = time.time_ns()
        timestamp = clock.send_event()

        # Artificial delay simulates network lag after event creation.
        delay_seconds = SENSOR_DELAY_BY_ID.get(sensor_id, 0)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        # After the delay, we can capture the local time again to show when the alert is actually sent.
        message = {
            "type": "alert",
            "sensor_id": sensor_id,
            "event": event,
            "location": "Room 101",
            "timestamp": timestamp,
            "detected_at_ns": detected_at_ns
        }

        client_socket.send(json.dumps(message).encode())    # Send the alert message to the monitoring server
        print(f"Sent alert: {message}")
        
def main():
    
    sensor_id = input("Enter sensor ID: ")
    
    client_socket = connect_to_monitoring_server()
    
    listen_thread = threading.Thread(       # Start a separate thread to listen for updates from the monitoring server while the main thread sends alerts
        target=listen_for_updates, 
        args=(client_socket,), 
        daemon=True
    )    
    
    listen_thread.start()
    
    send_alerts(client_socket, sensor_id)   # Start sending alerts to the monitoring server
    
if __name__ == "__main__":
    main()
