"""
Unit Tests for backdoor.py
Rigorous testing with edge cases, mocking of external dependencies (socket, subprocess, etc.),
and coverage of core functions.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import socket
import base64
import threading
import time
import sys
import platform
import getpass
import subprocess

# Import the backdoor module (adjust path if needed)
import backdoor  


# These tests are designed to be run in an isolated environment and may require adjustments based on the actual implementation of backdoor.py.
class TestBackdoor(unittest.TestCase):


  # Reset global variables before each test
  def setUp(self):
    backdoor.keyBuffer = ""
    backdoor.loggerIsRunning = False
    backdoor.glbSock = None


  # Test the send_beacon function to ensure it sends the correct beacon string based on system information.
  @patch('backdoor.platform')
  @patch('backdoor.getpass')
  @patch('backdoor.os')
  def test_send_beacon(self, mock_os, mock_getpass, mock_platform):
    mock_platform.node.return_value = "testpc"
    mock_getpass.getuser.return_value = "testuser"
    mock_os.name = "testOS"
    mock_platform.system.return_value = "Windows"

    mock_sock = MagicMock()
    backdoor.send_beacon(mock_sock)

    expected = "BKDR_ALIVE|testpc|testuser|ADMIN|Windows"
    mock_sock.send.assert_called_once_with(expected.encode("utf-8"))

  # Test directory change command.
  def test_execute_command_cd(self):
    mock_sock = MagicMock()
    with patch('backdoor.os.chdir') as mock_chdir, \
      patch('backdoor.os.getcwd') as mock_getcwd:
      mock_getcwd.return_value = "/new/dir"
      backdoor.execute_command("cd /new/dir", mock_sock)

    mock_chdir.assert_called_once_with("/new/dir")
    mock_sock.send.assert_called_once()
    sent = mock_sock.send.call_args[0][0]
    self.assertIn(b"CMD_RES|", sent)


  # Test normal shell command execution (Windows path)
  @patch('backdoor.subprocess.run')
  
  def test_execute_command_shell(self, mock_run):
    mock_sock = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout = "dir output"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    backdoor.os.name = "nt"

    backdoor.execute_command("dir", mock_sock)

    mock_run.assert_called_once()
    mock_sock.send.assert_called_once()
    sent = mock_sock.send.call_args[0][0]
    self.assertIn(b"CMD_RES|", sent)

  # Test timeout handling
  def test_execute_command_timeout(self):
      mock_sock = MagicMock()
      with patch('backdoor.subprocess.run') as mock_run:
          mock_run.side_effect = subprocess.TimeoutExpired("cmd", 15)
          backdoor.execute_command("sleep 30", mock_sock)

      mock_sock.send.assert_called_once()
      sent = mock_sock.send.call_args[0][0]
      self.assertIn(b"CMD_ERR|Command timed out", sent)




if __name__ == '__main__':
  unittest.main(verbosity=2)

  