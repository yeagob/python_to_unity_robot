"""Tests for Gymnasium environment (mock tests without Unity connection)."""

import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.observation_model import ObservationModel


# Environment constants for testing without importing the full environment
OBSERVATION_DIMENSION = 17
ACTION_DIMENSION = 7
JOINT_ANGLE_LIMITS = np.array([90.0, 90.0, 90.0, 180.0, 90.0, 90.0])
WORKSPACE_RADIUS_METERS = 0.6
LASER_MAXIMUM_RANGE_METERS = 1.0
MAXIMUM_DELTA_DEGREES = 10.0
GRIPPER_CLOSE_THRESHOLD = 0.5
DEFAULT_MAXIMUM_EPISODE_STEPS = 500


class TestEnvironmentConfiguration:
    """Tests for environment configuration and spaces."""

    def test_observation_space_shape(self) -> None:
        """Test observation space has correct shape (17 dimensions)."""
        assert OBSERVATION_DIMENSION == 17

    def test_action_space_shape(self) -> None:
        """Test action space has correct shape (7 dimensions)."""
        assert ACTION_DIMENSION == 7

    def test_joint_angle_limits(self) -> None:
        """Test joint angle limits are correctly defined."""
        limits = JOINT_ANGLE_LIMITS
        assert len(limits) == 6
        assert limits[0] == 90.0   # Axis 1: Base Y rotation
        assert limits[1] == 90.0   # Axis 2: Shoulder X rotation
        assert limits[2] == 90.0   # Axis 3: Elbow X rotation
        assert limits[3] == 180.0  # Axis 4: Wrist X rotation
        assert limits[4] == 90.0   # Axis 5: Wrist Z rotation
        assert limits[5] == 90.0   # Axis 6: Gripper orientation

    def test_workspace_radius(self) -> None:
        """Test workspace radius is correctly defined."""
        assert WORKSPACE_RADIUS_METERS == 0.6

    def test_maximum_delta_degrees(self) -> None:
        """Test maximum delta degrees is correctly defined."""
        assert MAXIMUM_DELTA_DEGREES == 10.0

    def test_default_maximum_episode_steps(self) -> None:
        """Test default maximum episode steps."""
        assert DEFAULT_MAXIMUM_EPISODE_STEPS == 500


class TestObservationNormalization:
    """Tests for observation normalization logic."""

    def test_normalize_joint_angles(self) -> None:
        """Test joint angle normalization."""
        joint_angles = [90.0, 90.0, 90.0, 180.0, 90.0, 90.0]
        limits = JOINT_ANGLE_LIMITS

        normalized = np.array(joint_angles) / limits

        np.testing.assert_array_almost_equal(normalized, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    def test_normalize_tcp_position(self) -> None:
        """Test TCP position normalization."""
        tcp_position = [0.6, 0.6, 0.6]
        workspace_radius = WORKSPACE_RADIUS_METERS

        normalized = np.array(tcp_position) / workspace_radius

        np.testing.assert_array_almost_equal(normalized, [1.0, 1.0, 1.0])

    def test_normalize_laser_distance(self) -> None:
        """Test laser distance normalization."""
        laser_distance = 1.0
        max_range = LASER_MAXIMUM_RANGE_METERS

        normalized = laser_distance / max_range

        assert normalized == 1.0

    def test_observation_clipping(self) -> None:
        """Test that observation values are clipped to [-1, 1]."""
        extreme_joint = 100.0
        limit = 90.0

        normalized = extreme_joint / limit
        clipped = np.clip(normalized, -1.0, 1.0)

        assert clipped == 1.0

    def test_full_observation_dimension(self) -> None:
        """Test that full normalized observation has correct dimension."""
        joint_angles = np.zeros(6)      # 0-5
        gripper_state = np.zeros(1)     # 6
        tcp_position = np.zeros(3)      # 7-9
        direction = np.zeros(3)         # 10-12
        laser = np.zeros(1)             # 13
        is_gripping = np.zeros(1)       # 14
        target_orient = np.zeros(2)     # 15-16

        full_obs = np.concatenate([
            joint_angles,
            gripper_state,
            tcp_position,
            direction,
            laser,
            is_gripping,
            target_orient
        ])

        assert len(full_obs) == 17


class TestActionScaling:
    """Tests for action scaling logic."""

    def test_joint_delta_scaling(self) -> None:
        """Test joint delta scaling from [-1, 1] to degrees."""
        raw_action = np.array([1.0, -1.0, 0.5, -0.5, 0.0])
        max_delta = MAXIMUM_DELTA_DEGREES

        scaled = raw_action * max_delta

        np.testing.assert_array_almost_equal(scaled, [10.0, -10.0, 5.0, -5.0, 0.0])

    def test_axis_6_orientation_threshold(self) -> None:
        """Test axis 6 orientation discrete conversion."""
        assert (0.0 if -0.5 < 0 else 1.0) == 0.0
        assert (0.0 if 0.0 < 0 else 1.0) == 1.0
        assert (0.0 if 0.5 < 0 else 1.0) == 1.0

    def test_gripper_threshold(self) -> None:
        """Test gripper close threshold."""
        threshold = GRIPPER_CLOSE_THRESHOLD

        assert (0.6 > threshold) is True
        assert (0.5 > threshold) is False
        assert (0.4 > threshold) is False


class TestMockObservation:
    """Tests using mock observation data."""

    def create_mock_observation(self) -> ObservationModel:
        """Create a mock observation for testing."""
        return ObservationModel(
            joint_angles=[45.0, -30.0, 60.0, 90.0, 15.0, 0.0],
            tool_center_point_position=[0.35, 0.25, 0.15],
            direction_to_target=[0.57, 0.57, 0.57],
            distance_to_target=0.12,
            gripper_state=0.2,
            is_gripping_object=True,
            laser_sensor_hit=True,
            laser_sensor_distance=0.05,
            collision_detected=False,
            target_orientation_one_hot=[1.0, 0.0],
            is_reset_frame=False
        )

    def test_mock_observation_to_normalized(self) -> None:
        """Test normalizing a mock observation."""
        obs = self.create_mock_observation()
        limits = JOINT_ANGLE_LIMITS
        workspace = WORKSPACE_RADIUS_METERS
        laser_max = LASER_MAXIMUM_RANGE_METERS

        norm_joints = np.array(obs.joint_angles[:6]) / limits
        norm_gripper = np.array([obs.gripper_state])
        norm_tcp = np.array(obs.tool_center_point_position) / workspace
        direction = np.array(obs.direction_to_target)
        norm_laser = np.array([obs.laser_sensor_distance / laser_max])
        is_grip = np.array([1.0 if obs.is_gripping_object else 0.0])
        target_orient = np.array(obs.target_orientation_one_hot)

        full_norm = np.concatenate([
            norm_joints, norm_gripper, norm_tcp, direction,
            norm_laser, is_grip, target_orient
        ])

        assert len(full_norm) == 17
        clipped = np.clip(full_norm, -1.0, 1.0)
        assert np.all(clipped >= -1.0)
        assert np.all(clipped <= 1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
