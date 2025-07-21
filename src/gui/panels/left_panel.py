from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
import os
from ..widgets.buttons import ActionButton

# Import shared logger
from src.gui.logging_config import logger

class LeftPanel(QGroupBox):
    action_requested = pyqtSignal(str)  # Signal with action name
    
    def __init__(self, parent=None):
        super().__init__("Main Actions", parent)
        logger.debug("Initializing [LeftPanel]")
        self.setup_ui()
        
    def setup_ui(self):
        logger.debug("Setting up [LeftPanel] UI")
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
        
        # Analysis section
        analysis_group = QGroupBox("Analysis")
        analysis_group.setStyleSheet(self.get_section_style())
        analysis_layout = QVBoxLayout()
        analysis_layout.setSpacing(10)
        
        dimensional_icon = self.load_icon("dimensions.svg")
        capacity_icon = self.load_icon("statistics.svg")
        
        self.dimensional_btn = ActionButton("Dimensional Study", dimensional_icon)
        self.capacity_btn = ActionButton("Capacity Study", capacity_icon)
        
        self.dimensional_btn.clicked.connect(lambda: self.emit_action("dimensional"))
        self.capacity_btn.clicked.connect(lambda: self.emit_action("capacity"))
        
        analysis_layout.addWidget(self.dimensional_btn)
        analysis_layout.addWidget(self.capacity_btn)
        analysis_group.setLayout(analysis_layout)
        
        # View section
        view_group = QGroupBox("Read")
        view_group.setStyleSheet(self.get_section_style())
        view_layout = QVBoxLayout()
        view_layout.setSpacing(10)
        
        drawing_icon = self.load_icon("drawing.svg")
        self.plan_btn = ActionButton("Read Drawing", drawing_icon)
        self.plan_btn.clicked.connect(lambda: self.emit_action("read_drawing"))
        
        view_layout.addWidget(self.plan_btn)
        #view_layout.addWidget(self.matrix_btn)
        view_group.setLayout(view_layout)
        
        # Data processing section
        data_group = QGroupBox("Data Processing")
        data_group.setStyleSheet(self.get_section_style())
        data_layout = QVBoxLayout()
        data_layout.setSpacing(10)
        
        process_icon = self.load_icon("read.svg")
        database_icon = self.load_icon("upload_database.svg")
        
        # Unified data processing button
        self.process_btn = ActionButton("Process Data", process_icon)
        self.update_btn = ActionButton("Update Database", database_icon)
        
        self.process_btn.clicked.connect(lambda: self.emit_action("process_data"))
        self.update_btn.clicked.connect(lambda: self.emit_action("update_db"))
        
        data_layout.addWidget(self.process_btn)
        data_layout.addWidget(self.update_btn)
        data_group.setLayout(data_layout)
        
        # Add all sections to main layout
        layout.addWidget(analysis_group)
        layout.addWidget(view_group)
        layout.addWidget(data_group)
        layout.addStretch()
        
        self.setLayout(layout)
        logger.debug("[LeftPanel] UI setup complete")
    
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
            logger.debug(f"[LeftPanel] Loaded icon: {icon_path}")
            return QIcon(icon_path)
        else:
            logger.warning(f"[LeftPanel] Icon not found: {icon_path}")
            return None  # return empty icon instead of None
        
    def emit_action(self, action_name):
        logger.debug(f"[LeftPanel] Action requested: {action_name}")
        self.action_requested.emit(action_name)
