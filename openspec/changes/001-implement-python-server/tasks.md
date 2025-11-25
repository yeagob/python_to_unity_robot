# Implementation Tasks: 4-DOF Robotic System with RL

**Change ID:** 001
**Last Updated:** 2025-11-25
**Status:** Implemented (Phases 1-4 Complete)

---

## Phase Overview

### TASK-1.1: Create 4-DOF Robot with ArticulationBody ✅
- [x] Create Base GameObject with ArticulationBody (Fixed type)
- [x] Create Axis1 child with ArticulationBody (Revolute Y, -180° to +180°)
- [x] Create Axis2 child with ArticulationBody (Revolute X, -90° to +90°)
- [x] Create Axis3 child with ArticulationBody (Revolute X, -135° to +135°)
- [x] Create Axis4 child with ArticulationBody (Revolute Z/X, -180° to +180°)
- [x] Add Wrist and GripperBase transforms
- [x] Create Gripper with two opposed ArticulationBody fingers (Prismatic)
- [x] Configure ArticulationDrive parameters (stiffness, damping)
- [x] Add visual meshes to each segment
- [x] Configure self-collision ignoring between adjacent segments

**References:** SYSTEM-002, SYSTEM-003

### TASK-1.2: Implement RobotController.cs ✅
- [x] Create `RobotController` MonoBehaviour
- [x] Implement `SetJointPositionsInstant()` for training mode (teleport)
- [x] Implement `SetJointPositionsSmooth()` for simulation mode (interpolation)
- [x] Implement `SetGripper(bool closed)` for gripper control
- [x] Implement `GetState()` returning `RobotState` struct
- [x] Implement `GetJointAngles()` for current joint positions
- [x] Add `ControlMode` enum (Training, Simulation)
- [x] Implement `OnCollisionEnter()` for collision detection
- [x] Add `ResetCollisionFlag()` method

**References:** INTERFACE-001, INTERFACE-002
**Implementation:** `Assets/Scripts/Controllers/RobotController.cs`

### TASK-1.3: Implement LaserSensor.cs ✅
- [x] Create `LaserSensor` MonoBehaviour
- [x] Implement Raycast from TCP `transform.forward`
- [x] Return `LaserData` struct (hit, distance, tag)
- [x] Add configurable max distance
- [x] Add debug visualization (Gizmos line)

**References:** SYSTEM-002
**Implementation:** `Assets/Scripts/Controllers/SensorController.cs`, `Assets/Scripts/Services/LaserSensorService.cs`

### TASK-1.4: Implement TargetSpawner.cs ✅
- [x] Create `TargetSpawner` MonoBehaviour
- [x] Implement random position in hemisphere (min/max radius, height)
- [x] Implement random orientation (vertical/horizontal)
- [x] Track `currentTarget` transform
- [x] Track `isVertical` flag for observation
- [x] Add "Target" tag to spawned objects
- [x] Implement `SpawnRandomTarget()` method

**References:** SYSTEM-001
**Implementation:** `Assets/Scripts/Controllers/TargetController.cs`, `Assets/Scripts/Services/RandomTargetService.cs`

### TASK-1.5: Manual Testing ✅
- [x] Control joints from Unity Inspector
- [x] Verify ArticulationBody physics stability
- [x] Test gripper open/close
- [x] Verify laser sensor detection
- [x] Test target spawning in valid positions

---

## Phase 2: The Connection (TCP Bridge) ✅

### TASK-2.1: Verify Built-in Dependencies ✅
- [x] Verify Unity uses System.Net.Sockets (built-in)
- [x] Verify Python socket module (built-in)
- [x] No external dependencies required

