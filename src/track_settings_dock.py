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
    QListWidget,
    QComboBox,
    QLineEdit,
    QSizePolicy,
    QColorDialog,
)
from PySide6.QtCore import Signal, Slot, Qt, QSize
from PySide6.QtGui import QVector3D, QVector2D, QIconEngine, QIcon

from data_store import HomographyPoint, Track
from settings_dialogs import AddNewPointDialog, EditPointDialog

from double_slider import DoubleSlider


class TrackEditor(QWidget):
    def __init__(self, track: Track, id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(QLineEdit(track.name))
        self.color_pick = QPushButton()
        self.color_pick.clicked.connect(self.showColourPicker)
        self.color_pick.setStyleSheet(f"background-color:rgb(255, 0, 0);")
        self.name_layout.addWidget(self.color_pick)
        self.v_layout.addLayout(self.name_layout)

        self.input_device = QComboBox()
        self.input_device.addItems(["Cursor", "Space Mouse 1", "Space Mouse 2"])
        self.v_layout.addWidget(self.input_device)
        self.v_layout.addWidget(QLabel("Height offset"))
        self.height_offset = DoubleSlider(orientation=Qt.Orientation.Horizontal)
        self.height_offset.setMinimum(-0.5)
        self.height_offset.setMaximum(2)
        self.height_offset.setTickInterval(0.01)
        self.v_layout.addWidget(self.height_offset)
        self.v_layout.addWidget(QLabel("Sensitivity"))
        self.sensitivity = DoubleSlider(orientation=Qt.Orientation.Horizontal)
        self.sensitivity.setMinimum(0)
        self.sensitivity.setMaximum(1)
        self.sensitivity.setTickInterval(0.01)
        self.v_layout.addWidget(self.sensitivity)
        self.v_layout.addWidget(QLabel("Smoothing"))
        self.smoothing = DoubleSlider(orientation=Qt.Orientation.Horizontal)
        self.smoothing.setMinimum(0)
        self.smoothing.setMaximum(1)
        self.smoothing.setTickInterval(0.01)
        self.v_layout.addWidget(self.smoothing)

    def showColourPicker(self, _):
        picker = QColorDialog()
        if picker.exec_() == QColorDialog.Accepted:
            colour = picker.currentColor()
            self.color_pick.setStyleSheet(f"background-color:rgb({colour.red()}, {colour.green()}, {colour.blue()});")


class TrackSettingsDock(QDockWidget):
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

        self.icon = QIcon(str((self.parent().data.src_folder / "images/icons/icons8-track-order-64.png").absolute()))
        icon_label = QLabel()
        icon_label.setPixmap(self.icon.pixmap(QSize(32, 32)))

        title_layout.addWidget(icon_label)
        title_layout.addSpacing(2)
        title_layout.addWidget(QLabel("Track settings"))
        title_layout.addStretch()

        self.track_list = QListWidget()
        self.track_list.setFlow(QListWidget.Flow.LeftToRight)
        self.track_list.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.track_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_layout.addWidget(self.track_list)

        new_item = QListWidgetItem()
        new_item.setFlags(new_item.flags() & ~Qt.ItemIsSelectable)
        widget = TrackEditor(self.parent().data.tracks[0], 0)
        new_item.setSizeHint(widget.sizeHint())
        self.track_list.addItem(new_item)
        self.track_list.setItemWidget(new_item, widget)

        new_item = QListWidgetItem()
        new_item.setFlags(new_item.flags() & ~Qt.ItemIsSelectable)
        widget = TrackEditor(self.parent().data.tracks[1], 1)
        new_item.setSizeHint(widget.sizeHint())
        self.track_list.addItem(new_item)
        self.track_list.setItemWidget(new_item, widget)

        self.track_list.setFixedHeight(self.track_list.sizeHintForRow(0))
        # self.track_list.setMinimumWidth(self.track_list.sizeHintForColumn(0))
        # self.track_list.setFixedHeight(self.track_list.sizeHintForRow(0) * self.track_list.count() + 2)

        self.resize(self.sizeHint())
