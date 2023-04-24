from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox


class CameraSelectDialog(QDialog):
    def __init__(self, availableCameras, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select a camera")

        vbox = QVBoxLayout()

        message = QLabel("Pick a new camera:")
        vbox.addWidget(message)

        self.combobox = QComboBox(self)
        self.combobox.addItems(availableCameras)
        vbox.addWidget(self.combobox)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

    def getCameraId(self) -> int:
        return self.combobox.currentIndex()
