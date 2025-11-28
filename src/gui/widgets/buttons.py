# src/gui/widgets/buttons.py
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ModernButton(QPushButton):
    """Custom modern button with professional styling and hover effects"""
    def __init__(self, text, primary=False, icon=None):
        super().__init__(text)
        self.primary = primary
        self.setMinimumHeight(48)
        self.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.setCursor(Qt.PointingHandCursor)
        
        if icon:
            self.setIcon(icon)
            from PyQt5.QtCore import QSize
            self.setIconSize(icon.actualSize(icon.availableSizes()[0]) if icon.availableSizes() else QSize(16, 16))
            
        self.setStyle()
        
    def setStyle(self):
        base_style = """
            QPushButton {{
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 500;
                min-width: 140px;
                text-align: center;
                border: none;
                {primary_style}
            }}
            QPushButton:hover {{
                {hover_style}
            }}
            QPushButton:pressed {{
                {pressed_style}
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
                border: 1px solid #ecf0f1;
            }}
        """
        
        if self.primary:
            stylesheet = base_style.format(
                primary_style="""
                    background-color: #3498db;
                    color: white;
                """,
                hover_style="""
                    background-color: #2980b9;
                """,
                pressed_style="""
                    background-color: #21618c;
                """
            )
        else:
            stylesheet = base_style.format(
                primary_style="""
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                """,
                hover_style="""
                    background-color: #d5dbdb;
                    border-color: #95a5a6;
                """,
                pressed_style="""
                    background-color: #abb2b9;
                    border-color: #7f8c8d;
                """
            )
        
        self.setStyleSheet(stylesheet)


class ActionButton(ModernButton):
    """Specialized button for main actions with enhanced styling"""
    def __init__(self, text, icon=None):
        super().__init__(text, primary=False, icon=icon)
        self.setMinimumHeight(52)
        self.setFont(QFont("Segoe UI", 11, QFont.Medium))
        
        # Override with action-specific styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #2c3e50;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                padding: 14px 20px;
                font-weight: 500;
                min-width: 160px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
                border-color: #2980b9;
            }
        """)


class CompactButton(ModernButton):
    """Compact button for secondary actions"""
    def __init__(self, text, icon=None):
        super().__init__(text, primary=False, icon=icon)
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 9, QFont.Medium))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
            }
        """)