# inputs.py
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QFont

class ModernLineEdit(QLineEdit):
    """Custom modern line edit"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QLineEdit:hover {
                border-color: #c0c0c0;
            }
        """)