from PySide6 import QtGui
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QComboBox, QMainWindow, QDialog, QDialogButtonBox
from PySide6.QtGui import QPixmap, QAction, QIcon
from PySide6.QtMultimedia import QMediaDevices, QMediaCaptureSession, QVideoSink, QVideoFrame, QCamera
from PySide6.QtMultimediaWidgets import QVideoWidget
import sys
import cv2
from PySide6.QtCore import Signal, Slot, Qt, QThread, QObject
import numpy as np
import ptvsd
from araviq6 import VideoFrameWorker, VideoFrameProcessor


class CameraSelectDialog(QDialog):
    def __init__(self, availableCameras, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select a camera")

        vbox = QVBoxLayout()

        message = QLabel("Pick a new camera:")
        vbox.addWidget(message)

        self.combobox = QComboBox(self)
        self.combobox.addItems(availableCameras)
        vbox.addWidget(self.combobox)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

    def getCameraId(self) -> int:
        return self.combobox.currentIndex()


class CameraProcessorWorker(VideoFrameWorker):
    def processArray(self, array: np.ndarray) -> np.ndarray:
        # Where Ben makes magic happen
        return cv2.GaussianBlur(array, (0, 0), 1)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lighthouse")

        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.disply_width = 1920
        self.display_height = 1080

        self.availableCameras = []
        cameras = QMediaDevices.videoInputs()
        for cameraDevice in cameras:
            self.availableCameras.append(cameraDevice.description())

        vbox = QVBoxLayout()

        central = QWidget()
        central.setLayout(vbox)
        self.setCentralWidget(central)

        self.camera = QCamera()
        self.captureSession = QMediaCaptureSession()
        self.cameraVideoSink = QVideoSink()
        self.frameProcessor = VideoFrameProcessor()
        self.cameraProcessor = CameraProcessorWorker()
        self.videoWidget = QVideoWidget()
        vbox.addWidget(self.videoWidget)

        self.captureSession.setCamera(self.camera)
        # Or just use this to pipe the camera straight to the UI
        # self.captureSession.setVideoSink(self.videoWidget.videoSink())

        # Converting to opencv and back again is monsterously expensive
        # Potentially the best route is to pipe video direct to UI and draw over using QT
        #   when a specific image processing step is needed then open a new window with
        #   the opencv processing pipeline, do calibration, alignment whatever whatever
        #   there and then on exit that window pushes the resulting matrices etc to the
        #   thread(s) that are processing the inputs and turning it into control signals.
        # If we wanted to implement something like auto following with Tensorflow/PyTorch/CV
        #   then we do the same intercept thing to get numpy arrays, pipe that to the
        #   auto-follow on a separate thread at a lower frame rate but don't convert the
        #   frames back to QT video to save processing power.

        self.captureSession.setVideoSink(self.cameraVideoSink)
        self.cameraVideoSink.videoFrameChanged.connect(
            self.frameProcessor.processVideoFrame
        )
        self.frameProcessor.videoFrameProcessed.connect(
            self.displayVideoFrame)
        self.frameProcessor.setWorker(self.cameraProcessor)

        self.camera.start()

        # https://icons8.com/icon/set/lighthouse/cotton
        self.lighthouseAction = QAction(
            QIcon("images/icons/icons8-lighthouse-64.png"), "&Lighthouse", self)
        self.newAction = QAction(
            QIcon("images/icons/icons8-one-page-64.png"), "&New", self)
        self.openAction = QAction(
            QIcon("images/icons/icons8-folder-64.png"), "&Open", self)
        self.changeCameraAction = QAction(
            QIcon("images/icons/icons8-documentary-64.png"), "&Change Camera", self)
        self.changeCameraAction.triggered.connect(
            self.cameraChangedActionCallback)
        self.exitAction = QAction(
            QIcon("images/icons/icons8-cancel-64.png"), "&Exit", self)
        self.exitAction.triggered.connect(self.exitActionCallback)

        fileToolBar = self.addToolBar("File")
        fileToolBar.addAction(self.lighthouseAction)
        fileToolBar.addAction(self.newAction)
        fileToolBar.addAction(self.openAction)
        fileToolBar.addAction(self.changeCameraAction)
        fileToolBar.addAction(self.exitAction)

    def exitActionCallback(self, s):
        self.close()

    def cameraChangedActionCallback(self, s):
        dialog = CameraSelectDialog(self.availableCameras)
        if (dialog.exec()):
            # TODO is this a race condition?  Does this need communicating over a Signal/Slot?
            # self.video_capture_thread.cam_id = dialog.getCameraId() TODO do something with the new camera ID
            pass

    @Slot(QVideoFrame)
    def displayVideoFrame(self, frame: QVideoFrame):
        self.videoWidget.videoSink().setVideoFrame(frame)

    def closeEvent(self, event):
        self.frameProcessor.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec())
