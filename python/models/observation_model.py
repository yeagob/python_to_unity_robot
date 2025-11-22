from dataclasses import dataclass
from typing import List


@dataclass
class ObservationModel:
    """Observation data received from Unity simulation."""

    joint_angles: List[float]
    tool_center_point_position: List[float]
    direction_to_target: List[float]
    distance_to_target: float
    gripper_state: float
    is_gripping_object: bool
    laser_sensor_hit: bool
    laser_sensor_distance: float
    collision_detected: bool
    target_orientation_one_hot: List[float]
    is_reset_frame: bool

    @classmethod
    def from_dictionary(cls, data: dict) -> "ObservationModel":
        """Create ObservationModel from Unity JSON response dictionary."""
        return cls(
            joint_angles=data.get("JointAngles", [0.0] * 6),
            tool_center_point_position=data.get("ToolCenterPointPosition", [0.0, 0.0, 0.0]),
            direction_to_target=data.get("DirectionToTarget", [0.0, 0.0, 0.0]),
            distance_to_target=data.get("DistanceToTarget", 0.0),
            gripper_state=data.get("GripperState", 1.0),
            is_gripping_object=data.get("IsGrippingObject", False),
            laser_sensor_hit=data.get("LaserSensorHit", False),
            laser_sensor_distance=data.get("LaserSensorDistance", 1.0),
            collision_detected=data.get("CollisionDetected", False),
            target_orientation_one_hot=data.get("TargetOrientationOneHot", [1.0, 0.0]),
            is_reset_frame=data.get("IsResetFrame", False)
        )

    def to_dictionary(self) -> dict:
        """Convert to dictionary for testing purposes."""
        return {
            "JointAngles": self.joint_angles,
            "ToolCenterPointPosition": self.tool_center_point_position,
            "DirectionToTarget": self.direction_to_target,
            "DistanceToTarget": self.distance_to_target,
            "GripperState": self.gripper_state,
            "IsGrippingObject": self.is_gripping_object,
            "LaserSensorHit": self.laser_sensor_hit,
            "LaserSensorDistance": self.laser_sensor_distance,
            "CollisionDetected": self.collision_detected,
            "TargetOrientationOneHot": self.target_orientation_one_hot,
            "IsResetFrame": self.is_reset_frame
        }
