import calendar
import json
from datetime import date
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QSettings, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen
from core.modules import BaseModule


class MiniPopup(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedSize(64, 28)
        self.callback = None
        self._opacity = 0.0
        self.hide()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"popOpacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_opacity(self):
        return self._opacity

    def _set_opacity(self, val):
        self._opacity = val
        self.update()

    popOpacity = pyqtProperty(float, _get_opacity, _set_opacity)

    def show_at(self, x, y_bottom):
        px = x - self.width() // 2
        py = y_bottom + 4
        if self.parentWidget():
            pw = self.parentWidget().width()
            ph = self.parentWidget().height()
            px = max(0, min(px, pw - self.width()))
            if py + self.height() > ph:
                py = y_bottom - self.height() - 28
        self.move(px, py)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    def paintEvent(self, event):
        if self._opacity <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        c = self.theme_manager.colors

        bg = QColor(c['card']).lighter(140)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 6, 6)

        half = self.width() / 2
        painter.setPen(QPen(QColor(c['text_dim']), 1))
        painter.drawLine(int(half), 4, int(half), self.height() - 4)

        font = QFont("Segoe UI Variable", 14)
        painter.setFont(font)
        painter.setPen(QColor("#4CAF50"))
        painter.drawText(QRectF(0, 0, half, self.height()), Qt.AlignmentFlag.AlignCenter, "✓")
        painter.setPen(QColor("#EF5350"))
        painter.drawText(QRectF(half, 0, half, self.height()), Qt.AlignmentFlag.AlignCenter, "✗")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            half = self.width() / 2
            if event.position().x() < half:
                if self.callback:
                    self.callback("check")
            else:
                if self.callback:
                    self.callback("cross")
            self.hide()


