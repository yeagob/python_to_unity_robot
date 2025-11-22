# Robot Interface Specification: RL Action and Observation Spaces

**Version:** 2.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the Reinforcement Learning interface for controlling the 4-DOF robotic arm in Unity. It specifies the observation space, action space, and reward function used by Gymnasium environments and RL algorithms like PPO.

---

## Requirements

### Requirement: INTERFACE-001 - Observation Space
The system SHALL provide a 15-dimensional normalized observation vector.

#### Scenario: Observation Vector Construction
- WHEN Unity builds an observation
- THEN it SHALL include the following components (in order):
  1. Joint angles (4 values, normalized by limits)
  2. Gripper state (1 value, 0=open, 1=closed)
  3. TCP position (3 values, normalized by workspace)
  4. Direction to target (3 values, unit vector)
  5. Laser distance (1 value, normalized)
  6. Is gripping flag (1 value, 0 or 1)
  7. Target orientation (2 values, one-hot)

#### Scenario: Normalization Bounds
- WHEN observation values are computed
- THEN all values SHALL be clipped to range [-1, 1]
- AND joint angles SHALL be divided by their respective limits
- AND TCP position SHALL be divided by workspace radius (0.6m)
- AND laser distance SHALL be divided by max range (1.0m)

#### Scenario: Target Orientation Encoding
- WHEN target is vertical
- THEN targetOrientation SHALL be [1, 0]
- WHEN target is horizontal
- THEN targetOrientation SHALL be [0, 1]

---

### Requirement: INTERFACE-002 - Action Space
The system SHALL accept a 5-dimensional continuous action vector.

#### Scenario: Action Vector Interpretation
- WHEN an action vector is received
- THEN it SHALL be interpreted as:
  1. Delta angle for Axis 1 (index 0)
  2. Delta angle for Axis 2 (index 1)
  3. Delta angle for Axis 3 (index 2)
  4. Delta angle for Axis 4 (index 3)
  5. Gripper command (index 4)

#### Scenario: Action Scaling
- WHEN raw actions are in range [-1, 1]
- THEN joint deltas SHALL be scaled by max_delta (10 degrees)
- AND gripper command > 0.5 SHALL close the gripper
- AND gripper command <= 0.5 SHALL open the gripper

#### Scenario: Joint Limits
- WHEN scaled actions would exceed joint limits
- THEN the joint position SHALL be clamped to valid range
- AND no error SHALL be raised

---

### Requirement: INTERFACE-003 - Reward Function
The system SHALL compute rewards based on task progress and safety.

#### Scenario: Distance Reward (R_dist)
- WHEN the TCP moves closer to target
- THEN reward SHALL increase proportionally
- AND reward = (prev_distance - current_distance) * 10.0

#### Scenario: Alignment Reward (R_align)
- WHEN TCP velocity aligns with target direction
- THEN reward SHALL be positive
- AND reward = dot(velocity_normalized, direction) * 0.5
- WHERE velocity = current_tcp - prev_tcp

#### Scenario: Grasp Reward (R_grasp)
- WHEN laser_distance < 0.05m AND gripper is closed AND object is gripped
- THEN reward SHALL be +100
- AND info['success'] SHALL be True

#### Scenario: Collision Penalty (R_penalty)
- WHEN robot collides with non-target object
- THEN reward SHALL be -100
- AND episode SHALL terminate (done=True)
- AND info['collision'] SHALL be True

#### Scenario: Total Reward
- WHEN calculating step reward
- THEN R_total = R_dist + R_align + R_grasp + R_penalty

---

### Requirement: INTERFACE-004 - Episode Management
The system SHALL manage RL episode boundaries correctly.

#### Scenario: Episode Termination
- WHEN collision occurs (non-target)
- THEN terminated SHALL be True
- AND truncated SHALL be False

#### Scenario: Episode Truncation
- WHEN step count exceeds max_episode_steps (500)
- THEN truncated SHALL be True
- AND terminated SHALL be False

#### Scenario: Episode Reset
- WHEN reset() is called
- THEN robot SHALL return to home position
- AND new target SHALL spawn at random location
- AND step counter SHALL reset to 0
- AND collision flags SHALL be cleared

---

### Requirement: INTERFACE-005 - Control Modes
The system SHALL support two operational modes.

#### Scenario: Training Mode
- WHEN mode is Training
- THEN joint positions SHALL change instantly (teleport)
- AND self-collisions SHALL be ignored
- AND this SHALL enable fast episode collection

#### Scenario: Simulation Mode
- WHEN mode is Simulation
- THEN joint positions SHALL interpolate smoothly
- AND max velocity SHALL be limited (90 deg/sec)
- AND this SHALL demonstrate realistic behavior

---

## Observation Space Definition

### Gymnasium Space
```python
observation_space = spaces.Box(
    low=-1.0,
    high=1.0,
    shape=(15,),
    dtype=np.float32
)
```

### Component Breakdown

