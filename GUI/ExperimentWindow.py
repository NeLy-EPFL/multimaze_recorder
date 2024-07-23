from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from Utilities import CustomTableWidget, ExperimentSettings

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))


import threading
import subprocess
import os
import json
import platform
import numpy as np


class ExperimentWindowSignals(QObject):
    """This class defines the signals for the ExperimentWindow class.
    It is used to define the signals that are emitted by the ExperimentWindow class to other windows of the GUI.
    """

    # experimentPathChanged = pyqtSignal(Path)
    experiment_typeChanged = pyqtSignal(str)


class ExperimentWindow(QWidget):
    def __init__(self, tab_widget, main_window, *args, **kwargs):
        super(ExperimentWindow, self).__init__(*args, **kwargs)

        """
        Experiment window
        
        This is the main window of the application.
        
        Attributes
        ----------
        tab_widget : QTabWidget
            The tab widget that contains the experiment window
        duration_spinbox : QSpinBox
            A spinbox widget for setting the duration of the recording
        fps_spinbox : QSpinBox
            A spinbox widget for setting the frame rate of the recording
        folder_lineedit : QLineEdit
            A line edit widget for entering the name of the data folder
        record_button : QPushButton
            A button widget for starting the recording process
        HardwareTrigger_checkbox : QCheckBox
            A checkbox widget for enabling hardware triggering
        stop_button : QPushButton
            A button widget for stopping the recording process
        table_style_selector : QComboBox
            A combo box widget for selecting the layout of the table
        table : QTableWidget
            A table widget for displaying the metadata
        folder_path : Path
            The path to the currently open data folder
        folder_open : bool
            A boolean indicating whether a data folder is currently open
        recording_thread : threading.Thread
            A thread for running the recording process
        live_stream_process : subprocess.Popen
            A process for running the live stream
        info_panel : QWidget
            A widget for displaying information about the currently open data folder
            
        Methods
        -------
        create_table(metadata=None)
            Create a new table widget using the provided metadata
        update_table_style(index)
            Update the table and metadata with the selected layout
        detect_table_style(metadata)
            Detect the layout of the table from the metadata
        close_folder()
            Close the currently open data folder
        on_button_clicked()
            Start the recording process
        on_hardware_checkbox_state_changed
            Enable or disable hardware triggering
        record_images(folder, fps, duration)
            Run the recording process with the selected settings
        on_stop_button_clicked()
            Terminate the recording thread
        start_live_stream()
            Start the live stream
        stop_live_stream()
            Stop the live stream
        create_metadata(table=None)
            Create a new metadata dictionary from the data in the table
        check_data_access()
            Check if the data folder can be accessed
        create_data_folder(metadata=None)
            Create a new data folder with the provided metadata
        open_data_folder(folder_path=None)
            Open an existing data folder
        save_data()
            Save the metadata to the currently open data folder
        has_unsaved_changes()
            Check if the metadata has unsaved changes
        
        """

        self.data_folder = Path("/mnt/upramdya_data/MD/")
        # TODO: put this somewhere else

        # Create widgets
        self.main_window = main_window
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
        self.settings = ExperimentSettings()
        self.populate_experiments()
        self.experiment_type_selector.currentIndexChanged.connect(
            self.on_experiment_type_changed
        )
        # Initialise the experiment type and path to the current experiment type
        self.set_experiment_path(0)

        # Emit the signal with the initial experiment path
        # self.signals.experimentPathChanged.emit(self.experiment_path)

        # Initialise the experiment type to the first item in the combo box with associated experiment path
        # self.current_experiment_type = self.experiment_type_selector.itemText(0)
        # self.experiment_path = self.data_folder / Path(
        #     self.settings.experiments[0]["path"]
        # )

        self.camera_settings = (
            "/home/matthias/multimaze_recorder/Presets/ballpushing_set.json"
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

        self.table_style_selector = QComboBox()
        self.table_style_selector.addItems(["arenas", "corridors"])
        self.table_style_selector.currentIndexChanged.connect(self.update_table_style)

        # Load existing metadata registries
        metadata_folder = Path("Metadata_Registries")
        metadata_list = [f.stem for f in metadata_folder.glob("*.json")]

        self.metadata_selector = QComboBox()
        # Add the available metadata registries to the combo box
        self.metadata_selector.addItems(metadata_list)
        # Add a default option for creating new metadata
        self.metadata_selector.addItem("New Metadata")
        self.metadata_selector.currentIndexChanged.connect(self.select_metadata)
        # TODO: find out why changing the metadata doesn't update the table.

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Experiment type:"))
        layout.addWidget(self.experiment_type_selector)
        layout.addWidget(QLabel("Duration:"))
        layout.addWidget(self.duration_spinbox)
        layout.addWidget(self.fps_label)
        layout.addWidget(self.fps_spinbox)
        layout.addWidget(QLabel("Folder:"))
        layout.addWidget(self.folder_lineedit)

        # Create a horizontal box layout for the record button and the checkbox
        hbox_record = QHBoxLayout()
        hbox_record.addWidget(self.record_button)
        hbox_record.addWidget(self.HardwareTrigger_checkbox)

        # Add the hbox layout to the main layout
        layout.addLayout(hbox_record)

        # Create a horizontal box layout for the style and metadata selectors

        hbox_style = QHBoxLayout()
        # layout.addWidget(self.stop_button)
        hbox_style.addWidget(QLabel("Table layout:"))
        hbox_style.addWidget(self.table_style_selector)

        hbox_style.addWidget(QLabel("Metadata:"))
        hbox_style.addWidget(self.metadata_selector)

        layout.addLayout(hbox_style)

        # Create an empty table
        self.table = self.create_table(init=True)

        # Add the table to the layout
        layout.addWidget(self.table)

        # Set the layout on the window
        self.setLayout(layout)

        # empty recording thread

        self.recording_thread = None

        # Intialize the updatable attributes to None

        self.folder_path = None

        # Initialize the folder_open attribute
        self.folder_open = False

        # Mac Datapath
        if platform.system() == "Darwin":
            self.DataPath = Path("/Volumes/upramdya/data/MD")
        # Linux Datapath
        if platform.system() == "Linux":
            self.DataPath = Path("/mnt/upramdya_data/MD/")
            self.local_path = Path("/home/matthias/Videos/")
            self.experiment_path = (
                self.DataPath / self.experiment_type_selector.currentText()
            )

        # Check if Arduino is available and enable hardware triggering if so
        if os.path.exists("/dev/ttyACM0"):
            self.HardwareTrigger_checkbox.setEnabled(True)
            self.HardwareTrigger_checkbox.setChecked(True)
        else:
            self.HardwareTrigger_checkbox.setEnabled(False)

    def set_experiment_path(self, index):
        self.current_experiment_type = self.experiment_type_selector.itemText(index)
        self.experiment_path = self.data_folder / Path(
            self.settings.experiments[index]["path"]
        )
        # Emit the signal with the new experiment type
        self.signals.experiment_typeChanged.emit(
            self.settings.experiments[index]["name"]
        )

    def populate_experiments(self):
        for experiment in self.settings.experiments:
            self.experiment_type_selector.addItem(experiment["name"])
        self.experiment_type_selector.addItem("New Experiment")

    def create_new_experiment(self):
        # Temporarily disable the "New Experiment" option to avoid the loop
        new_experiment_index = self.experiment_type_selector.findText("New Experiment")
        if new_experiment_index != -1:  # Check if "New Experiment" option exists
            self.experiment_type_selector.removeItem(new_experiment_index)

        path = QFileDialog.getExistingDirectory(self, "Select Experiment Data Folder")
        if path:
            name, ok = QInputDialog.getText(
                self, "Experiment Name", "Enter the name of the new experiment:"
            )
            if ok and name:
                # Get the path difference between the data folder and the selected folder
                path = Path(path).relative_to(self.data_folder)
                self.settings.add_experiment(name, path)
                # Insert the new experiment into the dropdown
                self.experiment_type_selector.insertItem(
                    self.experiment_type_selector.count(), name
                )
                # Set the current index to the new experiment
                self.experiment_type_selector.setCurrentIndex(
                    self.experiment_type_selector.count() - 1
                )

        # Re-add the "New Experiment" option at the end of the process
        self.experiment_type_selector.addItem("New Experiment")

    # def setup_processing_window(self):
    #     # This method will be called after the ExperimentWindow is fully initialized
    #     # to synchronize the folder updating process.

    #     self.processing_window = ProcessingWindow(self, self.main_window)

    def create_table(
        self, metadata=None, table_style="arenas", experiment_type=None, init=False
    ):
        """
        Create a new table widget using the provided metadata

        Parameters
        ----------
        metadata : dict, optional
            A dictionary containing the metadata for the table, by default None
        table_style : str, optional
            The layout style of the table, by default "arenas"

        Returns
        -------
        QTableWidget
            A table widget containing the metadata
        """
        # Create a table widget to display the data
        table = CustomTableWidget()

        if table_style == "corridors":
            column_count = 1 + 9 * 6
            column_labels = ["Variable"]
            for i in range(1, 10):
                for j in range(1, 7):
                    column_labels.append(f"Arena{i}_Corridor{j}")
        elif table_style == "arenas":
            column_count = 1 + 9
            column_labels = ["Variable"]
            for i in range(1, 10):
                column_labels.append(f"Arena{i}")
        table.setColumnCount(column_count)
        table.setHorizontalHeaderLabels(column_labels)

        # Add empty rows and items to the table
        for row in range(10):
            table.insertRow(row)
            for col in range(table.columnCount()):
                item = QTableWidgetItem("")
                table.setItem(row, col, item)

        if not init:

            # Check if metadata was provided
            if metadata:
                # Fill the "Variable" column with the values from the "Variable" key in the metadata
                for row, value in enumerate(metadata["Variable"]):
                    value_item = QTableWidgetItem(value)
                    table.setItem(row, 0, value_item)

                # Fill the other columns with the values from the other keys in the metadata
                col = 1
                for variable, values in metadata.items():
                    if variable != "Variable":
                        for row, value in enumerate(values):
                            value_item = QTableWidgetItem(value)
                            table.setItem(row, col, value_item)
                        col += 1

                # Check if a registry file exists for this type of experiment and is not empty

                for experiment in self.settings.experiments:
                    if experiment["name"] == self.current_experiment_type:
                        if experiment["metadata"]:
                            print(f"Loading metadata from {experiment['metadata']}")
                            registry_file = Path(experiment["metadata"])

                    # if not experiment_type:
                    #     if self.current_experiment_type == "BallPushing":
                    #         registry_file = Path(
                    #             "Metadata_Registries/variables_registry_BallPushing.json"
                    #         )
                    #     elif self.current_experiment_type == "Standard":
                    #         registry_file = Path(
                    #             "Metadata_Registries/variables_registry_Standard.json"
                    #         )

                    # else:
                    #     if experiment_type == "BallPushing":
                    #         registry_file = Path(
                    #             "Metadata_Registries/variables_registry_BallPushing.json"
                    #         )
                    #     elif experiment_type == "Standard":
                    #         registry_file = Path(
                    #             "Metadata_Registries/variables_registry_Standard.json"
                    #         )
                    else:
                        print("No metadata file found for this experiment type.")
                        # don't load any pre-existing metadata
                        registry_file = None

                if (
                    registry_file
                    and registry_file.exists()
                    and registry_file.stat().st_size > 0
                ):
                    # Read the list of known variables from the registry file
                    with open(registry_file, "r") as f:
                        variables_registry = json.load(f)
                else:
                    # Create a new list to store the known variables
                    variables_registry = []

                # Check if any known variables are missing from the table and add them if necessary
                row = len(metadata["Variable"])
                for variable in variables_registry:
                    if variable not in metadata["Variable"]:
                        table.insertRow(row)
                        value_item = QTableWidgetItem(variable)
                        table.setItem(row, 0, value_item)
                        # Set the values of the other columns for this row
                        for col in range(1, table.columnCount()):
                            value_item = QTableWidgetItem("")
                            table.setItem(row, col, value_item)
                        row += 1

            else:
                # Get the metadata from the selected registry file
                selected_registry = self.metadata_selector.currentText()

                if selected_registry != "New Metadata":
                    with open(
                        f"Metadata_Registries/{selected_registry}.json",
                        "r",
                    ) as f:
                        registry = json.load(f)

                    # Fill the "Variable" column with the values from the registry

                    for row, value in enumerate(registry):
                        value_item = QTableWidgetItem(value)
                        table.setItem(row, 0, value_item)

                else:
                    # Create a new list to store the known variables
                    variables_registry = []

            print(
                f"Creating table with {self.current_experiment_type} type and {table_style} style. Using registry {selected_registry}."
            )
        # Resize the rows and columns to fit their contents
        table.resizeRowsToContents()
        table.resizeColumnsToContents()

        # Set a smaller font size for the table
        font = table.font()
        font.setPointSize(10)
        table.setFont(font)

        # Set a larger minimum size for the table widget
        table.setMinimumSize(800, 600)

        # Add empty rows to the table
        table.add_empty_rows(10)

        # Set the background color of the cells
        table.set_cell_colors()

        return table

    def update_table_style(self, index):
        # Get the selected layout from the combo box
        table_style = self.table_style_selector.itemText(index)
        # Update the table and metadata with the new layout

        self.create_metadata(table_style=table_style)
        self.create_table(table_style=table_style)

        layout = self.layout()

        if not self.folder_open:
            table = self.create_table(table_style=table_style)
            # Remove the existing table from the layout (if any)
            if self.table:
                layout.removeWidget(self.table)
                self.table.deleteLater()

            # Add the new table to the layout
            layout.addWidget(table)

            # Store a reference to the new table in an attribute
            self.table = table

    def detect_table_style(self, metadata):
        # Check if the metadata contains keys for the "corridor" layout
        if any(key.startswith("Arena1_Corridor") for key in metadata.keys()):
            return "corridors"
        # Check if the metadata contains keys for the "arena" layout
        elif any(key.startswith("Arena") for key in metadata.keys()):
            return "arenas"
        # If neither layout is detected, return a default value
        else:
            return "arenas"

    def close_folder(self):
        if self.folder_open == False:
            return

        else:
            # Reset the folder_open attribute
            self.folder_open = False

            # Get the layout of the central widget
            layout = self.layout()

            table = self.create_table()

            # Remove the existing table from the layout (if any)
            if self.table:
                layout.removeWidget(self.table)
                self.table.deleteLater()

            # Store a reference to the new table in an attribute
            self.table = table

            layout.removeWidget(self.info_panel)

            # Add the new table to the layout
            layout.addWidget(table)

            # Clear the folder line edit
            self.folder_lineedit.clear()

            # Reset the folder_path attribute
            self.folder_path = None

            self.folder_lineedit.setDisabled(False)
            self.table_style_selector.setDisabled(False)
            self.experiment_type_selector.setDisabled(False)

    def on_hardware_checkbox_state_changed(self, state):
        # If the checkbox is checked, enable hardware triggering

        if state == 2:
            self.recording_script = (
                "/home/matthias/multimaze_recorder/Trigger_images.py"
            )
            self.fps_spinbox.setRange(16, 29)
            self.fps_spinbox.setValue(29)
            self.fps_label.setText("FPS (range: 16-29):")
            print(
                f"Hardware triggering enabled. Recording using {self.recording_script}"
            )
            # TODO : fix arduino not triggering when launching from GUI
        else:
            self.recording_script = "/home/matthias/multimaze_recorder/Snap_images.py"
            self.fps_spinbox.setRange(1, 30)
            self.fps_spinbox.setValue(30)
            self.fps_label.setText("FPS (range: 1-30):")
            print(
                f"Hardware triggering disabled. Recording using {self.recording_script}"
            )

    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()
        camera_settings = self.camera_settings

        # Check if a folder is open
        if self.folder_open == False:
            self.create_data_folder()
        else:
            self.save_data()

        # Save the fps value to a npy file in the data folder
        np.save(self.folder_path / "fps.npy", fps)

        # Save the duration value to a npy file in the data folder
        np.save(self.folder_path / "duration.npy", duration)

        # Stop the live stream
        self.stop_live_stream()

        # Disable the record button and spinboxes
        self.record_button.setEnabled(False)
        self.duration_spinbox.setEnabled(False)
        self.fps_spinbox.setEnabled(False)

        # TODO: Fix this not properly disabling, and also apply it to situation where images already exist

        print(f"Recording using {self.recording_script}")

        # Start the recording in a separate thread
        if self.main_window.local:
            self.recording_thread = threading.Thread(
                target=self.record_images,
                args=(self.recording_script, folder, fps, duration, camera_settings),
            )
            self.recording_thread.start()

        else:
            QMessageBox.information(
                self,
                "Information",
                "Experiment recording is only possible on the Maze recorder workstation",
            )
            return

    def record_images(self, script, folder, fps, duration, camera_settings):
        subprocess.run(
            ["python", script, folder, str(fps), str(duration), str(camera_settings)]
        )

        # Restart the live stream after recording is finished
        self.start_live_stream()

        # Re-enable the record button and spinboxes
        self.record_button.setEnabled(True)
        self.duration_spinbox.setEnabled(True)
        self.fps_spinbox.setEnabled(True)

    def on_stop_button_clicked(self):
        # Terminate the recording thread
        self.recording_thread.terminate()

        # TODO: fix 'AttributeError: 'Thread' object has no attribute 'terminate'

    def start_live_stream(self):
        # Start the live stream in a separate process
        if self.main_window.local:
            self.live_stream_process = subprocess.Popen(
                ["python", "/home/matthias/multimaze_recorder/LiveStream.py"]
            )
        else:
            return

    def stop_live_stream(self):
        # Stop the live stream by terminating the process
        if hasattr(self, "live_stream_process"):
            self.live_stream_process.terminate()

    def create_metadata(self, table=None, table_style="arenas"):
        # Create a new metadata dictionary
        metadata = {"Variable": []}
        if table_style == "corridors":
            for i in range(1, 10):
                for j in range(1, 7):
                    metadata[f"Arena{i}_Corridor{j}"] = []
        elif table_style == "arenas":
            for i in range(1, 10):
                metadata[f"Arena{i}"] = []

        # If a table object is provided, use it to populate the metadata dictionary
        if table:
            # Update the metadata with the data from the table
            variables = set()
            for row in range(table.rowCount()):
                variable_item = table.item(row, 0)
                if variable_item:
                    variable = variable_item.text()
                    if variable and variable not in variables:
                        variables.add(variable)
                        metadata["Variable"].append(variable)

                        for col in range(1, table.columnCount()):
                            value_item = table.item(row, col)
                            column_label = table.horizontalHeaderItem(col).text()
                            if value_item:
                                value = value_item.text()
                                metadata[column_label].append(value)
                            else:
                                metadata[column_label].append("")

        return metadata

    def check_data_access(self):
        if not self.DataPath.exists():
            # Display an error message and return
            QMessageBox.critical(
                self,
                "Error",
                f"Cannot access the data folder. Check labserver connection.",
            )
            return False

    def on_experiment_type_changed(self, index):
        # self.current_experiment_type = self.experiment_type_selector.itemText(index)

        # # If the experiment type is ball pushing, enable the table style selector
        # if self.current_experiment_type == "BallPushing":
        #     self.table_style_selector.setDisabled(False)
        #     self.camera_settings = (
        #         "/home/matthias/multimaze_recorder/Presets/ballpushing_set.json"
        #     )

        #     print(self.camera_settings)

        # # If the experiment type is not BallPushing, set the table style to "arenas" and disable the table style selector
        # elif self.current_experiment_type != "BallPushing":
        #     self.table_style_selector.setCurrentIndex(0)
        #     self.table_style_selector.setDisabled(True)
        #     self.camera_settings = (
        #         "/home/matthias/multimaze_recorder/Presets/standard_set.json"
        #     )

        # print(self.camera_settings)

        if self.experiment_type_selector.currentText() == "New Experiment":
            self.create_new_experiment()

        self.set_experiment_path(index)

        # Update Table
        # Create a new table using the loaded metadata
        table = self.create_table(experiment_type=self.current_experiment_type)

        # Get the layout of the central widget
        layout = self.layout()

        # Remove the existing table from the layout (if any)
        if self.table:
            layout.removeWidget(self.table)
            self.table.deleteLater()

        # Add the new table to the layout
        layout.addWidget(table)

        # Store a reference to the new table in an attribute
        self.table = table

        # Get the experiment path from the experiments.json file based on the selected experiment type
        # for experiment in self.settings.experiments:
        #     if experiment["name"] == self.current_experiment_type:
        #         self.experiment_path = Path(experiment["path"])
        #         break

        # self.experiment_path = self.DataPath / self.experiment_path

        print(f"Selected experiment type: {self.current_experiment_type}")

        # self.processing_window.update_remote_path(self.experiment_path)

    def select_metadata(self, index):
        # Get the selected metadata from the combo box
        registry = self.metadata_selector.currentText()

        if registry == "New Metadata":
            # Prompt the user to enter a new metadata name
            metadata_name, ok = QInputDialog.getText(
                self, "New Metadata", "Enter new metadata name:"
            )
            if not ok:
                return

            # Create a new .json registry file with the specified name
            with open(f"Metadata_Registries/{metadata_name}.json", "w") as f:
                json.dump([], f)

            # Add the new metadata to the combo box
            self.metadata_selector.addItem(metadata_name)
            # Set the current combo box value to the new metadata
            self.metadata_selector.setCurrentIndex(
                self.metadata_selector.findText(metadata_name)
            )

        else:

            self.current_experiment_type = registry

            # Remove the existing table from the layout (if any)
            layout = self.layout()

            print(registry)
            table = self.create_table(experiment_type=registry)

            if self.table:
                layout.removeWidget(self.table)
                self.table.deleteLater()

            # Add the new table to the layout
            layout.addWidget(table)

            # Store a reference to the new table in an attribute
            self.table = table

    def create_data_folder(self, metadata=None):
        # Check if a folder is already open
        if self.folder_open:
            # Prompt the user to enter a new folder name
            folder_name, ok = QInputDialog.getText(
                self, "New Data Folder", "Enter new folder name:"
            )
            if not ok:
                return

            # Prompt the user to choose an experiment type
            experiment_type, ok = QInputDialog.getItem(
                self,
                "Choose Experiment Type",
                "Choose an experiment type for the new data folder:",
                ["BallPushing", "Standard"],
                0,
                False,
            )
            if not ok:
                return

            self.current_experiment_type = experiment_type
            index = self.experiment_type_selector.findText(experiment_type)

            # If the experiment type is Standard, skip the table style selection and use the "arenas" layout
            if experiment_type == "Standard":
                table_style = "arenas"
            elif experiment_type == "BallPushing":

                # Prompt the user to choose a table style
                table_style, ok = QInputDialog.getItem(
                    self,
                    "Choose Table Style",
                    "Choose a table style for the new data folder:",
                    ["arenas", "corridors"],
                    0,
                    False,
                )
            # Find the index of the item with the specified text
            index = self.table_style_selector.findText(table_style)
            # Set the current index of the table style selector combo box
            self.table_style_selector.setCurrentIndex(index)

            if not ok:
                return

        else:
            # If there is a folder name in the lineedit, use it, else prompt the user to enter a folder name
            if self.folder_lineedit.text():
                folder_name = self.folder_lineedit.text()
                ok = True
            else:
                folder_name, ok = QInputDialog.getText(
                    self, "New Data Folder", "Enter folder name:"
                )
                if not ok:
                    return

            table_style = self.table_style_selector.currentText()

        folder_path = self.DataPath / folder_name
        # If the folder already exists, show a message box asking if the user wants to open the existing folder or choose a different name
        while folder_path.exists():
            reply = QMessageBox.question(
                self,
                "Folder Already Exists",
                f"The folder {folder_name} already exists. Would you like to open the existing folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            # Open the existing folder if the user clicked "Yes"
            if reply == QMessageBox.StandardButton.Yes:
                self.open_data_folder(folder_path)
                return
            # Prompt the user to enter a new folder name if they clicked "No"
            else:
                return

        if self.check_data_access() == False:
            return
        # Create the data folder with the specified name
        if ok and folder_name:
            folder_path = self.DataPath / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

            # Update the folder line edit with the full path to the new data folder
            self.folder_lineedit.setText(str(folder_path))

            # Create subdirectories for each arena
            for i in range(1, 10):
                arena_path = folder_path / f"arena{i}"
                arena_path.mkdir(parents=True, exist_ok=True)

                if self.current_experiment_type == "BallPushing":
                    # Create subdirectories for each corridor
                    for j in range(1, 7):
                        corridor_path = arena_path / f"corridor{j}"
                        corridor_path.mkdir(parents=True, exist_ok=True)

            if self.folder_open:
                self.table.deleteLater()
                table = self.create_table(table_style=table_style)
                # Store a reference to the new table in an attribute
                self.table = table

            # Create experiment.json in the main folder

            metadata = self.create_metadata(table=self.table, table_style=table_style)
            if self.check_data_access() == False:
                return
            with open(folder_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

            # Open the new data folder
            self.open_data_folder(folder_path)

    def open_data_folder(self, folder_path=None):
        if folder_path and str(self.DataPath) not in str(folder_path):
            return

        # Prompt the user to select a folder if no folder path was provided
        if not folder_path:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Open Data Folder", str(self.DataPath)
            )

        # Check if a valid folder was selected
        if not folder_path:
            return

        # Convert the folder path to a Path object
        folder_path = Path(folder_path)

        # Check if the selected folder has a valid structure
        valid_structure = True
        for i in range(1, 10):
            arena_path = folder_path / f"arena{i}"
            if not arena_path.is_dir():
                valid_structure = False
                break

            if self.current_experiment_type == "BallPushing":
                for j in range(1, 7):
                    corridor_path = arena_path / f"corridor{j}"
                    if not corridor_path.is_dir():
                        valid_structure = False
                        break
        # TODO: Fix wrong instances of this happening and also change the result of the reply
        if not valid_structure:
            # Show a message box asking for confirmation to open the folder
            reply = QMessageBox.question(
                self,
                "Invalid Folder Structure",
                "This doesn't look like an experiment folder. Are you sure you want to open it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            # Return if the user clicked "No"
            if reply == QMessageBox.StandardButton.No:
                return

        # Check if the selected folder contains a metadata.json file
        metadata_path = folder_path / "metadata.json"
        if not metadata_path.is_file():
            # Show a message box asking if the user wants to create a metadata.json file
            reply = QMessageBox.question(
                self,
                "Missing Metadata File",
                "This folder doesn't contain a metadata.json file. Would you like to create one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            # Return if the user clicked "No"
            if reply == QMessageBox.StandardButton.No:
                return
            # Create a new metadata.json file if the user clicked "Yes"
            elif reply == QMessageBox.StandardButton.Yes:
                # Prompt the user to choose a table style
                table_style, ok = QInputDialog.getItem(
                    self,
                    "Choose Table Style",
                    "Choose a table style for the new data folder:",
                    ["arenas", "corridors"],
                    0,
                    False,
                )
                # Find the index of the item with the specified text
                index = self.table_style_selector.findText(table_style)
                # Set the current index of the table style selector combo box
                self.table_style_selector.setCurrentIndex(index)

                if not ok:
                    return
                # Create a new metadata.json file in the selected folder
                metadata = self.create_metadata(table_style=table_style)
                if self.check_data_access() == False:
                    return
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=4)

        # Store the folder path in an attribute
        self.folder_path = folder_path

        # Load the metadata from the selected folder
        with open(folder_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        table_style = self.detect_table_style(metadata)

        # Update the layout selector combo box with the detected layout
        index = self.table_style_selector.findText(table_style)
        self.table_style_selector.setCurrentIndex(index)

        # Create a new table using the loaded metadata
        table = self.create_table(
            metadata, table_style=self.table_style_selector.currentText()
        )

        # Get the layout of the central widget
        layout = self.layout()

        # Remove the existing table from the layout (if any)
        if self.table:
            layout.removeWidget(self.table)
            self.table.deleteLater()

        # Add the new table to the layout
        layout.addWidget(table)

        # Store a reference to the new table in an attribute
        self.table = table

        # Remove the existing information panel from the layout (if any)
        if hasattr(self, "info_panel"):
            layout.removeWidget(self.info_panel)
            self.info_panel.deleteLater()

        # Create an information panel widget
        info_panel = QWidget()
        info_layout = QVBoxLayout()
        info_panel.setLayout(info_layout)

        # Add a label to display the folder path
        folder_label = QLabel(f"Folder: {folder_path}")

        info_layout.addWidget(folder_label)

        # Check if the subfolders contain videos and .h5 files
        full = True
        processed = True
        images = True

        for i in range(1, 10):
            arena_path = folder_path / f"arena{i}"
            local_arena_path = self.local_path / folder_path.name / f"arena{i}"

            if self.current_experiment_type == "Standard":

                if not any(arena_path.glob("*.mp4")):
                    full = False
                if not any(local_arena_path.glob("*.jpg")):
                    images = False
                if not any(arena_path.glob("*.h5")):
                    processed = False
            elif self.current_experiment_type == "BallPushing":
                for j in range(1, 7):
                    corridor_path = folder_path / f"arena{i}" / f"corridor{j}"
                    local_corridor_path = (
                        self.local_path
                        / folder_path.name
                        / f"arena{i}"
                        / f"corridor{j}"
                    )
                    if not any(corridor_path.glob("*.mp4")):
                        full = False
                    if not any(local_corridor_path.glob("*.jpg")):
                        images = False
                    if not any(corridor_path.glob("*.h5")):
                        processed = False

        if full or images:
            # Disable the duration and fps spinboxes
            self.duration_spinbox.setDisabled(True)
            self.fps_spinbox.setDisabled(True)
            self.record_button.setDisabled(True)

            # if there are duration and fps files, apply their value to the spinboxes
            if (folder_path / "duration.npy").exists():
                self.duration_spinbox.setValue(np.load(folder_path / "duration.npy"))
            if (folder_path / "fps.npy").exists():
                self.fps_spinbox.setValue(np.load(folder_path / "fps.npy"))

        # Add labels to display the status of the subfolders
        full_label = QLabel(f"Full: {'Yes' if full else 'No'}")
        processed_label = QLabel(f"Processed: {'Yes' if processed else 'No'}")
        info_layout.addWidget(full_label)
        info_layout.addWidget(processed_label)

        if images:
            # send a message to the user to inform that images are available for this experiment to be processed
            QMessageBox.information(
                self,
                "Information",
                f"Images are available for this experiment to be processed.",
            )

        self.info_panel = info_panel

        # Add the information panel to the layout

        layout.addWidget(info_panel)

        # Set the folder_open attribute to True
        self.folder_open = True

        # Set the folder line edit to the selected folder
        self.folder_lineedit.setText(str(folder_path.name))

        self.folder_lineedit.setDisabled(True)
        self.table_style_selector.setDisabled(True)
        self.experiment_type_selector.setDisabled(True)

        if self.tab_widget.currentIndex() != 0:
            self.tab_widget.setCurrentIndex(0)

    def save_data(self):
        # Get the current folder path
        folder_path = self.folder_path

        # If no folder path has been entered, check if the folder line edit is empty
        if not folder_path:
            folder_name = self.folder_lineedit.text()

            # If the folder line edit is empty, prompt the user to choose a folder name
            if not folder_name:
                metadata = self.create_metadata(table=self.table)

                # Call the create_data_folder method to create a new data folder with the given metadata
                self.create_data_folder(metadata)

                # Get the new folder path from the line edit
                folder_path = Path(self.folder_lineedit.text())

            else:
                # Use the text from the folder line edit as the folder name
                folder_path = self.DataPath / folder_name

                self.create_data_folder()
                metadata = self.create_metadata(table=self.table)

                # Save the updated metadata
                if self.check_data_access() == False:
                    return
                with open(folder_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=4)

        else:
            metadata = self.create_metadata(
                table=self.table, table_style=self.table_style_selector.currentText()
            )

            # Save the updated metadata
            if self.check_data_access() == False:
                return
            with open(folder_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

        # Check if the registry file exists and is not empty
        if self.current_experiment_type == "BallPushing":
            registry_file = Path(
                "Metadata_Registries/variables_registry_BallPushing.json"
            )
        elif self.current_experiment_type == "Standard":
            registry_file = Path("Metadata_Registries/variables_registry_Standard.json")

        if (
            registry_file
            and registry_file.exists()
            and registry_file.stat().st_size > 0
        ):
            # Read the list of known variables from the registry file
            with open(registry_file, "r") as f:
                variables_registry = json.load(f)
        else:
            # Create a new list to store the known variables
            variables_registry = []

        # Get the list of variables from the metadata
        variables = metadata["Variable"]
        # Update the registry with the new variables if any
        for variable in variables:
            if variable not in variables_registry:
                variables_registry.append(variable)
        # Save the updated registry
        if self.check_data_access() == False:
            return

        if self.current_experiment_type == "BallPushing":
            with open(
                "Metadata_Registries/variables_registry_BallPushing.json", "w"
            ) as f:
                json.dump(variables_registry, f, indent=4)
        elif self.current_experiment_type == "Standard":
            with open("Metadata_Registries/variables_registry_Standard.json", "w") as f:
                json.dump(variables_registry, f, indent=4)

        # Open the new data folder
        self.open_data_folder(folder_path)

    def has_unsaved_changes(self):
        # Get the folder path from the line edit
        folder_path = self.folder_path

        # If no folder path has been entered, return False
        if not folder_path:
            return False

        table_style = self.table_style_selector.currentText()
        # Load the metadata from the metadata.json file
        with open(folder_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        # Create a new metadata dictionary from the data in the table
        new_metadata = self.create_metadata(self.table, table_style=table_style)

        # Compare the loaded metadata with the new metadata
        return metadata != new_metadata
