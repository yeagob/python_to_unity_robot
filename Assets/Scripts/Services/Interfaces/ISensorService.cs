using UnityEngine;

namespace RobotSimulation.Services.Interfaces
{
    public interface ISensorService
    {
        bool HasDetectedObject { get; }
        float DetectedDistance { get; }
        string DetectedObjectTag { get; }

        void Initialize(Transform sensorOrigin, float maximumRange);
        void PerformSensorUpdate();
    }
}
