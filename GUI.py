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
            # Get the row that was clicked
            row = self.rowAt(event.y())

            # Create a context menu
            menu = QMenu(self)

            # Add an action to fill all arenas
            fill_all_action = QAction("Fill Experiment", self)
            fill_all_action.triggered.connect(lambda checked, row=row: self.fill_experiment(row))
            menu.addAction(fill_all_action)

            # Add a separator
            menu.addSeparator()

            # Add an action for each arena
            for i in range(1, 10):
                action = QAction(f"Fill Arena {i}", self)
                action.triggered.connect(lambda checked, i=i, row=row: self.fill_arena(i, row))
                menu.addAction(action)

            # Show the context menu at the current mouse position
            menu.exec(event.globalPos())

        def fill_arena(self, arena, row):
            # Prompt the user to enter a value
            value, ok = QInputDialog.getText(self, f"Fill Arena {arena}", "Value:")
            if not ok:
                return

            # Find the columns for the given arena
            for col in range(1, self.columnCount()):
                column_label = self.horizontalHeaderItem(col).text()
                if column_label.startswith(f"Arena{arena}_"):
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
                "#1ABC9C"
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
            metadata = {"Variable": []}
            for i in range(1, 10):
                for j in range(1, 7):
                    metadata[f"Arena{i}_Corridor{j}"] = []
            with open(folder_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

            # Open the new data folder
            self.open_data_folder(folder_path)

    def open_data_folder(self, folder_path=None):
        if not folder_path:
            # Prompt the user to select an existing data folder
            folder_path = QFileDialog.getExistingDirectory(self, "Select Data Folder")
        folder_path = Path(folder_path)

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

        # Split the table into parts
        window.split_table(3)
        
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

    # TODO: Buttons to fill whole line or specific arenas with some value
    # TODO: make the split table function work

    def split_table(self, parts):
        # Calculate the number of columns per part
        columns_per_part = self.table.columnCount() // parts

        # Create a list to store the table widgets
        tables = []

        # Create a table widget for each part
        for i in range(parts):
            # Create a new table widget
            table = QTableWidget()
            table.setColumnCount(columns_per_part)
            table.setRowCount(self.table.rowCount())

            # Set the horizontal header labels
            column_labels = [
                self.table.horizontalHeaderItem(j).text()
                for j in range(i * columns_per_part, (i + 1) * columns_per_part)
            ]
            table.setHorizontalHeaderLabels(column_labels)

            # Copy the data from the original table to the new table
            for row in range(self.table.rowCount()):
                for col in range(columns_per_part):
                    item = self.table.item(row, i * columns_per_part + col)
                    if item:
                        table.setItem(row, col, QTableWidgetItem(item))

            # Add the new table to the list of tables
            tables.append(table)

        # Create a window for each table
        for i, table in enumerate(tables):
            window = QMainWindow()
            window.setWindowTitle(f"Table Part {i + 1}")
            window.setCentralWidget(table)
            window.show()

        def on_cell_changed(self, row, column):
            # Check if the table attribute is not None
            if self.table is not None:
                # Check if the last row was modified
                if row == self.table.rowCount() - 1:
                    # Add a new empty row at the bottom of the table
                    last_row = self.table.rowCount()
                    self.table.insertRow(last_row)

    def save_data(self):
        # Get the folder path from the line edit
        folder_path = self.folder_path

        # If no folder path has been entered, prompt the user to choose a folder name
        if not folder_path:
            # Call the create_data_folder method to create a new data folder
            self.create_data_folder()

            # Get the new folder path from the line edit
            folder_path = Path(self.folder_lineedit.text())
            print(folder_path)

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
