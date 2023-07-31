from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys
import threading
import subprocess
import os
from pathlib import Path
import json


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
            "#E5E7E9",
            "#D35400",
            "#5D6D7E",
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


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Multimaze Recorder")
        # Set the default size of the window
        self.resize(800, 600)

        # Create widgets
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 10000)
        self.duration_spinbox.setValue(7200)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 120)
        self.fps_spinbox.setValue(30)

        self.folder_lineedit = QLineEdit()
        self.folder_lineedit.setReadOnly(True)

        button = QPushButton("Start Recording")
        button.clicked.connect(self.on_button_clicked)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Duration:"))
        layout.addWidget(self.duration_spinbox)
        layout.addWidget(QLabel("FPS:"))
        layout.addWidget(self.fps_spinbox)
        layout.addWidget(QLabel("Folder:"))
        layout.addWidget(self.folder_lineedit)
        layout.addWidget(button)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        # Create a menu bar
        menu_bar = self.menuBar()

        # Create a "File" menu
        file_menu = menu_bar.addMenu("&File")

        # Add options to the "File" menu
        new_action = QAction("&New", self)
        new_action.triggered.connect(self.create_data_folder)
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.open_data_folder)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)

        # Create an empty table
        self.table = self.create_table()

        # Add the table to the layout
        layout.addWidget(self.table)

        # Intialize the updatable attributes to None

        self.folder_path = None

    def create_table(self, metadata=None):
        # Create a table widget to display the data
        table = CustomTableWidget()
        column_count = 1 + 9 * 6
        column_labels = ["Variable"]
        for i in range(1, 10):
            for j in range(1, 7):
                column_labels.append(f"Arena{i}_Corridor{j}")
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

    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()

        # Stop the live stream
        self.stop_live_stream()

        # Save the data from the table
        self.save_data()

        # Start the recording in a separate thread
        recording_thread = threading.Thread(
            target=self.record_images, args=(folder, fps, duration)
        )
        recording_thread.start()

    def record_images(self, folder, fps, duration):
        # Replace 'recording_script.py' with the path to your recording script
        subprocess.run(
            [
                "python",
                "/home/matthias/multimaze_recorder/Snap_images.py",
                folder,
                str(fps),
                str(duration),
            ]
        )
        # Restart the live stream after recording is finished
        self.start_live_stream()

    def start_live_stream(self):
        # Start the live stream in a separate process
        # Replace 'live_stream_script.py' with the path to your live stream script
        self.live_stream_process = subprocess.Popen(
            ["python", "/home/matthias/multimaze_recorder/LiveStream.py"]
        )

    def stop_live_stream(self):
        # Stop the live stream by terminating the process
        if hasattr(self, "live_stream_process"):
            self.live_stream_process.terminate()

    def create_data_folder(self, metadata=None):
        # Mac Datapath
        DataPath = Path("/Users/ulric/Documents/TestFolders")
        # DataPath = Path("/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/")

        # Prompt the user to enter a folder name
        folder_name, ok = QInputDialog.getText(
            self, "New Data Folder", "Enter folder name:"
        )

        # Create the data folder with the specified name
        if ok and folder_name:
            folder_path = DataPath / folder_name
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

            # Create experiment.json in the main folder
            if metadata is None:
                metadata = {"Variable": []}
                for i in range(1, 10):
                    for j in range(1, 7):
                        metadata[f"Arena{i}_Corridor{j}"] = []
            with open(folder_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

            # Open the new data folder
            self.open_data_folder(folder_path)

    def open_data_folder(self, folder_path=None):
        # Prompt the user to select a folder if no folder path was provided
        if not folder_path:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Open Data Folder", str(Path.home())
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
                # Create a new metadata.json file in the selected folder
                metadata = {"Variable": []}
                for i in range(1, 10):
                    for j in range(1, 7):
                        metadata[f"Arena{i}_Corridor{j}"] = []
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=4)

        
        # Store the folder path in an attribute
        self.folder_path = folder_path

        # Load the metadata from the selected folder
        with open(folder_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        # Create a new table using the loaded metadata
        table = self.create_table(metadata)

        # Get the layout of the central widget
        layout = self.centralWidget().layout()

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

        # Set the folder line edit to the selected folder
        self.folder_lineedit.setText(str(folder_path.name))

    def save_data(self):
        # Get the folder path from the line edit
        folder_path = self.folder_path

        # If no folder path has been entered, prompt the user to choose a folder name
        if not folder_path:
            # Create a new metadata dictionary
            metadata = {"Variable": []}
            for i in range(1, 10):
                for j in range(1, 7):
                    metadata[f"Arena{i}_Corridor{j}"] = []

            # Update the metadata with the data from the table
            variables = set()
            for row in range(self.table.rowCount()):
                variable_item = self.table.item(row, 0)
                if variable_item:
                    variable = variable_item.text()
                    if variable and variable not in variables:
                        variables.add(variable)
                        metadata["Variable"].append(variable)

                        for col in range(1, self.table.columnCount()):
                            value_item = self.table.item(row, col)
                            column_label = self.table.horizontalHeaderItem(col).text()
                            if value_item:
                                value = value_item.text()
                                metadata[column_label].append(value)
                            else:
                                metadata[column_label].append("")

            # Call the create_data_folder method to create a new data folder with the given metadata
            self.create_data_folder(metadata)

            # Get the new folder path from the line edit
            folder_path = Path(self.folder_lineedit.text())
        else:
            # Create a new metadata dictionary
            metadata = {"Variable": []}
            for i in range(1, 10):
                for j in range(1, 7):
                    metadata[f"Arena{i}_Corridor{j}"] = []

            # Update the metadata with the data from the table
            variables = set()
            for row in range(self.table.rowCount()):
                variable_item = self.table.item(row, 0)
                if variable_item:
                    variable = variable_item.text()
                    if variable and variable not in variables:
                        variables.add(variable)
                        metadata["Variable"].append(variable)

                        for col in range(1, self.table.columnCount()):
                            value_item = self.table.item(row, col)
                            column_label = self.table.horizontalHeaderItem(col).text()
                            if value_item:
                                value = value_item.text()
                                metadata[column_label].append(value)
                            else:
                                metadata[column_label].append("")

            # Save the updated metadata
            with open(folder_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

    def has_unsaved_changes(self):
        # Get the folder path from the line edit
        folder_path = self.folder_path

        # If no folder path has been entered, return False
        if not folder_path:
            return False

        # Load the metadata from the metadata.json file
        with open(folder_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        # Create a new metadata dictionary from the data in the table
        new_metadata = {"Variable": []}
        for i in range(1, 10):
            for j in range(1, 7):
                new_metadata[f"Arena{i}_Corridor{j}"] = []

        variables = set()
        for row in range(self.table.rowCount()):
            variable_item = self.table.item(row, 0)
            if variable_item:
                variable = variable_item.text()
                if variable and variable not in variables:
                    variables.add(variable)
                    new_metadata["Variable"].append(variable)

                    for col in range(1, self.table.columnCount()):
                        value_item = self.table.item(row, col)
                        column_label = self.table.horizontalHeaderItem(col).text()
                        if value_item:
                            value = value_item.text()
                            new_metadata[column_label].append(value)
                        else:
                            new_metadata[column_label].append("")

        # Compare the loaded metadata with the new metadata
        return metadata != new_metadata

    def closeEvent(self, event):
        # Check if there are unsaved changes
        if self.has_unsaved_changes():
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
                self.save_data()

        event.accept()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

# Start the live stream when the window is shown
window.start_live_stream()

app.exec()

# Stop the live stream when the application exits
window.stop_live_stream()
