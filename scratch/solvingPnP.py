
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


src_folder = Path(".")
# Attempt to load camera calibration numpy saved files
calibration_matrix_file_dir = str((src_folder / "calibration_matrix.npy").absolute())
distortion_coefficients_file_dir = str((src_folder / "distortion_coefficients.npy").absolute())
camera_matrix = np.load(calibration_matrix_file_dir)
camera_dist = np.load(distortion_coefficients_file_dir)
print("\n[info] Camera Calibration Matrix Imported: \n", camera_matrix)

_homography_points = {
    "USL": HomographyPoint(QVector3D(3000, -5000, 0), QVector2D(982, 205)),
    "USR": HomographyPoint(QVector3D(-3000, -5000, 0), QVector2D(467, 96)),
    "DSL": HomographyPoint(QVector3D(3000, -11000, 0), QVector2D(801, 676)),
    "DSR": HomographyPoint(QVector3D(-3000, -11000, 0), QVector2D(70, 410)),
}

"""_homography_points = {
    "USL": HomographyPoint(QVector3D(0, 0, 0), QVector2D(1293, 320)),
    "USR": HomographyPoint(QVector3D(878, 0, 0), QVector2D(601, 316)),
    "DSL": HomographyPoint(QVector3D(0, 1000, 0), QVector2D(1530, 969)),
    "DSR": HomographyPoint(QVector3D(878, 1000, 0), QVector2D(436, 996)),
    "XTRA1": HomographyPoint(QVector3D(377.5, 0, 0), QVector2D(1002, 308)),
    #"XTRA2": HomographyPoint(QVector3D(878, 1000, 0), QVector2D(436, 996)),
}"""

"""camera_matrix = np.array(
    [
        [60, 0.00000000e+00, 6.40275357e+02],
        [0, 60, 3.59394975e+02],
        [0, 0, 1]
])"""

stage_corners_pixel_locs = []
stage_corners_world_geometry = []
for name, hom in _homography_points.items():
    stage_corners_world_geometry.append(hom.world_coord.toTuple())
    src = hom.screen_coord.toTuple()
    #if camera_matrix is not None:
    #    src = cv.undistortPoints(np.expand_dims(src, axis=1), camera_matrix, camera_dist, None, camera_matrix)[0][0]
    stage_corners_pixel_locs.append(src)

points2d = np.array(stage_corners_pixel_locs, dtype=np.float32)
points3d = np.array(stage_corners_world_geometry, dtype=np.float32)

print(points3d)
print(points2d)

success, r_vec, t_vec = cv.solvePnP(objectPoints=points3d, imagePoints=points2d, cameraMatrix=camera_matrix, distCoeffs=camera_dist, flags=cv.SOLVEPNP_IPPE)
print(success, "\n", r_vec, "\n\n", t_vec)

rot_m = cv.Rodrigues(r_vec)[0]
print(rot_m)
cam_pos = -np.matrix(rot_m).T * np.matrix(t_vec)
cam_pos = np.array(cam_pos.T.tolist()[0])
print("\n\n\n\n\nCAM POS\n", cam_pos)


point = (982, 205)

point_on_camera_plane = np.array(
    [(point[0] - camera_matrix[2, 0]) / camera_matrix[0, 0], (point[1] - camera_matrix[2, 1]) / camera_matrix[1, 1], 1, 1]
)

print("PETER'S SUM:\n", 2000*rot_m.dot(point_on_camera_plane[0:3]))
print("PETER'S SUM:\n", cam_pos + 2000*rot_m.dot(point_on_camera_plane[0:3]))

transform_M = np.empty((4, 4))
transform_M[:3, :3] = rot_m
transform_M[:3, 3] = t_vec.T
transform_M[3, :] = [0, 0, 0, 1]

print(transform_M)
print(point_on_camera_plane)
point_in_world_plane = np.linalg.inv(transform_M).dot(point_on_camera_plane)[0:3]
print("\n\npt in world:\n", point_in_world_plane, "\n")
print("\n\ncam in world:\n", cam_pos, "\n")

# Assume plane is at z=0 and totally level
def planeRayIntersection(ray_origin: np.array, ray_direction: np.array, target_height: float = 0) -> np.ndarray | None:
    normal = np.array([0.0, 0.0, 1.0])
    centre = np.array([0.0, 0.0, 0.0])
    denom = normal.dot(ray_direction);
    if (abs(denom) > 0.000001):
        t = (centre - (ray_origin - np.array([0, 0, target_height]))).dot(normal) / denom
        if (t > 0):
            return ray_origin + ray_direction * t
    return

print(planeRayIntersection(cam_pos, point_in_world_plane-cam_pos, 0))