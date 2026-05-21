from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
from platformdirs import user_config_dir
import os
import re
import glob
import json
import platform

_CONFIG_DIR = Path(__file__).parent / "config"
_USER_SETTINGS_FILE = Path(user_config_dir("mmrecorder")) / "settings.json"
_LAB_SERVER_CANDIDATES = [
    Path("/mnt/upramdya_data"),
    Path("/mnt/upramdya/data"),
    Path("/Volumes/upramdya/data"),  # macOS
]


class Settings:
    def __init__(self):
        self.config_dir = _CONFIG_DIR
        user_cfg = self._load_user_config()

        # Priority: env var → saved config file → default
        self.user = os.environ.get("MMRECORDER_USER") or user_cfg.get("user", "MD")

        self.local_path = Path(
            os.environ.get("MMRECORDER_LOCAL_PATH")
            or user_cfg.get("local_path", str(Path.home() / "Videos"))
        )

        if platform.system() == "Darwin":
            default_data = f"/Volumes/upramdya/data/{self.user}/"
        else:
            default_data = f"/mnt/upramdya_data/{self.user}/"

        self.datafolder = Path(
            os.environ.get("MMRECORDER_DATA_PATH")
            or user_cfg.get("data_path", default_data)
        )

        self.remote_host = (
            os.environ.get("MMRECORDER_REMOTE_HOST")
            or user_cfg.get("remote_host", "mmrecorder")
        )

        self.serial_port = (
            os.environ.get("MMRECORDER_SERIAL_PORT")
            or user_cfg.get("serial_port", "/dev/ttyACM0")
        )

        self.experiments = self.load_experiments()
        self.experiment_type = self.experiments[0]["name"] if self.experiments else None
        self.experiment_path = (
            self.datafolder / Path(self.experiments[0]["path"])
            if self.experiments
            else self.datafolder
        )
        self.metadata_template = self._resolve_config_path(
            self.experiments[0].get(
                "metadata_template",
                "Metadata_Templates/variables_registry_Standard.json",
            )
            if self.experiments
            else "Metadata_Templates/variables_registry_Standard.json"
        )
        self.camera_settings = self._resolve_config_path(
            self.experiments[0].get("camera_settings", "Presets/standard_set.json")
            if self.experiments
            else "Presets/standard_set.json"
        )

        print(f"Initialisation settings: Experiment type: {self.experiment_type}")
        print(f"Associated path: {self.experiment_path}")
        print(f"metadata file: {self.metadata_template}")
        print(f"camera settings: {self.camera_settings}")

    @staticmethod
    def detect_server() -> Path | None:
        """Return the first lab server mount point that exists, or None."""
        for candidate in _LAB_SERVER_CANDIDATES:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def discover_users(server_root: Path) -> list[str]:
        """Return sorted list of user directories (2–4 capital letters) on the server."""
        pattern = re.compile(r'^[A-Z]{2,4}$')
        if not server_root.exists():
            return []
        return sorted([
            d.name for d in server_root.iterdir()
            if d.is_dir() and pattern.match(d.name)
        ])

    @staticmethod
    def list_serial_ports() -> list[str]:
        """Return sorted list of connected serial ports (Arduino-compatible)."""
        return sorted(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))

    def _load_user_config(self) -> dict:
        if _USER_SETTINGS_FILE.exists():
            try:
                with open(_USER_SETTINGS_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def save_user_config(self):
        _USER_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_USER_SETTINGS_FILE, "w") as f:
            json.dump({
                "user": self.user,
                "local_path": str(self.local_path),
                "data_path": str(self.datafolder),
                "remote_host": self.remote_host,
                "serial_port": self.serial_port,
            }, f, indent=4)

    def apply_user_settings(self, user: str, data_path: str, local_path: str, remote_host: str, serial_port: str):
        self.user = user
        self.datafolder = Path(data_path)
        self.local_path = Path(local_path)
        self.remote_host = remote_host
        self.serial_port = serial_port
        if self.experiment_type:
            self.update_settings(self.experiment_type)
        self.save_user_config()

    def _resolve_config_path(self, relative_path: str) -> Path:
        return self.config_dir / relative_path

    def load_experiments(self):
        experiments_file = self.config_dir / "experiments.json"
        try:
            with open(experiments_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_experiments(self):
        with open(self.config_dir / "experiments.json", "w") as f:
            json.dump(self.experiments, f, indent=4)

    def add_experiment(self, name, path):
        self.experiments.append({"name": name, "path": str(path)})
        self.save_experiments()

    def create_new_experiment(self, parent):
        while True:
            name, ok = QInputDialog.getText(
                parent, "Experiment Name", "Enter the name of the new experiment:"
            )
            if ok and name:
                while True:
                    path = QFileDialog.getExistingDirectory(
                        parent, "Select Experiment Data Folder"
                    )
                    if not path:
                        return None
                    try:
                        relative_path = Path(path).relative_to(self.datafolder)
                        self.add_experiment(name, relative_path)
                        return name
                    except ValueError:
                        QMessageBox.warning(
                            parent,
                            "Invalid Folder Selection",
                            "The selected folder must be in your server data folder. "
                            "Please select another one.",
                        )
            else:
                return None

    def update_settings(self, experiment_name):
        print("Updating settings...")
        experiment = next(
            (exp for exp in self.experiments if exp["name"] == experiment_name), None
        )
        if experiment is not None:
            self.experiment_type = experiment["name"]
            self.experiment_path = self.datafolder / Path(experiment["path"])
            self.metadata_template = self._resolve_config_path(
                experiment.get(
                    "metadata_template",
                    "Metadata_Templates/variables_registry_Standard.json",
                )
            )
            self.camera_settings = self._resolve_config_path(
                experiment.get("camera_settings", "Presets/standard_set.json")
            )
            print(f"Updated settings: Experiment type: {self.experiment_type}")
            print(f"Associated path: {self.experiment_path}")
            print(f"Metadata file: {self.metadata_template}")
            print(f"Camera settings: {self.camera_settings}")
        else:
            print(f"No experiment found with the name: {experiment_name}")
