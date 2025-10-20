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
        variables = parent.metadata.get("Variable", [])
        for row, value in enumerate(variables):
            value_item = QTableWidgetItem(value)
            self.setItem(row, 0, value_item)

        # Fill the other columns by matching metadata keys to the table header labels.
        # This ensures Arena1..Arena9 always map to the same column regardless of the
        # ordering of keys in the metadata dict (which previously caused shuffling).
        for col in range(1, self.columnCount()):
            header = self.horizontalHeaderItem(col).text()
            values = parent.metadata.get(header, [])
            for row, value in enumerate(values):
                value_item = QTableWidgetItem(value)
                self.setItem(row, col, value_item)

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

    def load_metadata(self, parent, update_self=True):
        # New signature: if update_self is False, return the loaded dict without
        # mutating this Metadata instance. If update_self is True (default), update
        # self and return the dict for convenience.
        try:
            with open(parent.folder_path / "metadata.json", "r") as file:
                data = json.load(file)
                if update_self:
                    self.clear()
                    self.update(data)
                return data
        except FileNotFoundError:
            # Return empty dict when metadata file doesn't exist
            return {}

    def save_metadata(self, parent):
        # Build metadata from the current table widget state if available.
        # This makes saving robust against uncommitted cell edits and ensures the
        # saved file reflects what the user sees in the GUI.
        out = {}

        # Prefer to read the Variable column from the table (if present)
        if hasattr(parent, 'table') and parent.table is not None:
            table = parent.table
            # Try to commit any active editor: process events and clear focus so the
            # delegate will commit edited text into the model before we read it.
            try:
                app = QApplication.instance()
                if app:
                    app.processEvents()
            except Exception:
                pass

            try:
                table.clearFocus()
                if app:
                    app.processEvents()
            except Exception:
                pass
            rows = table.rowCount()

            # Read variables column
            variables = []
            for r in range(rows):
                item = table.item(r, 0)
                variables.append(item.text() if item else "")

            # Trim trailing empty rows from variables (common expectation)
            while variables and variables[-1] == "":
                variables.pop()

            out['Variable'] = variables

            # Read all other columns by header label
            for c in range(1, table.columnCount()):
                header = table.horizontalHeaderItem(c).text()
                col_values = []
                for r in range(len(out['Variable'])):
                    item = table.item(r, c)
                    col_values.append(item.text() if item else "")
                out[header] = col_values

        else:
            # Fallback: build from in-memory dict but in stable order
            if "Variable" in self:
                out["Variable"] = self.get("Variable", [])

            style = self.detect_table_style()

            if style == "arenas":
                for i in range(1, 10):
                    key = f"Arena{i}"
                    if key in self:
                        out[key] = self.get(key, [])
            elif style == "corridors":
                for i in range(1, 10):
                    for j in range(1, 7):
                        key = f"Arena{i}_Corridor{j}"
                        if key in self:
                            out[key] = self.get(key, [])

            for k, v in list(self.items()):
                if k not in out:
                    out[k] = v

        # Write out to file and update self to the ordered representation
        with open(parent.folder_path / "metadata.json", "w") as file:
            json.dump(out, file, indent=4)

        # Keep the in-memory Metadata ordered the same way as the file
        self.clear()
        self.update(out)

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

        # If there are any missing variables, ask the user if they want to create a new template or update the existing one
        if self.check_diff(parent) == True:
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("Variable Update")
            msg_box.setText(
                "The metadata contains variables that are not in the template. What would you like to do?"
            )

            update_button = msg_box.addButton(
                "Update Existing", QMessageBox.ButtonRole.ActionRole
            )
            create_button = msg_box.addButton(
                "Create New", QMessageBox.ButtonRole.ActionRole
            )
            do_nothing_button = msg_box.addButton(
                "Do Nothing", QMessageBox.ButtonRole.RejectRole
            )

            msg_box.exec()

            if msg_box.clickedButton() == do_nothing_button:
                print("No template changes made")
                return

            if msg_box.clickedButton() == create_button:
                # prompt the user to give a name to the new template
                name, ok = QInputDialog.getText(
                    parent, "Template Name", "Enter the name of the new template:"
                )

                if ok and name:
                    # Create a new template with the current variables and this name
                    self.create_template(
                        parent, parent.metadata_folder / f"{name}.json"
                    )

                    print(
                        f"Created metadata template: {parent.metadata_folder / f'{name}.json'}"
                    )

                else:
                    return

            elif msg_box.clickedButton() == update_button:

                # use create template method with the existing template name to update it
                self.create_template(
                    parent, parent.main_window.settings.metadata_template
                )

                print(
                    f"Updated metadata template: {parent.main_window.settings.metadata_template}"
                )
        else:
            print("No template changes made")

    def check_diff(self, parent):

        new_variables = []

        missing_variables = []

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

        # no changes will trigger nothing,
        # if there are new variables or missing variables, the user will be asked if they want to update the selected template or create a new one

        # If no new variables and no missing variables are found, returns "ok"
        if not new_variables and not missing_variables:
            return False

        # If missing variables are found, returns "missing"
        elif missing_variables or new_variables:
            return True

    def create_template(self, parent, path):

        # Create a new metadata template from the current variables
        template = {"Variable": self.get("Variable", [])}
        with open(path, "w") as file:
            json.dump(template, file, indent=4)

        print(f"Created metadata template: {template}")
