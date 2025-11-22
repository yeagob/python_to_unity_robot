# Technical Design: 4-DOF Robotic System with RL Sim-to-Real

**Version:** 2.0.0
**Change ID:** 001
**Date:** 2025-11-22
**Target:** AI Development Agent (Code Generation Agent)
**Context:** MVP Robotic Arm in Simulated Environment with Physics and Reinforcement Learning

---

## Code Standards Applied

| Standard | Description |
|----------|-------------|
| Strong Typing | No `var`, explicit types everywhere |
| Naming Convention | `[SerializeField] private Type _fieldName;` |
| Encapsulation | Properties for access, private backing fields |
| Always Braces | Even single-line blocks |
| Bootstrap Pattern | GameManager centralizes initialization |
| SOLID | All five principles applied |
| MVCS | Model-View-Controller-Service architecture |
| Separate Files | One enum/class per file |
| Self-Documenting | Minimal comments, descriptive names |
| Explicit Visibility | Always specify public/private/protected |

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MVCS ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│       MODELS        │    │     CONTROLLERS     │    │      SERVICES       │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ RobotStateModel     │◄───│ RobotController     │───►│ IRobotService       │
│ ObservationModel    │    │ NetworkController   │    │ INetworkService     │
│ CommandModel        │    │ SensorController    │    │ ISensorService      │
│ ConfigurationModel  │    │ TargetController    │    │ ITargetService      │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │    GAME MANAGER     │
                           │  (Bootstrap Entry)  │
                           └─────────────────────┘
```

---

## 2. Unity Layer - File Structure

```
Assets/
├── Scripts/
│   ├── Bootstrap/
│   │   └── GameManager.cs
│   │
│   ├── Models/
│   │   ├── RobotStateModel.cs
│   │   ├── ObservationModel.cs
│   │   ├── CommandModel.cs
│   │   └── ConfigurationModel.cs
│   │
│   ├── Controllers/
│   │   ├── RobotController.cs
│   │   ├── NetworkController.cs
│   │   ├── SensorController.cs
│   │   └── TargetController.cs
│   │
│   ├── Services/
│   │   ├── Interfaces/
│   │   │   ├── IRobotService.cs
│   │   │   ├── INetworkService.cs
│   │   │   ├── ISensorService.cs
│   │   │   └── ITargetService.cs
│   │   │
│   │   ├── RobotService.cs
│   │   ├── ZeroMQNetworkService.cs
│   │   ├── LaserSensorService.cs
│   │   └── RandomTargetService.cs
│   │
│   ├── Enums/
│   │   ├── RobotControlMode.cs
│   │   ├── CommandType.cs
│   │   └── CollisionType.cs
│   │
│   └── Events/
│       ├── RobotEvents.cs
│       └── CollisionEvents.cs
│
└── Prefabs/
    ├── Robot4DOF.prefab
    └── TargetBox.prefab
```

---

## 3. Unity Code - Enums (Separate Files)

### RobotControlMode.cs
```csharp
namespace RobotSimulation.Enums
{
    public enum RobotControlMode
    {
        Training = 0,
        Simulation = 1
    }
}
```

### CommandType.cs
```csharp
namespace RobotSimulation.Enums
{
    public enum CommandType
    {
        Step = 0,
        Reset = 1,
        Configuration = 2
    }
}
```

### CollisionType.cs
```csharp
namespace RobotSimulation.Enums
{
    public enum CollisionType
    {
        None = 0,
        Target = 1,
        Environment = 2,
        Self = 3
    }
}
```

---

## 4. Unity Code - Models (Separate Files)

### RobotStateModel.cs
```csharp
using UnityEngine;

namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class RobotStateModel
    {
        [SerializeField] private float[] _jointAngles;
        [SerializeField] private Vector3 _toolCenterPointPosition;
        [SerializeField] private Quaternion _toolCenterPointRotation;
        [SerializeField] private float _gripperOpenPercentage;
        [SerializeField] private bool _isGrippingObject;

        public float[] JointAngles
        {
            get { return _jointAngles; }
            set { _jointAngles = value; }
        }

        public Vector3 ToolCenterPointPosition
        {
            get { return _toolCenterPointPosition; }
            set { _toolCenterPointPosition = value; }
        }

        public Quaternion ToolCenterPointRotation
        {
            get { return _toolCenterPointRotation; }
            set { _toolCenterPointRotation = value; }
        }

        public float GripperOpenPercentage
        {
            get { return _gripperOpenPercentage; }
            set { _gripperOpenPercentage = value; }
        }

        public bool IsGrippingObject
        {
            get { return _isGrippingObject; }
            set { _isGrippingObject = value; }
        }

        public RobotStateModel()
        {
            _jointAngles = new float[4];
            _toolCenterPointPosition = Vector3.zero;
            _toolCenterPointRotation = Quaternion.identity;
            _gripperOpenPercentage = 1.0f;
            _isGrippingObject = false;
        }
    }
}
```

### ObservationModel.cs
```csharp
namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class ObservationModel
    {
        public float[] JointAngles { get; set; }
        public float[] ToolCenterPointPosition { get; set; }
        public float[] DirectionToTarget { get; set; }
        public float DistanceToTarget { get; set; }
        public float GripperState { get; set; }
        public bool IsGrippingObject { get; set; }
        public bool LaserSensorHit { get; set; }
        public float LaserSensorDistance { get; set; }
        public bool CollisionDetected { get; set; }
        public float[] TargetOrientationOneHot { get; set; }
        public bool IsResetFrame { get; set; }

        public ObservationModel()
        {
            JointAngles = new float[4];
            ToolCenterPointPosition = new float[3];
            DirectionToTarget = new float[3];
            TargetOrientationOneHot = new float[2];
        }
    }
}
```

### CommandModel.cs
```csharp
using RobotSimulation.Enums;

namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class CommandModel
    {
        public string Type { get; set; }
        public float[] Actions { get; set; }
        public float GripperCloseValue { get; set; }
        public bool SimulationModeEnabled { get; set; }

        public CommandType GetCommandType()
        {
            switch (Type)
            {
                case "STEP":
                    return CommandType.Step;
                case "RESET":
                    return CommandType.Reset;
                case "CONFIG":
                    return CommandType.Configuration;
                default:
                    return CommandType.Step;
            }
        }
    }
}
```

### ConfigurationModel.cs
```csharp
using UnityEngine;

namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class ConfigurationModel
    {
        [SerializeField] private float _maximumServoSpeedDegreesPerSecond;
        [SerializeField] private float _articulationDriveStiffness;
        [SerializeField] private float _articulationDriveDamping;
        [SerializeField] private float _physicsTimeStepSeconds;
        [SerializeField] private int _networkPortNumber;
        [SerializeField] private float _gripperClosedPositionMeters;
        [SerializeField] private float _gripperOpenPositionMeters;

        public float MaximumServoSpeedDegreesPerSecond
        {
            get { return _maximumServoSpeedDegreesPerSecond; }
            set { _maximumServoSpeedDegreesPerSecond = value; }
        }

        public float ArticulationDriveStiffness
        {
            get { return _articulationDriveStiffness; }
            set { _articulationDriveStiffness = value; }
        }

        public float ArticulationDriveDamping
        {
            get { return _articulationDriveDamping; }
            set { _articulationDriveDamping = value; }
        }

        public float PhysicsTimeStepSeconds
        {
            get { return _physicsTimeStepSeconds; }
            set { _physicsTimeStepSeconds = value; }
        }

        public int NetworkPortNumber
        {
            get { return _networkPortNumber; }
            set { _networkPortNumber = value; }
        }

        public float GripperClosedPositionMeters
        {
            get { return _gripperClosedPositionMeters; }
            set { _gripperClosedPositionMeters = value; }
        }

        public float GripperOpenPositionMeters
        {
            get { return _gripperOpenPositionMeters; }
            set { _gripperOpenPositionMeters = value; }
        }

        public static ConfigurationModel CreateDefault()
        {
            return new ConfigurationModel
            {
                _maximumServoSpeedDegreesPerSecond = 90.0f,
                _articulationDriveStiffness = 10000.0f,
                _articulationDriveDamping = 100.0f,
                _physicsTimeStepSeconds = 0.02f,
                _networkPortNumber = 5555,
                _gripperClosedPositionMeters = 0.0f,
                _gripperOpenPositionMeters = 0.05f
            };
        }
    }
}
```

---

## 5. Unity Code - Service Interfaces

### IRobotService.cs
```csharp
using RobotSimulation.Enums;
using RobotSimulation.Models;

