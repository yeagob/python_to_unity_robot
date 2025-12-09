using UnityEngine;

namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class ObservationModel
    {
        public float[] JointAngles;
        public float[] ToolCenterPointPosition;
        public float[] DirectionToTarget;
        public float DistanceToTarget;
        public float GripperState;
        public bool IsGrippingObject;
        public bool LaserSensorHit;
        public float LaserSensorDistance;
        public bool CollisionDetected;
        public float[] TargetOrientationOneHot;
        public bool IsResetFrame;
        public float[] JointAngleLimits;  // Upper limits (for backward compatibility)
        public float[] JointAngleLowerLimits;  // Lower limits (for asymmetric joints)

        public ObservationModel()
        {
            JointAngles = new float[6];
            ToolCenterPointPosition = new float[3];
            DirectionToTarget = new float[3];
            TargetOrientationOneHot = new float[2];
            JointAngleLimits = null;  // Only populated on reset frames
            JointAngleLowerLimits = null;  // Only populated on reset frames
        }

        public string ToJson()
        {
            return JsonUtility.ToJson(this);
        }

        public static ObservationModel FromJson(string json)
        {
            return JsonUtility.FromJson<ObservationModel>(json);
        }
    }
}
