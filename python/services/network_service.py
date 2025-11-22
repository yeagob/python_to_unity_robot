import json
import zmq
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.command_model import CommandModel
from models.observation_model import ObservationModel


class NetworkService:
    """ZeroMQ client service for Unity communication."""

    DEFAULT_ADDRESS: str = "tcp://localhost:5555"
    DEFAULT_TIMEOUT_MILLISECONDS: int = 5000

    def __init__(self, server_address: str = DEFAULT_ADDRESS) -> None:
        self._server_address: str = server_address
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to Unity server."""
        return self._is_connected

    def connect(self) -> None:
        """Establish connection to Unity ZeroMQ server."""
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(self._server_address)
        self._socket.setsockopt(zmq.RCVTIMEO, self.DEFAULT_TIMEOUT_MILLISECONDS)
        self._is_connected = True

    def disconnect(self) -> None:
        """Close connection to Unity server."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None

        if self._context is not None:
            self._context.term()
            self._context = None

        self._is_connected = False

    def send_command(self, command: CommandModel) -> ObservationModel:
        """Send command and receive observation response."""
        if not self._is_connected:
            raise RuntimeError("Not connected to Unity server")

        command_dictionary: dict = command.to_dictionary()
        serialized_command: str = json.dumps(command_dictionary)

        self._socket.send_string(serialized_command)

        response_string: str = self._socket.recv_string()
        response_dictionary: dict = json.loads(response_string)

        return ObservationModel.from_dictionary(response_dictionary)

    def send_raw_command(self, command_dictionary: dict) -> dict:
        """Send raw dictionary command and receive raw response."""
        if not self._is_connected:
            raise RuntimeError("Not connected to Unity server")

        serialized_command: str = json.dumps(command_dictionary)
        self._socket.send_string(serialized_command)

        response_string: str = self._socket.recv_string()
        return json.loads(response_string)
