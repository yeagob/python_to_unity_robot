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
            return config;
        }
    }
}
