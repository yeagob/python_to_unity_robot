"""Tests for data models."""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.observation_model import ObservationModel
from models.command_model import CommandModel
from models.reward_components import RewardComponents
from enums.command_type import CommandType


class TestObservationModel:
    """Tests for ObservationModel."""

    def test_from_dictionary_with_valid_data(self) -> None:
        """Test creating ObservationModel from valid dictionary."""
        data: dict = {
            "JointAngles": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
            "ToolCenterPointPosition": [0.1, 0.2, 0.3],
            "DirectionToTarget": [0.5, 0.5, 0.707],
            "DistanceToTarget": 0.15,
            "GripperState": 0.8,
            "IsGrippingObject": True,
            "LaserSensorHit": True,
            "LaserSensorDistance": 0.05,
            "CollisionDetected": False,
            "TargetOrientationOneHot": [1.0, 0.0],
            "IsResetFrame": False
        }

        observation: ObservationModel = ObservationModel.from_dictionary(data)

        assert observation.joint_angles == [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        assert observation.tool_center_point_position == [0.1, 0.2, 0.3]
        assert observation.direction_to_target == [0.5, 0.5, 0.707]
        assert observation.distance_to_target == 0.15
        assert observation.gripper_state == 0.8
        assert observation.is_gripping_object is True
        assert observation.laser_sensor_hit is True
        assert observation.laser_sensor_distance == 0.05
        assert observation.collision_detected is False
        assert observation.target_orientation_one_hot == [1.0, 0.0]
        assert observation.is_reset_frame is False

    def test_from_dictionary_with_empty_data(self) -> None:
        """Test creating ObservationModel with empty dictionary uses defaults."""
        data: dict = {}

        observation: ObservationModel = ObservationModel.from_dictionary(data)

        assert observation.joint_angles == [0.0] * 6
        assert observation.tool_center_point_position == [0.0, 0.0, 0.0]
        assert observation.distance_to_target == 0.0
        assert observation.gripper_state == 1.0
        assert observation.is_gripping_object is False

    def test_to_dictionary_roundtrip(self) -> None:
        """Test that to_dictionary creates valid data for from_dictionary."""
        original_data: dict = {
            "JointAngles": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "ToolCenterPointPosition": [0.1, 0.2, 0.3],
            "DirectionToTarget": [0.5, 0.5, 0.707],
            "DistanceToTarget": 0.15,
            "GripperState": 0.5,
            "IsGrippingObject": False,
            "LaserSensorHit": False,
            "LaserSensorDistance": 1.0,
            "CollisionDetected": False,
            "TargetOrientationOneHot": [0.0, 1.0],
            "IsResetFrame": True
        }

        observation: ObservationModel = ObservationModel.from_dictionary(original_data)
        result_dict: dict = observation.to_dictionary()

        assert result_dict["JointAngles"] == original_data["JointAngles"]
        assert result_dict["ToolCenterPointPosition"] == original_data["ToolCenterPointPosition"]
        assert result_dict["DistanceToTarget"] == original_data["DistanceToTarget"]


class TestCommandModel:
    """Tests for CommandModel."""

    def test_step_command_to_dictionary(self) -> None:
        """Test STEP command serialization."""
        command: CommandModel = CommandModel(
            command_type=CommandType.STEP,
            actions=[1.0, 2.0, 3.0, 4.0, 5.0],
            gripper_close_value=0.8,
            axis_6_orientation=1.0
        )

        result: dict = command.to_dictionary()

        assert result["Type"] == "STEP"
        assert result["Actions"] == [1.0, 2.0, 3.0, 4.0, 5.0]
        assert result["GripperCloseValue"] == 0.8
        assert result["Axis6Orientation"] == 1.0

    def test_reset_command_to_dictionary(self) -> None:
        """Test RESET command serialization."""
        command: CommandModel = CommandModel(command_type=CommandType.RESET)

        result: dict = command.to_dictionary()

        assert result["Type"] == "RESET"
        assert "Actions" not in result
        assert "GripperCloseValue" not in result

    def test_config_command_to_dictionary(self) -> None:
        """Test CONFIG command serialization."""
        command: CommandModel = CommandModel(
            command_type=CommandType.CONFIGURATION,
            simulation_mode_enabled=True
        )

        result: dict = command.to_dictionary()

        assert result["Type"] == "CONFIG"
        assert result["SimulationModeEnabled"] is True


class TestRewardComponents:
    """Tests for RewardComponents."""

    def test_total_reward_calculation(self) -> None:
        """Test total reward is sum of all components."""
        components: RewardComponents = RewardComponents(
            distance_reward=5.0,
            alignment_reward=0.3,
            grasp_reward=100.0,
            collision_penalty=0.0
        )

        assert components.total_reward == 105.3

    def test_total_reward_with_penalty(self) -> None:
        """Test total reward with collision penalty."""
        components: RewardComponents = RewardComponents(
            distance_reward=5.0,
            alignment_reward=0.3,
            grasp_reward=0.0,
            collision_penalty=-100.0
        )

        assert components.total_reward == -94.7

    def test_to_dictionary(self) -> None:
        """Test serialization to dictionary."""
        components: RewardComponents = RewardComponents(
            distance_reward=10.0,
            alignment_reward=0.5,
            grasp_reward=100.0,
            collision_penalty=-50.0
        )

        result: dict = components.to_dictionary()

        assert result["distance"] == 10.0
        assert result["alignment"] == 0.5
        assert result["grasp"] == 100.0
        assert result["collision"] == -50.0
        assert result["total"] == 60.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
