using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class RandomTargetService : ITargetService
    {
        private GameObject _targetPrefab;
        private Transform _robotBaseTransform;
        private GameObject _currentTargetInstance;
        private bool _isCurrentTargetVertical;

        private const float MINIMUM_SPAWN_RADIUS = 0.5f;
        private const float MAXIMUM_SPAWN_RADIUS = 2.5f;
        private const float MINIMUM_SPAWN_HEIGHT = 0.1f;
        private const float MAXIMUM_SPAWN_HEIGHT = 2f;
        private const string TARGET_TAG = "Target";

        public Transform CurrentTargetTransform
        {
            get
            {
                if (_currentTargetInstance != null)
                {
                    return _currentTargetInstance.transform;
                }
                return null;
            }
        }

        public bool IsTargetOrientationVertical => _isCurrentTargetVertical;

        public void Initialize(GameObject targetPrefab, Transform robotBaseTransform)
        {
            _targetPrefab = targetPrefab;
            _robotBaseTransform = robotBaseTransform;
        }

        public void SpawnNewRandomTarget()
        {
            DestroyCurrentTarget();

            if (_targetPrefab == null || _robotBaseTransform == null)
            {
                Debug.LogWarning("RandomTargetService: Missing prefab or robot base transform");
                return;
            }

            Vector3 spawnPosition = CalculateRandomSpawnPosition();
            Quaternion spawnRotation = CalculateRandomSpawnRotation();

            _currentTargetInstance = Object.Instantiate(
                _targetPrefab,
                spawnPosition,
                spawnRotation);
            _currentTargetInstance.tag = TARGET_TAG;
        }

        public void DestroyCurrentTarget()
        {
            if (_currentTargetInstance != null)
            {
                Object.Destroy(_currentTargetInstance);
                _currentTargetInstance = null;
            }
        }

        private Vector3 CalculateRandomSpawnPosition()
        {
            float randomAngleRadians = Random.Range(0.0f, 360.0f) * Mathf.Deg2Rad;
            float randomRadius = Random.Range(MINIMUM_SPAWN_RADIUS, MAXIMUM_SPAWN_RADIUS);
            float randomHeight = Random.Range(MINIMUM_SPAWN_HEIGHT, MAXIMUM_SPAWN_HEIGHT);

            Vector3 offsetFromBase = new Vector3(
                Mathf.Cos(randomAngleRadians) * randomRadius,
                randomHeight,
                Mathf.Sin(randomAngleRadians) * randomRadius);

            return _robotBaseTransform.position + offsetFromBase;
        }

        private Quaternion CalculateRandomSpawnRotation()
        {
            _isCurrentTargetVertical = Random.value > 0.5f;

            if (_isCurrentTargetVertical)
            {
                return Quaternion.identity;
            }

            float randomYRotation = Random.Range(0.0f, 360.0f);
            return Quaternion.Euler(90.0f, randomYRotation, 0.0f);
        }
    }
}
