using UnityEngine;
using RobotSimulation.Enums;

namespace RobotSimulation.Models
{
    [System.Serializable]
    public sealed class CommandModel
    {
        public string Type;
        public float[] Actions;
        public float GripperCloseValue;
        public float Axis6Orientation;
        public bool SimulationModeEnabled;

        public CommandType GetCommandType()
        {
            switch (Type)
            {
                case "STEP":
                    return CommandType.Step;
                case "RESET":
                    return CommandType.Reset;
                case "CONFIG":
                    return CommandType.Configuration;
                default:
                    return CommandType.Step;
            }
        }

        public static CommandModel FromJson(string json)
        {
            return JsonUtility.FromJson<CommandModel>(json);
        }
    }
}
