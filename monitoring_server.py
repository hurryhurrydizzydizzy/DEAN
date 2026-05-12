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
clients_lock = threading.Lock()
alerts_lock = threading.Lock()

def broadcast(message):     # Broadcast a message to all connected clients
    disconnected = []

    # Take a snapshot of clients while holding lock, then send without holding lock
    with clients_lock:
        snapshot = list(clients)

    payload = (json.dumps(message) + "\n").encode()

    for client in snapshot:
        try:
            client.send(payload)
        except Exception:
            disconnected.append(client)

    if disconnected:
        with clients_lock:
            for client in disconnected:
                if client in clients:
                    clients.remove(client)

def handle_sensor(client_socket):       # Handle incoming messages from a connected sensor
    # Use a file-like reader to get newline-delimited JSON messages
    f = client_socket.makefile('r')
    try:
        for line in f:      
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except Exception as e:
                print("JSON parse error:", e)
                continue

            if message.get("type") == "alert":
                sensor_timestamp = message["timestamp"]
                observed_time = clock.receive_event(sensor_timestamp)
                detected_at_ns = message.get("detected_at_ns")

                if detected_at_ns is not None:
                    detected_at_local = datetime.fromtimestamp(
                        detected_at_ns / 1_000_000_000
                    ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                else:
                    detected_at_local = "unknown"

                sensor_id = message["sensor_id"]

                print(f"\nAlert from {sensor_id} at server logical time {observed_time}")

                with alerts_lock:
                    alerts.append({
                        "sensor_id": sensor_id,
                        "sensor_timestamp": sensor_timestamp,
                        "observed_time": observed_time,
                        "detected_at_ns": detected_at_ns,
                        "timestamp": detected_at_local,
                    })

                    sorted_alerts = sorted(
                        list(alerts),
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
                    "first_detected_lamport": first_detector["sensor_timestamp"],
                    "first_detected_detected_at_ns": first_detector["detected_at_ns"],
                    "server_lamport": observed_time,
                }

                broadcast(response)
    except Exception as e:
        print("Error in handle_sensor:", e)
    finally:
        with clients_lock:
            if client_socket in clients:
                clients.remove(client_socket)
        try:
            client_socket.close()
        except Exception:
            pass
    
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
        with clients_lock:
            clients.append(client_socket) # Add the new client to the list of connected clients
        
        print(f"New connection from {addr}")
        
        thread = threading.Thread(      # Create a new thread to handle the sensor connection
            target=handle_sensor, 
            args=(client_socket,)
        ) 
        
        thread.start() # Start the thread to handle the sensor connection
        
if __name__ == "__main__":
    start_server() # Start the monitoring server