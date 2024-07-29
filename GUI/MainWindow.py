from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from Settings import Settings
from ExperimentWindow import ExperimentWindow
from ProcessingWindow import ProcessingWindow

import platform
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))


import subprocess

import socket


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

        # Detect if the application is running on the experimental workstation
        hostname = socket.gethostname()

        if hostname == "mmrecorder":
            self.local = True
        else:
            self.local = False

        self.online = True

        # If the application is running remotely, try to connect to the experimental workstation through SSH
        if not self.local:
            try:
                subprocess.run(["ssh", "mmrecorder", "echo", "Connected"])
            except:
                # Display an information message to the user that the application will run in offline mode
                QMessageBox.information(
                    self,
                    "Information",
                    "The application is running in offline mode. Some features may be disabled.",
                )

                self.online = False

        # Create the Windows

        # Initialise the settings

        self.settings = Settings()

        self.setWindowTitle("Multimaze Recorder")
        # Set the default size of the window
        self.resize(800, 600)

        # Create a vertical layout for the central widget
        layout = QVBoxLayout()

        # Create a tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create the experiment window and add it as a tab
        self.experiment_window = ExperimentWindow(self.tab_widget, self)
        self.tab_widget.addTab(self.experiment_window, "Experiment")

        # Create the processing window and add it as a tab
        self.processing_window = ProcessingWindow(self.tab_widget, self)
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.processing_window.set_experiment_path
        )
        self.tab_widget.addTab(self.processing_window, "Processing")

        # Handle the open data folder requests from the processing window
        self.processing_window.signals.openDataFolderRequested.connect(
            self.experiment_window.open_data_folder
        )

        # Handle the experiment path sharing between the experiment and processing windows
        # Connect the signal to the slot
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.processing_window.update_experiment_type
        )
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.refresh_settings
        )
        
        self.experiment_window.signals.folder_created.connect(
            self.processing_window.populate_folder_lists)

        # TODO: Create a terminal emulator widget
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
        new_action.triggered.connect(self.experiment_window.create_data_folder)
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.experiment_window.open_data_folder)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.experiment_window.save_data)
        file_menu.addAction(save_action)

        close_action = QAction("&Close", self)
        close_action.triggered.connect(self.experiment_window.close_folder)
        file_menu.addAction(close_action)

    def closeEvent(self, event):
        # Check if there are unsaved changes in the experiment window
        if self.experiment_window.has_unsaved_changes():
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
                self.experiment_window.save_data()

        event.accept()

    def refresh_settings(self, experiment_name):

        try:
            self.settings.update_settings(experiment_name)

            print("Updated settings in Main window.")

        except Exception as e:
            print(f"Error updating settings: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    experiment_window = mainWindow.findChild(ExperimentWindow)

    # Assuming start_live_stream is a method to start the stream
    experiment_window.start_live_stream()

    mainWindow.show()

    # Connect the application's aboutToQuit signal to stop the live stream
    app.aboutToQuit.connect(experiment_window.stop_live_stream)

    sys.exit(app.exec())