### TASK-2.2: Implement TcpNetworkService.cs ✅
- [x] Create `TcpNetworkService` class
- [x] Implement `TcpListener` on dedicated thread
- [x] Implement `ConcurrentQueue<string>` for request/response
- [x] Implement `NetworkLoop()` with length-prefixed message handling
- [x] Process commands in `FixedUpdate()` (main thread)
- [x] Implement `ProcessRequest()` JSON parsing
- [x] Implement `HandleStep()` for STEP commands
- [x] Implement `HandleReset()` for RESET commands
- [x] Implement `HandleConfig()` for CONFIG commands
- [x] Implement `BuildObservation()` for response data
- [x] Set `Time.fixedDeltaTime = 0.02f` (50Hz)
- [x] Implement proper cleanup in `Shutdown()`

**References:** COMM-001, COMM-002, COMM-004
**Implementation:** `Assets/Scripts/Services/TcpNetworkService.cs`, `Assets/Scripts/Bootstrap/GameManager.cs`

### TASK-2.3: Define Message Structures ✅
- [x] Create `Command` class (type, actions, gripperClose, simulationMode)
- [x] Create `Observation` class (all 15 observation fields)
- [x] Ensure proper JSON serialization attributes

**References:** COMM-002
**Implementation:** `Assets/Scripts/Models/CommandModel.cs`, `Assets/Scripts/Models/ObservationModel.cs`

### TASK-2.4: Create test_connection.py ✅
- [x] Implement basic TCP socket connection
- [x] Implement length-prefixed message sending/receiving
- [x] Send random STEP commands
- [x] Verify Unity responds with observation data
- [x] Test RESET command
- [x] Test CONFIG command (mode switching)
- [x] Print received observations for debugging

**Implementation:** `python/test_connection.py`

---

## Phase 3: The Gym Environment (Python) ✅

### TASK-3.1: Create UnityRobotEnv Class ✅
- [x] Create `unity_robot_env.py` file
- [x] Inherit from `gym.Env`
- [x] Define `observation_space` (Box, 15 dims, -1 to 1)
- [x] Define `action_space` (Box, 5 dims, -1 to 1)
- [x] Define joint limits for normalization

**References:** INTERFACE-003
**Implementation:** `python/environments/unity_robot_environment.py`

### TASK-3.2: Implement TCP Communication ✅
- [x] Implement `_setup_tcp()` for socket initialization
- [x] Implement `_send_command()` for length-prefixed JSON send/receive
- [x] Add timeout handling (5 seconds)
- [x] Add error handling for connection issues

**References:** COMM-001, COMM-003
**Implementation:** `python/services/network_service.py`

### TASK-3.3: Implement Observation Processing ✅
- [x] Implement `_process_observation()` method
- [x] Normalize joint angles by limits
- [x] Normalize TCP position by workspace
- [x] Pass through normalized direction vector
- [x] Normalize laser distance
- [x] Include gripper state, gripping flag
- [x] Include target orientation one-hot encoding
- [x] Clip all values to [-1, 1]

**References:** INTERFACE-003
**Implementation:** `python/environments/unity_robot_environment.py` (`_normalize_observation()`)

### TASK-3.4: Implement Reward Function ✅
- [x] Implement `_calculate_reward()` method
- [x] Calculate `R_dist`: Distance improvement reward
- [x] Calculate `R_align`: Velocity alignment with target direction
- [x] Calculate `R_grasp`: Grasp success reward (+100)
- [x] Calculate `R_penalty`: Collision penalty (-100)
- [x] Return reward, done flag, info dict

**References:** Design document Section 3.2
**Implementation:** `python/services/reward_calculation_service.py`

### TASK-3.5: Implement Gym Interface ✅
- [x] Implement `step(action)` method
- [x] Scale actions by max_delta
- [x] Send STEP command to Unity
- [x] Process observation and calculate reward
- [x] Handle truncation (max steps)
- [x] Implement `reset()` method
- [x] Send RESET command to Unity
- [x] Initialize prev_distance and prev_tcp_position
- [x] Implement `close()` method
- [x] Implement `set_simulation_mode()` helper

**Implementation:** `python/environments/unity_robot_environment.py`

---

## Phase 4: Training (RL Loop) ✅

### TASK-4.1: Create Training Script ✅
- [x] Create `train.py` file
- [x] Implement `make_env()` factory function
- [x] Create `DummyVecEnv` wrapper
- [x] Add `VecNormalize` for observation/reward normalization
- [x] Configure `CheckpointCallback` for saving

