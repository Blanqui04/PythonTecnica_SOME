import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QFont
from .panels.header import HeaderPanel
from .panels.left_panel import LeftPanel
from .panels.center_panel import CenterPanel
from .panels.right_panel import RightPanel
from .panels.status_bar import StatusBar
from .utils.styles import global_style

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Management System")
        self.setup_window()
        self.init_ui()
        self.setStyleSheet(global_style())
        
    def setup_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.85), int(screen.height() * 0.85))
        self.setMinimumSize(1000, 700)
        
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        self.header = HeaderPanel()
        self.header.search_requested.connect(self.handle_search)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left panel
        self.left_panel = LeftPanel()
        self.left_panel.action_requested.connect(self.handle_action)
        
        # Center panel
        self.center_panel = CenterPanel()
        
        # Right panel
        self.right_panel = RightPanel()
        self.right_panel.action_requested.connect(self.handle_action)
        
        content_layout.addWidget(self.left_panel, 1)
        content_layout.addWidget(self.center_panel, 2)
        content_layout.addWidget(self.right_panel, 1)
        
        # Status bar
        self.status_bar = StatusBar()
        
        main_layout.addWidget(self.header)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_bar)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
    def handle_search(self, criteria):
        self.status_bar.update_status(f"Searching: {criteria}")
        self.center_panel.update_content(f"Search results for: {criteria}")
        
    def handle_action(self, action_name):
        self.status_bar.update_status(f"Action: {action_name}")
        self.center_panel.update_content(f"Performing: {action_name}")
        
        # Connect to backend modules
        try:
            if action_name == "dimensional":
                from src.models.dimensional.dimensional_analyzer import run_analysis
                result = run_analysis()
                self.center_panel.update_content(f"Dimensional Analysis Results:\n\n{result}")
                
            elif action_name == "capacity":
                from src.models.capability.capability_analyzer import run_analysis
                result = run_analysis()
                self.center_panel.update_content(f"Capacity Study Results:\n\n{result}")
                
            elif action_name == "read_kop":
                from src.data_processing.utils.excel_reader import read_kop_file
                criteria = self.header.get_search_criteria()
                if not criteria.get('client') or not criteria.get('ref_project'):
                    self.center_panel.update_content("Please enter both Client and Project Reference")
                    return
                result = read_kop_file(criteria['client'], criteria['ref_project'])
                self.center_panel.update_content(f"KOP Processing Results:\n\n{result}")
                
            elif action_name == "process_csv":
                from src.data_processing.data_processor import process_csv_files
                result = process_csv_files()
                self.center_panel.update_content(f"CSV Processing Results:\n\n{result}")
                
            elif action_name == "update_db":
                from src.database.database_uploader import update_database
                result = update_database()
                self.center_panel.update_content(f"Database Update Results:\n\n{result}")
                
        except Exception as e:
            self.center_panel.update_content(f"Error performing action: {str(e)}")
            self.status_bar.update_status(f"Error: {str(e)}")

# Application runner
def run_app():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())