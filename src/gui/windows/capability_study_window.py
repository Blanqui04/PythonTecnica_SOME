# src/gui/windows/capability_study_window.py - FIXED VERSION
import os
import json
import math
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QHBoxLayout, 
    QLabel, QMessageBox, QFrame, QPushButton, QFileDialog, 
    QProgressDialog, QToolBar, QAction, QGroupBox, QScrollArea, 
    QGridLayout, QSplitter, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

from src.gui.widgets.element_input_widget import ElementInputWidget
from .spc_chart_window import ChartDisplayWidget
from ..logging_config import logger
from ..utils.session_manager import CapabilitySessionManager
from src.services.capacity_study_service import perform_capability_study
from src.services.data_export_service import DataExportService
from src.services.capability_calculator_service import CapabilityCalculatorService
from src.services.capability_session_service import CapabilitySessionService
from ..widgets.buttons import ModernButton, ActionButton, CompactButton
from ..widgets.inputs import ModernComboBox, ModernTextEdit


class StudyWorker(QThread):
    """Worker thread for performing capability study"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, ref_project, batch_number, elements, extrap_config):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.elements = elements
        self.extrap_config = extrap_config
    
    def run(self):
        try:
            logger.info(f"Starting capability study for {len(self.elements)} elements")
            
            self.progress.emit(10, "Initializing study...")
            
            # Perform the complete capability study including chart generation
            result = perform_capability_study(
                self.client,
                self.ref_project,
                self.elements,
                self.extrap_config,
                batch_number=self.batch_number
            )
            
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error occurred")
                self.error.emit(error_msg)
                return
            
            self.progress.emit(100, "Study completed!")
            self.result_ready.emit(result)
            
        except Exception as e:
            logger.error(f"Study worker error: {e}", exc_info=True)
            self.error.emit(str(e))


class CapabilityStudyWindow(QDialog):
    def __init__(self, client, ref_project, batch_number, parent=None):
        super().__init__(parent)
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.session_data = {}
        self.study_results = None
        self.chart_service = None
        self.pending_charts = {}
        self.elements_summary = {}
        self.current_element_key = None
        
        self.setWindowTitle(f"Capability Study - {client} - {ref_project} - Batch: {batch_number}")
        self.setMinimumSize(1600, 900)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        self.session_manager = CapabilitySessionManager()
        self.calculator_service = CapabilityCalculatorService()
        self.session_service = CapabilitySessionService()
        
        self._init_ui()
        self._apply_styles()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Main content with tabs
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 5px;
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Tab 1: Configuration
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        self.element_input_widget = ElementInputWidget(
            client=self.client,
            project_reference=self.ref_project,
            batch_lot=self.batch_number
        )
        self.element_input_widget.study_requested.connect(self._on_study_requested)
        config_layout.addWidget(self.element_input_widget)
        
        self.tabs.addTab(config_tab, "📝 Configuration")
        
        # Tab 2: Results (will be populated after study)
        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout(self.results_tab)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        
        placeholder = QLabel("Run study to see results and charts")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 16pt;
                padding: 100px;
                font-style: italic;
            }
        """)
        self.results_layout.addWidget(placeholder)
        
        self.tabs.addTab(self.results_tab, "📊 Results")
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)
        
        # Status bar
        self.status_bar = self._create_status_bar()
        main_layout.addWidget(self.status_bar)
    
    def _create_header(self):
        """Create header section"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border: none;
            }
        """)
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        title = QLabel(f"🔬 Capability Study - {self.client} / {self.ref_project} / Batch {self.batch_number}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title)
        layout.addStretch()
        
        return header
    
    def _create_toolbar(self):
        """Create toolbar with session controls"""
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                spacing: 10px;
            }
            QToolButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 0 5px;
                font-weight: 500;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
            }
        """)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Save session
        save_action = QAction("💾 Save Session", self)
        save_action.triggered.connect(self.save_session)
        toolbar.addAction(save_action)
        
        # Load session
        load_action = QAction("📂 Load Session", self)
        load_action.triggered.connect(self.load_session)
        toolbar.addAction(load_action)
        
        toolbar.addSeparator()
        
        # Export
        export_action = QAction("📤 Export to Excel", self)
        export_action.triggered.connect(self.export_to_excel)
        export_action.setEnabled(False)
        self.export_action = export_action
        toolbar.addAction(export_action)
        
        return toolbar
    
    def _create_status_bar(self):
        """Create status bar"""
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 5px 15px;
            }
        """)
        status_bar.setFixedHeight(40)
        
        layout = QHBoxLayout(status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M"))
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(time_label)
        
        return status_bar
    
    def _apply_styles(self):
        """Apply global styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QMessageBox {
                background-color: white;
            }
        """)
    
    def _on_study_requested(self, elements, extrap_config):
        """Handle study request from element input widget"""
        if not elements:
            QMessageBox.warning(self, "No Data", "No elements to analyze")
            return
        
        logger.info(f"Study requested for {len(elements)} elements")
        logger.info(f"Extrapolation config: {extrap_config}")
        
        # Create progress dialog
        progress = QProgressDialog(self)
        progress.setWindowTitle("Performing Capability Study")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setRange(0, 100)
        
        # Create and start worker thread
        self.worker = StudyWorker(
            self.client, 
            self.ref_project,
            self.batch_number,
            elements, 
            extrap_config
        )
        
        self.worker.progress.connect(
            lambda val, msg: (progress.setValue(val), progress.setLabelText(msg))
        )
        self.worker.result_ready.connect(
            lambda results: self._on_study_completed(results, progress)
        )
        self.worker.error.connect(
            lambda err: self._on_study_error(err, progress)
        )
        
        self.worker.start()
        progress.exec_()
    
    def _on_study_completed(self, results, progress):
        """Handle study completion"""
        progress.close()
        
        logger.info("Study completed, processing results...")
        
        # Extract results
        self.study_results = results.get("study_results")
        self.chart_service = results.get("chart_service")
        if self.chart_service:
            self.chart_service.chart_data_ready.connect(self._create_chart_in_main_thread)
        self.elements_summary = results.get("elements_summary", {})
        chart_results = results.get("chart_results", {})
        
        # Store session data
        self.session_data = {
            "client": self.client,
            "ref_project": self.ref_project,
            "batch_number": self.batch_number,
            "elements": self.element_input_widget.get_study_data()['elements'],
            "extrapolation": self.element_input_widget.get_study_data()['extrapolation'],
            "results": self.study_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enable export
        self.export_action.setEnabled(True)
        
        # Update status
        total_charts = sum(len(elem_results) for elem_results in chart_results.values())
        successful_charts = sum(
            sum(elem_results.values()) for elem_results in chart_results.values()
        )
        
        self.status_label.setText(
            f"✅ Study completed - {len(self.elements_summary)} elements analyzed, "
            f"{successful_charts}/{total_charts} charts generated"
        )
        
        # Build and show results tab
        self._build_results_tab()
        
        # Switch to results tab
        self.tabs.setCurrentWidget(self.results_tab)
        
        QMessageBox.information(
            self,
            "Study Complete",
            f"Successfully analyzed {len(self.elements_summary)} element(s).\n"
            f"Generated {successful_charts}/{total_charts} charts.\n\n"
            "You can now:\n"
            "• View and analyze charts in the Results tab\n"
            "• Export results to Excel\n"
            "• Save the session for later"
        )
    
    def _on_study_error(self, error, progress):
        """Handle study error"""
        progress.close()
        QMessageBox.critical(self, "Study Error", f"An error occurred during the study:\n\n{error}")
        self.status_label.setText("❌ Error occurred during study")
        logger.error(f"Study error: {error}")
    
    def _create_chart_in_main_thread(self, chart_data):
        """Create chart in main thread when data is ready"""
        try:
            if self.chart_service and chart_data:
                element_key = chart_data['element_key']
                chart_type = chart_data['chart_type']
                
                success = self.chart_service.chart_manager.create_chart(
                    element_key,
                    chart_type,
                    show=False,
                    save=True,
                    data=chart_data['data'],
                    config=chart_data['config']
                )
                
                if success:
                    self.status_label.setText(f"Created chart: {chart_type} for {element_key}")
                    
        except Exception as e:
            logger.error(f"Error creating chart in main thread: {e}")
    
    def _build_results_tab(self):
        """Build the complete results tab with embedded chart viewer"""
        # Clear existing content
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create main splitter for control panel and charts
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Controls
        control_panel = self._create_results_control_panel()
        splitter.addWidget(control_panel)
        
        # Right panel: Chart display
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
        """)
        
        self.chart_display = ChartDisplayWidget()
        scroll_area.setWidget(self.chart_display)
        splitter.addWidget(scroll_area)
        
        # Set splitter proportions
        splitter.setSizes([350, 1250])
        
        self.results_layout.addWidget(splitter)
        
        # Load first element if available
        if self.elements_summary:
            first_element_key = list(self.elements_summary.keys())[0]
            self.current_element_key = first_element_key
            self._load_element_charts(first_element_key)
    
    def _create_results_control_panel(self):
        """Create control panel for results tab"""
        control_widget = QWidget()
        control_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        control_widget.setMinimumWidth(320)
        control_widget.setMaximumWidth(400)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Element selection group
        element_group = self._create_element_selection_group()
        layout.addWidget(element_group)
        
        # Chart type selection group
        chart_group = self._create_chart_type_selection_group()
        layout.addWidget(chart_group)
        
        # Statistics group
        stats_group = self._create_statistics_display_group()
        layout.addWidget(stats_group)
        
        layout.addStretch()
        control_widget.setLayout(layout)
        
        return control_widget
    
    def _create_element_selection_group(self):
        """Create element selection group"""
        group = QGroupBox("🔍 Element Selection")
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
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Element combo box
        self.element_combo = ModernComboBox()
        self.element_combo.setMinimumHeight(32)
        
        # Populate with elements
        for element_key in self.elements_summary.keys():
            element_data = self.elements_summary[element_key]
            cavity = element_data.get('cavity', '')
            
            # Create display name
            if cavity:
                display_name = f"{element_key} - Cavity {cavity}"
            else:
                display_name = element_key
            
            self.element_combo.addItem(display_name, element_key)
        
        self.element_combo.currentIndexChanged.connect(self._on_element_selection_changed)
        layout.addWidget(self.element_combo)
        
        # Element info display
        self.element_info = ModernTextEdit()
        self.element_info.setMaximumHeight(100)
        self.element_info.setMinimumHeight(80)
        self.element_info.setReadOnly(True)
        self.element_info.setWordWrapMode(True)
        layout.addWidget(self.element_info)
        
        group.setLayout(layout)
        return group
    
    def _create_chart_type_selection_group(self):
        """Create chart type selection group"""
        group = QGroupBox("📈 Chart Types")
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
        layout.setSpacing(8)
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = CompactButton("All")
        select_all_btn.clicked.connect(self._select_all_charts)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = CompactButton("None")
        select_none_btn.clicked.connect(self._select_no_charts)
        button_layout.addWidget(select_none_btn)
        
        layout.addLayout(button_layout)
        
        # Chart type checkboxes
        self.chart_type_checkboxes = {}
        chart_types = [
            ("capability", "Capability"),
            ("normality", "Normality"),
            ("extrapolation", "Extrapolation"),
            ("individuals", "Individuals"),
            ("moving_range", "Moving Range"),
        ]
        
        for chart_type, display_name in chart_types:
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setMinimumHeight(22)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_chart_selection_changed)
            layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type] = checkbox
        
        group.setLayout(layout)
        return group
    
    def _create_statistics_display_group(self):
        """Create statistics display group"""
        group = QGroupBox("📊 Statistics")
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
        
        layout = QVBoxLayout()
        
        self.stats_info = ModernTextEdit()
        self.stats_info.setMaximumHeight(120)
        self.stats_info.setMinimumHeight(100)
        self.stats_info.setReadOnly(True)
        self.stats_info.setWordWrapMode(True)
        layout.addWidget(self.stats_info)
        
        group.setLayout(layout)
        return group
    
    def _on_element_selection_changed(self, index):
        """Handle element selection change"""
        if index >= 0:
            element_key = self.element_combo.itemData(index)
            if element_key and element_key != self.current_element_key:
                self.current_element_key = element_key
                self._load_element_charts(element_key)
    
    def _on_chart_selection_changed(self):
        """Handle chart type selection change"""
        if self.current_element_key:
            self._load_element_charts(self.current_element_key)
    
    def _select_all_charts(self):
        """Select all chart types"""
        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setChecked(True)
    
    def _select_no_charts(self):
        """Deselect all chart types"""
        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setChecked(False)
    
    def _load_element_charts(self, element_key):
        """Load charts for the selected element"""
        if not self.chart_service or element_key not in self.elements_summary:
            logger.warning(f"Cannot load charts for element: {element_key}")
            return
        
        logger.info(f"Loading charts for element: {element_key}")
        
        # Get element data
        element_data = self.elements_summary[element_key]
        cavity = element_data.get('cavity', '')
        
        # Update element info display
        info_parts = [f"Element: {element_key}"]
        if cavity:
            info_parts.append(f"Cavity: {cavity}")
        if 'nominal' in element_data:
            info_parts.append(f"Nominal: {element_data['nominal']:.3f}")
        if 'tolerance' in element_data and isinstance(element_data['tolerance'], list):
            tol_minus, tol_plus = element_data['tolerance']
            info_parts.append(f"Tolerance: {tol_minus:.3f} / +{tol_plus:.3f}")
        if 'sample_size' in element_data:
            info_parts.append(f"Sample Size: {element_data['sample_size']}")
        
        self.element_info.setPlainText("\n".join(info_parts))
        
        # Update statistics display
        stats_parts = []
        if 'mean' in element_data and element_data['mean'] is not None:
            stats_parts.append(f"Mean: {element_data['mean']:.4f}")
        if 'cp' in element_data and element_data['cp'] is not None:
            stats_parts.append(f"Cp: {element_data['cp']:.3f}")
        if 'cpk' in element_data and element_data['cpk'] is not None:
            stats_parts.append(f"Cpk: {element_data['cpk']:.3f}")
        if element_data.get('has_extrapolation', False):
            stats_parts.append(f"Extrapolated: Yes ({element_data.get('extrapolated_count', 0)} values)")
        
        self.stats_info.setPlainText("\n".join(stats_parts) if stats_parts else "No statistics available")
        
        # Clear and load charts
        self.chart_display.clear_charts()
        
        for chart_type, checkbox in self.chart_type_checkboxes.items():
            if checkbox.isChecked():
                # Get chart path from service
                chart_path = self.chart_service.get_chart_file_path(
                    element_key, 
                    chart_type, 
                    cavity
                )
                
                if os.path.exists(chart_path):
                    self.chart_display.add_chart(
                        chart_path, 
                        chart_type, 
                        element_id=element_key,
                        cavity=cavity
                    )
                    logger.debug(f"Added chart: {chart_type} for {element_key}")
                else:
                    logger.warning(f"Chart not found: {chart_path}")
    
    def save_session(self):
        """Save current session data to file"""
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Session",
                "",
                "Session Files (*.json);;All Files (*)",
                options=options
            )
            
            if not file_name:
                return
            
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            with open(file_name, "w") as f:
                json.dump(self.session_data, f, indent=4)
            
            QMessageBox.information(self, "Session Saved", f"Session saved successfully:\n{file_name}")
            logger.info(f"Session saved: {file_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save session:\n{e}")
            logger.error(f"Error saving session: {e}")
    
    def load_session(self):
        """Load session data from file"""
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(
                self, 
                "Load Session",
                "",
                "Session Files (*.json);;All Files (*)",
                options=options
            )
            
            if not file_name:
                return
            
            with open(file_name, "r") as f:
                self.session_data = json.load(f)
            
            # Restore window state
            self.client = self.session_data["client"]
            self.ref_project = self.session_data["ref_project"]
            self.batch_number = self.session_data["batch_number"]
            
            self.setWindowTitle(f"Capability Study - {self.client} - {self.ref_project} - Batch: {self.batch_number}")
            
            # Restore elements and extrapolation data
            elements = self.session_data["elements"]
            extrapolation = self.session_data["extrapolation"]
            
            self.element_input_widget.set_study_data(elements, extrapolation)
            
            QMessageBox.information(self, "Session Loaded", "Session loaded successfully")
            logger.info(f"Session loaded: {file_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load session:\n{e}")
            logger.error(f"Error loading session: {e}")
    
    def export_to_excel(self):
        """Export study results to Excel file"""
        if not self.study_results:
            QMessageBox.warning(self, "No Results", "No study results to export")
            return
        
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                "Export to Excel",
                "",
                "Excel Files (*.xlsx);;All Files (*)",
                options=options
            )
            
            if not file_name:
                return
            
            if not file_name.endswith(".xlsx"):
                file_name += ".xlsx"
            
            # Prepare data for export
            export_data = {
                "client": self.client,
                "ref_project": self.ref_project,
                "batch_number": self.batch_number,
                "results": self.study_results
            }
            
            # Use service to perform export
            export_service = DataExportService()
            export_service.export_capability_study_results(export_data, file_name)
            
            QMessageBox.information(self, "Export Successful", f"Results exported to Excel:\n{file_name}")
            logger.info(f"Results exported to Excel: {file_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{e}")
            logger.error(f"Error exporting results: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit? Unsaved data may be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()