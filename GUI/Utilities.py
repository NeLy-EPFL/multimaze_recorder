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