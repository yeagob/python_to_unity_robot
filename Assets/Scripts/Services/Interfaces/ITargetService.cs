using UnityEngine;

namespace RobotSimulation.Services.Interfaces
{
    public interface ITargetService
    {
        Transform CurrentTargetTransform { get; }
        bool IsTargetOrientationVertical { get; }

        void Initialize(GameObject targetPrefab, Transform robotBaseTransform);
        void SpawnNewRandomTarget();
        void DestroyCurrentTarget();
    }
}
