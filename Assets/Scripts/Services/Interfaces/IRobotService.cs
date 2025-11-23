using RobotSimulation.Enums;
using RobotSimulation.Models;

namespace RobotSimulation.Services.Interfaces
{
    public interface IRobotService
    {
        RobotControlMode CurrentControlMode { get; }

        void Initialize(ConfigurationModel configuration);
        void SetJointPositionsInstantaneous(float[] anglesInDegrees);
        void SetJointPositionsInterpolated(float[] anglesInDegrees);
        void SetGripperState(bool shouldClose);
        void SetAxis6Orientation(bool isHorizontal);
        RobotStateModel GetCurrentState();
        float[] GetCurrentJointAngles();
        void ResetToHomePosition();
        void UpdatePhysicsStep();
        void SetControlMode(RobotControlMode controlMode);
    }
}
