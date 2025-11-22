# Communication Specification: ZeroMQ Python-Unity Protocol

**Version:** 2.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the ZeroMQ-based communication protocol between Python RL agents and the Unity robot simulation. The protocol uses the REQ-REP (Request-Reply) pattern with JSON payloads, ensuring Python controls the simulation step for deterministic reinforcement learning training.

---

## Requirements

### Requirement: COMM-001 - ZeroMQ Connection
The system SHALL use ZeroMQ REQ-REP pattern for communication between Python and Unity.

#### Scenario: Connection Establishment
- WHEN Python client creates a ZMQ REQ socket
- AND connects to `tcp://localhost:5555`
- THEN the Unity server SHALL accept the connection via ResponseSocket
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
The system SHALL use JSON for all message serialization.

#### Scenario: Command Message (Python → Unity)
- WHEN Python sends a command
- THEN the message SHALL be a JSON object containing:
  - `type`: Command type string ("STEP", "RESET", "CONFIG")
  - `actions`: Array of 4 float values (joint deltas) for STEP
  - `gripperClose`: Float 0-1 for gripper action
  - `simulationMode`: Boolean for CONFIG commands

#### Scenario: Observation Message (Unity → Python)
- WHEN Unity responds to a command
- THEN the message SHALL be a JSON object containing:
  - `jointAngles`: Array of 4 float values (degrees)
  - `tcpPosition`: Array of 3 float values (x, y, z meters)
  - `directionToTarget`: Array of 3 float values (normalized)
  - `distanceToTarget`: Float (meters)
  - `gripperState`: Float 0-1 (open percentage)
  - `isGripping`: Boolean
  - `laserHit`: Boolean
  - `laserDistance`: Float (meters)
  - `collision`: Boolean
  - `targetOrientation`: Array of 2 floats (one-hot)
  - `reset`: Boolean (true after RESET command)

#### Scenario: Error Response
- WHEN an error occurs during processing
- THEN Unity SHALL respond with:
  - `error`: String describing the error

---

### Requirement: COMM-003 - Command Types
The system SHALL support three command types for RL training.

#### Scenario: STEP Command
- WHEN Python sends `{"type": "STEP", "actions": [...], "gripperClose": 0.5}`
- THEN Unity SHALL:
  1. Apply delta angles to current joint positions
  2. Set gripper state (>0.5 = closed)
  3. Execute one physics step
  4. Build and return observation

#### Scenario: RESET Command
- WHEN Python sends `{"type": "RESET"}`
- THEN Unity SHALL:
  1. Reset robot to home position (all joints = 0)
  2. Open gripper
  3. Spawn new target at random position
  4. Clear collision flags
  5. Return observation with `reset: true`

#### Scenario: CONFIG Command
- WHEN Python sends `{"type": "CONFIG", "simulationMode": true}`
- THEN Unity SHALL switch to simulation mode (smooth interpolation)
- AND respond with `{"status": "ok"}`

---

### Requirement: COMM-004 - Threading Model
The system SHALL handle network I/O on a dedicated thread in Unity.

#### Scenario: Unity Server Threading
- WHEN the ZMQ server starts
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

### ZeroMQ Configuration

| Parameter | Python (Client) | Unity (Server) |
|-----------|-----------------|----------------|
| Socket Type | REQ | REP (ResponseSocket) |
| Address | tcp://localhost:5555 | tcp://*:5555 |
| Library | pyzmq | NetMQ |
| Timeout | 5000ms | 100ms poll |

### Message Examples

#### STEP Command
```json
{
  "type": "STEP",
  "actions": [5.0, -2.5, 3.0, 1.0],
  "gripperClose": 0.8
}
```

#### STEP Response
```json
{
  "jointAngles": [45.0, -30.0, 60.0, 15.0],
  "tcpPosition": [0.35, 0.25, 0.15],
  "directionToTarget": [0.57, 0.57, 0.57],
  "distanceToTarget": 0.12,
  "gripperState": 0.2,
  "isGripping": true,
  "laserHit": true,
  "laserDistance": 0.05,
  "collision": false,
  "targetOrientation": [1.0, 0.0],
  "reset": false
}
```

#### RESET Command
```json
{
  "type": "RESET"
}
```

#### CONFIG Command
```json
{
  "type": "CONFIG",
  "simulationMode": true
}
```

---

## Python Client Implementation

```python
import zmq
import json

class UnityConnection:
    def __init__(self, address="tcp://localhost:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(address)
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)

    def send_command(self, cmd: dict) -> dict:
        """Send command and wait for response (blocking)."""
        self.socket.send_string(json.dumps(cmd))
        response = self.socket.recv_string()
        return json.loads(response)

    def step(self, actions: list, gripper: float) -> dict:
        return self.send_command({
            "type": "STEP",
            "actions": actions,
            "gripperClose": gripper
        })

    def reset(self) -> dict:
        return self.send_command({"type": "RESET"})

    def set_mode(self, simulation: bool) -> dict:
        return self.send_command({
            "type": "CONFIG",
            "simulationMode": simulation
        })

    def close(self):
        self.socket.close()
        self.context.term()
```

---

## Unity Server Implementation

```csharp
using NetMQ;
using NetMQ.Sockets;
using System.Threading;
using System.Collections.Concurrent;

public class ZMQBridge
{
    private ResponseSocket server;
    private ConcurrentQueue<string> requests = new();
    private ConcurrentQueue<string> responses = new();
    private bool running;

    public void Start(string address = "tcp://*:5555")
    {
        running = true;
        new Thread(() => ServerLoop(address)).Start();
    }

    private void ServerLoop(string address)
    {
        AsyncIO.ForceDotNet.Force();
        using (server = new ResponseSocket())
        {
            server.Bind(address);
            while (running)
            {
                if (server.TryReceiveFrameString(
                    TimeSpan.FromMilliseconds(100), out string req))
                {
                    requests.Enqueue(req);

                    // Wait for main thread response
                    while (!responses.TryDequeue(out string resp))
                    {
                        Thread.Sleep(1);
                        if (!running) return;
                    }
                    server.SendFrame(resp);
                }
            }
        }
        NetMQConfig.Cleanup();
    }

    // Call from FixedUpdate
    public bool TryGetRequest(out string request)
        => requests.TryDequeue(out request);

    public void SendResponse(string response)
        => responses.Enqueue(response);

    public void Stop()
    {
        running = false;
    }
}
```

---

## Error Handling

| Error | Python Handling | Unity Handling |
|-------|-----------------|----------------|
| Connection failed | Retry with backoff | Log and continue |
| Timeout | Raise exception | N/A |
| Malformed JSON | Raise exception | Return error response |
| Unknown command | Log warning | Return error response |

---

## Performance Considerations

1. **Latency**: ZeroMQ optimized for low-latency messaging
2. **Throughput**: Single request per physics step (~50 req/sec)
3. **Memory**: Minimal allocation per message
4. **Threading**: Network I/O isolated from physics thread

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [robot-interface.md](robot-interface.md) - RL observation/action spaces
- [chess-system.md](chess-system.md) - Chess-specific extensions
