from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, 
                             QLabel, QGroupBox, QFrame)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import pyqtSignal, Qt
import os

# Import custom widgets
from ..widgets.inputs import ModernLineEdit
from ..widgets.buttons import ModernButton

# Import shared logger
from src.gui.logging_config import logger

class HeaderPanel(QWidget):
    search_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing [HeaderPanel]")
        self.setup_ui()
        
    def setup_ui(self):
        logger.debug("Setting up [HeaderPanel] UI")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(15)
        
        # Top row with logo and title
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QLabel()
        self.load_logo()
        
        self.title_label = QLabel("Database Management System")
        self.title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 10px 0;
                padding: 0;
            }
        """)
        
        top_layout.addWidget(self.logo_label)
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #bdc3c7; }")
        
        # Search section
        search_group = QGroupBox("Search & Filter")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                color: #34495e;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                background-color: #fafafa;
            }
        """)
        
        search_layout = QGridLayout()
        search_layout.setSpacing(8)
        search_layout.setContentsMargins(20, 20, 20, 20)
        
        self.num_oferta_edit = ModernLineEdit("Enter offer number")
        self.ref_client_edit = ModernLineEdit("Enter client's name")
        self.num_lot_edit = ModernLineEdit("Enter lot number")
        self.ref_project_edit = ModernLineEdit("Enter project reference")
        
        label_style = """
            QLabel {
                font-weight: 600;
                color: #34495e;
                font-size: 12px;
                margin-bottom: 2px;
            }
        """
        
        num_oferta_label = QLabel("Offer Number:")
        ref_client_label = QLabel("Client:")
        num_lot_label = QLabel("Lot Number:")
        ref_project_label = QLabel("Project Reference:")
        
        for label in [num_oferta_label, ref_client_label, num_lot_label, ref_project_label]:
            label.setStyleSheet(label_style)
        
        search_icon = self.load_icon("search.svg")
        clear_icon = self.load_icon("clear.svg")
        
        self.search_btn = ModernButton("Search", primary=True, icon=search_icon)
        self.search_btn.clicked.connect(self.emit_search)
        
        self.clear_btn = ModernButton("Clear", icon=clear_icon)
        self.clear_btn.clicked.connect(self.clear_search)
        
        search_layout.addWidget(num_oferta_label, 0, 0)
        search_layout.addWidget(self.num_oferta_edit, 1, 0)
        search_layout.addWidget(ref_client_label, 0, 1)
        search_layout.addWidget(self.ref_client_edit, 1, 1)
        search_layout.addWidget(num_lot_label, 0, 2)
        search_layout.addWidget(self.num_lot_edit, 1, 2)
        search_layout.addWidget(ref_project_label, 0, 3)
        search_layout.addWidget(self.ref_project_edit, 1, 3)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        search_layout.addLayout(button_layout, 2, 0, 1, 4)
        
        search_group.setLayout(search_layout)
        
        self.result_info = QLabel("Ready to search...")
        self.result_info.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                font-size: 11px;
                margin-top: 5px;
                padding: 5px;
            }
        """)
        
        layout.addLayout(top_layout)
        layout.addWidget(separator)
        layout.addWidget(search_group)
        layout.addWidget(self.result_info)
        
        self.setLayout(layout)
        logger.debug("[HeaderPanel] UI setup complete")
        
    def load_logo(self):
        logo_path = os.path.join("assets", "images", "gui", "logo_some.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaledToHeight(50, Qt.SmoothTransformation))
            logger.info(f"Loaded logo from {logo_path}")
        else:
            logger.warning(f"Logo not found at {logo_path}, using fallback text")
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 14px;
                    font-weight: bold;
                    border: 2px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 15px 20px;
                    background-color: #ecf0f1;
                }
            """)
    
    def load_icon(self, icon_name):
        icon_path = os.path.join("assets", "icons", icon_name)
        if os.path.exists(icon_path):
            logger.info(f"Loaded icon: {icon_path}")
            return QIcon(icon_path)
        logger.warning(f"Icon not found: {icon_path}")
        return None
            
    def get_search_criteria(self):
        criteria = {
            'num_oferta': self.num_oferta_edit.text().strip(),
            'client': self.ref_client_edit.text().strip(),
            'num_lot': self.num_lot_edit.text().strip(),
            'ref_project': self.ref_project_edit.text().strip()
        }
        logger.debug(f"Search criteria retrieved: {criteria}")
        return criteria
        
    def emit_search(self):
        criteria = self.get_search_criteria()
        if any(criteria.values()):
            logger.info("Search initiated with criteria: %s", criteria)
            self.search_requested.emit(criteria)
            self.result_info.setText("Search initiated...")
        else:
            logger.info("Search attempted with empty criteria")
            self.result_info.setText("Please enter at least one search criterion")
            
    def clear_search(self):
        logger.debug("Clearing search fields")
        self.num_oferta_edit.clear()
        self.ref_client_edit.clear()
        self.num_lot_edit.clear()
        self.ref_project_edit.clear()
        self.result_info.setText("Search fields cleared")
        logger.info("Search fields cleared by user")
