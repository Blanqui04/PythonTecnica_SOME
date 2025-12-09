# src/gui/windows/capability_study_window.py - COMPLETE FIX
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

import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for thread safety

from typing import Dict

from src.gui.widgets.element_input_widget import ElementInputWidget
from .spc_chart_window import ChartDisplayWidget
from ..logging_config import logger
from ..utils.session_manager import CapabilitySessionManager
from src.services.capacity_study_service import perform_capability_study
from src.services.capability_session_service import CapabilitySessionService
from ..widgets.buttons import ModernButton, ActionButton, CompactButton
from ..widgets.inputs import ModernComboBox, ModernTextEdit
from ..utils.responsive_utils import ResponsiveWidget, ScreenUtils


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
            logger.info("=" * 80)
            logger.info("ELEMENT DATA BEING SENT TO STUDY:")
            
            for i, elem in enumerate(self.elements):
                logger.info(f"  Element {i+1}: {elem['element_id']}")
                logger.info(f"    Cavity: {elem.get('cavity', 'N/A')}")
                logger.info(f"    Values count: {len(elem.get('values', []))}")
                logger.info(f"    Has extrapolation: {elem.get('has_extrapolation', False)}")
                logger.info(f"    Original values count: {len(elem.get('original_values', []))}")
                if elem.get('has_extrapolation'):
                    logger.info(f"    Extrapolated values count: {len(elem.get('extrapolated_values', []))}")
                logger.info(f"    Has custom metrics: {elem.get('metrics') is not None}")
            
            logger.info("=" * 80)
            
            self.progress.emit(10, "Initializing study...")
            
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

