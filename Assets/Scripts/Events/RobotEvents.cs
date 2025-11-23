using System;
using RobotSimulation.Models;

namespace RobotSimulation.Events
{
    public static class RobotEvents
    {
        public static event Action<RobotStateModel> OnRobotStateChanged;
        public static event Action OnRobotResetCompleted;

        public static void RaiseRobotStateChanged(RobotStateModel newState)
        {
            if (OnRobotStateChanged != null)
            {
                OnRobotStateChanged.Invoke(newState);
            }
        }

        public static void RaiseRobotResetCompleted()
        {
            if (OnRobotResetCompleted != null)
            {
                OnRobotResetCompleted.Invoke();
            }
        }
    }
}
