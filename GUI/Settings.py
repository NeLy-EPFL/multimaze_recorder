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

    def update_settings(self, experiment_name):
        # Find the experiment with the matching name
        experiment = next(
            (exp for exp in self.experiments if exp["name"] == experiment_name), None
        )

        if experiment is not None:
            # Update the experiment type
            self.experiment_type = experiment["name"]

            # Update the experiment path
            self.experiment_path = self.datafolder / Path(experiment["path"])

            # Update the metadata template, use default if not specified
            self.metadata_template = (
                Path(experiment["metadata_template"])
                if "metadata_template" in experiment
                else Path("Metadata_Templates/variables_registry_Standard.json")
            )

            # Update the camera settings, use default if not specified
            self.camera_settings = (
                experiment["camera_settings"]
                if "camera_settings" in experiment
                else "Presets/standard_set.json"
            )

            # Optionally, print or log the updated settings
            print(f"Updated settings: Experiment type: {self.experiment_type}")
            print(f"Associated path: {self.experiment_path}")
            print(f"Metadata file: {self.metadata_template}")
            print(f"Camera settings: {self.camera_settings}")
        else:
            print(f"No experiment found with the name: {experiment_name}")
