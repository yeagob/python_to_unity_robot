using System;
using System.Threading;
using System.Collections.Concurrent;
using UnityEngine;
using RobotSimulation.Models;
using RobotSimulation.Services.Interfaces;

namespace RobotSimulation.Services
{
    public sealed class ZeroMQNetworkService : INetworkService
    {
        private Thread _networkThread;
        private ConcurrentQueue<string> _incomingRequestQueue;
        private ConcurrentQueue<string> _outgoingResponseQueue;
        private volatile bool _isRunning;
        private int _portNumber;

        public bool IsConnected => _isRunning;

        public event Action<CommandModel> OnCommandReceived;

        public ZeroMQNetworkService()
        {
            _incomingRequestQueue = new ConcurrentQueue<string>();
            _outgoingResponseQueue = new ConcurrentQueue<string>();
            _isRunning = false;
        }

        public void Initialize(int portNumber)
        {
            _portNumber = portNumber;
            _isRunning = true;
            _networkThread = new Thread(ExecuteNetworkLoop)
            {
                IsBackground = true
            };
            _networkThread.Start();
            Debug.Log($"ZeroMQNetworkService: Starting on port {portNumber}");
        }

        public void SendObservation(ObservationModel observation)
        {
            string serializedObservation = observation.ToJson();
            _outgoingResponseQueue.Enqueue(serializedObservation);
        }

        public void Shutdown()
        {
            _isRunning = false;

            if (_networkThread != null && _networkThread.IsAlive)
            {
                _networkThread.Join(1000);
            }

            Debug.Log("ZeroMQNetworkService: Shutdown complete");
        }

        public bool TryReceiveCommand(out CommandModel command)
        {
            command = null;

            if (_incomingRequestQueue.TryDequeue(out string requestJson))
            {
                try
                {
                    command = CommandModel.FromJson(requestJson);
                    return true;
                }
                catch (Exception ex)
                {
                    Debug.LogError($"ZeroMQNetworkService: Failed to parse command: {ex.Message}");
                    return false;
                }
            }

            return false;
        }

        public void SendResponse(string jsonResponse)
        {
            _outgoingResponseQueue.Enqueue(jsonResponse);
        }

        private void ExecuteNetworkLoop()
        {
            // NOTE: This implementation requires NetMQ package to be installed in Unity
            // Install via NuGet or download from: https://github.com/zeromq/netmq
            //
            // When NetMQ is installed, uncomment the following code:
            /*
            AsyncIO.ForceDotNet.Force();

            using (var responseSocket = new NetMQ.Sockets.ResponseSocket())
            {
                string bindAddress = $"tcp://*:{_portNumber}";
                responseSocket.Bind(bindAddress);

                while (_isRunning)
                {
                    bool didReceiveRequest = responseSocket.TryReceiveFrameString(
                        TimeSpan.FromMilliseconds(100),
                        out string receivedRequest);

                    if (didReceiveRequest)
                    {
                        _incomingRequestQueue.Enqueue(receivedRequest);
                        WaitForAndSendResponse(responseSocket);
                    }
                }
            }

            NetMQ.NetMQConfig.Cleanup();
            */

            // Placeholder loop - simulates network waiting
            while (_isRunning)
            {
                Thread.Sleep(100);

                // Process any pending responses (for testing without NetMQ)
                while (_outgoingResponseQueue.TryDequeue(out string response))
                {
                    // Response would be sent here
                }
            }
        }

        /*
        private void WaitForAndSendResponse(NetMQ.Sockets.ResponseSocket socket)
        {
            while (!_outgoingResponseQueue.TryDequeue(out string responseToSend))
            {
                Thread.Sleep(1);

                if (!_isRunning)
                {
                    return;
                }
            }

            socket.SendFrame(responseToSend);
        }
        */
    }
}
