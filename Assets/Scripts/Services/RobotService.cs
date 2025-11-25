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
                ArticulationBody joint = _jointArticulationBodies[jointIndex];

                // Skip joints without 1 DOF (e.g., Fixed joints)
                if (joint.jointType != ArticulationJointType.RevoluteJoint || joint.dofCount != 1)
                {
                    Debug.LogWarning($"RobotService: Skipping joint {jointIndex} - not a single-DOF revolute joint (type: {joint.jointType}, dof: {joint.dofCount})");
                    continue;
                }

                float clampedAngle = ClampJointAngle(anglesInDegrees[jointIndex], jointIndex);

                ArticulationDrive articulationDrive = joint.xDrive;
                articulationDrive.target = clampedAngle;
                joint.xDrive = articulationDrive;

                ArticulationReducedSpace jointPosition = new ArticulationReducedSpace(
                    clampedAngle * Mathf.Deg2Rad);
                joint.jointPosition = jointPosition;
            }
        }

        public void SetJointPositionsInterpolated(float[] anglesInDegrees)
        {
            int jointCount = Mathf.Min(anglesInDegrees.Length, _targetJointAngles.Length);

            for (int jointIndex = 0; jointIndex < jointCount; jointIndex++)
            {
                // Skip joints without 1 DOF
                if (jointIndex < _jointArticulationBodies.Length && _jointArticulationBodies[jointIndex].dofCount != 1)
                {
                    continue;
                }

                _targetJointAngles[jointIndex] = ClampJointAngle(anglesInDegrees[jointIndex], jointIndex);
            }
        }

        public void SetGripperState(bool shouldClose)
        {
            float targetPosition = shouldClose
                ? _configuration.GripperClosedPositionMeters
                : _configuration.GripperOpenPositionMeters;

            if (_gripperLeftArticulationBody != null && _gripperLeftArticulationBody.dofCount >= 1)
            {
                ArticulationDrive leftGripperDrive = _gripperLeftArticulationBody.xDrive;
                leftGripperDrive.target = targetPosition;
                _gripperLeftArticulationBody.xDrive = leftGripperDrive;
            }

            if (_gripperRightArticulationBody != null && _gripperRightArticulationBody.dofCount >= 1)
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
                ArticulationBody axis6Joint = _jointArticulationBodies[5];

                // Skip if not a 1-DOF revolute joint
                if (axis6Joint.jointType != ArticulationJointType.RevoluteJoint || axis6Joint.dofCount != 1)
                {
                    return;
                }

                float targetAngle = isHorizontal ? 90.0f : 0.0f;
                ArticulationDrive axis6Drive = axis6Joint.xDrive;
                axis6Drive.target = targetAngle;
                axis6Joint.xDrive = axis6Drive;

                if (_currentControlMode == RobotControlMode.Training)
                {
                    ArticulationReducedSpace jointPosition = new ArticulationReducedSpace(
                        targetAngle * Mathf.Deg2Rad);
                    axis6Joint.jointPosition = jointPosition;
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
                ArticulationBody joint = _jointArticulationBodies[jointIndex];

                // Skip joints without 1 DOF
                if (joint.dofCount != 1)
                {
                    currentAngles[jointIndex] = 0.0f;
                    continue;
                }

                float angleInRadians = joint.jointPosition[0];
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
                ArticulationBody joint = _jointArticulationBodies[jointIndex];

                // Skip joints without 1 DOF
                if (joint.dofCount != 1)
                {
                    continue;
                }

                ArticulationDrive articulationDrive = joint.xDrive;

                float interpolatedTarget = Mathf.MoveTowards(
                    articulationDrive.target,
                    _targetJointAngles[jointIndex],
                    _configuration.MaximumServoSpeedDegreesPerSecond * Time.fixedDeltaTime);

                articulationDrive.target = interpolatedTarget;
                articulationDrive.stiffness = _configuration.ArticulationDriveStiffness;
                articulationDrive.damping = _configuration.ArticulationDriveDamping;

                joint.xDrive = articulationDrive;
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
                // Skip joints without 1 DOF
                if (jointBody.dofCount != 1)
                {
                    continue;
                }

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

            // Check if gripper has valid DOF
            if (_gripperLeftArticulationBody.dofCount < 1)
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

        public float[] GetJointAngleLimits()
        {
            return (float[])JOINT_ANGLE_LIMITS.Clone();
        }
    }
}
