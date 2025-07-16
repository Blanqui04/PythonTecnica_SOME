from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.gui.logging_config import logger

class StatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing [StatusBar]")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                padding: 8px 12px;
                border-radius: 4px;
                color: #495057;
            }
        """)
        
        self.connection_status = QLabel("🟢 Database Connected")
        self.connection_status.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                padding: 8px 12px;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.connection_status)
        
        self.setLayout(layout)
        logger.debug("[StatusBar] UI setup completed")
        
    def update_status(self, message):
        logger.info(f"Updating status message: {message}")
        self.status_label.setText(message)
