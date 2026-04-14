import psutil
from PyQt6.QtWidgets import QLabel, QProgressBar, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath
from core.modules import BaseModule

class StatItem(QWidget):
    def __init__(self, icon_type, theme_manager, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.theme_manager = theme_manager
        self.value = 0
        self.setFixedHeight(35)
        
    def set_value(self, val):
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = self.theme_manager.colors
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c['accent']))
        
        path = QPainterPath()
        w, h = 24, 24                    
        if self.icon_type == "cpu":
                              
            path.addRoundedRect(2, 2, 20, 20, 4, 4)
            path.addRect(10, 0, 4, 2); path.addRect(10, 22, 4, 2)
        else:      
                               
            path.addRoundedRect(4, 2, 16, 20, 2, 2)
            path.addRect(4, 6, 4, 2); path.addRect(4, 12, 4, 2)
            
        painter.drawPath(path)
        
        painter.setPen(QColor(c['text']))
        painter.setFont(self.font())
        painter.drawText(30, 0, 60, self.height(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{int(self.value)}%")
        
        painter.setBrush(QColor(c['card']).darker(110))
        bar_rect_bg = QRectF(100, self.height()/2 - 2, 80, 4)
        painter.drawRoundedRect(bar_rect_bg, 2, 2)
        
        painter.setBrush(QColor(c['accent']))
        bar_rect_val = QRectF(100, self.height()/2 - 2, 80 * (self.value/100), 4)
        painter.drawRoundedRect(bar_rect_val, 2, 2)

class SystemStatModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        super().__init__(parent)
        self.theme_manager.themeChanged.connect(self.update_style)

    def setup_ui(self):
        self.layout.setSpacing(5)
        self.cpu_item = StatItem("cpu", self.theme_manager)
        self.ram_item = StatItem("ram", self.theme_manager)
        
        self.layout.addWidget(self.cpu_item)
        self.layout.addWidget(self.ram_item)

    def update_style(self):
        self.update()

    def update_content(self):
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        self.cpu_item.set_value(cpu_usage)
        self.ram_item.set_value(ram_usage)
