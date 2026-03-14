# Adv Topics in CS Project: Milestone 2 

## Goal: Creation of a functional Backdoor against windows/mac devices (prioritize windows)
1. User needs to open a port, and the target connects to it (target can be anyone on the internet - does not need to be in a local network)
  - Test connection not in a local network
2. The ability to use commands in terminal
  - Similar to the Milestone 1 project - use of shell commands (or the equivalent)
3. Counter some firewalls (use ngrok: reference - https://isc.sans.edu/diary/26866)
  - Reference the resource to create a c2 server using ngrok 
4. Get keyboard input
  - Function recording all keyboard inputs. 
5. Download and execute files
  - Function that downloads specified file to user’s computer or a public server
6. *Hide the presence - reopens when targets computer is rebooted
  - Using alias names
  - Erase logs
  - Steganography