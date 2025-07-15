from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QScrollArea

class CenterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Visualizer", parent)
        self.setup_ui()
        
    def setup_ui(self):
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
        
    def update_content(self, content):
        self.visualizer.setPlainText(content)