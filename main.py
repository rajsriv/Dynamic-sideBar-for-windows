import sys
from PyQt6.QtWidgets import QApplication
from core.sidebar import Sidebar
from core.theme_manager import ThemeManager
from core.media_manager import MediaManagerCore
from modules.clock import ClockModule
from modules.controls import ControlModule
from modules.media import MediaModule

def main():
    app = QApplication(sys.argv)
    
    theme_manager = ThemeManager()
    media_core = MediaManagerCore()
    
    sidebar = Sidebar(theme_manager)
    
    clock = ClockModule(theme_manager)
    sidebar.main_layout.addWidget(clock)
    
    controls = ControlModule(theme_manager)
    sidebar.main_layout.addWidget(controls)
    
    media = MediaModule(media_core, theme_manager)
    sidebar.main_layout.addWidget(media)
    
    sidebar.main_layout.addStretch()
    
    sidebar.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
