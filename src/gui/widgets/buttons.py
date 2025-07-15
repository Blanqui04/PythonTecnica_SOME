# buttons.py
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ModernButton(QPushButton):
    """Custom modern button with hover effects"""
    def __init__(self, text, primary=False, icon=None):
        super().__init__(text)
        self.primary = primary
        self.setMinimumHeight(45)
        self.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.setCursor(Qt.PointingHandCursor)
        
        if icon:
            self.setIcon(icon)
            
        self.setStyle()
        
    def setStyle(self):
        base_style = """
            QPushButton {{
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                min-width: 120px;
                {primary_style}
            }}
            QPushButton:hover {{
                {hover_style}
            }}
            QPushButton:pressed {{
                {pressed_style}
            }}
        """
        
        if self.primary:
            stylesheet = base_style.format(
                primary_style="background-color: #0078d4; color: white; border: none;",
                hover_style="background-color: #106ebe;",
                pressed_style="background-color: #005a9e;"
            )
        else:
            stylesheet = base_style.format(
                primary_style="background-color: #f5f5f5; color: #333; border: 1px solid #ddd;",
                hover_style="background-color: #e8e8e8; border-color: #bbb;",
                pressed_style="background-color: #d8d8d8;"
            )
            
        self.setStyleSheet(stylesheet)