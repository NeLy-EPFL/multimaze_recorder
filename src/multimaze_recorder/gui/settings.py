from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
import os
import json
import platform

_CONFIG_DIR = Path(__file__).parent / "config"


class Settings:
    def __init__(self):
        self.user = os.environ.get("MMRECORDER_USER", "MD")
        self.config_dir = _CONFIG_DIR

        self.local_path = Path(
            os.environ.get("MMRECORDER_LOCAL_PATH", Path.home() / "Videos")
        )

        if platform.system() == "Darwin":
            default_data = f"/Volumes/upramdya/data/{self.user}/"
        else:
            default_data = f"/mnt/upramdya_data/{self.user}/"

        self.datafolder = Path(
            os.environ.get("MMRECORDER_DATA_PATH", default_data)
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

    def _resolve_config_path(self, relative_path: str) -> Path:
        """Resolve a config-relative path to an absolute Path."""
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
