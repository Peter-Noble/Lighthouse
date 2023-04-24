"""

Basic implementations of various CV concepts done the "raw OpenCV" way!
(IE buffered camera, reading calibration parameter files, converting between camera pixel coordinate system to world)

"""

import os
import threading
from threading import Lock

import cv2 as cv
import numpy as np


class Camera:
    """
    Class for camera, uses threading to constantly read frames, to prevent buffer filling - which can result in outdated
    frames being grabbed.
    https://forum.opencv.org/t/delay-in-videocapture-because-of-buffer/2755 - 'Funny_pangoline'
    """
    last_frame = None
    last_ready = None
    lock = Lock()
    capture = None
    stopped = False

    def __init__(self, device=0, exposure=-4, width=1920, height=1080):
        self.capture = init_camera_capture(device, exposure, width, height)
        thread = threading.Thread(
            target=self.cam_buffer, args=(), name="read_thread")
        thread.daemon = True
        thread.start()

    def cam_buffer(self):
        while not self.stopped:
            with self.lock:
                self.last_ready = self.capture.grab()

    def read(self):
        if self.last_ready is not None:
            self.last_ready, self.last_frame = self.capture.retrieve()
            return True, self.last_frame.copy()
        else:
            self.stopped = True
            return False, None

    def release(self):
        self.stopped = True
        self.capture.release()

    def isOpened(self):
        if self.capture is not None and self.stopped is False and self.last_ready is not None:
            return True
        return False


def get_working_dir():
    dir = os.getcwd()
    if len(dir.split('/')) > 1:
        dir += '/'
    else:
        dir += '\\'
    return dir


def get_file_dir():
    dir = os.path.dirname(os.path.realpath(__file__))
    if len(dir.split('/')) > 1:
        dir += '/'
    else:
        dir += '\\'
    return dir


def init_camera_capture(device=0, exposure=-5, width=1920, height=1080):
    """
    Set up a VideoCapture for use with the specified camera device
    :param device: (int) index of camera within list of available devices
    :param exposure: (float) the manual exposure level to set
    :param width: horizontal resolution
    :param height: vertical resolution
    :return: (VideoCapture) the object from which video frames can be read
    """
    # Setup capture device
    # cap = cv.VideoCapture(device, apiPreference=cv.CAP_DSHOW)
    cap = cv.VideoCapture(device)

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    cap.set(cv.CAP_PROP_FOURCC, 0x47504A4D)
    # cap.set(cv.CAP_PROP_BUFFERSIZE, 1)

    # Prevent auto-exposure and manually set exposure level
    cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25)
    cap.set(cv.CAP_PROP_EXPOSURE, float(exposure))
    cap.set(cv.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv.CAP_PROP_AUTO_WB, 0.0)
    cap.set(cv.CAP_PROP_FPS, 25)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
    # cap.set(cv.CAP_PROP_SETTINGS, 1)

    return cap


# define storage locations
scripts_file_dir = get_file_dir()
media_file_dir = scripts_file_dir.replace("scripts", "media")
calibrations_file_dir = scripts_file_dir.replace(
    "scripts", "calibration_saved_params")


def post_display_tidy(cap, out=None):
    # When everything done, release the capture
    cap.release()
    if out is not None:
        out.release()
    cv.destroyAllWindows()


def create_display_window(name="Stage View", res=(1280, 720), offset=(0, 0)):
    # cv.namedWindow(name, cv.WND_PROP_FULLSCREEN)
    cv.namedWindow(name)
    # cv.setWindowProperty(name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.resizeWindow(name, res[0], res[1])
    cv.moveWindow(name, offset[0], offset[1])
    blank_img = np.zeros((720, 1280, 3), np.uint8) + 100
    cv.imshow(name, blank_img)
    cv.waitKey(1)
    return name, res[1], res[0]


def read_params_from_xml(fn='calibration_result.xml'):
    path = os.path.join(calibrations_file_dir, fn)
    fs = cv.FileStorage(path, cv.FILE_STORAGE_READ)
    cam_int = fs.getNode('cam_int').mat()
    cam_dist = fs.getNode('cam_dist').mat()

    return cam_int, cam_dist


def read_homography_from_xml(fn='homography_result.xml'):
    path = os.path.join(calibrations_file_dir, fn)
    fs = cv.FileStorage(path, cv.FILE_STORAGE_READ)
    h = fs.getNode('h').mat()
    status = fs.getNode('status').mat()

    return h, status


def read_params_from_npy(fn1='calibration_matrix.npy', fn2='distortion_coefficients.npy'):
    try:
        calib_mat = np.load(os.path.join(calibrations_file_dir, fn1))
        dist = np.load(os.path.join(calibrations_file_dir, fn2))
    except FileNotFoundError:
        calib_mat = None
        dist = None
    print("Camera Calibration Matrix Imported:")
    print(calib_mat)
    return calib_mat, dist
