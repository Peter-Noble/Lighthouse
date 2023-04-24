from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QSpinBox,
    QCheckBox,
)
from PySide6.QtCore import Signal, Slot, QPoint

from data_store import HomographyPoint


class SettingsDock(QDockWidget):
    def __init__(self):
        super().__init__()

        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget(None))

        self.settings_layout_widget = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_layout_widget.setLayout(self.settings_layout)
        self.setWidget(self.settings_layout_widget)

        self.list_widget = QListWidget()
        self.settings_layout.addWidget(self.list_widget)

        self.edit_homography_points = QCheckBox("Edit homography points")
        self.settings_layout.addWidget(self.edit_homography_points)

        self.track0 = QLabel("Track 0: 0.0, 0.0")
        self.tracks = [self.track0]
        self.settings_layout.addWidget(self.track0)

        # track_coord_layout = QHBoxLayout()
        # self.settings_layout.addLayout(track_coord_layout)

        # self.track_x = QSpinBox()
        # self.track_x.setMaximum(4096)
        # self.track_y = QSpinBox()
        # self.track_y.setMaximum(2048)
        # track_coord_layout.addWidget(self.track_x)
        # track_coord_layout.addWidget(self.track_y)

        # self.track_x.valueChanged.connect(self.updateTrack)
        # self.track_y.valueChanged.connect(self.updateTrack)

    @Slot(object)  # dict[str, HomographyPoint]
    def updateHomographyPoints(
        self, homography_points: dict[str, HomographyPoint]
    ) -> None:
        if self.list_widget.count() == 0:
            for name, hom in homography_points.items():
                item = QListWidgetItem()
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_widget.setLayout(item_layout)

                line_text = QLabel(f"{name} {hom}", objectName=name)
                item_layout.addWidget(line_text)

                # point_spin_x = QSpinBox()
                # point_spin_x.setMaximum(10000)
                # item_layout.addWidget(point_spin_x)
                # point_spin_y = QSpinBox()
                # point_spin_y.setMaximum(10000)
                # item_layout.addWidget(point_spin_y)

                item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, item_widget)

            self.list_widget.setCurrentRow(0)
        else:
            for name, hom in homography_points.items():
                for i in range(self.list_widget.count()):
                    item = self.list_widget.item(i)
                    row = self.list_widget.itemWidget(item)
                    label = row.findChild(QLabel, name)
                    if label is not None:
                        label.setText(f"{name} {hom}")
                        break

    @Slot(int, QPoint)
    def updateTrack(self, id: int, pos: QPoint):
        label = self.tracks[id]
        label.setText(f"Track {id}: {pos.x()}, {pos.y()}")
