# Python to Unity Robot

Project where any LLM can control a robotic arm simulator in Unity 3D using Reinforcement Learning.

## Project Overview

This project implements a 4-DOF robotic arm simulation in Unity 3D with Python-based RL training capabilities. The system uses ZeroMQ for communication, ArticulationBody for physics-accurate robot simulation, and PPO algorithm for learning pick-and-place tasks.

### Architecture

```
┌─────────────────────┐                    ┌─────────────────────┐
│     PYTHON          │                    │      UNITY 3D       │
│  (RL Agent/Brain)   │                    │   (Physics Engine)  │
├─────────────────────┤                    ├─────────────────────┤
│  Gymnasium Env      │◄──── ZeroMQ ─────►│  ArticulationBody   │
│  PPO/SAC Agent      │    REQ-REP/JSON    │  4-DOF Robot        │
│  Control Panel UI   │     Port 5555      │  Laser Sensor       │
└─────────────────────┘                    └─────────────────────┘
```

### Key Features

- **4-DOF Articulated Robot**: Using Unity's ArticulationBody for stable kinematics
- **Reinforcement Learning**: PPO training with Stable Baselines3
- **Dual Mode Operation**: Training (fast) and Simulation (realistic)
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
│   ├── communication.md               # ZeroMQ protocol
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
| [openspec/specs/robot-interface.md](openspec/specs/robot-interface.md) | RL observation space (15-dim), action space (5-dim), reward function | v2.0.0 |
| [openspec/specs/communication.md](openspec/specs/communication.md) | ZeroMQ REQ-REP protocol, message formats, threading model | v2.0.0 |
| [openspec/specs/chess-system.md](openspec/specs/chess-system.md) | Chess playing robot system, move execution, game management | v1.0.0 |

### Change Proposals

| Proposal | Status | Description |
|----------|--------|-------------|
| [001-implement-python-server](openspec/changes/001-implement-python-server/) | Proposed | 4-DOF RL system with ZMQ bridge |

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
- **Networking**: NetMQ (ZeroMQ for .NET)
- **Framework**: realvirtual (industrial automation)

### Python (Client)
- **RL Environment**: Gymnasium
- **RL Algorithm**: PPO (Stable Baselines3)
- **Communication**: pyzmq
- **UI**: CustomTkinter

---

## Implementation Phases

| Phase | Name | Description |
|-------|------|-------------|
| 1 | The Skeleton | Unity robot with ArticulationBody, sensors |
| 2 | The Connection | ZMQ bridge (NetMQ + pyzmq) |
| 3 | The Gym Environment | Gymnasium env with observation/action spaces |
| 4 | Training | PPO with curriculum learning |
| 5 | Control Panel | CustomTkinter UI for inference |

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
- [NetMQ (ZeroMQ for .NET)](https://netmq.readthedocs.io/)

---

## Getting Started

> **Note**: Implementation in progress. See [tasks.md](openspec/changes/001-implement-python-server/tasks.md) for current status.

### Prerequisites

**Unity:**
- Unity 6 (6000.2.7f2)
- NetMQ package

**Python:**
```bash
pip install gymnasium stable-baselines3 pyzmq numpy customtkinter
```

### Running the System

1. Open Unity project and start the scene
2. Run Python training script:
   ```bash
   python train.py
   ```
3. Or use the control panel:
   ```bash
   python control_panel.py
   ```

---

## License

See individual component licenses (realvirtual framework has commercial license).
