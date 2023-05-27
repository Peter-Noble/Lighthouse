from typing import Tuple
from PySide6.QtCore import Signal, QPoint, Slot, QSize, Qt
from PySide6.QtGui import QMouseEvent, QResizeEvent, QPen, QBrush, QColor, QVector3D, QVector2D
from PySide6.QtWidgets import QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtMultimediaWidgets import QVideoWidget, QGraphicsVideoItem
from PySide6.QtMultimedia import QMediaCaptureSession, QCameraFormat


class VideoDisplayWidget(QGraphicsView):
    click_position = Signal(QPoint)  # screen point

    def __init__(self, parent=None):
        super().__init__()
        self.main_window = parent
        # self.h_layout = QHBoxLayout()
        # self.setLayout(self.h_layout)
        self.video_scene = QGraphicsScene()
        # self.video_view = QGraphicsView()
        self.setScene(self.video_scene)
        # self.setAttribute(Qt.WA_AcceptTouchEvents, False)
        # self.h_layout.addWidget(self.video_view)
        self.video_item = None
        self.video_resolution = QSize(1280, 720)
        self.cursors: list[Tuple[QPoint, QPoint]] = []  # ground, target

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setInteractive(False)

    def setVideoInput(self, video_input: QMediaCaptureSession) -> None:
        self.video_item = QGraphicsVideoItem()
        video_input.setVideoOutput(self.video_item)
        self.video_scene.addItem(self.video_item)

        self.setSceneRect(0, 0, 1920, 1080)

    def mapToLocalCoord(self, p: QVector2D()) -> QVector2D:
        video_res = self.video_resolution
        display_res_x = self.video_item.boundingRect().width()
        display_res_y = self.video_item.boundingRect().height()
        x = display_res_x * p.x() / float(video_res.width())
        y = display_res_y * p.y() / float(video_res.height())
        #print("Video_res:", video_res)
        #print("Display_res_xy:", display_res_x, display_res_y)
        #print("p:", p)
        #print("return:", QVector2D(x, y))
        return QVector2D(x, y)

    def addTrack(self) -> None:
        pen = QPen()
        pen.setColor(QColor(255, 0, 0))
        pen.setWidth(1)

        brush = QBrush()
        brush.setColor(QColor(0, 0, 0, 0))

        r = 30

        t = len(self.cursors)
        c: Tuple[QVector2D, QVector2D] = self.main_window.data.getTrack2D(t)
        lower = self.video_scene.addLine(c[0].x(), c[0].y(), c[1].x(), c[1].y(), pen)
        lower.setZValue(1)
        upper = self.video_scene.addEllipse(c[0].x() - r, c[0].y() - r, 2 * r, 2 * r, pen, brush)
        upper.setZValue(1)

        self.cursors.append((lower, upper))

    @Slot(int, QPoint)
    def updateTrack(self, id):
        c: Tuple[QVector2D, QVector2D] = self.main_window.data.getTrack2D(id)
        print("C", c)

        r = 30

        c0 = self.mapToLocalCoord(c[0])
        c1 = self.mapToLocalCoord(c[1])
        c1_offset = self.mapToLocalCoord(c[1] - QVector2D(r, r))
        rm = self.mapToLocalCoord(QVector2D(2 * r, 2 * r))
        self.cursors[id][0].setLine(c0.x(), c0.y(), c1.x(), c1.y())
        self.cursors[id][1].setRect(c1_offset.x(), c1_offset.y(), rm.x(), rm.y())

    def mouseToVideoRes(self, pos: QPoint) -> QPoint:
        # res = self.videoSink().videoSize()
        # res = self.originalPixmap().size()
        res = self.video_resolution
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
        print("Mouse events")
        self.click_position.emit(self.mouseToVideoRes(event.pos()))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        print("Mouse event")
        self.click_position.emit(self.mouseToVideoRes(event.pos()))

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        pass

    def fitView(self) -> None:
        self.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.setSceneRect(self.video_item.boundingRect())

    @Slot(QCameraFormat)
    def formatChange(self, format: QCameraFormat) -> None:
        self.video_resolution = format.resolution()
        self.fitView()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitView()