class CalendarGrid(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._year = date.today().year
        self._month = date.today().month
        self._today = date.today()
        self._marks = {}
        self._hovered_cell = (-1, -1)
        self._cell_scales = {}
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.popup = MiniPopup(theme_manager, self)
        self.popup.callback = self._on_popup_choice
        self._popup_date = None

        self._load_marks()

    def _load_marks(self):
        settings = QSettings("RajSriv", "UpDock")
        raw = settings.value("calendar_marks", "{}")
        try:
            self._marks = json.loads(raw) if isinstance(raw, str) else {}
        except:
            self._marks = {}

    def _save_marks(self):
        settings = QSettings("RajSriv", "UpDock")
        settings.setValue("calendar_marks", json.dumps(self._marks))

    def set_month(self, year, month):
        self._year = year
        self._month = month
        self.popup.hide()
        self.update()

    def _get_cell_rect(self, row, col):
        cw = self.width() / 7
        header_h = 20
        ch = (self.height() - header_h) / 6
        return QRectF(col * cw, header_h + row * ch, cw, ch)

    def _date_at(self, row, col):
        cal = calendar.monthcalendar(self._year, self._month)
        if row < len(cal):
            day = cal[row][col]
            if day != 0:
                return day
        return None

    def _on_popup_choice(self, choice):
        if self._popup_date:
            key = f"{self._year}-{self._month:02d}-{self._popup_date:02d}"
            if choice == "check":
                if self._marks.get(key) == "check":
                    del self._marks[key]
                else:
                    self._marks[key] = "check"
            else:
                if self._marks.get(key) == "cross":
                    del self._marks[key]
                else:
                    self._marks[key] = "cross"
            self._save_marks()
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            cw = self.width() / 7
            header_h = 20
            ch = (self.height() - header_h) / 6
            col = int(event.position().x() / cw)
            row = int((event.position().y() - header_h) / ch)
            if 0 <= row < 6 and 0 <= col < 7:
                day = self._date_at(row, col)
                if day:
                    self._popup_date = day
                    cell_rect = self._get_cell_rect(row, col)
                    px = int(cell_rect.center().x())
                    py = int(cell_rect.bottom())
                    self.popup.show_at(px, py)

    def mouseMoveEvent(self, event):
        cw = self.width() / 7
        header_h = 20
        ch = (self.height() - header_h) / 6
        col = int(event.position().x() / cw)
        row = int((event.position().y() - header_h) / ch)
        new_cell = (row, col) if 0 <= row < 6 and 0 <= col < 7 else (-1, -1)
        if new_cell != self._hovered_cell:
            self._hovered_cell = new_cell
            self.update()

    def leaveEvent(self, event):
        self._hovered_cell = (-1, -1)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        accent = QColor(c['accent'])

        cw = self.width() / 7
        header_h = 20

        day_names = ["M", "T", "W", "T", "F", "S", "S"]
        font_header = QFont("Segoe UI Variable", 8)
        font_header.setWeight(QFont.Weight.Bold)
        painter.setFont(font_header)
        painter.setPen(QColor(c['text_dim']))
        for i, name in enumerate(day_names):
            painter.drawText(QRectF(i * cw, 0, cw, header_h), Qt.AlignmentFlag.AlignCenter, name)

        ch = (self.height() - header_h) / 6
        cal = calendar.monthcalendar(self._year, self._month)

        font_day = QFont("Segoe UI Variable", 10)
        font_day.setWeight(QFont.Weight.Medium)
        painter.setFont(font_day)

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue

                cell = self._get_cell_rect(row_idx, col_idx)
                is_today = (day == self._today.day and self._month == self._today.month and self._year == self._today.year)
                is_hovered = (row_idx, col_idx) == self._hovered_cell
                key = f"{self._year}-{self._month:02d}-{day:02d}"
                mark = self._marks.get(key)

                circle_rect = QRectF(cell.center().x() - 12, cell.center().y() - 12, 24, 24)

                if is_today:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(accent)
                    painter.drawEllipse(circle_rect)
                    painter.setPen(QColor("#FFFFFF"))
                elif is_hovered:
                    hover_bg = QColor(c['text'])
                    hover_bg.setAlpha(20)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(hover_bg)
                    painter.drawEllipse(circle_rect)
                    painter.setPen(QColor(c['text']))
                else:
                    painter.setPen(QColor(c['text']))

                painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, str(day))

                if mark:
                    mark_color = QColor("#4CAF50") if mark == "check" else QColor("#EF5350")
                    mark_color.setAlpha(180)
                    style = self.theme_manager.mark_style

                    if style == "underline":
                        painter.setPen(QPen(mark_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                        ux = cell.center().x() - 8
                        uy = circle_rect.bottom() + 2
                        painter.drawLine(QPointF(ux, uy), QPointF(ux + 16, uy))
                    else:
                        painter.setPen(QPen(mark_color, 1.5))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawRoundedRect(circle_rect.adjusted(-1, -1, 1, 1), 6, 6)


class NavButton(QWidget):
    def __init__(self, direction, theme_manager, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.theme_manager = theme_manager
        self._hover = False
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.callback = None

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.callback:
            self.callback()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        color = QColor(c['accent']) if self._hover else QColor(c['text_dim'])

        if self._hover:
            bg = QColor(c['text'])
            bg.setAlpha(15)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 6, 6)

        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath()
        w, h = self.width(), self.height()
        if self.direction == "left":
            path.moveTo(w * 0.55, h * 0.3)
            path.lineTo(w * 0.35, h * 0.5)
            path.lineTo(w * 0.55, h * 0.7)
        else:
            path.moveTo(w * 0.45, h * 0.3)
            path.lineTo(w * 0.65, h * 0.5)
            path.lineTo(w * 0.45, h * 0.7)
        painter.drawPath(path)


class CalendarModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        super().__init__(parent)
        self.timer.stop()

    def setup_ui(self):
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(10, 10, 10, 10)

        header = QHBoxLayout()
        header.setSpacing(4)

        self.btn_prev = NavButton("left", self.theme_manager)
        self.btn_prev.callback = self._prev_month

        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setStyleSheet("font-size: 13px; font-weight: 600; font-family: 'Segoe UI Variable'; background: transparent;")

        self.btn_next = NavButton("right", self.theme_manager)
        self.btn_next.callback = self._next_month

        header.addWidget(self.btn_prev)
        header.addStretch()
        header.addWidget(self.month_label)
        header.addStretch()
        header.addWidget(self.btn_next)

        self.layout.addLayout(header)

        self.grid = CalendarGrid(self.theme_manager)
        self.grid.setFixedHeight(170)
        self.layout.addWidget(self.grid)

        self._update_label()

    def _update_label(self):
        import calendar as cal_mod
        name = cal_mod.month_name[self.grid._month]
        self.month_label.setText(f"{name} {self.grid._year}")

    def _prev_month(self):
        m = self.grid._month - 1
        y = self.grid._year
        if m < 1:
            m = 12
            y -= 1
        self.grid.set_month(y, m)
        self._update_label()

    def _next_month(self):
        m = self.grid._month + 1
        y = self.grid._year
        if m > 12:
            m = 1
            y += 1
        self.grid.set_month(y, m)
        self._update_label()

    def update_content(self):
        pass