class CapabilityStudyWindow(QDialog, ResponsiveWidget):
    def __init__(self, client, ref_project, batch_number, parent=None):
        QDialog.__init__(self, parent)
        ResponsiveWidget.__init__(self)
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
        self.setMinimumSize(
            int(1600 * self.screen_utils.scale_factor),
            int(900 * self.screen_utils.scale_factor)
        )
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        self.session_manager = CapabilitySessionManager()
        self.session_service = CapabilitySessionService()
        
        # Initialize screen utilities
        self.screen_utils = ScreenUtils()
        logger.info(f"Capability Study window initialized for {self.screen_utils.current_screen['category']} screen")
        
        self._init_ui()
        self._apply_styles()
        self._apply_responsive_scaling()
    
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
        content_layout.setContentsMargins(
            int(15 * self.screen_utils.scale_factor),
            int(15 * self.screen_utils.scale_factor),
            int(15 * self.screen_utils.scale_factor),
            int(15 * self.screen_utils.scale_factor)
        )
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {self.screen_utils.scale_value(2)}px solid #dee2e6;
                border-radius: {self.screen_utils.scale_value(8)}px;
                background-color: white;
            }}
            QTabBar::tab {{
                padding: {self.screen_utils.scale_value(10)}px {self.screen_utils.scale_value(20)}px;
                margin-right: {self.screen_utils.scale_value(5)}px;
                background-color: #f8f9fa;
                border: {self.screen_utils.scale_value(2)}px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: {self.screen_utils.scale_value(6)}px;
                border-top-right-radius: {self.screen_utils.scale_value(6)}px;
                font-weight: 500;
                font-size: {self.screen_utils.scale_value(10)}pt;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                color: #007bff;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
            }}
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
        header.setFixedHeight(int(60 * self.screen_utils.scale_factor))
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(
            self.screen_utils.scale_value(20),
            self.screen_utils.scale_value(10),
            self.screen_utils.scale_value(20),
            self.screen_utils.scale_value(10)
        )
        
        title = QLabel(f"🔬 Capability Study - {self.client} / {self.ref_project} / Batch {self.batch_number}")
        title.setFont(QFont("Segoe UI", int(14 * self.screen_utils.scale_factor), QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title)
        layout.addStretch()
        
        return header
    
    def _create_toolbar(self):
        """Create toolbar with session controls"""
        toolbar = QToolBar()
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: #f8f9fa;
                border: {self.screen_utils.scale_value(1)}px solid #dee2e6;
                padding: {self.screen_utils.scale_value(8)}px;
                spacing: {self.screen_utils.scale_value(10)}px;
            }}
            QToolButton {{
                background-color: white;
                border: {self.screen_utils.scale_value(1)}px solid #dee2e6;
                border-radius: {self.screen_utils.scale_value(4)}px;
                padding: {self.screen_utils.scale_value(8)}px {self.screen_utils.scale_value(16)}px;
                margin: 0 {self.screen_utils.scale_value(5)}px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background-color: #e9ecef;
                border-color: #adb5bd;
            }}
            QToolButton:pressed {{
                background-color: #dee2e6;
            }}
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
        status_bar.setFixedHeight(int(40 * self.screen_utils.scale_factor))
        
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
        
        # Store session data - FIXED
        study_data = self.element_input_widget.get_study_data()
        self.session_data = {
            "client": self.client,
            "ref_project": self.ref_project,
            "batch_number": self.batch_number,
            "elements": study_data['elements'],
            "chart_config": study_data['chart_config'],
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
        # UPDATE: Configure control charts display based on chart config
        self._update_control_charts_display(study_data['chart_config'])
        
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
        splitter.setSizes([
            int(350 * self.screen_utils.scale_factor),
            int(1250 * self.screen_utils.scale_factor)
        ])
        
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
        control_widget.setMinimumWidth(int(320 * self.screen_utils.scale_factor))
        control_widget.setMaximumWidth(int(400 * self.screen_utils.scale_factor))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor)
        )
        layout.setSpacing(int(20 * self.screen_utils.scale_factor))
        
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
        self.element_combo.setMinimumHeight(int(32 * self.screen_utils.scale_factor))
        
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
        self.element_info.setMaximumHeight(int(100 * self.screen_utils.scale_factor))
        self.element_info.setMinimumHeight(int(80 * self.screen_utils.scale_factor))
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
        layout.setSpacing(int(8 * self.screen_utils.scale_factor))
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = CompactButton("All")
        select_all_btn.clicked.connect(self._select_all_charts)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = CompactButton("None")
        select_none_btn.clicked.connect(self._select_no_charts)
        button_layout.addWidget(select_none_btn)
        
        layout.addLayout(button_layout)
        
        # DYNAMIC chart type checkboxes based on study configuration
        self.chart_type_checkboxes = {}
        
        # Base charts (always available)
        base_charts = [
            ("capability", "Capability"),
            ("normality", "Normality"),
            ("distribution", "Distribution"),
        ]
        
        for chart_type, display_name in base_charts:
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setMinimumHeight(int(22 * self.screen_utils.scale_factor))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_chart_selection_changed)
            layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type] = checkbox
        
        # Control charts - will be populated after study based on configuration
        self.control_chart_group = QWidget()
        self.control_chart_layout = QVBoxLayout(self.control_chart_group)
        self.control_chart_layout.setContentsMargins(0, 0, 0, 0)
        self.control_chart_layout.setSpacing(int(8 * self.screen_utils.scale_factor))
        layout.addWidget(self.control_chart_group)
        
        group.setLayout(layout)
        return group

    def _update_control_charts_display(self, chart_config: Dict):
        """Update control charts based on study configuration"""
        # Clear existing control chart checkboxes
        while self.control_chart_layout.count():
            item = self.control_chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add appropriate control charts based on configuration
        chart_type = chart_config.get('type', 'i_mr')
        group_size = chart_config.get('group_size', 5)
        
        if chart_type == 'i_mr':
            control_charts = [
                ("individuals", "I Chart (Individuals)"),
                ("moving_range", "MR Chart (Moving Range)"),
            ]
            info_text = "Using Individual and Moving Range charts"
        elif chart_type == 'xr':
            control_charts = [
                ("xbar", f"X̄ Chart (Average, n={group_size})"),
                ("r_chart", f"R Chart (Range, n={group_size})"),
            ]
            info_text = f"Using X̄-R charts with subgroup size {group_size}"
        elif chart_type == 'xs':
            control_charts = [
                ("xbar", f"X̄ Chart (Average, n={group_size})"),
                ("s_chart", f"S Chart (Std Dev, n={group_size})"),
            ]
            info_text = f"Using X̄-S charts with subgroup size {group_size}"
        else:
            control_charts = []
            info_text = "No control charts configured"
        
        # Add info label
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #6c757d; font-size: 9pt; font-style: italic; padding: 5px;")
        info_label.setWordWrap(True)
        self.control_chart_layout.addWidget(info_label)
        
        # Add checkboxes for control charts
        for chart_type_name, display_name in control_charts:
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setMinimumHeight(int(22 * self.screen_utils.scale_factor))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_chart_selection_changed)
            self.control_chart_layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type_name] = checkbox
    
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
        self.stats_info.setMaximumHeight(int(120 * self.screen_utils.scale_factor))
        self.stats_info.setMinimumHeight(int(100 * self.screen_utils.scale_factor))
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
            info_parts.append(f"Nominal: {element_data['nominal']:.2f}")
        if 'tolerance' in element_data and isinstance(element_data['tolerance'], list):
            tol_minus, tol_plus = element_data['tolerance']
            info_parts.append(f"Tolerance: +{tol_plus:.2f} / {tol_minus:.2f}")
        if 'sample_size' in element_data:
            info_parts.append(f"Sample Size: {element_data['sample_size']}")
        
        self.element_info.setPlainText("\n".join(info_parts))
        
        # Update statistics display
        stats_parts = []
        if 'mean' in element_data and element_data['mean'] is not None:
            stats_parts.append(f"Mean: {element_data['mean']:.2f}")
        if 'cp' in element_data and element_data['cp'] is not None:
            stats_parts.append(f"Cp: {element_data['cp']:.2f}")
        if 'cpk' in element_data and element_data['cpk'] is not None:
            stats_parts.append(f"Cpk: {element_data['cpk']:.2f}")
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
        """Save current session - FIXED overwrite handling"""
        try:
            session_data = {
                "client": self.client,
                "ref_project": self.ref_project,
                "batch_number": self.batch_number,
                "timestamp": datetime.now().isoformat(),
                "version": "2.0"
            }
            
            study_data = self.element_input_widget.get_study_data()
            session_data["elements"] = study_data['elements']
            session_data["chart_config"] = study_data['chart_config']  # Changed from 'extrapolation'
            
            if self.study_results:
                session_data["results"] = {
                    "elements_count": len(self.elements_summary) if self.elements_summary else 0,
                    "has_charts": bool(self.chart_service),
                    "timestamp": datetime.now().isoformat()
                }
            
            default_name = f"{self.client}_{self.ref_project}_{self.batch_number}_session.json"
            
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Session", default_name,
                "Session Files (*.json);;All Files (*)"
            )
            
            if not file_name:
                return
            
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            # CRITICAL FIX: Handle existing file properly
            try:
                # Always try to write - QFileDialog already asked about overwrite
                os.makedirs(os.path.dirname(file_name) or '.', exist_ok=True)
                
                # Write to temp file first, then rename (atomic operation)
                temp_file = file_name + ".tmp"
                with open(temp_file, "w", encoding='utf-8') as f:
                    json.dump(session_data, f, indent=4, ensure_ascii=False)
                
                # Remove old file if exists, then rename temp
                if os.path.exists(file_name):
                    os.remove(file_name)
                os.rename(temp_file, file_name)
                
                logger.info(f"Session saved: {file_name}")
                
                QMessageBox.information(
                    self, "Session Saved", 
                    f"Session saved successfully:\n{file_name}\n\nElements: {len(session_data['elements'])}"
                )
                
            except PermissionError:
                QMessageBox.critical(
                    self, "Save Error", 
                    f"Permission denied:\n{file_name}\n\nFile may be open in another program."
                )
            except Exception as write_error:
                QMessageBox.critical(
                    self, "Save Error", 
                    f"Failed to save:\n{write_error}"
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error: {e}")
            logger.error(f"Save session error: {e}", exc_info=True)

    def load_session(self):
        """Load session data from file - COMPLETELY FIXED"""
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
            
            with open(file_name, "r", encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Validate session data structure
            required_fields = ["client", "ref_project", "elements"]
            missing_fields = [f for f in required_fields if f not in loaded_data]
            
            if missing_fields:
                QMessageBox.warning(
                    self, "Invalid Session", 
                    f"Session file is missing required fields: {', '.join(missing_fields)}"
                )
                return
            
            # Update window state
            self.client = loaded_data["client"]
            self.ref_project = loaded_data["ref_project"]
            self.batch_number = loaded_data.get("batch_number", "")
            
            self.setWindowTitle(
                f"Capability Study - {self.client} - {self.ref_project} - Batch: {self.batch_number}"
            )
            
            # Restore elements and chart configuration data
            elements = loaded_data.get("elements", [])
            chart_config = loaded_data.get("chart_config", {})  # Changed from 'extrapolation'
            
            # Load into widget
            self.element_input_widget.load_study_data({
                'elements': elements,
                'chart_config': chart_config
            })
            
            # Update status
            self.status_label.setText("Session loaded - Run study to generate charts")
            
            QMessageBox.information(
                self, "Session Loaded", 
                f"Session loaded successfully:\n\n"
                f"Client: {self.client}\n"
                f"Project: {self.ref_project}\n"
                f"Batch: {self.batch_number}\n"
                f"Elements: {len(elements)}"
            )
            logger.info(f"Session loaded: {file_name}")
        
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, "Load Error", 
                f"Failed to parse session file:\n{e}\n\nThe file may be corrupted."
            )
            logger.error(f"JSON decode error loading session: {e}", exc_info=True)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load session:\n{e}")
            logger.error(f"Error loading session: {e}", exc_info=True)

    def export_to_excel(self):
        """Export study results to Excel file - FIXED TO USE SPC EXPORT SERVICE"""
        if not self.study_results:
            QMessageBox.warning(self, "No Results", "No study results to export")
            return
        
        try:
            from src.services.spc_export_service import ExcelReportService
            
            # Create export service
            export_service = ExcelReportService(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number
            )
            
            # Initialize service
            if not export_service.initialize_services():
                QMessageBox.critical(self, "Export Error", "Failed to initialize export service")
                return
            
            # Get file name from user
            options = QFileDialog.Options()
            default_name = f"{self.client}_{self.ref_project}_{self.batch_number}_report.xlsx"
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                "Export to Excel",
                default_name,
                "Excel Files (*.xlsx);;All Files (*)",
                options=options
            )
            
            if not file_name:
                return
            
            if not file_name.endswith(".xlsx"):
                file_name += ".xlsx"
            
            # Extract directory and filename
            from pathlib import Path
            file_path = Path(file_name)
            custom_filename = file_path.name
            custom_output_path = str(file_path.parent)
            
            # Generate report
            success, result = export_service.generate_excel_only(
                part_description=f"{self.ref_project} - Batch {self.batch_number}",
                drawing_number=self.ref_project,
                methodology="cmm",
                facility="Manufacturing Facility",
                dimension_class="critical",
                open_file=True,
                custom_filename=custom_filename,
                custom_output_path=custom_output_path
            )
            
            if success:
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Results exported to Excel:\n{result}"
                )
                logger.info(f"Results exported to Excel: {result}")
            else:
                QMessageBox.critical(
                    self, "Export Error", 
                    f"Failed to export results:\n{result}"
                )
                logger.error(f"Export error: {result}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{e}")
            logger.error(f"Error exporting results: {e}", exc_info=True)
    
    def _apply_responsive_scaling(self):
        """Apply responsive scaling to all elements"""
        try:
            scale_factor = self.screen_utils.scale_factor
            margins = self.screen_utils.get_adaptive_margins()
            spacing = self.screen_utils.get_adaptive_spacing()
            
            # Scale window minimum size
            base_width, base_height = 1600, 900
            scaled_width = int(base_width * scale_factor)
            scaled_height = int(base_height * scale_factor)
            self.setMinimumSize(scaled_width, scaled_height)
            
            # Apply responsive scaling to main element input widget
            if hasattr(self, 'element_input_widget'):
                self.element_input_widget.apply_responsive_scaling()
            
            # Scale fonts for labels and buttons
            self._apply_responsive_fonts(scale_factor)
            
            logger.info(f"Capability Study responsive scaling applied: {scale_factor}x")
            
        except Exception as e:
            logger.warning(f"Could not apply responsive scaling to Capability Study: {e}")
    
    def _apply_responsive_fonts(self, scale_factor):
        """Apply responsive font scaling"""
        try:
            # Scale header fonts
            if hasattr(self, 'findChild'):
                for label in self.findChildren(QLabel):
                    font = label.font()
                    if font.pointSize() > 0:
                        new_size = max(8, int(font.pointSize() * scale_factor))
                        font.setPointSize(new_size)
                        label.setFont(font)
                
                # Scale button fonts
                for button in self.findChildren(QPushButton):
                    font = button.font()
                    if font.pointSize() > 0:
                        new_size = max(8, int(font.pointSize() * scale_factor))
                        font.setPointSize(new_size)
                        button.setFont(font)
                        
        except Exception as e:
            logger.warning(f"Could not apply font scaling: {e}")