**Implementation:** `python/train.py`, `python/controllers/training_controller.py`

### TASK-4.2: Configure PPO ✅
- [x] Set learning_rate = 3e-4
- [x] Set n_steps = 2048
- [x] Set batch_size = 64
- [x] Set n_epochs = 10
- [x] Set gamma = 0.99
- [x] Set gae_lambda = 0.95
- [x] Set clip_range = 0.2
- [x] Set ent_coef = 0.01
- [x] Enable TensorBoard logging

**Implementation:** `python/controllers/training_controller.py`

### TASK-4.3: Implement Curriculum Learning ✅
- [x] Define curriculum phases:
  - Lesson 1: Touch object (100K steps)
  - Lesson 2: Grasp object (200K steps)
  - Lesson 3: Pick & Place (500K steps)
- [x] Save model checkpoint after each phase
- [x] Save VecNormalize statistics

**Implementation:** `python/controllers/training_controller.py` (`_create_curriculum_phases()`)

### TASK-4.4: Training Verification ✅
- [x] Run short training session
- [x] Monitor TensorBoard metrics
- [x] Verify episode rewards increase
- [x] Check for training stability

---

## Phase 5: Control Panel & Inference ✅

### TASK-5.1: Create Control Panel UI ✅
- [x] Create `control_panel.py` file
- [x] Create `RobotControlPanel(ctk.CTk)` class
- [x] Add "Simulation Mode" checkbox
- [x] Add target position inputs (X, Y, Z)
- [x] Add "Connect" button
- [x] Add "Load Model" button
- [x] Add "Execute Trajectory" button
- [x] Add "Stop" button
- [x] Add status label

**Implementation:** `python/ui/control_panel.py`

### TASK-5.2: Implement UI Logic ✅
- [x] Implement `_connect()` - Create UnityRobotEnv
- [x] Implement `_on_mode_change()` - Send CONFIG to Unity
- [x] Implement `_load_model()` - Load PPO .zip file
- [x] Implement `_run_inference()` - Run inference loop in thread
- [x] Implement `_stop()` - Stop inference

**Implementation:** `python/ui/control_panel.py`

### TASK-5.3: Verify requirements.txt ✅
- [x] Verify gymnasium>=0.29.0
- [x] Verify stable-baselines3>=2.0.0
- [x] Verify numpy>=1.24.0
- [x] Verify customtkinter>=5.0.0
- [x] Verify tensorboard (optional)
- [x] Verify pytest>=7.0.0

---

## File Checklist

### Unity Scripts ✅
- [x] `Assets/Scripts/Controllers/RobotController.cs`
- [x] `Assets/Scripts/Services/TcpNetworkService.cs`
- [x] `Assets/Scripts/Controllers/SensorController.cs`
- [x] `Assets/Scripts/Controllers/TargetController.cs`
- [x] `Assets/Scripts/Services/LaserSensorService.cs`
- [x] `Assets/Scripts/Services/RandomTargetService.cs`
- [x] `Assets/Scripts/Services/RobotService.cs`
- [x] `Assets/Scripts/Bootstrap/GameManager.cs`

### Unity Prefabs ✅
- [x] `Assets/Prefabs/Target.prefab`
- [x] Robot prefab (configured in scene)

### Python Files ✅
- [x] `python/environments/unity_robot_environment.py`
- [x] `python/services/network_service.py`
- [x] `python/services/reward_calculation_service.py`
- [x] `python/controllers/training_controller.py`
- [x] `python/train.py`
- [x] `python/test_connection.py`
- [x] `python/requirements.txt`
- [x] `python/ui/control_panel.py`

---

## Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| 1 | 5 | 5 | 100% ✅ |
| 2 | 4 | 4 | 100% ✅ |
| 3 | 5 | 5 | 100% ✅ |
| 4 | 4 | 4 | 100% ✅ |
| 5 | 3 | 3 | 100% ✅ |
| **Total** | **21** | **21** | **100%** ✅ |

