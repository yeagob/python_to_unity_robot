using UnityEngine;
using RobotSimulation.Enums;
using RobotSimulation.Events;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Controllers
{
    public sealed class RobotController : MonoBehaviour
    {
        [Header("Articulation Body References")]
        [SerializeField] private ArticulationBody _rootArticulationBody;
        [SerializeField] private ArticulationBody[] _jointArticulationBodies;
        [SerializeField] private ArticulationBody _gripperLeftArticulationBody;
        [SerializeField] private ArticulationBody _gripperRightArticulationBody;
        [SerializeField] private Transform _toolCenterPointTransform;

        private IRobotService _robotService;
        private bool _collisionDetectedThisFrame;
        private CollisionType _lastCollisionType;

        public IRobotService RobotService => _robotService;

        public bool CollisionDetectedThisFrame => _collisionDetectedThisFrame;

        public CollisionType LastCollisionType => _lastCollisionType;

        public void InitializeController(IRobotService robotService)
        {
            _robotService = robotService;
            _collisionDetectedThisFrame = false;
            _lastCollisionType = CollisionType.None;

            ConfigureSelfCollisionIgnoring();
        }

        public void PerformFixedUpdate()
        {
            if (_robotService != null)
            {
                _robotService.UpdatePhysicsStep();
            }
        }

        public void ResetCollisionState()
        {
            _collisionDetectedThisFrame = false;
            _lastCollisionType = CollisionType.None;
        }

        public ArticulationBody[] GetJointArticulationBodies()
        {
            return _jointArticulationBodies;
        }

        public ArticulationBody GetGripperLeftArticulationBody()
        {
            return _gripperLeftArticulationBody;
        }

        public ArticulationBody GetGripperRightArticulationBody()
        {
            return _gripperRightArticulationBody;
        }

        public Transform GetToolCenterPointTransform()
        {
            return _toolCenterPointTransform;
        }

        private void OnCollisionEnter(Collision collisionInfo)
        {
            string collidedObjectTag = collisionInfo.gameObject.tag;
            CollisionType detectedCollisionType = DetermineCollisionType(collidedObjectTag);

            if (detectedCollisionType == CollisionType.Environment)
            {
                _collisionDetectedThisFrame = true;
                _lastCollisionType = detectedCollisionType;
                CollisionEvents.RaiseCollisionDetected(detectedCollisionType, collidedObjectTag);
            }
        }

        private CollisionType DetermineCollisionType(string objectTag)
        {
            if (objectTag == "Target")
            {
                return CollisionType.Target;
            }

            return CollisionType.Environment;
        }

        private void ConfigureSelfCollisionIgnoring()
        {
            Collider[] allColliders = GetComponentsInChildren<Collider>();

            for (int firstIndex = 0; firstIndex < allColliders.Length; firstIndex++)
            {
                for (int secondIndex = firstIndex + 1; secondIndex < allColliders.Length; secondIndex++)
                {
                    Physics.IgnoreCollision(allColliders[firstIndex], allColliders[secondIndex], true);
                }
            }
        }
    }
}
