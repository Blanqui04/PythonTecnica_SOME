# ---------- Llibreries
import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QLineEdit,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem, QSizePolicy,
                             QFrame, QGroupBox, QTextEdit, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QIcon
# ---------- Classes
from connexio_bbdd import PostgresConn
# ---------- Funcions
from kop_csv import main as l_kop, set_global_parameters, get_processor_status
from csv_func import main as l_csv
from to_sql import main as act_bbdd
from from_sql import cerca_ecap, cerca_dim
from e_cap import main as e_cap
from dim import main as dim
# ---------- Variables
dir_images = os.path.join(os.path.dirname(__file__), "ui_images")

class ModernButton(QPushButton):
    """Custom modern button with hover effects"""
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setMinimumHeight(50)
        self.setFont(QFont("Segoe UI", 11, QFont.Medium))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyle()
        
    def setStyle(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                    border-color: #bbb;
                }
                QPushButton:pressed {
                    background-color: #d8d8d8;
                }
            """)

class ModernLineEdit(QLineEdit):
    """Custom modern line edit with better styling"""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #c0c0c0;
            }
        """)

class DatabaseUI(QWidget):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Management System")
        
        # Initialize search variables that can be accessed throughout the application
        self.ref_project = ""
        self.client = ""
        self.num_oferta = ""
        self.num_lot = ""
        
        self.setup_window()
        self.init_ui()
        self.apply_global_styles()

    def setup_window(self):
        # Detect screen size and set window size
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        
        # Set window to 85% of screen size for better visibility
        win_width = int(screen_width * 0.85)
        win_height = int(screen_height * 0.85)
        self.resize(win_width, win_height)
        
        # Center the window
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        self.move(x, y)
        
        # Set minimum size
        self.setMinimumSize(1000, 700)

    def apply_global_styles(self):
        """Apply global styles to the application"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                color: #212529;
            }
            QLabel {
                color: #495057;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #495057;
            }
        """)

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left panel - Actions
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Center panel - Visualizer
        center_panel = self.create_center_panel()
        content_layout.addWidget(center_panel, 2)
        
        # Right panel - Edit actions
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(content_layout)
        
        # Status bar
        status_layout = self.create_status_bar()
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)

    def create_header(self):
        """Create the header section with logo and search"""
        header_layout = QVBoxLayout()
        
        # Top row with logo and title
        top_row = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(dir_images, "logo_some.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaledToHeight(60, Qt.SmoothTransformation))
        else:
            logo_label.setText("LOGO")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d4;")
        
        # Title
        title_label = QLabel("Database Management System")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #212529; margin-left: 20px;")
        
        top_row.addWidget(logo_label)
        top_row.addWidget(title_label)
        top_row.addStretch()
        
        # Search section
        search_group = QGroupBox("Search & Filter")
        search_layout = QGridLayout()
        
        # Search fields
        self.num_oferta_edit = ModernLineEdit("Número d'Oferta")
        self.ref_client_edit = ModernLineEdit("Referència Client")
        self.num_lot_edit = ModernLineEdit("Número de Lot")
        self.ref_project_edit = ModernLineEdit("Referència Projecte")
        
        # Search button
        search_btn = ModernButton("🔍 Cercar", primary=True)
        search_btn.clicked.connect(self.perform_search)
        
        # Clear button
        clear_btn = ModernButton("🗑️ Netejar")
        clear_btn.clicked.connect(self.clear_search)
        
        # Layout search fields
        search_layout.addWidget(QLabel("Num. Oferta:"), 0, 0)
        search_layout.addWidget(self.num_oferta_edit, 0, 1)
        search_layout.addWidget(QLabel("Ref. Client:"), 0, 2)
        search_layout.addWidget(self.ref_client_edit, 0, 3)
        
        search_layout.addWidget(QLabel("Num. Lot:"), 1, 0)
        search_layout.addWidget(self.num_lot_edit, 1, 1)
        search_layout.addWidget(QLabel("Ref. Projecte:"), 1, 2)
        search_layout.addWidget(self.ref_project_edit, 1, 3)
        
        search_layout.addWidget(search_btn, 0, 4, 2, 1)
        search_layout.addWidget(clear_btn, 0, 5, 2, 1)
        
        search_group.setLayout(search_layout)
        
        # Result info
        self.result_info = QLabel("Ready to search...")
        self.result_info.setStyleSheet("color: #6c757d; font-style: italic; margin-top: 10px;")
        
        header_layout.addLayout(top_row)
        header_layout.addWidget(search_group)
        header_layout.addWidget(self.result_info)
        
        return header_layout

    def create_left_panel(self):
        """Create left panel with main actions"""
        left_group = QGroupBox("Main Actions")
        left_layout = QVBoxLayout()
        
        # Analysis buttons
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout()
        
        dimensional_btn = ModernButton("📊 Estudi Dimensional")
        dimensional_btn.clicked.connect(self.accio_dimensional)
        analysis_layout.addWidget(dimensional_btn)
        
        capacity_btn = ModernButton("📈 Estudi de Capacitat")
        capacity_btn.clicked.connect(self.accio_capacitat)
        analysis_layout.addWidget(capacity_btn)
        
        analysis_group.setLayout(analysis_layout)
        left_layout.addWidget(analysis_group)
        
        # View buttons
        view_group = QGroupBox("View")
        view_layout = QVBoxLayout()
        
        plan_btn = ModernButton("🗺️ Veure Plànol")
        plan_btn.clicked.connect(self.accio_planol)
        view_layout.addWidget(plan_btn)
        
        matrix_btn = ModernButton("🔢 Veure Matriu")
        matrix_btn.clicked.connect(self.accio_matriu)
        view_layout.addWidget(matrix_btn)
        
        view_group.setLayout(view_layout)
        left_layout.addWidget(view_group)
        
        # Data processing buttons
        data_group = QGroupBox("Data Processing")
        data_layout = QVBoxLayout()
        
        kop_btn = ModernButton("📋 Llegir KOP")
        kop_btn.clicked.connect(self.llegir_kop)
        data_layout.addWidget(kop_btn)
        
        csv_btn = ModernButton("📄 Processar CSV")
        csv_btn.clicked.connect(self.processar_csv)
        data_layout.addWidget(csv_btn)
        
        update_btn = ModernButton("🔄 Actualitzar B.B.D.D.")
        update_btn.clicked.connect(self.actualitzar_bbdd)
        data_layout.addWidget(update_btn)
        
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)
        
        left_layout.addStretch()
        left_group.setLayout(left_layout)
        
        return left_group

    def create_center_panel(self):
        """Create center panel with visualizer"""
        center_group = QGroupBox("Visualizer")
        center_layout = QVBoxLayout()
        
        # Create a scroll area for the visualizer
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        # Main visualizer widget
        self.visualizer = QTextEdit()
        self.visualizer.setReadOnly(True)
        self.visualizer.setPlainText("Welcome to Database Management System\n\n" +
                                   "Use the search fields above to find data.\n" +
                                   "Select actions from the side panels to process data.\n\n" +
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
        center_layout.addWidget(scroll_area)
        
        center_group.setLayout(center_layout)
        return center_group

    def create_right_panel(self):
        """Create right panel with edit actions"""
        right_group = QGroupBox("Edit Actions")
        right_layout = QVBoxLayout()
        
        # Edit buttons
        edit_group = QGroupBox("Edit")
        edit_layout = QVBoxLayout()
        
        edit_dim_btn = ModernButton("✏️ Editar Dimensional")
        edit_dim_btn.clicked.connect(self.editar_dimensional)
        edit_layout.addWidget(edit_dim_btn)
        
        edit_study_btn = ModernButton("✏️ Editar Estudi")
        edit_study_btn.clicked.connect(self.editar_estudi)
        edit_layout.addWidget(edit_study_btn)
        
        edit_group.setLayout(edit_layout)
        right_layout.addWidget(edit_group)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        open_plan_btn = ModernButton("📂 Obrir Plànol")
        open_plan_btn.clicked.connect(self.obrir_planol)
        file_layout.addWidget(open_plan_btn)
        
        open_folder_btn = ModernButton("📁 Obrir Carpeta")
        open_folder_btn.clicked.connect(self.obrir_carpeta)
        file_layout.addWidget(open_folder_btn)
        
        file_group.setLayout(file_layout)
        right_layout.addWidget(file_group)
        
        # Additional actions
        additional_group = QGroupBox("Additional")
        additional_layout = QVBoxLayout()
        
        export_btn = ModernButton("📤 Exportar Dades")
        export_btn.clicked.connect(self.exportar_dades)
        additional_layout.addWidget(export_btn)
        
        import_btn = ModernButton("📥 Importar Dades")
        import_btn.clicked.connect(self.importar_dades)
        additional_layout.addWidget(import_btn)
        
        additional_group.setLayout(additional_layout)
        right_layout.addWidget(additional_group)
        
        right_layout.addStretch()
        right_group.setLayout(right_layout)
        
        return right_group

    def create_status_bar(self):
        """Create status bar"""
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                padding: 8px 12px;
                border-radius: 4px;
                color: #495057;
            }
        """)
        
        connection_status = QLabel("🟢 Database Connected")
        connection_status.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                padding: 8px 12px;
                border-radius: 4px;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(connection_status)
        
        return status_layout

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.setText(message)

    def update_visualizer(self, content):
        """Update visualizer content"""
        self.visualizer.setPlainText(content)

    # Search functionality
    def perform_search(self):
        """Perform search based on input fields"""
        # Update class variables with current search values
        self.num_oferta = self.num_oferta_edit.text().strip()
        self.client = self.ref_client_edit.text().strip()
        self.num_lot = self.num_lot_edit.text().strip()
        self.ref_project = self.ref_project_edit.text().strip()
        
        # Create search criteria
        search_criteria = []
        if self.num_oferta:
            search_criteria.append(f"Num. Oferta: {self.num_oferta}")
        if self.client:
            search_criteria.append(f"Client: {self.client}")
        if self.num_lot:
            search_criteria.append(f"Num. Lot: {self.num_lot}")
        if self.ref_project:
            search_criteria.append(f"Ref. Projecte: {self.ref_project}")
        
        if search_criteria:
            self.update_status("Searching...")
            search_text = "Search criteria:\n" + "\n".join(search_criteria)
            self.update_visualizer(search_text + "\n\nSearching database...")
            self.result_info.setText(f"Searching with {len(search_criteria)} criteria...")
            
            # Here you would implement actual database search
            # For now, we'll simulate the search
            self.simulate_search()
        else:
            self.show_warning("Please enter at least one search criterion.")

    def simulate_search(self):
        """Simulate database search (replace with actual implementation)"""
        # This is where you would call your database search functions
        # For example: cerca_ecap(self.num_oferta), cerca_dim(self.client), etc.
        
        result_text = f"""Search Results:
        
