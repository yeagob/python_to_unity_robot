# Technical Design: 4-DOF Robotic System with RL Sim-to-Real

**Version:** 1.0.0
**Change ID:** 001
**Date:** 2025-11-22
**Target:** AI Development Agent (Code Generation Agent)
**Context:** MVP Robotic Arm in Simulated Environment with Physics and Reinforcement Learning

---

## 1. System Architecture

The system follows an **Asynchronous Decoupled Client-Server Architecture**.

| Component | Role |
|-----------|------|
| **Server (Unity 3D)** | Physics simulation engine, rendering, kinematics execution |
| **Client (Python)** | Brain (RL Agent), state management, Control Panel (UI) |
| **Communication Bridge** | ZeroMQ (ZMQ) using REQ-REP pattern with JSON payloads |

**Key Principle:** Python controls the simulation "step", ensuring deterministic RL training.

### 1.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRAINING LOOP                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐                              ┌─────────────────────┐
│     PYTHON          │                              │      UNITY 3D       │
│  (RL Agent/Brain)   │                              │   (Physics Engine)  │
├─────────────────────┤                              ├─────────────────────┤
│                     │      Action + Config         │                     │
│  ┌───────────────┐  │  ─────────────────────────▶  │  ┌───────────────┐  │
│  │ PPO/SAC Agent │  │         JSON/ZMQ             │  │ ArticulationBody│ │
│  └───────────────┘  │                              │  │   4-DOF Robot  │  │
│         │           │                              │  └───────────────┘  │
│         ▼           │                              │         │           │
│  ┌───────────────┐  │                              │         ▼           │
│  │ Gymnasium Env │  │                              │  ┌───────────────┐  │
│  │ - step()      │  │      Observation + Reward    │  │ Physics Step  │  │
│  │ - reset()     │  │  ◀─────────────────────────  │  │ FixedUpdate() │  │
│  │ - reward()    │  │         JSON/ZMQ             │  └───────────────┘  │
│  └───────────────┘  │                              │         │           │
│         │           │                              │         ▼           │
│         ▼           │                              │  ┌───────────────┐  │
│  ┌───────────────┐  │                              │  │ Laser Sensor  │  │
│  │ Control Panel │  │                              │  │ (Raycast)     │  │
│  │ (CustomTkinter)│ │                              │  └───────────────┘  │
│  └───────────────┘  │                              │                     │
└─────────────────────┘                              └─────────────────────┘
         │                                                     │
         └──────────────────────┬──────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │       ZeroMQ          │
                    │   REQ-REP Pattern     │
                    │   Port: 5555          │
                    └───────────────────────┘
```

---

## 2. Unity 3D Layer (Simulation & Physics)

### 2.1 Scene Configuration and Robot Arm

**Critical Decision:** Use `ArticulationBody` instead of `Rigidbody + HingeJoint`.

> ArticulationBodies are infinitely superior for robotics in Unity due to their stability in kinematic chains and physical precision.

#### Kinematic Hierarchy

```
Base (ArticulationBody - Fixed)
└── Axis1 (ArticulationBody - Revolute Y)     ← Rotation: Yaw
    └── Axis2 (ArticulationBody - Revolute X) ← Rotation: Pitch
        └── Axis3 (ArticulationBody - Revolute X) ← Rotation: Pitch
            └── Axis4 (ArticulationBody - Revolute Z/X) ← Rotation: Roll/Pitch
                └── Wrist
                    └── GripperBase
                        ├── GripperLeft (Prismatic/Revolute)
                        └── GripperRight (Prismatic/Revolute - Opposed)
