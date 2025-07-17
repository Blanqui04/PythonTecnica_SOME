# src/gui/panels/center_panel.py
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QTextEdit, QScrollArea, QWidget, QStackedLayout
)
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

        self.stacked_layout = QStackedLayout()

        # Mode 1: Text view (default)
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.text_widget.setPlainText("Welcome to Database Management System\n\n"
                                      "Use the search fields above to find data.\n"
                                      "Select actions from the side panels to process data.\n\n"
                                      "Results and visualizations will appear here.")
        self.text_widget.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                color: #495057;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        text_scroll = QScrollArea()
        text_scroll.setWidgetResizable(True)
        text_scroll.setWidget(self.text_widget)

        # Mode 2: Custom widget view (e.g., interactive form or preview)
        self.custom_widget_container = QWidget()  # Placeholder, can be replaced dynamically

        self.stacked_layout.addWidget(text_scroll)             # index 0
        self.stacked_layout.addWidget(self.custom_widget_container)  # index 1

        layout.addLayout(self.stacked_layout)
        self.setLayout(layout)

    def update_content(self, content: str):
        """Update visualizer text content and switch to text mode."""
        logger.debug(f"Updating content in [CenterPanel]: {content[:60]}{'...' if len(content) > 60 else ''}")
        self.text_widget.setPlainText(content)
        self.stacked_layout.setCurrentIndex(0)
        logger.info("Visualizer content updated")

    def show_custom_widget(self, widget: QWidget):
        """Replace the custom panel and show it"""
        logger.debug("Switching to custom widget view in [CenterPanel]")
        widget.setParent(None)
        self.custom_widget_container = widget

        # Remove old widget (index 1) and add new
        self.stacked_layout.removeWidget(self.stacked_layout.widget(1))
        self.stacked_layout.insertWidget(1, widget)
        self.stacked_layout.setCurrentIndex(1)
        logger.info("Custom widget displayed in [CenterPanel]")

    def reset_to_text_view(self):
        """Return to the normal text display"""
        logger.debug("Returning to text view in [CenterPanel]")
        self.stacked_layout.setCurrentIndex(0)