namespace RobotSimulation.Services.Interfaces
{
    public interface IRobotService
    {
        RobotControlMode CurrentControlMode { get; }

        void Initialize(ConfigurationModel configuration);
        void SetJointPositionsInstantaneous(float[] anglesInDegrees);
        void SetJointPositionsInterpolated(float[] anglesInDegrees);
        void SetGripperState(bool shouldClose);
        RobotStateModel GetCurrentState();
        float[] GetCurrentJointAngles();
        void ResetToHomePosition();
        void UpdatePhysicsStep();
    }
}
```

### INetworkService.cs
```csharp
using System;
using RobotSimulation.Models;

namespace RobotSimulation.Services.Interfaces
{
    public interface INetworkService
    {
        bool IsConnected { get; }

        event Action<CommandModel> OnCommandReceived;

        void Initialize(int portNumber);
        void SendObservation(ObservationModel observation);
        void Shutdown();
        bool TryReceiveCommand(out CommandModel command);
        void SendResponse(string jsonResponse);
    }
}
```

### ISensorService.cs
```csharp
namespace RobotSimulation.Services.Interfaces
{
    public interface ISensorService
    {
        bool HasDetectedObject { get; }
        float DetectedDistance { get; }
        string DetectedObjectTag { get; }

        void Initialize(UnityEngine.Transform sensorOrigin, float maximumRange);
        void PerformSensorUpdate();
    }
}
```

### ITargetService.cs
```csharp
using UnityEngine;

namespace RobotSimulation.Services.Interfaces
{
    public interface ITargetService
    {
        Transform CurrentTargetTransform { get; }
        bool IsTargetOrientationVertical { get; }

