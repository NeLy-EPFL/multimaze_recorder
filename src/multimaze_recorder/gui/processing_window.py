from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys
import os
import subprocess
import json
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_PROCESSING_DIR = _REPO_ROOT / "Processing"
_REMOTE_HOST = os.environ.get("MMRECORDER_REMOTE_HOST", "mmrecorder")
_REMOTE_USER = os.environ.get("MMRECORDER_REMOTE_USER", "matthias")
_REMOTE_REPO = os.environ.get("MMRECORDER_REMOTE_REPO", "/home/matthias/multimaze_recorder")


class ProcessingWindowSignals(QObject):
    openDataFolderRequested = pyqtSignal(Path)


class ProcessingWindow(QWidget):
    def __init__(self, tab_widget, main_window):
        super().__init__()

        self.main_window = main_window
        self.settings = main_window.settings
        self.signals = ProcessingWindowSignals()
        self.tab_widget = tab_widget

        layout = QHBoxLayout()
        process_layout = QVBoxLayout()
        layout.addLayout(process_layout)

        for label, handler in [
            ("Crop Images", self.on_crop_button_clicked),
            ("Check Crops", self.on_check_crops_clicked),
            ("Make Videos", self.on_make_videos_button_clicked),
            ("Track Videos", self.on_track_videos_button_clicked),
            ("Check Tracks", self.on_check_tracks_button_clicked),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            process_layout.addWidget(btn)

        folder_layout = QVBoxLayout()
        layout.addLayout(folder_layout)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.populate_folder_lists)
        folder_layout.addWidget(refresh_button)

        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.filter_folders)
        folder_layout.addWidget(QLabel("Search:"))
        folder_layout.addWidget(self.search_bar)

        self.remote_path = self.settings.experiment_path

        self.data_path_label = QLabel(f"Lab server videos: ({self.remote_path})")
        folder_layout.addWidget(self.data_path_label)
        self.data_path_folder_list = QListWidget()
        folder_layout.addWidget(self.data_path_folder_list)

        folder_layout.addWidget(QLabel("Recorded Videos:"))
        self.local_path_folder_list = QListWidget()
        folder_layout.addWidget(self.local_path_folder_list)

        self.experiment_type = "Standard"
        self.populate_folder_lists()
        self.setLayout(layout)

    def update_experiment_type(self, experiment_type):
        self.experiment_type = experiment_type
        for experiment in self.settings.experiments:
            if experiment["name"] == experiment_type:
                self.update_remote_path(experiment["path"])
                break
        self.populate_folder_lists()
        print(f"Experiment type updated to {self.experiment_type}")

    def set_experiment_path(self, experiment_path):
        self.remote_path = Path(experiment_path)
        self.data_path_label.setText(f"Lab server videos: ({self.remote_path})")

    def update_remote_path(self, new_path):
        self.remote_path = self.main_window.settings.datafolder / Path(new_path)
        print(f"Updating remote path to {self.remote_path}")
        self.data_path_label.setText(f"Lab server videos: ({self.remote_path})")

    def _run_local_script(self, script_path):
        """Launch a Processing shell script in a new terminal."""
        subprocess.Popen(["gnome-terminal", "--", "/bin/bash", str(script_path)])

    def _run_remote_script(self, script_name):
        """Run a Processing shell script on the remote host via SSH."""
        remote_command = f"bash {_REMOTE_REPO}/Processing/{script_name}"
        ssh_command = f"ssh {_REMOTE_USER}@{_REMOTE_HOST} {remote_command}"
        result = subprocess.run(
            f"nohup {ssh_command} > /dev/null 2>&1 &",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            print(f"Remote command failed: {result.stderr.decode()}")

    def on_crop_button_clicked(self):
        if self.main_window.local:
            self._run_local_script(_PROCESSING_DIR / "ProcessImages.sh")
        elif self.main_window.online:
            self._run_remote_script("ProcessImages.sh")
        else:
            QMessageBox.information(
                self,
                "Information",
                "Experimental workstation is not reachable.",
            )
            return
        self.populate_folder_lists()

    def on_check_crops_clicked(self):
        if self.main_window.local:
            self._run_local_script(_PROCESSING_DIR / "CheckCrops.sh")
        elif self.main_window.online:
            remote_command = f"bash {_REMOTE_REPO}/Processing/CheckCrops.sh"
            ssh_command = f"ssh {_REMOTE_USER}@{_REMOTE_HOST} {remote_command}; exit"
            os.system(
                f'osascript -e \'tell application "Terminal" to do script "{ssh_command}"\''
            )
        self.populate_folder_lists()

    def on_make_videos_button_clicked(self):
        if self.main_window.local:
            self._run_local_script(_PROCESSING_DIR / "MakeVideos.sh")
        elif self.main_window.online:
            self._run_remote_script("MakeVideos.sh")
        self.populate_folder_lists()

    def on_track_videos_button_clicked(self):
        if self.main_window.local:
            subprocess.Popen(["gnome-terminal", "--", "balltracker"])
        else:
            QMessageBox.information(
                self,
                "Information",
                "Tracking is not yet implemented for remote execution.",
            )

    def on_check_tracks_button_clicked(self):
        if self.main_window.local:
            self._run_local_script(_PROCESSING_DIR / "CheckTracks.sh")
        elif self.main_window.online:
            self._run_remote_script("CheckTracks.sh")

    def check_metadata(self, folder) -> bool:
        metadata_path = Path(folder) / "metadata.json"
        if not metadata_path.exists():
            return False
        with open(metadata_path) as f:
            metadata = json.load(f)
        for variable, values in metadata.items():
            if variable != "Variable":
                if not all(v != "" for v in values):
                    return False
        return True

    def populate_folder_lists(self):
        self.data_path_folder_list.clear()
        self.local_path_folder_list.clear()

        data_path = self.remote_path
        if data_path.exists():
            for folder in data_path.iterdir():
                if folder.is_dir():
                    item = QListWidgetItem(folder.name)
                    if any(folder.name.endswith(s) for s in ["_Tracked"]):
                        color = "green" if self.check_metadata(folder) else "orange"
                    elif any(folder.name.endswith(s) for s in ["_Videos", "_Checked"]):
                        color = "red"
                    else:
                        color = "gray"
                    item.setForeground(QColor(color))
                    self.data_path_folder_list.addItem(item)

        if self.main_window.local:
            local_path = self.settings.local_path
            if local_path.exists():
                for folder in local_path.iterdir():
                    if folder.is_dir():
                        item = QListWidgetItem(folder.name)
                        if any(folder.name.endswith(s) for s in ["_Tracked", "_Videos", "_Checked"]):
                            item.setForeground(QColor("green"))
                        else:
                            item.setForeground(QColor("gray"))
                        self.local_path_folder_list.addItem(item)
        else:
            remote_path_str = str(self.settings.local_path).rstrip("/") + "/"
            ssh_command = f"ssh {_REMOTE_USER}@{_REMOTE_HOST} ls -d {remote_path_str}*/"
            result = subprocess.run(
                ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                for folder_name in result.stdout.decode().splitlines():
                    folder_name = Path(folder_name).name
                    item = QListWidgetItem(folder_name)
                    if folder_name.endswith("_Checked"):
                        item.setForeground(QColor("green"))
                    elif folder_name.endswith("_Recorded"):
                        item.setForeground(QColor("blue"))
                    elif any(folder_name.endswith(s) for s in ["_Cropped", "_Processing"]):
                        item.setForeground(QColor("orange"))
                    else:
                        item.setForeground(QColor("red"))
                    self.local_path_folder_list.addItem(item)
            else:
                print(f"SSH list error: {result.stderr.decode()}")

        self.data_path_folder_list.itemClicked.connect(self.on_data_path_folder_clicked)
        self.data_path_folder_list.sortItems()
        self.local_path_folder_list.sortItems()

    def filter_folders(self, text):
        for lst in (self.data_path_folder_list, self.local_path_folder_list):
            for i in range(lst.count()):
                item = lst.item(i)
                item.setHidden(text not in item.text())

    def on_data_path_folder_clicked(self, item):
        folder_path = self.remote_path / item.text()
        self.signals.openDataFolderRequested.emit(folder_path)
