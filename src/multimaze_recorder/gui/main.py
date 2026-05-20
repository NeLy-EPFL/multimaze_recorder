from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from multimaze_recorder.gui.settings import Settings
from multimaze_recorder.gui.experiment_window import ExperimentWindow
from multimaze_recorder.gui.processing_window import ProcessingWindow

import sys
import subprocess
import socket


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        hostname = socket.gethostname()
        self.local = (hostname == "mmrecorder")
        self.online = True

        if not self.local:
            try:
                subprocess.run(["ssh", "mmrecorder", "echo", "Connected"], timeout=5, check=True)
            except Exception:
                QMessageBox.information(
                    self,
                    "Information",
                    "The application is running in offline mode. Some features may be disabled.",
                )
                self.online = False

        self.settings = Settings()
        self.setWindowTitle("Multimaze Recorder")
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.experiment_window = ExperimentWindow(self.tab_widget, self)
        self.tab_widget.addTab(self.experiment_window, "Experiment")

        self.processing_window = ProcessingWindow(self.tab_widget, self)
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.processing_window.set_experiment_path
        )
        self.tab_widget.addTab(self.processing_window, "Processing")

        self.processing_window.signals.openDataFolderRequested.connect(
            self.experiment_window.open_data_folder
        )
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.processing_window.update_experiment_type
        )
        self.experiment_window.signals.experiment_typeChanged.connect(
            self.refresh_settings
        )
        self.experiment_window.signals.folder_created.connect(
            self.processing_window.populate_folder_lists
        )

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        for label, slot in [
            ("&New", self.experiment_window.create_data_folder),
            ("&Open", self.experiment_window.open_data_folder),
            ("&Save", self.experiment_window.save_data),
            ("&Close", self.experiment_window.close_folder),
        ]:
            action = QAction(label, self)
            action.triggered.connect(slot)
            file_menu.addAction(action)

    def closeEvent(self, event):
        if self.experiment_window.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Save Data",
                "Would you like to save data before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.experiment_window.save_data()
        event.accept()

    def refresh_settings(self, experiment_name):
        try:
            self.settings.update_settings(experiment_name)
            print("Updated settings in Main window.")
        except Exception as e:
            print(f"Error updating settings: {e}")


def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    experiment_window = mainWindow.findChild(ExperimentWindow)
    experiment_window.start_live_stream()
    mainWindow.show()
    app.aboutToQuit.connect(experiment_window.stop_live_stream)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
