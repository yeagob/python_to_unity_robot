"""Tests for reward calculation service."""

import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.observation_model import ObservationModel


# Import RewardCalculationService directly to avoid network_service import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services'))
from reward_calculation_service import RewardCalculationService


class TestRewardCalculationService:
    """Tests for RewardCalculationService."""

    def create_observation(
        self,
        distance: float = 0.3,
        tcp_position: list = None,
        direction: list = None,
        laser_distance: float = 1.0,
        is_gripping: bool = False,
        collision: bool = False
    ) -> ObservationModel:
        """Helper to create observation with specified values."""
        if tcp_position is None:
            tcp_position = [0.3, 0.2, 0.1]
        if direction is None:
            direction = [0.577, 0.577, 0.577]

        return ObservationModel(
            joint_angles=[0.0] * 6,
            tool_center_point_position=tcp_position,
            direction_to_target=direction,
            distance_to_target=distance,
            gripper_state=0.5,
            is_gripping_object=is_gripping,
            laser_sensor_hit=laser_distance < 1.0,
            laser_sensor_distance=laser_distance,
            collision_detected=collision,
            target_orientation_one_hot=[1.0, 0.0],
            is_reset_frame=False
        )

    def test_initial_reset_state(self) -> None:
        """Test that reset_state initializes previous state correctly."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(
            distance=0.5,
            tcp_position=[0.2, 0.3, 0.1]
        )

        service.reset_state(initial_obs)

        assert service._previous_distance_to_target == 0.5
        np.testing.assert_array_equal(
            service._previous_tool_center_point_position,
            [0.2, 0.3, 0.1]
        )
        assert service._is_first_step is True

    def test_first_step_no_distance_reward(self) -> None:
        """Test that first step after reset has no distance reward."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(distance=0.5)
        service.reset_state(initial_obs)

        next_obs: ObservationModel = self.create_observation(distance=0.4)
        reward, terminated, info = service.calculate_reward(next_obs)

        assert info["reward_components"]["distance"] == 0.0
        assert service._is_first_step is False

    def test_distance_improvement_reward(self) -> None:
        """Test reward for moving closer to target."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(distance=0.5)
        service.reset_state(initial_obs)

        obs1: ObservationModel = self.create_observation(distance=0.4)
        service.calculate_reward(obs1)

        obs2: ObservationModel = self.create_observation(distance=0.3)
        reward, terminated, info = service.calculate_reward(obs2)

        expected_distance_reward: float = 0.1 * 10.0
        assert abs(info["reward_components"]["distance"] - expected_distance_reward) < 0.001

    def test_distance_penalty_for_moving_away(self) -> None:
        """Test negative reward for moving away from target."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(distance=0.3)
        service.reset_state(initial_obs)

        obs1: ObservationModel = self.create_observation(distance=0.3)
        service.calculate_reward(obs1)

        obs2: ObservationModel = self.create_observation(distance=0.4)
        reward, terminated, info = service.calculate_reward(obs2)

        assert info["reward_components"]["distance"] < 0

    def test_grasp_success_reward(self) -> None:
        """Test reward for successful grasp."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation()
        service.reset_state(initial_obs)

        grasp_obs: ObservationModel = self.create_observation(
            laser_distance=0.03,
            is_gripping=True
        )
        reward, terminated, info = service.calculate_reward(grasp_obs)

        assert info["reward_components"]["grasp"] == 100.0
        assert info.get("success") is True

    def test_no_grasp_reward_when_not_gripping(self) -> None:
        """Test no grasp reward when close but not gripping."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation()
        service.reset_state(initial_obs)

        close_obs: ObservationModel = self.create_observation(
            laser_distance=0.03,
            is_gripping=False
        )
        reward, terminated, info = service.calculate_reward(close_obs)

        assert info["reward_components"]["grasp"] == 0.0

    def test_collision_penalty_and_termination(self) -> None:
        """Test collision penalty and episode termination."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation()
        service.reset_state(initial_obs)

        collision_obs: ObservationModel = self.create_observation(collision=True)
        reward, terminated, info = service.calculate_reward(collision_obs)

        assert info["reward_components"]["collision"] == -100.0
        assert terminated is True
        assert info.get("collision") is True

    def test_no_collision_no_termination(self) -> None:
        """Test no termination without collision."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation()
        service.reset_state(initial_obs)

        normal_obs: ObservationModel = self.create_observation(collision=False)
        reward, terminated, info = service.calculate_reward(normal_obs)

        assert info["reward_components"]["collision"] == 0.0
        assert terminated is False

    def test_alignment_reward_positive(self) -> None:
        """Test positive alignment reward for velocity towards target."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(
            tcp_position=[0.0, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        service.reset_state(initial_obs)

        obs1: ObservationModel = self.create_observation(
            tcp_position=[0.0, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        service.calculate_reward(obs1)

        obs2: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        reward, terminated, info = service.calculate_reward(obs2)

        assert info["reward_components"]["alignment"] > 0

    def test_alignment_reward_negative(self) -> None:
        """Test negative alignment reward for velocity away from target."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        service.reset_state(initial_obs)

        obs1: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        service.calculate_reward(obs1)

        obs2: ObservationModel = self.create_observation(
            tcp_position=[0.0, 0.0, 0.0],
            direction=[1.0, 0.0, 0.0]
        )
        reward, terminated, info = service.calculate_reward(obs2)

        assert info["reward_components"]["alignment"] < 0

    def test_alignment_zero_when_stationary(self) -> None:
        """Test zero alignment reward when robot is stationary."""
        service: RewardCalculationService = RewardCalculationService()
        initial_obs: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.1, 0.1]
        )
        service.reset_state(initial_obs)

        obs1: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.1, 0.1]
        )
        service.calculate_reward(obs1)

        obs2: ObservationModel = self.create_observation(
            tcp_position=[0.1, 0.1, 0.1]
        )
        reward, terminated, info = service.calculate_reward(obs2)

        assert info["reward_components"]["alignment"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
