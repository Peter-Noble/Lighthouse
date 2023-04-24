import sys

from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtMultimediaWidgets import QVideoWidget

app = QApplication(sys.argv)

# videoWidget = QVideoWidget()
videoWidget = QLabel()
videoWidget.show()

sys.exit(app.exec())