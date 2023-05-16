import os
import pickle
import sys

# import ptvsd  # ptvsd.debug_this_thread()

os.environ["QT_DRIVER"] = "PySide6"

from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import (
    QAction,
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QVector3D,
)
from PySide6.QtMultimedia import (
    QCamera,
    QMediaCaptureSession,
    QMediaDevices,
    QVideoFrame,
    QVideoSink,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from camera_select_dialog import CameraSelectDialog
from settings_dock import SettingsDock
from video_display_widget import VideoDisplayWidget
from data_store import DataStore
from psn_output import PSNOutput
from space_mouse import SpaceMouse


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lighthouse")
        self.resize(800, 400)

        # self.setWindowFlags(Qt.FramelessWindowHint)

        self.data = DataStore()
        self.data.setParent(self)

        self._previous_save_filename = str((self.data.src_folder / "showfile.lho").absolute())

        vbox = QVBoxLayout()

        central = QWidget()
        central.setLayout(vbox)
        self.setCentralWidget(central)

        self.video_widget = VideoDisplayWidget()
        vbox.addWidget(self.video_widget)

        self.camera = QCamera()
        self.capture_session = QMediaCaptureSession()
        self.camera_video_sink = QVideoSink()

        self.capture_session.setCamera(self.camera)

        self.capture_session.setVideoSink(self.camera_video_sink)
        self.camera_video_sink.videoFrameChanged.connect(self.displayVideoFrame)

        self.camera.start()

        # https://icons8.com/icon/set/lighthouse/cotton
        self.lighthouse_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-lighthouse-64.png").absolute())), "&Lighthouse", self
        )
        self.new_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-one-page-64.png").absolute())), "&New", self
        )
        # self.new_action.triggered.connect(self.newActionCallback)
        self.save_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-save-64.png").absolute())), "&Save", self
        )
        self.save_action.triggered.connect(self.saveActionCallback)
        self.save_action.setShortcut("Ctrl+S")
        self.open_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-folder-64.png").absolute())), "&Open", self
        )
        self.open_action.triggered.connect(self.openActionCallback)
        self.psn_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-track-order-64.png").absolute())),
            "&PSN Settings",
            self,
        )
        self.psn_action.triggered.connect(self.psnActionCallback)
        self.change_camera_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-documentary-64.png").absolute())),
            "&Change Camera",
            self,
        )
        self.change_camera_action.triggered.connect(self.cameraChangedActionCallback)
        self.exit_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-cancel-64.png").absolute())), "&Exit", self
        )
        self.exit_action.triggered.connect(self.exitActionCallback)

        file_tool_bar = self.addToolBar("File")
        file_tool_bar.addAction(self.lighthouse_action)
        file_tool_bar.addAction(self.new_action)
        file_tool_bar.addAction(self.save_action)
        file_tool_bar.addAction(self.open_action)
        file_tool_bar.addAction(self.psn_action)
        file_tool_bar.addAction(self.change_camera_action)
        file_tool_bar.addAction(self.exit_action)
        file_tool_bar.setMovable(False)

        self.settings_dock = SettingsDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.settings_dock)
        # self.settingsDock.track_changed.connect(self.data.setTrack)

        self.settings_dock.height_offset.doubleValueChanged.connect(self.data.setHeightOffset)

        self.data.track_changed.connect(self.settings_dock.updateTrack)
        self.data.homography_points_changed.connect(self.settings_dock.updateHomographyPoints)

        self.video_widget.click_position.connect(self.data.setHomographyScreenPoint)
        self.video_widget.click_position.connect(self.data.setTrack0)

        self.settings_dock.addNewHomographyPoint.connect(self.data.addNewHomographyPoint)
        self.settings_dock.editHomographyPoint.connect(self.data.setHomographyPoint)
        self.settings_dock.removeHomographyPoint.connect(self.data.removeHomographyPoint)

        self.data.broadcast()

        self.psn_output = PSNOutput()
        self.psn_output.addTrack()
        self.data.track_changed.connect(self.psn_output.setTrackWithPos)

        try:
            self.space_mouse = SpaceMouse(parent=self)
            self.space_mouse.cursor_moved.connect(self.data.setTrack0)
        except AttributeError:
            print("[Error] No 3d input device found")

    def exitActionCallback(self, s):
        self.close()

    def saveActionCallback(self):
        fileName = QFileDialog.getSaveFileName(
            self, "Save File", self._previous_save_filename, "Lighthouse Save Files (*.lho)"
        )[0]
        file = open(fileName, "wb")
        pickle.dump(self.data.serialise(), file)
        file.close()

    def openActionCallback(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Open File", self._previous_save_filename, "Lighthouse Save Files (*.lho)"
        )[0]
        if fileName != "":
            self.data.deserialise(fileName)
            self._previous_save_filename = fileName

    def psnActionCallback(self, s):
        print(self.data.getHomographyPoints())
        return
        # Euclidean Coordinates of the tracker current position.
        # Positive x is right, positive y is up and Positive z is depth.
        # Position is expressed in meters (m).
        pos = QVector3D(0, 0, 0)
        # Velocity is expressed in meters per second (m/s).
        # speed = QVector3D(0, 0, 0)
        speed = None
        # The tracker current X acceleration.
        # Acceleration is expressed in meters per second squared.
        # accel = QVector3D(0, 0, 0)
        accel = None
        # A vector indicating an axis around which the tracker is rotated.
        # The vector’s length is the amount of rotation in radians.
        # The orientation is absolute and not cumulated from packet to packet.
        # ori = QVector3D(0, 0, 0)
        ori = None
        # A 32-bit float representing the tracker’s validity.
        # status = 0
        status = None
        # Position of the target that the tracker is trying to reach.
        # Position is expressed in meters.
        # target_pos = QVector3D(0, 0, 0)
        target_pos = None
        # This is the number of microseconds elapsed since the PSN server
        # was started to the moment the tracker position was computed.
        # Since some trackers can be computed at different times or even
        # repeated across different frames, this timestamp is usually more accurate.
        # If this field is not present, you can simply use the packet timestamp as a fallback.
        # timestamp = 0
        timestamp = None
        self.psn_output.setTrack(0, pos, speed, accel, ori, status, target_pos, timestamp)

    def initCamera(self, id=-1):
        # TODO a bit of a crude way to achieve this.
        #   Find out how to change the camera without rebuilding the whole pipeline.

        if hasattr(self, "camera"):
            self.camera.stop()
            del self.camera
        if hasattr(self, "captureSession"):
            del self.capture_session
        if hasattr(self, "cameraVideoSink"):
            del self.camera_video_sink

        if id == -1:
            self.camera = QCamera()
        else:
            self.camera = QCamera(QMediaDevices.videoInputs()[id])

        self.capture_session.setCamera(self.camera)
        self.capture_session.setVideoSink(self.camera_video_sink)
        self.camera_video_sink.videoFrameChanged.connect(self.displayVideoFrame)
        self.camera.start()

    def cameraChangedActionCallback(self, s):
        dialog = CameraSelectDialog([c.description() for c in QMediaDevices.videoInputs()])
        if dialog.exec():
            self.initCamera(dialog.getCameraId())

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

        painter.drawEllipse(self.data.getTrack2D(0), 30, 30)

        painter.end()

        pix = QPixmap.fromImage(img)
        self.video_widget.setPixmap(pix)
        # self.videoWidget.videoSink().setVideoFrame(frame)

    def closeEvent(self, event):
        # self.frameProcessor.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec())
