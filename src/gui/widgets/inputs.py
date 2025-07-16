from PyQt5.QtWidgets import QLineEdit, QTextEdit, QComboBox
from PyQt5.QtGui import QFont

class ModernLineEdit(QLineEdit):
    """Custom modern line edit with professional styling"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                padding: 10px 14px;
                color: #2c3e50;
                font-weight: 400;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #bdc3c7;
            }
            QLineEdit::placeholder {
                color: #95a5a6;
                font-style: italic;
            }
        """)

class ModernTextEdit(QTextEdit):
    """Custom modern text edit for larger text input"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(100)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                padding: 12px;
                color: #2c3e50;
                font-weight: 400;
            }
            QTextEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QTextEdit:hover {
                border-color: #bdc3c7;
            }
        """)

class ModernComboBox(QComboBox):
    """Custom modern combo box with professional styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                padding: 10px 14px;
                color: #2c3e50;
                font-weight: 400;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #3498db;
                outline: none;
            }
            QComboBox:hover {
                border-color: #bdc3c7;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #7f8c8d;
                border-top: none;
                border-left: none;
                width: 6px;
                height: 6px;
                margin-right: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                padding: 4px;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                height: 32px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3498db;
                color: #ffffff;
            }
        """)

class SearchEdit(ModernLineEdit):
    """Specialized search input with enhanced styling"""
    def __init__(self, placeholder="Search...", parent=None):
        super().__init__(placeholder, parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 20px;
                padding: 8px 16px;
                color: #495057;
                font-weight: 400;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #6c757d;
                font-style: italic;
            }
        """)