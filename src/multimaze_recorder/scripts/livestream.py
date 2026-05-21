"""Live stream preview using the TIS camera."""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
from multimaze_recorder.utilities import configure_camera

_PACKAGE_CONFIG_DIR = Path(__file__).parent.parent / "gui" / "config"
DEFAULT_PRESETS = str(_PACKAGE_CONFIG_DIR / "Presets" / "standard_set.json")


class LiveStreamWindow(QWidget):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.setWindowTitle("Live Stream")

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.resize(640, 480)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30 fps

    def update_frame(self):
        if self.camera.snap_image(1):
            frame = self.camera.get_image()
            thumbnail = cv2.resize(frame, (640, 480))
            if thumbnail.ndim == 2:
                thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_GRAY2RGB)
            elif thumbnail.shape[2] == 4:
                thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGRA2RGB)
            else:
                thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            h, w, ch = thumbnail.shape
            qimg = QImage(thumbnail.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(qimg))

    def closeEvent(self, event):
        self.timer.stop()
        self.camera.stop_pipeline()
        event.accept()


def main():
    presets = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "MMRECORDER_PRESETS", DEFAULT_PRESETS
    )

    camera = configure_camera(presets)

    app = QApplication(sys.argv)
    window = LiveStreamWindow(camera)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
