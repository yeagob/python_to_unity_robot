using System;
using RobotSimulation.Enums;

namespace RobotSimulation.Events
{
    public static class CollisionEvents
    {
        public static event Action<CollisionType, string> OnCollisionDetected;

        public static void RaiseCollisionDetected(CollisionType collisionType, string collidedObjectTag)
        {
            if (OnCollisionDetected != null)
            {
                OnCollisionDetected.Invoke(collisionType, collidedObjectTag);
            }
        }
    }
}
