import numpy as np
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
from PySide6.QtCore import Signal, Slot, Qt, QSize
from PySide6.QtGui import QVector3D, QVector2D, QIconEngine, QIcon

from data_store import HomographyPoint
from settings_dialogs import AddNewPointDialog, EditPointDialog

from double_slider import DoubleSlider


class FixtureSettingsDock(QDockWidget):
    addNewHomographyPoint = Signal(str, HomographyPoint)
    editHomographyPoint = Signal(str, str, HomographyPoint)
    removeHomographyPoint = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget(None))

        self.settings_layout_widget = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_layout_widget.setLayout(self.settings_layout)
        self.setWidget(self.settings_layout_widget)

        title_layout = QHBoxLayout()
        self.settings_layout.addLayout(title_layout)

        self.icon = QIcon(str((self.parent().data.src_folder / "images/icons/icons8-light-64.png").absolute()))
        icon_label = QLabel()
        icon_label.setPixmap(self.icon.pixmap(QSize(32, 32)))

        title_layout.addWidget(icon_label)
        title_layout.addSpacing(2)
        title_layout.addWidget(QLabel("Fixtures"))
        title_layout.addStretch()

        self.settings_layout.addStretch()
