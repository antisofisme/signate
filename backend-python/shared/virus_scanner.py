"""
ClamAV Virus Scanner Integration
Scans uploaded files for viruses before saving to storage
"""

import os
import socket
import struct
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class VirusScanner:
    """
    ClamAV virus scanner integration

    Connects to ClamAV daemon via TCP socket to scan files
    """

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize virus scanner

        Args:
            host: ClamAV daemon host (default: from env CLAMAV_HOST or 'localhost')
            port: ClamAV daemon port (default: from env CLAMAV_PORT or 3310)
        """
        self.host = host or os.getenv('CLAMAV_HOST', 'localhost')
        self.port = int(port or os.getenv('CLAMAV_PORT', 3310))
        self.timeout = int(os.getenv('CLAMAV_TIMEOUT', '30'))  # Default: 30 seconds

    def scan_file(self, file_path) -> Tuple[bool, str]:
        """
        Scan file for viruses using ClamAV

        Args:
            file_path: Path to file to scan (Path object or string)

        Returns:
            Tuple of (is_clean, result_message)
            - is_clean: True if file is safe, False if virus detected
            - result_message: Scan result or virus name

        Raises:
            ConnectionError: If cannot connect to ClamAV
            TimeoutError: If scan times out
        """
        try:
            # Convert string to Path if needed
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Connect to ClamAV daemon
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)

                try:
                    sock.connect((self.host, self.port))
                except (ConnectionRefusedError, OSError) as e:
                    logger.error(f"Cannot connect to ClamAV at {self.host}:{self.port}: {e}")
                    raise ConnectionError(
                        f"ClamAV service unavailable. Please ensure ClamAV is running."
                    )

                # Send INSTREAM command
                sock.sendall(b'zINSTREAM\0')

                # Stream file data to ClamAV
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break

                        # Send chunk size (4 bytes, network byte order)
                        size = struct.pack(b'!L', len(chunk))
                        sock.sendall(size + chunk)

                # Send zero-length chunk to indicate end of file
                sock.sendall(struct.pack(b'!L', 0))

                # Receive scan result
                result = b''
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    result += chunk

                # Parse result
                response = result.decode('utf-8', errors='ignore').strip()

                logger.info(f"ClamAV scan result for {file_path.name}: {response}")

                # Check result
                if 'OK' in response:
                    return (True, "File is clean")
                elif 'FOUND' in response:
                    # Extract virus name
                    virus_name = response.split(':')[1].strip().replace(' FOUND', '')
                    logger.warning(f"Virus detected in {file_path.name}: {virus_name}")
                    return (False, f"Virus detected: {virus_name}")
                else:
                    # Unknown response
                    logger.error(f"Unknown ClamAV response: {response}")
                    return (False, f"Scan error: {response}")

        except socket.timeout:
            logger.error(f"ClamAV scan timeout for {file_path.name}")
            raise TimeoutError(f"Virus scan timed out after {self.timeout} seconds")

        except Exception as e:
            logger.error(f"Error scanning file {file_path.name}: {e}")
            raise

    def ping(self) -> bool:
        """
        Check if ClamAV is available

        Returns:
            True if ClamAV is reachable, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self.host, self.port))
                sock.sendall(b'zPING\0')
                response = sock.recv(4096)

                return b'PONG' in response

        except Exception as e:
            logger.error(f"ClamAV ping failed: {e}")
            return False

    def get_version(self) -> str:
        """
        Get ClamAV version

        Returns:
            Version string or error message
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self.host, self.port))
                sock.sendall(b'zVERSION\0')
                response = sock.recv(4096)

                return response.decode('utf-8', errors='ignore').strip()

        except Exception as e:
            return f"Error: {e}"


# Global scanner instance
_scanner = None


def get_virus_scanner() -> VirusScanner:
    """
    Get global virus scanner instance

    Returns:
        VirusScanner instance
    """
    global _scanner
    if _scanner is None:
        _scanner = VirusScanner()
    return _scanner
