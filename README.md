# Python to Unity Robot

Project where any LLM can control a robotic arm simulator in Unity 3D using Reinforcement Learning.

## Project Overview

This project implements a **6-DOF robotic arm** simulation in Unity 3D with Python-based RL training capabilities. The system uses **TCP sockets** for communication, ArticulationBody for physics-accurate robot simulation, and PPO algorithm for learning pick-and-place tasks.

### Architecture

```
┌─────────────────────┐                    ┌─────────────────────┐
│     PYTHON          │                    │      UNITY 3D       │
│  (RL Agent/Brain)   │                    │   (Physics Engine)  │
├─────────────────────┤                    ├─────────────────────┤
│  Gymnasium Env      │◄──── TCP/JSON ───►│  ArticulationBody   │
│  PPO Agent (SB3)    │   Length-Prefixed  │  6-DOF Robot        │
│  Control Panel UI   │     Port 5555      │  Laser Sensor       │
└─────────────────────┘                    └─────────────────────┘
```

### Key Features

- **6-DOF Articulated Robot**: Using Unity's ArticulationBody for stable kinematics
- **Reinforcement Learning**: PPO training with Stable Baselines3
- **TCP Communication**: Length-prefixed JSON messages for reliable sync communication
- **Dual Mode Operation**: Training (instant) and Simulation (smooth movement)
- **Curriculum Learning**: Progressive task complexity (touch → grasp → pick-and-place)
- **Chess Demo**: Robot chess playing demonstration

---

## OpenSpec Documentation

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) methodology for specification-driven AI development.

### Specification Structure

```
openspec/
├── README.md                          # OpenSpec methodology guide
├── specs/                             # Current specifications (source of truth)
│   ├── system.md                      # Core system requirements
│   ├── robot-interface.md             # RL observation/action spaces
│   ├── communication.md               # TCP protocol
│   └── chess-system.md                # Chess playing system
└── changes/                           # Proposed changes
    └── 001-implement-python-server/   # Current implementation proposal
        ├── proposal.md                # Change justification
        ├── design.md                  # Technical design document
        └── tasks.md                   # Implementation checklist
```

### Specification Files

| File | Description | Version |
|------|-------------|---------|
| [openspec/README.md](openspec/README.md) | OpenSpec methodology and workflow guide | - |
| [openspec/specs/system.md](openspec/specs/system.md) | Core system requirements and architecture | v1.0.0 |
| [openspec/specs/robot-interface.md](openspec/specs/robot-interface.md) | RL observation space (17-dim), action space (7-dim), reward function | v2.0.0 |
| [openspec/specs/communication.md](openspec/specs/communication.md) | TCP length-prefixed protocol, message formats | v2.0.0 |
| [openspec/specs/chess-system.md](openspec/specs/chess-system.md) | Chess playing robot system, move execution, game management | v1.0.0 |

### Change Proposals

| Proposal | Status | Description |
|----------|--------|-------------|
| [001-implement-python-server](openspec/changes/001-implement-python-server/) | Implemented | 6-DOF RL system with TCP bridge |

#### Proposal 001 Files

| File | Description |
|------|-------------|
| [proposal.md](openspec/changes/001-implement-python-server/proposal.md) | Motivation, scope, technical decisions, risks |
| [design.md](openspec/changes/001-implement-python-server/design.md) | Complete technical design with C# and Python code |
| [tasks.md](openspec/changes/001-implement-python-server/tasks.md) | 21 implementation tasks across 5 phases |

---

## Technical Stack

### Unity (Server)
- **Engine**: Unity 6 (6000.2.7f2)
- **Physics**: ArticulationBody for stable kinematic chains
- **Networking**: TCP sockets with length-prefixed JSON
- **Framework**: realvirtual (industrial automation)

### Python (Client)
- **RL Environment**: Gymnasium
- **RL Algorithm**: PPO (Stable Baselines3)
- **Communication**: TCP sockets (built-in `socket` module)
- **UI**: CustomTkinter

---

## Implementation Phases

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| 1 | The Skeleton | Unity robot with ArticulationBody, sensors | ✅ |
| 2 | The Connection | TCP bridge (length-prefixed JSON) | ✅ |
| 3 | The Gym Environment | Gymnasium env (17-dim obs, 7-dim action) | ✅ |
| 4 | Training | PPO with curriculum learning | ✅ |
| 5 | Control Panel | CustomTkinter UI for inference | ✅ |

---

## Quick Links

### Specifications
- [System Specification](openspec/specs/system.md)
- [Robot Interface (RL Spaces)](openspec/specs/robot-interface.md)
- [Communication Protocol](openspec/specs/communication.md)
- [Chess System](openspec/specs/chess-system.md)

### Implementation
- [Technical Design Document](openspec/changes/001-implement-python-server/design.md)
- [Implementation Tasks](openspec/changes/001-implement-python-server/tasks.md)
- [Change Proposal](openspec/changes/001-implement-python-server/proposal.md)

### External References
- [OpenSpec Methodology](https://github.com/Fission-AI/OpenSpec)
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/)
- [Unity ArticulationBody](https://docs.unity3d.com/Manual/class-ArticulationBody.html)
- [Gymnasium](https://gymnasium.farama.org/)

---

## Getting Started

### Prerequisites

**Unity:**
- Unity 6 (6000.2.7f2)
- realvirtual framework

**Python:**
```bash
pip install gymnasium stable-baselines3 numpy customtkinter
```

### Running the System

1. Open Unity project and start the RobotRL scene
2. Press Play in Unity (TCP server starts on port 5555)
3. Run Python training script:
   ```bash
   cd python
   python train.py
   ```
4. Or test the connection:
   ```bash
   cd python
   python test_connection.py
   ```
5. Or use the control panel:
   ```bash
   cd python
   python ui/control_panel.py
   ```

---

## Project Structure

```
python_to_unity_robot/
├── Assets/
│   └── Scripts/
│       ├── Controllers/          # Robot, Target, Sensor controllers
│       ├── Services/             # Network, Robot, Laser services
│       ├── Models/               # Command, Observation, State models
│       ├── Enums/                # CommandType, CollisionType
│       ├── Events/               # Robot and collision events
│       └── Bootstrap/            # GameManager entry point
├── python/
│   ├── environments/             # UnityRobotEnvironment (Gymnasium)
│   ├── services/                 # NetworkService, RewardCalculationService
│   ├── models/                   # Command, Observation, Reward models
│   ├── controllers/              # TrainingController
│   ├── ui/                       # ControlPanel (CustomTkinter)
│   ├── tests/                    # Unit tests
│   ├── train.py                  # Main training entry point
│   └── test_connection.py        # Connection verification
└── openspec/                     # OpenSpec documentation
```

---

## RL Interface

### Observation Space (17 dimensions)
| Index | Component | Range |
|-------|-----------|-------|
| 0-5 | Joint angles (normalized) | [-1, 1] |
| 6 | Gripper state | [0, 1] |
| 7-9 | TCP position (normalized) | [-1, 1] |
| 10-12 | Direction to target | [-1, 1] |
| 13 | Laser distance (normalized) | [0, 1] |
| 14 | Is gripping object | {0, 1} |
| 15-16 | Target orientation one-hot | {0, 1} |

### Action Space (7 dimensions)
| Index | Component | Range |
|-------|-----------|-------|
| 0-4 | Joint angle deltas | [-1, 1] → ±10° |
| 5 | Axis 6 orientation | <0: vertical, ≥0: horizontal |
| 6 | Gripper action | [-1, 1] |

---

## License

See individual component licenses (realvirtual framework has commercial license).
