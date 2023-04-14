import cv2 as cv
import numpy as np
from os import path

# Attempt to load camera calibration numpy saved files
calibrations_file_dir = ".\\"
fn1 = 'calibration_matrix.npy'
fn2 = 'distortion_coefficients.npy'
try:
    camera_matrix = np.load(path.join(calibrations_file_dir, fn1))
    camera_dist = np.load(path.join(calibrations_file_dir, fn2))
except FileNotFoundError:
    calib_mat = None
    dist = None
print("\nCamera Calibration Matrix Imported:")
print(camera_matrix)

# Define geometry of stage and label each point(?)
# Note this example in left-handed coords (Z up) w/ origin at upstage stage-right corner
stage_corners_world_geometry = {"upstage-right": [0, 0, 0],
                                "upstage-left": [12, 0, 0],
                                "downstage-right": [0, 8, 0],
                                "downstage-left": [12, 8, 0]}

# For each label, user selects corresponding location in viewfinder
# Note this example in OpenCV coords format (origin at top left of image)
stage_corners_pixel_locs = {"upstage-right": [143, 96],
                            "upstage-left": [1114, 112],
                            "downstage-right": [127, 676],
                            "downstage-left": [1096, 700]}

src = np.array(list(stage_corners_pixel_locs.values()), dtype=np.float32)
dst = np.array(list(stage_corners_world_geometry.values()), dtype=np.float32)

# If calibrated camera, account for distortion parameters:
if camera_matrix is not None:
    src = cv.undistortPoints(np.expand_dims(src, axis=1), camera_matrix, camera_dist, None, camera_matrix)

# Homography relation between real world planar surface of stage and imaging plane (camera sensor)
H, _ = cv.findHomography(src, dst)
print("\nHomography from img plane to stage system: \n", H)

# Convert user-selected pixel location into stage coordinate system
target_pixel_loc = [1100, 450]
img_pt = [target_pixel_loc[0], target_pixel_loc[1], 1]
t_x, t_y, t_z = np.array(np.dot(H, img_pt))
target_world_geometry = [t_x/t_z, t_y/t_z, 0]
print("\nImage pt: {} in stage coordinate system: \n{}".format(target_pixel_loc, target_world_geometry))

# Currently still need to address:
# Camera distortion - ADDRESSED
#       In pure OpenCV-land, would usually undistort image as soon as captured before displaying to user,
#       but unsure how to do that with QCamera
#
#       Can almost certainly do it much faster on a per-pixel basis in the above calculations, but I'm unsure what
#       the speediest way would be - just needs a quick Google!
#
# Non-planar stage
#       Could possibly create multiple homographies, one per z-height, and switch between automatically,
#       but this is not a flexible solution or trivial to solve
#
#       https://www.reddit.com/r/computervision/comments/2f6uyq/opencv_reverse_projection_from_2d_to_3d_given_an/
#
#       If we are guaranteed to have a robust camera calibration, we could do a proper projection - project from the
#       camera imaging origin through the defined pixel to define a line within the world coordinate system,
#       then calculate this line's intersection with our defined stage geometry?
#           Would still need to account for height of spotlight centre above staging IE height of performer etc.
#               Assuming operator aims target at performer's head / torso, we would have to offset projected line
#               downwards to find intersection with stage at performer's feet to ensure correct level of staging that
#               performer is standing on, then re-offset the z-height to their head / torso for output.

