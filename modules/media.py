import math
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QSize, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QBrush, QPainterPath, QIcon, QRadialGradient, QLinearGradient
from core.modules import BaseModule

class LavaLampWidget(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.blobs = []
        for _ in range(3):
            self.blobs.append({
                'pos': QPointF(random.random()*100, random.random()*100),
                'vel': QPointF((random.random()-0.5)*2, (random.random()-0.5)*2),
                'size': 40 + random.random()*40
            })
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_blobs)
        self.timer.start(50)

    def update_blobs(self):
        for b in self.blobs:
            b['pos'] += b['vel']
            if b['pos'].x() < 0 or b['pos'].x() > 100: b['vel'].setX(-b['vel'].x())
            if b['pos'].y() < 0 or b['pos'].y() > 100: b['vel'].setY(-b['vel'].y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = self.theme_manager.colors
        acc = QColor(c['accent'])
        
        painter.setBrush(QColor(c['card']).lighter(110))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        
        for b in self.blobs:
            center = QPointF(self.width() * (b['pos'].x()/100), self.height() * (b['pos'].y()/100))
            grad = QRadialGradient(center, b['size'])
            color = QColor(acc)
            color.setAlpha(80)
            grad.setColorAt(0, color)
            grad.setColorAt(1, Qt.GlobalColor.transparent)
            painter.setBrush(grad)
            painter.drawEllipse(center, b['size'], b['size'])

class ProgressRingWidget(QWidget):
    seekRequested = pyqtSignal(float)             

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedSize(140, 140)
        self.progress = 0.0
        self.pixmap = None
        self.ring_width = 4
        self.offset = 12
        self.is_seeking = False
        self.nub_radius = 6
        
        self.lava_lamp = LavaLampWidget(theme_manager, self)
        self.lava_lamp.setGeometry(32, 32, 76, 76)                       
        self.lava_lamp.hide()

    def set_progress(self, progress):
        if not self.is_seeking:
            self.progress = max(0, min(1, progress))
            self.update()

    def set_pixmap(self, bytes_data):
        if bytes_data:
            p = QPixmap()
            if p.loadFromData(bytes_data):
                self.pixmap = p.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self.lava_lamp.hide()
            else:
                self.pixmap = None
                self.lava_lamp.show()
        else:
            self.pixmap = None
            self.lava_lamp.show()
        self.update()

    def get_progress_from_pos(self, pos):
        center = QPointF(self.width() / 2, self.height() / 2)
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        angle = math.degrees(math.atan2(dy, dx))
        angle = (angle + 90) % 360
        if angle < 0: angle += 360
        return angle / 360.0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dist = math.sqrt((event.position().x() - self.width()/2)**2 + (event.position().y() - self.height()/2)**2)
            ring_radius = (self.width() - 10) / 2
            if abs(dist - ring_radius) < 20:
                self.is_seeking = True
                self.update_seek(event.position())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_seeking:
            self.update_seek(event.position())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_seeking:
            self.is_seeking = False
                                                    
            self.seekRequested.emit(self.progress)
        super().mouseReleaseEvent(event)

    def update_seek(self, pos):
        self.progress = self.get_progress_from_pos(pos)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        accent_color = QColor(c['accent'])
        rect = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        center = rect.center()
        radius = rect.width() / 2
        
        painter.setPen(QPen(QColor(c['card']).darker(110), self.ring_width))
        painter.drawEllipse(rect)
        
        progress_pen = QPen(accent_color if not self.is_seeking else QColor("#FFFFFF"), self.ring_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, -int(self.progress * 360 * 16))
        
        angle_rad = math.radians(self.progress * 360 - 90)
        nx = center.x() + radius * math.cos(angle_rad)
        ny = center.y() + radius * math.sin(angle_rad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPointF(nx, ny), self.nub_radius, self.nub_radius)
        
        if self.pixmap:
            inner_radius = radius - self.offset
            inner_rect = QRectF(center.x() - inner_radius, center.y() - inner_radius, inner_radius * 2, inner_radius * 2)
            path = QPainterPath(); path.addEllipse(inner_rect)
            painter.setClipPath(path)
            painter.drawPixmap(inner_rect.toRect(), self.pixmap)

class IconButton(QPushButton):
    def __init__(self, icon_type, theme_manager, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type; self.theme_manager = theme_manager
        self.setFixedSize(40, 40); self.is_hovered = False
        self.setStyleSheet("background: transparent; border: none;")
    def enterEvent(self, event): self.is_hovered = True; self.update()
    def leaveEvent(self, event): self.is_hovered = False; self.update()
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        color = QColor(c['accent']) if self.is_hovered else QColor(c['text'])
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(color)
        w, h = self.width(), self.height(); path = QPainterPath()
        if self.icon_type == "play":
            path.moveTo(w*0.35, h*0.25); path.lineTo(w*0.75, h*0.5); path.lineTo(w*0.35, h*0.75); path.closeSubpath()
        elif self.icon_type == "pause":
            path.addRoundedRect(w*0.3, h*0.25, w*0.15, h*0.5, 2, 2)
            path.addRoundedRect(w*0.55, h*0.25, w*0.15, h*0.5, 2, 2)
        elif self.icon_type == "next":
            path.moveTo(w*0.2, h*0.3); path.lineTo(w*0.5, h*0.5); path.lineTo(w*0.2, h*0.7); path.closeSubpath()
            path.moveTo(w*0.5, h*0.3); path.lineTo(w*0.8, h*0.5); path.lineTo(w*0.5, h*0.7); path.closeSubpath()
        elif self.icon_type == "prev":
            path.moveTo(w*0.8, h*0.3); path.lineTo(w*0.5, h*0.5); path.lineTo(w*0.8, h*0.7); path.closeSubpath()
            path.moveTo(w*0.5, h*0.3); path.lineTo(w*0.2, h*0.5); path.lineTo(w*0.5, h*0.7); path.closeSubpath()
        painter.drawPath(path)

class MediaModule(BaseModule):
    def __init__(self, media_manager, theme_manager, parent=None):
        self.media_manager = media_manager; self.theme_manager = theme_manager
        self.duration_ms = 0; super().__init__(parent)
        self.media_manager.metadataChanged.connect(self.on_metadata_changed)
        self.media_manager.positionChanged.connect(self.on_position_changed)
        self.media_manager.statusChanged.connect(self.on_status_changed)

    def setup_ui(self):
        self.layout.setSpacing(10)
        self.ring = ProgressRingWidget(self.theme_manager)
        self.ring.seekRequested.connect(self.on_seek_requested)
        ring_container = QHBoxLayout(); ring_container.addStretch(); ring_container.addWidget(self.ring); ring_container.addStretch()
        self.layout.addLayout(ring_container)
        self.title_label = QLabel("Not Playing")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.artist_label = QLabel("")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.artist_label.setStyleSheet("font-size: 11px; opacity: 0.7;")
        self.layout.addWidget(self.title_label); self.layout.addWidget(self.artist_label)
        cl = QHBoxLayout(); self.btn_prev = IconButton("prev", self.theme_manager); self.btn_play = IconButton("play", self.theme_manager); self.btn_next = IconButton("next", self.theme_manager)
        cl.addStretch(); cl.addWidget(self.btn_prev); cl.addWidget(self.btn_play); cl.addWidget(self.btn_next); cl.addStretch()
        self.layout.addLayout(cl)
        self.btn_play.clicked.connect(self.media_manager.play_pause); self.btn_next.clicked.connect(self.media_manager.next_track); self.btn_prev.clicked.connect(self.media_manager.prev_track)

    def on_seek_requested(self, percentage):
        if self.duration_ms > 0: self.media_manager.seek_to(int(percentage * self.duration_ms))
    def on_metadata_changed(self, info):
        if not info:
            self.title_label.setText("Not Playing"); self.artist_label.setText(""); self.ring.set_pixmap(None)
            return
        self.title_label.setText(info.get('title', 'Unknown')); self.artist_label.setText(info.get('artist', ''))
        self.ring.set_pixmap(info.get('art_bytes'))
    def on_position_changed(self, pos, dur):
        self.duration_ms = dur
        if dur > 0: self.ring.set_progress(pos / dur)
    def on_status_changed(self, is_playing):
        self.btn_play.icon_type = "pause" if is_playing else "play"; self.btn_play.update()
    def update_content(self): pass
