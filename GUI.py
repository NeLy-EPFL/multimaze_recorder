from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys
import threading
import subprocess
import os
from pathlib import Path
import json

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Multimaze Recorder")
        # Set the default size of the window
        self.resize(800, 600)

        # Create widgets
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 10000)
        self.duration_spinbox.setValue(900)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 120)
        self.fps_spinbox.setValue(30)

        self.folder_lineedit = QLineEdit()

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
        
        # Create a "Save" button and add it to the menu bar
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        menu_bar.setCornerWidget(save_button)
        
        # Initialize the table attribute
        self.table = None

    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()

        # Stop the live stream
        self.stop_live_stream()

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

    def create_data_folder(self):
        # Mac Datapath
        DataPath = Path('/Users/ulric/Documents/TestFolders')
        # DataPath = Path("/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/")

        # Prompt the user to enter a folder name
        folder_name, ok = QInputDialog.getText(self, "New Data Folder", "Enter folder name:")

        # Create the data folder with the specified name
        if ok and folder_name:
            folder_path = DataPath / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories for each arena
            for i in range(1, 10):
                arena_path = folder_path / f"arena{i}"
                arena_path.mkdir(parents=True, exist_ok=True)

                # Create subdirectories for each corridor
                for j in range(1, 7):
                    corridor_path = arena_path / f"corridor{j}"
                    corridor_path.mkdir(parents=True, exist_ok=True)

        # Create experiment.json in the main folder
        metadata = {"Variable": []}
        for i in range(1, 10):
            for j in range(1, 7):
                metadata[f"Arena{i}_Corridor{j}"] = []
        with open(folder_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)



    def open_data_folder(self):
        # Prompt the user to select an existing data folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Data Folder")
        folder_path = Path(folder_path)

        # Load the metadata from the selected folder
        with open(folder_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        # Create a table widget to display the data
        table = QTableWidget()
        column_count = 1 + 9 * 6
        column_labels = ["Variable"]
        for i in range(1, 10):
            for j in range(1, 7):
                column_labels.append(f"Arena{i}_Corridor{j}")
        table.setColumnCount(column_count)
        table.setHorizontalHeaderLabels(column_labels)

        # Add the table to the layout of the central widget
        layout = self.centralWidget().layout()
        layout.addWidget(table)
    # TODO: implement table filling, saving, reloading
    # TODO: Empty table when GUI launches
    # TODO: Color code
    # TODO: Buttons to fill whole line or specific arenas with some value



        
    

    def on_cell_changed(self, row, column):
        # Check if the table attribute is not None
        if self.table is not None:
            # Check if the last row was modified
            if row == self.table.rowCount() - 1:
                # Add a new empty row at the bottom of the table
                last_row = self.table.rowCount()
                self.table.insertRow(last_row)

            
        

        # TODO: Add code to load data from the selected folder
        

    def save_data(self):
        # Check if the table attribute is not None
        if self.table is not None:
            # Create a new dictionary to store the data from the table
            new_data = {}

            # Iterate over the rows in the table
            for row in range(self.table.rowCount()):
                # Get the key and value from the current row
                key_item = self.table.item(row, 0)
                value_item = self.table.item(row, 1)

                # Check if the key and value items are not None
                if key_item is not None and value_item is not None:
                    key = key_item.text()
                    value = value_item.text()

                    # Skip rows with empty keys
                    if key:
                        # Add the key and value to the new_data dictionary
                        new_data[key] = value

            # Update the experiment_data attribute with the new data
            self.experiment_data = new_data

            # Save the data to the experiment.json file
            folder_path = QFileDialog.getExistingDirectory(self, "Select Data Folder")
            folder_path = Path(folder_path)
            with open(folder_path / "experiment.json", "w") as f:
                json.dump(self.experiment_data, f)



app = QApplication(sys.argv)

window = MainWindow()
window.show()

# Start the live stream when the window is shown
window.start_live_stream()

app.exec()

# Stop the live stream when the application exits
window.stop_live_stream()


# TODO: Instead of creating a folder only when recording, have a button either to open existing folder or create new folder


# TODO: Implement single json file for experiment, arena and corridor data