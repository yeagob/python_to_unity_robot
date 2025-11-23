from dataclasses import dataclass
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enums.command_type import CommandType


@dataclass
class CommandModel:
    """Command to send to Unity simulation.

    Uses PascalCase field names for Unity JsonUtility compatibility.
    """

    command_type: CommandType
    actions: Optional[List[float]] = None
    gripper_close_value: Optional[float] = None
    axis_6_orientation: Optional[float] = None
    simulation_mode_enabled: Optional[bool] = None

    def to_dictionary(self) -> dict:
        """Convert command to dictionary for JSON serialization.

        Uses PascalCase keys for Unity JsonUtility compatibility.
        """
        result: dict = {"Type": self.command_type.value}

        if self.actions is not None:
            result["Actions"] = self.actions

        if self.gripper_close_value is not None:
            result["GripperCloseValue"] = self.gripper_close_value

        if self.axis_6_orientation is not None:
            result["Axis6Orientation"] = self.axis_6_orientation

        if self.simulation_mode_enabled is not None:
            result["SimulationModeEnabled"] = self.simulation_mode_enabled

        return result
