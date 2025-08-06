# src/gui/components/spc_export_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
                             QGroupBox, QProgressBar, QMessageBox, QFrame, QGridLayout)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont

from ...widgets.buttons import ModernButton, ActionButton, CompactButton
from ...widgets.inputs import ModernComboBox, ModernLineEdit
from ...utils.styles import get_color_palette
from src.services.spc_export_service import ExcelReportService
from ...logging_config import logger


class ExcelExportWorker(QThread):
    """Worker thread for Excel export to prevent UI freezing"""
    
    finished = pyqtSignal(bool, str)  # success, result_message
    progress = pyqtSignal(int)        # progress percentage
    status_update = pyqtSignal(str)   # status message

    def __init__(self, service: ExcelReportService, export_config: dict):
        super().__init__()
        self.service = service
        self.config = export_config

    def run(self):
        try:
            self.status_update.emit("Initializing export services...")
            self.progress.emit(10)
            
            # Generate complete report
            success, result = self.service.generate_complete_report(
                part_description=self.config['part_description'],
                drawing_number=self.config['drawing_number'],
                methodology=self.config['methodology'],
                facility=self.config['facility'],
                dimension_class=self.config['dimension_class'],
                generate_charts=self.config['generate_charts'],
                open_file=self.config['open_file']
            )
            
            self.progress.emit(100)
            
            if success:
                self.status_update.emit("Excel report generated successfully!")
                self.finished.emit(True, result)
            else:
                self.status_update.emit("Failed to generate Excel report")
                self.finished.emit(False, result)
                
        except Exception as e:
            logger.error(f"Error in Excel export worker: {e}")
            self.finished.emit(False, str(e))


