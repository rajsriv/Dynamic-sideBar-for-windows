import sys
from PyQt6.QtWidgets import QApplication
from core.sidebar import Sidebar
from core.theme_manager import ThemeManager
from core.media_manager import MediaManagerCore
from modules.clock import ClockModule
from modules.controls import ControlModule
from modules.media import MediaModule
from modules.stopwatch import StopwatchModule
from modules.calculator import CalculatorModule
from modules.settings import SettingsModule
from modules.calendar_mod import CalendarModule

def main():
    app = QApplication(sys.argv)
    
    theme_manager = ThemeManager()
    media_core = MediaManagerCore()
    
    sidebar = Sidebar(theme_manager)
    
    basic_layout = sidebar.tab_layouts[0]
    dock_layout = sidebar.tab_layouts[1]
    settings_layout = sidebar.tab_layouts[2]
    
    clock = ClockModule(theme_manager)
    basic_layout.insertWidget(basic_layout.count() - 1, clock)
    
    controls = ControlModule(theme_manager)
    basic_layout.insertWidget(basic_layout.count() - 1, controls)
    
    media = MediaModule(media_core, theme_manager)
    basic_layout.insertWidget(basic_layout.count() - 1, media)
    
    stopwatch = StopwatchModule(theme_manager)
    dock_layout.insertWidget(dock_layout.count() - 1, stopwatch)
    
    calculator = CalculatorModule(theme_manager)
    dock_layout.insertWidget(dock_layout.count() - 1, calculator)
    
    cal = CalendarModule(theme_manager)
    dock_layout.insertWidget(dock_layout.count() - 1, cal)
    
    settings = SettingsModule(theme_manager)
    settings_layout.insertWidget(settings_layout.count() - 1, settings)
    
    sidebar.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