Num. Oferta: {self.num_oferta or 'N/A'}
Client: {self.client or 'N/A'}
Num. Lot: {self.num_lot or 'N/A'}
Ref. Projecte: {self.ref_project or 'N/A'}

[Search results would appear here]
        """
        
        self.update_visualizer(result_text)
        self.update_status("Search completed")
        self.result_info.setText("Search completed successfully")

    def get_search_variables(self):
        """Get current search variables as a dictionary"""
        return {
            'ref_project': self.ref_project,
            'client': self.client,
            'num_oferta': self.num_oferta,
            'num_lot': self.num_lot
        }

    def clear_search(self):
        """Clear all search fields"""
        self.num_oferta_edit.clear()
        self.ref_client_edit.clear()
        self.num_lot_edit.clear()
        self.ref_project_edit.clear()
        self.result_info.setText("Search fields cleared")
        self.update_visualizer("Search fields cleared. Ready for new search.")

    # Action methods
    def accio_dimensional(self):
        """Execute dimensional analysis"""
        self.update_status("Executing dimensional analysis...")
        self.update_visualizer("Dimensional Analysis\n\nExecuting dimensional study...")
        try:
            # Call your dimensional analysis function with current search parameters
            # Pass the search variables if your function needs them
            result = dim()  # You can pass parameters like: dim(self.ref_project, self.client)
            self.update_visualizer(f"Dimensional Analysis Results:\n\n{result}")
        except Exception as e:
            self.show_error(f"Error in dimensional analysis: {str(e)}")
        finally:
            self.update_status("Ready")

    def accio_capacitat(self):
        """Execute capacity study"""
        self.update_status("Executing capacity study...")
        self.update_visualizer("Capacity Study\n\nExecuting capacity analysis...")
        try:
            # Call your capacity study function without creating new event loop
            # Pass the current search parameters if needed
            result = e_cap()  # Your function should not call app.exec_()
            self.update_visualizer(f"Capacity Study Results:\n\n{result}")
        except Exception as e:
            self.show_error(f"Error in capacity study: {str(e)}")
        finally:
            self.update_status("Ready")

    def accio_planol(self):
        """View plan"""
        self.update_status("Opening plan view...")
        self.update_visualizer("Plan View\n\nOpening plan visualization...")

    def accio_matriu(self):
        """View matrix"""
        self.update_status("Opening matrix view...")
        self.update_visualizer("Matrix View\n\nOpening matrix visualization...")

    def llegir_kop(self):
        """Read KOP file with current search parameters"""
        if not self.client or not self.ref_project:
            self.show_warning("Please fill in 'Client' and 'Ref. Projecte' fields before reading KOP file.")
            return
        
        self.update_status("Reading KOP file...")
        self.update_visualizer(f"KOP Reader\n\nReading KOP file for:\nClient: {self.client}\nProject: {self.ref_project}\n\nProcessing...")
        
        try:
            # Set global parameters for the KOP processor
            set_global_parameters(self.client, self.ref_project)
            
            # Call the KOP processor with current search parameters
            result_path, result_msg = l_kop(self.client, self.ref_project)
            
            if result_path:
                success_msg = f"KOP Processing Completed Successfully!\n\n{result_msg}\n\nDatasheet saved to: {result_path}"
                self.update_visualizer(success_msg)
                self.update_status("KOP processing completed")
            else:
                self.update_visualizer(f"KOP Processing Failed:\n\n{result_msg}")
                self.update_status("KOP processing failed")
                
        except Exception as e:
            error_msg = f"Error reading KOP: {str(e)}"
            self.show_error(error_msg)
            self.update_visualizer(f"KOP Processing Error:\n\n{error_msg}")
            self.update_status("KOP processing error")

    def processar_csv(self):
        """Process CSV file"""
        self.update_status("Processing CSV...")
        self.update_visualizer("CSV Processor\n\nProcessing CSV file...")
        try:
            result = l_csv()
            self.update_visualizer(f"CSV Processing Results:\n\n{result}")
        except Exception as e:
            self.show_error(f"Error processing CSV: {str(e)}")
        finally:
            self.update_status("Ready")

    def actualitzar_bbdd(self):
        """Update database"""
        self.update_status("Updating database...")
        self.update_visualizer("Database Update\n\nUpdating database...")
        try:
            result = act_bbdd()
            self.update_visualizer(f"Database Update Results:\n\n{result}")
        except Exception as e:
            self.show_error(f"Error updating database: {str(e)}")
        finally:
            self.update_status("Ready")

    # Edit actions
    def editar_dimensional(self):
        """Edit dimensional data"""
        self.update_status("Opening dimensional editor...")
        self.update_visualizer("Dimensional Editor\n\nOpening dimensional data editor...")

    def editar_estudi(self):
        """Edit study data"""
        self.update_status("Opening study editor...")
        self.update_visualizer("Study Editor\n\nOpening study data editor...")

    def obrir_planol(self):
        """Open plan file"""
        if not self.client or not self.ref_project:
            self.show_warning("Please fill in 'Client' and 'Ref. Projecte' fields first to open plan files.")
            return
            
        self.update_status("Opening plan file...")
        self.update_visualizer(f"Plan File\n\nOpening plan file for:\nClient: {self.client}\nProject: {self.ref_project}")
        
        # Here you would implement the logic to open plan files based on client and project
        # For example: open_plan_file(self.client, self.ref_project)
        
    def obrir_carpeta(self):
        """Open folder"""
        if not self.client or not self.ref_project:
            self.show_warning("Please fill in 'Client' and 'Ref. Projecte' fields first to open project folder.")
            return
            
        self.update_status("Opening project folder...")
        self.update_visualizer(f"Project Folder\n\nOpening project folder for:\nClient: {self.client}\nProject: {self.ref_project}")
        
        # Here you would implement the logic to open project folders based on client and project
        # For example: open_project_folder(self.client, self.ref_project)

    def exportar_dades(self):
        """Export data - Export current project data to various formats"""
        self.update_status("Exporting data...")
        export_info = """Data Export

