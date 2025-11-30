#!/usr/bin/env python3
"""Training script for the robotic arm RL agent."""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from controllers.training_controller import TrainingController


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Train 6-DOF Robot Arm RL Agent")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from a saved model"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to the saved model to resume from (e.g., ./models/robot_policy_touch)"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for training."""
    args = parse_arguments()
    
    print("=" * 60)
    print("6-DOF Robot Arm RL Training")
    print("=" * 60)

    if args.resume:
        if args.model_path is None:
            print("Error: --model-path is required when using --resume")
            sys.exit(1)
        print(f"\nResuming training from: {args.model_path}")
    
    training_controller: TrainingController = TrainingController(
        resume_from_model=args.model_path if args.resume else None
    )

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
