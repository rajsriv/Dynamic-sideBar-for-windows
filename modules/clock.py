# Creator : github.com/rajsriv
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTime, QDate, Qt
from core.modules import BaseModule

class ClockModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        super().__init__(parent)

    def setup_ui(self):
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 56px; font-weight: 200; letter-spacing: -2px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 16px; font-weight: 500; opacity: 0.7;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.date_label)
        self.update_content()

    def update_content(self):
        current_time = QTime.currentTime().toString("HH:mm")
        current_date = QDate.currentDate().toString("dddd, MMMM d")
        self.time_label.setText(current_time)
        self.date_label.setText(current_date)
