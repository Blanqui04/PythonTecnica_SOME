from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QScrollArea

# Import shared logger
from src.gui.logging_config import logger

class CenterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Visualizer", parent)
        logger.debug("Initializing [CenterPanel]")
        self.setup_ui()
        logger.info("[CenterPanel] initialized successfully")

    def setup_ui(self):
        logger.debug("Setting up UI for [CenterPanel]")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        # Create the text edit
        self.visualizer = QTextEdit()
        self.visualizer.setReadOnly(True)
        self.visualizer.setPlainText("Welcome to Database Management System\n\n"
                                     "Use the search fields above to find data.\n"
                                     "Select actions from the side panels to process data.\n\n"
                                     "Results and visualizations will appear here.")
        self.visualizer.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                color: #495057;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                line-height: 1.5;
            }
        """)

        scroll_area.setWidget(self.visualizer)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        logger.debug("UI for [CenterPanel] set up successfully")

    def update_content(self, content):
        logger.debug(f"Updating content in [CenterPanel]: {content[:60]}{'...' if len(content) > 60 else ''}")
        self.visualizer.setPlainText(content)
        logger.info("Visualizer content updated")
