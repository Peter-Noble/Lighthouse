from araviq6 import ScalableQLabel
from PySide6.QtCore import Signal, QPoint
from PySide6.QtGui import QMouseEvent


class VideoDisplayWidget(ScalableQLabel):
    click_position = Signal(QPoint)  # screen point

    def mouseToVideoRes(self, pos: QPoint) -> QPoint:
        # TODO guard against divisions by zero
        # res = self.videoSink().videoSize()
        res = self.originalPixmap().size()
        res_asp = res.width() / res.height()
        size = self.size()
        size_asp = size.width() / size.height()
        x = max(0, min(pos.x() / size.width() * res.width(), res.width()))
        y = max(0, min(pos.y() / size.height() * res.height(), res.height()))
        if size_asp > res_asp:
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
        self.click_position.emit(self.mouseToVideoRes(event.pos()))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.click_position.emit(self.mouseToVideoRes(event.pos()))
