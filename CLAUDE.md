# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

6-DOF Robotic Arm RL Training System combining Unity 3D (physics server) and Python (RL client) via TCP sockets.

```
PYTHON (Client)                    UNITY (Server)
├─ Gymnasium Env                   ├─ ArticulationBody 6-DOF
├─ PPO (Stable Baselines3)  ◄──►   ├─ Laser Sensor
├─ Training Controller      TCP     ├─ Random Targets
└─ Control Panel UI         5555    └─ TCP Server
```

## Development Commands

```bash
# Python setup
cd python
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Test connection (mock mode, no Unity needed)
python test_connection.py

# Start training (requires Unity running)
python train.py

# Launch control panel UI
python ui/control_panel.py

# Monitor training
tensorboard --logdir=./tensorboard_logs/
```

## Key Architecture

### Communication Protocol
TCP sockets with **length-prefixed JSON** on port 5555:
- Python sends: STEP/RESET/CONFIG commands
- Unity responds: 17-dimensional observation

### RL Interface
- **Observation**: 17 dimensions (joint angles, TCP position, target direction, laser distance, gripper state)
- **Action**: 7 dimensions (5 joint deltas, axis 6 orientation, gripper)
- **Reward**: Distance-based + alignment + grasp bonus (+100) + collision penalty (-100)

### Key Files
| Purpose | Python | Unity |
|---------|--------|-------|
| Entry Point | `train.py` | `Assets/Scripts/Bootstrap/GameManager.cs` |
| Network | `services/network_service.py` | `Assets/Scripts/Services/TcpNetworkService.cs` |
| RL Environment | `environments/unity_robot_environment.py` | - |
| Robot Control | - | `Assets/Scripts/Services/RobotService.cs` |
| Config | `config.py` | GameManager inspector |

### OpenSpec Specifications
Specs in `openspec/specs/` are source of truth:
- `system.md` - Core requirements
- `robot-interface.md` - RL observation/action spaces
- `communication.md` - TCP protocol

## Running the System

1. Open Unity project (Unity 6), open RobotRL scene, press Play
2. Run `python train.py` in separate terminal
3. (Optional) Run tensorboard for monitoring

## Configuration

Key settings in `python/config.py`:
- `UNITY_SERVER_ADDRESS = "tcp://localhost:5555"`
- `JOINT_ANGLE_LIMITS = [90.0, 90.0, 90.0, 180.0, 90.0, 90.0]`
- `MAXIMUM_DELTA_DEGREES = 10.0` per step
- `DEFAULT_MAXIMUM_EPISODE_STEPS = 500`
