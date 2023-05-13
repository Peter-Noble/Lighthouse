from PySide6.QtCore import Signal, Slot, Qt, QPoint, QObject
from PySide6.QtGui import QVector2D, QVector3D
from PySide6.QtWidgets import QLabel
from pathlib import Path
import numpy as np
import cv2 as cv


class HomographyPoint:
    def __init__(self, world_coord=QVector3D(), screen_coord=QVector2D()):
        self.world_coord = world_coord
        self.screen_coord = screen_coord

    def __format__(self, format_spec):
        w = f"({round(self.world_coord.x(), 2)}, {round(self.world_coord.y(), 2)}, {round(self.world_coord.z(), 2)}) "
        s = f"({round(self.screen_coord.x(), 2)}, {round(self.screen_coord.y(), 2)})"
        return w + s


class DataStore(QObject):
    track_changed = Signal(int, QVector3D)  # id, screen space pos
    homography_points_changed = Signal(object)  # The dictionary of homography points

    def __init__(self):
        super().__init__()

        self.src_folder = Path(".")

        self._homography_points = {
            "USL": HomographyPoint(QVector3D(3.9, -3, 0), QVector2D(221, 407)),
            "USR": HomographyPoint(QVector3D(-3.9, -3, 0), QVector2D(76, 310)),
            "DSL": HomographyPoint(QVector3D(3.9, -9, 0), QVector2D(168, 646)),
            "DSR": HomographyPoint(QVector3D(-3.9, -9, 0), QVector2D(10, 606)),
        }
        self._tracks = [QPoint()]
        self._camera_location = np.zeros(3, dtype=np.float32)
        self._camera_rotation = np.zeros(3, dtype=np.float32)
        self._camera_matrix = np.identity(3, dtype=np.float32)  # 3x3 camera matrix
        self._camera_distortion = np.zeros(4, dtype=np.float32)  # 4 vector of distortion coefficients

        self.homography_height = 0.0
        self.height_offset = 0.0

        # Attempt to load camera calibration numpy saved files
        calibration_matrix_file_dir = str((self.src_folder / "calibration_matrix.npy").absolute())
        distortion_coefficients_file_dir = str((self.src_folder / "distortion_coefficients.npy").absolute())
        try:
            self.camera_matrix = np.load(calibration_matrix_file_dir)
            self.camera_dist = np.load(distortion_coefficients_file_dir)
            print("\n[info] Camera Calibration Matrix Imported: \n", self.camera_matrix)
        except FileNotFoundError:
            self.camera_matrix = None
            self.camera_dist = None
            print("\n[info] Camera Calibration Matrix Could Not Be Imported")

        self.update_homography()

    def serialise():
        pass

    def deserialise():
        pass

    def broadcast(self) -> None:
        self.homography_points_changed.emit(self._homography_points)
        for id in range(len(self._tracks)):
            self.track_changed.emit(id, self._tracks[id])

    @Slot(float)
    def setHomographyHeight(self, height: float):
        self.homography_height = height
        print(height)

    @Slot(float)
    def setHeightOffset(self, height: float):
        self.height_offset = height
        print(height)

    @Slot(str, HomographyPoint)
    def setHomographyPoint(self, name: str, point: HomographyPoint) -> None:
        self._homography_points[name] = point
        self.homography_points_changed.emit(self._homography_points)

    @Slot(str, QPoint)
    def setHomographyScreenPoint(self, point: QPoint) -> None:
        settings_dock = self.parent().settings_dock

        if settings_dock.edit_homography_points.checkState() is Qt.CheckState.Unchecked:
            return

        item_widget = settings_dock.list_widget.itemWidget(settings_dock.list_widget.currentItem())
        name = item_widget.findChildren(QLabel)[0].objectName()

        self._homography_points[name].screen_coord = point
        self.update_homography()
        self.homography_points_changed.emit(self._homography_points)

    @Slot(int, QPoint)
    def setTrack(self, id: int, point: QPoint) -> None:
        self._tracks[id] = point
        self.track_changed.emit(id, self.apply_homography(point))

    @Slot(QPoint)
    def setTrack0(self, point: QPoint) -> None:
        self._tracks[0] = point
        self.track_changed.emit(id, self.apply_homography(point))

    def getTrack(self, id: int) -> QPoint:
        return self._tracks[id]

    def update_homography(self):
        stage_corners_pixel_locs = []
        stage_corners_world_geometry = []
        for name, hom in self._homography_points.items():
            stage_corners_world_geometry.append(hom.world_coord.toTuple())
            stage_corners_pixel_locs.append(hom.screen_coord.toTuple())

        src = np.array(np.array(stage_corners_pixel_locs, dtype=np.float32))
        dst = np.array(np.array(stage_corners_world_geometry, dtype=np.float32))

        # If calibrated camera, account for distortion parameters:
        if self.camera_matrix is not None:
            src = cv.undistortPoints(np.expand_dims(src, axis=1), self.camera_matrix, self.camera_dist, None, self.camera_matrix)

        # Homography relation between real world planar surface of stage and imaging plane (camera sensor)
        self._homography, _ = cv.findHomography(src, dst)
        print("\nHomography from img plane to stage system: \n", self._homography)

    def apply_homography(self, screen_point=QPoint):
        if self._homography is not None and not np.isnan(self._homography).any():
            img_pt = screen_point.toTuple()

            # If calibrated camera, account for distortion parameters:
            if self.camera_matrix is not None:
                img_pt = cv.undistortPoints(np.array(img_pt, dtype=np.float32), self.camera_matrix, self.camera_dist, None, self.camera_matrix)[0][0]

            t_x, t_y, t_z = np.dot(self._homography, [[[img_pt[0]], [img_pt[1]], [1]]])
            target_world_geometry = QVector3D(float(t_x) / float(t_z), float(t_y) / float(t_z), 0)
            print(f"Pt {screen_point.toTuple()} -> Real World Coords {target_world_geometry.toTuple()}")
            return target_world_geometry
        else:
            return None
