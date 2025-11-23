import json
import socket
import struct
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.command_model import CommandModel
from models.observation_model import ObservationModel


class NetworkService:
    """TCP socket client service for Unity communication.

    Uses length-prefixed JSON messages over TCP for reliable,
    synchronous request-reply communication with Unity.
    """

    DEFAULT_HOST: str = "localhost"
    DEFAULT_PORT: int = 5555
    DEFAULT_TIMEOUT_SECONDS: float = 5.0

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT
    ) -> None:
        self._host: str = host
        self._port: int = port
        self._socket: Optional[socket.socket] = None
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to Unity server."""
        return self._is_connected

    def connect(self) -> None:
        """Establish TCP connection to Unity server."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.DEFAULT_TIMEOUT_SECONDS)
        self._socket.connect((self._host, self._port))
        self._is_connected = True

    def disconnect(self) -> None:
        """Close TCP connection to Unity server."""
        if self._socket is not None:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None

        self._is_connected = False

    def send_command(self, command: CommandModel) -> ObservationModel:
        """Send command and receive observation response."""
        if not self._is_connected:
            raise RuntimeError("Not connected to Unity server")

        command_dictionary: dict = command.to_dictionary()
        response_dictionary: dict = self._send_and_receive(command_dictionary)

        return ObservationModel.from_dictionary(response_dictionary)

    def send_raw_command(self, command_dictionary: dict) -> dict:
        """Send raw dictionary command and receive raw response."""
        if not self._is_connected:
            raise RuntimeError("Not connected to Unity server")

        return self._send_and_receive(command_dictionary)

    def _send_and_receive(self, command: dict) -> dict:
        """Send length-prefixed JSON command and receive response."""
        # Serialize command to JSON bytes
        json_bytes: bytes = json.dumps(command).encode("utf-8")

        # Create length prefix (4 bytes, big-endian)
        length_prefix: bytes = struct.pack(">I", len(json_bytes))

        # Send length prefix + message
        self._socket.sendall(length_prefix + json_bytes)

        # Receive response length prefix
        length_data: bytes = self._receive_exact(4)
        message_length: int = struct.unpack(">I", length_data)[0]

        # Receive response message body
        response_bytes: bytes = self._receive_exact(message_length)

        return json.loads(response_bytes.decode("utf-8"))

    def _receive_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data: bytes = b""

        while len(data) < num_bytes:
            chunk: bytes = self._socket.recv(num_bytes - len(data))

            if not chunk:
                raise ConnectionError("Connection closed by Unity server")

            data += chunk

        return data
