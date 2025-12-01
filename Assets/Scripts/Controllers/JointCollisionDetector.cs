using UnityEngine;
using RobotSimulation.Enums;
using RobotSimulation.Events;

namespace RobotSimulation.Controllers
{
    /// <summary>
    /// Detects collisions on individual robot joints and reports them to the main RobotController.
    /// This component should be attached to each joint of the robot to detect self-collisions.
    /// </summary>
    public class JointCollisionDetector : MonoBehaviour
    {
        private RobotController _robotController;

        public void Initialize(RobotController robotController)
        {
            _robotController = robotController;
        }

        private void OnCollisionEnter(Collision collisionInfo)
        {
            if (_robotController == null)
            {
                return;
            }

            string collidedObjectTag = collisionInfo.gameObject.name;

            // Check if this is a self-collision (collision with another part of the robot)
            if (IsRobotPart(collisionInfo.gameObject))
            {
                // Report self-collision as Environment collision (penalty)
                CollisionEvents.RaiseCollisionDetected(CollisionType.Environment, "SelfCollision");
                _robotController.RegisterSelfCollision();
                Debug.LogWarning($"JointCollisionDetector: Self-collision detected on {gameObject.name} with {collisionInfo.gameObject.name}");
            }
            else
            {
                // Report other collisions
                CollisionType detectedCollisionType = DetermineCollisionType(collidedObjectTag);
                CollisionEvents.RaiseCollisionDetected(detectedCollisionType, collidedObjectTag);
                
                if (detectedCollisionType == CollisionType.Environment)
                {
                    _robotController.RegisterEnvironmentCollision();
                }
            }
        }

        private bool IsRobotPart(GameObject obj)
        {
            // Check if the collided object is part of the robot hierarchy
            return obj.GetComponentInParent<RobotController>() != null;
        }

        private CollisionType DetermineCollisionType(string objectTag)
        {
            if (objectTag == "Target")
            {
                return CollisionType.Target;
            }

            return CollisionType.Environment;
        }
    }
}
