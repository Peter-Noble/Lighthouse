try:
    import psn

    no_psn = False
except:
    no_psn = True

import socket
import time

from PySide6.QtCore import Signal, Slot, Qt, QPoint, QObject, QTimer
from PySide6.QtGui import QVector3D

PSN_DEFAULT_UDP_PORT = 56565
PSN_DEFAULT_UDP_MULTICAST_ADDR = "236.10.10.10"
MULTICAST_TTL = 2


# Helper functions
def get_time_ms():
    return int(time.time() * 1000)


start_time = get_time_ms()


def get_elapsed_time_ms():
    return get_time_ms() - start_time


class PSNOutput(QObject):
    def __init__(self):
        super().__init__()
        if no_psn:
            print("PSN module couldn't be found")
            return
        self.encoder = psn.Encoder("Lighthouse server")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

        self.tracks = {}

        self.transmit_frequency = 60
        self.info_counter = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.send)
        self.timer.start(1000 / self.transmit_frequency)

    def addTrack(self) -> None:
        if no_psn:
            return
        self.tracks[len(self.tracks)] = psn.Tracker(
            len(self.tracks), f"Tracker {len(self.tracks)}"
        )

    @Slot(int, QVector3D)
    def setTrackWithPos(self, id: int, pos: QVector3D):
        self.setTrack(id=id, pos=QVector3D(pos.x(), pos.z(), pos.y()))

    @Slot(int, QVector3D, QVector3D, QVector3D, QVector3D, float, QVector3D, float)
    def setTrack(
        self,
        id: int,
        pos: QVector3D,
        speed: QVector3D | None = None,
        accel: QVector3D | None = None,
        ori: QVector3D | None = None,
        status: float | None = None,
        target_pos: QVector3D | None = None,
        timestamp: float | None = None,
    ) -> None:
        if no_psn:
            return
        tracker = self.tracks[id]
        tracker.set_pos(psn.Float3(pos.x(), pos.y(), pos.z()))
        if speed is not None:
            tracker.set_speed(psn.Float3(speed.x(), speed.y(), speed.z()))
        if accel is not None:
            tracker.set_accel(psn.Float3(accel.x(), accel.y(), accel.z()))
        if ori is not None:
            tracker.set_ori(psn.Float3(ori.x(), ori.y(), ori.z()))
        if status is not None:
            tracker.set_status(status)
        if target_pos is not None:
            tracker.set_target_pos(
                psn.Float3(target_pos.x(), target_pos.y(), target_pos.z())
            )
        if timestamp is not None:
            tracker.set_timestamp(timestamp)
        self.tracks[id] = tracker

    def send(self) -> None:
        if no_psn:
            return

        if len(self.tracks) == 0:
            return

        #print("Send PSN")
        # Encode
        time_stamp = get_elapsed_time_ms()
        packets = []
        if self.info_counter == 0:
            packets.extend(self.encoder.encode_info(self.tracks, time_stamp))
            self.info_counter = self.transmit_frequency
        self.info_counter -= 1
        packets.extend(self.encoder.encode_data(self.tracks, time_stamp))

        for packet in packets:
            try:
                self.sock.sendto(
                    packet, (PSN_DEFAULT_UDP_MULTICAST_ADDR, PSN_DEFAULT_UDP_PORT)
                )
            except OSError as err:
                print("PACKET SEND ERROR")
                continue
