# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import*
from PyQt5.QtMultimediaWidgets import QVideoWidget
    
class VideoWidget(QVideoWidget):
    def __init__(self, parent = None):
        QVideoWidget.__init__(self, parent)