# Implementation Guide: 6-DOF Robot RL System

## Overview

This document provides instructions for implementing the Python-Unity robot arm simulation system for Reinforcement Learning training.

## Architecture

```
┌─────────────────────┐                    ┌─────────────────────┐
│     PYTHON          │                    │      UNITY 3D       │
│  (RL Agent/Brain)   │                    │   (Physics Engine)  │
├─────────────────────┤                    ├─────────────────────┤
│  Gymnasium Env      │◄──── ZeroMQ ─────►│  ArticulationBody   │
│  PPO Agent          │    REQ-REP/JSON    │  6-DOF Robot        │
│  Control Panel UI   │     Port 5555      │  Laser Sensor       │
└─────────────────────┘                    └─────────────────────┘
```

---

## Part 1: Unity Setup

### Step 1: Install Required Packages

1. Open **Window > Package Manager**
2. Install NetMQ via NuGet or download from: https://github.com/zeromq/netmq
   - Download `NetMQ.dll` and `AsyncIO.dll`
   - Place in `Assets/Plugins/`

### Step 2: Create Robot Hierarchy

Create a 6-DOF robot using ArticulationBody components:

```
Robot6DOF (Root ArticulationBody)
├── Base (ArticulationBody - Y rotation, ±90°)
│   └── Shoulder (ArticulationBody - X rotation, ±90°)
│       └── Elbow (ArticulationBody - X rotation, ±90°)
│           └── WristRotation (ArticulationBody - X rotation, ±180°)
│               └── WristBend (ArticulationBody - Z rotation, ±90°)
│                   └── GripperBase (ArticulationBody - X rotation, 0°/90°)
│                       ├── GripperLeft (ArticulationBody - Prismatic)
│                       ├── GripperRight (ArticulationBody - Prismatic)
│                       └── TCP (Transform - Tool Center Point)
```

### Step 3: Configure ArticulationBody Joints

For each joint:
1. Set **Articulation Joint Type** to **Revolute** (or **Prismatic** for grippers)
2. Configure **Drive**:
   - Stiffness: `10000`
   - Damping: `100`
   - Force Limit: `1000`
3. Set **Motion** limits:
   - Base: Lower=-90, Upper=90
   - Shoulder: Lower=-90, Upper=90
   - Elbow: Lower=-90, Upper=90
   - WristRotation: Lower=-180, Upper=180
   - WristBend: Lower=-90, Upper=90
   - GripperOrientation: Lower=0, Upper=90

### Step 4: Setup Scene

1. Create an empty GameObject named `GameManager`
2. Add the `GameManager.cs` script from `Assets/Scripts/Bootstrap/`
3. Create child objects for controllers:
   - Add `RobotController.cs` to the robot root
   - Add `SensorController.cs` to TCP
   - Add `TargetController.cs` to GameManager

4. Assign references in Inspector:
   - **GameManager**: Drag RobotController, SensorController, TargetController
   - **RobotController**: Assign joint ArticulationBodies array, gripper bodies, TCP transform
   - **SensorController**: Assign TCP as sensor origin
   - **TargetController**: Create a target prefab (cube), assign robot base transform

### Step 5: Create Target Prefab

1. Create a small cube (0.03m x 0.03m x 0.03m)
2. Add Rigidbody component
3. Set tag to "Target"
4. Save as prefab in `Assets/Prefabs/`

### Step 6: Enable NetMQ in ZeroMQNetworkService

Open `Assets/Scripts/Services/ZeroMQNetworkService.cs` and uncomment the NetMQ code:

```csharp
// Uncomment this code after installing NetMQ
AsyncIO.ForceDotNet.Force();

using (var responseSocket = new NetMQ.Sockets.ResponseSocket())
{
    // ... rest of the code
}
```

---

## Part 2: Python Setup

### Step 1: Install Dependencies

```bash
cd python
pip install -r requirements.txt
```

Required packages:
- gymnasium>=0.29.0
- stable-baselines3>=2.0.0
- pyzmq>=25.0.0
- numpy>=1.24.0
- customtkinter>=5.0.0
- tensorboard>=2.14.0

### Step 2: Run Tests

```bash
cd python
python -m pytest tests/ -v
```

All 35 tests should pass.

### Step 3: Test Connection (Mock)

```bash
cd python
python test_connection.py
```

This tests all Python components without needing Unity.

---

## Part 3: Running the System

### Option A: Training Mode

