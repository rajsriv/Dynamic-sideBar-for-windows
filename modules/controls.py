import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen
from core.modules import BaseModule

class ControlItem(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, icon_type, theme_manager, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.theme_manager = theme_manager
        self.value = 0
        self.is_dragging = False
        self.setFixedHeight(50) # Increased height for two-line layout
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def set_value(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def update_from_mouse(self, x):
        # Full width slider logic
        padding = 10
        usable_width = self.width() - 2 * padding
        if x < padding:
            self.set_value(0)
            self.valueChanged.emit(0)
        elif x > self.width() - padding:
            self.set_value(100)
            self.valueChanged.emit(100)
        else:
            new_val = int((x - padding) / usable_width * 100)
            self.set_value(new_val)
            self.valueChanged.emit(self.value)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.update_from_mouse(event.position().x())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update_from_mouse(event.position().x())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = self.theme_manager.colors
        accent = QColor(c['accent'])
        text_color = QColor(c['text'])
        
        # 1. Draw Icon (Top Row)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        
        path = QPainterPath()
        icon_size = 20
        off_x, off_y = 5, 5
        
        if self.icon_type == "brightness":
            cx, cy = off_x + icon_size/2, off_y + icon_size/2
            path.addEllipse(cx - 4, cy - 4, 8, 8)
            path.addRect(cx - 1, off_y, 2, 3) 
            path.addRect(cx - 1, off_y + icon_size - 3, 2, 3)
            path.addRect(off_x, cy - 1, 3, 2)
            path.addRect(off_x + icon_size - 3, cy - 1, 3, 2)
            # Add diagonals for better sun look
            path.addRect(cx - 6, cy - 6, 2, 2) # simplified diagonal
        else: # Volume
            # Speaker icon
            path.addRect(off_x + 2, off_y + 6, 4, 8) # Body
            path.moveTo(off_x + 6, off_y + 6); path.lineTo(off_x + 12, off_y + 2); path.lineTo(off_x + 12, off_y + 18); path.lineTo(off_x + 6, off_y + 14); path.closeSubpath() # Cone
            if self.value > 0:
                path.addRect(off_x + 14, off_y + 8, 2, 4)
            if self.value > 50:
                path.addRect(off_x + 18, off_y + 5, 2, 10)
            
        painter.drawPath(path)
        
        # 2. Draw Percentage Text (Top Row)
        painter.setPen(text_color)
        painter.setFont(self.font())
        painter.drawText(off_x + icon_size + 10, off_y, 60, icon_size, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{int(self.value)}%")
        
        # 3. Draw Slider Bar (Bottom Row)
        padding = 10
        bar_height = 8
        bar_y = 32
        bar_width = self.width() - 2 * padding
        
        # Bar background
        painter.setBrush(QColor(c['card']).darker(110))
        bar_rect_bg = QRectF(padding, bar_y, bar_width, bar_height)
        painter.drawRoundedRect(bar_rect_bg, bar_height/2, bar_height/2)
        
        # Bar value
        painter.setBrush(accent)
        bar_rect_val = QRectF(padding, bar_y, bar_width * (self.value/100), bar_height)
        painter.drawRoundedRect(bar_rect_val, bar_height/2, bar_height/2)
        
        # Knob
        if self.is_dragging:
            painter.setBrush(QColor("#FFFFFF"))
            knob_x = padding + bar_width * (self.value/100)
            painter.drawEllipse(QRectF(knob_x - 6, bar_y + bar_height/2 - 6, 12, 12))

class ControlModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        self._volume_interface = None
        self._init_volume()
        super().__init__(parent)
        self.theme_manager.themeChanged.connect(self.update_style)

    def _init_volume(self):
        try:
            # FIX: Use GetSpeakers().EndpointVolume directly
            devices = AudioUtilities.GetSpeakers()
            self._volume_interface = devices.EndpointVolume
        except Exception as e:
            print(f"Volume Init Error: {e}")

    def setup_ui(self):
        self.layout.setSpacing(10)
        self.brightness_item = ControlItem("brightness", self.theme_manager)
        self.volume_item = ControlItem("volume", self.theme_manager)
        
        self.layout.addWidget(self.brightness_item)
        self.layout.addWidget(self.volume_item)

        self.brightness_item.valueChanged.connect(self.set_brightness)
        self.volume_item.valueChanged.connect(self.set_volume)

    def set_brightness(self, val):
        try:
            sbc.set_brightness(val)
        except: pass

    def set_volume(self, val):
        if self._volume_interface:
            try:
                # SetMasterVolumeLevelScalar takes 0.0 to 1.0
                self._volume_interface.SetMasterVolumeLevelScalar(val / 100.0, None)
            except: pass

    def update_style(self):
        self.update()

    def update_content(self):
        # Update Brightness UI
        try:
            b = sbc.get_brightness()
            if b:
                current_b = b[0] if isinstance(b, list) else b
                if not self.brightness_item.is_dragging:
                    self.brightness_item.set_value(current_b)
        except: pass

        # Update Volume UI
        if self._volume_interface:
            try:
                current_v = self._volume_interface.GetMasterVolumeLevelScalar() * 100
                if not self.volume_item.is_dragging:
                    self.volume_item.set_value(current_v)
            except: pass
