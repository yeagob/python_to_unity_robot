import numpy as np
from typing import Tuple, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.observation_model import ObservationModel
from models.reward_components import RewardComponents


class RewardCalculationService:
    """Service for calculating RL rewards based on robot observations."""

    DISTANCE_REWARD_SCALE: float = 10.0
    ALIGNMENT_REWARD_SCALE: float = 0.5
    GRASP_SUCCESS_REWARD: float = 100.0
    COLLISION_PENALTY_VALUE: float = -100.0
    GRASP_DISTANCE_THRESHOLD: float = 0.05
    VELOCITY_MINIMUM_THRESHOLD: float = 1e-6

    def __init__(self) -> None:
        self._previous_distance_to_target: float = 0.0
        self._previous_tool_center_point_position: np.ndarray = np.zeros(3)
        self._is_first_step: bool = True

    def calculate_reward(
        self,
        observation: ObservationModel
    ) -> Tuple[float, bool, Dict[str, Any]]:
        """
        Calculate reward for current observation.

        Returns:
            Tuple of (total_reward, episode_terminated, info_dictionary)
        """
        reward_components: RewardComponents = RewardComponents()
        episode_terminated: bool = False
        information_dictionary: Dict[str, Any] = {}

        current_distance: float = observation.distance_to_target
        current_position: np.ndarray = np.array(observation.tool_center_point_position)
        target_direction: np.ndarray = np.array(observation.direction_to_target)

        if not self._is_first_step:
            reward_components.distance_reward = self._calculate_distance_reward(
                current_distance)

            reward_components.alignment_reward = self._calculate_alignment_reward(
                current_position, target_direction)

        reward_components.grasp_reward = self._calculate_grasp_reward(observation)

        if reward_components.grasp_reward > 0.0:
            information_dictionary["success"] = True

        collision_result: Tuple[float, bool] = self._calculate_collision_penalty(observation)
        reward_components.collision_penalty = collision_result[0]

        if collision_result[1]:
            episode_terminated = True
            information_dictionary["collision"] = True

        self._update_previous_state(current_distance, current_position)

        information_dictionary["reward_components"] = reward_components.to_dictionary()

        return reward_components.total_reward, episode_terminated, information_dictionary

    def reset_state(self, initial_observation: ObservationModel) -> None:
        """Reset reward calculation state for new episode."""
        self._previous_distance_to_target = initial_observation.distance_to_target
        self._previous_tool_center_point_position = np.array(
            initial_observation.tool_center_point_position)
        self._is_first_step = True

    def _calculate_distance_reward(self, current_distance: float) -> float:
        """Calculate reward based on distance improvement."""
        distance_improvement: float = self._previous_distance_to_target - current_distance
        return distance_improvement * self.DISTANCE_REWARD_SCALE

    def _calculate_alignment_reward(
        self,
        current_position: np.ndarray,
        target_direction: np.ndarray
    ) -> float:
        """Calculate reward based on velocity alignment with target direction."""
        velocity_vector: np.ndarray = current_position - self._previous_tool_center_point_position
        velocity_magnitude: float = float(np.linalg.norm(velocity_vector))

        if velocity_magnitude < self.VELOCITY_MINIMUM_THRESHOLD:
            return 0.0

        normalized_velocity: np.ndarray = velocity_vector / velocity_magnitude
        alignment_dot_product: float = float(np.dot(normalized_velocity, target_direction))

        return alignment_dot_product * self.ALIGNMENT_REWARD_SCALE

    def _calculate_grasp_reward(self, observation: ObservationModel) -> float:
        """Calculate reward for successful grasp."""
        is_close_to_target: bool = observation.laser_sensor_distance < self.GRASP_DISTANCE_THRESHOLD
        is_gripping: bool = observation.is_gripping_object

        if is_close_to_target and is_gripping:
            return self.GRASP_SUCCESS_REWARD

        return 0.0

    def _calculate_collision_penalty(
        self,
        observation: ObservationModel
    ) -> Tuple[float, bool]:
        """Calculate collision penalty and termination flag."""
        if observation.collision_detected:
            return self.COLLISION_PENALTY_VALUE, True

        return 0.0, False

    def _update_previous_state(
        self,
        current_distance: float,
        current_position: np.ndarray
    ) -> None:
        """Update previous state for next reward calculation."""
        self._previous_distance_to_target = current_distance
        self._previous_tool_center_point_position = current_position.copy()
        self._is_first_step = False