        void Initialize(GameObject targetPrefab, Transform robotBaseTransform);
        void SpawnNewRandomTarget();
        void DestroyCurrentTarget();
    }
}
```

---

## 6. Unity Code - Service Implementations

### RobotService.cs
```csharp
using UnityEngine;
using RobotSimulation.Enums;
using RobotSimulation.Models;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class RobotService : IRobotService
    {
        private readonly ArticulationBody[] _jointArticulationBodies;
        private readonly ArticulationBody _gripperLeftArticulationBody;
        private readonly ArticulationBody _gripperRightArticulationBody;
        private readonly Transform _toolCenterPointTransform;

        private ConfigurationModel _configuration;
        private RobotControlMode _currentControlMode;
        private float[] _targetJointAngles;

        public RobotControlMode CurrentControlMode
        {
            get { return _currentControlMode; }
        }

        public RobotService(
            ArticulationBody[] jointBodies,
            ArticulationBody gripperLeft,
            ArticulationBody gripperRight,
            Transform toolCenterPoint)
        {
            _jointArticulationBodies = jointBodies;
            _gripperLeftArticulationBody = gripperLeft;
            _gripperRightArticulationBody = gripperRight;
            _toolCenterPointTransform = toolCenterPoint;
            _targetJointAngles = new float[4];
            _currentControlMode = RobotControlMode.Training;
        }

        public void Initialize(ConfigurationModel configuration)
        {
            _configuration = configuration;
            ConfigureArticulationDrives();
        }

        public void SetJointPositionsInstantaneous(float[] anglesInDegrees)
        {
            for (int jointIndex = 0; jointIndex < _jointArticulationBodies.Length; jointIndex++)
            {
                ArticulationDrive articulationDrive = _jointArticulationBodies[jointIndex].xDrive;
                articulationDrive.target = anglesInDegrees[jointIndex];
                _jointArticulationBodies[jointIndex].xDrive = articulationDrive;

                ArticulationReducedSpace jointPosition = new ArticulationReducedSpace(
                    anglesInDegrees[jointIndex] * Mathf.Deg2Rad);
                _jointArticulationBodies[jointIndex].jointPosition = jointPosition;
            }
        }

        public void SetJointPositionsInterpolated(float[] anglesInDegrees)
        {
            for (int jointIndex = 0; jointIndex < anglesInDegrees.Length; jointIndex++)
            {
                _targetJointAngles[jointIndex] = anglesInDegrees[jointIndex];
            }
        }

        public void SetGripperState(bool shouldClose)
        {
            float targetPosition = shouldClose
                ? _configuration.GripperClosedPositionMeters
                : _configuration.GripperOpenPositionMeters;

            ArticulationDrive leftGripperDrive = _gripperLeftArticulationBody.xDrive;
            ArticulationDrive rightGripperDrive = _gripperRightArticulationBody.xDrive;

            leftGripperDrive.target = targetPosition;
            rightGripperDrive.target = targetPosition;

            _gripperLeftArticulationBody.xDrive = leftGripperDrive;
            _gripperRightArticulationBody.xDrive = rightGripperDrive;
        }

        public RobotStateModel GetCurrentState()
        {
            RobotStateModel stateModel = new RobotStateModel
            {
                JointAngles = GetCurrentJointAngles(),
                ToolCenterPointPosition = _toolCenterPointTransform.position,
                ToolCenterPointRotation = _toolCenterPointTransform.rotation,
                GripperOpenPercentage = GetGripperOpenPercentage(),
                IsGrippingObject = CheckIsGrippingObject()
            };

            return stateModel;
        }

        public float[] GetCurrentJointAngles()
        {
            float[] currentAngles = new float[_jointArticulationBodies.Length];

            for (int jointIndex = 0; jointIndex < _jointArticulationBodies.Length; jointIndex++)
            {
                float angleInRadians = _jointArticulationBodies[jointIndex].jointPosition[0];
                currentAngles[jointIndex] = angleInRadians * Mathf.Rad2Deg;
            }

            return currentAngles;
        }

        public void ResetToHomePosition()
        {
            float[] homeAngles = new float[] { 0.0f, 0.0f, 0.0f, 0.0f };
            SetJointPositionsInstantaneous(homeAngles);
            SetGripperState(false);
        }

        public void UpdatePhysicsStep()
        {
            if (_currentControlMode != RobotControlMode.Simulation)
            {
                return;
            }

            for (int jointIndex = 0; jointIndex < _jointArticulationBodies.Length; jointIndex++)
            {
                ArticulationDrive articulationDrive = _jointArticulationBodies[jointIndex].xDrive;

                float interpolatedTarget = Mathf.MoveTowards(
                    articulationDrive.target,
                    _targetJointAngles[jointIndex],
                    _configuration.MaximumServoSpeedDegreesPerSecond * Time.fixedDeltaTime);

                articulationDrive.target = interpolatedTarget;
                articulationDrive.stiffness = _configuration.ArticulationDriveStiffness;
                articulationDrive.damping = _configuration.ArticulationDriveDamping;

                _jointArticulationBodies[jointIndex].xDrive = articulationDrive;
            }
        }

        public void SetControlMode(RobotControlMode controlMode)
        {
            _currentControlMode = controlMode;
        }

        private void ConfigureArticulationDrives()
        {
            foreach (ArticulationBody jointBody in _jointArticulationBodies)
            {
                ArticulationDrive drive = jointBody.xDrive;
                drive.stiffness = _configuration.ArticulationDriveStiffness;
                drive.damping = _configuration.ArticulationDriveDamping;
                jointBody.xDrive = drive;
            }
        }

        private float GetGripperOpenPercentage()
        {
            float currentPosition = _gripperLeftArticulationBody.jointPosition[0];
            float openPosition = _configuration.GripperOpenPositionMeters;
            return currentPosition / openPosition;
        }

        private bool CheckIsGrippingObject()
        {
            return false;
        }
    }
}
```

### LaserSensorService.cs
```csharp
using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class LaserSensorService : ISensorService
    {
        private Transform _sensorOriginTransform;
        private float _maximumDetectionRange;
        private bool _hasDetectedObject;
        private float _detectedDistance;
        private string _detectedObjectTag;

        public bool HasDetectedObject
        {
            get { return _hasDetectedObject; }
        }

        public float DetectedDistance
        {
            get { return _detectedDistance; }
        }

        public string DetectedObjectTag
        {
            get { return _detectedObjectTag; }
        }

        public void Initialize(Transform sensorOrigin, float maximumRange)
        {
            _sensorOriginTransform = sensorOrigin;
            _maximumDetectionRange = maximumRange;
            _hasDetectedObject = false;
            _detectedDistance = maximumRange;
            _detectedObjectTag = string.Empty;
        }

        public void PerformSensorUpdate()
        {
            Ray sensorRay = new Ray(
                _sensorOriginTransform.position,
                _sensorOriginTransform.forward);

            RaycastHit raycastHitInfo;
            bool raycastDidHit = Physics.Raycast(
                sensorRay,
                out raycastHitInfo,
                _maximumDetectionRange);

            if (raycastDidHit)
            {
                _hasDetectedObject = true;
                _detectedDistance = raycastHitInfo.distance;
                _detectedObjectTag = raycastHitInfo.collider.tag;
            }
            else
            {
                _hasDetectedObject = false;
                _detectedDistance = _maximumDetectionRange;
                _detectedObjectTag = string.Empty;
            }
        }
    }
}
```

### RandomTargetService.cs
```csharp
using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class RandomTargetService : ITargetService
    {
        private GameObject _targetPrefab;
        private Transform _robotBaseTransform;
        private GameObject _currentTargetInstance;
        private bool _isCurrentTargetVertical;

        private const float MINIMUM_SPAWN_RADIUS = 0.2f;
        private const float MAXIMUM_SPAWN_RADIUS = 0.5f;
        private const float MINIMUM_SPAWN_HEIGHT = 0.1f;
        private const float MAXIMUM_SPAWN_HEIGHT = 0.4f;
        private const string TARGET_TAG = "Target";

        public Transform CurrentTargetTransform
        {
            get
            {
                if (_currentTargetInstance == null)
                {
                    return null;
                }
                return _currentTargetInstance.transform;
            }
        }

        public bool IsTargetOrientationVertical
        {
            get { return _isCurrentTargetVertical; }
        }

        public void Initialize(GameObject targetPrefab, Transform robotBaseTransform)
        {
            _targetPrefab = targetPrefab;
            _robotBaseTransform = robotBaseTransform;
        }

        public void SpawnNewRandomTarget()
        {
            DestroyCurrentTarget();

            Vector3 spawnPosition = CalculateRandomSpawnPosition();
            Quaternion spawnRotation = CalculateRandomSpawnRotation();

            _currentTargetInstance = Object.Instantiate(
                _targetPrefab,
                spawnPosition,
                spawnRotation);
            _currentTargetInstance.tag = TARGET_TAG;
        }

        public void DestroyCurrentTarget()
        {
            if (_currentTargetInstance != null)
            {
                Object.Destroy(_currentTargetInstance);
                _currentTargetInstance = null;
            }
        }

        private Vector3 CalculateRandomSpawnPosition()
        {
            float randomAngleRadians = Random.Range(0.0f, 360.0f) * Mathf.Deg2Rad;
            float randomRadius = Random.Range(MINIMUM_SPAWN_RADIUS, MAXIMUM_SPAWN_RADIUS);
            float randomHeight = Random.Range(MINIMUM_SPAWN_HEIGHT, MAXIMUM_SPAWN_HEIGHT);

            Vector3 offsetFromBase = new Vector3(
                Mathf.Cos(randomAngleRadians) * randomRadius,
                randomHeight,
                Mathf.Sin(randomAngleRadians) * randomRadius);

            return _robotBaseTransform.position + offsetFromBase;
        }

        private Quaternion CalculateRandomSpawnRotation()
        {
            _isCurrentTargetVertical = Random.value > 0.5f;

            if (_isCurrentTargetVertical)
            {
                return Quaternion.identity;
            }

            float randomYRotation = Random.Range(0.0f, 360.0f);
            return Quaternion.Euler(90.0f, randomYRotation, 0.0f);
        }
    }
}
```

---

## 7. Unity Code - Events

### CollisionEvents.cs
```csharp
using System;
using RobotSimulation.Enums;

namespace RobotSimulation.Events
{
    public static class CollisionEvents
    {
        public static event Action<CollisionType, string> OnCollisionDetected;

        public static void RaiseCollisionDetected(CollisionType collisionType, string collidedObjectTag)
        {
            if (OnCollisionDetected != null)
            {
                OnCollisionDetected.Invoke(collisionType, collidedObjectTag);
            }
        }
    }
}
```

### RobotEvents.cs
```csharp
using System;
using RobotSimulation.Models;

namespace RobotSimulation.Events
{
    public static class RobotEvents
    {
        public static event Action<RobotStateModel> OnRobotStateChanged;
        public static event Action OnRobotResetCompleted;

        public static void RaiseRobotStateChanged(RobotStateModel newState)
        {
            if (OnRobotStateChanged != null)
            {
                OnRobotStateChanged.Invoke(newState);
            }
        }

