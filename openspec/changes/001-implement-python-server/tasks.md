# Implementation Tasks: 4-DOF Robotic System with RL

**Change ID:** 001
**Last Updated:** 2025-11-22
**Status:** Implementation Ready

---

## Phase Overview

| Phase | Name | Status | Dependencies |
|-------|------|--------|--------------|
| 1 | The Skeleton (Unity) | Pending | None |
| 2 | The Connection (ZMQ Bridge) | Pending | Phase 1 |
| 3 | The Gym Environment (Python) | Pending | Phase 2 |
| 4 | Training (RL Loop) | Pending | Phase 3 |
| 5 | Control Panel & Inference | Pending | Phase 4 |

---

## Phase 1: The Skeleton (Unity)

### TASK-1.1: Create 4-DOF Robot with ArticulationBody
- [ ] Create Base GameObject with ArticulationBody (Fixed type)
- [ ] Create Axis1 child with ArticulationBody (Revolute Y, -180° to +180°)
- [ ] Create Axis2 child with ArticulationBody (Revolute X, -90° to +90°)
- [ ] Create Axis3 child with ArticulationBody (Revolute X, -135° to +135°)
- [ ] Create Axis4 child with ArticulationBody (Revolute Z/X, -180° to +180°)
- [ ] Add Wrist and GripperBase transforms
- [ ] Create Gripper with two opposed ArticulationBody fingers (Prismatic)
- [ ] Configure ArticulationDrive parameters (stiffness, damping)
- [ ] Add visual meshes to each segment
- [ ] Configure self-collision ignoring between adjacent segments

**References:** SYSTEM-002, SYSTEM-003

### TASK-1.2: Implement RobotController.cs
- [ ] Create `RobotController` MonoBehaviour
- [ ] Implement `SetJointPositionsInstant()` for training mode (teleport)
- [ ] Implement `SetJointPositionsSmooth()` for simulation mode (interpolation)
- [ ] Implement `SetGripper(bool closed)` for gripper control
- [ ] Implement `GetState()` returning `RobotState` struct
- [ ] Implement `GetJointAngles()` for current joint positions
- [ ] Add `ControlMode` enum (Training, Simulation)
- [ ] Implement `OnCollisionEnter()` for collision detection
- [ ] Add `ResetCollisionFlag()` method

**References:** INTERFACE-001, INTERFACE-002

### TASK-1.3: Implement LaserSensor.cs
- [ ] Create `LaserSensor` MonoBehaviour
- [ ] Implement Raycast from TCP `transform.forward`
- [ ] Return `LaserData` struct (hit, distance, tag)
- [ ] Add configurable max distance
- [ ] Add debug visualization (Gizmos line)

**References:** SYSTEM-002

### TASK-1.4: Implement TargetSpawner.cs
- [ ] Create `TargetSpawner` MonoBehaviour
- [ ] Implement random position in hemisphere (min/max radius, height)
- [ ] Implement random orientation (vertical/horizontal)
- [ ] Track `currentTarget` transform
- [ ] Track `isVertical` flag for observation
- [ ] Add "Target" tag to spawned objects
- [ ] Implement `SpawnRandomTarget()` method

**References:** SYSTEM-001

### TASK-1.5: Manual Testing
- [ ] Control joints from Unity Inspector
- [ ] Verify ArticulationBody physics stability
- [ ] Test gripper open/close
- [ ] Verify laser sensor detection
- [ ] Test target spawning in valid positions

---

## Phase 2: The Connection (ZMQ Bridge)

### TASK-2.1: Install Dependencies
- [ ] Add NetMQ to Unity project (via NuGet for Unity or manual DLL)
- [ ] Add AsyncIO.ForceDotNet for socket cleanup
- [ ] Add Newtonsoft.Json for serialization
- [ ] Install pyzmq in Python: `pip install pyzmq`

