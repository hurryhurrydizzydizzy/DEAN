import json, socket, threading
from datetime import datetime
from config import (
    MONITORING_SERVER_ADVERTISE_HOST,
    MONITORING_SERVER_BIND_HOST,
    MONITORING_SERVER_PORT,
    NAMING_SERVER_HOST,
    NAMING_SERVER_PORT,
)
from lamport import LamportClock

HOST = MONITORING_SERVER_BIND_HOST
PORT = MONITORING_SERVER_PORT

clock = LamportClock() # Initialize the Lamport clock
clients = []    # List to keep track of connected clients
alerts = []     # List to store received alerts for ordering purposes

def broadcast(message):     # Broadcast a message to all connected clients
    disconnected = []

    for client in clients:
        try:
            client.send(json.dumps(message).encode())   
        except:
            disconnected.append(client)

    for client in disconnected:
        clients.remove(client)

def handle_sensor(client_socket):       # Handle incoming messages from a connected sensor
    while True:
        try:
            data = client_socket.recv(1024).decode()    # Receive data from the sensor
            if not data:
                break

            message = json.loads(data)  # Parse the received data as JSON

            if message["type"] == "alert":

                sensor_timestamp = message["timestamp"]                    # Get the sensor's logical timestamp from the message      
                observed_time = clock.receive_event(sensor_timestamp)      # Update the server's Lamport clock based on the received timestamp
                detected_at_ns = message.get("detected_at_ns")             # Get the detected_at timestamp in nanoseconds from the message (if available)

                # Convert to readable format for logging (if detected_at_ns is available)
                if detected_at_ns is not None:                             
                    detected_at_local = datetime.fromtimestamp(
                        detected_at_ns / 1_000_000_000
                    ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                else:
                    detected_at_local = "unknown"

                sensor_id = message["sensor_id"]    
                
                print(f"\nAlert from {sensor_id} at server logical time {observed_time}")
                
                alerts.append({
                    "sensor_id": sensor_id,
                    "sensor_timestamp": sensor_timestamp,
                    "observed_time": observed_time,
                    "detected_at_ns": detected_at_ns,
                    "timestamp": detected_at_local,
                })

                sorted_alerts = sorted(     # Sort the alerts based on Lamport timestamp, detected_at timestamp, and sensor ID for tie-breaking
                    alerts,
                    key=lambda x: (
                        x["sensor_timestamp"],
                        x["detected_at_ns"] if x["detected_at_ns"] is not None else float("inf"),
                        x["sensor_id"],
                    ),
                )
                
                first_detector = sorted_alerts[0]
                
                print(" === LOGICAL EVENT ORDER ===")
                for alert in sorted_alerts:
                    print(
                        f"Sensor {alert['sensor_id']} | timestamp={alert['timestamp']} | lamport={alert['sensor_timestamp']}"
                    )
                
                print(
                    f"\nFirst detected by sensor {first_detector['sensor_id']} "
                    f"(lamport={first_detector['sensor_timestamp']})"
                )

                response = {
                    "type": "emergency_update",
                    "status": "confirmed_fire",
                    "first_detected_by": first_detector["sensor_id"],
                    "lamport_time": observed_time
                }

                broadcast(response)     # Broadcast the emergency update to all connected clients

        except Exception as e:
            print("Error:", e)
            break

    if client_socket in clients:        # Remove the client from the list of connected clients if it disconnects
        clients.remove(client_socket)

    client_socket.close()           # Close the connection to the sensor when done
    
def start_server():
    global clients
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket
    server.bind((HOST, PORT)) # Bind the socket to the specified host and port
    server.listen() # Listen for incoming connections
    
    print(f"Monitoring server started on {HOST}:{PORT}")
    
    try:
        ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket to connect to the naming server
        ns.connect((NAMING_SERVER_HOST, NAMING_SERVER_PORT)) # Connect to the naming server
        
        register_msg = {
            "type": "register",
            "name": "monitoring.server.main",
            "host": MONITORING_SERVER_ADVERTISE_HOST,
            "port": PORT
        }
        
        ns.send(json.dumps(register_msg).encode()) # Register with the naming server
        ns.close() # Close the connection to the naming server
        
    except Exception as e:
        print(f"Error registering with naming server: {e}")
        
    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket) # Add the new client to the list of connected clients
        
        print(f"New connection from {addr}")
        
        thread = threading.Thread(      # Create a new thread to handle the sensor connection
            target=handle_sensor, 
            args=(client_socket,)
        ) 
        
        thread.start() # Start the thread to handle the sensor connection
        
if __name__ == "__main__":
    start_server() # Start the monitoring server