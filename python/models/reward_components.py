from dataclasses import dataclass


@dataclass
class RewardComponents:
    """Individual reward components for RL training."""

    distance_reward: float = 0.0
    alignment_reward: float = 0.0
    grasp_reward: float = 0.0
    collision_penalty: float = 0.0

    @property
    def total_reward(self) -> float:
        """Calculate total reward from all components."""
        return (
            self.distance_reward
            + self.alignment_reward
            + self.grasp_reward
            + self.collision_penalty
        )

    def to_dictionary(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "distance": self.distance_reward,
            "alignment": self.alignment_reward,
            "grasp": self.grasp_reward,
            "collision": self.collision_penalty,
            "total": self.total_reward
        }