---

## Completion Criteria

All phases must be complete with:

1. **Phase 1**: Robot moves correctly in Unity Inspector ✅
2. **Phase 2**: test_connection.py can control robot and receive observations ✅
3. **Phase 3**: Gymnasium env passes `gym.utils.env_checker.check_env()` ✅
4. **Phase 4**: PPO agent learns to touch target (avg reward > 50) ✅
5. **Phase 5**: Control panel can run trained model in simulation mode ✅

---

## Notes for Code Generation Agent

1. **Normalization is critical** - All inputs to neural network must be [-1, 1] ✅
2. **Blocking communication** - Python waits for Unity response (determinism) ✅
3. **Physics at 50Hz** - `Time.fixedDeltaTime = 0.02f` ✅
4. **Collision = episode end** - Penalty of -100, done=True ✅
5. **Target orientation matters** - One-hot encoding changes approach strategy ✅


---

## Phase Overview

| Phase | Name | Status | Dependencies |
|-------|------|--------|--------------|
| 1 | The Skeleton (Unity) | Pending | None |
| 2 | The Connection (TCP Bridge) | Pending | Phase 1 |
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

## Phase 2: The Connection (TCP Bridge)

### TASK-2.1: Verify Built-in Dependencies
- [ ] Verify Unity uses System.Net.Sockets (built-in)
- [ ] Verify Python socket module (built-in)
- [ ] No external dependencies required

### TASK-2.2: Implement TcpNetworkService.cs
- [ ] Create `TcpNetworkService` class
- [ ] Implement `TcpListener` on dedicated thread
- [ ] Implement `ConcurrentQueue<string>` for request/response
- [ ] Implement `NetworkLoop()` with length-prefixed message handling
- [ ] Process commands in `FixedUpdate()` (main thread)
- [ ] Implement `ProcessRequest()` JSON parsing
- [ ] Implement `HandleStep()` for STEP commands
- [ ] Implement `HandleReset()` for RESET commands
- [ ] Implement `HandleConfig()` for CONFIG commands
- [ ] Implement `BuildObservation()` for response data
- [ ] Set `Time.fixedDeltaTime = 0.02f` (50Hz)
- [ ] Implement proper cleanup in `Shutdown()`

**References:** COMM-001, COMM-002, COMM-004

### TASK-2.3: Define Message Structures
- [ ] Create `Command` class (type, actions, gripperClose, simulationMode)
- [ ] Create `Observation` class (all 15 observation fields)
- [ ] Ensure proper JSON serialization attributes

**References:** COMM-002

### TASK-2.4: Create test_connection.py
- [ ] Implement basic TCP socket connection
- [ ] Implement length-prefixed message sending/receiving
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

### TASK-3.2: Implement TCP Communication
- [ ] Implement `_setup_tcp()` for socket initialization
- [ ] Implement `_send_command()` for length-prefixed JSON send/receive
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

### TASK-5.3: Verify requirements.txt
- [ ] Verify gymnasium>=0.29.0
- [ ] Verify stable-baselines3>=2.0.0
- [ ] Verify numpy>=1.24.0
- [ ] Verify customtkinter>=5.0.0
- [ ] Verify tensorboard (optional)
- [ ] Verify pytest>=7.0.0

---

## File Checklist

### Unity Scripts
- [ ] `Assets/Scripts/RobotController.cs`
- [ ] `Assets/Scripts/TcpNetworkService.cs`
- [ ] `Assets/Scripts/LaserSensor.cs`
- [ ] `Assets/Scripts/TargetSpawner.cs`

### Unity Prefabs
- [ ] `Assets/Prefabs/Robot4DOF.prefab`
- [ ] `Assets/Prefabs/TargetBox.prefab`

### Python Files
- [ ] `Python/unity_robot_env.py`
- [ ] `Python/train.py`
- [ ] `Python/control_panel.py`
- [ ] `Python/test_connection.py`
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
2. **Phase 2**: test_connection.py can control robot and receive observations
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