        public static void RaiseRobotResetCompleted()
        {
            if (OnRobotResetCompleted != null)
            {
                OnRobotResetCompleted.Invoke();
            }
        }
    }
}
```

---

## 8. Unity Code - Controllers

### RobotController.cs
```csharp
using UnityEngine;
using RobotSimulation.Enums;
using RobotSimulation.Events;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Controllers
{
    public sealed class RobotController : MonoBehaviour
    {
        [Header("Articulation Body References")]
        [SerializeField] private ArticulationBody _rootArticulationBody;
        [SerializeField] private ArticulationBody[] _jointArticulationBodies;
        [SerializeField] private ArticulationBody _gripperLeftArticulationBody;
        [SerializeField] private ArticulationBody _gripperRightArticulationBody;
        [SerializeField] private Transform _toolCenterPointTransform;

        private IRobotService _robotService;
        private bool _collisionDetectedThisFrame;
        private CollisionType _lastCollisionType;

        public IRobotService RobotService
        {
            get { return _robotService; }
        }

        public bool CollisionDetectedThisFrame
        {
            get { return _collisionDetectedThisFrame; }
        }

        public CollisionType LastCollisionType
        {
            get { return _lastCollisionType; }
        }

        public void InitializeController(IRobotService robotService)
        {
            _robotService = robotService;
            _collisionDetectedThisFrame = false;
            _lastCollisionType = CollisionType.None;

            ConfigureSelfCollisionIgnoring();
            SubscribeToEvents();
        }

        public void PerformFixedUpdate()
        {
            _robotService.UpdatePhysicsStep();
        }

        public void ResetCollisionState()
        {
            _collisionDetectedThisFrame = false;
            _lastCollisionType = CollisionType.None;
        }

        public ArticulationBody[] GetJointArticulationBodies()
        {
            return _jointArticulationBodies;
        }

        public ArticulationBody GetGripperLeftArticulationBody()
        {
            return _gripperLeftArticulationBody;
        }

        public ArticulationBody GetGripperRightArticulationBody()
        {
            return _gripperRightArticulationBody;
        }

        public Transform GetToolCenterPointTransform()
        {
            return _toolCenterPointTransform;
        }

        private void OnCollisionEnter(Collision collisionInfo)
        {
            string collidedObjectTag = collisionInfo.gameObject.tag;
            CollisionType detectedCollisionType = DetermineCollisionType(collidedObjectTag);

            if (detectedCollisionType == CollisionType.Environment)
            {
                _collisionDetectedThisFrame = true;
                _lastCollisionType = detectedCollisionType;
                CollisionEvents.RaiseCollisionDetected(detectedCollisionType, collidedObjectTag);
            }
        }

        private CollisionType DetermineCollisionType(string objectTag)
        {
            if (objectTag == "Target")
            {
                return CollisionType.Target;
            }

            return CollisionType.Environment;
        }

        private void ConfigureSelfCollisionIgnoring()
        {
            Collider[] allColliders = GetComponentsInChildren<Collider>();

            for (int firstIndex = 0; firstIndex < allColliders.Length; firstIndex++)
            {
                for (int secondIndex = firstIndex + 1; secondIndex < allColliders.Length; secondIndex++)
                {
                    Physics.IgnoreCollision(allColliders[firstIndex], allColliders[secondIndex], true);
                }
            }
        }

        private void SubscribeToEvents()
        {
        }

        private void OnDestroy()
        {
        }
    }
}
```

### SensorController.cs
```csharp
using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Controllers
{
    public sealed class SensorController : MonoBehaviour
    {
        [Header("Sensor Configuration")]
        [SerializeField] private Transform _sensorOriginTransform;
        [SerializeField] private float _maximumDetectionRangeMeters = 1.0f;

        private ISensorService _sensorService;

        public ISensorService SensorService
        {
            get { return _sensorService; }
        }

        public void InitializeController(ISensorService sensorService)
        {
            _sensorService = sensorService;
            _sensorService.Initialize(_sensorOriginTransform, _maximumDetectionRangeMeters);
        }

        public void PerformFixedUpdate()
        {
            _sensorService.PerformSensorUpdate();
        }

        public Transform GetSensorOriginTransform()
        {
            return _sensorOriginTransform;
        }

        public float GetMaximumDetectionRange()
        {
            return _maximumDetectionRangeMeters;
        }
    }
}
```

### TargetController.cs
```csharp
using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Controllers
{
    public sealed class TargetController : MonoBehaviour
    {
        [Header("Target Configuration")]
        [SerializeField] private GameObject _targetPrefab;
        [SerializeField] private Transform _robotBaseTransform;

        private ITargetService _targetService;

        public ITargetService TargetService
        {
            get { return _targetService; }
        }

        public void InitializeController(ITargetService targetService)
        {
            _targetService = targetService;
            _targetService.Initialize(_targetPrefab, _robotBaseTransform);
        }

        public GameObject GetTargetPrefab()
        {
            return _targetPrefab;
        }

        public Transform GetRobotBaseTransform()
        {
            return _robotBaseTransform;
        }
    }
}
```

---

## 9. Unity Code - Network Service (ZeroMQ)

### ZeroMQNetworkService.cs
```csharp
using System;
using System.Threading;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;
using RobotSimulation.Models;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class ZeroMQNetworkService : INetworkService
    {
        private ResponseSocket _responseSocket;
        private Thread _networkThread;
        private ConcurrentQueue<string> _incomingRequestQueue;
        private ConcurrentQueue<string> _outgoingResponseQueue;
        private volatile bool _isRunning;
        private int _portNumber;

        public bool IsConnected
        {
            get { return _isRunning; }
        }

        public event Action<CommandModel> OnCommandReceived;

        public ZeroMQNetworkService()
        {
            _incomingRequestQueue = new ConcurrentQueue<string>();
            _outgoingResponseQueue = new ConcurrentQueue<string>();
            _isRunning = false;
        }

        public void Initialize(int portNumber)
        {
            _portNumber = portNumber;
            _isRunning = true;
            _networkThread = new Thread(ExecuteNetworkLoop);
            _networkThread.IsBackground = true;
            _networkThread.Start();
        }

        public void SendObservation(ObservationModel observation)
        {
            string serializedObservation = JsonConvert.SerializeObject(observation);
            _outgoingResponseQueue.Enqueue(serializedObservation);
        }

        public void Shutdown()
        {
            _isRunning = false;

            if (_networkThread != null && _networkThread.IsAlive)
            {
                _networkThread.Join(1000);
            }
        }

        public bool TryReceiveCommand(out CommandModel command)
        {
            command = null;
            string requestJson;

            if (_incomingRequestQueue.TryDequeue(out requestJson))
            {
                command = JsonConvert.DeserializeObject<CommandModel>(requestJson);
                return true;
            }

            return false;
        }

        public void SendResponse(string jsonResponse)
        {
            _outgoingResponseQueue.Enqueue(jsonResponse);
        }

        private void ExecuteNetworkLoop()
        {
            AsyncIO.ForceDotNet.Force();

            using (_responseSocket = new ResponseSocket())
            {
                string bindAddress = string.Format("tcp://*:{0}", _portNumber);
                _responseSocket.Bind(bindAddress);

                while (_isRunning)
                {
                    string receivedRequest;
                    bool didReceiveRequest = _responseSocket.TryReceiveFrameString(
                        TimeSpan.FromMilliseconds(100),
                        out receivedRequest);

                    if (didReceiveRequest)
                    {
                        _incomingRequestQueue.Enqueue(receivedRequest);
                        WaitForAndSendResponse();
                    }
                }
            }

            NetMQConfig.Cleanup();
        }

        private void WaitForAndSendResponse()
        {
            string responseToSend;

            while (!_outgoingResponseQueue.TryDequeue(out responseToSend))
            {
                Thread.Sleep(1);

                if (!_isRunning)
                {
                    return;
                }
            }

            _responseSocket.SendFrame(responseToSend);
        }
    }
}
```

---

## 10. Unity Code - GameManager (Bootstrap)

### GameManager.cs
```csharp
using UnityEngine;
using Newtonsoft.Json;
using RobotSimulation.Controllers;
using RobotSimulation.Enums;
using RobotSimulation.Events;
using RobotSimulation.Models;
using RobotSimulation.Services;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Bootstrap
{
    public sealed class GameManager : MonoBehaviour
    {
        [Header("Controller References")]
        [SerializeField] private RobotController _robotController;
        [SerializeField] private SensorController _sensorController;
        [SerializeField] private TargetController _targetController;

        [Header("Configuration")]
        [SerializeField] private int _networkPortNumber = 5555;
        [SerializeField] private float _physicsTimeStep = 0.02f;

        private IRobotService _robotService;
        private INetworkService _networkService;
        private ISensorService _sensorService;
        private ITargetService _targetService;
        private ConfigurationModel _configuration;
        private RobotControlMode _currentControlMode;

        private void Awake()
        {
            InitializeConfiguration();
            InitializeServices();
            InitializeControllers();
            SubscribeToEvents();
        }

        private void FixedUpdate()
        {
            ProcessNetworkCommands();
            UpdateControllers();
        }

        private void OnDestroy()
        {
            ShutdownServices();
            UnsubscribeFromEvents();
        }

        private void InitializeConfiguration()
        {
            Time.fixedDeltaTime = _physicsTimeStep;
            _configuration = ConfigurationModel.CreateDefault();
            _configuration.NetworkPortNumber = _networkPortNumber;
            _configuration.PhysicsTimeStepSeconds = _physicsTimeStep;
            _currentControlMode = RobotControlMode.Training;
        }

        private void InitializeServices()
        {
            _robotService = new RobotService(
                _robotController.GetJointArticulationBodies(),
                _robotController.GetGripperLeftArticulationBody(),
                _robotController.GetGripperRightArticulationBody(),
                _robotController.GetToolCenterPointTransform());
            _robotService.Initialize(_configuration);

            _sensorService = new LaserSensorService();

            _targetService = new RandomTargetService();

            _networkService = new ZeroMQNetworkService();
            _networkService.Initialize(_configuration.NetworkPortNumber);
        }

        private void InitializeControllers()
        {
            _robotController.InitializeController(_robotService);
            _sensorController.InitializeController(_sensorService);
            _targetController.InitializeController(_targetService);
        }

        private void ProcessNetworkCommands()
        {
            CommandModel receivedCommand;

            if (!_networkService.TryReceiveCommand(out receivedCommand))
            {
                return;
            }

            CommandType commandType = receivedCommand.GetCommandType();

            switch (commandType)
            {
                case CommandType.Step:
                    HandleStepCommand(receivedCommand);
                    break;
                case CommandType.Reset:
                    HandleResetCommand();
                    break;
                case CommandType.Configuration:
                    HandleConfigurationCommand(receivedCommand);
                    break;
            }
        }

        private void HandleStepCommand(CommandModel command)
        {
            float[] currentJointAngles = _robotService.GetCurrentJointAngles();
            float[] newJointAngles = new float[4];

            for (int jointIndex = 0; jointIndex < 4; jointIndex++)
            {
                newJointAngles[jointIndex] = currentJointAngles[jointIndex] + command.Actions[jointIndex];
            }

            if (_currentControlMode == RobotControlMode.Training)
            {
                _robotService.SetJointPositionsInstantaneous(newJointAngles);
            }
            else
            {
                _robotService.SetJointPositionsInterpolated(newJointAngles);
            }

            bool shouldCloseGripper = command.GripperCloseValue > 0.5f;
            _robotService.SetGripperState(shouldCloseGripper);

            ObservationModel observation = BuildObservationModel(false);
            _networkService.SendObservation(observation);
        }

        private void HandleResetCommand()
        {
            _robotService.ResetToHomePosition();
            _robotController.ResetCollisionState();
            _targetService.SpawnNewRandomTarget();

            ObservationModel observation = BuildObservationModel(true);
            _networkService.SendObservation(observation);

            RobotEvents.RaiseRobotResetCompleted();
        }

        private void HandleConfigurationCommand(CommandModel command)
        {
            if (command.SimulationModeEnabled)
            {
                _currentControlMode = RobotControlMode.Simulation;
            }
            else
            {
                _currentControlMode = RobotControlMode.Training;
            }

            string responseJson = JsonConvert.SerializeObject(new { status = "ok" });
            _networkService.SendResponse(responseJson);
        }

        private ObservationModel BuildObservationModel(bool isResetFrame)
        {
            RobotStateModel robotState = _robotService.GetCurrentState();
            Transform targetTransform = _targetService.CurrentTargetTransform;

            Vector3 directionToTarget = Vector3.zero;
            float distanceToTarget = 0.0f;

            if (targetTransform != null)
            {
                directionToTarget = (targetTransform.position - robotState.ToolCenterPointPosition).normalized;
                distanceToTarget = Vector3.Distance(robotState.ToolCenterPointPosition, targetTransform.position);
            }

            ObservationModel observation = new ObservationModel
            {
                JointAngles = robotState.JointAngles,
                ToolCenterPointPosition = ConvertVector3ToFloatArray(robotState.ToolCenterPointPosition),
                DirectionToTarget = ConvertVector3ToFloatArray(directionToTarget),
                DistanceToTarget = distanceToTarget,
                GripperState = robotState.GripperOpenPercentage,
                IsGrippingObject = robotState.IsGrippingObject,
                LaserSensorHit = _sensorService.HasDetectedObject,
                LaserSensorDistance = _sensorService.DetectedDistance,
                CollisionDetected = _robotController.CollisionDetectedThisFrame,
                TargetOrientationOneHot = BuildTargetOrientationOneHot(),
                IsResetFrame = isResetFrame
            };

            return observation;
        }

        private float[] ConvertVector3ToFloatArray(Vector3 vector)
        {
            return new float[] { vector.x, vector.y, vector.z };
        }

        private float[] BuildTargetOrientationOneHot()
        {
            if (_targetService.IsTargetOrientationVertical)
            {
                return new float[] { 1.0f, 0.0f };
            }

            return new float[] { 0.0f, 1.0f };
        }

        private void UpdateControllers()
        {
            _robotController.PerformFixedUpdate();
            _sensorController.PerformFixedUpdate();
        }

        private void SubscribeToEvents()
        {
            CollisionEvents.OnCollisionDetected += HandleCollisionDetected;
        }

        private void UnsubscribeFromEvents()
        {
            CollisionEvents.OnCollisionDetected -= HandleCollisionDetected;
        }

        private void HandleCollisionDetected(CollisionType collisionType, string objectTag)
        {
        }

        private void ShutdownServices()
        {
            if (_networkService != null)
            {
                _networkService.Shutdown();
            }
        }
    }
}
```

---

## 11. Python Code - Type Hints and Structure

### File Structure
```
python/
├── models/
│   ├── __init__.py
│   ├── observation_model.py
│   ├── command_model.py
│   └── reward_components.py
│
├── services/
│   ├── __init__.py
│   ├── network_service.py
│   └── reward_calculation_service.py
│
├── environments/
│   ├── __init__.py
│   └── unity_robot_environment.py
│
├── controllers/
│   ├── __init__.py
│   └── training_controller.py
│
├── enums/
│   ├── __init__.py
│   └── command_type.py
│
├── ui/
│   ├── __init__.py
│   └── control_panel.py
│
├── config.py
├── train.py
└── requirements.txt
```

---

## 12. Python Code - Enums

### enums/command_type.py
```python
from enum import Enum


