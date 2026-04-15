import sys
import winreg
import os
import darkdetect
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QColor

class ThemeManager(QObject):
    themeChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = QSettings("RajSriv", "UpDock")
                                                       
        self._mode = 'system'
        self._user_name = "Raj"
        self.is_aura = False
        
        self.sidebar_width = 220
        self.window_margin = 20
        
        self.colors = {
            'bg': '#1C1C1E',
            'card': '#2C2C2E',
            'accent': '#34C759',
            'text': '#FFFFFF',
            'text_dim': '#8E8E93',
            'handle_bg': '#3A3A3C',
            'blob': '#34C759'
        }
        
        self._last_wallpaper = ""
        self._autostart = False
        self._mark_style = "stroke"
        
        self.load_settings()
        self.update_palette()

        # Synchronize registry with loaded setting
        self._update_registry(self._autostart)

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_wallpaper_change)
        self.poll_timer.start(5000)

    @property
    def mode(self): return self._mode

    @property
    def user_name(self): return self._user_name
    @user_name.setter
    def user_name(self, name):
        if self._user_name != name:
            self._user_name = name
            self.save_settings()
            self.themeChanged.emit()

    def set_mode(self, mode):
        self._mode = mode
        self.is_aura = 'aura' in mode
        self.update_palette()
        self.save_settings()
        self.themeChanged.emit()

    def get_wallpaper_path(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
                path, _ = winreg.QueryValueEx(key, "Wallpaper")
                return path
        except: return None

    @property
    def autostart(self):
        return self._autostart

    @autostart.setter
    def autostart(self, enabled):
        if self._autostart != enabled:
            self._autostart = enabled
            self._update_registry(enabled)
            self.save_settings()
            self.themeChanged.emit()

    def _update_registry(self, enabled):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "UpDock"
        
        if getattr(sys, 'frozen', False):
            exe_path = f'"{sys.executable}"'
        else:
            main_py = os.path.abspath(sys.argv[0])
            # If we are running main.py directly
            if not main_py.endswith('.py'):
                # Handle cases where sys.argv[0] might not be what we expect
                # Use a fallback or stick to known structure
                pass
            exe_path = f'"{sys.executable}" "{main_py}"'
                                                                             
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error updating registry: {e}")

    @property
    def mark_style(self): return self._mark_style

    @mark_style.setter
    def mark_style(self, style):
        if self._mark_style != style:
            self._mark_style = style
            self.save_settings()
            self.themeChanged.emit()

    def load_settings(self):
        self._mode = str(self.settings.value("mode", "system"))
        self._user_name = str(self.settings.value("user_name", "Raj"))
        state = self.settings.value("autostart", False)
        # QSettings can return string or bool depending on platform/version
        if isinstance(state, str):
            self._autostart = state.lower() == 'true'
        else:
            self._autostart = bool(state)
        self._mark_style = str(self.settings.value("mark_style", "stroke"))
        self.is_aura = 'aura' in self._mode

    def save_settings(self):
        self.settings.setValue("mode", self._mode)
        self.settings.setValue("user_name", self._user_name)
        self.settings.setValue("autostart", self._autostart)
        self.settings.setValue("mark_style", self._mark_style)

    def check_wallpaper_change(self):
        current_wp = self.get_wallpaper_path()
        if current_wp != self._last_wallpaper:
            self._last_wallpaper = current_wp
            self.update_palette()
            self.themeChanged.emit()

    def update_palette(self):
        eff_mode = self._mode
        if eff_mode == 'system':
            eff_mode = 'dark' if darkdetect.isDark() else 'day'
        
        is_light = 'day' in eff_mode
            
        wp_path = self.get_wallpaper_path()
        dom = (30, 30, 30)
        accent = (52, 199, 89)
        
        if wp_path and os.path.exists(wp_path):
            try:
                img = Image.open(wp_path); img = img.convert("RGB"); img = img.resize((50, 50))
                colors = img.getcolors(2500)
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                dom = sorted_colors[0][1]
                
                max_s = -1
                for count, color in sorted_colors[:15]:
                    r, g, b = color
                    mx = max(r, g, b); mn = min(r, g, b)
                    s = (mx - mn) / mx if mx > 0 else 0
                    if s > max_s: max_s = s; accent = color
            except: pass

        if is_light:
            self.colors['bg'] = "#FFFFFF"
            self.colors['card'] = "#F2F2F7"
            self.colors['accent'] = QColor(*accent).lighter(110).name()
            self.colors['handle_bg'] = "#F2F2F7"
            self.colors['text'] = "#000000"
            self.colors['text_dim'] = "#8E8E93"
            self.colors['blob'] = self.colors['accent']
        else:
            bg_q = QColor(*dom)
            h, s, v, a = bg_q.getHsv()
            bg_q.setHsv(h, min(s, 50), 25)
            self.colors['bg'] = bg_q.name()
            self.colors['card'] = QColor(bg_q).lighter(125).name()
            acc_q = QColor(*accent)
            h, s, v, a = acc_q.getHsv()
            acc_q.setHsv(h, max(s, 160), max(v, 200))
            self.colors['accent'] = acc_q.name()
            self.colors['handle_bg'] = QColor(bg_q).lighter(120).name()
            self.colors['text'] = "#FFFFFF"
            self.colors['text_dim'] = "#8E8E93"
            self.colors['blob'] = self.colors['accent']

    def get_qss(self):
        c = self.colors
        bg_color = c['bg']
        return f"""
            QWidget {{
                font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
                color: {c['text']};
            }}
            #SidebarContainer {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }}
            #ModuleCard {{
                background-color: rgba(0, 0, 0, 0.05) if '{c['bg']}' == '#FFFFFF' else rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
            #HandleButton {{
                background-color: {c['handle_bg']};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            #Title {{
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            QLabel {{ background: transparent; }}
        """
