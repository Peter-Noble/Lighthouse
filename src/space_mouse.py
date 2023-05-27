import pyspacemouse
from PySide6.QtCore import Slot, QObject, QTimer, Signal, QPoint, Qt, QThread, QSize
from PySide6.QtGui import QVector3D, QVector2D

import math
import time


class SpaceMouseWatcher(QThread):
    cursor_moved = Signal(int, QPoint)  # Mouse ID, point

    def __init__(self, device, id: int, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.device = device
        self.id = id

        self.pos = QVector2D(0, 0)

        self.roll = 0
        self.pitch = 0
        self.x = 0
        self.y = 0
        self.t = None

        self.last_update_t = None
        self.last_emit_change = 0

    def run(self):
        self.device.set_led(1)

        while not self.exiting:
            state = self.device.read()
            current_time = time.time()
            if state:
                self.t = state.t
                self.roll = state.roll
                self.pitch = state.pitch
                self.x = state.x
                self.y = state.y

            if self.t is not None and self.last_update_t is None:
                self.last_update_t = current_time

            if self.t is not None and self.last_update_t is not None:
                update_t_diff = current_time - self.last_update_t
                self.last_update_t = current_time

                emit_t_diff = current_time - self.last_emit_change

                self.pos = self.pos + QVector2D(
                    (self.moveCurve(self.roll) + self.x * 2) * update_t_diff * 100,
                    (-self.moveCurve(self.pitch) - self.y * 2) * update_t_diff * 100,
                )
                # res: QSize = self.parent().parent().video_widget.originalPixmap().size()
                res: QSize = self.parent().parent().video_widget.video_resolution
                self.pos.setX(max(0, min(self.pos.x(), res.width())))
                self.pos.setY(max(0, min(self.pos.y(), res.height())))

                if emit_t_diff >= 1 / 60:
                    self.last_emit_change = current_time
                    self.cursor_moved.emit(self.id, QPoint(self.pos.x(), self.pos.y()))
            time.sleep(0.001)
        self.device.set_led(0)
        self.device.close()

    def moveCurve(self, x):
        return 3 * x**3 + math.copysign(3 * x**2, x) + 1 * x


class SpaceMouse(QObject):
    def __init__(self, device, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False
        self.watcher = SpaceMouseWatcher(device, id, parent=self)
        self.watcher.start()

    def cleanup(self):
        self.watcher.exiting = True
        self.watcher.wait()


def createAllSpaceMice(parent) -> list[SpaceMouse]:
    devices = pyspacemouse.open_all()
    result = []

    if all([device for device in devices]):
        for i, device in enumerate(devices):
            device.set_led(0)
            result.append(SpaceMouse(device, i, parent=parent))

    return result
