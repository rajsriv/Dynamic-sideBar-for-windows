from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient
from core.modules import BaseModule


class AnimatedToggle(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._knob_x = 4.0
        self.callback = None

        self._anim = QPropertyAnimation(self, b"knobX")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _get_knob_x(self):
        return self._knob_x

    def _set_knob_x(self, val):
        self._knob_x = val
        self.update()

    knobX = pyqtProperty(float, _get_knob_x, _set_knob_x)

    @property
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, val):
        self._checked = val
        target = 24.0 if val else 4.0
        self._anim.stop()
        self._anim.setStartValue(self._knob_x)
        self._anim.setEndValue(target)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checked = not self._checked
            if self.callback:
                self.callback(self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors

        track_rect = QRectF(0, 0, self.width(), self.height())
        if self._checked:
            track_color = QColor(c['accent'])
        else:
            track_color = QColor(c['card']).lighter(150)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, 12, 12)

        knob_size = 16
        knob_y = (self.height() - knob_size) / 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(self._knob_x, knob_y, knob_size, knob_size))


class ThemeCard(QWidget):
    def __init__(self, mode_id, label, colors_preview, theme_manager, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.label = label
        self.colors_preview = colors_preview
        self.theme_manager = theme_manager
        self._selected = False
        self._hover = False
        self._scale = 1.0
        self.callback = None
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._scale_anim = QPropertyAnimation(self, b"cardScale")
        self._scale_anim.setDuration(200)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def _get_scale(self):
        return self._scale

    def _set_scale(self, val):
        self._scale = val
        self.update()

    cardScale = pyqtProperty(float, _get_scale, _set_scale)

    def enterEvent(self, event):
        self._hover = True
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.03)
        self._scale_anim.start()

    def leaveEvent(self, event):
        self._hover = False
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.callback:
                self.callback(self.mode_id)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors

        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)

        if self._selected:
            border_color = QColor(c['accent'])
            bg = QColor(c['accent'])
            bg.setAlpha(25)
        else:
            border_color = QColor(c['text_dim'])
            border_color.setAlpha(60)
            bg = QColor(c['card'])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 10, 10)

        if self._selected:
            from PyQt6.QtGui import QPen
            painter.setPen(QPen(border_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 10, 10)

        swatch_x = 12
        swatch_y = 10
        swatch_size = 14
        for i, color_hex in enumerate(self.colors_preview):
            sx = swatch_x + i * (swatch_size + 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color_hex))
            painter.drawRoundedRect(QRectF(sx, swatch_y, swatch_size, swatch_size), 4, 4)

        font = QFont("Segoe UI Variable", 10)
        font.setWeight(QFont.Weight.DemiBold if self._selected else QFont.Weight.Medium)
        painter.setFont(font)
        text_color = QColor(c['accent']) if self._selected else QColor(c['text'])
        painter.setPen(text_color)
        painter.drawText(QRectF(12, 28, self.width() - 24, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.label)

        if self._selected:
            check_x = self.width() - 26
            check_y = 10
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c['accent']))
            painter.drawEllipse(QRectF(check_x, check_y, 18, 18))

            from PyQt6.QtGui import QPen
            painter.setPen(QPen(QColor("#FFFFFF"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            path = QPainterPath()
            path.moveTo(check_x + 5, check_y + 9)
            path.lineTo(check_x + 8, check_y + 12)
            path.lineTo(check_x + 13, check_y + 6)
            painter.drawPath(path)


class SectionLabel(QWidget):
    def __init__(self, text, theme_manager, parent=None):
        super().__init__(parent)
        self.text = text
        self.theme_manager = theme_manager
        self.setFixedHeight(28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors

        font = QFont("Segoe UI Variable", 9)
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(font)
        painter.setPen(QColor(c['text_dim']))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, self.text.upper())


class SettingRow(QWidget):
    def __init__(self, label, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(40)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet(f"font-size: 13px; font-family: 'Segoe UI Variable'; background: transparent;")
        self._layout.addWidget(self.label_widget)
        self._layout.addStretch()

        self.toggle = AnimatedToggle(theme_manager)
        self._layout.addWidget(self.toggle)


class SegmentedPicker(QWidget):
    def __init__(self, options, theme_manager, parent=None):
        super().__init__(parent)
        self.options = options
        self.theme_manager = theme_manager
        self._selected = 0
        self._indicator_x = 0.0
        self.callback = None
        self.setFixedHeight(30)
        self.setMinimumWidth(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"indicatorX")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _get_ix(self):
        return self._indicator_x

    def _set_ix(self, val):
        self._indicator_x = val
        self.update()

    indicatorX = pyqtProperty(float, _get_ix, _set_ix)

    def set_index(self, idx):
        if idx == self._selected:
            return
        self._selected = idx
        seg_w = self.width() / len(self.options)
        self._anim.stop()
        self._anim.setStartValue(self._indicator_x)
        self._anim.setEndValue(idx * seg_w)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            seg_w = self.width() / len(self.options)
            idx = int(event.position().x() / seg_w)
            idx = max(0, min(idx, len(self.options) - 1))
            if idx != self._selected:
                self.set_index(idx)
                if self.callback:
                    self.callback(self.options[idx])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        n = len(self.options)
        seg_w = self.width() / n

        bg = QColor(c['card']).lighter(120)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)

        ind_color = QColor(c['accent'])
        ind_color.setAlpha(40)
        pad = 3
        painter.setBrush(ind_color)
        painter.drawRoundedRect(QRectF(self._indicator_x + pad, pad, seg_w - 2 * pad, self.height() - 2 * pad), 6, 6)

        font = QFont("Segoe UI Variable", 9)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        for i, opt in enumerate(self.options):
            color = QColor(c['accent']) if i == self._selected else QColor(c['text_dim'])
            painter.setPen(color)
            painter.drawText(QRectF(i * seg_w, 0, seg_w, self.height()), Qt.AlignmentFlag.AlignCenter, opt)


class SettingPickerRow(QWidget):
    def __init__(self, label, options, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(62)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet("font-size: 13px; font-family: 'Segoe UI Variable'; background: transparent;")
        self._layout.addWidget(self.label_widget)

        self.picker = SegmentedPicker(options, theme_manager)
        self._layout.addWidget(self.picker)


class SettingsModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        super().__init__(parent)
        self.timer.stop()
        self._sync_from_manager()
        self.theme_manager.themeChanged.connect(self._sync_from_manager)

    def setup_ui(self):
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)

        theme_section = SectionLabel("Appearance", self.theme_manager)
        self.layout.addWidget(theme_section)

        self.theme_modes = [
            ("system", "System", ["#6E6E73", "#34C759", "#FFFFFF"]),
            ("day", "Light", ["#FFFFFF", "#F2F2F7", "#007AFF"]),
            ("dark", "Dark", ["#1C1C1E", "#2C2C2E", "#34C759"]),
            ("day_aura", "Light Aura", ["#FFFFFF", "#E8F5E9", "#66BB6A"]),
            ("dark_aura", "Dark Aura", ["#1C1C1E", "#1B5E20", "#00E676"]),
        ]

        self.theme_cards = []
        for mode_id, label, colors in self.theme_modes:
            card = ThemeCard(mode_id, label, colors, self.theme_manager)
            card.callback = self._on_theme_selected
            self.layout.addWidget(card)
            self.theme_cards.append(card)

        spacer = QWidget()
        spacer.setFixedHeight(4)
        spacer.setStyleSheet("background: transparent;")
        self.layout.addWidget(spacer)

        general_section = SectionLabel("General", self.theme_manager)
        self.layout.addWidget(general_section)

        self.autostart_row = SettingRow("Launch at Startup", self.theme_manager)
        self.autostart_row.toggle.callback = self._on_autostart_changed
        self.layout.addWidget(self.autostart_row)

        self.mark_row = SettingPickerRow("Calendar Marks", ["Stroke", "Underline"], self.theme_manager)
        self.mark_row.picker.callback = self._on_mark_style_changed
        self.layout.addWidget(self.mark_row)

    def _on_theme_selected(self, mode_id):
        self.theme_manager.set_mode(mode_id)
        self._update_theme_cards()

    def _on_autostart_changed(self, checked):
        self.theme_manager.autostart = checked

    def _on_mark_style_changed(self, label):
        self.theme_manager.mark_style = label.lower()

    def _sync_from_manager(self):
        self._update_theme_cards()
        if hasattr(self, 'autostart_row'):
            current = self.theme_manager.autostart
            if self.autostart_row.toggle._checked != current:
                self.autostart_row.toggle._checked = current
                self.autostart_row.toggle._knob_x = 24.0 if current else 4.0
                self.autostart_row.toggle.update()
        if hasattr(self, 'mark_row'):
            idx = 0 if self.theme_manager.mark_style == "stroke" else 1
            if self.mark_row.picker._selected != idx:
                self.mark_row.picker._selected = idx
                seg_w = self.mark_row.picker.width() / len(self.mark_row.picker.options)
                self.mark_row.picker._indicator_x = idx * seg_w
                self.mark_row.picker.update()

    def _update_theme_cards(self):
        if not hasattr(self, 'theme_cards'):
            return
        current_mode = self.theme_manager.mode
        for card in self.theme_cards:
            card._selected = (card.mode_id == current_mode)
            card.update()

    def update_content(self):
        pass
