from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
import json


class Settings:
    def __init__(self):

        self.user = "MD"

        self.datafolder = Path(f"/mnt/upramdya_data/{self.user}/")

        self.experiments = self.load_experiments()

        # Load the "name" of the first experiment
        self.experiment_type = self.experiments[0]["name"] if self.experiments else None

        # Load the "path" of the first experiment
        self.experiment_path = self.datafolder / Path(self.experiments[0]["path"])

        # Load the "metadata_template" of the first experiment if any
        self.metadata_template = (
            Path(self.experiments[0]["metadata_template"])
            if self.experiments and "metadata_template" in self.experiments[0]
            else Path("Metadata_Templates/variables_registry_Standard.json")
        )

        # Load the "camera_settings" of the first experiment if any, else load the default settings
        self.camera_settings = (
            self.experiments[0]["camera_settings"]
            if self.experiments and "camera_settings" in self.experiments[0]
            else "Presets/standard_set.json"
        )

        # Generate a message to display the initial settings of the GUI
        print(f"Initialisation settings: Experiment type: {self.experiment_type}")
        print(f"Associated path: {self.experiment_path}")
        print(f"metadata file: {self.metadata_template}")
        print(f"camera settings: {self.camera_settings}")

    def load_experiments(self):
        # Load experiments from a file or return a default list
        try:
            with open("experiments.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def save_experiments(self):
        with open("experiments.json", "w") as file:
            json.dump(self.experiments, file)

    def add_experiment(self, name, path):
        self.experiments.append({"name": name, "path": str(path)})
        self.save_experiments()

    def create_new_experiment(self, parent):
        while True:  # Start a loop to allow re-selection if the name is not provided
            name, ok = QInputDialog.getText(
                parent, "Experiment Name", "Enter the name of the new experiment:"
            )

            if ok and name:
                while True:  # Inner loop for folder selection
                    path = QFileDialog.getExistingDirectory(
                        parent, "Select Experiment Data Folder"
                    )
                    if not path:
                        return None  # User cancelled the dialog or closed it without selecting a path

                    try:
                        # Attempt to get the path difference between the data folder and the selected folder
                        relative_path = Path(path).relative_to(self.datafolder)
                        self.add_experiment(name, relative_path)
                        return name

                    except ValueError:
                        # The selected path is not a subpath of the datafolder
                        QMessageBox.warning(
                            parent,
                            "Invalid Folder Selection",
                            "The selected folder must be in your server data folder. Please select another one.",
                        )
                        # No return statement here, so the inner loop continues for folder selection
            else:  # User cancelled the dialog or closed it without entering a name
                return None
