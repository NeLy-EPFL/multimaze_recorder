from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from multimaze_recorder.gui.widgets import CustomTableWidget, Metadata

import sys
import time
import threading
import subprocess
import os
import json
import platform
import numpy as np
from pathlib import Path


class ExperimentWindowSignals(QObject):
    experiment_typeChanged = pyqtSignal(str)
    folder_created = pyqtSignal()


class ExperimentWindow(QWidget):
    def __init__(self, tab_widget, main_window, *args, **kwargs):
        super(ExperimentWindow, self).__init__(*args, **kwargs)

        self.main_window = main_window
        self.metadata = Metadata(self, new=True)
        self.signals = ExperimentWindowSignals()
        self.tab_widget = tab_widget

        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 10000)
        self.duration_spinbox.setValue(3600)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 30)
        self.fps_spinbox.setValue(30)
        self.fps_label = QLabel()

        self.experiment_type_selector = QComboBox()
        for experiment in self.main_window.settings.experiments:
            self.experiment_type_selector.addItem(experiment["name"])
        self.experiment_type_selector.addItem("New Experiment")
        self.experiment_type_selector.currentIndexChanged.connect(
            self.on_experiment_type_changed
        )

        self.folder_lineedit = QLineEdit()
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.on_button_clicked)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop_button_clicked)

        self.HardwareTrigger_checkbox = QCheckBox("Hardware Trigger")
        self.HardwareTrigger_checkbox.stateChanged.connect(
            self.on_hardware_checkbox_state_changed
        )

        self.metadata_folder = self.main_window.settings.config_dir / "Metadata_Templates"
        metadata_list = [f.stem for f in self.metadata_folder.glob("*.json")]

        self.template_selector = QComboBox()
        for template in metadata_list:
            self.template_selector.addItem(template)
        self.template_selector.addItem("New template")
        self.template_selector.currentIndexChanged.connect(self.select_metadata)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Experiment type:"))
        layout.addWidget(self.experiment_type_selector)
        layout.addWidget(QLabel("Duration:"))
        layout.addWidget(self.duration_spinbox)
        layout.addWidget(self.fps_label)
        layout.addWidget(self.fps_spinbox)
        layout.addWidget(QLabel("Folder:"))
        layout.addWidget(self.folder_lineedit)

        hbox_record = QHBoxLayout()
        hbox_record.addWidget(self.record_button)
        hbox_record.addWidget(self.HardwareTrigger_checkbox)
        layout.addLayout(hbox_record)

        hbox_style = QHBoxLayout()
        hbox_style.addWidget(QLabel("Metadata:"))
        hbox_style.addWidget(self.template_selector)

        layout.addLayout(hbox_style)

        self.table = CustomTableWidget(self)
        self.table_style_selector = QComboBox()
        self.table_style_selector.addItems(["arenas", "corridors"])
        self.table_style_selector.currentIndexChanged.connect(
            self.table.update_table_style
        )
        hbox_style.addWidget(QLabel("Table layout:"))
        hbox_style.addWidget(self.table_style_selector)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.recording_thread = None
        self.folder_path = None
        self.folder_open = False

        # Default to snap recording; switch to trigger if configured serial port exists
        self._set_recording_mode(hardware=False)
        if os.path.exists(self.main_window.settings.serial_port):
            self.HardwareTrigger_checkbox.setEnabled(True)
            self.HardwareTrigger_checkbox.setChecked(True)
        else:
            self.HardwareTrigger_checkbox.setEnabled(False)

    def _set_recording_mode(self, hardware: bool):
        if hardware:
            self._recording_module = "multimaze_recorder.scripts.trigger"
            self.fps_spinbox.setRange(16, 29)
            self.fps_spinbox.setValue(29)
            self.fps_label.setText("FPS (range: 16-29):")
        else:
            self._recording_module = "multimaze_recorder.scripts.snap"
            self.fps_spinbox.setRange(1, 30)
            self.fps_spinbox.setValue(30)
            self.fps_label.setText("FPS (range: 1-30):")
        print(f"Recording module: {self._recording_module}")

    def close_folder(self):
        if not self.folder_open:
            return
        self.folder_open = False
        self.metadata.load_template(self)
        self.table.set_metadata(self)
        self.folder_lineedit.clear()
        self.folder_path = None
        self.folder_lineedit.setDisabled(False)
        self.table_style_selector.setDisabled(False)
        self.experiment_type_selector.setDisabled(False)
        self.template_selector.setDisabled(False)

    def on_hardware_checkbox_state_changed(self, state):
        self._set_recording_mode(hardware=(state == 2))

    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()
        camera_settings = str(self.main_window.settings.camera_settings)

        if not self.folder_open:
            self.create_data_folder()
            if not self.folder_path:
                return
        else:
            self.save_data()

        np.save(self.folder_path / "fps.npy", fps)
        np.save(self.folder_path / "duration.npy", duration)

        self.stop_live_stream()
        self.record_button.setEnabled(False)
        self.duration_spinbox.setEnabled(False)
        self.fps_spinbox.setEnabled(False)

        print(f"Recording module: {self._recording_module}")

        if self.main_window.local:
            self.recording_thread = threading.Thread(
                target=self.record_images,
                args=(self._recording_module, folder, fps, duration, camera_settings),
            )
            self.recording_thread.start()
        else:
            QMessageBox.information(
                self,
                "Information",
                "Experiment recording is only possible on the Maze recorder workstation",
            )

    def record_images(self, module, folder, fps, duration, camera_settings):
        env = os.environ.copy()
        env["MMRECORDER_LOCAL_PATH"] = str(self.main_window.settings.local_path)
        env["QT_LOGGING_RULES"] = "*.warning=false"
        subprocess.run(
            [sys.executable, "-m", module, folder, str(fps), str(duration), camera_settings],
            env=env,
        )
        time.sleep(1)
        self.start_live_stream()
        self.record_button.setEnabled(True)
        self.duration_spinbox.setEnabled(True)
        self.fps_spinbox.setEnabled(True)

    def on_stop_button_clicked(self):
        if self.recording_thread and self.recording_thread.is_alive():
            # Thread cannot be directly terminated; best effort via process kill
            print("Stop requested – recording will finish current frame cycle")

    def start_live_stream(self):
        if self.main_window.local:
            env = os.environ.copy()
            env["MMRECORDER_PRESETS"] = str(self.main_window.settings.camera_settings)
            self.live_stream_process = subprocess.Popen(
                [sys.executable, "-m", "multimaze_recorder.scripts.livestream"],
                env=env,
            )

    def stop_live_stream(self):
        if hasattr(self, "live_stream_process"):
            self.live_stream_process.terminate()

    def check_data_access(self):
        if not self.main_window.settings.datafolder.exists():
            QMessageBox.critical(
                self,
                "Error",
                "Cannot access the data folder. Check labserver connection.",
            )
            return False

    def on_experiment_type_changed(self, index):
        if self.experiment_type_selector.currentText() == "New Experiment":
            new_experiment_index = self.experiment_type_selector.findText("New Experiment")
            if new_experiment_index != -1:
                self.experiment_type_selector.removeItem(new_experiment_index)

            new_exp_name = self.main_window.settings.create_new_experiment(self)
            self.experiment_type_selector.addItem("New Experiment")

            if new_exp_name:
                index = next(
                    (
                        i
                        for i, exp in enumerate(self.main_window.settings.experiments)
                        if exp["name"] == new_exp_name
                    ),
                    -1,
                )
                if index != -1:
                    self.experiment_type_selector.insertItem(index, new_exp_name)
                    self.experiment_type_selector.setCurrentIndex(index)
                else:
                    print("Error: New experiment was not added correctly.")
                    return
            else:
                if self.experiment_type_selector.count() > 0:
                    self.experiment_type_selector.setCurrentIndex(0)
                return

        if 0 <= index < len(self.main_window.settings.experiments):
            self.signals.experiment_typeChanged.emit(
                self.main_window.settings.experiments[index]["name"]
            )
        else:
            print("Error: Invalid experiment index.")
            return

        self.metadata.load_template(self)
        self.template_selector.setCurrentIndex(
            self.template_selector.findText(
                self.main_window.settings.metadata_template.stem
            )
        )
        self.table.set_metadata(self)
        print(f"Selected experiment type: {self.main_window.settings.experiment_type}")

    def select_metadata(self, index):
        if self.template_selector.currentText() == "New template":
            template_name, ok = QInputDialog.getText(
                self, "New Metadata Template", "Enter new template name:"
            )
            if not ok:
                return
            registry = self.metadata_folder / f"{template_name}.json"
            self.metadata.create_template(self, registry)
            self.template_selector.addItem(template_name)
            self.template_selector.setCurrentIndex(
                self.template_selector.findText(template_name)
            )
            self.metadata.load_template(self, registry)
            self.table.set_metadata(self)
        else:
            registry = self.metadata_folder / f"{self.template_selector.currentText()}.json"
            self.metadata.load_template(self, registry)
            self.table.set_metadata(self)

    def create_data_folder(self):
        if self.check_data_access() == False:
            QMessageBox.information(
                self,
                "Information",
                "Data folder is not accessible. The folder couldn't be created.",
            )
            return

        if self.folder_open:
            folder_name, ok = QInputDialog.getText(
                self, "New Data Folder", "Enter new folder name:"
            )
            if not ok:
                return

            experiment_type, ok = QInputDialog.getItem(
                self,
                "Choose Experiment Type",
                "Choose an experiment type for the new data folder:",
                [exp["name"] for exp in self.main_window.settings.experiments],
                0,
                False,
            )
            if not ok:
                return

            self.main_window.settings.experiment_type = experiment_type
            index = self.experiment_type_selector.findText(experiment_type)

            if experiment_type == "BallPushing":
                table_style, ok = QInputDialog.getItem(
                    self,
                    "Choose Table Style",
                    "Choose a table style for the new data folder:",
                    ["arenas", "corridors"],
                    0,
                    False,
                )
            else:
                table_style = "arenas"

            self.folder_path = self.main_window.settings.experiment_path / folder_name
            while self.folder_path.exists():
                folder_name, ok = QInputDialog.getText(
                    self,
                    "Folder Already Exists",
                    f"The folder '{folder_name}' already exists. Enter a new name:",
                )
                if not ok:
                    return
                self.folder_path = self.main_window.settings.experiment_path / folder_name

            self.folder_path.mkdir(parents=True, exist_ok=True)
            self.folder_lineedit.setText(str(self.folder_path))
            self.open_data_folder(self.folder_path)

        else:
            folder_name = self.folder_lineedit.text()
            if not folder_name:
                folder_name, ok = QInputDialog.getText(
                    self, "New Data Folder", "Enter new folder name:"
                )
                if not ok:
                    return

            self.folder_path = self.main_window.settings.experiment_path / folder_name
            while self.folder_path.exists():
                folder_name, ok = QInputDialog.getText(
                    self,
                    "Folder Already Exists",
                    f"The folder '{folder_name}' already exists. Enter a new name:",
                )
                if not ok:
                    return
                self.folder_path = self.main_window.settings.experiment_path / folder_name

            self.folder_path.mkdir(parents=True, exist_ok=True)
            self.folder_lineedit.setText(str(self.folder_path))
            self.open_data_folder(self.folder_path)

    def open_data_folder(self, folder_path=None, recorded=False):
        if self.folder_path and str(self.main_window.settings.datafolder) not in str(folder_path):
            pass

        if not folder_path:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Open Data Folder", str(self.main_window.settings.datafolder)
            )

        if not folder_path:
            return

        self.folder_path = Path(folder_path)

        if not self.folder_path.glob("*.mp4"):
            pass

        metadata_path = self.folder_path / "metadata.json"

        if not metadata_path.is_file():
            self.metadata.save_metadata(self)
        else:
            self.metadata.load_metadata(self)

        self.folder_open = True
        self.folder_lineedit.setDisabled(True)
        self.table_style_selector.setDisabled(True)
        self.experiment_type_selector.setDisabled(True)
        self.template_selector.setDisabled(True)

        self.table.set_metadata(self)

        if self.layout().count() > 0:
            folder_label = QLabel(f"Folder: {self.folder_path}")
            self.layout().addWidget(folder_label)

        if (self.folder_path / "duration.npy").exists():
            self.duration_spinbox.setValue(
                int(np.load(self.folder_path / "duration.npy"))
            )
        if (self.folder_path / "fps.npy").exists():
            self.fps_spinbox.setValue(int(np.load(self.folder_path / "fps.npy")))

        self.folder_lineedit.setText(str(self.folder_path.name))

        self.signals.folder_created.emit()

    def check_images(self, folder_path):
        if not list(folder_path.glob("*.jpg")):
            return False
        return True

    def save_data(self):
        if not self.folder_path:
            return False
        self.metadata.save_metadata(self)
        self.metadata.update_template(self)
        return True

    def has_unsaved_changes(self):
        if not self.folder_path:
            return False
        saved = self.metadata.load_metadata(self, update_self=False)
        current = dict(self.metadata)
        return saved != current
