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
    COLLISION_PENALTY_VALUE: float = -300.0
    UNDERGROUND_PENALTY_VALUE: float = -300.0
    SURVIVAL_REWARD: float = 0.02
    ACTION_PENALTY_SCALE: float = 0.05
    GRASP_DISTANCE_THRESHOLD: float = 0.3
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

        # Survival reward (for existing without colliding)
        reward_components.survival_reward = self.SURVIVAL_REWARD

        # Action penalty (to encourage smooth movement)
        # Note: We don't have the action here, but we can infer it from joint changes or pass it in.
        # For now, let's skip explicit action penalty here or calculate it based on velocity if needed.
        # Actually, let's keep it simple: Survival reward is the main fix for now.
        # If we want action penalty, we need to pass 'action' to this method.
        # Let's stick to Survival Reward first as it's the most critical for "staying alive".

        reward_components.grasp_reward = self._calculate_grasp_reward(observation)

        if reward_components.grasp_reward > 0.0:
            information_dictionary["success"] = True

        # Check for collision
        collision_result: Tuple[float, bool] = self._calculate_collision_penalty(observation)
        reward_components.collision_penalty = collision_result[0]

        if collision_result[1]:
            episode_terminated = True
            information_dictionary["collision"] = True

        # Check for underground (TCP below base)
        underground_result: Tuple[float, bool] = self._calculate_underground_penalty(
            current_position)
        reward_components.collision_penalty += underground_result[0]

        if underground_result[1]:
            episode_terminated = True
            information_dictionary["underground"] = True

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
        """Calculate reward for successful grasp (or reach)."""
        # Relaxed condition: Success if distance < 0.3 (30cm), gripping not required for now
        is_close_to_target: bool = observation.distance_to_target < self.GRASP_DISTANCE_THRESHOLD
        
        # Note: We removed 'is_gripping' requirement to facilitate initial learning
        # is_gripping: bool = observation.is_gripping_object

        if is_close_to_target:
            # Log success with joint angles
            joint_angles_str = ", ".join([f"{angle:.2f}°" for angle in observation.joint_angles])
            print(f"\n🎯 SUCCESS! Target Position Reached (Distance < {self.GRASP_DISTANCE_THRESHOLD}m)!")
            print(f"   Joint Angles: [{joint_angles_str}]")
            print(f"   TCP Position: [{observation.tool_center_point_position[0]:.3f}, "
                  f"{observation.tool_center_point_position[1]:.3f}, "
                  f"{observation.tool_center_point_position[2]:.3f}]")
            print(f"   Distance to Target: {observation.distance_to_target:.4f}m\n")
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

    def _calculate_underground_penalty(
        self,
        current_position: np.ndarray
    ) -> Tuple[float, bool]:
        """Calculate penalty for TCP going below the base (Y < 0)."""
        tcp_y_position: float = current_position[1]
        
        if tcp_y_position < 0.0:
            return self.UNDERGROUND_PENALTY_VALUE, True
        
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
