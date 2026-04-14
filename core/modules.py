from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import QTimer

class BaseModule(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModuleCard")
        self.setProperty("class", "ModuleCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_content)
        self.timer.start(1000)

    def setup_ui(self):
                                     
        pass

    def update_content(self):
                                        
        pass
