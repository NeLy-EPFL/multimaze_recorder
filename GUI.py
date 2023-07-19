from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys
import threading
import subprocess

class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Multimaze Recorder")
        
        # Create widgets
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 10000)
        self.duration_spinbox.setValue(900)
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 120)
        self.fps_spinbox.setValue(30)
        
        self.folder_lineedit = QLineEdit()
        
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

    def on_button_clicked(self):
        duration = self.duration_spinbox.value()
        fps = self.fps_spinbox.value()
        folder = self.folder_lineedit.text()
        
        # Stop the live stream
        self.stop_live_stream()

         # Start the recording in a separate thread
        recording_thread = threading.Thread(target=self.record_images, args=(folder, fps, duration))
        recording_thread.start()

    def record_images(self, folder, fps, duration):
         # Replace 'recording_script.py' with the path to your recording script
         subprocess.run(['python', '/home/matthias/multimaze_recorder/Snap_images.py', folder, str(fps), str(duration)])
         # Restart the live stream after recording is finished
         self.start_live_stream()

    def start_live_stream(self):
         # Start the live stream in a separate process
         # Replace 'live_stream_script.py' with the path to your live stream script
         self.live_stream_process = subprocess.Popen(['python', '/home/matthias/multimaze_recorder/LiveStream.py'])

    def stop_live_stream(self):
         # Stop the live stream by terminating the process
         if hasattr(self, 'live_stream_process'):
             self.live_stream_process.terminate()

app = QApplication(sys.argv)

window = MainWindow()
window.show()

# Start the live stream when the window is shown
window.start_live_stream()

app.exec()

# Stop the live stream when the application exits
window.stop_live_stream()


