# src/gui/windows/dimensional_study_window.py
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QProgressBar,
    QComboBox,
    QTabWidget,
    QFrame,
    QSplitter,
    QGroupBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPixmap, QFont
import pandas as pd
import os
import logging
from typing import List, Optional
from .base_dimensional_window import BaseDimensionalWindow
from .components.dimensional_table_manager import DimensionalTableManager
from .components.dimensional_session_manager import SessionManager
from .components.dimensional_summary_widget import SummaryWidget
from src.models.dimensional.dimensional_result import DimensionalResult
from ..workers.dimensional_processing_thread import ProcessingThread
from ..utils.styles import global_style, get_color_palette
from ..widgets.buttons import ModernButton, CompactButton  # , ActionButton


class DimensionalStudyWindow(BaseDimensionalWindow):
    """Enhanced dimensional study window with professional automotive styling"""

    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__(client, ref_project, batch_number)

        # Initialize enhanced logging
        self._init_logging()

        self.unsaved_changes = False
        self.manual_mode = False
        self.results = []
        self.processing_thread = None
        self._apply_professional_styling = global_style
        self.colors = get_color_palette

        # Initialize enhanced managers
        self._init_table_manager()
        self._init_session_manager()

        # Setup enhanced UI
        self.setWindowTitle("🔧 Dimensional Study - Professional Analysis Suite")
        self.setMinimumSize(1600, 1000)
        self._init_ui()
        self._apply_professional_styling()

        # Load last session
        QTimer.singleShot(100, self.session_manager._load_last_session)
        
        # Auto-load database data option (after session load)
        QTimer.singleShot(500, self._check_auto_load_database)

    def _init_logging(self):
        """Initialize enhanced logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Configure the root logger for the application
        self.logger = logging.getLogger(
            f"DimensionalStudy.{self.client_name}.{self.project_ref}"
        )
        self.logger.setLevel(logging.DEBUG)

        # Only add handlers if they haven't been added before
        if not self.logger.handlers:
            # File handler for dimensional.log
            file_handler = logging.FileHandler(
                logs_dir / "dimensional.log", mode="a", encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

            self.logger.info("Initialized logging for DimensionalStudyWindow")
            self.logger.debug(
                f"Client: {self.client_name}, Project: {self.project_ref}, Batch: {self.batch_number}"
            )

    def _log_message(self, message: str, level: str = "INFO"):
        """
        Enhanced logging with both GUI and file logging
        Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        try:
            # Log to file using the standard logger
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message)

        except Exception as e:
            print(f"Logging failed: {str(e)}")

    def _init_table_manager(self):
        """Initialize enhanced table manager with logging"""
        self.logger.debug("Initializing Table Manager")
        try:
            self.table_manager = DimensionalTableManager(
                display_columns=[
                    "element_id",
                    "batch",
                    "cavity",
                    "class",
                    "description",
                    "measuring_instrument",
                    "unit",
                    "datum",
                    "evaluation_type",
                    "nominal",
                    "lower_tolerance",
                    "upper_tolerance",
                    "measurement_1",
                    "measurement_2",
                    "measurement_3",
                    "measurement_4",
                    "measurement_5",
                    "minimum",
                    "maximum",
                    "mean",
                    "std_deviation",
                    "status",
                    "force_status",
                ],
                column_headers=[
                    "Element ID",
                    "Batch",
                    "Cavity",
                    "Class",
                    "Description",
                    "Measuring Inst.",
                    "Unit",
                    "Datum",
                    "Eval Type",
                    "Nominal",
                    "Lower Tol",
                    "Upper Tol",
                    "Meas 1",
                    "Meas 2",
                    "Meas 3",
                    "Meas 4",
                    "Meas 5",
                    "Min",
                    "Max",
                    "Mean",
                    "Std Dev",
                    "Status",
                    "Force Status",
                ],
                required_columns=[
                    "element_id",
                    "batch",
                    "cavity",
                    "class",
                    "description",
                    "measuring_instrument",
                    "unit",
                    "datum",
                    "evaluation_type",
                    "nominal",
                    "lower_tolerance",
                    "upper_tolerance",
                ],
                measurement_columns=[
                    "measurement_1",
                    "measurement_2",
                    "measurement_3",
                    "measurement_4",
                    "measurement_5",
                ],
                batch_number=self.batch_number,
            )
            self.table_manager.set_parent_window(self)
            self.logger.info("Table manager initialized successfully")
        except Exception as e:
            self._log_message(f"Failed to initialize table manager: {str(e)}", "ERROR")
            raise

    def _init_session_manager(self):
        """Initialize session manager with logging"""
        self.logger.debug("Initializing Session Manager")
        try:
            self.session_manager = SessionManager(
                self.client_name,
                self.project_ref,
                self.batch_number,
                log_callback=self._log_message,
                parent=self,
            )
            self.logger.info("Session manager initialized successfully")
        except Exception as e:
            self._log_message(
                f"Failed to initialize session manager: {str(e)}", "ERROR"
            )
            raise

    def _init_summary_widget(self):
        """Initialize optimized summary widget"""
        if not hasattr(self, 'summary_widget') or not self.summary_widget:
            self.summary_widget = SummaryWidget(parent=self)
            self.summary_widget.update_complete.connect(self._on_summary_update_complete)
            
            # Add to tabs if not already present
            self.results_tabs.insertTab(0, self.summary_widget, "📊 Enhanced Summary")
            self.results_tabs.setCurrentIndex(0)
            
            self._log_message("📊 Optimized summary widget initialized", "INFO")

    def _init_ui(self):
        """Initialize enhanced professional UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Enhanced header section
        header_frame = self._create_header_section()
        main_layout.addWidget(header_frame)

        # Enhanced control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Enhanced main content area with splitter
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter)

        # Enhanced status bar
        status_frame = self._create_status_section()
        main_layout.addWidget(status_frame)

        # Set main widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def _create_header_section(self) -> QFrame:
        """Create IMPROVED professional header section - more compact and graceful"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        header_frame.setFixedHeight(100)  # Reduced from 130
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 8px;
                border: 1px solid #1a252f;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)  # Reduced margins
        layout.setSpacing(15)  # Reduced spacing

        # Left: Project information - more compact
        info_group = QGroupBox("📋 Project Information")
        info_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #415A77;
                border-radius: 6px;
                margin: 5px 0;
                padding: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 8px;
                background-color: #34495e;
                border-radius: 4px;
            }
        """)
        
        info_layout = QVBoxLayout()  # Changed to vertical for more compact
        info_layout.setSpacing(3)  # Tight spacing

        # More compact labels
        client_label = QLabel(f"🏢 {self.client_name}")
        client_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        client_label.setStyleSheet("color: #ecf0f1; margin: 2px;")

        project_label = QLabel(f"📁 {self.project_ref}")
        project_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        project_label.setStyleSheet("color: #ecf0f1; margin: 2px;")

        batch_label = QLabel(f"📦 {self.batch_number}")
        batch_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        batch_label.setStyleSheet("color: #ecf0f1; margin: 2px;")

        info_layout.addWidget(client_label)
        info_layout.addWidget(project_label)
        info_layout.addWidget(batch_label)
        info_group.setLayout(info_layout)

        # Center: Configuration - more graceful arrangement
        config_group = QGroupBox("⚙️ Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #415A77;
                border-radius: 6px;
                margin: 5px 0;
                padding: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 8px;
                background-color: #34495e;
                border-radius: 4px;
            }
        """)
        
        config_layout = QVBoxLayout()
        config_layout.setSpacing(5)

        # Report type row
        report_row = QHBoxLayout()
        report_label = QLabel("📊")
        report_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        report_row.addWidget(report_label)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "PPAP", "FOT (First Off Tool)", "Process Validation", "Internal Audit",
            "Customer Audit", "Tool modification", "Supplier Change", "Material Change",
            "Annual Requalification", "Serial Production Control", "Temporary Deviation Approval",
            "Quality Incident", "Customer Complaint", "New Measurement Equipment Validation",
            "New Operator Validation", "Plant Layout Change", "Process Parameter Change",
            "New Product Models or Variants", "Internal Benchmarking", "Packaging Validation"
        ])
        self.report_type_combo.setMinimumWidth(140)
        self.report_type_combo.setStyleSheet(self._get_compact_combo_style())
        report_row.addWidget(self.report_type_combo)
        report_row.addStretch()

        # Tolerance row  
        tolerance_row = QHBoxLayout()
        tolerance_label = QLabel("📏")
        tolerance_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        tolerance_row.addWidget(tolerance_label)

        self.tolerance_combo = QComboBox()
        self.tolerance_combo.addItems([
            "ISO 2768-m (General)", "ISO 2768-f (Fine)", "ISO 2768-c (Coarse)",
            "ISO 2768-v (Very Coarse)", "DIN 6930", "DIN 7168-m", "DIN 16901",
            "ISO 286-1", "ISO 286-2", "Customer Specific", "Other/Custom"
        ])
        self.tolerance_combo.setMinimumWidth(140)
        self.tolerance_combo.setStyleSheet(self._get_compact_combo_style())
        tolerance_row.addWidget(self.tolerance_combo)
        tolerance_row.addStretch()

        config_layout.addLayout(report_row)
        config_layout.addLayout(tolerance_row)
        config_group.setLayout(config_layout)

        # Right: Company logo - more compact
        logo_frame = QFrame()
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(5, 5, 5, 5)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_path = "assets/images/gui/logo_some.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                200, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation  # Reduced size
            )
            logo_label.setPixmap(pixmap)
        else:
            # More elegant fallback logo
            logo_label.setText("🏭\nAUTOMOTIVE\nQUALITY")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 10px;
                    border: 1px solid #2471a3;
                }
            """)
            logo_label.setFixedSize(120, 60)

        logo_layout.addWidget(logo_label)
        logo_frame.setLayout(logo_layout)

        # Arrange sections with better proportions
        layout.addWidget(info_group, 2)
        layout.addWidget(config_group, 3)
        layout.addWidget(logo_frame, 1)

        header_frame.setLayout(layout)
        return header_frame
    
    def _apply_professional_styling(self):
        """Apply enhanced professional styling throughout the application"""
        # Set the main window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 4px 12px;
                background-color: white;
                border-radius: 4px;
                color: #495057;
            }
        """)
    
    def _get_compact_combo_style(self) -> str:
        """Compact combo box style for header"""
        return """
            QComboBox {
                background-color: #34495e;
                color: white;
                padding: 4px 8px;
                border: 1px solid #415A77;
                border-radius: 4px;
                font-size: 10px;
                max-height: 24px;
            }
            QComboBox:hover {
                background-color: #415A77;
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIgM0w1IDZMOCAzIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            QComboBox QAbstractItemView {
                background-color: #34495e;
                selection-background-color: #3498db;
                color: white;
                border: 1px solid #415A77;
                border-radius: 4px;
                font-size: 10px;
            }
        """

    def _create_control_panel(self) -> QFrame:
        """Create enhanced control panel"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setFixedHeight(100)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)

        # Mode control group
        mode_group = QGroupBox("📝 Input Mode")
        mode_layout = QHBoxLayout()

        self.mode_toggle = ModernButton("🔄 Switch to Manual Entry")
        self.mode_toggle.setMinimumSize(180, 40)
        self.mode_toggle.clicked.connect(self._toggle_mode)

        self.load_db_button = ModernButton("💾 Load from Database")
        self.load_db_button.setMinimumSize(160, 40)
        self.load_db_button.clicked.connect(self._load_data_from_database)

        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addWidget(self.load_db_button)
        mode_group.setLayout(mode_layout)

        # Manual mode controls (initially hidden)
        manual_group = QGroupBox("✏️ Manual Controls")
        manual_layout = QHBoxLayout()

        self.add_row_button = CompactButton("➕ Add Row")
        self.duplicate_row_button = CompactButton("📋 Duplicate")
        self.delete_row_button = CompactButton("🗑️ Delete")

        for btn in [
            self.add_row_button,
            self.duplicate_row_button,
            self.delete_row_button,
        ]:
            btn.setMinimumSize(100, 40)
            btn.setVisible(False)

        self.add_row_button.clicked.connect(self._add_manual_row)
        self.duplicate_row_button.clicked.connect(self._duplicate_row)
        self.delete_row_button.clicked.connect(self._delete_row)

        manual_layout.addWidget(self.add_row_button)
        manual_layout.addWidget(self.duplicate_row_button)
        manual_layout.addWidget(self.delete_row_button)
        manual_group.setLayout(manual_layout)

        # Analysis controls
        analysis_group = QGroupBox("🔬 Analysis")
        analysis_layout = QHBoxLayout()

        self.run_study_button = ModernButton(
            "\U0001f680 Run Dimensional Study", primary=True
        )
        self.run_study_button.setMinimumSize(170, 40)
        self.run_study_button.setEnabled(False)
        self.run_study_button.clicked.connect(self._run_study)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(25)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("🔄 Processing...")

        analysis_layout.addWidget(self.run_study_button)
        analysis_layout.addWidget(self.progress_bar)
        analysis_group.setLayout(analysis_layout)

        # Session controls
        session_group = QGroupBox("💾 Session")
        session_layout = QHBoxLayout()

        self.save_button = ModernButton("💾 Save")
        self.save_button.setMinimumSize(80, 40)
        self.save_button.clicked.connect(self.session_manager.save_session)
        session_layout.addWidget(self.save_button)

        self.load_button = ModernButton("📂 Load")
        self.load_button.setMinimumSize(80, 40)
        self.load_button.clicked.connect(self.session_manager._load_session)
        session_layout.addWidget(self.load_button)

        self.export_button = ModernButton("📤 Export")
        self.export_button.setMinimumSize(80, 40)
        self.export_button.clicked.connect(self.session_manager._export_data)
        session_layout.addWidget(self.export_button)

        self.clear_button = ModernButton("🧹 Clear")
        self.clear_button.setMinimumSize(80, 40)
        self.clear_button.clicked.connect(self._clear_all)
        session_layout.addWidget(self.clear_button)

        session_group.setLayout(session_layout)

        layout.addWidget(mode_group)
        layout.addWidget(manual_group)
        layout.addWidget(analysis_group)
        layout.addWidget(session_group)
        layout.addStretch()

        control_frame.setLayout(layout)
        return control_frame

    def _create_content_area(self) -> QSplitter:
        """Create IMPROVED content area - removed activity log, cleaner layout"""
        splitter = QSplitter(Qt.Vertical)

        # Enhanced results tabs with better styling
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabsClosable(True)
        self.results_tabs.tabCloseRequested.connect(self._remove_tab)
        self.results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e0;
                border-radius: 8px;
                background-color: white;
                margin-top: 2px;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                color: #495057;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-bottom-color: white;
                color: #2c3e50;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-color: #3498db;
            }
            QTabBar::close-button {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkgM0wzIDlNMyAzTDkgOSIgc3Ryb2tlPSIjNmM3NTdkIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            QTabBar::close-button:hover {
                background-color: rgba(220, 53, 69, 0.1);
                border-radius: 3px;
            }
        """)

        # Initialize and add enhanced summary tab
        self._init_summary_widget()
        
        # Give the splitter all available space to tabs (no activity log)
        splitter.addWidget(self.results_tabs)
        
        # Set splitter handle styling for a more professional look
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                border: 1px solid #adb5bd;
                margin: 2px 0;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
            }
        """)

        return splitter

    def _create_status_section(self) -> QFrame:
        """Create ENHANCED status section with better visual design"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setFixedHeight(35)  # Slightly reduced
        status_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-top: 1px solid #dee2e6;
                border-radius: 0 0 8px 8px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(20)

        # Status with icon and better styling
        status_container = QFrame()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        status_icon = QLabel("🔄")
        status_icon.setFont(QFont("Segoe UI", 12))
        status_layout.addWidget(status_icon)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.status_label.setStyleSheet("color: #2c3e50;")
        status_layout.addWidget(self.status_label)

        status_container.setLayout(status_layout)

        # Stats with better visual separation
        stats_container = QFrame()
        stats_container.setStyleSheet("""
            QFrame {
                background-color: rgba(52, 152, 219, 0.1);
                border: 1px solid rgba(52, 152, 219, 0.3);
                border-radius: 15px;
                padding: 2px 12px;
            }
        """)
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(8, 2, 8, 2)

        self.stats_label = QLabel("No data loaded")
        self.stats_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.stats_label.setStyleSheet("color: #2980b9;")
        stats_layout.addWidget(self.stats_label)
        stats_container.setLayout(stats_layout)

        layout.addWidget(status_container)
        layout.addStretch()
        layout.addWidget(stats_container)

        status_frame.setLayout(layout)
        return status_frame

    def _remove_tab(self, index: int):
        """IMPROVED: Remove tab with better user feedback"""
        if 0 <= index < self.results_tabs.count():
            tab_name = self.results_tabs.tabText(index)
            widget = self.results_tabs.widget(index)
            
            # Prevent closing summary tab
            if "Summary" in tab_name:
                QMessageBox.information(
                    self,
                    "Cannot Close",
                    "The Summary tab cannot be closed as it contains essential analysis information."
                )
                return
            
            self.results_tabs.removeTab(index)
            if widget:
                widget.deleteLater()
            
            self._log_message(f"📝 Closed tab: {tab_name}")


    def _run_study(self):
        """Execute the dimensional study - FIXED to avoid double execution"""
        self.logger.info("=" * 60)
        self.logger.info("STARTING DIMENSIONAL STUDY ANALYSIS")
        self.logger.info("=" * 60)

        try:
            # Prevent double execution
            if hasattr(self, "_study_running") and self._study_running:
                self._log_message("⚠️ Study already running, please wait...", "WARNING")
                return

            self._study_running = True

            # Ensure summary widget is initialized and visible
            if not hasattr(self, "summary_widget") or not self.summary_widget:
                self._init_summary_widget()

            self.summary_widget.ensure_visibility()

            # Get all data from tables
            all_df = self.table_manager._get_dataframe_from_tables()
            self.logger.info(f"📊 Total records extracted from tables: {len(all_df)}")

            if all_df.empty:
                msg = "No data found in tables"
                self.logger.error(f"❌ {msg}")
                QMessageBox.warning(self, "No Data", msg)
                self._study_running = False
                return

            # Store original data if this is the first study run
            if self.summary_widget.metrics["studies_run"] == 0:
                self.summary_widget.store_original_data(all_df)
                self._log_message("📋 Original data stored for comparison", "INFO")

            # Update summary with current table data
            self.summary_widget.update_summary(results=None, table_data=all_df)

            # Log data composition
            self._log_data_composition(all_df)

            self.logger.info(f"🚀 Starting analysis on {len(all_df)} total records")

            # Disable UI during processing
            self._set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Start processing in thread
            self.processing_thread = ProcessingThread(all_df)
            self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.processing_thread.processing_finished.connect(
                self._on_processing_finished
            )
            self.processing_thread.error_occurred.connect(self._on_processing_error)
            self.processing_thread.start()

        except Exception as e:
            error_msg = f"Error starting dimensional study: {str(e)}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            QMessageBox.critical(self, "Processing Error", error_msg)
            self._set_ui_enabled(True)
            self._study_running = False

    def _handle_results(self, results: List[DimensionalResult]):
        """Handle analysis results and update summary - OPTIMIZED VERSION"""
        try:
            self._log_message(
                f"✅ Analysis completed with {len(results)} results", "INFO"
            )

            # Store results
            self.results = results

            # Update tables with results FIRST (this is the heavy operation)
            self.table_manager._update_tables_with_results(results)

            # Update summary with results (optimized with throttling)
            if hasattr(self, "summary_widget") and self.summary_widget:
                # Use non-blocking update
                QTimer.singleShot(
                    100, lambda: self.summary_widget.update_summary(results=results)
                )
                self._log_message("📊 Summary update scheduled", "INFO")

            # Update status immediately (lightweight)
            good_count = sum(1 for r in results if r.status.value == "GOOD")
            success_rate = (good_count / len(results)) * 100 if results else 0

            self.stats_label.setText(
                f"📊 Analysis Complete: {len(results)} dimensions, {success_rate:.1f}% success rate"
            )

            # Log completion
            self._log_message(
                f"🎯 Success Rate: {success_rate:.1f}% ({good_count}/{len(results)})",
                "INFO",
            )

            # Mark as saved (results don't need saving until user modifies)
            self.unsaved_changes = False

        except Exception as e:
            self._log_message(f"❌ Error handling results: {str(e)}", "ERROR")
        finally:
            self._reset_ui_state()

    def _on_summary_update_complete(self):
        """Handle summary update completion"""
        self._log_message("📊 Summary update completed", "DEBUG")

    def _reset_ui_state(self):
        """Reset UI state after operations"""
        self.run_study_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

    def _validate_input(self) -> bool:
        """Validate input data before processing"""
        df = self.table_manager._get_dataframe_from_tables()
        if df.empty:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load data or add manual entries before running the study.",
            )
            return False

        # Check for required fields
        required_fields = ["element_id", "description"]
        missing_fields = []

        for field in required_fields:
            if field not in df.columns or df[field].isna().all():
                missing_fields.append(field)

        if missing_fields:
            QMessageBox.warning(
                self,
                "Missing Data",
                f"Required fields are missing or empty: {', '.join(missing_fields)}",
            )
            return False

        return True

    def _log_data_composition(self, df):
        """Log detailed data composition for debugging"""
        self.logger.info("📋 DATA COMPOSITION ANALYSIS:")
        self.logger.info("-" * 40)

        # Log evaluation types
        if "evaluation_type" in df.columns:
            eval_counts = df["evaluation_type"].value_counts()
            for eval_type, count in eval_counts.items():
                self.logger.info(f"  📌 {eval_type}: {count} records")
        else:
            self.logger.warning("  ⚠️ No evaluation_type column found!")

        # Log force status distribution
        if "force_status" in df.columns:
            force_counts = df["force_status"].value_counts()
            self.logger.info("  🔧 Force Status Distribution:")
            for status, count in force_counts.items():
                self.logger.info(f"    - {status}: {count} records")

        # Log records with nominal = 0
        if "nominal" in df.columns:
            zero_nominal = df[df["nominal"] == 0.0]
            self.logger.info(f"  🎯 Records with nominal = 0: {len(zero_nominal)}")
            if len(zero_nominal) > 0:
                for idx, row in zero_nominal.iterrows():
                    self.logger.info(
                        f"    - {row.get('element_id', 'Unknown')}: {row.get('description', 'No description')}"
                    )

        # Log measurement availability
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        records_with_measurements = 0
        for idx, row in df.iterrows():
            has_measurements = any(
                pd.notna(row.get(col)) and str(row.get(col)).strip() != ""
                for col in measurement_cols
            )
            if has_measurements:
                records_with_measurements += 1

        self.logger.info(
            f"  📏 Records with measurements: {records_with_measurements}/{len(df)}"
        )
        self.logger.info("-" * 40)

    def _on_processing_finished(self, results: List[DimensionalResult]):
        """Handle completion of processing - ENHANCED"""
        self.logger.info("=" * 60)
        self.logger.info("PROCESSING COMPLETED - ANALYZING RESULTS")
        self.logger.info("=" * 60)

        try:
            self.results = results
            self.progress_bar.setVisible(False)
            self._set_ui_enabled(True)
            self._study_running = False  # Reset flag

            if not results:
                self.logger.error("❌ No valid results generated")
                QMessageBox.information(
                    self,
                    "No Results",
                    "No valid results were generated from the input data.",
                )
                return

            # Log detailed results analysis
            self._log_results_analysis(results)

            # Update tables with results
            self.logger.info("🔄 Updating tables with results...")
            self.table_manager._update_tables_with_results(results)

            # Update summary with results
            if hasattr(self, "summary_widget") and self.summary_widget:
                # Get current table data for comparison
                current_df = self.table_manager._get_dataframe_from_tables()

                # Update summary with both results and current table data
                self.summary_widget.update_summary(
                    results=results, table_data=current_df, force_refresh=True
                )
                self._log_message("📊 Summary updated with analysis results", "INFO")

            # Update status
            good_count = sum(1 for r in results if r.status.value == "GOOD")
            success_rate = (good_count / len(results)) * 100 if results else 0

            self.stats_label.setText(
                f"📊 Analysis Complete: {len(results)} dimensions, {success_rate:.1f}% success rate"
            )

            # Enable export and auto-save
            self.export_button.setEnabled(True)
            self.session_manager._auto_save_session()

            self.logger.info("✅ Processing completed successfully")

        except Exception as e:
            self._log_message(f"❌ Error in processing completion: {str(e)}", "ERROR")
            self._study_running = False

    def _safe_update_summary_with_results(self, results: List[DimensionalResult]):
        """Safely update summary with results"""
        try:
            if hasattr(self, "summary_widget") and self.summary_widget:
                self.summary_widget.update_summary(results=results)
                self._log_message("✅ Summary updated with analysis results", "INFO")
        except Exception as e:
            self._log_message(
                f"❌ Error updating summary with results: {str(e)}", "ERROR"
            )

    def _log_results_analysis(self, results):
        """Log detailed analysis of results"""
        self.logger.info("📊 RESULTS ANALYSIS:")
        self.logger.info("-" * 40)
        self.logger.info(f"  Total results: {len(results)}")

        # Status distribution
        status_counts = {}
        for result in results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            self.logger.info(f"  {status}: {count} records")

        # Log individual results for debugging
        self.logger.info("🔍 INDIVIDUAL RESULT DETAILS:")
        for i, result in enumerate(results[:10]):  # Log first 10 for debugging
            self.logger.info(f"  [{i + 1}] {result.element_id} - {result.status.value}")
            self.logger.info(f"      Description: {result.description}")
            self.logger.info(f"      Nominal: {result.nominal}")
            self.logger.info(f"      Measurements: {result.measurements}")
            self.logger.info(
                f"      Tolerances: {result.lower_tolerance} / {result.upper_tolerance}"
            )
            if result.warnings:
                self.logger.info(f"      Warnings: {'; '.join(result.warnings)}")

        if len(results) > 10:
            self.logger.info(f"  ... and {len(results) - 10} more results")

        self.logger.info("-" * 40)

    def _start_processing_thread(self, df: pd.DataFrame):
        """Start the processing thread with the given dataframe"""
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)

        self.processing_thread = ProcessingThread(df)
        self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processing_thread.processing_finished.connect(self._on_processing_finished)
        self.processing_thread.error_occurred.connect(self._on_processing_error)
        self.processing_thread.start()

    def _handle_error(self, context: str, error: Exception):
        """Centralized error handling with logging"""
        error_msg = f"{context}: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        QMessageBox.critical(self, "Error", error_msg)

    def _on_processing_error(self, error_msg: str):
        """Handle processing thread errors with logging"""
        self.logger.error(f"Processing error: {error_msg}")
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Processing Error", f"Analysis failed:\n{error_msg}")

    def _clear_all(self):
        """FIXED: Clear all data but preserve summary widget with proper reset"""
        self.logger.debug("Clear all requested")
        reply = QMessageBox.question(
            self,
            "Clear All Data?",
            "Are you sure you want to clear all data and reset the analysis?\n\n"
            "This will:\n"
            "• Clear all measurement data\n"
            "• Reset analysis results\n"
            "• Reset summary statistics\n"
            "• Clear activity logs\n\n"
            "The summary widget will remain visible but reset to initial state.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                self.logger.info("🧹 Clearing all data with enhanced cleanup")

                # Clear data tabs but preserve summary
                self._clear_data_tabs_only()

                # Reset summary widget instead of recreating
                if hasattr(self, "summary_widget") and self.summary_widget:
                    self.summary_widget.reset_widget()
                    # Ensure it's properly positioned
                    self.summary_widget.ensure_visibility()
                else:
                    # Create new summary widget if somehow missing
                    self._init_summary_widget()
                
                self.results = []

                # Reset UI state
                self.run_study_button.setEnabled(False)
                self.export_button.setEnabled(False)

                # Clear table manager data if needed
                if hasattr(self, "table_manager"):
                    # Don't clear table manager itself, just reset state
                    self.table_manager._original_measurements = {}

                # Clear unsaved changes
                self._clear_unsaved_changes()

                # Update status
                self.stats_label.setText("📊 Data cleared - Ready for new data")

                self.logger.info("✅ All data cleared successfully, summary widget preserved and reset")
                self._log_message("🧹 All data cleared, ready for new analysis", "INFO")

            except Exception as e:
                self._handle_error("Clear All", e)

    def _toggle_mode(self):
        """FIXED: Toggle between file and manual entry modes with proper cleanup"""
        self.manual_mode = not self.manual_mode

        # Ensure summary widget exists and is visible
        if not hasattr(self, "summary_widget") or not self.summary_widget:
            self._init_summary_widget()

        self.summary_widget.ensure_visibility()

        if self.manual_mode:
            self.mode_toggle.setText("🔄 Switch to File Mode")
            self._prepare_manual_table()
            self.add_row_button.setVisible(True)
            self.duplicate_row_button.setVisible(True)
            self.delete_row_button.setVisible(True)
            self.load_db_button.setVisible(False)
            self._log_message("📝 Switched to manual entry mode")
        else:
            self.mode_toggle.setText("🔄 Switch to Manual Entry")
            self._clear_data_tabs_only()  # Only clear data tabs, preserve summary
            self.add_row_button.setVisible(False)
            self.duplicate_row_button.setVisible(False)
            self.delete_row_button.setVisible(False)
            self.load_db_button.setVisible(True)
            self.run_study_button.setEnabled(True)
            self._log_message("📁 Switched to file mode")

    def _clear_data_tabs_only(self):
        """FIXED: Clear only data tabs, preserve summary tab with proper cleanup"""
        try:
            # Find and preserve summary tab
            summary_widget = None
            summary_tab_text = ""
            
            for i in range(self.results_tabs.count()):
                tab_text = self.results_tabs.tabText(i)
                if "Summary" in tab_text:
                    summary_widget = self.results_tabs.widget(i)
                    summary_tab_text = tab_text
                    break

            # Remove all tabs (but don't delete summary widget)
            widgets_to_delete = []
            for i in range(self.results_tabs.count()):
                widget = self.results_tabs.widget(i)
                if widget != summary_widget:
                    widgets_to_delete.append(widget)
            
            # Clear tabs
            self.results_tabs.clear()
            
            # Delete non-summary widgets
            for widget in widgets_to_delete:
                try:
                    widget.deleteLater()
                except Exception:
                    pass

            # Restore summary tab as first tab
            if summary_widget:
                self.results_tabs.insertTab(0, summary_widget, summary_tab_text)
                self.results_tabs.setCurrentIndex(0)
                self._log_message("📊 Summary tab preserved during data clear", "DEBUG")

            # Reset relevant data
            self.results = []
            
            self._log_message("🧹 Data tabs cleared, summary preserved", "DEBUG")

        except Exception as e:
            self._log_message(f"❌ Error clearing data tabs: {str(e)}", "ERROR")


    def _clear_current_data(self):
        """Clear current data without confirmation dialog"""
        try:
            # Clear all tabs
            while self.results_tabs.count():
                widget = self.results_tabs.widget(0)
                self.results_tabs.removeTab(0)
                widget.deleteLater()

            # Reset data structures
            self.results = []
            self.run_study_button.setEnabled(False)
            self._clear_unsaved_changes()
            self._log_message("Data cleared for mode switch")

        except Exception as e:
            self._handle_error("Clear Current Data", e)

    def _prepare_manual_table(self):
        """FIXED: Prepare table for manual data entry with proper formatting"""
        # Clear existing data tabs but preserve summary
        self._clear_data_tabs_only()

        # Create main data entry table using table manager
        main_table = self.table_manager._create_results_table()
        self.results_tabs.addTab(main_table, "📝 Data Entry")

        # Set focus to the data entry tab (summary should be at index 0)
        self.results_tabs.setCurrentIndex(1)

        # Add initial row with proper formatting
        main_table.setRowCount(1)
        self.table_manager._populate_default_row(main_table, 0)

        # Enable editing and run button
        self.run_study_button.setEnabled(True)
        self._log_message("📝 Manual entry table prepared with proper formatting", "INFO")

    def _add_manual_row(self):
        """FIXED: Add a new row for manual entry with proper formatting"""
        current_widget = self.results_tabs.currentWidget()
        if not isinstance(current_widget, QTableWidget):
            self._log_message("⚠️ No active table for adding row", "WARNING")
            return

        try:
            row_count = current_widget.rowCount()
            current_widget.insertRow(row_count)
            
            # Populate with proper formatting using table manager
            self.table_manager._populate_default_row(current_widget, row_count)

            # Mark changes and update summary
            self._mark_unsaved_changes()
            self.run_study_button.setEnabled(True)

            # Record edit in summary
            if hasattr(self, "summary_widget") and self.summary_widget:
                self.summary_widget.record_edit("Added new dimension row")

            self._log_message(f"➕ Added new row #{row_count + 1}", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error adding manual row: {str(e)}", "ERROR")

    def _duplicate_row(self):
        """FIXED: Duplicate the currently selected row with proper formatting"""
        current_widget = self.results_tabs.currentWidget()
        if not isinstance(current_widget, QTableWidget):
            QMessageBox.information(
                self, "No Table", "Please select a data entry table first."
            )
            return

        current_row = current_widget.currentRow()
        if current_row == -1:
            QMessageBox.information(
                self, "No Selection", "Please select a row to duplicate."
            )
            return

        try:
            # Use table manager's duplicate method for consistency
            self.table_manager._duplicate_row(current_widget)
            
            # Mark changes
            self._mark_unsaved_changes()

            # Record edit in summary
            if hasattr(self, "summary_widget") and self.summary_widget:
                self.summary_widget.record_edit("Duplicated dimension row")

            self._log_message(f"📋 Duplicated row #{current_row + 1}", "INFO")
        except Exception as e:
            self._log_message(f"❌ Error duplicating row: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Duplication Error", f"Failed to duplicate row: {str(e)}")

    def _delete_row(self):
        """FIXED: Delete the currently selected row"""
        current_widget = self.results_tabs.currentWidget()
        if not isinstance(current_widget, QTableWidget):
            return

        current_row = current_widget.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a row to delete."
            )
            return

        try:
            reply = QMessageBox.question(
                self, "Confirm Delete", 
                f"Are you sure you want to delete row #{current_row + 1}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Get element info before deletion for logging
                element_item = current_widget.item(current_row, 0)  # element_id column
                element_id = element_item.text() if element_item else f"Row {current_row + 1}"
                
                current_widget.removeRow(current_row)
                self._mark_unsaved_changes()

                # Record edit in summary
                if hasattr(self, "summary_widget") and self.summary_widget:
                    self.summary_widget.record_edit("Deleted dimension row")
                    self.summary_widget.metrics["dimensions_deleted"] = self.summary_widget.metrics.get("dimensions_deleted", 0) + 1

                self._log_message(f"🗑️ Deleted {element_id}", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error deleting row: {str(e)}", "ERROR")

    def _update_summary_from_tables(self):
        """Update summary widget with current table data - OPTIMIZED"""
        if not hasattr(self, "summary_widget") or not self.summary_widget:
            return

        try:
            # Get current table data (this can be expensive, so we throttle it)
            df = self.table_manager._get_dataframe_from_tables()
            if not df.empty:
                # Use throttled update
                self.summary_widget.update_summary(table_data=df)
                self._log_message("📊 Summary updated with table changes", "DEBUG")
        except Exception as e:
            self._log_message(f"❌ Error updating summary: {str(e)}", "ERROR")

    def _load_data_from_database(self):
        """Load measurement data from database table mesuresqualitat where maquina='gompc_projectes'"""
        try:
            # Ask user how many records to load
            from PyQt5.QtWidgets import QInputDialog
            
            num_records, ok = QInputDialog.getInt(
                self, 
                "Database Load Options", 
                "How many different elements would you like to load?\n(Up to 5 measurements per element will be grouped by Project+Lot+Element)",
                5,  # default value
                1,  # minimum value
                50,  # maximum value - increased since we're loading element groups
                1   # step
            )
            
            if not ok:
                self._log_message("Database load cancelled by user", "INFO")
                return
                
            self._log_message(f"🔍 Connecting to database to load grouped measurements for {num_records} different elements...")
            
            # Import database adapter
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            from src.services.network_scanner import NetworkScanner
            
            # Load database configuration
            scanner = NetworkScanner()
            db_config = scanner.load_db_config()
            
            if not db_config:
                raise Exception("Could not load database configuration")
            
            # Create database adapter - db_config is already the primary config
            db_adapter = QualityMeasurementDBAdapter({'primary': db_config})
            
            if not db_adapter.connect():
                raise Exception("Could not connect to database")
            
            self._log_message("✅ Database connection established")
            
            # Query to get measurements grouped by id_referencia_client, id_lot, and element
            # This will give us multiple measurements for the same element/project/lot combination
            query = f"""
            WITH grouped_measurements AS (
                SELECT 
                    element as element_id,
                    COALESCE(property, COALESCE(element, 'Measurement')) as description,
                    COALESCE(nominal, 0) as nominal,
                    COALESCE(tolerancia_negativa, 0) as lower_tolerance,
                    COALESCE(tolerancia_positiva, 0) as upper_tolerance,
                    actual as measurement_value,
                    desviacio as deviation_value,
                    check_value,
                    data_hora,
                    client,
                    id_referencia_client,
                    id_lot,
                    COALESCE(cavitat, '') as cavitat,
                    COALESCE(pieza, '') as pieza,
                    COALESCE(datum, '') as datum,
                    COALESCE(fase, '') as fase,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_referencia_client, id_lot, element 
                        ORDER BY data_hora DESC
                    ) as measurement_rank
                FROM mesuresqualitat 
                WHERE maquina = 'gompc_projectes' 
                    AND element IS NOT NULL 
                    AND id_referencia_client IS NOT NULL 
                    AND id_lot IS NOT NULL
            )
            SELECT 
                element_id,
                description,
                nominal,
                lower_tolerance,
                upper_tolerance,
                measurement_value,
                deviation_value,
                check_value,
                data_hora,
                client,
                id_referencia_client,
                id_lot,
                cavitat,
                pieza,
                datum,
                fase,
                measurement_rank
            FROM grouped_measurements 
            WHERE measurement_rank <= 5
            ORDER BY id_referencia_client, id_lot, element_id, measurement_rank
            LIMIT {num_records * 5}
            """
            
            # Execute query and get DataFrame
            df = db_adapter.execute_query_to_dataframe(query)
            
            if df.empty:
                self._log_message("⚠️ No grouped measurement data found in database for maquina='gompc_projectes'", "WARNING")
                QMessageBox.information(
                    self, 
                    "No Data Found", 
                    "No measurement data found in database for machine 'gompc_projectes'\n\n"
                    "Make sure the table 'mesuresqualitat' contains records with:\n"
                    "• maquina = 'gompc_projectes'\n"
                    "• Valid element, id_referencia_client, and id_lot values"
                )
                return
            
            # Transform data to dimensional analysis format
            dimensional_df = self._transform_db_data_to_dimensional_format(df)
            
            # Populate table with transformed data
            self._populate_table_from_dataframe(dimensional_df)
            
            # Log detailed success information
            total_measurements = dimensional_df[[f'measurement_{i}' for i in range(1, 6)]].notna().sum().sum()
            elements_with_data = dimensional_df[dimensional_df['measurement_count'] > 0].shape[0]
            
            self._log_message(
                f"✅ Successfully loaded {len(dimensional_df)} element records with {total_measurements} total measurements from database",
                "INFO"
            )
            self._log_message(
                f"📊 Elements with measurement data: {elements_with_data}/{len(dimensional_df)}",
                "INFO"
            )
            
            self.run_study_button.setEnabled(True)  # Enable run button
            
            # Close database connection
            db_adapter.close()
            
            # Update summary
            if hasattr(self, "summary_widget"):
                total_measurements = dimensional_df[[f'measurement_{i}' for i in range(1, 6)]].notna().sum().sum()
                self.summary_widget.record_edit(
                    f"Loaded {len(dimensional_df)} elements with {total_measurements} measurements from database (gompc_projectes)"
                )
                self._update_summary_from_tables()
                
        except Exception as e:
            error_msg = f"Failed to load data from database: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Database Load Error", error_msg)

    def _transform_db_data_to_dimensional_format(self, db_df: pd.DataFrame) -> pd.DataFrame:
        """Transform database data format to dimensional analysis format with proper grouping"""
        try:
            if db_df.empty:
                return pd.DataFrame()
            
            # Group by id_referencia_client, id_lot, and element_id to aggregate measurements
            grouped_data = []
            
            # Create grouping key
            grouping_columns = ['id_referencia_client', 'id_lot', 'element_id']
            
            for group_key, group_df in db_df.groupby(grouping_columns):
                id_ref, lot, element_id = group_key
                
                # Take the first row for base information (all should be the same for grouped data)
                base_row = group_df.iloc[0]
                
                # Build base record with safe value extraction
                record = {
                    'element_id': str(element_id).strip(),
                    'description': str(base_row.get('description', 'No description')).strip(),
                    'nominal': self._safe_float_conversion(base_row.get('nominal', 0)),
                    'batch': str(lot).strip(),
                    'cavity': str(base_row.get('cavitat', '')).strip(),
                    'class': str(base_row.get('pieza', '')).strip(),
                    'datum_element_id': str(base_row.get('datum', '')).strip(),
                    'evaluation_type': 'Normal',  # Default evaluation type
                    'measuring_instrument': 'GOMPC'
                }
                
                # Handle tolerances safely
                lower_tol = self._safe_float_conversion(base_row.get('lower_tolerance', 0))
                upper_tol = self._safe_float_conversion(base_row.get('upper_tolerance', 0))
                
                # Set tolerances (None if zero or invalid)
                record['lower_tolerance'] = lower_tol if lower_tol != 0 else None
                record['upper_tolerance'] = upper_tol if upper_tol != 0 else None
                
                # Collect all measurements for this group (up to 5)
                measurements = []
                for _, measurement_row in group_df.head(5).iterrows():
                    measurement_value = self._safe_float_conversion(measurement_row.get('measurement_value'))
                    if measurement_value is not None:
                        measurements.append(measurement_value)
                
                # Fill measurement columns (measurement_1 to measurement_5)
                for i in range(1, 6):
                    if i <= len(measurements):
                        record[f'measurement_{i}'] = measurements[i-1]
                    else:
                        record[f'measurement_{i}'] = None
                
                # Add additional fields from database
                record['client'] = str(base_row.get('client', self.client_name)).strip()
                record['project_ref'] = str(id_ref).strip()
                record['timestamp'] = str(base_row.get('data_hora', ''))
                record['fase'] = str(base_row.get('fase', '')).strip()
                record['measurement_count'] = len(measurements)
                
                # Add some metadata for tracking
                record['db_group_key'] = f"{id_ref}_{lot}_{element_id}"
                record['latest_measurement_time'] = str(group_df['data_hora'].max())
                
                grouped_data.append(record)
                
                # Log group information
                self._log_message(
                    f"Grouped element '{element_id}' (Project: {id_ref}, Lot: {lot}) - {len(measurements)} measurements",
                    "DEBUG"
                )
            
            result_df = pd.DataFrame(grouped_data)
            
            # Sort by project, lot, and element for better organization
            if not result_df.empty:
                result_df = result_df.sort_values(['project_ref', 'batch', 'element_id'])
                result_df = result_df.reset_index(drop=True)
            
            self._log_message(
                f"Transformed {len(db_df)} database records into {len(result_df)} dimensional analysis records",
                "INFO"
            )
            
            # Log summary of what was loaded
            if not result_df.empty:
                projects = result_df['project_ref'].nunique()
                lots = result_df['batch'].nunique()
                elements = result_df['element_id'].nunique()
                total_measurements = result_df[[f'measurement_{i}' for i in range(1, 6)]].notna().sum().sum()
                
                self._log_message(
                    f"📊 Loaded data summary: {projects} projects, {lots} lots, {elements} elements, {total_measurements} total measurements",
                    "INFO"
                )
            
            return result_df
            
        except Exception as e:
            self._log_message(f"Error transforming database data: {str(e)}", "ERROR")
            raise

    def _safe_float_conversion(self, value) -> Optional[float]:
        """Safely convert value to float, returning None if invalid"""
        try:
            if value is None or pd.isna(value):
                return None
            
            if isinstance(value, str):
                value = value.strip()
                if value == '' or value.lower() in ['null', 'none', 'nan']:
                    return None
            
            converted = float(value)
            # Check for reasonable range (avoid extreme values)
            if -1e10 <= converted <= 1e10:
                return converted
            else:
                return None
                
        except (ValueError, TypeError, OverflowError):
            return None

    def _mark_unsaved_changes(self):
        """FIXED: Mark unsaved changes with optimized summary updates"""
        self.unsaved_changes = True

        # Update window title to show unsaved changes
        current_title = self.windowTitle()
        if "*" not in current_title:
            self.setWindowTitle(f"{current_title} *")

        # Record edit in summary widget (lightweight)
        if hasattr(self, "summary_widget") and self.summary_widget:
            try:
                self.summary_widget.record_edit("Table data modified")
            except Exception as e:
                self._log_message(f"Could not record edit: {str(e)}", "DEBUG")

        # Schedule delayed summary update to avoid performance issues
        if not hasattr(self, "_pending_summary_update"):
            self._pending_summary_update = True
            QTimer.singleShot(1000, self._delayed_summary_update)  # 1 second delay


    def _delayed_summary_update(self):
        """Delayed summary update with automatic reset flag"""
        try:
            if hasattr(self, "summary_widget") and hasattr(self, "table_manager"):
                df = self.table_manager._get_dataframe_from_tables()
                if not df.empty:
                    self.summary_widget.update_summary(table_data=df)
                    self._log_message("📊 Summary updated after delay", "DEBUG")
        except Exception as e:
            self._log_message(f"Delayed summary update failed: {str(e)}", "DEBUG")
        finally:
            # Reset the pending update flag
            if hasattr(self, "_pending_summary_update"):
                delattr(self, "_pending_summary_update")

    def _clear_unsaved_changes(self):
        """FIXED: Clear the unsaved changes flag with proper title handling"""
        self.unsaved_changes = False
        current_title = self.windowTitle()
        if current_title.endswith(" *"):
            self.setWindowTitle(current_title[:-2])

    def _populate_table_from_dataframe(self, df: pd.DataFrame):
        """Populate table from DataFrame - delegate to session manager with consistent formatting"""
        if hasattr(self, 'session_manager'):
            self.session_manager._populate_table_from_dataframe(df)
        else:
            self._log("❌ Session manager not available for table population", "ERROR")

    def _populate_table_row_from_series(self, table: QTableWidget, row_idx: int, row_data: pd.Series):
        """Helper to populate a single row with consistent formatting"""
        try:
            # Define formatting constants
            centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]  # cavity, nominal, tolerances, calculated
            bold_columns = [9, 10, 11]  # nominal, tolerances
            dropdown_columns = {
                3: ("class", self.table_manager.class_options),
                5: ("measuring_instrument", self.table_manager.instrument_options),
                6: ("unit", self.table_manager.unit_options),
                7: ("datum", self.table_manager.datum_options),
                8: ("evaluation_type", self.table_manager.evaluation_options),
                24: ("force_status", self.table_manager.force_status_options),
            }
            calculated_columns = [17, 18, 19, 20, 21, 22, 23]  # min, max, mean, std, pp, ppk, status

            # Populate each column
            for col_idx, col_name in enumerate(self.table_manager.display_columns):
                if col_idx >= table.columnCount():
                    break

                if col_idx in dropdown_columns:
                    # Create dropdown
                    field_info = dropdown_columns[col_idx]
                    combo = QComboBox()
                    combo.addItems(field_info[1])

                    # Set value from dataframe if exists
                    if col_name in row_data.index and pd.notna(row_data[col_name]):
                        value = str(row_data[col_name]).strip()
                        if value in field_info[1]:
                            combo.setCurrentText(value)
                        else:
                            # Set appropriate defaults
                            defaults = {
                                5: "3D Scanbox",
                                6: "mm",
                                8: "Normal",
                                24: "AUTO"
                            }
                            combo.setCurrentText(defaults.get(col_idx, field_info[1][0] if field_info[1] else ""))
                    else:
                        # Set defaults for empty values
                        defaults = {
                            5: "3D Scanbox",
                            6: "mm", 
                            8: "Normal",
                            24: "AUTO"
                        }
                        combo.setCurrentText(defaults.get(col_idx, ""))

                    combo.setStyleSheet(self.table_manager._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(row_idx, col_idx, combo)

                elif col_idx in calculated_columns:
                    # Create calculated column with read-only styling
                    if col_name in row_data.index and pd.notna(row_data[col_name]):
                        value = str(row_data[col_name])
                    else:
                        value = ""

                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                    # Apply specific styling for calculated columns
                    if col_idx == 23:  # Status column
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                        # Status color will be applied during analysis
                    elif col_idx in [21, 22]:  # Pp, Ppk columns
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor(248, 240, 255))  # Light purple
                        item.setForeground(QColor(138, 43, 226))   # Purple text
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    else:  # Other calculated columns
                        if col_idx in centered_columns:
                            item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor(240, 242, 245))  # Light gray
                        item.setForeground(QColor(40, 44, 52))     # Dark text
                        item.setFont(QFont("Segoe UI", 9))

                    table.setItem(row_idx, col_idx, item)

                else:
                    # Create regular input column
                    if col_name in row_data.index and pd.notna(row_data[col_name]):
                        value = str(row_data[col_name])
                    else:
                        value = ""

                    item = QTableWidgetItem(value)

                    # Apply consistent formatting
                    if col_idx in centered_columns:
                        item.setTextAlignment(Qt.AlignCenter)
                    
                    if col_idx in bold_columns:
                        font = QFont("Segoe UI", 9, QFont.Bold)
                    else:
                        font = QFont("Segoe UI", 9)
                    
                    item.setFont(font)
                    item.setForeground(QColor(40, 44, 52))  # Consistent dark text
                    
                    table.setItem(row_idx, col_idx, item)

        except Exception as e:
            self._log_message(f"⚠️ Error populating row {row_idx}: {str(e)}", "WARNING")


    def closeEvent(self, event):
        """FIXED: Handle window close event with proper cleanup"""
        try:
            # Check for unsaved changes
            if hasattr(self, "unsaved_changes") and self.unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before closing?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save,
                )

                if reply == QMessageBox.Save:
                    if hasattr(self, "session_manager"):
                        self.session_manager._save_session()
                    event.accept()
                elif reply == QMessageBox.Discard:
                    event.accept()
                else:
                    event.ignore()
                    return

            # Auto-save session before closing
            if hasattr(self, "session_manager") and hasattr(self, "unsaved_changes"):
                try:
                    self.session_manager._auto_save_session()
                except Exception as e:
                    self._log_message(f"Auto-save failed during close: {str(e)}", "WARNING")

            # Clean up summary widget properly
            if hasattr(self, "summary_widget") and self.summary_widget:
                try:
                    self.summary_widget.cleanup()
                    self._log_message("Summary widget cleaned up", "DEBUG")
                except Exception as e:
                    self._log_message(f"Summary widget cleanup error: {str(e)}", "DEBUG")

            # Clean up processing thread if running
            if hasattr(self, "processing_thread") and self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.terminate()
                self.processing_thread.wait(3000)  # Wait up to 3 seconds

            # Clean up any pending timers
            if hasattr(self, "_pending_summary_update"):
                delattr(self, "_pending_summary_update")

            # Log window closing
            self._log_message(
                f"Window closing - client: {getattr(self, 'client_name', 'Unknown')}, "
                f"project: {getattr(self, 'project_ref', 'Unknown')}, "
                f"batch: {getattr(self, 'batch_number', 'Unknown')}",
                "INFO",
            )

            event.accept()

        except Exception as e:
            self._log_message(f"Error during window close: {str(e)}", "ERROR")
            event.accept()  # Close anyway to prevent hanging

    def _set_ui_enabled(self, enabled: bool):
        """Enable/disable UI during processing"""
        self.mode_toggle.setEnabled(enabled)
        self.load_db_button.setEnabled(enabled)
        self.add_row_button.setEnabled(enabled)
        self.duplicate_row_button.setEnabled(enabled)
        self.delete_row_button.setEnabled(enabled)
        self.run_study_button.setEnabled(enabled)

    def _check_auto_load_database(self):
        """Check if user wants to auto-load data from database"""
        try:
            # Only offer auto-load if no data is already loaded
            if hasattr(self, 'table_manager') and self.table_manager:
                current_df = self.table_manager._get_dataframe_from_tables()
                if not current_df.empty:
                    self._log_message("Data already loaded, skipping auto-load check", "DEBUG")
                    return
            
            # Ask user if they want to load data from database
            reply = QMessageBox.question(
                self,
                "Auto-load Database Data",
                "Would you like to automatically load the latest measurement data from the database?\n\n"
                "• Source: mesuresqualitat table (machine: gompc_projectes)\n"
                "• Grouping: Up to 5 measurements per Element+Project+Lot combination\n"
                "• Data: Latest measurements for dimensional analysis",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._log_message("🔄 User opted for auto-loading database data", "INFO")
                self._load_data_from_database()
            else:
                self._log_message("User declined auto-loading database data", "DEBUG")
                
        except Exception as e:
            self._log_message(f"Error in auto-load check: {str(e)}", "ERROR")