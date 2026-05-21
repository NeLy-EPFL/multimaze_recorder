from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import json


class CustomTableWidget(QTableWidget):

    def __init__(
        self,
        parent,
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

        for row in range(10):
            self.insertRow(row)
            for col in range(self.columnCount()):
                self.setItem(row, col, QTableWidgetItem(""))

    def set_metadata(self, parent):
        variables = parent.metadata.get("Variable", [])
        for row, value in enumerate(variables):
            self.setItem(row, 0, QTableWidgetItem(value))

        for col in range(1, self.columnCount()):
            header = self.horizontalHeaderItem(col).text()
            values = parent.metadata.get(header, [])
            for row, value in enumerate(values):
                self.setItem(row, col, QTableWidgetItem(value))

        self.finalize_table()

    def on_cell_changed(self, row, col):
        self.update_metadata(self.parent(), row, col)

    def update_metadata(self, parent, row, col):
        item = self.item(row, col)
        value = item.text() if item else ""
        column_label = self.horizontalHeaderItem(col).text()
        if col == 0:
            if "Variable" not in parent.metadata:
                parent.metadata["Variable"] = []
            if len(parent.metadata["Variable"]) <= row:
                parent.metadata["Variable"].extend(
                    [""] * (row + 1 - len(parent.metadata["Variable"]))
                )
            parent.metadata["Variable"][row] = value
        else:
            if column_label not in parent.metadata:
                parent.metadata[column_label] = []
            if len(parent.metadata[column_label]) <= row:
                parent.metadata[column_label].extend(
                    [""] * (row + 1 - len(parent.metadata[column_label]))
                )
            parent.metadata[column_label][row] = value

    def finalize_table(self):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        self.setMinimumSize(800, 600)
        self.add_empty_rows(10)
        self.set_cell_colors()

    def contextMenuEvent(self, event):
        row = self.rowAt(event.y())
        col = self.columnAt(event.x())
        menu = QMenu(self)

        fill_all_action = QAction("Fill Experiment", self)
        fill_all_action.triggered.connect(
            lambda checked, row=row: self.fill_experiment(row)
        )
        menu.addAction(fill_all_action)
        menu.addSeparator()

        fill_arena_action = QAction("Fill Arena", self)
        fill_arena_action.triggered.connect(
            lambda checked, col=col, row=row: self.fill_arena(col, row)
        )
        menu.addAction(fill_arena_action)
        menu.exec(event.globalPos())

    def fill_arena(self, col, row):
        column_label = self.horizontalHeaderItem(col).text()
        arena_number = int(column_label.split("_")[0][5:])
        value, ok = QInputDialog.getText(self, f"Fill Arena {arena_number}", "Value:")
        if not ok:
            return
        for c in range(1, self.columnCount()):
            label = self.horizontalHeaderItem(c).text()
            if label.startswith(f"Arena{arena_number}_"):
                item = self.item(row, c)
                if item:
                    item.setText(value)

    def fill_experiment(self, row):
        value, ok = QInputDialog.getText(self, "Fill Experiment", "Value:")
        if not ok:
            return
        for col in range(1, self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setText(value)

    def add_empty_rows(self, row_count):
        empty_rows = [
            row
            for row in range(self.rowCount())
            if all(
                not (self.item(row, col) and self.item(row, col).text())
                for col in range(self.columnCount())
            )
        ]
        for _ in range(max(0, row_count - len(empty_rows))):
            row = self.rowCount()
            self.insertRow(row)
            for col in range(self.columnCount()):
                self.setItem(row, col, QTableWidgetItem(""))

    def set_cell_colors(self):
        colors = [
            "#F7DC6F", "#82E0AA", "#85C1E9", "#BB8FCE", "#F1948A",
            "#6C88C4", "#D35400", "#FFBD00", "#1ABC9C",
        ]
        for row in range(self.rowCount()):
            for col in range(1, self.columnCount()):
                column_label = self.horizontalHeaderItem(col).text()
                arena_number = int(column_label.split("_")[0][5:])
                color = colors[arena_number - 1]
                item = self.item(row, col)
                if item:
                    item.setBackground(QColor(color))

    def update_table_style(self, index):
        table_style = self.table_style_selector.itemText(index)
        self.create_table(table_style=table_style)
        layout = self.layout
        if not self.folder_open:
            table = self.create_table(table_style=table_style)
            if self.table:
                layout.removeWidget(self.table)
                self.table.deleteLater()
            layout.addWidget(table)
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
            try:
                with open(path) as f:
                    self.update(json.load(f))
            except FileNotFoundError:
                print("Metadata template not found")
        else:
            try:
                with open(parent.main_window.settings.metadata_template) as f:
                    self.update(json.load(f))
            except FileNotFoundError:
                print("Metadata template not found")

    def load_metadata(self, parent, update_self=True):
        try:
            with open(parent.folder_path / "metadata.json") as f:
                data = json.load(f)
                if update_self:
                    self.clear()
                    self.update(data)
                return data
        except FileNotFoundError:
            return {}

    def save_metadata(self, parent):
        out = {}

        if hasattr(parent, 'table') and parent.table is not None:
            table = parent.table
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
            variables = []
            for r in range(rows):
                item = table.item(r, 0)
                variables.append(item.text() if item else "")
            while variables and variables[-1] == "":
                variables.pop()
            out['Variable'] = variables

            for c in range(1, table.columnCount()):
                header = table.horizontalHeaderItem(c).text()
                out[header] = [
                    (table.item(r, c).text() if table.item(r, c) else "")
                    for r in range(len(out['Variable']))
                ]
        else:
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
            for k, v in self.items():
                if k not in out:
                    out[k] = v

        with open(parent.folder_path / "metadata.json", "w") as f:
            json.dump(out, f, indent=4)
        self.clear()
        self.update(out)

    def detect_table_style(self):
        if any(key.startswith("Arena1_Corridor") for key in self.keys()):
            return "corridors"
        elif any(key.startswith("Arena") for key in self.keys()):
            return "arenas"
        return "arenas"

    def update_template(self, parent):
        if self.check_diff(parent):
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("Variable Update")
            msg_box.setText(
                "The metadata contains variables that are not in the template. "
                "What would you like to do?"
            )
            update_button = msg_box.addButton("Update Existing", QMessageBox.ButtonRole.ActionRole)
            create_button = msg_box.addButton("Create New", QMessageBox.ButtonRole.ActionRole)
            do_nothing_button = msg_box.addButton("Do Nothing", QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()

            if msg_box.clickedButton() == do_nothing_button:
                return
            if msg_box.clickedButton() == create_button:
                name, ok = QInputDialog.getText(
                    parent, "Template Name", "Enter the name of the new template:"
                )
                if ok and name:
                    self.create_template(parent, parent.metadata_folder / f"{name}.json")
            elif msg_box.clickedButton() == update_button:
                self.create_template(parent, parent.main_window.settings.metadata_template)
        else:
            print("No template changes made")

    def check_diff(self, parent):
        variables = [v for v in self.get("Variable", []) if v]
        try:
            with open(parent.main_window.settings.metadata_template) as f:
                template = json.load(f)
        except FileNotFoundError:
            print("Metadata template not found")
            return False
        template_variables = [v for v in template.get("Variable", []) if v]
        new_vars = [v for v in variables if v not in template_variables]
        missing_vars = [v for v in template_variables if v not in variables]
        return bool(new_vars or missing_vars)

    def create_template(self, parent, path):
        template = {"Variable": [v for v in self.get("Variable", []) if v]}
        with open(path, "w") as f:
            json.dump(template, f, indent=4)
        print(f"Created metadata template: {template}")
