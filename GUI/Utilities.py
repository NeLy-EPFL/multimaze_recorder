from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json


class CustomTableWidget(QTableWidget):

    def __init__(
        self,
        parent,
        # metadata=None,
        table_style="arenas",
        experiment_type=None,
        init=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.setup_table(table_style)

        self.set_metadata(parent)

        self.cellChanged.connect(self.on_cell_changed)

    def setup_table(self, table_style="arenas"):

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
        self.setColumnCount(column_count)
        self.setHorizontalHeaderLabels(column_labels)

        # Add empty rows and items to the table
        for row in range(10):
            self.insertRow(row)
            for col in range(self.columnCount()):
                item = QTableWidgetItem("")
                self.setItem(row, col, item)

    def set_metadata(self, parent):

        # Fill the "Variable" column with the values from the "Variable" key in the metadata
        for row, value in enumerate(parent.metadata["Variable"]):
            value_item = QTableWidgetItem(value)
            self.setItem(row, 0, value_item)

        # Fill the other columns with the values from the other keys in the metadata
        col = 1
        for variable, values in parent.metadata.items():
            if variable != "Variable":
                for row, value in enumerate(values):
                    value_item = QTableWidgetItem(value)
                    self.setItem(row, col, value_item)
                col += 1

        # Call the finalize_table method to resize the rows and columns, set the font size, and add empty rows
        self.finalize_table()

    def on_cell_changed(self, row, col):
        self.update_metadata(self.parent(), row, col)

    def update_metadata(self, parent, row, col):

        # Get the value from the cell
        item = self.item(row, col)
        value = item.text() if item else ""

        # Update the metadata dictionary
        column_label = self.horizontalHeaderItem(col).text()
        if col == 0:
            # Update the "Variable" column
            if "Variable" not in parent.metadata:
                parent.metadata["Variable"] = []
            if len(parent.metadata["Variable"]) <= row:
                parent.metadata["Variable"].extend(
                    [""] * (row + 1 - len(parent.metadata["Variable"]))
                )
            parent.metadata["Variable"][row] = value
        else:
            # Update other columns
            if column_label not in parent.metadata:
                parent.metadata[column_label] = []
            if len(parent.metadata[column_label]) <= row:
                parent.metadata[column_label].extend(
                    [""] * (row + 1 - len(parent.metadata[column_label]))
                )
            parent.metadata[column_label][row] = value

    def finalize_table(self):
        # Resize the rows and columns to fit their contents
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        # Set a smaller font size for the table
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        # Set a larger minimum size for the table widget
        self.setMinimumSize(800, 600)

        # Add empty rows to the table
        self.add_empty_rows(10)

        # Set the background color of the cells
        self.set_cell_colors()

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
        # Check if there are any empty rows
        empty_rows = []
        for row in range(self.rowCount()):
            is_empty = True
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and item.text():
                    is_empty = False
                    break
            if is_empty:
                empty_rows.append(row)

        # Calculate how many rows need to be added
        rows_to_add = max(0, row_count - len(empty_rows))

        # Add the necessary number of empty rows
        for _ in range(rows_to_add):
            row = self.rowCount()
            self.insertRow(row)
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

    def update_table_style(self, index):
        # Get the selected layout from the combo box
        table_style = self.table_style_selector.itemText(index)
        # Update the table and metadata with the new layout

        self.create_table(table_style=table_style)

        layout = self.layout

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


class Metadata(dict):

    def __init__(self, parent, new=False):
        super().__init__()
        if new == False:
            self.load_metadata(parent)
            print(f"Loading Metadata: {self}")
        else:

            self.load_template(parent)
            print(f"Initialising Metadata with parent: {self}")

    def load_template(self, parent, path=None):

        if path:
            print(f"Loading metadata template from path: {path}")
            try:
                with open(path, "r") as file:
                    data = json.load(file)
                    self.update(data)
            except FileNotFoundError:
                print("Metadata template not found")
        else:
            try:
                with open(parent.main_window.settings.metadata_template, "r") as file:
                    data = json.load(file)
                    self.update(data)
            except FileNotFoundError:
                print("Metadata template not found")

    def load_metadata(self, parent):
        try:
            with open(parent.folder_path / "metadata.json", "r") as file:
                data = json.load(file)
                self.update(data)
        except FileNotFoundError:
            print("Metadata file not found")

    def save_metadata(self, parent):
        # TODO: improve the save_metadata method to correctly save the current table and not an empty one
        with open(parent.folder_path / "metadata.json", "w") as file:
            json.dump(self, file, indent=4)

    def detect_table_style(self):
        print(f"Detecting table style for metadata: {self}")

        # Check if the metadata contains keys for the "corridor" layout
        if any(key.startswith("Arena1_Corridor") for key in self.keys()):
            return "corridors"
        # Check if the metadata contains keys for the "arena" layout
        elif any(key.startswith("Arena") for key in self.keys()):
            return "arenas"
        # If neither layout is detected, return a default value
        else:
            return "arenas"

    def update_template(self, parent):
        # Get the Variable column from the metadata
        variables = self.get("Variable", [])

        # Get the Variable column from the selected template
        try:
            with open(parent.main_window.settings.metadata_template, "r") as file:
                template = json.load(file)
        except FileNotFoundError:
            print("Metadata template not found")

        template_variables = template.get("Variable", [])

        # Find the variables that are in the metadata but not in the template
        new_variables = [
            variable for variable in variables if variable not in template_variables
        ]

        # Also find any variables that were in the template but not in the metadata
        missing_variables = [
            variable for variable in template_variables if variable not in variables
        ]

        # If there are any missing variables, ask the user if they want to create a new template or update the existing one
        if missing_variables:
            reply = QMessageBox.question(
                parent,
                "Missing Variables",
                "The metadata contains variables that are not in the template. Would you like to update the template?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.No:
                return

            if reply == QMessageBox.StandardButton.Yes:
                # prompt the user to give a name to the new template
                name, ok = QInputDialog.getText(
                    parent, "Template Name", "Enter the name of the new template:"
                )

                if ok and name:
                    # Create a new template with the current variables and this name
                    self.create_template(
                        parent, parent.metadata_folder / f"{name}.json"
                    )
                
                else:
                    return

        else:

            # Add the new variables to the template
            template_variables.extend(new_variables)

            # Save the updated template
            with open(parent.main_window.settings.metadata_template, "w") as file:
                json.dump(template, file, indent=4)

            print(f"Updated metadata template: {template}")

    def create_template(self, parent, path):

        # Create a new metadata template from the current variables
        template = {"Variable": self.get("Variable", [])}
        with open(path, "w") as file:
            json.dump(template, file, indent=4)

        print(f"Created metadata template: {template}")
