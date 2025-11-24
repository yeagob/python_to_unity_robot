"""Simple test to verify Unity TCP connection."""
import socket
import json
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    """Test connection to Unity server."""
    print("=" * 60)
    print("Unity Connection Test")
    print("=" * 60)

    host = "localhost"
    port = 5555
    timeout = 5.0

    print(f"\nAttempting to connect to {host}:{port}...")

    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # Connect
        sock.connect((host, port))
        print("[OK] TCP connection established!")

        # Send RESET command
        print("\nSending RESET command...")
        command = {
            "Type": "RESET"  # Unity expects "Type" field with uppercase value
        }

        json_bytes = json.dumps(command).encode("utf-8")
        length_prefix = struct.pack(">I", len(json_bytes))

        sock.sendall(length_prefix + json_bytes)
        print("[OK] RESET command sent")

        # Try to receive response
        print("\nWaiting for response from Unity...")
        length_data = sock.recv(4)

        if len(length_data) < 4:
            print("[FAIL] Failed to receive response length")
            return False

        message_length = struct.unpack(">I", length_data)[0]
        print(f"[OK] Response length received: {message_length} bytes")

        # Receive full message
        response_bytes = b""
        while len(response_bytes) < message_length:
            chunk = sock.recv(message_length - len(response_bytes))
            if not chunk:
                print("[FAIL] Connection closed while receiving response")
                return False
            response_bytes += chunk

        response = json.loads(response_bytes.decode("utf-8"))
        print("[OK] Response received successfully!")
        print(f"\nResponse keys: {list(response.keys())}")

        # Check if observation has expected fields
        if "JointAngles" in response:
            joint_angles = response['JointAngles']
            print(f"Joint angles: {joint_angles}")
            print(f"Number of joints: {len(joint_angles)}")

        if "ToolCenterPointPosition" in response:
            print(f"TCP position: {response['ToolCenterPointPosition']}")

        print("\n" + "=" * 60)
        print("[SUCCESS] CONNECTION TEST PASSED!")
        print("=" * 60)

        sock.close()
        return True

    except socket.timeout:
        print("\n[FAIL] Connection timeout!")
        print("Unity is not responding. Make sure:")
        print("  1. Unity is running")
        print("  2. RobotRL scene is loaded")
        print("  3. Unity is in Play mode")
        return False

    except ConnectionRefusedError:
        print("\n[FAIL] Connection refused!")
        print("Unity is not listening on port 5555.")
        print("Make sure Unity is in Play mode.")
        return False

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
