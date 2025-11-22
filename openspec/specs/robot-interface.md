# Robot Interface Specification: LLM Robot Control

**Version:** 1.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the interface through which Large Language Models (LLMs) can control robotic manipulators in the Unity simulation. The interface provides high-level commands that abstract the complexity of robot kinematics and motion planning.

---

## Requirements

### Requirement: INTERFACE-001 - Command Reception
The system SHALL receive and process robot control commands from external LLM agents.

#### Scenario: Move to Position Command
- WHEN an LLM sends a `move_to_position` command with coordinates (x, y, z)
- THEN the robot SHALL compute the inverse kinematics
- AND move the end effector to the specified position
- AND return a success/failure status

#### Scenario: Move to Named Location
- WHEN an LLM sends a `move_to` command with a named location (e.g., "home", "pickup_zone")
- THEN the robot SHALL retrieve the predefined coordinates
- AND execute the movement to that location

#### Scenario: Invalid Command Handling
- WHEN an LLM sends a malformed or invalid command
- THEN the system SHALL return an error response
- AND the robot SHALL remain in its current position

---

### Requirement: INTERFACE-002 - Gripper Control
The system SHALL provide gripper control capabilities for object manipulation.

#### Scenario: Grip Object
- WHEN an LLM sends a `grip` command
- THEN the gripper SHALL close to grasp an object
- AND return the grip status (success/failure/no_object)

#### Scenario: Release Object
- WHEN an LLM sends a `release` command
- THEN the gripper SHALL open to release the held object
- AND return confirmation of the release

#### Scenario: Set Grip Force
- WHEN an LLM specifies a grip force parameter
- THEN the gripper SHALL adjust to the specified force level
- AND maintain that force during the grip operation

---

### Requirement: INTERFACE-003 - State Queries
The system SHALL respond to state query requests from LLM agents.

#### Scenario: Query Robot Position
- WHEN an LLM sends a `get_position` query
- THEN the system SHALL return the current end effector position
- AND include orientation data (quaternion or euler angles)

#### Scenario: Query Joint States
- WHEN an LLM sends a `get_joints` query
- THEN the system SHALL return all joint angles
- AND include joint velocity information if available

#### Scenario: Query Gripper State
- WHEN an LLM sends a `get_gripper_state` query
- THEN the system SHALL return the gripper position (open percentage)
- AND indicate if an object is currently gripped

---

### Requirement: INTERFACE-004 - Motion Parameters
The system SHALL allow configuration of motion parameters by LLM agents.

#### Scenario: Set Movement Speed
- WHEN an LLM specifies a `speed` parameter (0.0 to 1.0)
- THEN subsequent movements SHALL execute at the specified speed percentage
- AND return acknowledgment of the speed change

#### Scenario: Set Acceleration Profile
- WHEN an LLM specifies acceleration and deceleration values
- THEN the motion controller SHALL use these parameters
- AND ensure smooth motion transitions

---

### Requirement: INTERFACE-005 - Feedback and Events
The system SHALL provide real-time feedback and event notifications to LLM agents.

#### Scenario: Motion Complete Event
- WHEN a robot completes a commanded movement
- THEN the system SHALL emit a `motion_complete` event
- AND include the final position achieved

#### Scenario: Collision Detection
- WHEN the robot detects a potential collision
- THEN the system SHALL emit a `collision_warning` event
- AND optionally halt the current motion

#### Scenario: Error Notification
- WHEN an error occurs during robot operation
- THEN the system SHALL emit an `error` event
- AND include error code and description

---

## Command Reference

### Movement Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `move_to_position` | x, y, z, [rx, ry, rz] | Move to Cartesian coordinates |
| `move_to` | location_name | Move to predefined location |
| `move_joints` | j1, j2, j3, j4, j5, j6 | Move to joint configuration |
| `move_linear` | x, y, z, [speed] | Linear interpolated movement |
| `move_relative` | dx, dy, dz | Relative movement from current position |

### Gripper Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `grip` | [force] | Close gripper |
| `release` | - | Open gripper |
| `set_gripper` | position (0-100) | Set gripper to specific position |

### Query Commands

| Command | Returns | Description |
|---------|---------|-------------|
| `get_position` | {x, y, z, rx, ry, rz} | Current end effector pose |
| `get_joints` | {j1, j2, ...} | Current joint angles |
| `get_gripper_state` | {position, is_gripping} | Gripper status |
| `get_workspace` | {min, max} | Robot workspace bounds |

---

## Response Format

All commands SHALL return responses in the following JSON format:

```json
{
  "command": "move_to_position",
  "status": "success|error|in_progress",
  "timestamp": 1732300800000,
  "data": {
    "position": {"x": 0.5, "y": 0.3, "z": 0.2},
    "duration_ms": 1500
  },
  "error": null
}
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| E001 | INVALID_COMMAND | Command not recognized |
| E002 | OUT_OF_REACH | Target position is outside workspace |
| E003 | COLLISION_DETECTED | Path would cause collision |
| E004 | IK_NO_SOLUTION | Inverse kinematics has no solution |
| E005 | JOINT_LIMIT | Joint limit would be exceeded |
| E006 | GRIPPER_FAULT | Gripper operation failed |
| E007 | TIMEOUT | Operation timed out |

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [communication.md](communication.md) - Communication protocol details
- [chess-system.md](chess-system.md) - Chess-specific robot interface