1. **Start Unity**:
   - Open the project in Unity
   - Press Play

2. **Start Training**:
   ```bash
   cd python
   python train.py
   ```

Training will proceed through three curriculum phases:
- **Touch** (100K steps): Learn to reach the target
- **Grasp** (200K steps): Learn to grip the target
- **Pick & Place** (500K steps): Full manipulation task

Models are saved to `python/models/` and checkpoints to `python/checkpoints/`.

### Option B: Inference Mode (Control Panel)

1. **Start Unity** (Press Play)

2. **Launch Control Panel**:
   ```bash
   cd python
   python -m ui.control_panel
   ```

3. **Use the UI**:
   - Click "Connect to Unity"
   - Click "Load Trained Model" (after training)
   - Click "Execute Trajectory" to run inference
   - Toggle "Simulation Mode" for smooth movement

---

## Part 4: Observation & Action Spaces

### Observation Space (17 dimensions)

| Index | Component | Range |
|-------|-----------|-------|
| 0-5 | Joint angles (normalized) | [-1, 1] |
| 6 | Gripper state | [0, 1] |
| 7-9 | TCP position (normalized) | [-1, 1] |
| 10-12 | Direction to target | [-1, 1] |
| 13 | Laser distance (normalized) | [0, 1] |
| 14 | Is gripping flag | {0, 1} |
| 15-16 | Target orientation (one-hot) | {0, 1} |

### Action Space (7 dimensions)

| Index | Component | Raw Range | Effect |
|-------|-----------|-----------|--------|
| 0-4 | Joint deltas | [-1, 1] | × 10° per step |
| 5 | Axis 6 orientation | [-1, 1] | <0=vertical, ≥0=horizontal |
| 6 | Gripper command | [-1, 1] | >0.5 = close |

---

## Part 5: Reward Function

Total reward per step:

$$R_{total} = R_{dist} + R_{align} + R_{grasp} + R_{penalty}$$

| Component | Formula | Typical Range |
|-----------|---------|---------------|
| R_dist | (prev_distance - current_distance) × 10 | [-5, +5] |
| R_align | velocity · direction × 0.5 | [-0.5, +0.5] |
| R_grasp | +100 when grasping target | {0, 100} |
| R_penalty | -100 on collision | {-100, 0} |

---

## Troubleshooting

### Unity: "NetMQ not found"
- Download NetMQ NuGet package
- Extract DLLs to `Assets/Plugins/`
- Restart Unity

### Python: "Connection timeout"
- Ensure Unity is running with Play mode active
- Check port 5555 is not blocked by firewall
- Verify GameManager is in the scene

### Training: "Reward not improving"
- Check that targets are spawning (visible in Unity)
- Verify laser sensor is pointing forward from TCP
- Ensure collision detection is working

### Performance: "Slow training"
- Set Unity to run in background (Edit > Project Settings > Player)
- Use headless mode for faster training
- Reduce physics quality if needed

---

## File Structure

```
python_to_unity_robot/
├── Assets/Scripts/
│   ├── Bootstrap/GameManager.cs
│   ├── Controllers/{Robot,Sensor,Target}Controller.cs
│   ├── Enums/{RobotControlMode,CommandType,CollisionType}.cs
│   ├── Events/{Collision,Robot}Events.cs
│   ├── Models/{RobotState,Observation,Command,Configuration}Model.cs
│   └── Services/
│       ├── Interfaces/I{Robot,Network,Sensor,Target}Service.cs
│       ├── RobotService.cs
│       ├── LaserSensorService.cs
│       ├── RandomTargetService.cs
│       └── ZeroMQNetworkService.cs
├── python/
│   ├── enums/command_type.py
│   ├── models/{observation,command,reward}_model.py
│   ├── services/{network,reward_calculation}_service.py
│   ├── environments/unity_robot_environment.py
│   ├── controllers/training_controller.py
│   ├── ui/control_panel.py
│   ├── tests/test_{models,reward,environment}.py
│   ├── train.py
│   ├── test_connection.py
│   └── requirements.txt
└── openspec/
    └── specs/{system,robot-interface,communication}.md
```

---

## Next Steps

1. Create robot prefab in Unity with ArticulationBody hierarchy
2. Install NetMQ package and enable ZeroMQ code
3. Test connection with `python test_connection.py`
4. Run training with `python train.py`
5. Monitor with TensorBoard: `tensorboard --logdir=./tensorboard_logs/`
