import numpy as np

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

if __name__ == "__main__":
    assert np.linalg.norm(planeRayIntersection(np.array([0, 10, 10]), np.array([0, -1, -1])) - np.array([0, 0, 0])) < 0.00001
    assert np.linalg.norm(planeRayIntersection(np.array([0, 0, 10]), np.array([0, 0, -1])) - np.array([0, 0, 0])) < 0.00001
    assert np.linalg.norm(planeRayIntersection(np.array([0, 20, 10]), np.array([0, -2, -1])) - np.array([0, 0, 0])) < 0.00001
    assert np.linalg.norm(planeRayIntersection(np.array([0, 10, 10]), np.array([0, -2, -1])) - np.array([0, -10, 0])) < 0.00001
    assert planeRayIntersection(np.array([0, 0, 10]), np.array([0, 0, 1])) is None
    assert np.linalg.norm(planeRayIntersection(np.array([0, 10, 12]), np.array([0, -1, -1]), 2) - np.array([0, 0, 2])) < 0.00001
    assert np.linalg.norm(planeRayIntersection(np.array([0, 0, 10]), np.array([0, 0, -1]), 2) - np.array([0, 0, 2])) < 0.00001
