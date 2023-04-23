import sys

import cv2
import numpy as np
# import ptvsd  # ptvsd.debug_this_thread()

import os
os.environ["QT_DRIVER"] = "PySide6"
from araviq6 import VideoFrameProcessor, VideoFrameWorker, ScalableQLabel
import qimage2ndarray

from PySide6.QtCore import Signal, Slot, Qt, QPoint
from PySide6.QtGui import QAction, QIcon, QMouseEvent, QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtMultimedia import (QCamera, QMediaCaptureSession, QMediaDevices,
                                  QVideoFrame, QVideoSink)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog,
                               QDialogButtonBox, QLabel, QMainWindow,
                               QVBoxLayout, QWidget, QDockWidget, QListWidget,
                               QListWidgetItem, QPushButton, QHBoxLayout,
                               QSpinBox)


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


class VideoDisplayWidget(ScalableQLabel):
    clickPosition = Signal(QPoint)

    def mouseToVideoRes(self, pos: QPoint) -> QPoint:
        # TODO guard against divisions by zero
        # res = self.videoSink().videoSize()
        res = self.originalPixmap().size()
        res_asp = res.width() / res.height()
        size = self.size()
        size_asp = size.width() / size.height()
        x = max(0, min(pos.x() / size.width() * res.width(), res.width()))
        y = max(0, min(pos.y() / size.height() * res.height(), res.height()))
        if (size_asp > res_asp):
            x_width = size.height() * res_asp
            x_extra = size.width() - x_width
            x_use = pos.x() - x_extra / 2
            x = max(0, min(x_use / size.width() * res.width(), res.width()))
        else:
            y_height = size.width() / res_asp
            y_extra = size.height() - y_height
            y_use = pos.y() - y_extra / 2
            y = max(0, min(y_use / y_height * res.height(), res.height()))
        return QPoint(x, y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clickPosition.emit(self.mouseToVideoRes(event.pos()))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.clickPosition.emit(self.mouseToVideoRes(event.pos()))


class SettingsDock(QDockWidget):
    track_change = Signal(QPoint)

    def __init__(self):
        super().__init__()

        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget(None))

        self.settings_layout_widget = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_layout_widget.setLayout(self.settings_layout)
        self.setWidget(self.settings_layout_widget)

        self.listWidget = QListWidget()
        self.settings_layout.addWidget(self.listWidget)

        for point in ["USR", "USL", "DSR", "DSL"]:
            item = QListWidgetItem()
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_widget.setLayout(item_layout)

            line_text = QLabel(point)
            item_layout.addWidget(line_text)

            point_spin_x = QSpinBox()
            point_spin_x.setMaximum(10000)
            item_layout.addWidget(point_spin_x)
            point_spin_y = QSpinBox()
            point_spin_y.setMaximum(10000)
            item_layout.addWidget(point_spin_y)

            item.setSizeHint(item_widget.sizeHint())
            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item, item_widget)

        self.listWidget.setCurrentRow(0)

        track_coord_layout = QHBoxLayout()
        self.settings_layout.addLayout(track_coord_layout)

        self.track_x = QSpinBox()
        self.track_x.setMaximum(4096)
        self.track_y = QSpinBox()
        self.track_y.setMaximum(2048)
        track_coord_layout.addWidget(self.track_x)
        track_coord_layout.addWidget(self.track_y)

        self.track_x.valueChanged.connect(self.updateTrack)
        self.track_y.valueChanged.connect(self.updateTrack)

    def updateTrack(self, _):
        self.track_change.emit(QPoint(self.track_x.value(), self.track_y.value()))

    @Slot(QPoint)
    def update_coordinate(self, pos: QPoint):
        # print(f"Update coordinate {pos}")
        # print(f"Current row {self.listWidget.currentRow()}")
        list_row = self.listWidget.currentItem()
        row = self.listWidget.itemWidget(list_row)
        boxes = row.findChildren(QSpinBox)
        boxes[0].setValue(pos.x())
        boxes[1].setValue(pos.y())


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lighthouse")
        self.resize(600, 300)

        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.disply_width = 1920
        self.display_height = 1080

        self.track_position = QPoint(0, 0)

        vbox = QVBoxLayout()

        central = QWidget()
        central.setLayout(vbox)
        self.setCentralWidget(central)

        self.camera = QCamera()
        self.captureSession = QMediaCaptureSession()
        self.cameraVideoSink = QVideoSink()
        # # # self.frameProcessor = VideoFrameProcessor()
        # # # self.cameraProcessor = CameraProcessorWorker()
        self.videoWidget = VideoDisplayWidget()
        vbox.addWidget(self.videoWidget)

        self.captureSession.setCamera(self.camera)
        # # # Or just use this to pipe the camera straight to the UI
        # # # self.captureSession.setVideoSink(self.videoWidget.videoSink())

        # # # Converting to opencv and back again is monsterously expensive
        # # # Potentially the best route is to pipe video direct to UI and draw over using QT
        # # #   when a specific image processing step is needed then open a new window with
        # # #   the opencv processing pipeline, do calibration, alignment whatever whatever
        # # #   there and then on exit that window pushes the resulting matrices etc to the
        # # #   thread(s) that are processing the inputs and turning it into control signals.
        # # # If we wanted to implement something like auto following with Tensorflow/PyTorch/CV
        # # #   then we do the same intercept thing to get numpy arrays, pipe that to the
        # # #   auto-follow on a separate thread at a lower frame rate but don't convert the
        # # #   frames back to QT video to save processing power.

        self.captureSession.setVideoSink(self.cameraVideoSink)
        self.cameraVideoSink.videoFrameChanged.connect(self.displayVideoFrame)
        # # # self.cameraVideoSink.videoFrameChanged.connect(
        # # #     self.frameProcessor.processVideoFrame)
        # # # self.frameProcessor.videoFrameProcessed.connect(self.displayVideoFrame)
        # # # self.frameProcessor.setWorker(self.cameraProcessor)

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
        fileToolBar.setMovable(False)

        self.settingsDock = SettingsDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.settingsDock)
        self.settingsDock.track_change.connect(self.updateTrackPosition)

        self.videoWidget.clickPosition.connect(self.settingsDock.update_coordinate)

    def exitActionCallback(self, s):
        self.close()

    def cameraChangedActionCallback(self, s):
        dialog = CameraSelectDialog([c.description()
                                    for c in QMediaDevices.videoInputs()])
        if (dialog.exec()):
            self.camera.stop()

            # TODO a bit of a crude way to achieve this.
            #   Find out how to change the camera without rebuilding the whole pipeline.
            del self.camera
            del self.captureSession
            del self.cameraVideoSink
            # self.frameProcessor.stop()
            # del self.frameProcessor
            # del self.cameraProcessor

            self.camera = QCamera()
            self.captureSession = QMediaCaptureSession()
            self.cameraVideoSink = QVideoSink()
            # self.frameProcessor = VideoFrameProcessor()
            # self.cameraProcessor = CameraProcessorWorker()

            self.camera = QCamera(QMediaDevices.videoInputs()[
                                  dialog.getCameraId()])

            # Or just use this to pipe the camera straight to the UI
            # self.captureSession.setCamera(self.camera)
            # self.captureSession.setVideoSink(self.videoWidget.videoSink())

            self.captureSession.setCamera(self.camera)
            self.captureSession.setVideoSink(self.cameraVideoSink)
            self.cameraVideoSink.videoFrameChanged.connect(self.displayVideoFrame)
            # self.cameraVideoSink.videoFrameChanged.connect(
            #     self.frameProcessor.processVideoFrame)
            # self.frameProcessor.videoFrameProcessed.connect(
            #     self.displayVideoFrame)
            # self.frameProcessor.setWorker(self.cameraProcessor)
            self.camera.start()

    @Slot(QVideoFrame)
    def displayVideoFrame(self, frame: QVideoFrame):
        # image_as_numpy_array = qimage2ndarray.rgb_view(frame.toImage(), byteorder=None)
        img = frame.toImage()

        painter = QPainter(img)

        painter.setRenderHints(QPainter.Antialiasing, True)
        # set the brush and pen to the same color
        painter.setBrush(QColor(255, 0, 0))
        pen = QPen()
        pen.setColor(QColor(255, 0, 0))
        pen.setWidth(3)
        painter.setPen(pen)

        brush = QBrush()
        brush.setColor(QColor(0, 0, 0, 0))
        painter.setBrush(brush)

        painter.drawEllipse(self.track_position, 50, 50)

        painter.end()

        pix = QPixmap.fromImage(img)
        self.videoWidget.setPixmap(pix)
        # self.videoWidget.videoSink().setVideoFrame(frame)

    @Slot(QPoint)
    def updateTrackPosition(self, point: QPoint):
        self.track_position = point

    def closeEvent(self, event):
        # self.frameProcessor.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec())
