# REGISTER || STORE NAME-> ADDRESS
# LOOKUP || GET ADDRESS FROM NAME

import json, socket, threading
from config import NAMING_SERVER_BIND_HOST, NAMING_SERVER_PORT

HOST = NAMING_SERVER_BIND_HOST
PORT = NAMING_SERVER_PORT

registry = {}    # Dictionary to store name -> (host, port) mappings

# -----------------------------------------------------------------------------------------------------------------
# Handle client connections
# -------------------------------------------------------------------------------------------------------------------_

def handle_client(client_socket):
    try:
        data = client_socket.recv(1024).decode() # Receive data from the client
        
        if not data:
            return
        
        message = json.loads(data)               # Parse the JSON message
        msg_type = message.get("type")
        
        if msg_type == "register":
            name = message.get("name")
            host = message.get("host")
            port = message.get("port")
            
            registry[name] = (host, port)           # Store the name and address in the registry
            
            print(f"Registered {name} at {host}:{port}")
            
            response = {
                "status": "ok",
                "message": f"{name} registered successfully"
            }
            
            client_socket.send(json.dumps(response).encode())  # Send response to the client
        
        elif msg_type == "lookup":
            name = message.get("name")
            
            if name in registry:                # Check if the name exists in the registry
                host, port = registry[name]
                
                response = {            # Prepare the response with the address information
                    "status": "ok",
                    "host": host,
                    "port": port
                }    
            else:
                response = {
                    "status": "error",
                    "message": f"{name} not found"
                }
            
            client_socket.send(json.dumps(response).encode())  # Send response to the client
        
        print(f"Received message: {message}")   
    
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        client_socket.close()
        
# -----------------------------------------------------------------------------------------------------------------
# Main server loop
# ----------------------------------------------------------------------------------------------------------------- 
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      # Create a TCP socket  

    try:
        server.bind((HOST, PORT))       # Bind the server socket to the specified host and port
    except OSError as error:
        print(f"Failed to bind naming server to {HOST}:{PORT}: {error}")
        print("Try setting NAMING_SERVER_PORT to a different unused TCP port.")
        return

    server.listen() # Listen for incoming connections
    
    print(f"Naming server running on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()     # Accept incoming client connection
        
        print(f"Connection from {addr}")
        
        client_thread = threading.Thread(
            target=handle_client, 
            args=(client_socket,)
        )
        client_thread.start()     # Start a new thread to handle the client connection
        
if __name__ == "__main__":
    start_server()