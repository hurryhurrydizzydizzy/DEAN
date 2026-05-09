import json, time, random, socket, threading
from config import (
    NAMING_SERVER_HOST,
    NAMING_SERVER_PORT,
    SENSOR_DELAY_BY_ID,
)
from lamport import LamportClock

clock = LamportClock() # Initialize the Lamport clock

def get_monitoring_server():
    
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

def connect_to_monitoring_server():
    
    host, port = get_monitoring_server()
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    client.connect((host, port))
    
    print(f"Connected to monitoring server at {host}:{port}")
    
    return client

def listen_for_updates(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            
            if not data:
                break
            
            message = json.loads(data.decode())
            
            if message["type"] == "emergency_update":
                
                clock.receive_event(message["lamport_time"])
                
                print(f"EMERGENCY UPDATE: {message}")
                
        except Exception as e:
            print("Error:", e)
            break
        
def send_alerts(client_socket, sensor_id):
    while True:
        
        input("\nPress Enter to send an alert...")
        
        event = random.choice([
            "fire_detected",
            "smoke_detected",
            "heat_detected"
        ])

        # Capture when the event was detected and stamp with Lamport time immediately.
        detected_at_ns = time.time_ns()
        timestamp = clock.send_event()

        # Optional artificial delay simulates network lag after event creation.
        delay_seconds = SENSOR_DELAY_BY_ID.get(sensor_id, 0)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        message = {
            "type": "alert",
            "sensor_id": sensor_id,
            "event": event,
            "location": "Room 101",
            "timestamp": timestamp,
            "detected_at_ns": detected_at_ns
        }

        client_socket.send(json.dumps(message).encode())
        print(f"Sent alert: {message}")
        
def main():
    
    sensor_id = input("Enter sensor ID: ")
    
    client_socket = connect_to_monitoring_server()
    
    listen_thread = threading.Thread(
        target=listen_for_updates, 
        args=(client_socket,), 
        daemon=True
    )    
    
    listen_thread.start()
    
    send_alerts(client_socket, sensor_id)
    
if __name__ == "__main__":
    main()
