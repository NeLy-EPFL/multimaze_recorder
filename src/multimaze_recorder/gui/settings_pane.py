from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
from multimaze_recorder.gui.settings import Settings


class SettingsPaneSignals(QObject):
    settings_applied = pyqtSignal()


class SettingsPane(QWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.signals = SettingsPaneSignals()
        self._build_ui()
        self._populate()

    def _build_ui(self):
        outer = QVBoxLayout()
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        # --- User ---
        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
        self.user_combo.currentTextChanged.connect(self._on_user_changed)
        user_row = QHBoxLayout()
        user_row.addWidget(self.user_combo)
        refresh_users_btn = QPushButton("Refresh")
        refresh_users_btn.clicked.connect(self._populate_users)
        user_row.addWidget(refresh_users_btn)
        user_widget = QWidget()
        user_widget.setLayout(user_row)
        form.addRow("User initials:", user_widget)
        form.addRow("", QLabel(
            "<small>2–4 capital letters (e.g. MD, VLR). "
            "Populated from existing user directories on the lab server.</small>"
        ))

        # --- Data path ---
        self.data_path_edit = QLineEdit()
        data_row = QHBoxLayout()
        data_row.addWidget(self.data_path_edit)
        browse_data_btn = QPushButton("Browse")
        browse_data_btn.clicked.connect(self._browse_data_path)
        data_row.addWidget(browse_data_btn)
        data_widget = QWidget()
        data_widget.setLayout(data_row)
        form.addRow("Data path:", data_widget)
        form.addRow("", QLabel(
            "<small>Full path to your data folder on the lab server, including your user directory.<br>"
            "Lab server is usually mounted at <b>/mnt/upramdya_data</b> or <b>/mnt/upramdya/data</b>.<br>"
            "Example: /mnt/upramdya_data/MD/</small>"
        ))

        # --- Local path ---
        self.local_path_edit = QLineEdit()
        local_row = QHBoxLayout()
        local_row.addWidget(self.local_path_edit)
        browse_local_btn = QPushButton("Browse")
        browse_local_btn.clicked.connect(self._browse_local_path)
        local_row.addWidget(browse_local_btn)
        local_widget = QWidget()
        local_widget.setLayout(local_row)
        form.addRow("Local path:", local_widget)
        form.addRow("", QLabel(
            "<small>Where raw images are saved on this machine during recording.<br>"
            "Default: ~/Videos</small>"
        ))

        # --- Remote host ---
        self.remote_host_edit = QLineEdit()
        form.addRow("Remote host:", self.remote_host_edit)
        form.addRow("", QLabel(
            "<small>SSH hostname of the recording workstation (the machine physically connected to the camera).<br>"
            "Used to detect whether the GUI is running locally (on the recorder) or remotely.<br>"
            "Must match the workstation's hostname or an alias defined in /etc/hosts or ~/.ssh/config.<br>"
            "Example: if the workstation is named <b>mmrecorder</b>, enter <b>mmrecorder</b>.</small>"
        ))

        # --- Serial port ---
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.setEditable(True)
        serial_row = QHBoxLayout()
        serial_row.addWidget(self.serial_port_combo)
        refresh_serial_btn = QPushButton("Refresh")
        refresh_serial_btn.clicked.connect(self._populate_serial_ports)
        serial_row.addWidget(refresh_serial_btn)
        serial_widget = QWidget()
        serial_widget.setLayout(serial_row)
        form.addRow("Serial port:", serial_widget)
        form.addRow("", QLabel(
            "<small>Arduino port for the hardware trigger (e.g. /dev/ttyACM0).<br>"
            "If no ports appear: make sure the Arduino is plugged in, then click Refresh.<br>"
            "If it still doesn't appear, your user may not be in the <b>dialout</b> group:<br>"
            "&nbsp;&nbsp;<code>sudo usermod -aG dialout $USER</code>  then log out and back in.</small>"
        ))

        outer.addLayout(form)
        outer.addStretch()

        self.apply_btn = QPushButton("Apply && Save")
        self.apply_btn.clicked.connect(self._apply)
        outer.addWidget(self.apply_btn)

        self.setLayout(outer)

    def _populate(self):
        s = self.main_window.settings
        self.local_path_edit.setText(str(s.local_path))
        self.remote_host_edit.setText(s.remote_host)
        self._populate_users()
        self._populate_serial_ports()
        # data path last — _populate_users may have updated it via _on_user_changed
        self.data_path_edit.setText(str(s.datafolder))

    def _populate_users(self):
        s = self.main_window.settings
        server = s.detect_server()
        # Block signal while repopulating to avoid spurious data-path updates
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        if server:
            self.user_combo.addItems(s.discover_users(server))
        idx = self.user_combo.findText(s.user)
        if idx >= 0:
            self.user_combo.setCurrentIndex(idx)
        else:
            self.user_combo.setCurrentText(s.user)
        self.user_combo.blockSignals(False)

    def _populate_serial_ports(self):
        current = self.serial_port_combo.currentText()
        self.serial_port_combo.blockSignals(True)
        self.serial_port_combo.clear()
        ports = Settings.list_serial_ports()
        self.serial_port_combo.addItems(ports)
        if current:
            idx = self.serial_port_combo.findText(current)
            if idx >= 0:
                self.serial_port_combo.setCurrentIndex(idx)
            else:
                self.serial_port_combo.setCurrentText(current)
        elif not ports:
            self.serial_port_combo.setCurrentText(self.main_window.settings.serial_port)
        self.serial_port_combo.blockSignals(False)

    def _on_user_changed(self, new_user: str):
        """Auto-update the data path when user changes, if it follows the lab convention."""
        if not new_user:
            return
        server = self.main_window.settings.detect_server()
        if server is None:
            return
        try:
            rel = Path(self.data_path_edit.text()).relative_to(server)
            # Replace the first path component (the user directory) with the new user
            rest = Path(*rel.parts[1:]) if len(rel.parts) > 1 else Path()
            new_path = server / new_user / rest if rest != Path() else server / new_user
            self.data_path_edit.setText(str(new_path))
        except ValueError:
            pass  # data path is not under the server root — leave it alone

    def _browse_data_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Data Folder", self.data_path_edit.text())
        if path:
            self.data_path_edit.setText(path)

    def _browse_local_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Local Folder", self.local_path_edit.text())
        if path:
            self.local_path_edit.setText(path)

    def _apply(self):
        self.main_window.settings.apply_user_settings(
            user=self.user_combo.currentText().strip(),
            data_path=self.data_path_edit.text().strip(),
            local_path=self.local_path_edit.text().strip(),
            remote_host=self.remote_host_edit.text().strip(),
            serial_port=self.serial_port_combo.currentText().strip(),
        )
        self.signals.settings_applied.emit()
        QMessageBox.information(
            self,
            "Settings saved",
            "Settings have been saved.\n\n"
            "Path and user changes take effect immediately.\n"
            "Remote host changes require a restart.",
        )
