import sys
import random
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMenu, QInputDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QTimer, QSize, QEvent, QPointF
from PyQt6.QtGui import QAction, QCursor, QPainter, QColor, QPainterPath, QPen, QRadialGradient
from .theme_manager import ThemeManager

class LavaLampBackground(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.blobs = []
        for _ in range(5):
            self.blobs.append({
                'pos': QPointF(random.random()*100, random.random()*100),
                'vel': QPointF((random.random()-0.5)*0.2, (random.random()-0.5)*0.2),
                'size': 120 + random.random()*80
            })
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_blobs)
        self.timer.start(50)

    def update_blobs(self):
        if not self.isVisible(): return
        for b in self.blobs:
            b['pos'] += b['vel']
            if b['pos'].x() < -20 or b['pos'].x() > 120: b['vel'].setX(-b['vel'].x())
            if b['pos'].y() < -20 or b['pos'].y() > 120: b['vel'].setY(-b['vel'].y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = self.theme_manager.colors
        blob_color = QColor(c['blob'])
        
        for b in self.blobs:
            center = QPointF(self.width() * (b['pos'].x()/100), self.height() * (b['pos'].y()/100))
            grad = QRadialGradient(center, b['size'])
            
            color = QColor(blob_color)
            color.setAlpha(60)              
            grad.setColorAt(0, color)
            grad.setColorAt(1, Qt.GlobalColor.transparent)
            
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, b['size'], b['size'])

class HandleButton(QPushButton):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedSize(32, 32)
        self.setObjectName("HandleButton")
        self.is_flipped = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dragging = False
        self._drag_start_x = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c['handle_bg']))
        painter.drawEllipse(self.rect())
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath()
        w, h = self.width(), self.height()
        if not self.is_flipped:
            path.moveTo(w*0.6, h*0.35); path.lineTo(w*0.4, h*0.5); path.lineTo(w*0.6, h*0.65)
        else:
            path.moveTo(w*0.4, h*0.35); path.lineTo(w*0.6, h*0.5); path.lineTo(w*0.4, h*0.65)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start_x = event.globalPosition().x()
            self.window()._start_window_x = self.window().x()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta_x = event.globalPosition().x() - self._drag_start_x
            self.window().handle_drag(delta_x)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self.window().handle_release()
        super().mouseReleaseEvent(event)

