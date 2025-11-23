using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;
using UnityEngine;
using RobotSimulation.Models;
using RobotSimulation.Services.Interfaces;
using System.IO;

namespace RobotSimulation.Services
{
    public sealed class TcpNetworkService : INetworkService
    {
        private TcpListener _listener;
        private TcpClient _client;
        private NetworkStream _stream;
        private Thread _networkThread;
        private ConcurrentQueue<string> _incomingRequestQueue;
        private ConcurrentQueue<string> _outgoingResponseQueue;
        private volatile bool _isRunning;
        private int _portNumber;

        public bool IsConnected => _client?.Connected ?? false;

        public event Action<CommandModel> OnCommandReceived;

        public TcpNetworkService()
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
            Debug.Log($"TcpNetworkService: Listening on port {portNumber}");
        }

        public void SendObservation(ObservationModel observation)
        {
            string serializedObservation = observation.ToJson();
            _outgoingResponseQueue.Enqueue(serializedObservation);
        }

        public void Shutdown()
        {
            _isRunning = false;

            try
            {
                _client?.Close();
            }
            catch (Exception)
            {
                // Ignore errors during shutdown
            }

            try
            {
                _listener?.Stop();
            }
            catch (Exception)
            {
                // Ignore errors during shutdown
            }

            if (_networkThread != null && _networkThread.IsAlive)
            {
                _networkThread.Join(1000);
            }

            Debug.Log("TcpNetworkService: Shutdown complete");
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
                    Debug.LogError($"TcpNetworkService: Failed to parse command: {ex.Message}");
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
            try
            {
                _listener = new TcpListener(IPAddress.Any, _portNumber);
                _listener.Start();
                Debug.Log($"TcpNetworkService: Server started on port {_portNumber}");

                while (_isRunning)
                {
                    try
                    {
                        // Accept new client if none connected
                        if (_client == null || !_client.Connected)
                        {
                            if (_listener.Pending())
                            {
                                _client = _listener.AcceptTcpClient();
                                _stream = _client.GetStream();
                                Debug.Log("TcpNetworkService: Python client connected");
                            }
                            else
                            {
                                Thread.Sleep(10);
                                continue;
                            }
                        }

                        // Check for incoming data
                        if (_stream != null && _stream.DataAvailable)
                        {
                            string requestMessage = ReceiveLengthPrefixedMessage();
                            _incomingRequestQueue.Enqueue(requestMessage);

                            // Wait for response from main Unity thread
                            WaitAndSendResponse();
                        }
                        else
                        {
                            Thread.Sleep(1);
                        }
                    }
                    catch (SocketException ex)
                    {
                        Debug.LogWarning($"TcpNetworkService: Socket error: {ex.Message}");
                        CloseClientConnection();
                    }
                    catch (IOException ex)
                    {
                        Debug.LogWarning($"TcpNetworkService: IO error: {ex.Message}");
                        CloseClientConnection();
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"TcpNetworkService: Fatal error in network loop: {ex.Message}");
            }
            finally
            {
                CloseClientConnection();
                _listener?.Stop();
            }
        }

        private string ReceiveLengthPrefixedMessage()
        {
            // Read 4-byte length prefix (big-endian)
            byte[] lengthBuffer = new byte[4];
            int bytesRead = 0;

            while (bytesRead < 4)
            {
                int received = _stream.Read(lengthBuffer, bytesRead, 4 - bytesRead);
                if (received == 0)
                {
                    throw new IOException("Connection closed while reading message length");
                }
                bytesRead += received;
            }

            // Convert from big-endian to int
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(lengthBuffer);
            }
            int messageLength = BitConverter.ToInt32(lengthBuffer, 0);

            // Read message body
            byte[] messageBuffer = new byte[messageLength];
            bytesRead = 0;

            while (bytesRead < messageLength)
            {
                int received = _stream.Read(messageBuffer, bytesRead, messageLength - bytesRead);
                if (received == 0)
                {
                    throw new IOException("Connection closed while reading message body");
                }
                bytesRead += received;
            }

            return Encoding.UTF8.GetString(messageBuffer);
        }

        private void SendLengthPrefixedMessage(string message)
        {
            byte[] messageBytes = Encoding.UTF8.GetBytes(message);

            // Create 4-byte length prefix (big-endian)
            byte[] lengthBytes = BitConverter.GetBytes(messageBytes.Length);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(lengthBytes);
            }

            // Send length prefix
            _stream.Write(lengthBytes, 0, 4);

            // Send message body
            _stream.Write(messageBytes, 0, messageBytes.Length);
            _stream.Flush();
        }

        private void WaitAndSendResponse()
        {
            string response;
            while (!_outgoingResponseQueue.TryDequeue(out response))
            {
                Thread.Sleep(1);

                if (!_isRunning)
                {
                    return;
                }
            }

            SendLengthPrefixedMessage(response);
        }

        private void CloseClientConnection()
        {
            try
            {
                _stream?.Close();
                _client?.Close();
            }
            catch (Exception)
            {
                // Ignore errors during cleanup
            }

            _stream = null;
            _client = null;
        }
    }
}