| Index | Component | Raw Range | Normalization |
|-------|-----------|-----------|---------------|
| 0 | Axis 1 angle | -180° to +180° | / 180 |
| 1 | Axis 2 angle | -90° to +90° | / 90 |
| 2 | Axis 3 angle | -135° to +135° | / 135 |
| 3 | Axis 4 angle | -180° to +180° | / 180 |
| 4 | Gripper state | 0 to 1 | direct |
| 5 | TCP X | -0.6m to +0.6m | / 0.6 |
| 6 | TCP Y | 0 to 0.6m | / 0.6 |
| 7 | TCP Z | -0.6m to +0.6m | / 0.6 |
| 8 | Dir X | -1 to +1 | direct |
| 9 | Dir Y | -1 to +1 | direct |
| 10 | Dir Z | -1 to +1 | direct |
| 11 | Laser distance | 0 to 1m | / 1.0 |
| 12 | Is gripping | 0 or 1 | direct |
| 13 | Target vertical | 0 or 1 | direct |
| 14 | Target horizontal | 0 or 1 | direct |

---

## Action Space Definition

### Gymnasium Space
```python
action_space = spaces.Box(
    low=-1.0,
    high=1.0,
    shape=(5,),
    dtype=np.float32
)
```

### Component Breakdown

| Index | Component | Raw Range | Scaling |
|-------|-----------|-----------|---------|
| 0 | Delta Axis 1 | -1 to +1 | × 10° |
| 1 | Delta Axis 2 | -1 to +1 | × 10° |
| 2 | Delta Axis 3 | -1 to +1 | × 10° |
| 3 | Delta Axis 4 | -1 to +1 | × 10° |
| 4 | Gripper | -1 to +1 | >0.5 = close |

---

## Reward Function Details

### Mathematical Definition

$$R_{total} = R_{dist} + R_{align} + R_{grasp} + R_{penalty}$$

Where:
- $R_{dist} = (d_{t-1} - d_t) \times 10.0$
- $R_{align} = \frac{\vec{v}}{|\vec{v}|} \cdot \vec{d} \times 0.5$ (if $|\vec{v}| > \epsilon$)
- $R_{grasp} = 100.0$ (if laser < 0.05m AND gripping)
- $R_{penalty} = -100.0$ (if collision with non-target)

### Reward Shaping Rationale

| Component | Purpose | Magnitude |
|-----------|---------|-----------|
| R_dist | Encourage approaching target | ~0-5 per step |
| R_align | Discourage inefficient paths | ~0-0.5 per step |
| R_grasp | Terminal success signal | +100 once |
| R_penalty | Safety constraint | -100 terminal |

---

## Curriculum Learning

### Lesson Progression

| Lesson | Goal | R_grasp Condition | Steps |
|--------|------|-------------------|-------|
| 1: Touch | TCP reaches target | distance < 0.1m | 100K |
| 2: Grasp | Grip the object | laser < 0.05m + grip | 200K |
| 3: Pick & Place | Full task | lift + place | 500K |

### Reward Modification per Lesson

```python
# Lesson 1: Touch only
if lesson == 1:
    if distance_to_target < 0.1:
        reward += 50  # Touch bonus

# Lesson 2+: Full grasp reward
if lesson >= 2:
    if laser_distance < 0.05 and is_gripping:
        reward += 100  # Grasp bonus
```

---

## State Diagram

```
                    ┌─────────────┐
                    │   RESET     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
           ┌───────│   ACTIVE    │◄──────┐
           │       └──────┬──────┘       │
           │              │              │
           │     STEP (action)           │
           │              │              │
           ▼              ▼              │
    ┌─────────────┐ ┌─────────────┐      │
    │  COLLISION  │ │  CONTINUE   │──────┘
    │ (done=True) │ │             │
    └─────────────┘ └──────┬──────┘
                           │
                    max_steps reached?
                           │
                    ┌──────┴──────┐
                    │  TRUNCATED  │
                    │(trunc=True) │
                    └─────────────┘
```

---

## Python Implementation Example

```python
def _calculate_reward(self, obs: Dict) -> Tuple[float, bool, Dict]:
    reward = 0.0
    done = False
    info = {}

    distance = obs['distanceToTarget']
    tcp = np.array(obs['tcpPosition'])
    direction = np.array(obs['directionToTarget'])

    # R_dist: Distance improvement
    if self.prev_distance is not None:
        r_dist = (self.prev_distance - distance) * 10.0
        reward += r_dist

    # R_align: Velocity alignment
    velocity = tcp - self.prev_tcp
    if np.linalg.norm(velocity) > 1e-6:
        v_norm = velocity / np.linalg.norm(velocity)
        r_align = np.dot(v_norm, direction) * 0.5
        reward += r_align

    # R_grasp: Success
    if obs['laserDistance'] < 0.05 and obs['isGripping']:
        reward += 100.0
        info['success'] = True

    # R_penalty: Collision
    if obs['collision']:
        reward -= 100.0
        done = True
        info['collision'] = True

    self.prev_distance = distance
    self.prev_tcp = tcp.copy()

    return reward, done, info
```

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [communication.md](communication.md) - ZeroMQ protocol details
- [chess-system.md](chess-system.md) - Chess-specific interface extensions
