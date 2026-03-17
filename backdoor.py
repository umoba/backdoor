"""
design@asij

"""

import socket


# If the free version of ngrok is used, the address will change each time ngrok is activated
address = "tcp://0.tcp.jp.ngrok.io:14091" # address
port = 4444 # port 


# Handles the connection of the client 
def connectClient():
  # Creates a socket object as clientSocket
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:

    # Connect to server
    clientSocket.connect((address, port))







if __name__ == "__main__":
  connectClient()
