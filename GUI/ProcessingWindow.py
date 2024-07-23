from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from Utilities import CustomTableWidget, ExperimentSettings

import sys
from pathlib import Path


# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import subprocess
import os
import json
import time


class ProcessingWindowSignals(QObject):
    """This class defines the signals that are emitted by the ProcessingWindow class.
    It is used to connect the signals emitted by the ProcessingWindow class to the slots in the MainWindow class, which can be redirected to ExperimentWindow class, for instance to open a folder select in PW and show it in EW.
    """

    openDataFolderRequested = pyqtSignal(Path)


class ProcessingWindow(QWidget):
    def __init__(self, tab_widget, main_window):
        super().__init__()

        self.data_folder = Path("/mnt/upramdya_data/MD/")

        self.main_window = main_window

        self.signals = ProcessingWindowSignals()
        self.tab_widget = tab_widget
        # Store a reference to the experiment window
        # self.experiment_window = ExperimentWindow(self.tab_widget, self.main_window)

        self.settings = ExperimentSettings()

        # Create a horizontal layout for the central widget
        layout = QHBoxLayout()

        process_layout = QVBoxLayout()

        layout.addLayout(process_layout)
        # Create buttons for the processing window
        crop_button = QPushButton("Crop Images")
        crop_button.clicked.connect(self.on_crop_button_clicked)
        process_layout.addWidget(crop_button)

        check_crops = QPushButton("Check Crops")
        check_crops.clicked.connect(self.on_check_crops_clicked)
        process_layout.addWidget(check_crops)

        make_videos_button = QPushButton("Make Videos")
        make_videos_button.clicked.connect(self.on_make_videos_button_clicked)
        process_layout.addWidget(make_videos_button)

        track_videos_button = QPushButton("Track Videos")
        track_videos_button.clicked.connect(self.on_track_videos_button_clicked)
        process_layout.addWidget(track_videos_button)

        check_tracks_button = QPushButton("Check Tracks")
        check_tracks_button.clicked.connect(self.on_check_tracks_button_clicked)
        process_layout.addWidget(check_tracks_button)

        # Create a vertical layout for the folder lists
        folder_layout = QVBoxLayout()
        layout.addLayout(folder_layout)

        # Create a refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.populate_folder_lists)
        folder_layout.addWidget(refresh_button)

        # Create a search bar for the processing window
        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.filter_folders)
        # Add the search bar to the folder layout
        search_bar_label = QLabel("Search:")
        folder_layout.addWidget(search_bar_label)
        folder_layout.addWidget(self.search_bar)

        # self.remote_path = self.experiment_window.experiment_path
        # Initialize remote_path with a default value
        self.remote_path = Path.home()

        # Create a label and list widget for the data path folders
        self.data_path_label = QLabel(f"Lab server videos: ({self.remote_path})")
        folder_layout.addWidget(self.data_path_label)
        self.data_path_folder_list = QListWidget()
        folder_layout.addWidget(self.data_path_folder_list)

        # Create a label and list widget for the local path folders
        local_path_label = QLabel("Recorded Videos:")
        folder_layout.addWidget(local_path_label)
        self.local_path_folder_list = QListWidget()
        folder_layout.addWidget(self.local_path_folder_list)

        self.experiment_type = "Standard"

        # Populate the list widgets with the folders
        self.populate_folder_lists()

        self.setLayout(layout)

    def update_experiment_type(self, experiment_type):
        self.experiment_type = experiment_type

        for experiment in self.settings.experiments:
            if experiment["name"] == experiment_type:
                newpath = experiment["path"]
                break
        # Update the remote path based on the experiment type

        self.update_remote_path(newpath)

        self.populate_folder_lists()

        print(f"Experiment type updated to {self.experiment_type}")

    def set_experiment_path(self, experiment_path):
        # Ensure experiment_path is a Path object
        self.remote_path = Path(experiment_path)
        # Update the label text
        self.data_path_label.setText(f"Lab server videos: ({self.remote_path})")

    def update_remote_path(self, new_path):
        # Ensure new_path is a Path object
        self.remote_path = self.data_folder / Path(new_path)
        print(f"Updating remote path to {self.remote_path}")
        # Update the label to reflect the new path
        self.data_path_label.setText(f"Lab server videos: ({self.remote_path})")

    def on_crop_button_clicked(self):
        # Launch the terminal and run the run_processimages command
        if self.main_window.local:
            subprocess.Popen(["gnome-terminal", "--", "run_processimages"])

        elif self.main_window.online:
            # Run the SSH command with nohup on macOS without opening a new Terminal window
            remote_user = "matthias"
            remote_host = "mmrecorder"
            remote_command = (
                "bash /home/matthias/Tracking_Analysis/Tracktor/ProcessImages.sh"
            )
            ssh_command = f"ssh {remote_user}@{remote_host} {remote_command}"
            nohup_command = f"nohup {ssh_command} > /dev/null 2>&1 &"
            result = subprocess.run(
                nohup_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Check if the command completed successfully
            if result.returncode == 0:
                print("The command was successfully run.")
            else:
                print(f"The command failed with exit code {result.returncode}.")
                print(f"Error output: {result.stderr.decode()}")

            # Unavailable method
            # QMessageBox.information(self, "Information", "This command is not yet implemented for remote execution and should be run from the workstation.")
            # return

        else:
            QMessageBox.information(
                self,
                "Information",
                "Experimental workstation is not reachable. Command cannot be executed.",
            )
            return

        self.populate_folder_lists()

    def on_check_crops_clicked(self):
        # Launch the terminal and run the check_crops command
        if self.main_window.local:
            subprocess.Popen(["gnome-terminal", "--", "check_crops"])

        else:
            # Run the SSH command in a new Terminal window on macOS
            remote_user = "matthias"
            remote_host = "mmrecorder"
            remote_command = (
                "bash /home/matthias/Tracking_Analysis/Tracktor/CheckCrops.sh"
            )
            ssh_command = f"ssh {remote_user}@{remote_host} {remote_command}; exit"
            os.system(
                f'osascript -e \'tell application "Terminal" to do script "{ssh_command}"\''
            )

            # Wait for the check_crops command to finish
            while True:
                time.sleep(1)
                result = subprocess.run(
                    ["pgrep", "-f", remote_command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if result.returncode != 0:
                    break

            # Call the populate_folder_lists function
            self.populate_folder_lists()

    def on_make_videos_button_clicked(self):
        # Launch the terminal and run the run_makevideos command
        if self.main_window.local:

            subprocess.Popen(
                [
                    "gnome-terminal",
                    "--",
                    "/bin/bash",
                    "/home/matthias/Tracking_Analysis/Tracktor/MakeVideos.sh",
                ]
            )

        else:
            # Run the SSH command with nohup on macOS without opening a new Terminal window
            remote_user = "matthias"
            remote_host = "mmrecorder"
            remote_command = (
                "bash /home/matthias/Tracking_Analysis/Tracktor/MakeVideos.sh"
            )
            ssh_command = f"ssh {remote_user}@{remote_host} {remote_command}"
            nohup_command = f"nohup {ssh_command} > /dev/null 2>&1 &"
            result = subprocess.run(
                nohup_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Check if the command completed successfully
            if result.returncode == 0:
                print("The command was successfully run.")
            else:
                print(f"The command failed with exit code {result.returncode}.")
                print(f"Error output: {result.stderr.decode()}")

            self.populate_folder_lists()

    def on_track_videos_button_clicked(self):
        # Launch the terminal and run the balltracker command
        if self.main_window.local:
            subprocess.Popen(["gnome-terminal", "--", "balltracker"])

        else:
            QMessageBox.information(
                self,
                "Information",
                "This command is not yet implemented for remote execution and should be run from the workstation.",
            )
            return

    def on_check_tracks_button_clicked(self):
        if self.main_window.local:
            subprocess.Popen(["gnome-terminal", "--", "check_tracks"])

        else:
            # Run the SSH command with nohup on macOS without opening a new Terminal window
            remote_user = "matthias"
            remote_host = "mmrecorder"
            remote_command = (
                "bash /home/matthias/Tracking_Analysis/Tracktor/CheckTracks.sh"
            )
            ssh_command = f"ssh {remote_user}@{remote_host} {remote_command}"
            nohup_command = f"nohup {ssh_command} > /dev/null 2>&1 &"
            result = subprocess.run(
                nohup_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Check if the command completed successfully
            if result.returncode == 0:
                print("The command was successfully run.")
            else:
                print(f"The command failed with exit code {result.returncode}.")
                print(f"Error output: {result.stderr.decode()}")

    def check_metadata(self, folder) -> bool:
        # Load the variables registry

        # if self.experiment_window.current_experiment_type == "Standard":
        #     with open("Metadata_Registries/variables_registry_Standard.json", "r") as f:
        #         variables_registry = json.load(f)
        # elif self.experiment_window.current_experiment_type == "BallPushing":
        #     with open(
        #         "Metadata_Registries/variables_registry_BallPushing.json", "r"
        #     ) as f:
        #         variables_registry = json.load(f)

        # Check if the current experiment type has a corresponding metadata registry and if so load it, else load an empty registry

        # for experiment in self.settings.experiments:
        #     if experiment["name"] == self.experiment_type:
        #         if experiment["metadata_registry"]:
        #             with open(experiment["metadata_registry"], "r") as f:
        #                 variables_registry = json.load(f)
        #         break

        # else:
        #     variables_registry = {}

        # Load the metadata file
        metadata_path = Path(folder) / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            return False

        # Check if all variables from the registry are present in the metadata
        # if not all(variable in metadata["Variable"] for variable in variables_registry):
        #     return False

        # Check if all columns have an associated value for each variable
        for variable, values in metadata.items():
            if variable != "Variable":
                if not all(value != "" for value in values):
                    return False

        return True

    def populate_folder_lists(self):
        # Clear the list widgets
        self.data_path_folder_list.clear()
        self.local_path_folder_list.clear()

        # Get the data path from the experiment window
        data_path = self.remote_path

        print(data_path)

        # Add the folders from the data path to the data path list widget
        if data_path.exists():
            for folder in data_path.iterdir():
                if folder.is_dir():
                    item = QListWidgetItem(folder.name)
                    if any(
                        folder.name.endswith(suffix)
                        for suffix in [
                            "_Tracked",
                        ]
                    ):
                        if self.check_metadata(folder):
                            item.setForeground(QColor("green"))
                        else:
                            item.setForeground(QColor("orange"))
                    elif any(
                        folder.name.endswith(suffix)
                        for suffix in ["_Videos", "_Checked"]
                    ):
                        item.setForeground(QColor("red"))
                    else:
                        item.setForeground(QColor("gray"))
                    self.data_path_folder_list.addItem(item)

        # Add the folders from the local path to the local path list widget
        if self.main_window.local:
            local_path = Path("/home/matthias/Videos/")
            for folder in local_path.iterdir():
                if folder.is_dir():
                    item = QListWidgetItem(folder.name)
                    if any(
                        folder.name.endswith(suffix)
                        for suffix in ["_Tracked", "_Videos", "_Checked"]
                    ):
                        item.setForeground(QColor("green"))
                    else:
                        item.setForeground(QColor("gray"))
                    self.local_path_folder_list.addItem(item)

        else:
            # Set the remote hostname and username
            remote_host = "mmrecorder"
            remote_user = "matthias"

            # Set the remote path to list the folders
            remote_path = "/home/matthias/Videos/"

            # Run the 'ls' command on the remote machine using the 'ssh' command
            ssh_command = f"ssh {remote_user}@{remote_host} ls -d {remote_path}*/"
            result = subprocess.run(
                ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Check if the command completed successfully
            if result.returncode == 0:
                # Get the list of folders from the command output
                folder_names = result.stdout.decode().splitlines()

                # Add the folders to the GUI
                for folder_name in folder_names:
                    folder_name = Path(folder_name).name
                    item = QListWidgetItem(folder_name)
                    if any(folder_name.endswith(suffix) for suffix in ["_Checked"]):
                        item.setForeground(QColor("green"))
                    elif any(folder_name.endswith(suffix) for suffix in ["_Recorded"]):
                        item.setForeground(QColor("blue"))
                    elif any(
                        folder_name.endswith(suffix)
                        for suffix in ["_Cropped", "_Processing"]
                    ):
                        item.setForeground(QColor("orange"))
                    else:
                        item.setForeground(QColor("red"))
                    self.local_path_folder_list.addItem(item)
            else:
                # Print an error message if the command failed
                print(f"Error: {result.stderr.decode()}")

        self.data_path_folder_list.itemClicked.connect(self.on_data_path_folder_clicked)

        # Sort the items in the list
        self.data_path_folder_list.sortItems()
        self.local_path_folder_list.sortItems()

    def filter_folders(self, text):
        for i in range(self.data_path_folder_list.count()):
            item = self.data_path_folder_list.item(i)
            item.setHidden(text not in item.text())
        for i in range(self.local_path_folder_list.count()):
            item = self.local_path_folder_list.item(i)
            item.setHidden(text not in item.text())

    def on_data_path_folder_clicked(self, item):
        # Get the name of the clicked folder
        folder_name = item.text()

        folder_path = self.remote_path / folder_name
        # Send a signal to the main window to open the folder in the experiment window
        self.signals.openDataFolderRequested.emit(folder_path)
