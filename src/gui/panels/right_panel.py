from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
import os

# Import shared logger
from src.gui.logging_config import logger

from ..widgets.buttons import ActionButton

class RightPanel(QGroupBox):
    action_requested = pyqtSignal(str)  # Signal with action name
    
    def __init__(self, parent=None):
        super().__init__("Additional Actions", parent)
        logger.debug("Initializing [RightPanel]")
        self.setup_ui()
        logger.info("[RightPanel] initialized successfully")
        
    def setup_ui(self):
        logger.debug("Setting up UI for [RightPanel]")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 20)
        
        # Set panel styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                background-color: #fafafa;
            }
        """)
        
        # Edit section
        edit_group = QGroupBox("Edit")
        edit_group.setStyleSheet(self.get_section_style())
        edit_layout = QVBoxLayout()
        edit_layout.setSpacing(10)
        
        edit_icon = self.load_icon("edit.svg")
        self.edit_btn = ActionButton("Edit Data", edit_icon)
        self.edit_btn.clicked.connect(lambda: self.emit_action("edit_data"))
        edit_layout.addWidget(self.edit_btn)
        edit_group.setLayout(edit_layout)
        
        # File operations section
        file_group = QGroupBox("File Operations")
        file_group.setStyleSheet(self.get_section_style())
        file_layout = QVBoxLayout()
        file_layout.setSpacing(10)
        
        o_drawing_icon = self.load_icon("drawing.svg")
        folder_icon = self.load_icon("open_folder.svg")
        
        self.view_drawing_btn = ActionButton("View Drawing", o_drawing_icon)
        self.open_folder_btn = ActionButton("Open Folder", folder_icon)
        
        self.view_drawing_btn.clicked.connect(lambda: self.emit_action("view_drawing"))
        self.open_folder_btn.clicked.connect(lambda: self.emit_action("open_folder"))
        
        file_layout.addWidget(self.view_drawing_btn)
        file_layout.addWidget(self.open_folder_btn)
        file_group.setLayout(file_layout)
        
        # Data transfer section
        transfer_group = QGroupBox("Data Transfer")
        transfer_group.setStyleSheet(self.get_section_style())
        transfer_layout = QVBoxLayout()
        transfer_layout.setSpacing(10)
        
        export_icon = self.load_icon("export.svg")
        import_icon = self.load_icon("import.svg")
        
        self.export_btn = ActionButton("Export Data", export_icon)
        self.import_btn = ActionButton("Import Data", import_icon)
        
        self.export_btn.clicked.connect(lambda: self.emit_action("export_data"))
        self.import_btn.clicked.connect(lambda: self.emit_action("import_data"))
        
        transfer_layout.addWidget(self.export_btn)
        transfer_layout.addWidget(self.import_btn)
        transfer_group.setLayout(transfer_layout)
        
        # Add all sections to main layout
        layout.addWidget(edit_group)
        layout.addWidget(file_group)
        layout.addWidget(transfer_group)
        layout.addStretch()
        
        self.setLayout(layout)
        logger.debug("UI for [RightPanel] set up successfully")
    
    def get_section_style(self):
        return """
            QGroupBox {
                font-weight: 500;
                font-size: 12px;
                color: #34495e;
                border: 1px solid #d5dbdb;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                background-color: #ffffff;
            }
        """
    
    def load_icon(self, icon_name):
        icon_path = os.path.join("assets", "icons", icon_name)
        if os.path.exists(icon_path):
            logger.debug(f"Loaded icon: {icon_path}")
            return QIcon(icon_path)
        else:
            logger.warning(f"Icon not found: {icon_path}")
            return None
        
    def emit_action(self, action_name):
        logger.info(f"Action emitted from [RightPanel]: {action_name}")
        self.action_requested.emit(action_name)
