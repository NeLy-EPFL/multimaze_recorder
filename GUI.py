from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys
import threading
import subprocess
import os
from pathlib import Path
import json
import platform
import socket
import time


class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def contextMenuEvent(self, event):
        # Get the row and column that was clicked
        row = self.rowAt(event.y())
        col = self.columnAt(event.x())

        # Create a context menu
        menu = QMenu(self)

        # Add an action to fill all arenas
        fill_all_action = QAction("Fill Experiment", self)
        fill_all_action.triggered.connect(
            lambda checked, row=row: self.fill_experiment(row)
        )
        menu.addAction(fill_all_action)

        # Add a separator
        menu.addSeparator()

        # Add an action to fill the selected arena
        fill_arena_action = QAction("Fill Arena", self)
        fill_arena_action.triggered.connect(
            lambda checked, col=col, row=row: self.fill_arena(col, row)
        )
        menu.addAction(fill_arena_action)

        # Show the context menu at the current mouse position
        menu.exec(event.globalPos())

    def fill_arena(self, col, row):
        # Get the arena number from the column label
        column_label = self.horizontalHeaderItem(col).text()
        arena_number = int(column_label.split("_")[0][5:])

        # Prompt the user to enter a value
        value, ok = QInputDialog.getText(self, f"Fill Arena {arena_number}", "Value:")
        if not ok:
            return

        # Find the columns for the given arena
        for col in range(1, self.columnCount()):
            column_label = self.horizontalHeaderItem(col).text()
            if column_label.startswith(f"Arena{arena_number}_"):
                # Set the value for the given row in the column
                item = self.item(row, col)
                if item:
                    item.setText(value)

    def fill_experiment(self, row):
        # Prompt the user to enter a value
        value, ok = QInputDialog.getText(self, "Fill Experiment", "Value:")
        if not ok:
            return

        # Set the value for all cells in the given row
        for col in range(1, self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setText(value)

    def add_empty_rows(self, row_count):
        for _ in range(row_count):
            row = self.rowCount()
            self.insertRow(row)
            # Add empty items to each cell of the new row
            for col in range(self.columnCount()):
                item = QTableWidgetItem("")
                self.setItem(row, col, item)

    def set_cell_colors(self):
        # Define a list of colors to use for each arena
        colors = [
            "#F7DC6F",
            "#82E0AA",
            "#85C1E9",
            "#BB8FCE",
            "#F1948A",
            "#6C88C4",
            "#D35400",
            "#FFBD00",
            "#1ABC9C",
        ]

        # Iterate over the cells of the table
        for row in range(self.rowCount()):
            for col in range(1, self.columnCount()):
                # Get the arena number from the column label
                column_label = self.horizontalHeaderItem(col).text()
                arena_number = int(column_label.split("_")[0][5:])

                # Get the color for this arena
                color = colors[arena_number - 1]

                # Set the background color of the cell
                item = self.item(row, col)
                if item:
                    item.setBackground(QColor(color))


class ExperimentWindow(QWidget):
    def __init__(self, tab_widget, *args, **kwargs):
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

        # Create widgets
        self.tab_widget = tab_widget

        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 10000)
        self.duration_spinbox.setValue(7200)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 120)
        self.fps_spinbox.setValue(30)

        self.folder_lineedit = QLineEdit()

        self.record_button = QPushButton("Start Recording")

        self.record_button.clicked.connect(self.on_button_clicked)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        
        self.HardwareTrigger_checkbox = QCheckBox("Hardware Trigger")
        self.HardwareTrigger_checkbox.stateChanged.connect(self.on_hardware_checkbox_state_changed)

        self.table_style_selector = QComboBox()
        self.table_style_selector.addItems(["arenas", "corridors"])
        self.table_style_selector.currentIndexChanged.connect(self.update_table_style)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Duration:"))
        layout.addWidget(self.duration_spinbox)
        layout.addWidget(QLabel("FPS:"))
        layout.addWidget(self.fps_spinbox)
        layout.addWidget(QLabel("Folder:"))
        layout.addWidget(self.folder_lineedit)
        
        # Create a horizontal box layout for the record button and the checkbox
        hbox = QHBoxLayout()
        hbox.addWidget(self.record_button)
        hbox.addWidget(self.HardwareTrigger_checkbox)

        # Add the hbox layout to the main layout
        layout.addLayout(hbox)
        
        # layout.addWidget(self.stop_button)
        layout.addWidget(QLabel("Table layout:"))
        layout.addWidget(self.table_style_selector)

        # Create an empty table
        self.table = self.create_table()

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
            self.DataPath = Path(
                "/Volumes/Ramdya-Lab/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos"
            )
        # Linux Datapath
        if platform.system() == "Linux":
            self.DataPath = Path(
                "/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/"
            )
        
        # Check if Arduino is available and enable hardware triggering if so
        if os.path.exists("/dev/ttyACM0"):
            self.HardwareTrigger_checkbox.setEnabled(True)
            self.HardwareTrigger_checkbox.setChecked(True)
        else:
            self.HardwareTrigger_checkbox.setEnabled(False)

    def create_table(self, metadata=None, table_style="arenas"):
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

            # Check if the registry file exists and is not empty
            registry_file = Path("variables_registry.json")
            if registry_file.exists() and registry_file.stat().st_size > 0:
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
            # Check if the registry file exists and is not empty
            registry_file = Path("variables_registry.json")
            if registry_file.exists() and registry_file.stat().st_size > 0:
                # Read the list of known variables from the registry file
                with open(registry_file, "r") as f:
                    variables_registry = json.load(f)
            else:
                # Create a new list to store the known variables
                variables_registry = []

            # Fill the "Variable" column with the values from the registry
            for row, value in enumerate(variables_registry):
                value_item = QTableWidgetItem(value)
                table.setItem(row, 0, value_item)

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

    def on_hardware_checkbox_state_changed(self, state):
        if state == Qt.checked:
            self.recording_script = "/home/matthias/multimaze_recorder/Trigger_images.py"
        else:
            self.recording_script = "/home/matthias/multimaze_recorder/Snap_images.py"
    
    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()

        # Check if a folder is open
        if self.folder_open == False:
            self.create_data_folder()
        else:
            self.save_data()

        # Stop the live stream
        self.stop_live_stream()

        # Disable the record button and spinboxes
        self.record_button.setEnabled(False)
        self.duration_spinbox.setEnabled(False)
        self.fps_spinbox.setEnabled(False)
        
        print(f"Recording using {self.recording_script}")

        # Start the recording in a separate thread
        if platform.system() == "Linux":
            self.recording_thread = threading.Thread(
                target=self.record_images, args=(self.recording_script, folder, fps, duration)
            )
            self.recording_thread.start()

        elif platform.system() == "Darwin":
            QMessageBox.information(
                self, "Information", "Camera recording is not supported on laptop."
            )
            return

    def record_images(self, script, folder, fps, duration):
        subprocess.run(
            [
                "python",
                script,
                folder,
                str(fps),
                str(duration),
            ]
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
        if platform.system() == "Linux":
            self.live_stream_process = subprocess.Popen(
                ["python", "/home/matthias/multimaze_recorder/LiveStream.py"]
            )
        elif platform.system() == "Darwin":
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

    def create_data_folder(self, metadata=None):
        # Check if a folder is already open
        if self.folder_open:
            # Prompt the user to enter a new folder name
            folder_name, ok = QInputDialog.getText(
                self, "New Data Folder", "Enter new folder name:"
            )
            if not ok:
                return

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
            for j in range(1, 7):
                corridor_path = arena_path / f"corridor{j}"
                if not corridor_path.is_dir():
                    valid_structure = False
                    break

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
        for i in range(1, 10):
            for j in range(1, 7):
                corridor_path = folder_path / f"arena{i}" / f"corridor{j}"
                if not any(corridor_path.glob("*.mp4")):
                    full = False
                if not any(corridor_path.glob("*.h5")):
                    processed = False

        # Add labels to display the status of the subfolders
        full_label = QLabel(f"Full: {'Yes' if full else 'No'}")
        processed_label = QLabel(f"Processed: {'Yes' if processed else 'No'}")
        info_layout.addWidget(full_label)
        info_layout.addWidget(processed_label)

        self.info_panel = info_panel

        # Add the information panel to the layout

        layout.addWidget(info_panel)

        # Set the folder_open attribute to True
        self.folder_open = True

        # Set the folder line edit to the selected folder
        self.folder_lineedit.setText(str(folder_path.name))

        self.folder_lineedit.setDisabled(True)
        self.table_style_selector.setDisabled(True)

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
        registry_file = Path("variables_registry.json")
        if registry_file.exists() and registry_file.stat().st_size > 0:
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
        with open("variables_registry.json", "w") as f:
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


class ProcessingWindow(QWidget):
    def __init__(self, tab_widget):
        super().__init__()

        self.tab_widget = tab_widget
        # Store a reference to the experiment window
        self.experiment_window = ExperimentWindow(self.tab_widget)

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

        # Create a label and list widget for the data path folders
        data_path_label = QLabel("Lab server videos:")
        folder_layout.addWidget(data_path_label)
        self.data_path_folder_list = QListWidget()
        folder_layout.addWidget(self.data_path_folder_list)

        # Create a label and list widget for the local path folders
        local_path_label = QLabel("Recorded Videos:")
        folder_layout.addWidget(local_path_label)
        self.local_path_folder_list = QListWidget()
        folder_layout.addWidget(self.local_path_folder_list)

        # Populate the list widgets with the folders
        self.populate_folder_lists()

        self.setLayout(layout)

    def on_crop_button_clicked(self):
        # Launch the terminal and run the run_processimages command
        if sys.platform == "darwin":
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
            subprocess.Popen(["gnome-terminal", "--", "run_processimages"])

        self.populate_folder_lists()

    def on_check_crops_clicked(self):
        # Launch the terminal and run the check_crops command
        if sys.platform == "darwin":
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
        else:
            subprocess.Popen(["gnome-terminal", "--", "check_crops"])

    def on_make_videos_button_clicked(self):
        # Launch the terminal and run the run_makevideos command
        if sys.platform == "darwin":
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
        else:
            subprocess.Popen(
                [
                    "gnome-terminal",
                    "--",
                    "/bin/bash",
                    "/home/matthias/Tracking_Analysis/Tracktor/MakeVideos.sh",
                ]
            )

    def on_track_videos_button_clicked(self):
        # Launch the terminal and run the balltracker command
        if sys.platform == "darwin":
            QMessageBox.information(
                self,
                "Information",
                "This command is not yet implemented for remote execution and should be run from the workstation.",
            )
            return
        else:
            subprocess.Popen(["gnome-terminal", "--", "balltracker"])

    def on_check_tracks_button_clicked(self):
        if sys.platform == "darwin":
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
        with open("variables_registry.json", "r") as f:
            variables_registry = json.load(f)

        # Load the metadata file
        metadata_path = Path(folder) / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            return False

        # Check if all variables from the registry are present in the metadata
        if not all(variable in metadata["Variable"] for variable in variables_registry):
            return False

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
        data_path = Path(self.experiment_window.DataPath)

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
        if sys.platform == "linux":
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

        if sys.platform == "darwin":
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

    def on_data_path_folder_clicked(self, item):
        # Get the name of the clicked folder
        folder_name = item.text()

        folder_path = Path(self.experiment_window.DataPath) / folder_name
        # Call the open_folder function with the name of the clicked folder
        experiment_window.open_data_folder(folder_path)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        """
        Main window of the application.
        
        Attributes
        ----------
        tab_widget : QTabWidget
            The tab widget containing the experiment and processing windows.
        
        Methods
        ---------
        closeEvent : override
            Called when the window is closed. Handles 1) checking for unsaved changes in the experiment window, 2) closing the live stream, and 3) closing the application.
        
        """

        self.setWindowTitle("Multimaze Recorder")
        # Set the default size of the window
        self.resize(800, 600)

        # Create a vertical layout for the central widget
        layout = QVBoxLayout()

        # Create a tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create the experiment window and add it as a tab
        experiment_window = ExperimentWindow(self.tab_widget)
        self.tab_widget.addTab(experiment_window, "Experiment")

        # Create the processing window and add it as a tab
        processing_window = ProcessingWindow(self.tab_widget)
        self.tab_widget.addTab(processing_window, "Processing")

        # Create a terminal emulator widget
        # self.terminal = QTermWidget()
        # layout.addWidget(self.terminal)

        # Set the layout for the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create a menu bar
        menu_bar = self.menuBar()

        # Create a "File" menu
        file_menu = menu_bar.addMenu("&File")

        # Add options to the "File" menu
        new_action = QAction("&New", self)
        new_action.triggered.connect(experiment_window.create_data_folder)
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        open_action.triggered.connect(experiment_window.open_data_folder)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.triggered.connect(experiment_window.save_data)
        file_menu.addAction(save_action)

        close_action = QAction("&Close", self)
        close_action.triggered.connect(experiment_window.close_folder)
        file_menu.addAction(close_action)

    def closeEvent(self, event):
        # Check if there are unsaved changes in the experiment window
        if experiment_window.has_unsaved_changes():
            print("unsaved changes")
            # Prompt the user to save data before closing
            reply = QMessageBox.question(
                self,
                "Save Data",
                "Would you like to save data before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Save the data from the table
                experiment_window.save_data()

        event.accept()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

# Get a reference to the experiment window
experiment_window = window.findChild(ExperimentWindow)

# Start the live stream when the window is shown
experiment_window.start_live_stream()

app.exec()

# Stop the live stream when the application exits
experiment_window.stop_live_stream()
