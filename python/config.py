"""Configuration constants for the Python robot control system."""

# Network Configuration
UNITY_SERVER_ADDRESS: str = "tcp://localhost:5555"
NETWORK_TIMEOUT_MILLISECONDS: int = 5000

# Robot Configuration (6-DOF)
NUMBER_OF_JOINTS: int = 6
JOINT_ANGLE_LIMITS: list = [90.0, 90.0, 90.0, 180.0, 90.0, 90.0]
MAXIMUM_DELTA_DEGREES: float = 10.0

# Observation Space
OBSERVATION_DIMENSION: int = 17
WORKSPACE_RADIUS_METERS: float = 0.6
LASER_MAXIMUM_RANGE_METERS: float = 1.0

# Action Space
ACTION_DIMENSION: int = 7
GRIPPER_CLOSE_THRESHOLD: float = 0.5

# Episode Configuration
DEFAULT_MAXIMUM_EPISODE_STEPS: int = 500

# Reward Configuration
DISTANCE_REWARD_SCALE: float = 10.0
ALIGNMENT_REWARD_SCALE: float = 0.5
GRASP_SUCCESS_REWARD: float = 100.0
COLLISION_PENALTY_VALUE: float = -100.0
GRASP_DISTANCE_THRESHOLD: float = 0.05

# Training Configuration
LEARNING_RATE: float = 3e-4
STEPS_PER_UPDATE: int = 2048
BATCH_SIZE: int = 64
TRAINING_EPOCHS: int = 10
DISCOUNT_FACTOR: float = 0.99
GAE_LAMBDA: float = 0.95
CLIP_RANGE: float = 0.2
ENTROPY_COEFFICIENT: float = 0.01
CHECKPOINT_FREQUENCY: int = 10000

# Curriculum Phases
CURRICULUM_PHASES: list = [
    {"name": "touch", "steps": 100_000, "threshold": 50.0},
    {"name": "grasp", "steps": 200_000, "threshold": 100.0},
    {"name": "pick_and_place", "steps": 500_000, "threshold": 200.0}
]
