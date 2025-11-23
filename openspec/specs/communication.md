# Communication Specification: TCP Socket Python-Unity Protocol

**Version:** 3.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the TCP Socket-based communication protocol between Python RL agents and the Unity robot simulation. The protocol uses a simple synchronous TCP connection with JSON payloads, ensuring Python controls the simulation step for deterministic reinforcement learning training.

**Note:** This replaces the previous ZeroMQ/NetMQ implementation due to compatibility issues with Unity (see: https://github.com/zeromq/netmq/issues/631).

---

## Requirements

### Requirement: COMM-001 - TCP Socket Connection
The system SHALL use standard TCP sockets for communication between Python and Unity.

#### Scenario: Connection Establishment
- WHEN Python client creates a TCP socket
- AND connects to `localhost:5555`
- THEN the Unity server SHALL accept the connection via TcpListener
- AND be ready to process requests

#### Scenario: Request-Reply Cycle
- WHEN Python sends a request message
- THEN Python SHALL block until Unity responds
- AND Unity SHALL process exactly one request before responding
- AND this SHALL ensure deterministic simulation stepping

#### Scenario: Connection Timeout
- WHEN no response is received within 5 seconds
- THEN Python SHALL raise a timeout exception
- AND the client MAY attempt reconnection

---

### Requirement: COMM-002 - Message Format
The system SHALL use length-prefixed JSON for all message serialization.

#### Scenario: Message Framing
- WHEN a message is sent
- THEN it SHALL be prefixed with a 4-byte big-endian integer (message length)
- AND followed by UTF-8 encoded JSON
- AND this SHALL prevent message fragmentation issues

#### Scenario: Command Message (Python → Unity)
- WHEN Python sends a command
- THEN the message SHALL be a JSON object containing:
  - `Type`: Command type string ("STEP", "RESET", "CONFIG")
  - `Actions`: Array of 5 float values (joint deltas for axes 1-5) for STEP
  - `GripperCloseValue`: Float 0-1 for gripper action
  - `Axis6Orientation`: Float (0=vertical, 1=horizontal) for discrete axis 6
  - `SimulationModeEnabled`: Boolean for CONFIG commands

#### Scenario: Observation Message (Unity → Python)
- WHEN Unity responds to a command
- THEN the message SHALL be a JSON object containing:
  - `JointAngles`: Array of 6 float values (degrees)
  - `ToolCenterPointPosition`: Array of 3 float values (x, y, z meters)
  - `DirectionToTarget`: Array of 3 float values (normalized)
  - `DistanceToTarget`: Float (meters)
  - `GripperState`: Float 0-1 (open percentage)
  - `IsGrippingObject`: Boolean
  - `LaserSensorHit`: Boolean
  - `LaserSensorDistance`: Float (meters)
  - `CollisionDetected`: Boolean
  - `TargetOrientationOneHot`: Array of 2 floats (one-hot)
  - `IsResetFrame`: Boolean (true after RESET command)

#### Scenario: Error Response
- WHEN an error occurs during processing
- THEN Unity SHALL respond with:
  - `error`: String describing the error

---

### Requirement: COMM-003 - Command Types
The system SHALL support three command types for RL training.

#### Scenario: STEP Command
- WHEN Python sends `{"Type": "STEP", "Actions": [...], "GripperCloseValue": 0.5}`
- THEN Unity SHALL:
  1. Apply delta angles to current joint positions (axes 1-5)
  2. Set axis 6 orientation (discrete: 0° or 90°)
  3. Set gripper state (>0.5 = closed)
  4. Execute one physics step
  5. Build and return observation

#### Scenario: RESET Command
- WHEN Python sends `{"Type": "RESET"}`
- THEN Unity SHALL:
  1. Reset robot to home position (all joints = 0)
  2. Open gripper
  3. Spawn new target at random position
  4. Clear collision flags
  5. Return observation with `IsResetFrame: true`

#### Scenario: CONFIG Command
- WHEN Python sends `{"Type": "CONFIG", "SimulationModeEnabled": true}`
- THEN Unity SHALL switch to simulation mode (smooth interpolation)
- AND respond with `{"status": "ok"}`

---

### Requirement: COMM-004 - Threading Model
The system SHALL handle network I/O on a dedicated thread in Unity.

#### Scenario: Unity Server Threading
- WHEN the TCP server starts
- THEN network I/O SHALL run on a background thread
- AND requests SHALL be queued via ConcurrentQueue
- AND processing SHALL occur in FixedUpdate (main thread)
- AND responses SHALL be queued back to the network thread

#### Scenario: Physics Synchronization
- WHEN a STEP command is processed
- THEN it SHALL be executed in FixedUpdate
- AND the response SHALL reflect the state after physics step
- AND Time.fixedDeltaTime SHALL be 0.02f (50Hz)

---

### Requirement: COMM-005 - Determinism
The system SHALL guarantee deterministic simulation for RL training.

#### Scenario: Blocking Communication
- WHEN Python calls `socket.recv()`
- THEN Python SHALL block until Unity responds
- AND this SHALL ensure one action per physics step
- AND training SHALL be reproducible with same seed

#### Scenario: Physics Timing
- WHEN Unity processes requests
- THEN exactly one physics step SHALL occur per STEP command
- AND Time.fixedDeltaTime SHALL remain constant

---

## Protocol Details

### TCP Socket Configuration

| Parameter | Python (Client) | Unity (Server) |
|-----------|-----------------|----------------|
| Socket Type | TCP Client | TcpListener |
| Address | localhost:5555 | 0.0.0.0:5555 |
| Library | socket (stdlib) | System.Net.Sockets |
| Timeout | 5000ms | Blocking with flag |

### Message Framing

```
+----------------+------------------+
| Length (4 bytes)| JSON Payload     |
| Big-endian int | UTF-8 encoded    |
+----------------+------------------+
```

### Message Examples

#### STEP Command
```json
{
  "Type": "STEP",
  "Actions": [5.0, -2.5, 3.0, 1.0, -1.0],
  "Axis6Orientation": 0.0,
  "GripperCloseValue": 0.8
}
```

#### STEP Response
```json
{
  "JointAngles": [45.0, -30.0, 60.0, 15.0, 10.0, 0.0],
  "ToolCenterPointPosition": [0.35, 0.25, 0.15],
  "DirectionToTarget": [0.57, 0.57, 0.57],
  "DistanceToTarget": 0.12,
  "GripperState": 0.2,
  "IsGrippingObject": true,
  "LaserSensorHit": true,
  "LaserSensorDistance": 0.05,
  "CollisionDetected": false,
  "TargetOrientationOneHot": [1.0, 0.0],
  "IsResetFrame": false
}
```

#### RESET Command
```json
{
  "Type": "RESET"
}
```

#### CONFIG Command
```json
{
  "Type": "CONFIG",
  "SimulationModeEnabled": true
}
```

---

## Python Client Implementation

```python
import socket
import struct
import json
from typing import Optional


class TcpNetworkService:
    """TCP socket client for Unity communication."""

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
        return self._is_connected

    def connect(self) -> None:
        """Establish TCP connection to Unity server."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.DEFAULT_TIMEOUT_SECONDS)
        self._socket.connect((self._host, self._port))
        self._is_connected = True

    def disconnect(self) -> None:
        """Close TCP connection."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self._is_connected = False

    def send_command(self, command: dict) -> dict:
        """Send command and receive response (blocking)."""
        if not self._is_connected:
            raise RuntimeError("Not connected to Unity server")

        # Serialize and send with length prefix
        json_bytes = json.dumps(command).encode("utf-8")
        length_prefix = struct.pack(">I", len(json_bytes))
        self._socket.sendall(length_prefix + json_bytes)

        # Receive length prefix
        length_data = self._receive_exact(4)
        message_length = struct.unpack(">I", length_data)[0]

        # Receive message body
        response_bytes = self._receive_exact(message_length)
        return json.loads(response_bytes.decode("utf-8"))

    def _receive_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data = b""
        while len(data) < num_bytes:
            chunk = self._socket.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed by server")
            data += chunk
        return data
```

---

## Unity Server Implementation

```csharp
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;
using UnityEngine;

public sealed class TcpNetworkService : INetworkService
{
    private TcpListener _listener;
    private TcpClient _client;
    private NetworkStream _stream;
    private Thread _networkThread;
    private ConcurrentQueue<string> _incomingRequests;
    private ConcurrentQueue<string> _outgoingResponses;
    private volatile bool _isRunning;
    private int _port;

    public bool IsConnected => _client?.Connected ?? false;

    public TcpNetworkService()
    {
        _incomingRequests = new ConcurrentQueue<string>();
        _outgoingResponses = new ConcurrentQueue<string>();
    }

    public void Initialize(int port)
    {
        _port = port;
        _isRunning = true;
        _networkThread = new Thread(NetworkLoop) { IsBackground = true };
        _networkThread.Start();
        Debug.Log($"TcpNetworkService: Listening on port {port}");
    }

    private void NetworkLoop()
    {
        _listener = new TcpListener(IPAddress.Any, _port);
        _listener.Start();

        while (_isRunning)
        {
            try
            {
                if (_client == null || !_client.Connected)
                {
                    if (_listener.Pending())
                    {
                        _client = _listener.AcceptTcpClient();
                        _stream = _client.GetStream();
                        Debug.Log("TcpNetworkService: Client connected");
                    }
                    else
                    {
                        Thread.Sleep(10);
                        continue;
                    }
                }

                if (_stream.DataAvailable)
                {
                    string request = ReceiveMessage();
                    _incomingRequests.Enqueue(request);

                    // Wait for response from main thread
                    while (!_outgoingResponses.TryDequeue(out string response))
                    {
                        Thread.Sleep(1);
                        if (!_isRunning) return;
                    }
                    SendMessage(response);
                }
                else
                {
                    Thread.Sleep(1);
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"TcpNetworkService: {ex.Message}");
                _client?.Close();
                _client = null;
            }
        }

        _listener?.Stop();
    }

    private string ReceiveMessage()
    {
        byte[] lengthBuffer = new byte[4];
        _stream.Read(lengthBuffer, 0, 4);
        if (BitConverter.IsLittleEndian)
            Array.Reverse(lengthBuffer);
        int length = BitConverter.ToInt32(lengthBuffer, 0);

        byte[] messageBuffer = new byte[length];
        int bytesRead = 0;
        while (bytesRead < length)
        {
            bytesRead += _stream.Read(messageBuffer, bytesRead, length - bytesRead);
        }
        return Encoding.UTF8.GetString(messageBuffer);
    }

    private void SendMessage(string message)
    {
        byte[] messageBytes = Encoding.UTF8.GetBytes(message);
        byte[] lengthBytes = BitConverter.GetBytes(messageBytes.Length);
        if (BitConverter.IsLittleEndian)
            Array.Reverse(lengthBytes);

        _stream.Write(lengthBytes, 0, 4);
        _stream.Write(messageBytes, 0, messageBytes.Length);
        _stream.Flush();
    }

    public bool TryReceiveCommand(out CommandModel command)
    {
        command = null;
        if (_incomingRequests.TryDequeue(out string json))
        {
            command = JsonUtility.FromJson<CommandModel>(json);
            return true;
        }
        return false;
    }

    public void SendObservation(ObservationModel obs)
    {
        _outgoingResponses.Enqueue(JsonUtility.ToJson(obs));
    }

    public void SendResponse(string json)
    {
        _outgoingResponses.Enqueue(json);
    }

    public void Shutdown()
    {
        _isRunning = false;
        _client?.Close();
        _listener?.Stop();
        _networkThread?.Join(1000);
        Debug.Log("TcpNetworkService: Shutdown complete");
    }
}
```

---

## Error Handling

| Error | Python Handling | Unity Handling |
|-------|-----------------|----------------|
| Connection failed | Retry with backoff | Log and await |
| Timeout | Raise exception | N/A |
| Malformed JSON | Raise exception | Return error response |
| Connection lost | Reconnect | Accept new connection |

---

## Migration from ZeroMQ

### Why TCP Sockets?

1. **No external dependencies** - Uses standard library on both sides
2. **Unity compatibility** - No NetMQ issues with debugger or context cleanup
3. **Simpler debugging** - Standard tools work (netcat, wireshark)
4. **Same semantics** - Still synchronous request-reply pattern

### Changes Required

| Component | ZeroMQ | TCP Sockets |
|-----------|--------|-------------|
| Python import | `import zmq` | `import socket` |
| Unity package | NetMQ NuGet | System.Net.Sockets |
| Message format | Raw string | Length-prefixed |
| Field naming | camelCase | PascalCase (JsonUtility) |

---

## Performance Considerations

1. **Latency**: TCP adds ~0.1ms vs ZMQ, negligible for 50Hz
2. **Throughput**: Single request per physics step (~50 req/sec)
3. **Memory**: Minimal allocation per message
4. **Reliability**: TCP guarantees delivery and ordering

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [robot-interface.md](robot-interface.md) - RL observation/action spaces
- [chess-system.md](chess-system.md) - Chess-specific extensions