class ExcelExportDialog(QDialog):
    """
    Professional dialog for configuring Excel SPC report export
    """
    
    def __init__(self, client: str, ref_project: str, batch_number: str, parent=None):
        super().__init__(parent)
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.colors = get_color_palette()
        
        # Initialize service
        self.excel_service = ExcelReportService(
            client=client,
            ref_project=ref_project,
            batch_number=batch_number
        )
        
        self.worker = None
        
        self.setup_ui()
        # self.apply_styles()
        self.load_defaults()

    def setup_ui(self):
        self.setWindowTitle("Export Excel SPC Report")
        self.setModal(True)
        self.resize(650, 700)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Configuration sections
        config_widget = self.create_configuration_section()
        main_layout.addWidget(config_widget)
        
        # Progress section (initially hidden)
        self.progress_widget = self.create_progress_section()
        self.progress_widget.setVisible(False)
        main_layout.addWidget(self.progress_widget)
        
        # Buttons
        buttons_widget = self.create_buttons_section()
        main_layout.addWidget(buttons_widget)
        
        self.setLayout(main_layout)

    def create_header(self):
        """Create the dialog header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_frame.setFixedHeight(100)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title = QLabel("Excel SPC Report Export")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Generate professional statistical capability analysis report")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #ecf0f1; background: transparent;")
        text_layout.addWidget(subtitle)
        
        project_info = QLabel(f"Project: {self.client} - {self.ref_project} - {self.batch_number}")
        project_info.setFont(QFont("Segoe UI", 9))
        project_info.setStyleSheet("color: #bdc3c7; background: transparent;")
        text_layout.addWidget(project_info)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        header_frame.setLayout(layout)
        return header_frame

    def create_configuration_section(self):
        """Create the configuration section"""
        config_frame = QFrame()
        config_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Part Information Group
        part_group = self.create_part_info_group()
        layout.addWidget(part_group)
        
        # Technical Information Group
        tech_group = self.create_technical_info_group()
        layout.addWidget(tech_group)
        
        # Export Options Group
        options_group = self.create_export_options_group()
        layout.addWidget(options_group)
        
        config_frame.setLayout(layout)
        return config_frame

    def create_part_info_group(self):
        """Create part information group"""
        group = QGroupBox("📋 Part Information")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Part Description
        layout.addWidget(QLabel("Part Description:"), 0, 0)
        self.part_description_edit = ModernLineEdit()
        self.part_description_edit.setPlaceholderText("Enter detailed part description...")
        layout.addWidget(self.part_description_edit, 0, 1)
        
        # Drawing Number
        layout.addWidget(QLabel("Drawing Number:"), 1, 0)
        self.drawing_number_edit = ModernLineEdit()
        self.drawing_number_edit.setPlaceholderText("e.g., BMW-SB-2024-001-Rev.C")
        layout.addWidget(self.drawing_number_edit, 1, 1)
        
        # Facility
        layout.addWidget(QLabel("Manufacturing Facility:"), 2, 0)
        self.facility_edit = ModernLineEdit()
        self.facility_edit.setPlaceholderText("Enter facility name...")
        layout.addWidget(self.facility_edit, 2, 1)
        
        group.setLayout(layout)
        return group

    def create_technical_info_group(self):
        """Create technical information group"""
        group = QGroupBox("🔧 Technical Information")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Methodology
        layout.addWidget(QLabel("Measurement Methodology:"), 0, 0)
        self.methodology_combo = ModernComboBox()
        self.methodology_combo.addItems([
            "CMM (Coordinate Measuring Machine)",
            "MSA (Measurement System Analysis)",
            "Manual Measurement",
            "Optical Measurement System",
            "Laser Measurement System",
            "Gauge Measurement"
        ])
        layout.addWidget(self.methodology_combo, 0, 1)
        
        # Dimension Class
        layout.addWidget(QLabel("Dimension Classification:"), 1, 0)
        self.dimension_class_combo = ModernComboBox()
        self.dimension_class_combo.addItems([
            "CC (Critical Characteristic)",
            "SC (Significant Characteristic)",
            "IC (Important Characteristic)",
            "Standard Dimension"
        ])
        layout.addWidget(self.dimension_class_combo, 1, 1)
        
        group.setLayout(layout)
        return group

    def create_export_options_group(self):
        """Create export options group"""
        group = QGroupBox("⚙️ Export Options")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
            QCheckBox {
                color: #495057;
                font-size: 10pt;
                spacing: 5px;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Generate charts option
        self.generate_charts_cb = QCheckBox("Generate SPC charts before creating report")
        self.generate_charts_cb.setChecked(True)
        self.generate_charts_cb.setToolTip("Generate all statistical process control charts")
        layout.addWidget(self.generate_charts_cb)
        
        # Open file option
        self.open_file_cb = QCheckBox("Open Excel file after generation")
        self.open_file_cb.setChecked(True)
        self.open_file_cb.setToolTip("Automatically open the generated Excel file")
        layout.addWidget(self.open_file_cb)
        
        # Include all elements option
        self.include_all_elements_cb = QCheckBox("Include all analyzed elements")
        self.include_all_elements_cb.setChecked(True)
        self.include_all_elements_cb.setToolTip("Include all elements in the report (each on separate sheet)")
        layout.addWidget(self.include_all_elements_cb)
        
        group.setLayout(layout)
        return group

    def create_progress_section(self):
        """Create progress section"""
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Status label
        self.status_label = QLabel("Ready to export...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #495057; background: transparent;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        progress_frame.setLayout(layout)
        return progress_frame

    def create_buttons_section(self):
        """Create buttons section"""
        buttons_frame = QFrame()
        
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # Preview button
        self.preview_btn = ActionButton("👁️ Preview Elements")
        self.preview_btn.clicked.connect(self.preview_elements)
        self.preview_btn.setToolTip("Preview which elements will be included")
        layout.addWidget(self.preview_btn)
        
        layout.addStretch()
                # Export button
        self.export_btn = ModernButton("📤 Export Report")
        self.export_btn.clicked.connect(self.start_export_process)
        self.export_btn.setToolTip("Generate and export the Excel SPC report")
        layout.addWidget(self.export_btn)

        # Cancel button
        self.cancel_btn = CompactButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        buttons_frame.setLayout(layout)
        return buttons_frame

    def start_export_process(self):
        """Start the export process with proper dimension class handling"""
        
        # CHANGE: Extract dimension class properly from combo box
        dimension_class_text = self.dimension_class_combo.currentText()
        
        # Extract the abbreviation from the full text
        if "CC (" in dimension_class_text:
            dimension_class = "CC"
        elif "SC (" in dimension_class_text:
            dimension_class = "SC"  
        elif "IC (" in dimension_class_text:
            dimension_class = "IC"
        else:
            dimension_class = "Standard"
        
        # CHANGE: Extract methodology properly
        methodology_text = self.methodology_combo.currentText()
        if "CMM" in methodology_text:
            methodology = "CMM"
        elif "MSA" in methodology_text:
            methodology = "MSA"
        elif "Manual" in methodology_text:
            methodology = "Manual"
        elif "Optical" in methodology_text:
            methodology = "Optical"
        elif "Laser" in methodology_text:
            methodology = "Laser"
        elif "Gauge" in methodology_text:
            methodology = "Gauge"
        else:
            methodology = "CMM"  # Default
        
        export_config = {
            "part_description": self.part_description_edit.text().strip(),
            "drawing_number": self.drawing_number_edit.text().strip(),
            "facility": self.facility_edit.text().strip(),
            "methodology": methodology,  # CHANGED: Use extracted methodology
            "dimension_class": dimension_class,  # CHANGED: Use extracted dimension class
            "generate_charts": self.generate_charts_cb.isChecked(),
            "open_file": self.open_file_cb.isChecked(),
        }

        self.worker = ExcelExportWorker(self.excel_service, export_config)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.finished.connect(self.export_finished)

        self.progress_widget.setVisible(True)
        self.status_label.setText("Preparing to export...")
        self.progress_bar.setValue(0)
        self.worker.start()

    def export_finished(self, success: bool, message: str):
        if success:
            QMessageBox.information(self, "Export Complete", f"Report exported successfully:\n{message}")
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", f"An error occurred:\n{message}")
            self.progress_widget.setVisible(False)

    def preview_elements(self):
        elements = self.excel_service.get_available_elements()
        summary = f"{len(elements)} elements found:\n\n" + "\n".join(f"• {el}" for el in elements)
        QMessageBox.information(self, "Analyzed Elements", summary)

    def load_defaults(self):
        self.methodology_combo.setCurrentText("CMM (Coordinate Measuring Machine)")
        self.dimension_class_combo.setCurrentText("CC (Critical Characteristic)")
