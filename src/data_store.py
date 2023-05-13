from PySide6.QtCore import Signal, Slot, Qt, QPoint, QObject
from PySide6.QtGui import QVector2D, QVector3D
from PySide6.QtWidgets import QLabel
import numpy as np


class HomographyPoint:
    def __init__(self, world_coord=QVector3D(), screen_coord=QVector2D()):
        self.world_coord = world_coord
        self.screen_coord = screen_coord

    def __format__(self, format_spec):
        w = f"({round(self.world_coord.x(), 2)}, {round(self.world_coord.y(), 2)}, {round(self.world_coord.z(), 2)}) "
        s = f"({round(self.screen_coord.x(), 2)}, {round(self.screen_coord.y(), 2)})"
        return w + s


class DataStore(QObject):
    track_changed = Signal(int, QPoint)  # id, screen space pos
    homography_points_changed = Signal(object)  # The dictionary of homography points

    def __init__(self):
        super().__init__()
        self._homography_points = {
            "USL": HomographyPoint(QVector3D(0, 0, 0), QVector2D(0, 0)),
            "USR": HomographyPoint(QVector3D(12, 0, 0), QVector2D(0, 0)),
            "DSL": HomographyPoint(QVector3D(0, 8, 0), QVector2D(0, 0)),
            "DSR": HomographyPoint(QVector3D(12, 8, 0), QVector2D(0, 0)),
        }
        self._tracks = [QPoint()]
        self._camera_location = np.zeros(3, dtype=np.float32)
        self._camera_rotation = np.zeros(3, dtype=np.float32)
        self._camera_matrix = np.identity(3, dtype=np.float32)  # 3x3 camera matrix
        self._camera_distortion = np.zeros(4, dtype=np.float32)  # 4 vector of distortion coefficients
        
    def serialise():
        pass

    def deserialise():
        pass

    def broadcast(self) -> None:
        self.homography_points_changed.emit(self._homography_points)
        for id in range(len(self._tracks)):
            self.track_changed.emit(id, self._tracks[id])

    @Slot(str, HomographyPoint)
    def setHomographyPoint(self, name: str, point: HomographyPoint) -> None:
        self._homography_points[name] = point
        self.homography_points_changed.emit(self._homography_points)

    @Slot(str, QPoint)
    def setHomographyScreenPoint(self, point: QPoint) -> None:
        settings_dock = self.parent().settings_dock

        if settings_dock.edit_homography_points.checkState() is Qt.CheckState.Unchecked:
            return

        item_widget = settings_dock.list_widget.itemWidget(
            settings_dock.list_widget.currentItem()
        )
        name = item_widget.findChildren(QLabel)[0].objectName()

        self._homography_points[name].screen_coord = point
        self.homography_points_changed.emit(self._homography_points)

    @Slot(int, QPoint)
    def setTrack(self, id: int, point: QPoint) -> None:
        self._tracks[id] = point
        self.track_changed.emit(id, point)

    @Slot(QPoint)
    def setTrack0(self, point: QPoint) -> None:
        self._tracks[0] = point
        self.track_changed.emit(id, point)

    def getTrack(self, id: int) -> QPoint:
        return self._tracks[id]
