# Creator : github.com/rajsriv
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from core.modules import BaseModule


class StopwatchButton(QWidget):
    def __init__(self, text, accent=False, theme_manager=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.accent = accent
        self.theme_manager = theme_manager
        self._hover = False
        self._pressed = False
        self.callback = None
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self.update()
            if self.callback:
                self.callback()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors

        rect = QRectF(0, 0, self.width(), self.height())

        if self.accent:
            bg = QColor(c['accent'])
            if self._hover:
                bg = bg.lighter(120)
            if self._pressed:
                bg = bg.darker(120)
            text_color = QColor("#FFFFFF")
        else:
            bg = QColor(c['card']).lighter(130)
            if self._hover:
                bg = bg.lighter(120)
            if self._pressed:
                bg = bg.darker(110)
            text_color = QColor(c['text'])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 8, 8)

        font = QFont("Segoe UI Variable", 10)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text)


class StopwatchModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        self._running = False
        self._elapsed_ms = 0
        self._lap_start = 0
        super().__init__(parent)
        self.timer.stop()

        self._sw_timer = QTimer(self)
        self._sw_timer.setInterval(37)
        self._sw_timer.timeout.connect(self._tick)
        self._et = QElapsedTimer()

    def setup_ui(self):
        self.layout.setSpacing(8)

        self.time_label = QLabel("00:00.00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 36px; font-weight: 200; letter-spacing: -1px; font-family: 'Segoe UI Variable';")
        self.layout.addWidget(self.time_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_reset = StopwatchButton("Reset", accent=False, theme_manager=self.theme_manager)
        self.btn_reset.callback = self._reset

        self.btn_start = StopwatchButton("Start", accent=True, theme_manager=self.theme_manager)
        self.btn_start.callback = self._toggle

        btn_row.addWidget(self.btn_reset)
        btn_row.addWidget(self.btn_start)
        self.layout.addLayout(btn_row)

    def _format_time(self, ms):
        total_s = ms / 1000
        mins = int(total_s // 60)
        secs = total_s % 60
        return f"{mins:02d}:{secs:05.2f}"

    def _tick(self):
        current = self._elapsed_ms + self._et.elapsed()
        self.time_label.setText(self._format_time(current))

    def _toggle(self):
        if self._running:
            self._elapsed_ms += self._et.elapsed()
            self._sw_timer.stop()
            self._running = False
            self.btn_start.text = "Start"
            self.btn_start.accent = True
            self.btn_start.update()
            self.time_label.setText(self._format_time(self._elapsed_ms))
        else:
            self._et.start()
            self._sw_timer.start()
            self._running = True
            self.btn_start.text = "Stop"
            self.btn_start.accent = False
            self.btn_start.update()

    def _reset(self):
        self._sw_timer.stop()
        self._running = False
        self._elapsed_ms = 0
        self.time_label.setText("00:00.00")
        self.btn_start.text = "Start"
        self.btn_start.accent = True
        self.btn_start.update()