class CommandType(Enum):
    STEP = "STEP"
    RESET = "RESET"
    CONFIGURATION = "CONFIG"
```

---

## 13. Python Code - Models

### models/observation_model.py
```python
from dataclasses import dataclass
from typing import List


@dataclass
class ObservationModel:
    joint_angles: List[float]
    tool_center_point_position: List[float]
    direction_to_target: List[float]
    distance_to_target: float
    gripper_state: float
    is_gripping_object: bool
    laser_sensor_hit: bool
    laser_sensor_distance: float
    collision_detected: bool
    target_orientation_one_hot: List[float]
    is_reset_frame: bool

    @classmethod
    def from_dictionary(cls, data: dict) -> "ObservationModel":
        return cls(
            joint_angles=data.get("JointAngles", [0.0, 0.0, 0.0, 0.0]),
            tool_center_point_position=data.get("ToolCenterPointPosition", [0.0, 0.0, 0.0]),
            direction_to_target=data.get("DirectionToTarget", [0.0, 0.0, 0.0]),
            distance_to_target=data.get("DistanceToTarget", 0.0),
            gripper_state=data.get("GripperState", 1.0),
            is_gripping_object=data.get("IsGrippingObject", False),
            laser_sensor_hit=data.get("LaserSensorHit", False),
            laser_sensor_distance=data.get("LaserSensorDistance", 1.0),
            collision_detected=data.get("CollisionDetected", False),
            target_orientation_one_hot=data.get("TargetOrientationOneHot", [1.0, 0.0]),
            is_reset_frame=data.get("IsResetFrame", False)
        )
