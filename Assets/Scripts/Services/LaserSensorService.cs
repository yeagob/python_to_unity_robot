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

        public bool HasDetectedObject => _hasDetectedObject;

        public float DetectedDistance => _detectedDistance;

        public string DetectedObjectTag => _detectedObjectTag;

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
            if (_sensorOriginTransform == null)
            {
                _hasDetectedObject = false;
                _detectedDistance = _maximumDetectionRange;
                _detectedObjectTag = string.Empty;
                return;
            }

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
