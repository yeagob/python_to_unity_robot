using UnityEngine;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Controllers
{
    public sealed class TargetController : MonoBehaviour
    {
        [Header("Target Configuration")]
        [SerializeField] private GameObject _targetPrefab;
        [SerializeField] private Transform _robotBaseTransform;

        private ITargetService _targetService;

        public ITargetService TargetService => _targetService;

        public void InitializeController(ITargetService targetService)
        {
            _targetService = targetService;
            _targetService.Initialize(_targetPrefab, _robotBaseTransform);
        }

        public GameObject GetTargetPrefab()
        {
            return _targetPrefab;
        }

        public Transform GetRobotBaseTransform()
        {
            return _robotBaseTransform;
        }
    }
}