```

### models/command_model.py
```python
from dataclasses import dataclass
from typing import List, Optional
from enums.command_type import CommandType


@dataclass
class CommandModel:
    command_type: CommandType
    actions: Optional[List[float]] = None
    gripper_close_value: Optional[float] = None
    simulation_mode_enabled: Optional[bool] = None

    def to_dictionary(self) -> dict:
        result: dict = {"type": self.command_type.value}

        if self.actions is not None:
            result["actions"] = self.actions

        if self.gripper_close_value is not None:
            result["gripperClose"] = self.gripper_close_value

        if self.simulation_mode_enabled is not None:
            result["simulationMode"] = self.simulation_mode_enabled

        return result
```

### models/reward_components.py
```python
from dataclasses import dataclass


@dataclass
class RewardComponents:
    distance_reward: float = 0.0
    alignment_reward: float = 0.0
    grasp_reward: float = 0.0
    collision_penalty: float = 0.0

    @property
    def total_reward(self) -> float:
        return (
            self.distance_reward
            + self.alignment_reward
            + self.grasp_reward
            + self.collision_penalty
        )
```

---

## 14. Python Code - Services

### services/network_service.py
```python
import json
import zmq
from typing import Optional
from models.command_model import CommandModel
from models.observation_model import ObservationModel


class NetworkService:
    DEFAULT_ADDRESS: str = "tcp://localhost:5555"
    DEFAULT_TIMEOUT_MILLISECONDS: int = 5000

    def __init__(self, server_address: str = DEFAULT_ADDRESS) -> None:
        self._server_address: str = server_address
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> None:
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(self._server_address)
        self._socket.setsockopt(zmq.RCVTIMEO, self.DEFAULT_TIMEOUT_MILLISECONDS)
        self._is_connected = True

    def disconnect(self) -> None:
        if self._socket is not None:
            self._socket.close()

        if self._context is not None:
            self._context.term()

        self._is_connected = False

    def send_command(self, command: CommandModel) -> ObservationModel:
        command_dictionary: dict = command.to_dictionary()
        serialized_command: str = json.dumps(command_dictionary)

        self._socket.send_string(serialized_command)

        response_string: str = self._socket.recv_string()
        response_dictionary: dict = json.loads(response_string)

        return ObservationModel.from_dictionary(response_dictionary)

    def send_raw_command(self, command_dictionary: dict) -> dict:
        serialized_command: str = json.dumps(command_dictionary)
        self._socket.send_string(serialized_command)

        response_string: str = self._socket.recv_string()
        return json.loads(response_string)
```

### services/reward_calculation_service.py
```python
import numpy as np
from typing import Tuple, Dict, Any
from models.observation_model import ObservationModel
from models.reward_components import RewardComponents


class RewardCalculationService:
    DISTANCE_REWARD_SCALE: float = 10.0
    ALIGNMENT_REWARD_SCALE: float = 0.5
    GRASP_SUCCESS_REWARD: float = 100.0
    COLLISION_PENALTY_VALUE: float = -100.0
    GRASP_DISTANCE_THRESHOLD: float = 0.05
    VELOCITY_MINIMUM_THRESHOLD: float = 1e-6

    def __init__(self) -> None:
        self._previous_distance_to_target: float = 0.0
        self._previous_tool_center_point_position: np.ndarray = np.zeros(3)
        self._is_first_step: bool = True

    def calculate_reward(
        self,
        observation: ObservationModel
    ) -> Tuple[float, bool, Dict[str, Any]]:
        reward_components: RewardComponents = RewardComponents()
        episode_terminated: bool = False
        information_dictionary: Dict[str, Any] = {}

        current_distance: float = observation.distance_to_target
        current_position: np.ndarray = np.array(observation.tool_center_point_position)
        target_direction: np.ndarray = np.array(observation.direction_to_target)

        if not self._is_first_step:
            reward_components.distance_reward = self._calculate_distance_reward(
                current_distance)

            reward_components.alignment_reward = self._calculate_alignment_reward(
                current_position, target_direction)

        reward_components.grasp_reward = self._calculate_grasp_reward(observation)

        if reward_components.grasp_reward > 0.0:
            information_dictionary["success"] = True

        collision_result: Tuple[float, bool] = self._calculate_collision_penalty(observation)
        reward_components.collision_penalty = collision_result[0]

        if collision_result[1]:
            episode_terminated = True
            information_dictionary["collision"] = True

        self._update_previous_state(current_distance, current_position)

        information_dictionary["reward_components"] = {
            "distance": reward_components.distance_reward,
            "alignment": reward_components.alignment_reward,
            "grasp": reward_components.grasp_reward,
            "collision": reward_components.collision_penalty
        }

        return reward_components.total_reward, episode_terminated, information_dictionary

    def reset_state(self, initial_observation: ObservationModel) -> None:
        self._previous_distance_to_target = initial_observation.distance_to_target
        self._previous_tool_center_point_position = np.array(
            initial_observation.tool_center_point_position)
        self._is_first_step = True

    def _calculate_distance_reward(self, current_distance: float) -> float:
        distance_improvement: float = self._previous_distance_to_target - current_distance
        return distance_improvement * self.DISTANCE_REWARD_SCALE

    def _calculate_alignment_reward(
        self,
        current_position: np.ndarray,
        target_direction: np.ndarray
    ) -> float:
        velocity_vector: np.ndarray = current_position - self._previous_tool_center_point_position
        velocity_magnitude: float = np.linalg.norm(velocity_vector)

        if velocity_magnitude < self.VELOCITY_MINIMUM_THRESHOLD:
            return 0.0

        normalized_velocity: np.ndarray = velocity_vector / velocity_magnitude
        alignment_dot_product: float = np.dot(normalized_velocity, target_direction)

        return alignment_dot_product * self.ALIGNMENT_REWARD_SCALE

    def _calculate_grasp_reward(self, observation: ObservationModel) -> float:
        is_close_to_target: bool = observation.laser_sensor_distance < self.GRASP_DISTANCE_THRESHOLD
        is_gripping: bool = observation.is_gripping_object

        if is_close_to_target and is_gripping:
            return self.GRASP_SUCCESS_REWARD

        return 0.0

    def _calculate_collision_penalty(
        self,
        observation: ObservationModel
    ) -> Tuple[float, bool]:
        if observation.collision_detected:
            return self.COLLISION_PENALTY_VALUE, True

        return 0.0, False

    def _update_previous_state(
        self,
        current_distance: float,
        current_position: np.ndarray
    ) -> None:
        self._previous_distance_to_target = current_distance
        self._previous_tool_center_point_position = current_position.copy()
        self._is_first_step = False