class Sidebar(QMainWindow):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        
        self.sidebar_width = self.theme_manager.sidebar_width
        self.handle_width = 45 
        self.margin = self.theme_manager.window_margin
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.update_style()
        
        self.is_expanded = False
        self._start_window_x = 0
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        QTimer.singleShot(100, self.init_geometry)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_mouse_pos)
        self.check_timer.start(100)
        
        self.theme_manager.themeChanged.connect(self.update_style)

    def init_geometry(self):
        screen = self.screen()
        geom = screen.availableGeometry()
        self.bar_height = geom.height() - (2 * self.margin)
        self.y_pos = geom.top() + self.margin
        self.abs_right_edge = geom.right()
        self.floating_right_edge = geom.right() - self.margin
        
        self.master_container.setFixedHeight(self.bar_height)
        self.sidebar_panel.setFixedHeight(self.bar_height)
        self.lava_bg.setGeometry(0, 0, self.sidebar_width, self.bar_height)
        
        self.collapse(animate=False)

    def setup_ui(self):
        self.master_container = QWidget()
        self.setCentralWidget(self.master_container)
        self.master_layout = QHBoxLayout(self.master_container)
        self.master_layout.setContentsMargins(0, 0, 0, 0)
        self.master_layout.setSpacing(0)
        
        self.handle_container = QWidget()
        self.handle_container.setFixedWidth(self.handle_width)
        self.handle_layout = QVBoxLayout(self.handle_container)
        self.handle_layout.setContentsMargins(5, 0, 0, 0)
        self.handle_btn = HandleButton(self.theme_manager, self.handle_container)
        self.handle_layout.addStretch(); self.handle_layout.addWidget(self.handle_btn); self.handle_layout.addStretch()
        
        self.sidebar_panel = QWidget()
        self.sidebar_panel.setObjectName("SidebarContainer")
        self.sidebar_panel.setFixedWidth(self.sidebar_width)
        
        self.lava_bg = LavaLampBackground(self.theme_manager, self.sidebar_panel)
        self.lava_bg.lower()                            
        
        self.main_layout = QVBoxLayout(self.sidebar_panel)
        self.main_layout.setContentsMargins(15, 30, 15, 30)
        self.main_layout.setSpacing(15)
        
        self.title_label = QLabel(f"Hi, {self.theme_manager.user_name} !")
        self.title_label.setObjectName("Title")
        self.main_layout.addWidget(self.title_label)
        
        self.master_layout.addWidget(self.handle_container)
        self.master_layout.addWidget(self.sidebar_panel)
        self.sidebar_panel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar_panel.customContextMenuRequested.connect(self.show_context_menu)

    def update_style(self):
        self.setStyleSheet(self.theme_manager.get_qss())
        self.title_label.setText(f"Hi, {self.theme_manager.user_name} !")
                                
        self.lava_bg.setVisible(self.theme_manager.is_aura)
        if self.theme_manager.is_aura:
            self.lava_bg.timer.start()
        else:
            self.lava_bg.timer.stop()

    def handle_drag(self, delta_x):
        new_x = self._start_window_x + delta_x
        limit = self.abs_right_edge - self.handle_width
        if new_x > limit: new_x = limit
        self.move(int(new_x), self.y_pos)

    def handle_release(self):
        collapsed_x = self.abs_right_edge - self.handle_width
        if self.x() < (collapsed_x - 50): self.expand()
        else: self.collapse()

    def check_mouse_pos(self):
        if self.is_expanded and not self.handle_btn._dragging:
            if not self.geometry().contains(QCursor.pos()) and not self.isActiveWindow():
                self.collapse()

    def expand(self):
        if self.animation.state() == QPropertyAnimation.State.Running: self.animation.stop()
        self.is_expanded = True
        self.handle_btn.is_flipped = True
        self.handle_btn.update()
        tw = self.sidebar_width + self.handle_width
        end_rect = QRect(int(self.floating_right_edge - tw), self.y_pos, tw, self.bar_height)
        self.animation.setStartValue(self.geometry()); self.animation.setEndValue(end_rect); self.animation.start()
        self.activateWindow()

    def collapse(self, animate=True):
        if self.animation.state() == QPropertyAnimation.State.Running: self.animation.stop()
        self.is_expanded = False
        self.handle_btn.is_flipped = False
        self.handle_btn.update()
        tw = self.sidebar_width + self.handle_width
        end_rect = QRect(int(self.abs_right_edge - self.handle_width), self.y_pos, tw, self.bar_height)
        if animate:
            self.animation.setStartValue(self.geometry()); self.animation.setEndValue(end_rect); self.animation.start()
        else: self.setGeometry(end_rect)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {self.theme_manager.colors['bg']}; color: {self.theme_manager.colors['text']}; border: 1px solid {self.theme_manager.colors['accent']}; border-radius: 6px; padding: 5px; }} QMenu::item:selected {{ background: {self.theme_manager.colors['accent']}; color: white; }}")
        
        change_name = menu.addAction("Change Name")
        menu.addSeparator()
        
        menu.addAction("System").triggered.connect(lambda: self.theme_manager.set_mode('system'))
        menu.addAction("Day").triggered.connect(lambda: self.theme_manager.set_mode('day'))
        menu.addAction("Dark").triggered.connect(lambda: self.theme_manager.set_mode('dark'))
        menu.addAction("Day Aura").triggered.connect(lambda: self.theme_manager.set_mode('day_aura'))
        menu.addAction("Dark Aura").triggered.connect(lambda: self.theme_manager.set_mode('dark_aura'))
        
        menu.addSeparator()
        
        autostart_action = menu.addAction("Launch at Startup")
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.theme_manager.autostart)
        autostart_action.triggered.connect(lambda checked: setattr(self.theme_manager, 'autostart', checked))
        
        menu.addSeparator()
        exit_app = menu.addAction("Exit App")
        
        action = menu.exec(self.sidebar_panel.mapToGlobal(pos))
        if action == change_name:
            name, ok = QInputDialog.getText(self, "Update Greeting", "Enter your name:", text=self.theme_manager.user_name)
            if ok and name: 
                self.theme_manager.user_name = name
                self.theme_manager.save_settings()                
        elif action == exit_app: sys.exit()
