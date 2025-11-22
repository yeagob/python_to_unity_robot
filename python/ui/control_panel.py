import threading
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RobotControlPanel:
    """Control panel for robot simulation and inference."""

    WINDOW_TITLE: str = "Robot Control Panel"
    WINDOW_GEOMETRY: str = "600x500"
    BUTTON_PADDING: int = 5
    FRAME_PADDING: int = 10

    def __init__(self) -> None:
        # Import here to make CustomTkinter optional
        import customtkinter as ctk

        self._ctk = ctk
        self._root: ctk.CTk = ctk.CTk()
        self._environment = None
        self._trained_model = None
        self._inference_thread: Optional[threading.Thread] = None
        self._is_inference_running: bool = False

        self._configure_window()
        self._create_mode_selection_frame()
        self._create_target_position_frame()
        self._create_control_buttons_frame()
        self._create_status_display()

    def run(self) -> None:
        """Start the control panel main loop."""
        self._root.mainloop()

    def _configure_window(self) -> None:
        """Configure main window properties."""
        self._root.title(self.WINDOW_TITLE)
        self._root.geometry(self.WINDOW_GEOMETRY)

    def _create_mode_selection_frame(self) -> None:
        """Create mode selection UI."""
        ctk = self._ctk
        mode_frame: ctk.CTkFrame = ctk.CTkFrame(self._root)
        mode_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        self._simulation_mode_variable = ctk.BooleanVar(value=False)

        simulation_mode_checkbox: ctk.CTkCheckBox = ctk.CTkCheckBox(
            mode_frame,
            text="Simulation Mode (Smooth Movement)",
            variable=self._simulation_mode_variable,
            command=self._handle_mode_change
        )
        simulation_mode_checkbox.pack(pady=self.BUTTON_PADDING)

    def _create_target_position_frame(self) -> None:
        """Create target position input UI."""
        ctk = self._ctk
        target_frame: ctk.CTkFrame = ctk.CTkFrame(self._root)
        target_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        title_label: ctk.CTkLabel = ctk.CTkLabel(target_frame, text="Target Position:")
        title_label.pack()

        self._target_position_entries: dict = {}
        axis_labels: list = ["X", "Y", "Z"]

        for axis_label in axis_labels:
            entry_frame: ctk.CTkFrame = ctk.CTkFrame(target_frame)
            entry_frame.pack(fill="x", pady=2)

            axis_name_label: ctk.CTkLabel = ctk.CTkLabel(entry_frame, text=f"{axis_label}:")
            axis_name_label.pack(side="left")

            position_entry: ctk.CTkEntry = ctk.CTkEntry(entry_frame, width=100)
            position_entry.insert(0, "0.3")
            position_entry.pack(side="left", padx=self.BUTTON_PADDING)

            self._target_position_entries[axis_label] = position_entry

    def _create_control_buttons_frame(self) -> None:
        """Create control buttons UI."""
        ctk = self._ctk
        buttons_frame: ctk.CTkFrame = ctk.CTkFrame(self._root)
        buttons_frame.pack(pady=self.FRAME_PADDING, padx=self.FRAME_PADDING, fill="x")

        connect_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Connect to Unity",
            command=self._handle_connect
        )
        connect_button.pack(pady=self.BUTTON_PADDING)

        load_model_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Load Trained Model",
            command=self._handle_load_model
        )
        load_model_button.pack(pady=self.BUTTON_PADDING)

        execute_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Execute Trajectory",
            command=self._handle_execute_trajectory
        )
        execute_button.pack(pady=self.BUTTON_PADDING)

        stop_button: ctk.CTkButton = ctk.CTkButton(
            buttons_frame,
            text="Stop Execution",
            command=self._handle_stop_execution
        )
        stop_button.pack(pady=self.BUTTON_PADDING)

    def _create_status_display(self) -> None:
        """Create status display label."""
        ctk = self._ctk
        self._status_label: ctk.CTkLabel = ctk.CTkLabel(
            self._root,
            text="Status: Disconnected"
        )
        self._status_label.pack(pady=self.FRAME_PADDING)

    def _handle_connect(self) -> None:
        """Handle connect button click."""
        try:
            from environments.unity_robot_environment import UnityRobotEnvironment
            self._environment = UnityRobotEnvironment()
            self._update_status("Status: Connected to Unity")
        except Exception as connection_error:
            self._update_status(f"Connection Error: {connection_error}")

    def _handle_mode_change(self) -> None:
        """Handle simulation mode toggle."""
        if self._environment is None:
            return

        enable_simulation_mode: bool = self._simulation_mode_variable.get()
        self._environment.set_simulation_mode(enable_simulation_mode)

        mode_name: str = "Simulation" if enable_simulation_mode else "Training"
        self._update_status(f"Status: Mode changed to {mode_name}")

    def _handle_load_model(self) -> None:
        """Handle load model button click."""
        try:
            from stable_baselines3 import PPO
            model_path: str = "./models/robot_policy_pick_and_place"
            self._trained_model = PPO.load(model_path)
            self._update_status("Status: Trained model loaded successfully")
        except Exception as load_error:
            self._update_status(f"Model Load Error: {load_error}")

    def _handle_execute_trajectory(self) -> None:
        """Handle execute trajectory button click."""
        if self._environment is None:
            self._update_status("Error: Not connected to Unity")
            return

        if self._trained_model is None:
            self._update_status("Error: No trained model loaded")
            return

        self._is_inference_running = True
        self._update_status("Status: Executing trajectory...")

        self._inference_thread = threading.Thread(
            target=self._execute_inference_loop,
            daemon=True
        )
        self._inference_thread.start()

    def _handle_stop_execution(self) -> None:
        """Handle stop execution button click."""
        self._is_inference_running = False
        self._update_status("Status: Execution stopped")

    def _execute_inference_loop(self) -> None:
        """Execute model inference in loop."""
        observation, _ = self._environment.reset()

        while self._is_inference_running:
            action, _ = self._trained_model.predict(observation, deterministic=True)
            observation, reward, terminated, truncated, info = self._environment.step(action)

            if terminated or truncated:
                if info.get("success", False):
                    self._update_status("Status: Task completed successfully!")
                else:
                    self._update_status("Status: Episode ended")
                break

        self._is_inference_running = False

    def _update_status(self, status_message: str) -> None:
        """Update status label text."""
        self._status_label.configure(text=status_message)


def main() -> None:
    """Main entry point for control panel."""
    control_panel: RobotControlPanel = RobotControlPanel()
    control_panel.run()


if __name__ == "__main__":
    main()
