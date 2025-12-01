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

            // Attach collision detectors to all joints
            AttachCollisionDetectorsToJoints();
        }

        public void PerformFixedUpdate()
        {
            if (_robotService != null)
            {
                _jointArticulationBodies[0].enabled = true;
                _robotService.UpdatePhysicsStep();
            }
        }

        public void ResetCollisionState()
        {
            _collisionDetectedThisFrame = false;
            _lastCollisionType = CollisionType.None;
        }

        public void RegisterSelfCollision()
        {
            _collisionDetectedThisFrame = true;
            _lastCollisionType = CollisionType.Environment;
        }

        public void RegisterEnvironmentCollision()
        {
            _collisionDetectedThisFrame = true;
            _lastCollisionType = CollisionType.Environment;
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

            // Always raise the event for logging/debugging
            CollisionEvents.RaiseCollisionDetected(detectedCollisionType, collidedObjectTag);

            // Only set the flag for Environment collisions (penalties)
            if (detectedCollisionType == CollisionType.Environment)
            {
                _collisionDetectedThisFrame = true;
                _lastCollisionType = detectedCollisionType;
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

        private void AttachCollisionDetectorsToJoints()
        {
            // Attach collision detector to root
            if (_rootArticulationBody != null)
            {
                JointCollisionDetector detector = _rootArticulationBody.gameObject.AddComponent<JointCollisionDetector>();
                detector.Initialize(this);
            }

            // Attach collision detectors to all joints
            foreach (ArticulationBody joint in _jointArticulationBodies)
            {
                if (joint != null)
                {
                    JointCollisionDetector detector = joint.gameObject.AddComponent<JointCollisionDetector>();
                    detector.Initialize(this);
                }
            }

            // Attach to grippers
            if (_gripperLeftArticulationBody != null)
            {
                JointCollisionDetector detector = _gripperLeftArticulationBody.gameObject.AddComponent<JointCollisionDetector>();
                detector.Initialize(this);
            }

            if (_gripperRightArticulationBody != null)
            {
                JointCollisionDetector detector = _gripperRightArticulationBody.gameObject.AddComponent<JointCollisionDetector>();
                detector.Initialize(this);
            }

            Debug.Log("RobotController: Collision detectors attached to all joints for self-collision detection.");
        }
    }
}