```

#### Joint Configuration

| Joint | Type | Axis | Range | Purpose |
|-------|------|------|-------|---------|
| Axis1 | Revolute | Y | -180° to +180° | Base rotation |
| Axis2 | Revolute | X | -90° to +90° | Shoulder pitch |
| Axis3 | Revolute | X | -135° to +135° | Elbow pitch |
| Axis4 | Revolute | Z/X | -180° to +180° | Wrist roll/pitch |
| Gripper | Prismatic | Local | 0 to 0.05m | Open/Close |

#### Laser Sensor (Raycast)

```csharp
// Raycast from TCP (Tool Center Point) forward
Ray ray = new Ray(tcp.position, tcp.forward);
if (Physics.Raycast(ray, out RaycastHit hit, maxDistance))
{
    // Output: bool hit, float distance, string tag
    sensorData.hit = true;
    sensorData.distance = hit.distance;
    sensorData.tag = hit.collider.tag;
}
```

### 2.2 Movement Controllers (C# Scripts)

#### RobotController.cs

```csharp
using UnityEngine;
using System.Collections.Generic;

public class RobotController : MonoBehaviour
{
    [Header("Robot Configuration")]
    public ArticulationBody rootBody;
    public ArticulationBody[] joints = new ArticulationBody[4];
    public ArticulationBody gripperLeft;
    public ArticulationBody gripperRight;
    public Transform tcp; // Tool Center Point

    [Header("Control Mode")]
    public ControlMode mode = ControlMode.Training;

    [Header("Simulation Settings")]
    public float maxServoSpeed = 90f; // degrees/second
    public float pidStiffness = 10000f;
    public float pidDamping = 100f;

    public enum ControlMode
    {
        Training,    // Instantaneous (teleport)
        Simulation   // Smooth interpolation
    }

