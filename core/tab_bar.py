# Creator : github.com/rajsriv
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, pyqtSignal, pyqtProperty, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont


class TabButton(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, text, index, theme_manager, parent=None):
        super().__init__(parent)
        self.text = text
        self.index = index
        self.theme_manager = theme_manager
        self.is_active = False
        self._hover = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors

        if self.is_active:
            color = QColor(c['accent'])
        elif self._hover:
            color = QColor(c['text'])
            color.setAlpha(200)
        else:
            color = QColor(c['text_dim'])

        font = QFont("Segoe UI Variable", 11)
        font.setWeight(QFont.Weight.Bold if self.is_active else QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)


class TabBar(QWidget):
    tabChanged = pyqtSignal(int)

    def __init__(self, tabs, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(40)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.buttons = []
        for i, label in enumerate(tabs):
            btn = TabButton(label, i, theme_manager)
            btn.clicked.connect(self._on_tab_clicked)
            self._layout.addWidget(btn)
            self.buttons.append(btn)

        self.current_index = 0
        self.buttons[0].is_active = True

        self._indicator_x = 0.0
        self._indicator_width = 0.0

        self._anim = QPropertyAnimation(self, b"geometry")
        QTimer.singleShot(50, self._init_indicator)

    def _init_indicator(self):
        if self.buttons:
            btn = self.buttons[0]
            self._indicator_x = float(btn.x())
            self._indicator_width = float(btn.width())
            self.update()

    def _on_tab_clicked(self, index):
        if index == self.current_index:
            return

        for btn in self.buttons:
            btn.is_active = False
            btn.update()

        self.buttons[index].is_active = True
        self.buttons[index].update()

        self.current_index = index
        target_btn = self.buttons[index]
        self._animate_indicator(float(target_btn.x()), float(target_btn.width()))
        self.tabChanged.emit(index)

    def _animate_indicator(self, target_x, target_w):
        self._anim_x = QPropertyAnimation(self, b"indicatorX")
        self._anim_x.setDuration(300)
        self._anim_x.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim_x.setStartValue(self._indicator_x)
        self._anim_x.setEndValue(target_x)

        self._anim_w = QPropertyAnimation(self, b"indicatorWidth")
        self._anim_w.setDuration(300)
        self._anim_w.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim_w.setStartValue(self._indicator_width)
        self._anim_w.setEndValue(target_w)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(self._anim_x)
        self._anim_group.addAnimation(self._anim_w)
        self._anim_group.start()

    def _get_indicator_x(self):
        return self._indicator_x

    def _set_indicator_x(self, val):
        self._indicator_x = val
        self.update()

    def _get_indicator_width(self):
        return self._indicator_width

    def _set_indicator_width(self, val):
        self._indicator_width = val
        self.update()

    indicatorX = pyqtProperty(float, _get_indicator_x, _set_indicator_x)
    indicatorWidth = pyqtProperty(float, _get_indicator_width, _set_indicator_width)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = self.theme_manager.colors
        accent = QColor(c['accent'])

        h = 3
        y = self.height() - h
        pill_w = self._indicator_width * 0.5
        pill_x = self._indicator_x + (self._indicator_width - pill_w) / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(int(pill_x), y, int(pill_w), h, h / 2, h / 2)


class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._speed = 400
        self._animation_type = QEasingCurve.Type.OutCubic
        self._now = 0
        self._next = 0
        self._active = False
        self._current_anim_group = None

    def slide_to(self, index):
        if index == self.currentIndex():
            return
        if self._active:
            return

        self._active = True
        width = self.frameRect().width()
        height = self.frameRect().height()

        _next = index
        _now = self.currentIndex()
        direction = 1 if _next > _now else -1

        next_widget = self.widget(_next)
        now_widget = self.widget(_now)

        next_widget.setGeometry(0, 0, width, height)
        next_widget.show()
        next_widget.raise_()

        now_start = QPoint(0, 0)
        now_end = QPoint(-direction * width, 0)
        next_start = QPoint(direction * width, 0)
        next_end = QPoint(0, 0)

        anim_now = QPropertyAnimation(now_widget, b"pos")
        anim_now.setDuration(self._speed)
        anim_now.setEasingCurve(self._animation_type)
        anim_now.setStartValue(now_start)
        anim_now.setEndValue(now_end)

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self._speed)
        anim_next.setEasingCurve(self._animation_type)
        anim_next.setStartValue(next_start)
        anim_next.setEndValue(next_end)

        self._current_anim_group = QParallelAnimationGroup()
        self._current_anim_group.addAnimation(anim_now)
        self._current_anim_group.addAnimation(anim_next)

        self._now = _now
        self._next = _next

        self._current_anim_group.finished.connect(self._on_animation_done)
        self._current_anim_group.start()

    def _on_animation_done(self):
        self.setCurrentIndex(self._next)
        self.widget(self._now).move(0, 0)
        self._active = False