### TASK-2.2: Implement ZMQServer.cs
- [ ] Create `ZMQServer` MonoBehaviour
- [ ] Implement `ResponseSocket` on dedicated thread
- [ ] Implement `ConcurrentQueue<string>` for request/response
- [ ] Implement `ServerLoop()` with `TryReceiveFrameString`
- [ ] Process commands in `FixedUpdate()` (main thread)
- [ ] Implement `ProcessRequest()` JSON parsing
- [ ] Implement `HandleStep()` for STEP commands
- [ ] Implement `HandleReset()` for RESET commands
- [ ] Implement `HandleConfig()` for CONFIG commands
- [ ] Implement `BuildObservation()` for response data
- [ ] Set `Time.fixedDeltaTime = 0.02f` (50Hz)
- [ ] Implement proper cleanup in `OnDestroy()`

**References:** COMM-001, COMM-002, COMM-004

### TASK-2.3: Define Message Structures
- [ ] Create `Command` class (type, actions, gripperClose, simulationMode)
- [ ] Create `Observation` class (all 15 observation fields)
- [ ] Ensure proper JSON serialization attributes

**References:** COMM-002

### TASK-2.4: Create test_client.py
- [ ] Implement basic ZMQ REQ socket connection
- [ ] Send random STEP commands
- [ ] Verify Unity responds with observation data
- [ ] Test RESET command
- [ ] Test CONFIG command (mode switching)
- [ ] Print received observations for debugging

---

## Phase 3: The Gym Environment (Python)

### TASK-3.1: Create UnityRobotEnv Class
- [ ] Create `unity_robot_env.py` file
- [ ] Inherit from `gym.Env`
- [ ] Define `observation_space` (Box, 15 dims, -1 to 1)
- [ ] Define `action_space` (Box, 5 dims, -1 to 1)
- [ ] Define joint limits for normalization

**References:** INTERFACE-003

### TASK-3.2: Implement ZMQ Communication
- [ ] Implement `_setup_zmq()` for socket initialization
- [ ] Implement `_send_command()` for JSON send/receive
- [ ] Add timeout handling (5 seconds)
- [ ] Add error handling for connection issues

**References:** COMM-001, COMM-003

### TASK-3.3: Implement Observation Processing
- [ ] Implement `_process_observation()` method
- [ ] Normalize joint angles by limits
- [ ] Normalize TCP position by workspace
- [ ] Pass through normalized direction vector
- [ ] Normalize laser distance
- [ ] Include gripper state, gripping flag
- [ ] Include target orientation one-hot encoding
- [ ] Clip all values to [-1, 1]

**References:** INTERFACE-003

### TASK-3.4: Implement Reward Function
- [ ] Implement `_calculate_reward()` method
- [ ] Calculate `R_dist`: Distance improvement reward
- [ ] Calculate `R_align`: Velocity alignment with target direction
- [ ] Calculate `R_grasp`: Grasp success reward (+100)
- [ ] Calculate `R_penalty`: Collision penalty (-100)
- [ ] Return reward, done flag, info dict

**References:** Design document Section 3.2

### TASK-3.5: Implement Gym Interface
- [ ] Implement `step(action)` method
- [ ] Scale actions by max_delta
- [ ] Send STEP command to Unity
- [ ] Process observation and calculate reward
- [ ] Handle truncation (max steps)
- [ ] Implement `reset()` method
- [ ] Send RESET command to Unity
- [ ] Initialize prev_distance and prev_tcp_position
- [ ] Implement `close()` method
- [ ] Implement `set_simulation_mode()` helper

---

## Phase 4: Training (RL Loop)

### TASK-4.1: Create Training Script
- [ ] Create `train.py` file
- [ ] Implement `make_env()` factory function
- [ ] Create `DummyVecEnv` wrapper
- [ ] Add `VecNormalize` for observation/reward normalization
- [ ] Configure `CheckpointCallback` for saving

