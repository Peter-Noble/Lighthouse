import pickle
from typing import Tuple

from PySide6.QtCore import Signal, Slot, Qt, QPoint, QObject, QAbstractListModel
from PySide6.QtGui import QVector2D, QVector3D
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QLineEdit, QComboBox
from pathlib import Path
import numpy as np
import cv2 as cv

from plane_ray_intersection import planeRayIntersection

# import ptvsd  # ptvsd.debug_this_thread()


class HomographyPoint:
    def __init__(self, world_coord=QVector3D(), screen_coord=QVector2D()):
        self.world_coord = world_coord
        self.screen_coord = screen_coord

    def __format__(self, format_spec):
        w = f"({round(self.world_coord.x(), 2)}, {round(self.world_coord.y(), 2)}, {round(self.world_coord.z(), 2)}) "
        s = f"({round(self.screen_coord.x(), 2)}, {round(self.screen_coord.y(), 2)})"
        return w + s


class Track:
    def __init__(self, name: str):
        self.name = name
        self.input_device = ""
        self.height_offset = 0.0


class DataStore(QObject):
    track_changed = Signal(int, QVector3D)  # id, screen space pos
    homography_points_changed = Signal(object)  # The dictionary of homography points

    serialise_attributes = [
        "_camera_dist",
        "_camera_matrix",
        "_camera_inv",
        "_homography_points",
        "_t_vec",
        "_r_vec",
        "_height_offset",
        "tracks",
    ]

    def __init__(self):
        super().__init__()

        self.src_folder = Path(__file__).parents[0]

        self._homography_points = {
            # "USL": HomographyPoint(QVector3D(3000, -5000, 0), QVector2D(982, 205)),
            # "USR": HomographyPoint(QVector3D(-3000, -5000, 0), QVector2D(467, 96)),
            # "DSL": HomographyPoint(QVector3D(3000, -11000, 0), QVector2D(801, 676)),
            # "DSR": HomographyPoint(QVector3D(-3000, -11000, 0), QVector2D(70, 410)),
        }
        self._tracks = [QVector3D(), QVector3D()]
        self._camera_inv = None  # np.identity(3, dtype=np.float32)
        self._camera_matrix = np.identity(3, dtype=np.float32)  # 3x3 camera matrix
        self._camera_dist = np.zeros(4, dtype=np.float32)  # 4 vector of distortion coefficients
        self._r_vec = None
        self._t_vec = None

        self.tracks: list[Track] = [Track("Default track"), Track("Default track 2")]

        self._height_offset = 0.0

        # Attempt to load camera calibration numpy saved files
        calibration_matrix_file_dir = str((self.src_folder / "calibration_files" / "calibration_matrix.npy").absolute())
        distortion_coefficients_file_dir = str(
            (self.src_folder / "calibration_files" / "distortion_coefficients.npy").absolute()
        )
        try:
            self._camera_matrix = np.load(calibration_matrix_file_dir)
            self._camera_dist = np.load(distortion_coefficients_file_dir)
            print("\n[info] Camera Calibration Matrix Imported: \n", self._camera_matrix)
        except FileNotFoundError:
            self._camera_matrix = None
            self._camera_dist = None
            print("\n[info] Camera Calibration Matrix Could Not Be Imported")

        self.update_homography()

    def write_previous_config(self, filename: str):
        conf_filename = self.src_folder.parent / "Projects/.conf"
        try:
            file = open(conf_filename, "w")
        except FileNotFoundError:
            return
        file.write(filename)
        file.close()

    def find_previous_config(self):
        conf_filename = self.src_folder.parent / "Projects/.conf"
        try:
            file = open(conf_filename, "r")
        except FileNotFoundError:
            return
        contents = file.readline()
        file.close()

        my_file = Path(contents)
        if my_file.is_file():
            self.deserialise(str(my_file))
        else:
            print("Cannot find file:", my_file)


    def serialise(self):
        return {a: getattr(self, a) for a in self.serialise_attributes}

    def deserialise(self, fileName):
        try:
            file = open(fileName, "rb")
        except FileNotFoundError:
            return
        attributes = pickle.load(file)
        file.close()
        for a in self.serialise_attributes:
            if a in attributes:
                setattr(self, a, attributes[a])
                if a == "_height_offset":
                    self.parent().geometry_settings_dock.height_offset.setValue(attributes[a])
        self.broadcast()

    def broadcast(self) -> None:
        self.homography_points_changed.emit(self._homography_points)
        for id in range(len(self._tracks)):
            self.track_changed.emit(id, self._tracks[id])

    @Slot(float)
    def setHeightOffset(self, height: float):
        self._height_offset = height
        print(height)

    @Slot(str, QVector3D)
    def addNewHomographyPoint(self, name: str, homography: HomographyPoint):
        self._homography_points[name] = homography

    @Slot(str, str, HomographyPoint)
    def setHomographyPoint(self, existing_name: str, updated_name: str, updated_point: HomographyPoint) -> None:
        self._homography_points.pop(existing_name)
        self._homography_points[updated_name] = updated_point
        self.homography_points_changed.emit(self._homography_points)

    @Slot(str)
    def removeHomographyPoint(self, existing_name: str) -> None:
        self._homography_points.pop(existing_name)
        self.homography_points_changed.emit(self._homography_points)

    @Slot(str, QPoint)
    def setHomographyScreenPoint(self, point: QPoint) -> None:
        settings_dock = self.parent().geometry_settings_dock

        if settings_dock.edit_homography_points.checkState() is Qt.CheckState.Unchecked:
            return

        item_widget = settings_dock.list_widget.itemWidget(settings_dock.list_widget.currentItem())
        name = item_widget.findChildren(QLabel)[0].objectName()

        if name != "__add_new__":
            self._homography_points[name].screen_coord = point
            if len(self._homography_points) >= 4:
                self.update_homography()
            self.homography_points_changed.emit(self._homography_points)

    @Slot(int, QPoint)
    def setTrack(self, id: int, point: QPoint) -> None:
        if self.parent().geometry_settings_dock.edit_homography_points.checkState() is Qt.CheckState.Unchecked:
            if id < len(self._tracks):
                new_target = self.apply_homography(point)
                if new_target is not None:
                    self._tracks[id] = new_target
                    self.track_changed.emit(id, self._tracks[id])

    @Slot(QPoint)
    def setTrack0(self, point: QPoint) -> None:
        if self.parent().geometry_settings_dock.edit_homography_points.checkState() is Qt.CheckState.Unchecked:
            new_target = self.apply_homography(point)
            if new_target is not None:
                self._tracks[0] = new_target
                self.track_changed.emit(0, self._tracks[0])

    def getTrack(self, id: int) -> QVector3D:
        return self._tracks[id]

    def getTrack2D(self, id: int) -> Tuple[QVector2D, QVector2D]:
        if self._r_vec is not None and self._t_vec is not None:
            track = self.getTrack(id)
            pts = np.array([track.x(), track.y(), track.z()])
            res, _ = cv.projectPoints(pts, self._r_vec, self._t_vec, self._camera_matrix, self._camera_dist)
            pts = np.array(
                [track.x(), track.y(), track.z() - self._height_offset * 1000]
            )  # TODO subtract height offset in here
            res2, _ = cv.projectPoints(pts, self._r_vec, self._t_vec, self._camera_matrix, self._camera_dist)
            return (QVector2D(res2[0][0][0], res2[0][0][1]), QVector2D(res[0][0][0], res[0][0][1]))
        return (QVector2D(0, 0), QVector2D(0, 0))

    def getNumTracks(self) -> int:
        return len(self._tracks)

    def update_homography(self):
        if self._homography_points.items():
            stage_corners_pixel_locs = []
            stage_corners_world_geometry = []
            for name, hom in self._homography_points.items():
                stage_corners_world_geometry.append(hom.world_coord.toTuple())
                stage_corners_pixel_locs.append(hom.screen_coord.toTuple())
                # print(hom.world_coord.toTuple())

            src = np.array(np.array(stage_corners_pixel_locs, dtype=np.float32))
            dst = np.array(np.array(stage_corners_world_geometry, dtype=np.float32))

            # If calibrated camera, account for distortion parameters:
            if self._camera_matrix is not None:
                src = cv.undistortPoints(
                    np.expand_dims(src, axis=1), self._camera_matrix, self._camera_dist, None, self._camera_matrix
                )

            # Calculate relation between real world planar surface of stage and imaging plane (camera sensor)
            success, r_vec, t_vec = cv.solvePnP(
                objectPoints=dst,
                imagePoints=src,
                cameraMatrix=self._camera_matrix,
                distCoeffs=self._camera_dist,
                flags=cv.SOLVEPNP_IPPE,
            )

            self._r_vec = r_vec
            self._t_vec = t_vec

            rot_m = cv.Rodrigues(r_vec)[0]

            cam_pos = -np.matrix(rot_m).T * np.matrix(t_vec)
            cam_pos = np.array(cam_pos.T.tolist()[0])
            print("\nCamera position within stage system: \n", cam_pos)

            transform_M_i = np.empty((4, 4))
            transform_M_i[:3, :3] = rot_m.T
            transform_M_i[:3, 3] = cam_pos
            transform_M_i[3, :] = [0, 0, 0, 1]

            self._camera_inv = transform_M_i

    def apply_homography(self, screen_point=QPoint) -> QVector3D | None:
        if self._camera_inv is not None:
            img_pt = screen_point.toTuple()

            # If calibrated camera, account for distortion parameters:
            if self._camera_matrix is not None:
                img_pt = cv.undistortPoints(
                    np.array(img_pt, dtype=np.float32),
                    self._camera_matrix,
                    self._camera_dist,
                    None,
                    self._camera_matrix,
                )[0][0]

            cam_pos = self._camera_inv[:3, 3]

            point_on_camera_plane = np.array(
                [
                    (img_pt[0] - self._camera_matrix[0, 2]) / self._camera_matrix[0, 0],
                    (img_pt[1] - self._camera_matrix[1, 2]) / self._camera_matrix[1, 1],
                    1,
                    1,
                ]
            )
            point_in_world_plane = self._camera_inv.dot(point_on_camera_plane)
            point_in_world_plane = point_in_world_plane[:3] / point_in_world_plane[3]

            ray = point_in_world_plane - cam_pos
            result = planeRayIntersection(cam_pos, ray, self._height_offset)
            if result is None:
                return None
            # print(f"Pt {screen_point.toTuple()} -> Real World Coords {result}")
            return QVector3D(result[0], result[1], result[2])
        else:
            return None

    def getHomographyPoints(self):
        return self._homography_points
