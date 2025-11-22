# Communication Specification: Python-Unity Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the communication protocol between Python-based LLM agents and the Unity robot simulation. The protocol enables bidirectional communication for robot control, state queries, and event notifications.

---

## Requirements

### Requirement: COMM-001 - Connection Establishment
The system SHALL support reliable connection establishment between Python clients and the Unity server.

#### Scenario: TCP Connection
- WHEN a Python client initiates a connection to the Unity server
- THEN the server SHALL accept the connection on the configured port
- AND respond with a connection acknowledgment message
- AND the connection SHALL remain open for subsequent commands

#### Scenario: Connection Timeout
- WHEN a connection attempt exceeds the timeout period (30 seconds)
- THEN the client SHALL receive a timeout error
- AND retry logic MAY be implemented by the client

#### Scenario: Multiple Clients
- WHEN multiple Python clients attempt to connect
- THEN the server SHALL handle connections based on configuration
- AND either accept multiple clients or reject additional connections with appropriate error

---

### Requirement: COMM-002 - Message Format
The system SHALL use a standardized message format for all communications.

#### Scenario: Request Message
- WHEN a client sends a request
- THEN the message SHALL be formatted as JSON
- AND include: message_id, command, parameters, timestamp

#### Scenario: Response Message
- WHEN the server responds to a request
- THEN the message SHALL be formatted as JSON
- AND include: message_id (matching request), status, data, error, timestamp

#### Scenario: Event Message
- WHEN the server emits an event
- THEN the message SHALL be formatted as JSON
- AND include: event_type, data, timestamp

---

### Requirement: COMM-003 - Message Framing
The system SHALL implement message framing to handle TCP stream segmentation.

#### Scenario: Length-Prefixed Messages
- WHEN sending a message
- THEN the message SHALL be prefixed with a 4-byte big-endian length field
- AND the receiver SHALL read the length first, then the message body

#### Scenario: Large Messages
- WHEN a message exceeds the buffer size
- THEN the receiver SHALL accumulate data until the complete message is received
- AND process the message only when complete

---

### Requirement: COMM-004 - Request-Response Pattern
The system SHALL implement synchronous request-response communication.

#### Scenario: Command Execution
- WHEN a client sends a command request
- THEN the server SHALL process the command
- AND return a response before the client timeout expires
- AND the response SHALL reference the original request ID

#### Scenario: Long-Running Commands
- WHEN a command takes extended time (e.g., robot movement)
- THEN the server SHALL return an immediate acknowledgment
- AND send a completion event when the operation finishes
- AND support status queries during execution

---

### Requirement: COMM-005 - Event Streaming
The system SHALL support asynchronous event notifications from server to client.

#### Scenario: State Change Events
- WHEN the robot state changes
- THEN the server SHALL emit an event notification
- AND include relevant state information in the event data

#### Scenario: Error Events
- WHEN an error occurs during operation
- THEN the server SHALL emit an error event
- AND include error code, message, and context

#### Scenario: Event Subscription
- WHEN a client subscribes to specific event types
- THEN the server SHALL only send subscribed events to that client
- AND support dynamic subscription changes

---

### Requirement: COMM-006 - Error Handling
The system SHALL implement robust error handling for communication failures.

#### Scenario: Malformed Message
- WHEN a malformed JSON message is received
- THEN the receiver SHALL respond with a parse error
- AND continue operating (not crash)

#### Scenario: Connection Lost
- WHEN the TCP connection is unexpectedly closed
- THEN both parties SHALL detect the disconnection
- AND clean up associated resources
- AND the Unity simulation SHALL continue operating safely

#### Scenario: Reconnection
- WHEN a client reconnects after disconnection
- THEN the server SHALL accept the new connection
- AND reset any client-specific state

---

### Requirement: COMM-007 - Security
The system SHALL implement basic security measures for the communication channel.

#### Scenario: Local Connection Only
- WHEN the server starts
- THEN it SHALL by default only accept connections from localhost
- AND external connections SHALL require explicit configuration

