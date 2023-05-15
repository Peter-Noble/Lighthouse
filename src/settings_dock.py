import numpy as np
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QDockWidget, QListWidget, QListWidgetItem, QHBoxLayout, \
    QCheckBox, QSlider
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QVector3D, QVector2D

from data_store import HomographyPoint
from settings_dialogs import AddNewPointDialog


class DoubleSlider(QSlider):
    # create our our signal that we can connect to if necessary
    doubleValueChanged = Signal(float)

    def __init__(self, decimals=2, *args, **kargs):
        super(DoubleSlider, self).__init__(*args, **kargs)
        self._multi = 10 ** decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        value = float(super(DoubleSlider, self).value()) / self._multi
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super(DoubleSlider, self).value()) / self._multi

    def setMinimum(self, value):
        return super(DoubleSlider, self).setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super(DoubleSlider, self).setMaximum(value * self._multi)

    def setSingleStep(self, value):
        return super(DoubleSlider, self).setSingleStep(value * self._multi)

    def singleStep(self):
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def setValue(self, value):
        super(DoubleSlider, self).setValue(int(value * self._multi))


class SettingsDock(QDockWidget):
    addNewHomographyPoint = Signal(str, HomographyPoint)

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
        self.edit_homography_points.setChecked(True)
        self.settings_layout.addWidget(self.edit_homography_points)

        self.track0 = QLabel("Track 0: 0.0, 0.0")
        self.tracks = [self.track0]
        self.settings_layout.addWidget(self.track0)

        self.settings_layout.addWidget(QLabel("Height offset"))
        self.height_offset = DoubleSlider(orientation=Qt.Orientation.Horizontal)
        self.height_offset.setMinimum(-2)
        self.height_offset.setMaximum(2)
        self.height_offset.setTickInterval(0.01)
        self.settings_layout.addWidget(self.height_offset)

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

    @Slot(str, HomographyPoint)
    def addHomographyPoint(self, name, hom):
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

    @Slot(object)  # dict[str, HomographyPoint]
    def updateHomographyPoints(self, homography_points: dict[str, HomographyPoint]) -> None:
        if self.list_widget.count() == 0:
            add_new = QListWidgetItem()
            add_new.setData(-1, "__add_new__")
            add_new_widget = QWidget()
            add_new_layout = QHBoxLayout()
            add_new_widget.setLayout(add_new_layout)
            line_text = QLabel("Add New", objectName="__add_new__")
            add_new_layout.addWidget(line_text)
            add_new.setSizeHint(add_new_widget.sizeHint())
            self.list_widget.addItem(add_new)
            self.list_widget.setItemWidget(add_new, add_new_widget)
            self.list_widget.itemClicked.connect(self.homographyListClick)

            for name, hom in homography_points.items():
                self.addHomographyPoint(name, hom)

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


    @Slot(int, QVector3D)
    def updateTrack(self, id: int, pos: QVector3D):
        print("Updating track:", pos)
        label = self.tracks[id]
        label.setText(f"Track {id}: {round(pos.x(), 2)}, {round(pos.y(), 2)}, {round(pos.z(), 2)}")

    def homographyListClick(self, item: QListWidgetItem):
        if str(item.data(-1)) == "__add_new__":
            dlg = AddNewPointDialog()
            ret = dlg.exec_()
            if ret:
                new_point = dlg.current_unit_multiplier * QVector3D(
                    float(dlg.x_input.text()), float(dlg.y_input.text()), float(dlg.z_input.text())
                )
                new_homogrphy_pt = HomographyPoint(new_point, QVector2D(0, 0))
                self.addNewHomographyPoint.emit(dlg.pt_label_input.text(), new_homogrphy_pt)
                self.addHomographyPoint(dlg.pt_label_input.text(), new_homogrphy_pt)

