"""
Listener starts by using ngrok tcp 4444 to create a tunnel to the targets machine. 
It then listens for incoming connections on the specified port and handles them accordingly.

"""

import socket
import threading


# Define IP and port to listen on
IP = '0.0.0.0' # Host IP
PORT = 4444 # Port for conenction

# Dictionary to store connected clients
clients = {}

# Function to handle incoming client connections
# This function will be responsible for receiving data from the client and processing it as needed
# 

def handle_client(client_socket, client_address):



# Create a TCP server (listener) and bind it to the specified IP and port
# Identify all connected target cients in the dictionary for accessability
# Listen on port for client connections, then use a thread (from threading library) to handle them simultaneously
# All connected clients will be stored in a dictionary for easy access and management
# The handle_client function will be responsible for receiving data from the client and processing it as needed
# 
# 
def start_listener():
  # Creates a TCP server and bind it to IP and PORT
  listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  listener.bind((IP, PORT))
  listener.listen()

  # Prints connection
  print(f'[*] Server listening on {IP}:{PORT}')

  while True:
    sock, addr = listener.accept() # Accept client connection
    thread = threading.Thread(target = handle_client, args = (sock, addr)) # Create a new thread to handle the client connection
    thread.start() # Start the thread to handle the client connection 
    
    clients[addr] = sock # Store the client connection in the clients dictionary for easy access and management

    print(f'[*] Number of connected clients: {len(clients)}') # Print the number of connected clients







# Run starat_listener
if __name__ == "__main__":
  start_listener()



