import numpy as np
import helper_functions as fn
import cv2 as cv
from os import path

# Attempt to load camera calibration numpy saved files
calibrations_file_dir = ".\\"
fn1 = 'calibration_matrix.npy'
fn2 = 'distortion_coefficients.npy'
try:
    camera_matrix = np.load(path.join(calibrations_file_dir, fn1))
    camera_dist = np.load(path.join(calibrations_file_dir, fn2))
    print("\n[info] Camera Calibration Matrix Imported:")
    print(camera_matrix)
except FileNotFoundError:
    camera_matrix = None
    camera_dist = None
    print("\n[info] Camera Calibration Matrix Could Not Be Imported")

# Define stage geometry in real-world coordinates
stage_corners_world_geometry = {"upstage-right": [0, 0, 0],
                                "upstage-left": [12, 0, 0],
                                "downstage-right": [0, 8, 0],
                                "downstage-left": [12, 8, 0]}
stage_corners_pixel_locs = {}

# Instantiate camera and operator window
print("\n[info] Initialising Camera Input, Please Wait...")
cap = fn.Camera(0, -2, 1280, 720)
op_window, w, h = fn.create_display_window("Operator View", (1280, 720))
print("\n[info] Camera Initialised. Please Follow The Onscreen Instructions.")

# Deal with mouse click positions
pos_list = []


def onMouseDuringSetup(event, x, y, flags, param):
    global pos_list
    if event == cv.EVENT_LBUTTONDOWN:
        print('x = %d, y = %d' % (x, y))
        pos_list.append((x, y))


def onMouseDuringOperation(event, x, y, flags, param):
    global H
    if event == cv.EVENT_LBUTTONDOWN:
        img_pt = [x, y, 1]
        t_x, t_y, t_z = np.array(np.dot(H, img_pt))
        target_world_geometry = [t_x / t_z, t_y / t_z, 0]
        print("\nImage pt: {} in stage coordinate system: \n{}".format(
            (x, y), target_world_geometry))


cv.setMouseCallback(op_window, onMouseDuringSetup)

if cap.isOpened():
    while True:
        # grab frame from camera
        ret, frame = cap.read()

        cv.putText(frame, "Please align the camera, then press 'a' to begin", (10, 25),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, 8)

        # display frames to operator
        cv.imshow(op_window, frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord('a'):
            break

    # Setup stage corner locations
    for label in stage_corners_world_geometry:
        while True:
            print(label)
            # grab frame from camera
            ret, frame = cap.read()

            cv.putText(frame, "Select the location of corner '" + label + "' then press 'a'", (10, 25),
                       cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, 8)

            # display frames to operator
            cv.imshow(op_window, frame)
            key = cv.waitKey(0) & 0xFF
            if key == ord('a'):
                if len(pos_list) > 0 and pos_list[-1] not in stage_corners_pixel_locs.values():
                    stage_corners_pixel_locs[label] = pos_list[-1]
                    break
            elif key == ord('x') or key == ord('q'):
                fn.post_display_tidy(cap)
                exit(0)

    src = np.array(list(stage_corners_pixel_locs.values()), dtype=np.float32)
    dst = np.array(list(stage_corners_world_geometry.values()),
                   dtype=np.float32)

    # If calibrated camera, account for distortion parameters:
    if camera_matrix is not None:
        src = cv.undistortPoints(np.expand_dims(
            src, axis=1), camera_matrix, camera_dist, None, camera_matrix)

    # Homography relation between real world planar surface of stage and imaging plane (camera sensor)
    H, _ = cv.findHomography(src, dst)
    print("\nHomography from img plane to stage system: \n", H)

    cv.setMouseCallback(op_window, onMouseDuringOperation)

    while True:

        # grab frames from camera
        ret, frame = cap.read()

        cv.putText(frame, "Press 'x' to exit", (10, 25),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, 8)

        # display frames to operator
        cv.imshow(op_window, frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord('x') or key == ord('q'):
            break

fn.post_display_tidy(cap)
