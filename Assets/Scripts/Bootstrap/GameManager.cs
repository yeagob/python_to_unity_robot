using UnityEngine;
using RobotSimulation.Controllers;
using RobotSimulation.Enums;
using RobotSimulation.Events;
using RobotSimulation.Models;
using RobotSimulation.Services;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Bootstrap
{

    public class GameManager : MonoBehaviour
    {
        [System.Serializable]
        private class ConfigurationResponse
        {
            public string status;
        }

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
            Debug.Log("GameManager: Initialization complete");
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

            _networkService = new TcpNetworkService();
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
            int numJoints = currentJointAngles.Length;
            float[] newJointAngles = new float[numJoints];

            int actionCount = Mathf.Min(command.Actions != null ? command.Actions.Length : 0, Mathf.Min(5, numJoints));
            for (int jointIndex = 0; jointIndex < actionCount; jointIndex++)
            {
                newJointAngles[jointIndex] = currentJointAngles[jointIndex] + command.Actions[jointIndex];
            }

            // Copy remaining angles unchanged
            for (int jointIndex = actionCount; jointIndex < numJoints; jointIndex++)
            {
                newJointAngles[jointIndex] = currentJointAngles[jointIndex];
            }

            if (_currentControlMode == RobotControlMode.Training)
            {
                _robotService.SetJointPositionsInstantaneous(newJointAngles);
            }
            else
            {
                _robotService.SetJointPositionsInterpolated(newJointAngles);
            }

            // Handle Axis 6 orientation (discrete)
            bool axis6Horizontal = command.Axis6Orientation >= 0.5f;
            _robotService.SetAxis6Orientation(axis6Horizontal);

            // Handle gripper
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
            _currentControlMode = command.SimulationModeEnabled
                ? RobotControlMode.Simulation
                : RobotControlMode.Training;

            _robotService.SetControlMode(_currentControlMode);

            ConfigurationResponse response = new ConfigurationResponse { status = "ok" };
            string responseJson = JsonUtility.ToJson(response);
            _networkService.SendResponse(responseJson);

            Debug.Log($"GameManager: Mode changed to {_currentControlMode}");
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
                IsResetFrame = isResetFrame,
                JointAngleLimits = isResetFrame ? _robotService.GetJointAngleLimits() : null
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
            Debug.Log($"GameManager: Collision detected - {collisionType} with {objectTag}");
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