```

---

## 15. Python Code - Environment

### environments/unity_robot_environment.py
```python
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, Any, Optional
from models.command_model import CommandModel
from models.observation_model import ObservationModel
from enums.command_type import CommandType
from services.network_service import NetworkService
from services.reward_calculation_service import RewardCalculationService


class UnityRobotEnvironment(gym.Env):
    OBSERVATION_DIMENSION: int = 15
    ACTION_DIMENSION: int = 5
    MAXIMUM_DELTA_DEGREES: float = 10.0
    GRIPPER_CLOSE_THRESHOLD: float = 0.5
    DEFAULT_MAXIMUM_EPISODE_STEPS: int = 500

    JOINT_ANGLE_LIMITS: np.ndarray = np.array([180.0, 90.0, 135.0, 180.0])
    WORKSPACE_RADIUS_METERS: float = 0.6
    LASER_MAXIMUM_RANGE_METERS: float = 1.0

    metadata: Dict[str, Any] = {"render_modes": ["human"], "render_fps": 50}

    def __init__(
        self,
        server_address: str = "tcp://localhost:5555",
        maximum_episode_steps: int = DEFAULT_MAXIMUM_EPISODE_STEPS,
        render_mode: Optional[str] = None
    ) -> None:
        super().__init__()

        self._server_address: str = server_address
        self._maximum_episode_steps: int = maximum_episode_steps
        self._render_mode: Optional[str] = render_mode
        self._current_step_count: int = 0

        self._network_service: NetworkService = NetworkService(server_address)
        self._reward_calculation_service: RewardCalculationService = RewardCalculationService()

        self.observation_space: spaces.Box = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.OBSERVATION_DIMENSION,),
            dtype=np.float32
        )

        self.action_space: spaces.Box = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.ACTION_DIMENSION,),
            dtype=np.float32
        )

        self._network_service.connect()

    def step(
        self,
        action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self._current_step_count += 1

        scaled_joint_deltas: np.ndarray = action[:4] * self.MAXIMUM_DELTA_DEGREES
        gripper_action_value: float = float(action[4])

        step_command: CommandModel = CommandModel(
            command_type=CommandType.STEP,
            actions=scaled_joint_deltas.tolist(),
            gripper_close_value=gripper_action_value
        )

        observation_model: ObservationModel = self._network_service.send_command(step_command)
        normalized_observation: np.ndarray = self._normalize_observation(observation_model)

        reward: float
        terminated: bool
        information: Dict[str, Any]
        reward, terminated, information = self._reward_calculation_service.calculate_reward(
            observation_model)

        truncated: bool = self._current_step_count >= self._maximum_episode_steps

        return normalized_observation, reward, terminated, truncated, information

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)

        self._current_step_count = 0

        reset_command: CommandModel = CommandModel(command_type=CommandType.RESET)
        observation_model: ObservationModel = self._network_service.send_command(reset_command)

        self._reward_calculation_service.reset_state(observation_model)

        normalized_observation: np.ndarray = self._normalize_observation(observation_model)

        return normalized_observation, {}

    def close(self) -> None:
        self._network_service.disconnect()

    def set_simulation_mode(self, enable_smooth_movement: bool) -> None:
        configuration_command: CommandModel = CommandModel(
            command_type=CommandType.CONFIGURATION,
            simulation_mode_enabled=enable_smooth_movement
        )
        self._network_service.send_command(configuration_command)

    def _normalize_observation(self, observation: ObservationModel) -> np.ndarray:
        normalized_joint_angles: np.ndarray = (
            np.array(observation.joint_angles) / self.JOINT_ANGLE_LIMITS
        )

        gripper_state_array: np.ndarray = np.array([observation.gripper_state])

        normalized_tool_position: np.ndarray = (
            np.array(observation.tool_center_point_position) / self.WORKSPACE_RADIUS_METERS
        )

        direction_to_target: np.ndarray = np.array(observation.direction_to_target)

        normalized_laser_distance: np.ndarray = np.array([
            observation.laser_sensor_distance / self.LASER_MAXIMUM_RANGE_METERS
        ])

        is_gripping_array: np.ndarray = np.array([
            1.0 if observation.is_gripping_object else 0.0
        ])

        target_orientation: np.ndarray = np.array(observation.target_orientation_one_hot)

        concatenated_observation: np.ndarray = np.concatenate([
            normalized_joint_angles,
            gripper_state_array,
            normalized_tool_position,
            direction_to_target,
            normalized_laser_distance,
            is_gripping_array,
            target_orientation
        ])

        clipped_observation: np.ndarray = np.clip(
            concatenated_observation, -1.0, 1.0
        ).astype(np.float32)

        return clipped_observation
```

---

## 16. Python Code - Training

### train.py
```python
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback
from environments.unity_robot_environment import UnityRobotEnvironment
from dataclasses import dataclass
from typing import List


@dataclass
class CurriculumPhase:
    name: str
    training_steps: int
    reward_threshold: float


class TrainingController:
    LEARNING_RATE: float = 3e-4
    STEPS_PER_UPDATE: int = 2048
    BATCH_SIZE: int = 64
    TRAINING_EPOCHS: int = 10
    DISCOUNT_FACTOR: float = 0.99
    GAE_LAMBDA: float = 0.95
    CLIP_RANGE: float = 0.2
    ENTROPY_COEFFICIENT: float = 0.01
    CHECKPOINT_FREQUENCY: int = 10000

    def __init__(self, server_address: str = "tcp://localhost:5555") -> None:
        self._server_address: str = server_address
        self._environment: VecNormalize = None
        self._model: PPO = None
        self._curriculum_phases: List[CurriculumPhase] = self._create_curriculum_phases()

    def initialize_training(self) -> None:
        vectorized_environment: DummyVecEnv = DummyVecEnv([self._create_environment])
        self._environment = VecNormalize(
            vectorized_environment,
            norm_obs=True,
            norm_reward=True
        )

        self._model = PPO(
            policy="MlpPolicy",
            env=self._environment,
            learning_rate=self.LEARNING_RATE,
            n_steps=self.STEPS_PER_UPDATE,
            batch_size=self.BATCH_SIZE,
            n_epochs=self.TRAINING_EPOCHS,
            gamma=self.DISCOUNT_FACTOR,
            gae_lambda=self.GAE_LAMBDA,
            clip_range=self.CLIP_RANGE,
            ent_coef=self.ENTROPY_COEFFICIENT,
            verbose=1,
            tensorboard_log="./tensorboard_logs/"
        )

    def execute_curriculum_training(self) -> None:
        checkpoint_callback: CheckpointCallback = CheckpointCallback(
            save_freq=self.CHECKPOINT_FREQUENCY,
            save_path="./checkpoints/",
            name_prefix="robot_policy"
        )

        for phase in self._curriculum_phases:
            print(f"\n{'=' * 60}")
            print(f"CURRICULUM PHASE: {phase.name}")
            print(f"Training Steps: {phase.training_steps}")
            print(f"{'=' * 60}\n")

            self._model.learn(
                total_timesteps=phase.training_steps,
                callback=checkpoint_callback,
                reset_num_timesteps=False
            )

            model_save_path: str = f"./models/robot_policy_{phase.name}"
            normalizer_save_path: str = f"./models/normalizer_{phase.name}.pkl"

            self._model.save(model_save_path)
            self._environment.save(normalizer_save_path)

            print(f"Phase '{phase.name}' completed. Model saved.")

    def shutdown(self) -> None:
        if self._environment is not None:
            self._environment.close()

    def _create_environment(self) -> UnityRobotEnvironment:
        return UnityRobotEnvironment(
            server_address=self._server_address,
            maximum_episode_steps=500
        )

    def _create_curriculum_phases(self) -> List[CurriculumPhase]:
        return [
            CurriculumPhase(name="touch", training_steps=100_000, reward_threshold=50.0),
            CurriculumPhase(name="grasp", training_steps=200_000, reward_threshold=100.0),
            CurriculumPhase(name="pick_and_place", training_steps=500_000, reward_threshold=200.0)
        ]


