# Technical Design: Python-Unity Communication Server

**Change ID:** 001
**Date:** 2025-11-22

## Architecture Overview

```
┌─────────────────┐          TCP/IP           ┌─────────────────┐
│                 │  ───────────────────────▶ │                 │
│  Python Client  │      Port 5555            │  Unity Server   │
│  (LLM Agent)    │  ◀─────────────────────── │  (Simulation)   │
│                 │    JSON Messages          │                 │
└─────────────────┘                           └─────────────────┘
        │                                             │
        │                                             │
        ▼                                             ▼
┌─────────────────┐                           ┌─────────────────┐
│ robot_client.py │                           │ NetworkServer   │
│ - connect()     │                           │ - Listen Thread │
│ - send_command()│                           │ - Message Queue │
│ - events        │                           │ - Handlers      │
└─────────────────┘                           └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │ realvirtual     │
                                              │ - Drive         │
                                              │ - Kinematic     │
                                              │ - Gripper       │
                                              └─────────────────┘
```

## Unity Server Design

### Class Structure

```csharp
// Main server component
public class NetworkServer : MonoBehaviour
{
    [SerializeField] private int port = 5555;
    [SerializeField] private RobotController robotController;

    private TcpListener listener;
    private TcpClient client;
    private Thread listenerThread;
    private ConcurrentQueue<Message> incomingQueue;
    private ConcurrentQueue<Message> outgoingQueue;
}

// Message types
public class Message
{
    public string id;
    public string type;  // "request", "response", "event"
    public string command;
    public Dictionary<string, object> parameters;
    public long timestamp;
}

// Command handler interface
public interface ICommandHandler
{
    string CommandName { get; }
    Message Handle(Message request);
}

// Robot controller wrapper
public class RobotController : MonoBehaviour
{
    public Kinematic kinematic;
    public Gripper gripper;
    public Drive[] drives;

    public void MoveToPosition(Vector3 position);
    public void Grip();
    public void Release();
    public Vector3 GetPosition();
}
```

### Threading Model

```
┌─────────────────────────────────────────────────────────────┐
│                     NETWORK THREAD                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ TCP Listen  │───▶│ Read Frame  │───▶│ Parse JSON  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                               │             │
│                                               ▼             │
│                                    ┌──────────────────┐    │
│                                    │ Incoming Queue   │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MAIN UNITY THREAD                       │
│                                                             │
│  Update() {                                                 │
│    while (incomingQueue.TryDequeue(out msg))               │
│    {                                                        │
│      response = ProcessCommand(msg);                        │
│      outgoingQueue.Enqueue(response);                      │
│    }                                                        │
│  }                                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SEND THREAD                             │
│  ┌─────────────────┐    ┌─────────────┐    ┌────────────┐  │
│  │ Outgoing Queue  │───▶│ Serialize   │───▶│ TCP Send   │  │
│  └─────────────────┘    └─────────────┘    └────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Command Handlers

```csharp
// Example: Move to position handler
public class MoveToPositionHandler : ICommandHandler
{
    public string CommandName => "move_to_position";

    private RobotController robot;

    public Message Handle(Message request)
    {
        var x = (float)request.parameters["x"];
        var y = (float)request.parameters["y"];
        var z = (float)request.parameters["z"];

        try
        {
            robot.MoveToPosition(new Vector3(x, y, z));

            return new Message
            {
                id = request.id,
                type = "response",
                status = "success",
                data = new { position = new { x, y, z } }
            };
        }
        catch (Exception e)
        {
            return new Message
            {
                id = request.id,
                type = "response",
                status = "error",
                error = new { code = "E002", message = e.Message }
            };
        }
    }
}
```

## Python Client Design

### Class Structure

```python
class RobotClient:
    """TCP client for communicating with Unity robot simulation."""

    def __init__(self, host: str = '127.0.0.1', port: int = 5555):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self._event_thread: Optional[threading.Thread] = None

    # Connection management
    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    # Low-level communication
    def _send_message(self, message: dict) -> None: ...
    def _receive_message(self) -> dict: ...
    def send_command(self, command: str, **params) -> dict: ...

    # High-level robot control
    def move_to_position(self, x: float, y: float, z: float) -> dict: ...
    def move_to(self, location: str) -> dict: ...
    def grip(self, force: float = 1.0) -> dict: ...
    def release(self) -> dict: ...
    def get_position(self) -> dict: ...
    def get_joints(self) -> dict: ...

    # Event handling
    def on_event(self, event_type: str, callback: Callable) -> None: ...
    def start_event_listener(self) -> None: ...
    def stop_event_listener(self) -> None: ...
```

### Usage Example

```python
from robot_client import RobotClient

# Create client and connect
client = RobotClient()
client.connect()

# Register event handlers
def on_motion_complete(event):
    print(f"Motion complete: {event['data']['position']}")

client.on_event('motion_complete', on_motion_complete)
client.start_event_listener()

# Control the robot
client.move_to_position(x=0.5, y=0.3, z=0.2)
client.grip()
client.move_to_position(x=0.1, y=0.1, z=0.5)
client.release()

# Get current state
pos = client.get_position()
print(f"Current position: {pos['data']['position']}")

# Cleanup
client.stop_event_listener()
client.disconnect()
```

## Message Flow Example

### Command Request/Response

```
Python                                          Unity
  │                                               │
  │  ┌─────────────────────────────────────┐     │
  │  │ {                                   │     │
  │  │   "id": "abc-123",                  │     │
  │  │   "type": "request",                │     │
  │  │   "command": "move_to_position",    │     │
  │  │   "params": {"x": 0.5, "y": 0.3}    │────▶│
  │  │ }                                   │     │
  │  └─────────────────────────────────────┘     │
  │                                               │
  │                                    [Robot moves]
  │                                               │
  │  ┌─────────────────────────────────────┐     │
  │  │ {                                   │     │
  │  │   "id": "abc-123",                  │     │
  │◀─│   "type": "response",               │─────│
  │  │   "status": "success",              │     │
  │  │   "data": {"position": {...}}       │     │
  │  │ }                                   │     │
  │  └─────────────────────────────────────┘     │
  │                                               │
```

## Error Handling Strategy

1. **Network Errors**: Automatic reconnection with exponential backoff
2. **Parse Errors**: Log and return error response, don't crash
3. **Command Errors**: Return structured error with code and message
4. **Timeout**: Configurable per-command timeout with cancellation

## Performance Considerations

1. **Message Queue Size**: Limit to 1000 messages to prevent memory issues
2. **Update Rate**: Process max 10 messages per Update() call
3. **Serialization**: Use Newtonsoft.Json for consistent performance
4. **Buffer Size**: 64KB default, configurable for large messages

## Security Notes

1. Default to localhost-only connections
2. No sensitive data in logs
3. Validate all incoming JSON structure
4. Rate limiting on connection attempts (future enhancement)
