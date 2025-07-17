# src/gui/main_window.py
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
)
#from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QThread
from .panels.header import HeaderPanel
from .panels.left_panel import LeftPanel
from .panels.center_panel import CenterPanel
from .panels.right_panel import RightPanel
from .panels.status_bar import StatusBar
from .utils.styles import global_style

# Configure logging
from src.gui.logging_config import logger

from src.services.data_processing_orchestrator import DataProcessingOrchestrator
from src.services.database_update import update_database
from src.gui.workers.capability_study_worker import CapabilityStudyWorker
#from src.services.capacity_study_service import perform_capability_study
from src.gui.widgets.element_input_widget import ElementInputWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Management System")
        self.setup_window()
        self.init_ui()
        self.setStyleSheet(global_style())

    def setup_window(self):
        """Setup window size and position"""
        screen = QApplication.primaryScreen().availableGeometry()

        # Set minimum size
        self.setMinimumSize(1000, 700)

        # Try to maximize window, with fallback
        try:
            self.setWindowState(Qt.WindowMaximized)
            logger.info("Window maximized successfully")
        except AttributeError as e:
            logger.warning(f"Failed to maximize window: {e}")
            # Fallback to 80% of screen size
            width = int(screen.width() * 0.8)
            height = int(screen.height() * 0.8)
            self.resize(width, height)
            # Center the window
            self.move((screen.width() - width) // 2, (screen.height() - height) // 2)
            logger.info(f"Window resized to {width}x{height} and centered")

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        self.header = HeaderPanel()
        self.header.search_requested.connect(self.handle_search)

        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left panel (1/4 width)
        self.left_panel = LeftPanel()
        self.left_panel.action_requested.connect(self.handle_action)

        # Center panel (1/2 width)
        self.center_panel = CenterPanel()

        # Right panel (1/4 width)
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

        logger.info("UI initialized successfully")

    def handle_search(self, criteria):
        """Handle search requests from header panel"""
        try:
            self.status_bar.update_status(f"Searching: {criteria}")
            self.center_panel.update_content(f"Search results for: {criteria}")
            logger.info(f"Search performed with criteria: {criteria}")
        except Exception as e:
            logger.error(f"Error in handle_search: {e}")
            self.show_error_message(
                "Search Error", f"Failed to perform search: {str(e)}"
            )

    def handle_action(self, action_name):
        """Handle action requests from panels"""
        try:
            self.status_bar.update_status(f"Action: {action_name}")
            self.center_panel.update_content(f"Performing: {action_name}")
            logger.info(f"Action requested: {action_name}")

            # Use a timer to allow UI to update before running potentially long operations
            QTimer.singleShot(100, lambda: self._execute_action(action_name))

        except Exception as e:
            logger.error(f"Error in handle_action: {e}")
            self.show_error_message(
                "Action Error", f"Failed to handle action: {str(e)}"
            )

    def _execute_action(self, action_name):
        """Execute the requested action"""
        try:
            if action_name == "dimensional":
                self._run_dimensional_analysis()

            elif action_name == "capacity":
                self._run_capacity_analysis()

            elif action_name == "process_data":
                self._process_data()

            elif action_name == "update_db":
                self._update_database()

            else:
                logger.warning(f"Unknown action: {action_name}")
                self.center_panel.update_content(f"Unknown action: {action_name}")

        except ImportError as e:
            error_msg = f"Module not found: {str(e)}"
            logger.error(error_msg)
            self.center_panel.update_content(error_msg)
            self.status_bar.update_status("Error: Module not found")

        except Exception as e:
            error_msg = f"Error performing action '{action_name}': {str(e)}"
            logger.error(error_msg)
            self.center_panel.update_content(error_msg)
            self.status_bar.update_status(f"Error: {str(e)}")

    def _run_dimensional_analysis(self):
        """Run dimensional analysis"""
        from src.models.dimensional.dimensional_analyzer import run_analysis

        result = run_analysis()
        self.center_panel.update_content(f"Dimensional Analysis Results:\n\n{result}")
        self.status_bar.update_status("Dimensional analysis completed")

    def _run_capacity_analysis(self):
        """Create and show the element input widget with proper signal connection"""
        self.element_input_widget = ElementInputWidget()
        # Connect the widget's study_requested signal to our handler
        self.element_input_widget.study_requested.connect(self.run_capacity_study_with_elements)
        
        self.center_panel.show_custom_widget(self.element_input_widget)
        self.status_bar.update_status("Introduïu dades per l'estudi de capacitat")

    def run_capacity_study_with_elements(self, elements):
        """Run capacity study with the provided elements using a worker thread"""
        try:
            client = self.header.ref_client_edit.text().strip()
            ref_project = self.header.ref_project_edit.text().strip()

            if not client or not ref_project:
                QMessageBox.critical(
                    self,
                    "Missing Info",
                    "Client i Project Reference són obligatoris.",
                    QMessageBox.Ok,
                )
                return

            # Show status
            self.status_bar.update_status("Executant estudi de capacitat...")
            self.center_panel.update_content("⏳ Executant estudi de capacitat...\n\nAixò pot trigar uns moments.")

            # Create worker thread
            self.worker_thread = QThread()
            self.worker = CapabilityStudyWorker(client, ref_project, elements)
            self.worker.moveToThread(self.worker_thread)

            # Connect signals
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_study_finished)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            # Start the worker
            self.worker_thread.start()

        except Exception as e:
            self.status_bar.update_status(f"Error a l'estudi: {e}")
            self.center_panel.update_content(f"❌ Error a l'estudi de capacitat: {e}")
            logger.error(f"Error a l'estudi de capacitat: {e}")

    def on_study_finished(self, result):
        """Handle completion of capacity study"""
        self.center_panel.reset_to_text_view()
        self.center_panel.update_content(f"✅ Estudi de capacitat finalitzat!\n\n{result}")
        self.status_bar.update_status("Estudi de capacitat completat")

    def _process_data(self):
        """Process data files"""
        client = self.header.ref_client_edit.text().strip()
        ref_project = self.header.ref_project_edit.text().strip()

        if not client or not ref_project:
            QMessageBox.critical(
                self,
                "Missing Info",
                "Please enter both Client and Project Reference",
                QMessageBox.Ok,
            )
            return

        orchestrator = DataProcessingOrchestrator()
        result, msg = orchestrator.process_and_transform(client, ref_project)

        if result:
            self.center_panel.update_content("✅ Data processed and transformed!")
            self.status_bar.update_status("Processing completed")
        else:
            self.center_panel.update_content(f"❌ {msg}")
            self.status_bar.update_status("Processing error")

    def _update_database(self):
        client = self.header.ref_client_edit.text().strip()
        ref_project = self.header.ref_project_edit.text().strip()

        if not client or not ref_project:
            self.status_bar.update_status("Client and Project Reference are required to update database.")
            return

        success = update_database(client, ref_project)

        if success:
            self.center_panel.update_content("Database update completed successfully!")
            self.status_bar.update_status("Processing completed")
        else:
            self.center_panel.update_content("Database update failed. Check logs for details.")
            self.status_bar.update_status("Processing error")

    def show_error_message(self, title, message):
        """Show error message dialog"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("Application closing")
        event.accept()


# Application runner
def run_app():
    """Run the application"""
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))

        # Set application properties
        app.setApplicationName("Database Management System")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Your Organization")

        window = MainWindow()
        window.show()

        logger.info("Application started successfully")
        return app.exec_()

    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_app())