def main() -> None:
    training_controller: TrainingController = TrainingController()

    try:
        training_controller.initialize_training()
        training_controller.execute_curriculum_training()
    finally:
        training_controller.shutdown()
        print("\nTraining completed successfully.")


if __name__ == "__main__":
    main()
```

---

## 17. Python Code - Control Panel

### ui/control_panel.py
```python
import threading
import customtkinter as ctk
from typing import Optional
from stable_baselines3 import PPO
from environments.unity_robot_environment import UnityRobotEnvironment


class RobotControlPanel(ctk.CTk):
    WINDOW_TITLE: str = "Robot Control Panel"
    WINDOW_GEOMETRY: str = "600x500"
    BUTTON_PADDING: int = 5
    FRAME_PADDING: int = 10

    def __init__(self) -> None:
        super().__init__()

        self._environment: Optional[UnityRobotEnvironment] = None
        self._trained_model: Optional[PPO] = None
        self._inference_thread: Optional[threading.Thread] = None
        self._is_inference_running: bool = False

        self._configure_window()
        self._create_mode_selection_frame()
        self._create_target_position_frame()
        self._create_control_buttons_frame()
        self._create_status_display()

    def _configure_window(self) -> None:
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_GEOMETRY)

    def _create_mode_selection_frame(self) -> None:
        mode_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        mode_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        self._simulation_mode_variable: ctk.BooleanVar = ctk.BooleanVar(value=False)

        simulation_mode_checkbox: ctk.CTkCheckBox = ctk.CTkCheckBox(
            mode_frame,
            text="Simulation Mode (Smooth Movement)",
            variable=self._simulation_mode_variable,
            command=self._handle_mode_change
        )
        simulation_mode_checkbox.pack(pady=self.BUTTON_PADDING)

    def _create_target_position_frame(self) -> None:
        target_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        target_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        title_label: ctk.CTkLabel = ctk.CTkLabel(target_frame, text="Target Position:")
        title_label.pack()

        self._target_position_entries: dict = {}
        axis_labels: list = ["X", "Y", "Z"]

        for axis_label in axis_labels:
            entry_frame: ctk.CTkFrame = ctk.CTkFrame(target_frame)
            entry_frame.pack(fill="x", pady=2)

            axis_name_label: ctk.CTkLabel = ctk.CTkLabel(entry_frame, text=f"{axis_label}:")
            axis_name_label.pack(side="left")

            position_entry: ctk.CTkEntry = ctk.CTkEntry(entry_frame, width=100)
            position_entry.insert(0, "0.3")
            position_entry.pack(side="left", padx=self.BUTTON_PADDING)

            self._target_position_entries[axis_label] = position_entry

    def _create_control_buttons_frame(self) -> None:
        buttons_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        buttons_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        connect_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Connect to Unity",
            command=self._handle_connect
        )
        connect_button.pack(pady=self.BUTTON_PADDING)

        load_model_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Load Trained Model",
            command=self._handle_load_model
        )
        load_model_button.pack(pady=self.BUTTON_PADDING)

        execute_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Execute Trajectory",
            command=self._handle_execute_trajectory
        )
        execute_button.pack(pady=self.BUTTON_PADDING)

        stop_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Stop Execution",
            command=self._handle_stop_execution
        )
        stop_button.pack(pady=self.BUTTON_PADDING)

    def _create_status_display(self) -> None:
        self._status_label: ctk.CTkLabel = ctk.CTkLabel(
            self,
            text="Status: Disconnected"
        )
        self._status_label.pack(pady=self.FRAME_PADDING)

    def _handle_connect(self) -> None:
        try:
            self._environment = UnityRobotEnvironment()
            self._update_status("Status: Connected to Unity")
        except Exception as connection_error:
            self._update_status(f"Connection Error: {connection_error}")

    def _handle_mode_change(self) -> None:
        if self._environment is None:
            return

        enable_simulation_mode: bool = self._simulation_mode_variable.get()
        self._environment.set_simulation_mode(enable_simulation_mode)

        mode_name: str = "Simulation" if enable_simulation_mode else "Training"
        self._update_status(f"Status: Mode changed to {mode_name}")

    def _handle_load_model(self) -> None:
        try:
            model_path: str = "./models/robot_policy_pick_and_place"
            self._trained_model = PPO.load(model_path)
            self._update_status("Status: Trained model loaded successfully")
        except Exception as load_error:
            self._update_status(f"Model Load Error: {load_error}")

    def _handle_execute_trajectory(self) -> None:
        if self._environment is None:
            self._update_status("Error: Not connected to Unity")
            return

        if self._trained_model is None:
            self._update_status("Error: No trained model loaded")
            return

        self._is_inference_running = True
        self._update_status("Status: Executing trajectory...")

        self._inference_thread = threading.Thread(
            target=self._execute_inference_loop,
            daemon=True
        )
        self._inference_thread.start()

    def _handle_stop_execution(self) -> None:
        self._is_inference_running = False
        self._update_status("Status: Execution stopped")

    def _execute_inference_loop(self) -> None:
        observation, _ = self._environment.reset()

        while self._is_inference_running:
            action, _ = self._trained_model.predict(observation, deterministic=True)
            observation, reward, terminated, truncated, info = self._environment.step(action)

            if terminated or truncated:
                if info.get("success", False):
                    self._update_status("Status: Task completed successfully!")
                else:
                    self._update_status("Status: Episode ended")
                break

        self._is_inference_running = False

    def _update_status(self, status_message: str) -> None:
        self._status_label.configure(text=status_message)


def main() -> None:
    control_panel: RobotControlPanel = RobotControlPanel()
    control_panel.mainloop()


if __name__ == "__main__":
    main()
```

---

## 18. Requirements

### requirements.txt
```
gymnasium>=0.29.0
stable-baselines3>=2.0.0
pyzmq>=25.0.0
numpy>=1.24.0
customtkinter>=5.0.0
tensorboard>=2.14.0
```

---

## 19. Critical Implementation Notes

| Aspect | Requirement |
|--------|-------------|
| Collision Penalty | Handled via `CollisionEvents` → `GameManager` → `ObservationModel.CollisionDetected` → `RewardCalculationService._calculate_collision_penalty()` |
| Type Safety | All variables explicitly typed, no `var` usage |
| Naming | `_privateField`, `PublicProperty`, full descriptive names |
| Encapsulation | Private fields with public properties throughout |
| Bootstrap | `GameManager.Awake()` initializes all services, no `Start()` usage |
| SOLID | Single responsibility per class, interfaces for dependencies |
| MVCS | Clear separation: Models, Controllers, Services |
| Braces | Always present, even single-line blocks |
