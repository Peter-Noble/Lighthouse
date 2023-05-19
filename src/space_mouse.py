import pyspacemouse
from PySide6.QtCore import Slot, QObject, QTimer, Signal, QPoint, Qt
from PySide6.QtGui import QVector3D, QVector2D

import math


class SpaceMouse(QObject):
    cursor_moved = Signal(QPoint)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pos = QVector2D(0, 0)

        self.active = False
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
        return 3 * x**3 + math.copysign(3 * x**2, x) + 1 * x

    def update(self):
        if self.device and self.parent().geometry_settings_dock.use_space_mouse.checkState() is Qt.CheckState.Checked:
            state = self.device.read()
            if state:
                if not self.active:
                    self.active = True
                    self.device.set_led(1)
                self.roll = state.roll
                self.pitch = state.pitch
                self.x = state.x
                self.y = state.y
            self.pos = self.pos + QVector2D(
                self.moveCurve(self.roll) + self.x * 2, -self.moveCurve(self.pitch) - self.y * 2
            )
            res = self.parent().video_widget.originalPixmap().size()
            self.pos.setX(max(0, min(self.pos.x(), res.width())))
            self.pos.setY(max(0, min(self.pos.y(), res.height())))
            self.cursor_moved.emit(QPoint(self.pos.x(), self.pos.y()))
        else:
            if self.active:
                self.active = False
                self.device.set_led(0)

    def cleanup(self):
        self.device.set_led(0)
        self.device.close()
