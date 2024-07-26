from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json


class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def set_metadata(self, metadata):
        if metadata:
            # Fill the "Variable" column with the values from the "Variable" key in the metadata
            for row, value in enumerate(metadata["Variable"]):
                value_item = QTableWidgetItem(value)
                self.setItem(row, 0, value_item)

            # Fill the other columns with the values from the other keys in the metadata
            col = 1
            for variable, values in metadata.items():
                if variable != "Variable":
                    for row, value in enumerate(values):
                        value_item = QTableWidgetItem(value)
                        self.setItem(row, col, value_item)
                    col += 1

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

    def update_table_style(self, index):
        # Get the selected layout from the combo box
        table_style = self.table_style_selector.itemText(index)
        # Update the table and metadata with the new layout

        self.create_metadata(table_style=table_style)
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


class Metadata:

    def __init__(self, parent, new=False):

        if not new:
            self.metadata = self.load_metadata(parent)

        else:
            self.metadata = self.create_metadata()

    def create_metadata(self, table=None, table_style="arenas"):
        # Create a new metadata dictionary
        self.metadata = {"Variable": []}
        if table_style == "corridors":
            for i in range(1, 10):
                for j in range(1, 7):
                    self.metadata[f"Arena{i}_Corridor{j}"] = []
        elif table_style == "arenas":
            for i in range(1, 10):
                self.metadata[f"Arena{i}"] = []

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
                        self.metadata["Variable"].append(variable)

                        for col in range(1, table.columnCount()):
                            value_item = table.item(row, col)
                            column_label = table.horizontalHeaderItem(col).text()
                            if value_item:
                                value = value_item.text()
                                self.metadata[column_label].append(value)
                            else:
                                self.metadata[column_label].append("")

        return self.metadata

    def load_metadata(self, parent):
        try:
            with open(parent.folder_path / "metadata.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Metadata file not found")
            return []

    def save_metadata(self, parent):
        # TODO: improve the save_metadata method to correctly save the current table and not an empty one

        with open(parent.folder_path / "metadata.json", "w") as file:
            json.dump(self.metadata, file, indent=4)

    def detect_table_style(self):

        metadata = self.metadata
        print(f"Detecting table style for metadata: {metadata}")

        # Check if the metadata contains keys for the "corridor" layout
        if any(key.startswith("Arena1_Corridor") for key in metadata.keys()):
            return "corridors"
        # Check if the metadata contains keys for the "arena" layout
        elif any(key.startswith("Arena") for key in metadata.keys()):
            return "arenas"
        # If neither layout is detected, return a default value
        else:
            return "arenas"


class MetadataTemplate:
    def __init__(self, parent):

        self.path = parent.main_window.settings.metadata_template
        print(f"Initialising Metadata Template with path {self.path}")

        self.variables = self.load_metadata_variables()

    def update_template(self, parent):
        metadata_template_path = Path(parent.main_window.settings.metadata_template)
        standard_template_path = Path(
            "Metadata_Templates/variables_registry_Standard.json"
        )

        if metadata_template_path != standard_template_path:
            metadata_template = self.load_metadata_template(self.path)
            if metadata_template is None:
                return

            if any(
                variable not in metadata_template
                for variable in parent.metadata.metadata["Variable"]
            ):
                reply = QMessageBox.question(
                    parent,
                    "Update Metadata Template",
                    "New variables found in the metadata. Update the current metadata template?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.update_existing_template(metadata_template, self.path)
                else:
                    self.create_and_save_new_template()
            else:
                print("Metadata template already up to date.")
        else:
            reply = QMessageBox.question(
                parent,
                "Create New Metadata Template",
                "Would you like to create a new metadata template with the current variables?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.create_and_save_new_template()

    def load_metadata_template(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading metadata template: {e}")
            return None

    def update_existing_template(self, metadata_template, path):
        for variable in self.metadata.metadata["Variable"]:
            if variable not in metadata_template:
                metadata_template.append(variable)
        self.save_metadata_template(path, metadata_template)
        print(f"Saving updated metadata template to {path}")

    def create_and_save_new_template(self, parent):
        template_name, ok = QInputDialog.getText(
            parent, "New Metadata Template", "Enter new metadata template name:"
        )
        if not ok:
            return

        metadata_template = parent.main_window.settings.metadata_template
        new_template_path = Path(f"Metadata_Templates/{template_name}.json")
        self.save_metadata_template(new_template_path, metadata_template)
        parent.main_window.settings.metadata_template = str(new_template_path)

        reply = QMessageBox.question(
            parent,
            "Set as Default Metadata Template",
            "Would you like to set this new metadata template as the default for this experiment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.update_experiment_registry(new_template_path)

        self.reload_metadata_templates()

    def update_experiment_registry(self, new_template_path):
        current_registry = self.main_window.settings.experiments
        current_registry[self.experiment_type_selector.currentIndex()]["metadata"] = (
            str(new_template_path)
        )
        self.main_window.settings.save_experiments()

    def reload_metadata_templates(self):
        metadata_folder = Path("Metadata_Templates")
        metadata_list = [f.stem for f in metadata_folder.glob("*.json")]
        self.metadata_selector.clear()
        self.metadata_selector.addItems(metadata_list)
        self.metadata_selector.addItem("New Metadata")

    def save_metadata_template(self, path, metadata_template):
        try:
            with open(path, "w") as f:
                json.dump(metadata_template, f, indent=4)
        except IOError as e:
            print(f"Error saving metadata template: {e}")

    def load_metadata_variables(self):
        # First load the template
        metadata_template = self.load_metadata_template(self.path)

        return metadata_template