#### Scenario: Authentication (Optional)
- WHEN authentication is enabled
- THEN clients SHALL provide valid credentials on connection
- AND unauthorized clients SHALL be rejected

---

## Protocol Details

### Connection Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| Host | 127.0.0.1 | Server bind address |
| Port | 5555 | Server listen port |
| Timeout | 30000ms | Connection/request timeout |
| Buffer Size | 65536 bytes | Message buffer size |
| Max Message Size | 1MB | Maximum allowed message |

---

### Message Structure

#### Request Format
```json
{
  "id": "uuid-string",
  "type": "request",
  "command": "move_to_position",
  "params": {
    "x": 0.5,
    "y": 0.3,
    "z": 0.2
  },
  "timestamp": 1732300800000
}
```

#### Response Format
```json
{
  "id": "uuid-string",
  "type": "response",
  "status": "success",
  "data": {
    "position": {"x": 0.5, "y": 0.3, "z": 0.2},
    "duration_ms": 1500
  },
  "error": null,
  "timestamp": 1732300801500
}
```

#### Event Format
```json
{
  "type": "event",
  "event": "motion_complete",
  "data": {
    "position": {"x": 0.5, "y": 0.3, "z": 0.2},
    "success": true
  },
  "timestamp": 1732300801500
}
```

---

### Framing Protocol

```
+------------------+------------------+
| Length (4 bytes) | JSON Message     |
| Big-endian uint  | UTF-8 encoded    |
+------------------+------------------+
```

Example (Python):
```python
import struct
import json

def send_message(sock, message):
    data = json.dumps(message).encode('utf-8')
    length = struct.pack('>I', len(data))
    sock.sendall(length + data)

def receive_message(sock):
    length_data = sock.recv(4)
    length = struct.unpack('>I', length_data)[0]
    data = sock.recv(length)
    return json.loads(data.decode('utf-8'))
```

---

### Event Types

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `connected` | Client connected | client_id |
| `motion_started` | Robot started moving | target, speed |
| `motion_complete` | Robot reached target | position, success |
| `collision_warning` | Potential collision detected | location, severity |
| `gripper_state_changed` | Gripper opened/closed | position, gripping |
| `error` | Error occurred | code, message |
| `game_state_changed` | Chess game state changed | fen, last_move |

---

### Status Codes

| Status | Description |
|--------|-------------|
| `success` | Operation completed successfully |
| `error` | Operation failed |
| `pending` | Operation in progress |
| `queued` | Command queued for execution |

---

## Python Client Example

```python
import socket
import struct
import json
import uuid
from typing import Optional, Dict, Any

class RobotClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 5555):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Establish connection to Unity server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30.0)
        self.sock.connect((self.host, self.port))
        return True

    def disconnect(self):
        """Close the connection."""
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict:
        """Send a command and wait for response."""
        message = {
            'id': str(uuid.uuid4()),
            'type': 'request',
            'command': command,
            'params': params or {},
            'timestamp': int(time.time() * 1000)
        }

        # Send
        data = json.dumps(message).encode('utf-8')
        self.sock.sendall(struct.pack('>I', len(data)) + data)

        # Receive
        length_data = self.sock.recv(4)
        length = struct.unpack('>I', length_data)[0]
        response_data = self.sock.recv(length)

        return json.loads(response_data.decode('utf-8'))

    # Convenience methods
    def move_to(self, x: float, y: float, z: float) -> Dict:
        return self.send_command('move_to_position', {'x': x, 'y': y, 'z': z})

    def grip(self) -> Dict:
        return self.send_command('grip')

    def release(self) -> Dict:
        return self.send_command('release')

    def get_position(self) -> Dict:
        return self.send_command('get_position')
```

---

## Unity Server Considerations

The Unity server implementation SHALL:

1. Run network operations on a separate thread to avoid blocking the main Unity thread
2. Use thread-safe queues for passing commands to the simulation
3. Implement proper synchronization for shared state
4. Handle client disconnection gracefully
5. Log all communication for debugging purposes

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [robot-interface.md](robot-interface.md) - Robot command reference
- [chess-system.md](chess-system.md) - Chess-specific commands
