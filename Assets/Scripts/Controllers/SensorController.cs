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

        public ISensorService SensorService => _sensorService;

        public void InitializeController(ISensorService sensorService)
        {
            _sensorService = sensorService;
            _sensorService.Initialize(_sensorOriginTransform, _maximumDetectionRangeMeters);
        }

        public void PerformFixedUpdate()
        {
            if (_sensorService != null)
            {
                _sensorService.PerformSensorUpdate();
            }
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
