from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from ProcessingWindow import ProcessingWindow
from MainWindow import MainWindow
from Utilities import CustomTableWidget, ExperimentSettings

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))


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