### TASK-4.2: Configure PPO
- [ ] Set learning_rate = 3e-4
- [ ] Set n_steps = 2048
- [ ] Set batch_size = 64
- [ ] Set n_epochs = 10
- [ ] Set gamma = 0.99
- [ ] Set gae_lambda = 0.95
- [ ] Set clip_range = 0.2
- [ ] Set ent_coef = 0.01
- [ ] Enable TensorBoard logging

### TASK-4.3: Implement Curriculum Learning
- [ ] Define curriculum phases:
  - Lesson 1: Touch object (100K steps)
  - Lesson 2: Grasp object (200K steps)
  - Lesson 3: Pick & Place (500K steps)
- [ ] Save model checkpoint after each phase
- [ ] Save VecNormalize statistics

### TASK-4.4: Training Verification
- [ ] Run short training session
- [ ] Monitor TensorBoard metrics
- [ ] Verify episode rewards increase
- [ ] Check for training stability

---

## Phase 5: Control Panel & Inference

### TASK-5.1: Create Control Panel UI
- [ ] Create `control_panel.py` file
- [ ] Create `RobotControlPanel(ctk.CTk)` class
- [ ] Add "Simulation Mode" checkbox
- [ ] Add target position inputs (X, Y, Z)
- [ ] Add "Connect" button
- [ ] Add "Load Model" button
- [ ] Add "Execute Trajectory" button
- [ ] Add "Stop" button
- [ ] Add status label

### TASK-5.2: Implement UI Logic
- [ ] Implement `_connect()` - Create UnityRobotEnv
- [ ] Implement `_on_mode_change()` - Send CONFIG to Unity
- [ ] Implement `_load_model()` - Load PPO .zip file
- [ ] Implement `_run_inference()` - Run inference loop in thread
- [ ] Implement `_stop()` - Stop inference

### TASK-5.3: Create requirements.txt
- [ ] Add gymnasium>=0.29.0
- [ ] Add stable-baselines3>=2.0.0
- [ ] Add pyzmq>=25.0.0
- [ ] Add numpy>=1.24.0
- [ ] Add customtkinter>=5.0.0
- [ ] Add tensorboard (optional)

---

## File Checklist

### Unity Scripts
- [ ] `Assets/Scripts/RobotController.cs`
- [ ] `Assets/Scripts/ZMQServer.cs`
- [ ] `Assets/Scripts/LaserSensor.cs`
- [ ] `Assets/Scripts/TargetSpawner.cs`

### Unity Prefabs
- [ ] `Assets/Prefabs/Robot4DOF.prefab`
- [ ] `Assets/Prefabs/TargetBox.prefab`

### Python Files
- [ ] `Python/unity_robot_env.py`
- [ ] `Python/train.py`
- [ ] `Python/control_panel.py`
- [ ] `Python/test_client.py`
- [ ] `Python/requirements.txt`

---

## Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| 1 | 5 | 0 | 0% |
| 2 | 4 | 0 | 0% |
| 3 | 5 | 0 | 0% |
| 4 | 4 | 0 | 0% |
| 5 | 3 | 0 | 0% |
| **Total** | **21** | **0** | **0%** |

---

## Completion Criteria

All phases must be complete with:

1. **Phase 1**: Robot moves correctly in Unity Inspector
2. **Phase 2**: test_client.py can control robot and receive observations
3. **Phase 3**: Gymnasium env passes `gym.utils.env_checker.check_env()`
4. **Phase 4**: PPO agent learns to touch target (avg reward > 50)
5. **Phase 5**: Control panel can run trained model in simulation mode

---

## Notes for Code Generation Agent

1. **Normalization is critical** - All inputs to neural network must be [-1, 1]
2. **Blocking communication** - Python waits for Unity response (determinism)
3. **Physics at 50Hz** - `Time.fixedDeltaTime = 0.02f`
4. **Collision = episode end** - Penalty of -100, done=True
5. **Target orientation matters** - One-hot encoding changes approach strategy
