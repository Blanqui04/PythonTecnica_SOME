from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, 
                             QLabel, QGroupBox)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import pyqtSignal, Qt
import os

# Import custom widgets
from ..widgets.inputs import ModernLineEdit
from ..widgets.buttons import ModernButton

class HeaderPanel(QWidget):
    search_requested = pyqtSignal(dict)  # Signal with search criteria
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top row with logo and title
        top_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.load_logo()
        
        self.title_label = QLabel("Database Management System")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        
        top_layout.addWidget(self.logo_label)
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # Search section
        search_group = QGroupBox("Search & Filter")
        search_layout = QGridLayout()
        
        # Search fields
        self.num_oferta_edit = ModernLineEdit("Número d'Oferta")
        self.ref_client_edit = ModernLineEdit("Referència Client")
        self.num_lot_edit = ModernLineEdit("Número de Lot")
        self.ref_project_edit = ModernLineEdit("Referència Projecte")
        
        # Buttons
        self.search_btn = ModernButton("🔍 Search", primary=True)
        self.search_btn.clicked.connect(self.emit_search)
        
        self.clear_btn = ModernButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_search)
        
        # Layout
        search_layout.addWidget(QLabel("Num. Oferta:"), 0, 0)
        search_layout.addWidget(self.num_oferta_edit, 0, 1)
        search_layout.addWidget(QLabel("Ref. Client:"), 0, 2)
        search_layout.addWidget(self.ref_client_edit, 0, 3)
        
        search_layout.addWidget(QLabel("Num. Lot:"), 1, 0)
        search_layout.addWidget(self.num_lot_edit, 1, 1)
        search_layout.addWidget(QLabel("Ref. Projecte:"), 1, 2)
        search_layout.addWidget(self.ref_project_edit, 1, 3)
        
        search_layout.addWidget(self.search_btn, 0, 4, 2, 1)
        search_layout.addWidget(self.clear_btn, 0, 5, 2, 1)
        
        search_group.setLayout(search_layout)
        
        # Result info
        self.result_info = QLabel("Ready to search...")
        self.result_info.setStyleSheet("color: #6c757d; font-style: italic;")
        
        layout.addLayout(top_layout)
        layout.addWidget(search_group)
        layout.addWidget(self.result_info)
        
        self.setLayout(layout)
        
    def load_logo(self):
        logo_path = os.path.join("assets", "images", "logo_some.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaledToHeight(50, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("LOGO")
            
    def get_search_criteria(self):
        return {
            'num_oferta': self.num_oferta_edit.text().strip(),
            'client': self.ref_client_edit.text().strip(),
            'num_lot': self.num_lot_edit.text().strip(),
            'ref_project': self.ref_project_edit.text().strip()
        }
        
    def emit_search(self):
        criteria = self.get_search_criteria()
        if any(criteria.values()):  # At least one field has value
            self.search_requested.emit(criteria)
        else:
            self.result_info.setText("Please enter at least one search criterion")
            
    def clear_search(self):
        self.num_oferta_edit.clear()
        self.ref_client_edit.clear()
        self.num_lot_edit.clear()
        self.ref_project_edit.clear()
        self.result_info.setText("Search fields cleared")