    // ═══════════════════════════════════════════════════════════════
    // TRAINING MODE: Instantaneous movement for fast RL episodes
    // ═══════════════════════════════════════════════════════════════
    public void SetJointPositionsInstant(float[] angles)
    {
        for (int i = 0; i < joints.Length; i++)
        {
            var drive = joints[i].xDrive;
            drive.target = angles[i];
            joints[i].xDrive = drive;

            // Force immediate position (teleport)
            joints[i].jointPosition = new ArticulationReducedSpace(angles[i] * Mathf.Deg2Rad);
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // SIMULATION MODE: Smooth interpolated movement
    // ═══════════════════════════════════════════════════════════════
    private float[] targetAngles = new float[4];

    public void SetJointPositionsSmooth(float[] angles)
    {
        targetAngles = angles;
    }

    void FixedUpdate()
    {
        if (mode == ControlMode.Simulation)
        {
            for (int i = 0; i < joints.Length; i++)
            {
                var drive = joints[i].xDrive;
                float currentTarget = drive.target;
                float newTarget = Mathf.MoveTowards(
                    currentTarget,
                    targetAngles[i],
                    maxServoSpeed * Time.fixedDeltaTime
                );
                drive.target = newTarget;
                drive.stiffness = pidStiffness;
                drive.damping = pidDamping;
                joints[i].xDrive = drive;
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // GRIPPER CONTROL
    // ═══════════════════════════════════════════════════════════════
    public void SetGripper(bool closed)
    {
        float target = closed ? 0f : 0.05f; // meters

        var driveL = gripperLeft.xDrive;
        var driveR = gripperRight.xDrive;
        driveL.target = target;
        driveR.target = target;
        gripperLeft.xDrive = driveL;
        gripperRight.xDrive = driveR;
    }

    // ═══════════════════════════════════════════════════════════════
    // STATE RETRIEVAL
    // ═══════════════════════════════════════════════════════════════
    public RobotState GetState()
    {
        return new RobotState
        {
            jointAngles = GetJointAngles(),
            tcpPosition = tcp.position,
            tcpRotation = tcp.rotation,
            gripperOpen = GetGripperState(),
            isGripping = CheckGripping()
        };
    }

    public float[] GetJointAngles()
    {
        float[] angles = new float[4];
        for (int i = 0; i < joints.Length; i++)
        {
            angles[i] = joints[i].jointPosition[0] * Mathf.Rad2Deg;
        }
        return angles;
    }

    // ═══════════════════════════════════════════════════════════════
    // COLLISION HANDLING
    // ═══════════════════════════════════════════════════════════════
    [HideInInspector] public bool collisionDetected = false;
    [HideInInspector] public string collisionTag = "";

    void OnCollisionEnter(Collision collision)
    {
        if (!collision.gameObject.CompareTag("Target"))
        {
            collisionDetected = true;
            collisionTag = collision.gameObject.tag;
        }
    }

    public void ResetCollisionFlag()
    {
        collisionDetected = false;
        collisionTag = "";
    }
}

[System.Serializable]
public struct RobotState
{
    public float[] jointAngles;
    public Vector3 tcpPosition;
    public Quaternion tcpRotation;
    public float gripperOpen;
    public bool isGripping;
}
```

#### Self-Collision Configuration

```csharp
// In Awake() or Start()
void ConfigureSelfCollision()
{
    // Disable collisions between adjacent robot segments
    Collider[] allColliders = GetComponentsInChildren<Collider>();
    for (int i = 0; i < allColliders.Length - 1; i++)
    {
        Physics.IgnoreCollision(allColliders[i], allColliders[i + 1], true);
    }
}
```

### 2.3 Communication Bridge (ZMQ in C#)

**Library:** NetMQ (ZeroMQ port for .NET)

#### ZMQServer.cs

```csharp
using NetMQ;
using NetMQ.Sockets;
using UnityEngine;
using System.Threading;
using System.Collections.Concurrent;
using Newtonsoft.Json;

public class ZMQServer : MonoBehaviour
{
    [Header("Network Settings")]
    public string address = "tcp://*:5555";

    [Header("References")]
    public RobotController robot;
    public TargetSpawner targetSpawner;
    public LaserSensor laserSensor;

    private ResponseSocket server;
    private Thread serverThread;
    private ConcurrentQueue<string> requestQueue = new ConcurrentQueue<string>();
    private ConcurrentQueue<string> responseQueue = new ConcurrentQueue<string>();
    private bool isRunning = false;

    void Start()
    {
        Time.fixedDeltaTime = 0.02f; // 50Hz physics
        StartServer();
    }

    void StartServer()
    {
        isRunning = true;
        serverThread = new Thread(ServerLoop);
        serverThread.Start();
        Debug.Log($"ZMQ Server started on {address}");
    }

    void ServerLoop()
    {
        AsyncIO.ForceDotNet.Force();
        using (server = new ResponseSocket())
        {
            server.Bind(address);

            while (isRunning)
            {
                if (server.TryReceiveFrameString(System.TimeSpan.FromMilliseconds(100), out string request))
                {
                    requestQueue.Enqueue(request);

                    // Wait for response from main thread
                    while (!responseQueue.TryDequeue(out string response))
                    {
                        Thread.Sleep(1);
                        if (!isRunning) return;
                    }

                    server.SendFrame(response);
                }
            }
        }
        NetMQConfig.Cleanup();
    }

    void FixedUpdate()
    {
        if (requestQueue.TryDequeue(out string request))
        {
            string response = ProcessRequest(request);
            responseQueue.Enqueue(response);
        }
    }

    string ProcessRequest(string jsonRequest)
    {
        try
        {
            var cmd = JsonConvert.DeserializeObject<Command>(jsonRequest);

            switch (cmd.type)
            {
                case "STEP":
                    return HandleStep(cmd);
                case "RESET":
                    return HandleReset(cmd);
                case "CONFIG":
                    return HandleConfig(cmd);
                default:
                    return CreateErrorResponse($"Unknown command: {cmd.type}");
            }
        }
        catch (System.Exception e)
        {
            return CreateErrorResponse(e.Message);
        }
    }

    string HandleStep(Command cmd)
    {
        // Apply actions to robot
        float[] deltaAngles = cmd.actions;
        float[] currentAngles = robot.GetJointAngles();
        float[] newAngles = new float[4];

        for (int i = 0; i < 4; i++)
        {
            newAngles[i] = currentAngles[i] + deltaAngles[i];
        }

        if (robot.mode == RobotController.ControlMode.Training)
            robot.SetJointPositionsInstant(newAngles);
        else
            robot.SetJointPositionsSmooth(newAngles);

        // Gripper action
        robot.SetGripper(cmd.gripperClose > 0.5f);

        // Build observation response
        var obs = BuildObservation();
        return JsonConvert.SerializeObject(obs);
    }

    string HandleReset(Command cmd)
    {
        // Reset robot to home position
        robot.SetJointPositionsInstant(new float[] { 0, 0, 0, 0 });
        robot.SetGripper(false);
        robot.ResetCollisionFlag();

        // Spawn new target
        targetSpawner.SpawnRandomTarget();

        var obs = BuildObservation();
        obs.reset = true;
        return JsonConvert.SerializeObject(obs);
    }

    string HandleConfig(Command cmd)
    {
        // Set control mode
        if (cmd.simulationMode)
            robot.mode = RobotController.ControlMode.Simulation;
        else
            robot.mode = RobotController.ControlMode.Training;

        return JsonConvert.SerializeObject(new { status = "ok" });
    }

    Observation BuildObservation()
    {
        var state = robot.GetState();
        var targetPos = targetSpawner.currentTarget.position;
        var laserData = laserSensor.GetData();

        return new Observation
        {
            jointAngles = state.jointAngles,
            tcpPosition = Vec3ToArray(state.tcpPosition),
            directionToTarget = Vec3ToArray((targetPos - state.tcpPosition).normalized),
            distanceToTarget = Vector3.Distance(state.tcpPosition, targetPos),
            gripperState = state.gripperOpen,
            isGripping = state.isGripping,
            laserHit = laserData.hit,
            laserDistance = laserData.distance,
            collision = robot.collisionDetected,
            targetOrientation = targetSpawner.isVertical ? new float[]{1,0} : new float[]{0,1}
        };
    }

    float[] Vec3ToArray(Vector3 v) => new float[] { v.x, v.y, v.z };

    string CreateErrorResponse(string message)
    {
        return JsonConvert.SerializeObject(new { error = message });
    }

    void OnDestroy()
    {
        isRunning = false;
        serverThread?.Join(1000);
    }
}

// ═══════════════════════════════════════════════════════════════
// DATA STRUCTURES
// ═══════════════════════════════════════════════════════════════

[System.Serializable]
public class Command
{
    public string type;           // "STEP", "RESET", "CONFIG"
    public float[] actions;       // [delta1, delta2, delta3, delta4]
    public float gripperClose;    // 0-1
    public bool simulationMode;   // for CONFIG
}

[System.Serializable]
public class Observation
{
    public float[] jointAngles;
    public float[] tcpPosition;
    public float[] directionToTarget;
    public float distanceToTarget;
    public float gripperState;
    public bool isGripping;
    public bool laserHit;
    public float laserDistance;
    public bool collision;
    public float[] targetOrientation; // one-hot: [vertical, horizontal]
    public bool reset;
}
```

### 2.4 Target Spawner

```csharp
public class TargetSpawner : MonoBehaviour
{
    [Header("Spawn Configuration")]
    public GameObject targetPrefab;
    public Transform robotBase;
    public float minRadius = 0.2f;
    public float maxRadius = 0.5f;
    public float minHeight = 0.1f;
    public float maxHeight = 0.4f;

    [HideInInspector] public Transform currentTarget;
    [HideInInspector] public bool isVertical;

    public void SpawnRandomTarget()
    {
        if (currentTarget != null)
            Destroy(currentTarget.gameObject);

        // Random position in hemisphere
        float angle = Random.Range(0f, 360f) * Mathf.Deg2Rad;
        float radius = Random.Range(minRadius, maxRadius);
        float height = Random.Range(minHeight, maxHeight);

        Vector3 pos = robotBase.position + new Vector3(
            Mathf.Cos(angle) * radius,
            height,
            Mathf.Sin(angle) * radius
        );

        // Random orientation
        isVertical = Random.value > 0.5f;
        Quaternion rot = isVertical
            ? Quaternion.identity
            : Quaternion.Euler(90, Random.Range(0, 360), 0);

        var obj = Instantiate(targetPrefab, pos, rot);
        obj.tag = "Target";
        currentTarget = obj.transform;
    }
}
```

---

## 3. Python Layer (RL & Control)

### 3.1 Technology Stack

| Component | Library | Reason |
|-----------|---------|--------|
| RL Environment | Gymnasium | Standard RL API, custom env support |
| RL Algorithm | PPO (Proximal Policy Optimization) | Stability with continuous actions |
| RL Library | Stable Baselines3 | Production-ready implementations |
| UI Panel | CustomTkinter | Non-blocking UI integration |
| Communication | pyzmq | ZeroMQ Python bindings |

### 3.2 Gymnasium Environment Definition

#### UnityRobotEnv.py

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import zmq
import json
from typing import Tuple, Dict, Any, Optional

class UnityRobotEnv(gym.Env):
    """
    Custom Gymnasium environment for 4-DOF robot arm in Unity.
    Communicates via ZeroMQ REQ-REP pattern.
    """

    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(
        self,
        server_address: str = "tcp://localhost:5555",
        max_episode_steps: int = 500,
        render_mode: Optional[str] = None
    ):
        super().__init__()

        self.server_address = server_address
        self.max_episode_steps = max_episode_steps
        self.render_mode = render_mode
        self.current_step = 0

        # ═══════════════════════════════════════════════════════════
        # OBSERVATION SPACE (Normalized -1 to 1 or 0 to 1)
        # ═══════════════════════════════════════════════════════════
        # Total: 4 + 1 + 3 + 3 + 1 + 1 + 2 = 15 dimensions
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(15,),
            dtype=np.float32
        )

        # ═══════════════════════════════════════════════════════════
        # ACTION SPACE (Continuous)
        # ═══════════════════════════════════════════════════════════
        # 4 joint deltas + 1 gripper action
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(5,),
            dtype=np.float32
        )

        # Joint limits for normalization
        self.joint_limits = np.array([180, 90, 135, 180])  # degrees
        self.max_delta = 10.0  # max degrees per step

        # State tracking
        self.prev_distance = None
        self.prev_tcp_velocity = np.zeros(3)
        self.prev_tcp_position = np.zeros(3)

        # ZMQ Setup
        self._setup_zmq()

    def _setup_zmq(self):
        """Initialize ZeroMQ connection."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(self.server_address)
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout

    def _send_command(self, cmd: Dict) -> Dict:
        """Send command to Unity and receive response."""
        self.socket.send_string(json.dumps(cmd))
        response = self.socket.recv_string()
        return json.loads(response)

    # ═══════════════════════════════════════════════════════════════
    # OBSERVATION PROCESSING
    # ═══════════════════════════════════════════════════════════════

    def _process_observation(self, obs: Dict) -> np.ndarray:
        """Convert Unity observation to normalized numpy array."""

        # 1. Normalized joint angles (4 values)
        joints_norm = np.array(obs['jointAngles']) / self.joint_limits

        # 2. Gripper state (1 value: 0=open, 1=closed)
        gripper = np.array([obs['gripperState']])

        # 3. TCP position relative to base (3 values, normalized)
        tcp = np.array(obs['tcpPosition']) / 0.6  # workspace ~0.6m

        # 4. Direction to target (3 values, already normalized)
        direction = np.array(obs['directionToTarget'])

        # 5. Laser distance (1 value, normalized)
        laser = np.array([obs['laserDistance'] / 1.0])  # max 1m

        # 6. Is gripping flag (1 value)
        gripping = np.array([1.0 if obs['isGripping'] else 0.0])

        # 7. Target orientation one-hot (2 values)
        orientation = np.array(obs['targetOrientation'])

        # Concatenate all
        observation = np.concatenate([
            joints_norm,    # 4
            gripper,        # 1
            tcp,            # 3
            direction,      # 3
            laser,          # 1
            gripping,       # 1
            orientation     # 2
        ]).astype(np.float32)

        return np.clip(observation, -1.0, 1.0)

    # ═══════════════════════════════════════════════════════════════
    # REWARD FUNCTION
    # ═══════════════════════════════════════════════════════════════

    def _calculate_reward(self, obs: Dict) -> Tuple[float, bool, Dict]:
        """
        Calculate reward based on:
        - Distance improvement (R_dist)
        - Velocity alignment (R_align)
        - Grasp success (R_grasp)
        - Collision penalty (R_penalty)

        R_total = R_dist + R_align + R_grasp + R_penalty
        """
        reward = 0.0
        done = False
        info = {}

        current_distance = obs['distanceToTarget']
        current_tcp = np.array(obs['tcpPosition'])
        direction = np.array(obs['directionToTarget'])

        # ─────────────────────────────────────────────────────────
        # R_dist: Distance improvement reward
        # ─────────────────────────────────────────────────────────
        if self.prev_distance is not None:
            distance_delta = self.prev_distance - current_distance
            r_dist = distance_delta * 10.0  # Scale factor
            reward += r_dist
            info['r_dist'] = r_dist

        # ─────────────────────────────────────────────────────────
        # R_align: Velocity alignment with target direction
        # ─────────────────────────────────────────────────────────
        tcp_velocity = current_tcp - self.prev_tcp_position
        if np.linalg.norm(tcp_velocity) > 1e-6:
            velocity_norm = tcp_velocity / np.linalg.norm(tcp_velocity)
            alignment = np.dot(velocity_norm, direction)
            r_align = alignment * 0.5  # Reward aligned movement
            reward += r_align
            info['r_align'] = r_align

        # ─────────────────────────────────────────────────────────
        # R_grasp: Grasp success reward
        # ─────────────────────────────────────────────────────────
        if obs['laserDistance'] < 0.05 and obs['isGripping']:
            r_grasp = 100.0  # Big reward for successful grasp
            reward += r_grasp
            info['r_grasp'] = r_grasp
            info['success'] = True
            # Could set done=True here for pickup-only task

        # ─────────────────────────────────────────────────────────
        # R_penalty: Collision penalty
        # ─────────────────────────────────────────────────────────
        if obs['collision']:
            r_penalty = -100.0
            reward += r_penalty
            done = True
            info['r_penalty'] = r_penalty
            info['collision'] = True

        # Update state for next step
        self.prev_distance = current_distance
        self.prev_tcp_position = current_tcp.copy()

        return reward, done, info

    # ═══════════════════════════════════════════════════════════════
    # GYM INTERFACE
    # ═══════════════════════════════════════════════════════════════

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute one environment step."""
        self.current_step += 1

        # Scale actions
        delta_angles = action[:4] * self.max_delta  # degrees
        gripper_action = action[4]

        # Send to Unity
        cmd = {
            "type": "STEP",
            "actions": delta_angles.tolist(),
            "gripperClose": float(gripper_action)
        }
        obs = self._send_command(cmd)

        # Check for errors
        if 'error' in obs:
            raise RuntimeError(f"Unity error: {obs['error']}")

        # Process
        observation = self._process_observation(obs)
        reward, terminated, info = self._calculate_reward(obs)

        # Check truncation (max steps)
        truncated = self.current_step >= self.max_episode_steps

        return observation, reward, terminated, truncated, info

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Reset the environment."""
        super().reset(seed=seed)

        self.current_step = 0
        self.prev_distance = None
        self.prev_tcp_position = np.zeros(3)

        # Send reset to Unity
        cmd = {"type": "RESET"}
        obs = self._send_command(cmd)

        observation = self._process_observation(obs)
        self.prev_distance = obs['distanceToTarget']
        self.prev_tcp_position = np.array(obs['tcpPosition'])

        return observation, {}

    def close(self):
        """Clean up resources."""
        self.socket.close()
        self.context.term()

    def set_simulation_mode(self, smooth: bool):
        """Switch between training and simulation modes."""
        cmd = {
            "type": "CONFIG",
            "simulationMode": smooth
        }
        self._send_command(cmd)
```

### 3.3 Training Script

```python
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from unity_robot_env import UnityRobotEnv
import os

def make_env():
    return UnityRobotEnv(
        server_address="tcp://localhost:5555",
        max_episode_steps=500
    )

def train():
    # Create vectorized environment with normalization
    env = DummyVecEnv([make_env])
    env = VecNormalize(env, norm_obs=True, norm_reward=True)

    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path="./checkpoints/",
        name_prefix="robot_ppo"
    )

    # PPO Configuration
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log="./tensorboard/"
    )

    # Curriculum Learning Phases
    CURRICULUM = [
        {"name": "touch", "steps": 100_000, "reward_threshold": 50},
        {"name": "grasp", "steps": 200_000, "reward_threshold": 100},
        {"name": "pick_place", "steps": 500_000, "reward_threshold": 200},
    ]

    for phase in CURRICULUM:
        print(f"\n{'='*50}")
        print(f"CURRICULUM PHASE: {phase['name']}")
        print(f"{'='*50}\n")

        model.learn(
            total_timesteps=phase['steps'],
            callback=checkpoint_callback,
            reset_num_timesteps=False
        )

        # Save phase checkpoint
        model.save(f"models/robot_{phase['name']}")
        env.save(f"models/vecnormalize_{phase['name']}.pkl")

    print("\nTraining complete!")
    env.close()

if __name__ == "__main__":
    train()
```

### 3.4 Control Panel UI

```python
import customtkinter as ctk
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from unity_robot_env import UnityRobotEnv
import threading
import numpy as np

class RobotControlPanel(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Robot Control Panel")
        self.geometry("600x500")

        self.env = None
        self.model = None
        self.running = False

        self._create_widgets()

    def _create_widgets(self):
        # Mode Selection
        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=10, padx=10, fill="x")

        self.sim_mode_var = ctk.BooleanVar(value=False)
        self.sim_mode_check = ctk.CTkCheckBox(
            self.mode_frame,
            text="Simulation Mode (Smooth)",
            variable=self.sim_mode_var,
            command=self._on_mode_change
        )
        self.sim_mode_check.pack(pady=5)

        # Manual Target Input
        self.target_frame = ctk.CTkFrame(self)
        self.target_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.target_frame, text="Target Position:").pack()

        self.target_entries = {}
        for axis in ['X', 'Y', 'Z']:
            frame = ctk.CTkFrame(self.target_frame)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=f"{axis}:").pack(side="left")
            entry = ctk.CTkEntry(frame, width=100)
            entry.insert(0, "0.3")
            entry.pack(side="left", padx=5)
            self.target_entries[axis] = entry

        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=10, padx=10, fill="x")

        self.connect_btn = ctk.CTkButton(
            self.btn_frame,
            text="Connect",
            command=self._connect
        )
        self.connect_btn.pack(pady=5)

        self.load_btn = ctk.CTkButton(
            self.btn_frame,
            text="Load Model",
            command=self._load_model
        )
        self.load_btn.pack(pady=5)

        self.run_btn = ctk.CTkButton(
            self.btn_frame,
            text="Execute Trajectory",
            command=self._run_inference
        )
        self.run_btn.pack(pady=5)

        self.stop_btn = ctk.CTkButton(
            self.btn_frame,
            text="Stop",
            command=self._stop
        )
        self.stop_btn.pack(pady=5)

        # Status
        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected")
        self.status_label.pack(pady=10)

    def _connect(self):
        try:
            self.env = UnityRobotEnv()
            self.status_label.configure(text="Status: Connected")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")

    def _on_mode_change(self):
        if self.env:
            self.env.set_simulation_mode(self.sim_mode_var.get())

    def _load_model(self):
        try:
            self.model = PPO.load("models/robot_pick_place")
            self.status_label.configure(text="Status: Model loaded")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")

    def _run_inference(self):
        if not self.env or not self.model:
            self.status_label.configure(text="Connect and load model first")
            return

        self.running = True
        self.status_label.configure(text="Running inference...")

        def run():
            obs, _ = self.env.reset()
            while self.running:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, done, truncated, info = self.env.step(action)

                if done or truncated:
                    if info.get('success'):
                        self.status_label.configure(text="Success!")
                    break

            self.running = False

        threading.Thread(target=run, daemon=True).start()

    def _stop(self):
        self.running = False
        self.status_label.configure(text="Stopped")

if __name__ == "__main__":
    app = RobotControlPanel()
    app.mainloop()
```

---

## 4. Implementation Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: THE SKELETON (Unity)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Set up scene with ArticulationBodies (4-DOF chain)                       │
│  □ Implement Raycast laser sensor                                           │
│  □ Implement random box spawning in reachable hemisphere                    │
│  □ Manual test: Control joints from Inspector                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: THE CONNECTION (ZMQ Bridge)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Install NetMQ in Unity (via NuGet)                                       │
│  □ Install pyzmq in Python (pip install pyzmq)                              │
│  □ Create ZMQServer.cs: Listen JSON, parse, apply to motors, return state   │
│  □ Create test_client.py: Send random commands, verify Unity responds       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: THE GYM ENVIRONMENT (Python)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Create UnityRobotEnv(gym.Env) class                                      │
│  □ Implement step(): Send action → Wait ZMQ → Calculate reward → Return     │
│  □ Implement reset(): Send RESET → Unity repositions robot and object       │
│  □ Implement observation normalization                                       │
│  □ Implement reward function with R_dist, R_align, R_grasp, R_penalty       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: TRAINING (RL Loop)                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Configure PPO with MlpPolicy                                             │
│  □ Implement Curriculum Learning:                                           │
│    ├── Lesson 1: Touch object only (no grasping)                           │
│    ├── Lesson 2: Grasp object                                              │
│    └── Lesson 3: Complete Pick & Place                                     │
│  □ Train and save checkpoints                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: CONTROL PANEL & INFERENCE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Build CustomTkinter UI                                                   │
│  □ Implement "Simulation Mode" toggle (sends flag to Unity)                 │
│  □ Add sliders/inputs for manual origin/destination coordinates             │
│  □ "Execute Trajectory" button: Load .zip model, run inference loop         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Critical Notes for Code Generation Agent

### 5.1 Normalization

> **CRITICAL:** All neural network inputs must be normalized to [-1, 1] or [0, 1].

```python
# Unity returns angles in degrees (e.g., -90 to 90)
# Python must normalize:
joint_normalized = joint_degrees / joint_max_degrees
```

### 5.2 Timing & Determinism

```csharp
// Unity: Set fixed timestep
Time.fixedDeltaTime = 0.02f;  // 50Hz physics
```

```python
# Python: BLOCKING wait for Unity response
# This guarantees determinism in RL training
response = socket.recv_string()  # Blocks until Unity responds
```

### 5.3 Target Orientation Encoding

```python
# One-hot encoding in observation:
# Vertical target:   [1, 0]
# Horizontal target: [0, 1]
# This changes wrist approach strategy
```

### 5.4 Collision Handling

```csharp
// Unity: Detect non-target collisions
void OnCollisionEnter(Collision collision)
{
    if (!collision.gameObject.CompareTag("Target"))
    {
        collisionDetected = true;
    }
}
```

```python
# Python: Massive penalty + episode termination
if obs['collision']:
    reward = -100
    done = True
```

---

## 6. File Structure

```
project/
├── Unity/
│   ├── Assets/
│   │   ├── Scripts/
│   │   │   ├── RobotController.cs
│   │   │   ├── ZMQServer.cs
│   │   │   ├── LaserSensor.cs
│   │   │   └── TargetSpawner.cs
│   │   └── Prefabs/
│   │       ├── Robot4DOF.prefab
│   │       └── TargetBox.prefab
│   └── Packages/
│       └── NetMQ/
│
└── Python/
    ├── unity_robot_env.py
    ├── train.py
    ├── control_panel.py
    ├── test_client.py
    ├── models/
    │   ├── robot_touch.zip
    │   ├── robot_grasp.zip
    │   └── robot_pick_place.zip
    └── requirements.txt
```

---

**This specification is sufficient to generate the complete code for both layers. Proceed to implementation.**
