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
            get => _jointAngles;
            set => _jointAngles = value;
        }

        public Vector3 ToolCenterPointPosition
        {
            get => _toolCenterPointPosition;
            set => _toolCenterPointPosition = value;
        }

        public Quaternion ToolCenterPointRotation
        {
            get => _toolCenterPointRotation;
            set => _toolCenterPointRotation = value;
        }

        public float GripperOpenPercentage
        {
            get => _gripperOpenPercentage;
            set => _gripperOpenPercentage = value;
        }

        public bool IsGrippingObject
        {
            get => _isGrippingObject;
            set => _isGrippingObject = value;
        }

        public RobotStateModel()
        {
            _jointAngles = new float[6];
            _toolCenterPointPosition = Vector3.zero;
            _toolCenterPointRotation = Quaternion.identity;
            _gripperOpenPercentage = 1.0f;
            _isGrippingObject = false;
        }
    }
}
