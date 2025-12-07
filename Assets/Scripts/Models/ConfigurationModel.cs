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

        [Header("Joint Anchor Rotations")]
        [Tooltip("Anchor rotations for each joint axis. These rotate the xDrive to align with the actual rotation axis.")]
        [SerializeField] private Vector3[] _jointAnchorRotations;

        public float MaximumServoSpeedDegreesPerSecond
        {
            get => _maximumServoSpeedDegreesPerSecond;
            set => _maximumServoSpeedDegreesPerSecond = value;
        }

        public float ArticulationDriveStiffness
        {
            get => _articulationDriveStiffness;
            set => _articulationDriveStiffness = value;
        }

        public float ArticulationDriveDamping
        {
            get => _articulationDriveDamping;
            set => _articulationDriveDamping = value;
        }

        public float PhysicsTimeStepSeconds
        {
            get => _physicsTimeStepSeconds;
            set => _physicsTimeStepSeconds = value;
        }

        public int NetworkPortNumber
        {
            get => _networkPortNumber;
            set => _networkPortNumber = value;
        }

        public float GripperClosedPositionMeters
        {
            get => _gripperClosedPositionMeters;
            set => _gripperClosedPositionMeters = value;
        }

        public float GripperOpenPositionMeters
        {
            get => _gripperOpenPositionMeters;
            set => _gripperOpenPositionMeters = value;
        }

        /// <summary>
        /// Gets the joint anchor rotations. Returns configured values or defaults if not set.
        /// Default values align each joint's xDrive with its actual rotation axis:
        /// - Axis 1: (0, 0, 90) - rotates to Y axis
        /// - Axis 2: (0, 90, 0) - rotates to Z axis
        /// - Axis 3: (0, 90, 0) - rotates to Z axis
        /// - Axis 4: (0, 0, 0) - uses X axis (default)
        /// - Axis 5: (270, 90, 0) - rotates to Z axis
        /// - Axis 6: (0, 0, 90) - rotates to X axis (local Z rotation of 90°)
        /// </summary>
        public Vector3[] JointAnchorRotations
        {
            get
            {
                if (_jointAnchorRotations == null || _jointAnchorRotations.Length == 0)
                {
                    return GetDefaultJointAnchorRotations();
                }
                return _jointAnchorRotations;
            }
            set => _jointAnchorRotations = value;
        }

        /// <summary>
        /// Returns the default anchor rotations for a 6-axis robot arm.
        /// These values are specific to the robot model and align each xDrive
        /// with the joint's actual rotation axis.
        /// </summary>
        public static Vector3[] GetDefaultJointAnchorRotations()
        {
            return new Vector3[]
            {
                new Vector3(0f, 0f, 90f),    // Axis 1: Y rotation
                new Vector3(0f, 90f, 0f),    // Axis 2: Z rotation
                new Vector3(0f, 90f, 0f),    // Axis 3: Z rotation
                new Vector3(0f, 0f, 0f),     // Axis 4: X rotation (default)
                new Vector3(270f, 90f, 0f),  // Axis 5: Z rotation
                new Vector3(0f, 0f, 90f)     // Axis 6: X rotation (90° local Z offset)
            };
        }

        public static ConfigurationModel CreateDefault()
        {
            ConfigurationModel config = new ConfigurationModel();
            config._maximumServoSpeedDegreesPerSecond = 90.0f;
            config._articulationDriveStiffness = 10000.0f;
            config._articulationDriveDamping = 100.0f;
            config._physicsTimeStepSeconds = 0.02f;
            config._networkPortNumber = 5555;
            config._gripperClosedPositionMeters = 0.0f;
            config._gripperOpenPositionMeters = 0.05f;
            config._jointAnchorRotations = GetDefaultJointAnchorRotations();
            return config;
        }
    }
}
