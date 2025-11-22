#!/usr/bin/env python3
"""Test script for Unity-Python ZeroMQ connection."""

import json
import time
import sys

def test_with_mock():
    """Test the system components without Unity connection."""
    print("\n" + "=" * 60)
    print("Testing Python Components (Mock Mode)")
    print("=" * 60)

    # Test models
    from models.observation_model import ObservationModel
    from models.command_model import CommandModel
    from models.reward_components import RewardComponents
    from enums.command_type import CommandType

    print("\n[1] Testing ObservationModel...")
    obs_data = {
        "JointAngles": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "ToolCenterPointPosition": [0.3, 0.2, 0.1],
        "DirectionToTarget": [0.577, 0.577, 0.577],
        "DistanceToTarget": 0.15,
        "GripperState": 0.5,
        "IsGrippingObject": False,
        "LaserSensorHit": True,
        "LaserSensorDistance": 0.08,
        "CollisionDetected": False,
        "TargetOrientationOneHot": [1.0, 0.0],
        "IsResetFrame": False
    }
    obs = ObservationModel.from_dictionary(obs_data)
    print(f"   Joint angles: {obs.joint_angles}")
    print(f"   TCP position: {obs.tool_center_point_position}")
    print(f"   Distance to target: {obs.distance_to_target}")
    print("   OK")

    print("\n[2] Testing CommandModel...")
    step_cmd = CommandModel(
        command_type=CommandType.STEP,
        actions=[5.0, -2.5, 3.0, 1.0, -1.0],
        axis_6_orientation=1.0,
        gripper_close_value=0.8
    )
    cmd_dict = step_cmd.to_dictionary()
    print(f"   Command type: {cmd_dict['type']}")
    print(f"   Actions: {cmd_dict['actions']}")
    print(f"   Gripper: {cmd_dict['gripperClose']}")
    print("   OK")

    print("\n[3] Testing RewardComponents...")
    from services.reward_calculation_service import RewardCalculationService
    reward_service = RewardCalculationService()
    reward_service.reset_state(obs)

    # Simulate moving closer
    obs_closer = ObservationModel.from_dictionary({
        **obs_data,
        "DistanceToTarget": 0.10,
        "ToolCenterPointPosition": [0.32, 0.22, 0.12]
    })
    reward, terminated, info = reward_service.calculate_reward(obs_closer)
    print(f"   Reward (moving closer): {reward:.4f}")
    print(f"   Components: {info.get('reward_components', {})}")
    print("   OK")

    # Test grasp reward
    obs_grasp = ObservationModel.from_dictionary({
        **obs_data,
        "LaserSensorDistance": 0.03,
        "IsGrippingObject": True
    })
    reward, terminated, info = reward_service.calculate_reward(obs_grasp)
    print(f"\n   Reward (successful grasp): {reward:.4f}")
    print(f"   Success: {info.get('success', False)}")
    print("   OK")

    print("\n[4] Testing observation normalization...")
    import numpy as np
    JOINT_ANGLE_LIMITS = np.array([90.0, 90.0, 90.0, 180.0, 90.0, 90.0])
    WORKSPACE_RADIUS = 0.6
    LASER_MAX = 1.0

    joint_angles = np.array(obs.joint_angles[:6])
    norm_joints = joint_angles / JOINT_ANGLE_LIMITS
    norm_tcp = np.array(obs.tool_center_point_position) / WORKSPACE_RADIUS
    norm_laser = obs.laser_sensor_distance / LASER_MAX

    print(f"   Normalized joints: {norm_joints}")
    print(f"   Normalized TCP: {norm_tcp}")
    print(f"   Normalized laser: {norm_laser}")
    print("   OK")

    print("\n" + "=" * 60)
    print("All mock tests passed!")
    print("=" * 60)
    return True


def test_with_unity():
    """Test actual connection to Unity (requires Unity to be running)."""
    print("\n" + "=" * 60)
    print("Testing Unity Connection")
    print("=" * 60)

    try:
        import zmq
    except ImportError:
        print("\n[!] pyzmq not installed. Install with: pip install pyzmq")
        return False

    print("\n[1] Creating ZeroMQ socket...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
    socket.connect("tcp://localhost:5555")
    print("   Socket created and connected to tcp://localhost:5555")

    try:
        print("\n[2] Sending RESET command...")
        reset_cmd = {"type": "RESET"}
        socket.send_string(json.dumps(reset_cmd))

        response = socket.recv_string()
        obs = json.loads(response)
        print(f"   Received observation:")
        print(f"   - Joint angles: {obs.get('JointAngles', 'N/A')}")
        print(f"   - TCP position: {obs.get('ToolCenterPointPosition', 'N/A')}")
        print(f"   - Reset frame: {obs.get('IsResetFrame', 'N/A')}")
        print("   OK")

        print("\n[3] Sending STEP command...")
        step_cmd = {
            "type": "STEP",
            "actions": [5.0, -2.5, 3.0, 1.0, -1.0],
            "axis6Orientation": 0.0,
            "gripperClose": 0.3
        }
        socket.send_string(json.dumps(step_cmd))

        response = socket.recv_string()
        obs = json.loads(response)
        print(f"   New joint angles: {obs.get('JointAngles', 'N/A')}")
        print("   OK")

        print("\n[4] Sending CONFIG command (switch to simulation mode)...")
        config_cmd = {
            "type": "CONFIG",
            "simulationMode": True
        }
        socket.send_string(json.dumps(config_cmd))

        response = socket.recv_string()
        result = json.loads(response)
        print(f"   Response: {result}")
        print("   OK")

        print("\n" + "=" * 60)
        print("Unity connection test passed!")
        print("=" * 60)
        return True

    except zmq.Again:
        print("\n[!] Timeout: Unity is not responding.")
        print("    Make sure Unity is running with the GameManager active.")
        return False
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return False
    finally:
        socket.close()
        context.term()


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("Python-Unity Robot Connection Test")
    print("=" * 60)

    # Always run mock tests first
    mock_ok = test_with_mock()

    if not mock_ok:
        print("\n[!] Mock tests failed!")
        sys.exit(1)

    # Ask if user wants to test Unity connection
    print("\n" + "-" * 60)
    print("Do you want to test the Unity connection?")
    print("(Requires Unity to be running with the simulation)")
    print("-" * 60)

    try:
        response = input("\nTest Unity connection? [y/N]: ").strip().lower()
        if response == 'y':
            unity_ok = test_with_unity()
            if not unity_ok:
                print("\n[!] Unity connection test failed.")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
