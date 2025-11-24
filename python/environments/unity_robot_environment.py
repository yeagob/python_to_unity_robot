import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.command_model import CommandModel
from models.observation_model import ObservationModel
from enums.command_type import CommandType
from services.network_service import NetworkService
from services.reward_calculation_service import RewardCalculationService


class UnityRobotEnvironment(gym.Env):
    """Gymnasium environment for Unity 6-DOF robot simulation."""

    OBSERVATION_DIMENSION: int = 17
    ACTION_DIMENSION: int = 7
    MAXIMUM_DELTA_DEGREES: float = 10.0
    GRIPPER_CLOSE_THRESHOLD: float = 0.5
    DEFAULT_MAXIMUM_EPISODE_STEPS: int = 500

    # Joint angle limits for normalization (6 joints)
    JOINT_ANGLE_LIMITS: np.ndarray = np.array([90.0, 90.0, 90.0, 180.0, 90.0, 90.0])
    WORKSPACE_RADIUS_METERS: float = 0.6
    LASER_MAXIMUM_RANGE_METERS: float = 1.0

    metadata: Dict[str, Any] = {"render_modes": ["human"], "render_fps": 50}

    def __init__(
        self,
        server_address: str = "tcp://localhost:5555",
        maximum_episode_steps: int = DEFAULT_MAXIMUM_EPISODE_STEPS,
        render_mode: Optional[str] = None
    ) -> None:
        super().__init__()

        self._server_address: str = server_address
        self._maximum_episode_steps: int = maximum_episode_steps
        self._render_mode: Optional[str] = render_mode
        self._current_step_count: int = 0
        self._num_joints: Optional[int] = None  # Will be detected on first reset

        # Parse server address (format: "tcp://host:port")
        host, port = self._parse_server_address(server_address)
        self._network_service: NetworkService = NetworkService(host, port)
        self._reward_calculation_service: RewardCalculationService = RewardCalculationService()

        # 17-dimensional observation space (normalized to [-1, 1])
        self.observation_space: spaces.Box = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.OBSERVATION_DIMENSION,),
            dtype=np.float32
        )

        # 7-dimensional action space: 5 continuous joint deltas + 1 axis6 orientation + 1 gripper
        self.action_space: spaces.Box = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.ACTION_DIMENSION,),
            dtype=np.float32
        )

        self._network_service.connect()

    def step(
        self,
        action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one environment step."""
        self._current_step_count += 1

        # Scale joint deltas (up to 5 actions or number of joints, whichever is less)
        num_action_joints = min(5, self._num_joints) if self._num_joints else 5
        scaled_joint_deltas: np.ndarray = action[:num_action_joints] * self.MAXIMUM_DELTA_DEGREES

        # Axis 6 orientation: <0 = vertical (0), >=0 = horizontal (1)
        axis_6_orientation: float = 0.0 if action[5] < 0 else 1.0

        # Gripper action
        gripper_action_value: float = float(action[6])

        step_command: CommandModel = CommandModel(
            command_type=CommandType.STEP,
            actions=scaled_joint_deltas.tolist(),
            axis_6_orientation=axis_6_orientation,
            gripper_close_value=gripper_action_value
        )

        observation_model: ObservationModel = self._network_service.send_command(step_command)
        normalized_observation: np.ndarray = self._normalize_observation(observation_model)

        reward: float
        terminated: bool
        information: Dict[str, Any]
        reward, terminated, information = self._reward_calculation_service.calculate_reward(
            observation_model)

        truncated: bool = self._current_step_count >= self._maximum_episode_steps

        return normalized_observation, reward, terminated, truncated, information

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment."""
        super().reset(seed=seed)

        self._current_step_count = 0

        reset_command: CommandModel = CommandModel(command_type=CommandType.RESET)
        observation_model: ObservationModel = self._network_service.send_command(reset_command)

        self._reward_calculation_service.reset_state(observation_model)

        normalized_observation: np.ndarray = self._normalize_observation(observation_model)

        return normalized_observation, {}

    def close(self) -> None:
        """Close the environment and disconnect from Unity."""
        self._network_service.disconnect()

    def set_simulation_mode(self, enable_smooth_movement: bool) -> None:
        """Switch between training mode (instant) and simulation mode (smooth)."""
        configuration_command: CommandModel = CommandModel(
            command_type=CommandType.CONFIGURATION,
            simulation_mode_enabled=enable_smooth_movement
        )
        self._network_service.send_command(configuration_command)

    def _parse_server_address(self, address: str) -> Tuple[str, int]:
        """Parse server address from 'tcp://host:port' format."""
        # Remove protocol prefix if present
        if address.startswith("tcp://"):
            address = address[6:]
        elif address.startswith("://"):
            address = address[3:]

        # Split host and port
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            port = int(port_str)
        else:
            host = address
            port = NetworkService.DEFAULT_PORT

        return host, port

    def _normalize_observation(self, observation: ObservationModel) -> np.ndarray:
        """Normalize observation to [-1, 1] range."""
        # Detect number of joints on first call
        if self._num_joints is None:
            self._num_joints = len(observation.joint_angles)
            print(f"Detected {self._num_joints} joints from Unity")

        # Normalize joint angles - use actual number of joints from Unity
        joint_angles_array: np.ndarray = np.array(observation.joint_angles)
        joint_limits = self.JOINT_ANGLE_LIMITS[:self._num_joints]
        normalized_joint_angles: np.ndarray = joint_angles_array / joint_limits

        # Pad with zeros if less than 6 joints to maintain observation dimension
        if self._num_joints < 6:
            padding = np.zeros(6 - self._num_joints)
            normalized_joint_angles = np.concatenate([normalized_joint_angles, padding])

        # Gripper state (1 value)
        gripper_state_array: np.ndarray = np.array([observation.gripper_state])

        # Normalize TCP position (3 values)
        normalized_tool_position: np.ndarray = (
            np.array(observation.tool_center_point_position) / self.WORKSPACE_RADIUS_METERS
        )

        # Direction to target (3 values, already normalized)
        direction_to_target: np.ndarray = np.array(observation.direction_to_target)

        # Normalize laser distance (1 value)
        normalized_laser_distance: np.ndarray = np.array([
            observation.laser_sensor_distance / self.LASER_MAXIMUM_RANGE_METERS
        ])

        # Is gripping flag (1 value)
        is_gripping_array: np.ndarray = np.array([
            1.0 if observation.is_gripping_object else 0.0
        ])

        # Target orientation one-hot (2 values)
        target_orientation: np.ndarray = np.array(observation.target_orientation_one_hot)

        # Concatenate all components: 6 + 1 + 3 + 3 + 1 + 1 + 2 = 17
        concatenated_observation: np.ndarray = np.concatenate([
            normalized_joint_angles,      # 0-5: joint angles
            gripper_state_array,          # 6: gripper state
            normalized_tool_position,     # 7-9: TCP position
            direction_to_target,          # 10-12: direction to target
            normalized_laser_distance,    # 13: laser distance
            is_gripping_array,            # 14: is gripping
            target_orientation            # 15-16: target orientation
        ])

        clipped_observation: np.ndarray = np.clip(
            concatenated_observation, -1.0, 1.0
        ).astype(np.float32)

        return clipped_observation
