from typing import Tuple
import numpy as np


# https://stackoverflow.com/questions/43219259/how-to-get-the-ray-equation-of-a-2d-point-in-world-space
def imagePointToRay(point: np.ndarray, camera_matrix: np.ndarray, translation: np.ndarray, rotation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    point_on_camera_plane = np.array([(point[0] - camera_matrix[2, 0]) / camera_matrix[0, 0], (point[1] - camera_matrix[2, 1]) / camera_matrix[1, 1], 1])
    # transformation_matrix = ...
    return (translation, transformation_matrix * point_on_camera_plane - translation)
