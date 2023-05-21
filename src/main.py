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
    QDialogButtonBox,
    QLabel,
    QDialog,
)

from camera_select_dialog import CameraSelectDialog
from geometry_settings_dock import GeometrySettingsDock
from fixture_settings_dock import FixtureSettingsDock
from track_settings_dock import TrackSettingsDock
from video_display_widget import VideoDisplayWidget
from data_store import DataStore
from psn_output import PSNOutput
from space_mouse import SpaceMouse, createAllSpaceMice
from network_settings import NetworkSettings

from dev_status import is_release


class ConfirmExitDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Exit?")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox()
        ok_btn = self.buttonBox.addButton("Ok", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = self.buttonBox.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)

        ok_btn.setAutoDefault(False)
        ok_btn.setDefault(False)

        cancel_btn.setAutoDefault(True)
        cancel_btn.setDefault(True)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Are you sure you want to exit?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class App(QMainWindow):
    def __init__(self):
        print("[startup] Creating the main window")
        super().__init__()
        self.setWindowTitle("Lighthouse")
        self.resize(800, 400)

        # self.setWindowFlags(Qt.FramelessWindowHint)

        print("[startup] Creating the data store")
        self.data = DataStore()
        self.data.setParent(self)

        self._previous_save_filename = str((self.data.src_folder / "showfile.lho").absolute())

        print("[startup] Creating central widget and layout")
        vbox = QVBoxLayout()
        central = QWidget()
        central.setLayout(vbox)
        self.setCentralWidget(central)

        print("[startup] Creating video display")
        self.video_widget = VideoDisplayWidget()
        vbox.addWidget(self.video_widget)

        print("[startup] Creating camera")
        self.camera = QCamera()
        print("[startup] Creating capture session")
        self.capture_session = QMediaCaptureSession()
        print("[startup] Creating video sink")
        self.camera_video_sink = QVideoSink()

        print("[startup] Setting capture session camera")
        self.capture_session.setCamera(self.camera)
        print("[startup] Setting capture session video sink")
        self.capture_session.setVideoSink(self.camera_video_sink)
        print("[startup] Attaching new frame callback")
        self.camera_video_sink.videoFrameChanged.connect(self.displayVideoFrame)

        print("[startup] Starting camera")
        self.camera.start()

        print("[startup] Creating settings docks and windows")
        self.network_settings = NetworkSettings()

        self.geometry_settings_dock = GeometrySettingsDock(parent=self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.geometry_settings_dock)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.RightDockWidgetArea)
        self.fixture_settings_dock = FixtureSettingsDock(parent=self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.fixture_settings_dock)
        self.track_settings_dock = TrackSettingsDock(parent=self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.track_settings_dock)

        print("[startup] Creating action bar")
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

        self.change_camera_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-documentary-64.png").absolute())),
            "&Change Camera",
            self,
        )
        self.change_camera_action.triggered.connect(self.cameraChangedActionCallback)

        self.network_settings_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-network-64.png").absolute())), "&Network", self
        )
        self.network_settings_action.triggered.connect(self.network_settings.show)

        self.geometry_settings_action = QAction(
            self.geometry_settings_dock.icon,
            "&Geometry settings",
            self,
        )
        self.geometry_settings_action.triggered.connect(self.toggleGeometrySettings)

        self.fixture_settings_action = QAction(
            self.fixture_settings_dock.icon,
            "&Fixture settings",
            self,
        )
        self.fixture_settings_action.triggered.connect(self.toggleFixtureSettings)

        self.track_settings_action = QAction(
            self.track_settings_dock.icon,
            "&Track Settings",
            self,
        )
        self.track_settings_action.triggered.connect(self.toggleTrackSettings)

        self.exit_action = QAction(
            QIcon(str((self.data.src_folder / "images/icons/icons8-cancel-64.png").absolute())), "&Exit", self
        )
        self.exit_action.triggered.connect(self.exitActionCallback)

        file_tool_bar = self.addToolBar("File")
        file_tool_bar.addAction(self.lighthouse_action)
        file_tool_bar.addAction(self.new_action)
        file_tool_bar.addAction(self.save_action)
        file_tool_bar.addAction(self.open_action)
        file_tool_bar.addAction(self.change_camera_action)
        file_tool_bar.addAction(self.fixture_settings_action)
        file_tool_bar.addAction(self.track_settings_action)
        file_tool_bar.addAction(self.geometry_settings_action)
        file_tool_bar.addAction(self.network_settings_action)
        file_tool_bar.addAction(self.exit_action)
        file_tool_bar.setMovable(False)

        print("[startup] Connecting slots and signals")

        self.geometry_settings_dock.height_offset.doubleValueChanged.connect(self.data.setHeightOffset)

        self.data.track_changed.connect(self.geometry_settings_dock.updateTrack)
        self.data.homography_points_changed.connect(self.geometry_settings_dock.updateHomographyPoints)

        self.video_widget.click_position.connect(self.data.setHomographyScreenPoint)
        self.video_widget.click_position.connect(self.data.setTrack0)

        self.geometry_settings_dock.addNewHomographyPoint.connect(self.data.addNewHomographyPoint)
        self.geometry_settings_dock.editHomographyPoint.connect(self.data.setHomographyPoint)
        self.geometry_settings_dock.removeHomographyPoint.connect(self.data.removeHomographyPoint)

        self.data.broadcast()

        print("[startup] Setting up PSN")
        self.psn_output = PSNOutput()
        self.psn_output.addTrack()
        self.psn_output.addTrack()
        self.data.track_changed.connect(self.psn_output.setTrackWithPos)

        print("[startup] Setting up SpaceMouse")
        try:
            self.space_mice = createAllSpaceMice(self)
            for mouse in self.space_mice:
                mouse.watcher.cursor_moved.connect(self.data.setTrack)
        except AttributeError:
            print("[Error] No 3d input device found")

    def exitActionCallback(self, s):
        self.close()

    def toggleGeometrySettings(self):
        if self.geometry_settings_dock.isHidden():
            self.geometry_settings_dock.show()
        else:
            self.geometry_settings_dock.hide()

    def toggleFixtureSettings(self):
        if self.fixture_settings_dock.isHidden():
            self.fixture_settings_dock.show()
        else:
            self.fixture_settings_dock.hide()

    def toggleTrackSettings(self):
        if self.track_settings_dock.isHidden():
            self.track_settings_dock.show()
        else:
            self.track_settings_dock.hide()

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

        for t in range(self.data.getNumTracks()):
            painter.drawEllipse(self.data.getTrack2D(t), 30, 30)

        painter.end()

        pix = QPixmap.fromImage(img)
        self.video_widget.setPixmap(pix)
        # self.videoWidget.videoSink().setVideoFrame(frame)

    def cleanup(self):
        self.network_settings.close()
        self.space_mouse.cleanup()

    def closeEvent(self, event):
        if is_release:
            if ConfirmExitDialog().exec():
                super().closeEvent(event)
                self.cleanup()
            else:
                event.ignore()
        else:
            super().closeEvent(event)
            self.cleanup()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    app.setWindowIcon(QIcon(str((a.data.src_folder / "images/icons/icons8-lighthouse-64.png").absolute())))

    a.show()
    sys.exit(app.exec())
