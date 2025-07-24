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

# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton
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

# from src.services.capacity_study_service import perform_capability_study
from src.gui.widgets.element_input_widget import ElementInputWidget
from .windows.spc_chart_window import SPCChartWindow
from .windows.dimensional_window import DimensionalStudyWindow



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Management System")
        self.last_analysis_action = None  # Track the last analysis action performed
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

        content_layout.addWidget(self.left_panel, 2)
        content_layout.addWidget(self.center_panel, 5)
        content_layout.addWidget(self.right_panel, 2)

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
                self.last_analysis_action = "dimensional"
                self._run_dimensional_analysis()

            elif action_name == "capacity":
                self.last_analysis_action = "capacity"
                self._run_capacity_analysis()

            elif action_name == "process_data":
                self._process_data()

            elif action_name == "update_db":
                self._update_database()

            elif action_name == "read_drawing":
                self._read_drawing()

            elif action_name == "view_drawing":
                self._view_drawing()

            elif action_name == "export_data":
                self._export_data()

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
        self.dimensional_window = DimensionalStudyWindow(
            client = self.header.ref_client_edit.text().strip(),
            ref_project = self.header.ref_project_edit.text().strip(),
            batch_number = self.header.num_batch_edit.text().strip()
        )
        self.dimensional_window.showMaximized()


    def _run_capacity_analysis(self):
        self.element_input_widget = ElementInputWidget()
        self.element_input_widget.study_requested.connect(
            self.run_capacity_study_with_elements
        )
        self.center_panel.show_custom_widget(self.element_input_widget)
        self.status_bar.update_status("Introduïu dades per l'estudi de capacitat")

    def run_capacity_study_with_elements(self, elements, extrap_config):
        try:
            client = self.header.ref_client_edit.text().strip()
            ref_project = self.header.ref_project_edit.text().strip()
            batch_number = self.header.num_batch_edit.text().strip()

            if not client or not ref_project or not batch_number:
                QMessageBox.critical(
                    self,
                    "Missing Info",
                    "Client, Project Reference and Batch number són obligatoris.",
                    QMessageBox.Ok,
                )
                return

            self.status_bar.update_status("Executant estudi de capacitat...")
            self.center_panel.update_content(
                f"⏳ Executant estudi de capacitat...\n\nBatch: {batch_number if batch_number else 'N/A'}"
            )

            self.worker_thread = QThread()
            self.worker = CapabilityStudyWorker(
                client, ref_project, elements, extrap_config, batch_number=batch_number
            )
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_study_finished)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()

        except Exception as e:
            self.status_bar.update_status(f"Error a l'estudi: {e}")
            self.center_panel.update_content(f"❌ Error a l'estudi de capacitat: {e}")
            logger.error(f"Error a l'estudi de capacitat: {e}")

    # Replace your existing on_study_finished method with this:
    def on_study_finished(self, result):
        """Handle capability study completion"""
        # Update center panel with completion message
        self.center_panel.reset_to_text_view()
        self.center_panel.update_content(
            f"✅ Estudi de capacitat finalitzat!\n\n{result}"
        )
        self.status_bar.update_status("Estudi de capacitat completat")
        
        try:
            # Get client and project info from header
            client = self.header.ref_client_edit.text().strip()
            ref_project = self.header.ref_project_edit.text().strip()
            batch_number = self.header.num_batch_edit.text().strip()
            
            if not client or not ref_project or not batch_number:
                logger.warning("Client or project information missing, cannot display charts")
                return
                
            # Create and show chart window
            logger.info(f"Opening SPC charts for study: {ref_project}_{batch_number}")
            self.chart_window = SPCChartWindow(client, ref_project, batch_number, parent=self)
            self.chart_window.show()
            
        except Exception as e:
            logger.error(f"Error opening SPC charts: {e}")
            # Show error message to user
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Error", 
                f"No s'han pogut mostrar els gràfics SPC:\n\n{str(e)}"
            )

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
        
        # Determinar el mode segons el client
        mode = 'kop'  # Mode per defecte
        if client.upper() == 'ZF':
            mode = 'zf'  # Mode específic per ZF
        
        result, msg = orchestrator.process_and_transform(client, ref_project, mode)

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
            self.status_bar.update_status(
                "Client and Project Reference are required to update database."
            )
            return

        success = update_database(client, ref_project)

        if success:
            self.center_panel.update_content("Database update completed successfully!")
            self.status_bar.update_status("Processing completed")
        else:
            self.center_panel.update_content(
                "Database update failed. Check logs for details."
            )
            self.status_bar.update_status("Processing error")

    def _read_drawing(self):
        """Read and save drawing PDFs from server to database"""
        try:
            # Get client and project info
            client = self.header.ref_client_edit.text().strip()
            project_id = self.header.ref_project_edit.text().strip()
            
            if not client or not project_id:
                self.center_panel.update_content(
                    "❌ Falten dades\n\n"
                    "Si us plau, introdueix:\n"
                    "• Nom del Client (No Client)\n"
                    "• ID del Projecte\n\n"
                    "Aquestes dades són necessàries per buscar els dibuixos al servidor."
                )
                self.status_bar.update_status("Missing client or project data")
                return
            
            # Import here to avoid circular imports
            from src.services.drawing_pdf_reader import DrawingPDFReader
            
            # Update UI to show processing
            self.center_panel.update_content(
                f"🔍 Buscant dibuixos...\n\n"
                f"Client: {client}\n"
                f"Projecte: {project_id}\n\n"
                f"Cercant al servidor: \\\\server.some.local\\Projectes en curs\n"
                f"Carpeta: {client}\\{project_id} - ...\\2-PART TECHNICAL INFO\\1-CUSTOMER PART DRAWINGS\n\n"
                f"Si us plau, espera..."
            )
            self.status_bar.update_status("Reading drawings from server...")
            
            # Process in background (this could be moved to a thread for better UX)
            reader = DrawingPDFReader(client, project_id)
            result = reader.read_and_save_drawings()
            
            # Update UI with results
            if result['success']:
                message = (
                    f"✅ Dibuixos processats correctament\n\n"
                    f"Client: {client}\n"
                    f"Projecte: {project_id}\n\n"
                    f"📊 Resum:\n"
                    f"• PDFs trobats: {result['pdfs_found']}\n"
                    f"• PDFs guardats/actualitzats: {result['pdfs_saved']}\n\n"
                )
                
                if result.get('pdf_list'):
                    message += "📄 Fitxers processats:\n"
                    for pdf_name in result['pdf_list']:
                        message += f"• {pdf_name}\n"
                
                message += f"\n{result['message']}"
                
                self.center_panel.update_content(message)
                self.status_bar.update_status("Drawings processed successfully")
                logger.info(f"Successfully processed {result['pdfs_saved']} drawings for {client}/{project_id}")
            else:
                error_message = (
                    f"❌ Error processant dibuixos\n\n"
                    f"Client: {client}\n"
                    f"Projecte: {project_id}\n\n"
                    f"Error: {result['error']}\n\n"
                    f"Comprova:\n"
                    f"• Connexió al servidor \\\\server.some.local\\Projectes en curs\n"
                    f"• Que existeixi la carpeta del client '{client}'\n"
                    f"• Que existeixi la carpeta del projecte que comenci per '{project_id}'\n"
                    f"• Que existeixi la subcarpeta '2-PART TECHNICAL INFO\\1-CUSTOMER PART DRAWINGS'\n"
                    f"• Que hi hagi fitxers PDF amb el format adequat"
                )
                
                self.center_panel.update_content(error_message)
                self.status_bar.update_status("Error reading drawings")
                logger.error(f"Error processing drawings for {client}/{project_id}: {result['error']}")
            
        except Exception as e:
            logger.error(f"Error in _read_drawing: {e}")
            self.center_panel.update_content(
                f"❌ Error inesperat\n\n"
                f"Error: {str(e)}\n\n"
                f"Consulta els logs per més detalls."
            )
            self.status_bar.update_status("Unexpected error")

    def _view_drawing(self):
        """Toggle view between text and PDF drawing mode"""
        try:
            self.center_panel.toggle_view_mode()
            self.status_bar.update_status("Toggled drawing view")
            logger.info("View drawing action triggered - toggled view mode")
        except Exception as e:
            logger.error(f"Error in view drawing: {e}")
            self.center_panel.update_content(f"Error toggling view: {str(e)}")
            self.status_bar.update_status("Error toggling view")

    def _export_data(self):
        """Export data based on current project reference and last analysis action"""
        try:
            # Get project reference from header
            ref_project = self.header.ref_project_edit.text().strip()
            client = self.header.ref_client_edit.text().strip()
            
            if not ref_project:
                self.center_panel.update_content("Please enter Project Reference to export data.")
                self.status_bar.update_status("Export failed: No project reference")
                return
            
            if not self.last_analysis_action:
                self.center_panel.update_content("Please run an analysis (Dimensional Study or Capacity Study) before exporting data.")
                self.status_bar.update_status("Export failed: No analysis performed")
                return
            
            # Import here to avoid circular imports
            from src.services.data_export_service import export_analysis_data
            
            # Export data based on the last analysis action
            export_result = export_analysis_data(
                analysis_type=self.last_analysis_action,
                ref_project=ref_project,
                client=client
            )
            
            if export_result['success']:
                self.center_panel.update_content(
                    f"✅ Data Export Successful!\n\n"
                    f"Analysis Type: {self.last_analysis_action.title()} Study\n"
                    f"Project Reference: {ref_project}\n"
                    f"Client: {client if client else 'N/A'}\n"
                    f"Export File: {export_result['filename']}\n"
                    f"File Path: {export_result['filepath']}\n"
                    f"Records Exported: {export_result.get('records_count', 'N/A')}\n\n"
                    f"The file has been saved and is ready for use."
                )
                self.status_bar.update_status(f"Export completed: {export_result['filename']}")
                logger.info(f"Data export successful: {export_result['filename']}")
            else:
                self.center_panel.update_content(
                    f"❌ Data Export Failed\n\n"
                    f"Analysis Type: {self.last_analysis_action.title()} Study\n"
                    f"Project Reference: {ref_project}\n"
                    f"Error: {export_result['error']}\n\n"
                    f"Please check the logs for more details."
                )
                self.status_bar.update_status("Export failed")
                logger.error(f"Data export failed: {export_result['error']}")
                
        except Exception as e:
            error_msg = f"Error during data export: {str(e)}"
            logger.error(error_msg)
            self.center_panel.update_content(f"❌ Export Error\n\n{error_msg}")
            self.status_bar.update_status("Export error")

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
