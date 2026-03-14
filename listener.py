"""
Listener starts by using ngrok tcp 4444 to create a tunnel to the local machine. 
It then listens for incoming connections on the specified port and handles them accordingly.
"""

import socket

#Define IP and port to listen on
IP = '0.0.0.0'
PORT = 4444


#Create a TCP socket and bind it to the specified IP and port
#
def start_listener():
