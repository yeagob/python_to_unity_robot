using System;
using RobotSimulation.Models;

namespace RobotSimulation.Services.Interfaces
{
    public interface INetworkService
    {
        bool IsConnected { get; }

        event Action<CommandModel> OnCommandReceived;

        void Initialize(int portNumber);
        void SendObservation(ObservationModel observation);
        void Shutdown();
        bool TryReceiveCommand(out CommandModel command);
        void SendResponse(string jsonResponse);
    }
}
