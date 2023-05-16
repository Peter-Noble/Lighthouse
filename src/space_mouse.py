import pyspacemouse
from PySide6.QtCore import Slot, QObject, QTimer, Signal, QPoint, Qt
from PySide6.QtGui import QVector3D, QVector2D


class SpaceMouse(QObject):
    cursor_moved = Signal(QPoint)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pos = QVector2D(0, 0)

        self.device = pyspacemouse.open()

        self.roll = 0
        self.pitch = 0
        self.x = 0
        self.y = 0

        if self.device:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update)
            update_frequency = 60
            self.timer.start(1000 / update_frequency)

    def moveCurve(self, x):
        return 6 * x**3 + 1 * x

    def update(self):
        if self.device and self.parent().settings_dock.use_space_mouse.checkState() is Qt.CheckState.Checked:
            state = self.device.read()
            if state:
                self.roll = state.roll
                self.pitch = state.pitch
                self.x = state.x
                self.y = state.y

                # state.x
                # state.y
                # state.z
                # state.roll
                # state.pitch
                # state.yaw
                # state.t
            # if abs(self.roll) > 0.0 and abs(self.pitch) > 0.0:
            self.pos = self.pos + QVector2D(
                self.moveCurve(self.roll) + self.x * 2, -self.moveCurve(self.pitch) - self.y * 2
            )
            res = self.parent().video_widget.originalPixmap().size()
            self.pos.setX(max(0, min(self.pos.x(), res.width())))
            self.pos.setY(max(0, min(self.pos.y(), res.height())))
            self.cursor_moved.emit(QPoint(self.pos.x(), self.pos.y()))
            # print(self.pos)
            # print(
            #     " ".join(["%4s %+.2f" % (k, getattr(state, k)) for k in ["x", "y", "z", "roll", "pitch", "yaw", "t"]])
            # )
