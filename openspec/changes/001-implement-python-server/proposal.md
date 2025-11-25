# Proposal: 4-DOF Robotic System with Reinforcement Learning Sim-to-Real

**Change ID:** 001
**Date:** 2025-11-22
**Status:** Proposed
**Author:** AI Development Agent

---

## Summary

Implement a complete 4-DOF robotic arm simulation system in Unity 3D with Reinforcement Learning (RL) training capabilities in Python. The system uses TCP sockets for communication, ArticulationBody for physics-accurate robot simulation, and PPO algorithm for training pick-and-place tasks.

---

## Motivation

The goal is to create an MVP robotic arm simulator that:

1. **Enables RL Training**: Allow LLMs and RL agents to learn manipulation tasks through trial and error
2. **Sim-to-Real Transfer**: Use ArticulationBody physics for realistic behavior that transfers to real robots
3. **Deterministic Control**: Python controls the simulation step for reproducible RL training
4. **Dual Mode Operation**: Support fast training mode and smooth simulation/inference mode

### Use Cases

- Training pick-and-place policies with PPO/SAC
- Sim-to-real transfer for physical robot arms
- LLM-controlled robot demonstrations (chess playing)
- Research platform for robot learning

---

## Scope

### In Scope

**Unity (Server)**
- 4-DOF articulated robot arm using ArticulationBody
- Laser sensor (Raycast) from TCP
- Random target spawning in reachable hemisphere
- TCP server with length-prefixed JSON protocol
- Training mode (instant teleport) and Simulation mode (smooth interpolation)
- Collision detection and reporting

**Python (Client)**
- Gymnasium environment (`UnityRobotEnv`)
- TCP client for Unity communication
- Observation space: 15 dimensions (normalized)
- Action space: 5 dimensions (4 joints + gripper)
- Reward function: $R_{total} = R_{dist} + R_{align} + R_{grasp} + R_{penalty}$
- PPO training with Stable Baselines3
- Curriculum learning (touch → grasp → pick-and-place)
- CustomTkinter control panel

### Out of Scope (Future Enhancements)

- Vision-based observations (camera input)
- Multiple robot arms
- Dynamic obstacle avoidance
- Real robot hardware interface
- Distributed training

---

## Technical Decisions

### Why ArticulationBody over Rigidbody + HingeJoint?

| Aspect | ArticulationBody | Rigidbody + HingeJoint |
|--------|------------------|------------------------|
| Stability | Excellent for kinematic chains | Can be unstable |
| Precision | High joint precision | Drift over time |
| Performance | Optimized for robots | General purpose |
| Control | Direct drive access | Requires workarounds |

### Why TCP Sockets?

| Aspect | TCP Sockets | Alternative |
|--------|-------------|-------------|
| Dependencies | None (stdlib) | External libs |
| Reliability | Built-in guarantees | Varies |
| Debugging | Standard tools | Library-specific |
| Complexity | Simple API | Minimal |

### Why PPO over SAC?

| Aspect | PPO | SAC |
|--------|-----|-----|
| Stability | More stable | Can diverge |
| Sample Efficiency | Lower | Higher |
| Continuous Actions | Good | Excellent |
| Tuning | Easier | More parameters |

**Decision**: PPO for initial implementation due to stability. SAC can be added later.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐         TCP             ┌─────────────┐
    │   PYTHON    │◄───────────────────────►│    UNITY    │
    │             │   Length-Prefixed JSON   │             │
    │ ┌─────────┐ │                          │ ┌─────────┐ │
    │ │Gymnasium│ │   Action (5 floats)      │ │ Article.│ │
    │ │   Env   │─┼────────────────────────►│ │  Body   │ │
    │ └─────────┘ │                          │ │ Physics │ │
    │      │      │                          │ └─────────┘ │
    │      ▼      │   Observation (15 floats)│      │      │
    │ ┌─────────┐ │◄─────────────────────────┼──────┘      │
    │ │   PPO   │ │                          │             │
    │ │ Agent   │ │                          │ ┌─────────┐ │
    │ └─────────┘ │   RESET/CONFIG commands  │ │ Target  │ │
    │      │      │────────────────────────►│ │ Spawner │ │
    │      ▼      │                          │ └─────────┘ │
    │ ┌─────────┐ │                          │             │
    │ │ Control │ │                          │ ┌─────────┐ │
    │ │  Panel  │ │                          │ │ Laser   │ │
    │ │  (UI)   │ │                          │ │ Sensor  │ │
    │ └─────────┘ │                          │ └─────────┘ │
    └─────────────┘                          └─────────────┘
```

---

## Affected Specifications

| Specification | Impact |
|---------------|--------|
| communication.md | **Major**: TCP socket protocol |
| robot-interface.md | **Major**: Update to RL action/observation spaces |
| system.md | **Minor**: Add ArticulationBody requirements |
| chess-system.md | **None**: Future integration |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Physics instability | Low | High | ArticulationBody is designed for this |
| Training divergence | Medium | Medium | Curriculum learning, reward shaping |
| Communication latency | Low | Low | TCP is fast enough for 50Hz |
| Unity thread safety | Medium | High | ConcurrentQueue for cross-thread |
| Sim-to-real gap | Medium | High | Realistic physics parameters |

---

## Success Criteria

1. **Connection**: Python can connect to Unity via TCP
2. **Control**: Robot responds to action commands
3. **Observation**: Unity returns accurate state data
4. **Training**: PPO agent can learn to touch target
5. **Curriculum**: Agent progresses through learning stages
6. **Inference**: Trained model can execute in simulation mode

---

## Dependencies

### Unity
- Unity 6 (6000.2.7f2)
- System.Net.Sockets (built-in)

### Python
```
gymnasium>=0.29.0
stable-baselines3>=2.0.0
numpy>=1.24.0
customtkinter>=5.0.0
```

---

## Implementation Phases

| Phase | Description | Est. Complexity |
|-------|-------------|-----------------|
| 1 | Unity robot skeleton (ArticulationBody) | Medium |
| 2 | TCP Bridge (native sockets) | Low |
| 3 | Gymnasium Environment | Medium |
| 4 | RL Training Loop | Low |
| 5 | Control Panel UI | Low |

---

## References

- [Technical Design Document](design.md) - Complete implementation details
- [Implementation Tasks](tasks.md) - Task breakdown and tracking
- [OpenSpec Methodology](https://github.com/Fission-AI/OpenSpec)
- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Unity ArticulationBody](https://docs.unity3d.com/Manual/class-ArticulationBody.html)
