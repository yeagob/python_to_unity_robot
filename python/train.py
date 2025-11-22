#!/usr/bin/env python3
"""Training script for the robotic arm RL agent."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from controllers.training_controller import TrainingController


def main() -> None:
    """Main entry point for training."""
    print("=" * 60)
    print("6-DOF Robot Arm RL Training")
    print("=" * 60)

    training_controller: TrainingController = TrainingController()

    try:
        print("\nInitializing training...")
        training_controller.initialize_training()

        print("\nStarting curriculum training...")
        training_controller.execute_curriculum_training()

    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
    except Exception as error:
        print(f"\nTraining error: {error}")
        raise
    finally:
        training_controller.shutdown()
        print("\nTraining session ended.")


if __name__ == "__main__":
    main()
