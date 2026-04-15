from PyQt6.QtWidgets import QLabel, QGridLayout, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont
from core.modules import BaseModule


class CalcButton(QWidget):
    def __init__(self, text, theme_manager, role="num", parent=None):
        super().__init__(parent)
        self.text = text
        self.theme_manager = theme_manager
        self.role = role
        self._hover = False
        self._pressed = False
        self.callback = None
        self.setFixedHeight(36)
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
                self.callback(self.text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.theme_manager.colors
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)

        if self.role == "accent":
            bg = QColor(c['accent'])
            if self._pressed:
                bg = bg.darker(120)
            elif self._hover:
                bg = bg.lighter(120)
            text_color = QColor("#FFFFFF")
        elif self.role == "op":
            bg = QColor(c['card']).lighter(160)
            if self._pressed:
                bg = bg.darker(120)
            elif self._hover:
                bg = bg.lighter(115)
            text_color = QColor(c['accent'])
        else:
            bg = QColor(c['card']).lighter(125)
            if self._pressed:
                bg = bg.darker(120)
            elif self._hover:
                bg = bg.lighter(115)
            text_color = QColor(c['text'])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 8, 8)

        font = QFont("Segoe UI Variable", 12)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text)


class CalculatorModule(BaseModule):
    def __init__(self, theme_manager, parent=None):
        self.theme_manager = theme_manager
        self._expression = ""
        self._display_text = "0"
        self._just_evaluated = False
        super().__init__(parent)
        self.timer.stop()

    def setup_ui(self):
        self.layout.setSpacing(6)

        self.display = QLabel("0")
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setStyleSheet("font-size: 28px; font-weight: 300; font-family: 'Segoe UI Variable'; padding: 4px 8px;")
        self.display.setFixedHeight(44)
        self.layout.addWidget(self.display)

        self.expr_label = QLabel("")
        self.expr_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.expr_label.setStyleSheet("font-size: 11px; color: #8E8E93; padding: 0px 8px;")
        self.expr_label.setFixedHeight(16)
        self.layout.addWidget(self.expr_label)

        buttons = [
            ("C", "op"), ("±", "op"), ("%", "op"), ("÷", "op"),
            ("7", "num"), ("8", "num"), ("9", "num"), ("×", "op"),
            ("4", "num"), ("5", "num"), ("6", "num"), ("−", "op"),
            ("1", "num"), ("2", "num"), ("3", "num"), ("+", "op"),
            ("0", "num"), (".", "num"), ("⌫", "op"), ("=", "accent"),
        ]

        grid = QGridLayout()
        grid.setSpacing(4)

        for i, (text, role) in enumerate(buttons):
            btn = CalcButton(text, self.theme_manager, role)
            btn.callback = self._on_button
            row, col = divmod(i, 4)
            grid.addWidget(btn, row, col)

        self.layout.addLayout(grid)

    def _on_button(self, text):
        if text == "C":
            self._expression = ""
            self._display_text = "0"
            self._just_evaluated = False
        elif text == "⌫":
            if self._just_evaluated:
                self._expression = ""
                self._display_text = "0"
                self._just_evaluated = False
            elif self._display_text and self._display_text != "0":
                self._display_text = self._display_text[:-1]
                if not self._display_text:
                    self._display_text = "0"
        elif text == "±":
            if self._display_text and self._display_text != "0":
                if self._display_text.startswith("-"):
                    self._display_text = self._display_text[1:]
                else:
                    self._display_text = "-" + self._display_text
        elif text == "%":
            try:
                val = float(self._display_text)
                self._display_text = self._format_result(val / 100)
            except:
                pass
        elif text == "=":
            self._evaluate()
        elif text in ("+", "−", "×", "÷"):
            op_map = {"+": "+", "−": "-", "×": "*", "÷": "/"}
            if self._just_evaluated:
                self._expression = self._display_text + op_map[text]
                self._just_evaluated = False
            else:
                self._expression += self._display_text + op_map[text]
            self._display_text = ""
        else:
            if self._just_evaluated:
                self._expression = ""
                self._display_text = ""
                self._just_evaluated = False
            if self._display_text == "0" and text != ".":
                self._display_text = text
            else:
                self._display_text += text

        self._update_display()

    def _evaluate(self):
        expr = self._expression + self._display_text
        if not expr:
            return
        try:
            result = eval(expr)
            self.expr_label.setText(expr.replace("*", "×").replace("/", "÷").replace("-", "−") + " =")
            self._display_text = self._format_result(result)
            self._expression = ""
            self._just_evaluated = True
        except:
            self._display_text = "Error"
            self._expression = ""
            self._just_evaluated = True

    def _format_result(self, val):
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        if isinstance(val, float):
            return f"{val:.8g}"
        return str(val)

    def _update_display(self):
        shown = self._display_text if self._display_text else "0"
        self.display.setText(shown)
        if not self._just_evaluated:
            preview = self._expression.replace("*", "×").replace("/", "÷").replace("-", "−")
            self.expr_label.setText(preview)

    def update_content(self):
        pass
