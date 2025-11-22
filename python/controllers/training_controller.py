from dataclasses import dataclass
from typing import List, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class CurriculumPhase:
    """Definition of a curriculum learning phase."""
    name: str
    training_steps: int
    reward_threshold: float


class TrainingController:
    """Controller for RL training with PPO and curriculum learning."""

    LEARNING_RATE: float = 3e-4
    STEPS_PER_UPDATE: int = 2048
    BATCH_SIZE: int = 64
    TRAINING_EPOCHS: int = 10
    DISCOUNT_FACTOR: float = 0.99
    GAE_LAMBDA: float = 0.95
    CLIP_RANGE: float = 0.2
    ENTROPY_COEFFICIENT: float = 0.01
    CHECKPOINT_FREQUENCY: int = 10000

    def __init__(self, server_address: str = "tcp://localhost:5555") -> None:
        self._server_address: str = server_address
        self._environment = None
        self._model = None
        self._curriculum_phases: List[CurriculumPhase] = self._create_curriculum_phases()

    def initialize_training(self) -> None:
        """Initialize training environment and PPO model."""
        # Import here to avoid dependency issues when not training
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        from environments.unity_robot_environment import UnityRobotEnvironment

        vectorized_environment = DummyVecEnv([self._create_environment])
        self._environment = VecNormalize(
            vectorized_environment,
            norm_obs=True,
            norm_reward=True
        )

        # Create directories for models and logs
        os.makedirs("./models", exist_ok=True)
        os.makedirs("./checkpoints", exist_ok=True)
        os.makedirs("./tensorboard_logs", exist_ok=True)

        self._model = PPO(
            policy="MlpPolicy",
            env=self._environment,
            learning_rate=self.LEARNING_RATE,
            n_steps=self.STEPS_PER_UPDATE,
            batch_size=self.BATCH_SIZE,
            n_epochs=self.TRAINING_EPOCHS,
            gamma=self.DISCOUNT_FACTOR,
            gae_lambda=self.GAE_LAMBDA,
            clip_range=self.CLIP_RANGE,
            ent_coef=self.ENTROPY_COEFFICIENT,
            verbose=1,
            tensorboard_log="./tensorboard_logs/"
        )

    def execute_curriculum_training(self) -> None:
        """Execute curriculum learning through all phases."""
        from stable_baselines3.common.callbacks import CheckpointCallback

        checkpoint_callback: CheckpointCallback = CheckpointCallback(
            save_freq=self.CHECKPOINT_FREQUENCY,
            save_path="./checkpoints/",
            name_prefix="robot_policy"
        )

        for phase in self._curriculum_phases:
            print(f"\n{'=' * 60}")
            print(f"CURRICULUM PHASE: {phase.name}")
            print(f"Training Steps: {phase.training_steps}")
            print(f"{'=' * 60}\n")

            self._model.learn(
                total_timesteps=phase.training_steps,
                callback=checkpoint_callback,
                reset_num_timesteps=False
            )

            model_save_path: str = f"./models/robot_policy_{phase.name}"
            normalizer_save_path: str = f"./models/normalizer_{phase.name}.pkl"

            self._model.save(model_save_path)
            self._environment.save(normalizer_save_path)

            print(f"Phase '{phase.name}' completed. Model saved.")

    def shutdown(self) -> None:
        """Shutdown training and close environment."""
        if self._environment is not None:
            self._environment.close()

    def _create_environment(self):
        """Factory method for creating environment instances."""
        from environments.unity_robot_environment import UnityRobotEnvironment
        return UnityRobotEnvironment(
            server_address=self._server_address,
            maximum_episode_steps=500
        )

    def _create_curriculum_phases(self) -> List[CurriculumPhase]:
        """Define curriculum learning phases."""
        return [
            CurriculumPhase(name="touch", training_steps=100_000, reward_threshold=50.0),
            CurriculumPhase(name="grasp", training_steps=200_000, reward_threshold=100.0),
            CurriculumPhase(name="pick_and_place", training_steps=500_000, reward_threshold=200.0)
        ]
