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
        private bool _axis6IsHorizontal;

        private static readonly float[] JOINT_ANGLE_LIMITS = new float[] { 90.0f, 90.0f, 90.0f, 180.0f, 90.0f, 90.0f };

        public RobotControlMode CurrentControlMode => _currentControlMode;

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
            _targetJointAngles = new float[6];
            _currentControlMode = RobotControlMode.Training;
            _axis6IsHorizontal = false;
        }

        public void Initialize(ConfigurationModel configuration)
        {
            _configuration = configuration;
            ConfigureArticulationDrives();
        }

        public void SetJointPositionsInstantaneous(float[] anglesInDegrees)
        {
            int jointCount = Mathf.Min(anglesInDegrees.Length, _jointArticulationBodies.Length);

            for (int jointIndex = 0; jointIndex < jointCount; jointIndex++)
            {
                float clampedAngle = ClampJointAngle(anglesInDegrees[jointIndex], jointIndex);

                ArticulationDrive articulationDrive = _jointArticulationBodies[jointIndex].xDrive;
                articulationDrive.target = clampedAngle;
                _jointArticulationBodies[jointIndex].xDrive = articulationDrive;

                ArticulationReducedSpace jointPosition = new ArticulationReducedSpace(
                    clampedAngle * Mathf.Deg2Rad);
                _jointArticulationBodies[jointIndex].jointPosition = jointPosition;
            }
        }

        public void SetJointPositionsInterpolated(float[] anglesInDegrees)
        {
            int jointCount = Mathf.Min(anglesInDegrees.Length, _targetJointAngles.Length);

            for (int jointIndex = 0; jointIndex < jointCount; jointIndex++)
            {
                _targetJointAngles[jointIndex] = ClampJointAngle(anglesInDegrees[jointIndex], jointIndex);
            }
        }

        public void SetGripperState(bool shouldClose)
        {
            float targetPosition = shouldClose
                ? _configuration.GripperClosedPositionMeters
                : _configuration.GripperOpenPositionMeters;

            if (_gripperLeftArticulationBody != null)
            {
                ArticulationDrive leftGripperDrive = _gripperLeftArticulationBody.xDrive;
                leftGripperDrive.target = targetPosition;
                _gripperLeftArticulationBody.xDrive = leftGripperDrive;
            }

            if (_gripperRightArticulationBody != null)
            {
                ArticulationDrive rightGripperDrive = _gripperRightArticulationBody.xDrive;
                rightGripperDrive.target = targetPosition;
                _gripperRightArticulationBody.xDrive = rightGripperDrive;
            }
        }

        public void SetAxis6Orientation(bool isHorizontal)
        {
            _axis6IsHorizontal = isHorizontal;

            if (_jointArticulationBodies.Length >= 6)
            {
                float targetAngle = isHorizontal ? 90.0f : 0.0f;
                ArticulationDrive axis6Drive = _jointArticulationBodies[5].xDrive;
                axis6Drive.target = targetAngle;
                _jointArticulationBodies[5].xDrive = axis6Drive;

                if (_currentControlMode == RobotControlMode.Training)
                {
                    ArticulationReducedSpace jointPosition = new ArticulationReducedSpace(
                        targetAngle * Mathf.Deg2Rad);
                    _jointArticulationBodies[5].jointPosition = jointPosition;
                }
            }
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
            float[] homeAngles = new float[] { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
            SetJointPositionsInstantaneous(homeAngles);
            SetGripperState(false);
            _axis6IsHorizontal = false;

            for (int jointIndex = 0; jointIndex < _jointArticulationBodies.Length; jointIndex++)
            {
                _targetJointAngles[jointIndex] = 0.0f;
            }
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
            if (_gripperLeftArticulationBody == null)
            {
                return 1.0f;
            }

            float currentPosition = _gripperLeftArticulationBody.jointPosition[0];
            float openPosition = _configuration.GripperOpenPositionMeters;

            if (openPosition <= 0.0f)
            {
                return 0.0f;
            }

            return Mathf.Clamp01(currentPosition / openPosition);
        }

        private bool CheckIsGrippingObject()
        {
            float gripperPercentage = GetGripperOpenPercentage();
            return gripperPercentage < 0.3f;
        }

        private float ClampJointAngle(float angle, int jointIndex)
        {
            if (jointIndex >= JOINT_ANGLE_LIMITS.Length)
            {
                return angle;
            }

            float limit = JOINT_ANGLE_LIMITS[jointIndex];
            return Mathf.Clamp(angle, -limit, limit);
        }
    }
}