Purpose: Export current project data to various formats such as:
- Excel (.xlsx) - For spreadsheet analysis
- CSV (.csv) - For data interchange
- PDF (.pdf) - For reports and documentation
- JSON (.json) - For data backup and API integration

This function allows you to save your analysis results, dimensional studies, 
capacity studies, and other project data in different formats for external use, 
sharing with clients, or archiving purposes.
"""
        self.update_visualizer(export_info)

    def importar_dades(self):
        """Import data - Import data from external sources into the database"""
        self.update_status("Importing data...")
        import_info = """Data Import

Purpose: Import data from external sources into the database such as:
- Excel files (.xlsx, .xls) - Import measurement data, specifications
- CSV files (.csv) - Import structured data from other systems
- KOP files - Import machine/equipment data
- Database files - Import from other database systems

This function allows you to:
1. Import new project data from external sources
2. Update existing records with new information
3. Batch import multiple files at once
4. Validate data before importing to ensure data integrity
5. Map columns from external files to database fields

The imported data will be processed and integrated into your current database 
structure for analysis and reporting.
"""
        self.update_visualizer(import_info)

    # Utility methods
    def show_warning(self, message):
        """Show warning message"""
        QMessageBox.warning(self, "Warning", message)

    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        """Show info message"""
        QMessageBox.information(self, "Information", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = DatabaseUI()
    window.show()
    
    sys.exit(app.exec_())
