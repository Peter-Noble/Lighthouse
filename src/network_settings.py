from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QCheckBox,
    QSlider,
    QPushButton,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QVector3D, QVector2D, QIconEngine, QIcon


class NetworkSettings(QDockWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout()
        self.label = QLabel("Another Window")
        layout.addWidget(self.label)
        self.setLayout(layout)
