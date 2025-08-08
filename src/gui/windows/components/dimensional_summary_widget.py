# src/gui/windows/components/dimensional_summary_widget.py - ENHANCED SOPHISTICATED VERSION
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QGroupBox, 
    QTextEdit, QProgressBar, QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QScrollArea, QPushButton)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import pandas as pd
from typing import List, Optional
from src.models.dimensional.dimensional_result import DimensionalResult
from src.gui.windows.components.helpers.summary_circular_progress import CircularProgressWidget
from src.gui.windows.components.helpers.summary_metric_card import CompactMetricCard
from src.gui.windows.components.helpers.summary_pie_chart import StatusPieChart


class SummaryWidget(QWidget):
    """Enhanced summary widget with sophisticated layout and comprehensive analysis"""
    
    update_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._reset_metrics()
        self._last_update = datetime.now()
        self._update_threshold = 1.0
        
        # Data tracking for comparisons
        self.original_data = {}
        self.current_data = {}
        self.session_loaded = False
        self.results = []  # Store results for detailed analysis
        
        # Initialize UI
        self._init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._periodic_refresh)
        self.refresh_timer.start(3000)

    def _periodic_refresh(self):
        """Periodic refresh with throttling"""
        try:
            current_time = datetime.now()
            if (current_time - self._last_update).total_seconds() > 5.0:  # 5 second throttle
                # Only refresh if we have data
                if self.metrics.get("total_dimensions", 0) > 0:
                    self._update_all_content()
                    self._last_update = current_time
        except Exception as e:
            self._log_message(f"❌ Error in periodic refresh: {str(e)}", "ERROR")

    def _reset_metrics(self):
        """Reset all metrics to default values"""
        self.metrics = {
            # Basic counts
            "total_dimensions": 0,
            "studies_run": 0,
            "edits_made": 0,
            
            # Status counts
            "passed": 0,
            "failed": 0,
            "warning": 0,
            "ted": 0,
            "to_check": 0,
            "success_rate": 0.0,
            
            # Data quality
            "completeness": 0.0,
            "dimensions_with_measurements": 0,
            "total_measurements": 0,
            
            # Evaluation type breakdown
            "normal_dimensions": 0,
            "gdt_dimensions": 0,
            "basic_dimensions": 0,
            "informative_dimensions": 0,
            "note_dimensions": 0,
            
            # Tolerance analysis
            "unilateral_tolerances": 0,
            "bilateral_tolerances": 0,
            "zero_nominal_gdt": 0,
            
            # Process capability (CC, SC, IC only)
            "cc_dimensions": 0,
            "sc_dimensions": 0,
            "ic_dimensions": 0,
            "avg_pp": 0.0,
            "avg_ppk": 0.0,
            "capability_count": 0,
            
            # Cavity analysis
            "cavity_breakdown": {},
            
            # Change tracking
            "dimensions_modified": 0,
            "dimensions_added": 0,
            "dimensions_deleted": 0,
            "modification_details": [],
            
            # Session info
            "session_start": datetime.now(),
            
            # Evaluation type status breakdown
            "eval_type_status": {}
        }

    def _init_ui(self):
        """Initialize sophisticated UI with proper space utilization"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Session header
        self.session_header = self._create_session_header()
        layout.addWidget(self.session_header)

        # Main tabs for different analysis views
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-bottom-color: transparent;
                border-radius: 6px 6px 0 0;
                padding: 10px 16px;
                margin-right: 2px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5dbdb;
            }
        """)

        # Create tabs
        self.main_tabs.addTab(self._create_overview_tab(), "📊 Overview")
        self.main_tabs.addTab(self._create_status_analysis_tab(), "🎯 Status Analysis")
        self.main_tabs.addTab(self._create_quality_tab(), "❌ Quality Issues")
        self.main_tabs.addTab(self._create_capability_tab(), "📈 Process Capability")
        self.main_tabs.addTab(self._create_evaluation_tab(), "🔧 Evaluation Types")
        self.main_tabs.addTab(self._create_comparison_tab(), "🔄 Data Changes")

        layout.addWidget(self.main_tabs)
        self.setLayout(layout)

    def record_edit(self, description: str):
        """Record an edit action"""
        try:
            self.metrics["edits_made"] += 1
            self._log_message(f"✏️ Edit recorded: {description}")
        except Exception as e:
            self._log_message(f"❌ Error recording edit: {str(e)}", "ERROR")

    def reset_widget(self):
        """Reset widget to initial state"""
        try:
            self._reset_metrics()
            self.original_data = {}
            self.current_data = {}
            self.session_loaded = False
            self._update_all_content()
            self._log_message("🔄 Summary widget reset successfully")
        except Exception as e:
            self._log_message(f"❌ Error resetting widget: {str(e)}", "ERROR")

    def _create_session_header(self) -> QWidget:
        """Create compact session info header"""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setFixedHeight(40)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2c3e50, stop:1 #3498db);
                color: white;
                border-radius: 4px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8)
        
        self.session_label = QLabel("🕐 Session: Just started")
        self.session_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        self.quick_stats_label = QLabel("📊 No data loaded")
        self.quick_stats_label.setFont(QFont("Segoe UI", 9))
        
        layout.addWidget(self.session_label)
        layout.addStretch()
        layout.addWidget(self.quick_stats_label)
        
        header.setLayout(layout)
        return header

    def _create_overview_tab(self) -> QWidget:
        """Create improved overview tab with optimal space usage"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Compact metrics section
        metrics_group = QGroupBox("📊 Key Metrics")
        metrics_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        metrics_group.setMaximumHeight(100)
        
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(6)
        
        # Compact metric cards - 2 rows, 3 columns
        self.metric_cards = {}
        cards_data = [
            ("Dimensions", "0", "📏", "#3498db"),
            ("Studies", "0", "🔬", "#9b59b6"),
            ("Success", "0%", "✅", "#27ae60"),
            ("Complete", "0%", "📊", "#f39c12"),
            ("GD&T", "0", "🔧", "#e67e22"),
            ("Changes", "0", "✏️", "#e74c3c"),
        ]

        for i, (title, value, icon, color) in enumerate(cards_data):
            card = CompactMetricCard(title, value, icon, color)
            card.setMaximumHeight(40)  # Make cards more compact
            key = title.lower()
            self.metric_cards[key] = card
            row, col = divmod(i, 3)
            metrics_layout.addWidget(card, row, col)

        metrics_group.setLayout(metrics_layout)
        main_layout.addWidget(metrics_group)

        # Visualization section with horizontal layout
        visual_group = QGroupBox("📈 Status & Quality Overview")
        visual_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        visual_group.setMinimumHeight(200)
        visual_group.setMaximumHeight(250)
        
        visual_layout = QHBoxLayout()
        visual_layout.setSpacing(12)
        
        # Status pie chart section
        status_frame = QFrame()
        status_frame.setMaximumWidth(180)
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(4, 4, 4, 4)
        
        status_title = QLabel("Status Distribution")
        status_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        status_title.setAlignment(Qt.AlignCenter)
        status_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        status_layout.addWidget(status_title)
        
        self.status_pie_chart = StatusPieChart({}, 100)  # Smaller pie chart
        status_layout.addWidget(self.status_pie_chart, alignment=Qt.AlignCenter)
        
        # Compact legend
        self.status_legend = QWidget()
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(2)
        legend_layout.setContentsMargins(4, 4, 4, 4)
        self.status_legend.setLayout(legend_layout)
        status_layout.addWidget(self.status_legend)
        
        status_frame.setLayout(status_layout)
        visual_layout.addWidget(status_frame)
        
        # Circular progress indicators
        progress_frame = QFrame()
        progress_frame.setMaximumWidth(200)
        progress_layout = QGridLayout()
        progress_layout.setSpacing(8)
        
        # Success rate
        success_title = QLabel("Success Rate")
        success_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        success_title.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(success_title, 0, 0)
        
        self.success_circle = CircularProgressWidget(0, 100, QColor("#27ae60"), "0%", 70)
        progress_layout.addWidget(self.success_circle, 1, 0, alignment=Qt.AlignCenter)
        
        # Completeness
        complete_title = QLabel("Data Complete")
        complete_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        complete_title.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(complete_title, 0, 1)
        
        self.completeness_circle = CircularProgressWidget(0, 100, QColor("#3498db"), "0%", 70)
        progress_layout.addWidget(self.completeness_circle, 1, 1, alignment=Qt.AlignCenter)
        
        progress_frame.setLayout(progress_layout)
        visual_layout.addWidget(progress_frame)
        
        # Breakdown information in vertical layout
        breakdown_frame = QFrame()
        breakdown_layout = QVBoxLayout()
        breakdown_layout.setSpacing(6)
        breakdown_layout.setContentsMargins(4, 4, 4, 4)
        
        # Cavity section
        cavity_title = QLabel("🏭 Cavity Analysis")
        cavity_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        cavity_title.setStyleSheet("color: #34495e; margin-bottom: 3px;")
        breakdown_layout.addWidget(cavity_title)
        
        cavity_scroll = QScrollArea()
        cavity_scroll.setMaximumHeight(60)
        cavity_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cavity_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        cavity_scroll.setWidgetResizable(True)
        
        cavity_widget = QWidget()
        self.cavity_layout = QVBoxLayout()
        self.cavity_layout.setSpacing(2)
        cavity_widget.setLayout(self.cavity_layout)
        cavity_scroll.setWidget(cavity_widget)
        breakdown_layout.addWidget(cavity_scroll)
        
        # Classification section
        class_title = QLabel("📋 Classification")
        class_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        class_title.setStyleSheet("color: #8e44ad; margin-bottom: 3px;")
        breakdown_layout.addWidget(class_title)
        
        class_scroll = QScrollArea()
        class_scroll.setMaximumHeight(60)
        class_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        class_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        class_scroll.setWidgetResizable(True)
        
        class_widget = QWidget()
        self.classification_layout = QVBoxLayout()
        self.classification_layout.setSpacing(2)
        class_widget.setLayout(self.classification_layout)
        class_scroll.setWidget(class_widget)
        breakdown_layout.addWidget(class_scroll)
        
        # Tolerance section
        tol_title = QLabel("📐 Tolerances")
        tol_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        tol_title.setStyleSheet("color: #16a085; margin-bottom: 3px;")
        breakdown_layout.addWidget(tol_title)
        
        tol_scroll = QScrollArea()
        tol_scroll.setMaximumHeight(60)
        tol_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tol_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tol_scroll.setWidgetResizable(True)
        
        tol_widget = QWidget()
        self.tolerance_layout = QVBoxLayout()
        self.tolerance_layout.setSpacing(2)
        tol_widget.setLayout(self.tolerance_layout)
        tol_scroll.setWidget(tol_widget)
        breakdown_layout.addWidget(tol_scroll)
        
        breakdown_frame.setLayout(breakdown_layout)
        visual_layout.addWidget(breakdown_frame)
        
        visual_group.setLayout(visual_layout)
        main_layout.addWidget(visual_group)
        
        # Add stretch to prevent expansion
        main_layout.addStretch()
        
        widget.setLayout(main_layout)
        return widget

    def _create_status_analysis_tab(self) -> QWidget:
        """Create detailed status analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Status overview with progress bars
        status_group = QGroupBox("📈 Detailed Status Breakdown")
        status_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        self.status_progress_layout = QVBoxLayout()
        self.status_progress_layout.setSpacing(6)
        status_group.setLayout(self.status_progress_layout)
        layout.addWidget(status_group)

        # Evaluation type status matrix
        matrix_group = QGroupBox("🔧 Status by Evaluation Type")
        matrix_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        
        self.status_matrix_table = QTableWidget()
        self.status_matrix_table.setColumnCount(7)
        self.status_matrix_table.setHorizontalHeaderLabels([
            "Evaluation Type", "Total", "Good", "Failed", "Warning", "T.E.D.", "To Check"
        ])
        self.status_matrix_table.horizontalHeader().setStretchLastSection(True)
        self.status_matrix_table.setAlternatingRowColors(True)
        self.status_matrix_table.setMaximumHeight(200)
        
        matrix_layout = QVBoxLayout()
        matrix_layout.addWidget(self.status_matrix_table)
        matrix_group.setLayout(matrix_layout)
        layout.addWidget(matrix_group)

        # Status recommendations
        rec_group = QGroupBox("💡 Status Analysis & Recommendations")
        rec_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        self.status_recommendations = QTextEdit()
        self.status_recommendations.setMaximumHeight(150)
        self.status_recommendations.setReadOnly(True)
        rec_layout = QVBoxLayout()
        rec_layout.addWidget(self.status_recommendations)
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_quality_tab(self) -> QWidget:
        """Create enhanced quality tab with better failed dimensions display"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Quality summary header
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #fff5f5, stop:1 #ffe6e6);
                border: 2px solid #fed7d7;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        summary_frame.setMaximumHeight(60)
        
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(8, 8, 8, 8)
        
        # Failed dimensions summary
        self.failed_summary_label = QLabel("❌ Analyzing failed dimensions...")
        self.failed_summary_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.failed_summary_label.setStyleSheet("color: #c53030;")
        summary_layout.addWidget(self.failed_summary_label)
        
        summary_layout.addStretch()
        
        # Refresh button
        self.refresh_quality_btn = QPushButton("🔄 Refresh Analysis")
        self.refresh_quality_btn.setMaximumHeight(30)
        self.refresh_quality_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_quality_btn.clicked.connect(self._refresh_quality_analysis)
        summary_layout.addWidget(self.refresh_quality_btn)
        
        summary_frame.setLayout(summary_layout)
        layout.addWidget(summary_frame)

        # Quality tabs for better organization
        quality_tabs = QTabWidget()
        quality_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #212529;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
        """)

        # Failed dimensions tab
        failed_tab = self._create_failed_dimensions_tab()
        quality_tabs.addTab(failed_tab, "❌ Failed")

        # Warning dimensions tab  
        warning_tab = self._create_warning_dimensions_tab()
        quality_tabs.addTab(warning_tab, "⚠️ Warnings")

        # Quality insights tab
        insights_tab = self._create_quality_insights_tab()
        quality_tabs.addTab(insights_tab, "💡 Insights")

        layout.addWidget(quality_tabs)
        widget.setLayout(layout)
        return widget
    
    def _create_failed_dimensions_tab(self) -> QWidget:
        """Create dedicated failed dimensions tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Failed dimensions table
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(8)
        self.failed_table.setHorizontalHeaderLabels([
            "Element ID", "Description", "Cavity", "Class", "Eval Type", 
            "Out of Spec", "Deviation", "Status"
        ])
        
        # Configure table appearance
        self.failed_table.setAlternatingRowColors(True)
        self.failed_table.setSortingEnabled(True)
        self.failed_table.horizontalHeader().setStretchLastSection(True)
        self.failed_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Set column widths for better visibility
        header = self.failed_table.horizontalHeader()
        header.resizeSection(0, 80)   # Element ID
        header.resizeSection(1, 150)  # Description
        header.resizeSection(2, 60)   # Cavity
        header.resizeSection(3, 50)   # Class
        header.resizeSection(4, 80)   # Eval Type
        header.resizeSection(5, 120)  # Out of Spec
        header.resizeSection(6, 80)   # Deviation
        header.resizeSection(7, 80)   # Status
        
        # Style the table
        self.failed_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #fff3cd;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.failed_table)
        widget.setLayout(layout)
        return widget

    def _create_warning_dimensions_tab(self) -> QWidget:
        """Create dedicated warning dimensions tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Warning dimensions table
        self.warning_table = QTableWidget()
        self.warning_table.setColumnCount(7)
        self.warning_table.setHorizontalHeaderLabels([
            "Element ID", "Description", "Cavity", "Class", "Issue Type", 
            "Details", "Recommendation"
        ])
        
        # Configure table
        self.warning_table.setAlternatingRowColors(True)
        self.warning_table.setSortingEnabled(True)
        self.warning_table.horizontalHeader().setStretchLastSection(True)
        self.warning_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Set column widths
        header = self.warning_table.horizontalHeader()
        header.resizeSection(0, 80)   # Element ID
        header.resizeSection(1, 120)  # Description  
        header.resizeSection(2, 60)   # Cavity
        header.resizeSection(3, 50)   # Class
        header.resizeSection(4, 100)  # Issue Type
        header.resizeSection(5, 120)  # Details
        
        # Style the table
        self.warning_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #fff3cd;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QHeaderView::section {
                background-color: #fff3cd;
                padding: 8px;
                border: 1px solid #ffeaa7;
                font-weight: bold;
                color: #856404;
            }
        """)
        
        layout.addWidget(self.warning_table)
        widget.setLayout(layout)
        return widget

    def _create_quality_insights_tab(self) -> QWidget:
        """Create quality insights tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Quality metrics overview
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        metrics_frame.setMaximumHeight(80)
        
        metrics_layout = QHBoxLayout()
        
        # Quality metric cards
        self.quality_metric_cards = {}
        quality_metrics = [
            ("Failure Rate", "0%", "❌", "#e74c3c"),
            ("Warning Rate", "0%", "⚠️", "#f39c12"),
            ("Critical Fails", "0", "🚨", "#c0392b"),
            ("Quality Score", "100", "🏆", "#27ae60")
        ]
        
        for title, value, icon, color in quality_metrics:
            card = CompactMetricCard(title, value, icon, color)
            card.setMaximumHeight(50)
            key = title.lower().replace(" ", "_")
            self.quality_metric_cards[key] = card
            metrics_layout.addWidget(card)
        
        metrics_frame.setLayout(metrics_layout)
        layout.addWidget(metrics_frame)

        # Quality insights text area
        insights_group = QGroupBox("💡 Quality Analysis & Recommendations")
        insights_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                border: 2px solid #3498db;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        insights_layout = QVBoxLayout()
        
        self.quality_insights_text = QTextEdit()
        self.quality_insights_text.setReadOnly(True)
        self.quality_insights_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-family: 'Segoe UI';
                font-size: 10px;
                line-height: 1.4;
            }
        """)
        
        insights_layout.addWidget(self.quality_insights_text)
        insights_group.setLayout(insights_layout)
        layout.addWidget(insights_group)
        
        widget.setLayout(layout)
        return widget

    def _create_capability_tab(self) -> QWidget:
        """Create process capability analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Capability overview
        capability_frame = QFrame()
        capability_layout = QHBoxLayout()
        capability_layout.setSpacing(15)

        # PP/PPK visualization
        pp_group = QGroupBox("📊 Process Performance (Pp)")
        pp_group.setStyleSheet("font-weight: bold; color: #2c3e50;")
        pp_layout = QVBoxLayout()
        
        self.pp_circle = CircularProgressWidget(0, 2.0, QColor("#3498db"), "0.000")
        pp_layout.addWidget(self.pp_circle, alignment=Qt.AlignCenter)
        
        pp_info = QLabel("Process Performance")
        pp_info.setAlignment(Qt.AlignCenter)
        pp_info.setFont(QFont("Segoe UI", 9))
        pp_layout.addWidget(pp_info)
        
        pp_group.setLayout(pp_layout)
        capability_layout.addWidget(pp_group)

        # PPK visualization
        ppk_group = QGroupBox("🎯 Process Performance Index (Ppk)")
        ppk_group.setStyleSheet("font-weight: bold; color: #2c3e50;")
        ppk_layout = QVBoxLayout()
        
        self.ppk_circle = CircularProgressWidget(0, 2.0, QColor("#27ae60"), "0.000")
        ppk_layout.addWidget(self.ppk_circle, alignment=Qt.AlignCenter)
        
        ppk_info = QLabel("Process Performance Index")
        ppk_info.setAlignment(Qt.AlignCenter)
        ppk_info.setFont(QFont("Segoe UI", 9))
        ppk_layout.addWidget(ppk_info)
        
        ppk_group.setLayout(ppk_layout)
        capability_layout.addWidget(ppk_group)

        # Capability interpretation
        interp_group = QGroupBox("📈 Capability Interpretation")
        interp_group.setStyleSheet("font-weight: bold; color: #2c3e50;")
        interp_layout = QVBoxLayout()
        
        self.capability_interpretation = QLabel("No capability data available")
        self.capability_interpretation.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.capability_interpretation.setAlignment(Qt.AlignCenter)
        self.capability_interpretation.setWordWrap(True)
        interp_layout.addWidget(self.capability_interpretation)
        
        interp_group.setLayout(interp_layout)
        capability_layout.addWidget(interp_group)

        capability_frame.setLayout(capability_layout)
        layout.addWidget(capability_frame)

        # Capability details table
        details_group = QGroupBox("📋 Capability Details (CC, SC, IC Dimensions)")
        details_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        
        self.capability_table = QTableWidget()
        self.capability_table.setColumnCount(6)
        self.capability_table.setHorizontalHeaderLabels([
            "Element ID", "Class", "Description", "Pp", "Ppk", "Capability Level"
        ])
        self.capability_table.horizontalHeader().setStretchLastSection(True)
        self.capability_table.setAlternatingRowColors(True)
        self.capability_table.setSortingEnabled(True)
        
        details_layout = QVBoxLayout()
        details_layout.addWidget(self.capability_table)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        widget.setLayout(layout)
        return widget

    def _create_evaluation_tab(self) -> QWidget:
        """Create evaluation types analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Evaluation type summary
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f0f8ff; border: 1px solid #bee3f8; border-radius: 6px; padding: 10px;")
        summary_layout = QGridLayout()
        
        self.eval_summary_cards = {}
        eval_types = [
            ("Normal", "📏", "#3498db"),
            ("GD&T", "🔧", "#e67e22"),
            ("Basic", "ℹ️", "#9b59b6"),
            ("Informative", "📋", "#1abc9c"),
            ("Note", "📝", "#f39c12")
        ]
        
        for i, (eval_type, icon, color) in enumerate(eval_types):
            card = CompactMetricCard(eval_type, "0", icon, color)
            self.eval_summary_cards[eval_type.lower()] = card
            row, col = divmod(i, 3)
            summary_layout.addWidget(card, row, col)
        
        summary_frame.setLayout(summary_layout)
        layout.addWidget(summary_frame)

        # Detailed evaluation breakdown table
        eval_group = QGroupBox("🔧 Detailed Evaluation Type Analysis")
        eval_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        
        self.eval_table = QTableWidget()
        self.eval_table.setColumnCount(8)
        self.eval_table.setHorizontalHeaderLabels([
            "Type", "Count", "Good", "Failed", "Warning", "T.E.D.", "To Check", "Success Rate"
        ])
        self.eval_table.horizontalHeader().setStretchLastSection(True)
        self.eval_table.setAlternatingRowColors(True)
        self.eval_table.setMaximumHeight(200)
        
        eval_layout = QVBoxLayout()
        eval_layout.addWidget(self.eval_table)
        eval_group.setLayout(eval_layout)
        layout.addWidget(eval_group)

        # Special analysis
        special_group = QGroupBox("🎯 Special Analysis & Insights")
        special_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        self.special_analysis_text = QTextEdit()
        self.special_analysis_text.setReadOnly(True)
        self.special_analysis_text.setMaximumHeight(200)
        special_layout = QVBoxLayout()
        special_layout.addWidget(self.special_analysis_text)
        special_group.setLayout(special_layout)
        layout.addWidget(special_group)

        widget.setLayout(layout)
        return widget

    def _create_comparison_tab(self) -> QWidget:
        """Create data comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Change summary
        change_frame = QFrame()
        change_frame.setStyleSheet("background-color: #fffaf0; border: 1px solid #fbd38d; border-radius: 6px; padding: 10px;")
        change_layout = QHBoxLayout()
        
        self.change_summary_cards = {}
        change_types = [
            ("Modified", "✏️", "#e67e22"),
            ("Added", "➕", "#27ae60"),
            ("Deleted", "🗑️", "#e74c3c")
        ]
        
        for change_type, icon, color in change_types:
            card = CompactMetricCard(f"{change_type} Dims", "0", icon, color)
            self.change_summary_cards[change_type.lower()] = card
            change_layout.addWidget(card)
        
        change_frame.setLayout(change_layout)
        layout.addWidget(change_frame)

        # Detailed modifications table
        mod_group = QGroupBox("📝 Detailed Modifications")
        mod_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        
        self.modifications_table = QTableWidget()
        self.modifications_table.setColumnCount(4)
        self.modifications_table.setHorizontalHeaderLabels([
            "Element ID", "Change Type", "Field Changed", "Change Details"
        ])
        self.modifications_table.horizontalHeader().setStretchLastSection(True)
        self.modifications_table.setAlternatingRowColors(True)
        
        mod_layout = QVBoxLayout()
        mod_layout.addWidget(self.modifications_table)
        mod_group.setLayout(mod_layout)
        layout.addWidget(mod_group)

        # Session comparison info
        session_group = QGroupBox("📊 Session Information")
        session_group.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        self.session_info_text = QTextEdit()
        self.session_info_text.setReadOnly(True)
        self.session_info_text.setMaximumHeight(150)
        session_layout = QVBoxLayout()
        session_layout.addWidget(self.session_info_text)
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        widget.setLayout(layout)
        return widget

    def ensure_visibility(self):
        """Ensure summary widget is visible and accessible"""
        try:
            if hasattr(self.parent_window, "results_tabs"):
                # Check if summary tab exists
                summary_tab_index = -1
                for i in range(self.parent_window.results_tabs.count()):
                    if "Summary" in self.parent_window.results_tabs.tabText(i):
                        summary_tab_index = i
                        break

                # If not found, add it as first tab
                if summary_tab_index == -1:
                    self.parent_window.results_tabs.insertTab(
                        0, self, "📊 Enhanced Summary"
                    )
                    self.parent_window.results_tabs.setCurrentIndex(0)
                    self._log_message("📊 Summary tab restored", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error ensuring summary visibility: {str(e)}", "ERROR")

    def _log_message(self, message: str, level: str = "INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        try:
            if hasattr(self.parent_window, '_log_message'):
                self.parent_window._log_message(formatted_message, level)
            elif level in ["ERROR", "WARNING"]:
                print(f"{level}: {formatted_message}")
        except Exception:
            pass  # Silent fail for logging

    def restore_summary_data(self, data: dict):
        """Restore summary data from saved session"""
        try:
            if not data:
                return
            
            # Restore original data if present
            if "original_data" in data:
                self.original_data = data["original_data"]
                self.session_loaded = True
            
            # Restore metrics
            if "metrics" in data:
                for key, value in data["metrics"].items():
                    if key == "session_start":
                        # Convert string to datetime if needed
                        if isinstance(value, str):
                            try:
                                self.metrics[key] = datetime.fromisoformat(value)
                            except Exception:
                                self.metrics[key] = datetime.now()
                        else:
                            self.metrics[key] = value
                    else:
                        if key in self.metrics:
                            self.metrics[key] = value
            
            # Update UI with restored data
            self._update_all_content()
            self._log_message("📊 Summary data restored from session", "INFO")
            
        except Exception as e:
            self._log_message(f"❌ Error restoring summary data: {str(e)}", "ERROR")

    def get_summary_data(self) -> dict:
        """Get current summary data for session saving"""
        try:
            return {
                "original_data": self.original_data,
                "metrics": self.metrics.copy(),
                "session_loaded": self.session_loaded
            }
        except Exception as e:
            self._log_message(f"❌ Error getting summary data: {str(e)}", "ERROR")
            return {}

    def store_original_data(self, table_data: pd.DataFrame):
        """Store original data when session is first loaded"""
        if table_data is None or table_data.empty:
            return

        try:
            self.original_data = {}
            for _, row in table_data.iterrows():
                element_id = row.get("element_id")
                if element_id:
                    self.original_data[element_id] = {
                        "measurements": {f"measurement_{i}": row.get(f"measurement_{i}") for i in range(1, 6)},
                        "nominal": row.get("nominal"),
                        "lower_tolerance": row.get("lower_tolerance"),
                        "upper_tolerance": row.get("upper_tolerance"),
                        "description": row.get("description"),
                        "cavity": row.get("cavity"),
                        "class": row.get("class"),
                        "evaluation_type": row.get("evaluation_type"),
                        "force_status": row.get("force_status"),
                    }
            
            self.session_loaded = True
            self._log_message(f"📋 Stored original data for {len(self.original_data)} dimensions")

        except Exception as e:
            self._log_message(f"❌ Error storing original data: {str(e)}", "ERROR")

    def update_summary(self, results: Optional[List[DimensionalResult]] = None, 
                      table_data: Optional[pd.DataFrame] = None, 
                      force_refresh: bool = False, store_original: bool = False):
        """Enhanced update with comprehensive analysis"""
        try:
            now = datetime.now()
            
            # Throttling check
            if not force_refresh and (now - self._last_update).total_seconds() < self._update_threshold:
                return
            self._last_update = now

            # Store original data if this is first load
            if store_original and table_data is not None and not self.session_loaded:
                self.store_original_data(table_data)

            # Update with current data
            if table_data is not None:
                self._analyze_table_data(table_data)
                self._track_data_changes(table_data)

            # Update with results and store for detailed analysis
            if results:
                self.results = results  # Store results for quality analysis
                self._analyze_results(results)

            # Update all UI components
            self._update_all_content()
            
            self.update_complete.emit()

        except Exception as e:
            self._log_message(f"❌ Error updating summary: {str(e)}", "ERROR")

    def _analyze_table_data(self, table_data: pd.DataFrame):
        """Comprehensive table data analysis"""
        if table_data.empty:
            return

        m = self.metrics
        
        # Basic counts
        m["total_dimensions"] = len(table_data)
        
        # Evaluation type breakdown
        eval_counts = table_data["evaluation_type"].value_counts()
        m["normal_dimensions"] = eval_counts.get("Normal", 0)
        m["gdt_dimensions"] = eval_counts.get("GD&T", 0)
        m["basic_dimensions"] = eval_counts.get("Basic", 0)
        m["informative_dimensions"] = eval_counts.get("Informative", 0)
        m["note_dimensions"] = eval_counts.get("Note", 0)
        
        # Classification breakdown
        class_counts = table_data["class"].value_counts()
        m["cc_dimensions"] = class_counts.get("CC", 0)
        m["sc_dimensions"] = class_counts.get("SC", 0)
        m["ic_dimensions"] = class_counts.get("IC", 0)
        
        # Tolerance analysis
        m["unilateral_tolerances"] = 0
        m["bilateral_tolerances"] = 0
        m["zero_nominal_gdt"] = 0
        
        for _, row in table_data.iterrows():
            lower_tol = row.get("lower_tolerance")
            upper_tol = row.get("upper_tolerance")
            nominal = row.get("nominal", 0)
            eval_type = row.get("evaluation_type", "Normal")
            
            # Convert to numeric, handle NaN
            try:
                lower_tol = float(lower_tol) if pd.notna(lower_tol) and str(lower_tol).strip() != "" else None
                upper_tol = float(upper_tol) if pd.notna(upper_tol) and str(upper_tol).strip() != "" else None
                nominal = float(nominal) if pd.notna(nominal) and str(nominal).strip() != "" else 0.0
            except (ValueError, TypeError):
                lower_tol = None
                upper_tol = None
                nominal = 0.0
            
            # Count tolerance types
            if lower_tol is not None and upper_tol is not None and lower_tol != upper_tol:
                m["bilateral_tolerances"] += 1
            elif (lower_tol is not None and upper_tol is None) or (lower_tol is None and upper_tol is not None):
                m["unilateral_tolerances"] += 1
            elif lower_tol is not None and upper_tol is not None and lower_tol == upper_tol:
                m["unilateral_tolerances"] += 1
            
            # Count zero nominal GD&T
            if abs(nominal) < 0.0001 and eval_type == "GD&T":
                m["zero_nominal_gdt"] += 1
        
        # Calculate completeness
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        total_measurements = 0
        dimensions_with_measurements = 0
        
        for _, row in table_data.iterrows():
            row_measurements = 0
            for col in measurement_cols:
                val = row.get(col)
                if pd.notna(val) and str(val).strip() != "":
                    row_measurements += 1
                    total_measurements += 1
            
            if row_measurements > 0:
                dimensions_with_measurements += 1
        
        m["total_measurements"] = total_measurements
        m["dimensions_with_measurements"] = dimensions_with_measurements
        m["completeness"] = (total_measurements / (len(table_data) * 5) * 100) if len(table_data) > 0 else 0
        
        # Cavity breakdown
        cavity_counts = table_data["cavity"].value_counts().to_dict()
        m["cavity_breakdown"] = {str(k): v for k, v in cavity_counts.items()}

    def _analyze_results(self, results: List[DimensionalResult]):
        """Analyze dimensional results for status and capability"""
        if not results:
            return

        m = self.metrics
        m["studies_run"] += 1
        
        # Status counts with evaluation type tracking
        status_counts = {"GOOD": 0, "BAD": 0, "WARNING": 0, "TED": 0, "TO_CHECK": 0}
        eval_type_status = {}
        pp_values = []
        ppk_values = []
        
        for result in results:
            # Get evaluation type
            eval_type = getattr(result, 'evaluation_type', 'Normal')
            if eval_type not in eval_type_status:
                eval_type_status[eval_type] = {"GOOD": 0, "BAD": 0, "WARNING": 0, "TED": 0, "TO_CHECK": 0, "TOTAL": 0}
            
            # Count status
            status = result.status.value if hasattr(result.status, "value") else str(result.status)
            
            # Map status correctly
            if status in ["GOOD", "PASS"]:
                status_counts["GOOD"] += 1
                eval_type_status[eval_type]["GOOD"] += 1
            elif status in ["BAD", "FAIL", "OUT_OF_SPEC"]:
                status_counts["BAD"] += 1
                eval_type_status[eval_type]["BAD"] += 1
            elif status in ["WARNING", "WARN"]:
                status_counts["WARNING"] += 1
                eval_type_status[eval_type]["WARNING"] += 1
            elif status in ["TED", "T.E.D.", "BASIC", "INFORMATIVE"]:
                status_counts["TED"] += 1
                eval_type_status[eval_type]["TED"] += 1
            elif status in ["TO_CHECK", "NOTE"]:
                status_counts["TO_CHECK"] += 1
                eval_type_status[eval_type]["TO_CHECK"] += 1
            
            eval_type_status[eval_type]["TOTAL"] += 1
            
            # Collect capability data for CC, SC, IC dimensions only
            if (hasattr(result, "classe") and result.classe and 
                result.classe.upper() in ["CC", "SC", "IC"]):
                if hasattr(result, "pp") and result.pp is not None:
                    pp_values.append(result.pp)
                if hasattr(result, "ppk") and result.ppk is not None:
                    ppk_values.append(result.ppk)
        
        # Store evaluation type status breakdown
        m["eval_type_status"] = eval_type_status
        
        # Update metrics
        m["passed"] = status_counts["GOOD"]
        m["failed"] = status_counts["BAD"]
        m["warning"] = status_counts["WARNING"]
        m["ted"] = status_counts["TED"]
        m["to_check"] = status_counts["TO_CHECK"]
        
        total_evaluable = m["passed"] + m["failed"] + m["warning"]
        m["success_rate"] = (m["passed"] / total_evaluable * 100) if total_evaluable > 0 else 0
        
        # Process capability averages
        m["avg_pp"] = sum(pp_values) / len(pp_values) if pp_values else 0.0
        m["avg_ppk"] = sum(ppk_values) / len(ppk_values) if ppk_values else 0.0
        m["capability_count"] = len(pp_values)

    def _track_data_changes(self, current_data: pd.DataFrame):
        """Track changes from original data"""
        if not self.original_data or current_data.empty:
            return

        try:
            modifications = []
            current_ids = set(current_data["element_id"].dropna().unique())
            original_ids = set(self.original_data.keys())
            
            # Find additions and deletions
            added_ids = current_ids - original_ids
            deleted_ids = original_ids - current_ids
            
            self.metrics["dimensions_added"] = len(added_ids)
            self.metrics["dimensions_deleted"] = len(deleted_ids)
            
            # Find modifications
            for _, row in current_data.iterrows():
                element_id = row.get("element_id")
                if element_id in self.original_data:
                    original = self.original_data[element_id]
                    changes = []
                    
                    # Check measurements
                    for i in range(1, 6):
                        orig_val = original["measurements"].get(f"measurement_{i}")
                        curr_val = row.get(f"measurement_{i}")
                        
                        if pd.isna(orig_val) and pd.isna(curr_val):
                            continue
                        
                        if pd.notna(orig_val) and pd.notna(curr_val):
                            if abs(float(orig_val) - float(curr_val)) > 0.001:
                                changes.append(f"M{i}: {orig_val:.3f} → {curr_val:.3f}")
                        elif pd.isna(orig_val) and pd.notna(curr_val):
                            changes.append(f"M{i}: empty → {curr_val:.3f}")
                        elif pd.notna(orig_val) and pd.isna(curr_val):
                            changes.append(f"M{i}: {orig_val:.3f} → empty")
                    
                    # Check other fields
                    for field in ["nominal", "lower_tolerance", "upper_tolerance", "force_status"]:
                        orig_val = original.get(field)
                        curr_val = row.get(field)
                        
                        if pd.isna(orig_val) and pd.isna(curr_val):
                            continue
                        
                        if orig_val != curr_val:
                            changes.append(f"{field}: {orig_val} → {curr_val}")
                    
                    if changes:
                        modifications.append({
                            "element_id": element_id,
                            "changes": changes[:5],
                            "change_count": len(changes)
                        })
            
            self.metrics["dimensions_modified"] = len(modifications)
            self.metrics["modification_details"] = modifications[:20]
            
        except Exception as e:
            self._log_message(f"❌ Error tracking changes: {str(e)}", "ERROR")

    def _update_all_content(self):
        """Enhanced update method with better error handling and performance"""
        try:  
            self._update_session_header()           # Update session header
            self._update_overview_tab()             # Update overview tab with improved layout
            self._update_status_analysis_tab()      # Update status analysis
            self._update_quality_tab()              # Update quality tab with enhanced failed dimensions display
            self._update_capability_tab()           # Update capability tab
            self._update_evaluation_tab()           # Update evaluation tab
            self._update_comparison_tab()           # Update comparison tab
            self.ensure_visibility()                # Ensure summary is visible
            
        except Exception as e:
            self._log_message(f"❌ Error updating summary content: {str(e)}", "ERROR")


    def _update_session_header(self):
        """Update session header"""
        m = self.metrics
        
        # Ensure session_start is a datetime object
        session_start = m.get("session_start", datetime.now())
        if isinstance(session_start, str):
            try:
                session_start = datetime.fromisoformat(session_start)
                m["session_start"] = session_start
            except Exception:
                session_start = datetime.now()
                m["session_start"] = session_start

        # Calculate session duration
        duration = datetime.now() - session_start
        duration_str = str(duration).split('.')[0]
        
        # Update session label
        self.session_label.setText(f"🕐 Session: {duration_str}")
        
        # Update quick stats
        if m["total_dimensions"] > 0:
            stats_text = (f"📊 {m['total_dimensions']} dims | "
                         f"✅ {m['success_rate']:.1f}% success | "
                         f"🔧 {m['gdt_dimensions']} GD&T | "
                         f"✏️ {m['dimensions_modified']} modified")
        else:
            stats_text = "📊 No data loaded"
        
        self.quick_stats_label.setText(stats_text)

    def _update_overview_tab(self):
        """Enhanced overview tab update with better space utilization"""
        m = self.metrics
        
        # Update compact metric cards with appropriate data
        metric_updates = {
            "dimensions": str(m["total_dimensions"]),
            "studies": str(m["studies_run"]),
            "success": f"{m['success_rate']:.1f}%",
            "complete": f"{m['completeness']:.1f}%",
            "gd&t": str(m["gdt_dimensions"]),
            "changes": str(m["dimensions_modified"] + m["dimensions_added"] + m["dimensions_deleted"])
        }
        
        # Update metric cards safely
        for key, value in metric_updates.items():
            if key in self.metric_cards:
                try:
                    self.metric_cards[key].update_value(value)
                except Exception as e:
                    self._log_message(f"Error updating metric card {key}: {str(e)}", "WARNING")
        
        # Update status pie chart with proper data
        status_data = {
            "GOOD": m["passed"],
            "BAD": m["failed"], 
            "WARNING": m["warning"],
            "TED": m["ted"],
            "TO_CHECK": m["to_check"]
        }
        
        try:
            self.status_pie_chart.update_data(status_data)
            self._update_status_legend(status_data)
        except Exception as e:
            self._log_message(f"Error updating status visualization: {str(e)}", "WARNING")
        
        # Update circular progress indicators
        try:
            self.completeness_circle.update_value(m["completeness"], f"{m['completeness']:.1f}%")
            self.success_circle.update_value(m["success_rate"], f"{m['success_rate']:.1f}%")
        except Exception as e:
            self._log_message(f"Error updating progress circles: {str(e)}", "WARNING")
        
        # Update breakdown sections
        try:
            self._update_cavity_breakdown()
            self._update_classification_breakdown()
            self._update_tolerance_analysis()
        except Exception as e:
            self._log_message(f"Error updating breakdown sections: {str(e)}", "WARNING")


    def _update_cavity_breakdown(self):
        """Update cavity breakdown section with optimized layout"""
        # Clear existing widgets
        self._clear_layout(self.cavity_layout)
        
        m = self.metrics
        cavity_data = m.get("cavity_breakdown", {})
        
        if not cavity_data:
            no_data_label = QLabel("No cavity data")
            no_data_label.setFont(QFont("Segoe UI", 9))
            no_data_label.setStyleSheet("color: #6c757d;")
            self.cavity_layout.addWidget(no_data_label)
            return
        
        # Create compact cavity display
        for cavity, count in sorted(cavity_data.items()):
            cavity_frame = QFrame()
            cavity_frame.setMaximumHeight(25)
            cavity_layout = QHBoxLayout()
            cavity_layout.setContentsMargins(4, 2, 4, 2)
            cavity_layout.setSpacing(6)
            
            # Cavity indicator
            indicator = QLabel("🏭")
            indicator.setFont(QFont("Segoe UI", 10))
            
            # Cavity info
            info_label = QLabel(f"Cavity {cavity}: {count}")
            info_label.setFont(QFont("Segoe UI", 9))
            info_label.setStyleSheet("color: #34495e; font-weight: bold;")
            
            cavity_layout.addWidget(indicator)
            cavity_layout.addWidget(info_label)
            cavity_layout.addStretch()
            
            cavity_frame.setLayout(cavity_layout)
            self.cavity_layout.addWidget(cavity_frame)
        
        # Add spacer to prevent stretching
        self.cavity_layout.addStretch()

    def _update_classification_breakdown(self):
        """Update classification breakdown with better visualization"""
        self._clear_layout(self.classification_layout)
        
        m = self.metrics
        
        # Classification data with color coding
        class_data = [
            ("CC", m["cc_dimensions"], "#e74c3c", "Critical"),
            ("SC", m["sc_dimensions"], "#f39c12", "Significant"), 
            ("IC", m["ic_dimensions"], "#27ae60", "Important")
        ]
        
        total_classified = sum(data[1] for data in class_data)
        
        if total_classified == 0:
            no_data_label = QLabel("No classified dimensions")
            no_data_label.setFont(QFont("Segoe UI", 9))
            no_data_label.setStyleSheet("color: #6c757d;")
            self.classification_layout.addWidget(no_data_label)
            return
        
        for class_type, count, color, description in class_data:
            if count > 0:
                class_frame = QFrame()
                class_frame.setMaximumHeight(25)
                class_layout = QHBoxLayout()
                class_layout.setContentsMargins(4, 2, 4, 2)
                class_layout.setSpacing(6)
                
                # Color indicator
                indicator = QLabel("●")
                indicator.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
                
                # Class info
                percentage = (count / total_classified * 100) if total_classified > 0 else 0
                info_label = QLabel(f"{class_type}: {count} ({percentage:.1f}%)")
                info_label.setFont(QFont("Segoe UI", 9))
                info_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                info_label.setToolTip(f"{description} Characteristics")
                
                class_layout.addWidget(indicator)
                class_layout.addWidget(info_label)
                class_layout.addStretch()
                
                class_frame.setLayout(class_layout)
                self.classification_layout.addWidget(class_frame)
        
        self.classification_layout.addStretch()

    def _update_tolerance_analysis(self):
        """Update tolerance analysis section"""
        self._clear_layout(self.tolerance_layout)
        
        m = self.metrics
        
        tolerance_data = [
            ("Bilateral", m["bilateral_tolerances"], "📏", "#3498db"),
            ("Unilateral", m["unilateral_tolerances"], "📐", "#9b59b6"),
            ("Zero Nominal GD&T", m["zero_nominal_gdt"], "🔧", "#e67e22")
        ]
        
        total_dims = m["total_dimensions"]
        
        if total_dims == 0:
            no_data_label = QLabel("No tolerance data")
            no_data_label.setFont(QFont("Segoe UI", 9))
            no_data_label.setStyleSheet("color: #6c757d;")
            self.tolerance_layout.addWidget(no_data_label)
            return
        
        for tol_type, count, icon, color in tolerance_data:
            if count > 0:
                tol_frame = QFrame()
                tol_frame.setMaximumHeight(25)
                tol_layout = QHBoxLayout()
                tol_layout.setContentsMargins(4, 2, 4, 2)
                tol_layout.setSpacing(6)
                
                # Icon
                icon_label = QLabel(icon)
                icon_label.setFont(QFont("Segoe UI", 10))
                
                # Tolerance info
                percentage = (count / total_dims * 100) if total_dims > 0 else 0
                info_label = QLabel(f"{tol_type}: {count} ({percentage:.1f}%)")
                info_label.setFont(QFont("Segoe UI", 9))
                info_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                
                tol_layout.addWidget(icon_label)
                tol_layout.addWidget(info_label)
                tol_layout.addStretch()
                
                tol_frame.setLayout(tol_layout)
                self.tolerance_layout.addWidget(tol_frame)
        
        self.tolerance_layout.addStretch()

    def _clear_layout(self, layout):
        """Utility function to clear a layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self._clear_layout(item.layout())


    def _update_status_legend(self, status_data: dict):
        """Update status legend"""
        # Clear existing legend
        layout = self.status_legend.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add legend items
        colors = {
            "GOOD": "#27ae60",
            "BAD": "#e74c3c",
            "WARNING": "#f39c12",
            "TED": "#3498db",
            "TO_CHECK": "#f39c12"
        }
        
        labels = {
            "GOOD": "✅ Good",
            "BAD": "❌ Failed",
            "WARNING": "⚠️ Warning",
            "TED": "ℹ️ T.E.D.",
            "TO_CHECK": "🔍 To Check"
        }
        
        for status, count in status_data.items():
            if count > 0:
                item_frame = QFrame()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(4, 2, 4, 2)
                
                # Color indicator
                color_label = QLabel("●")
                color_label.setStyleSheet(f"color: {colors[status]}; font-size: 12px; font-weight: bold;")
                
                # Label and count
                text_label = QLabel(f"{labels[status]}: {count}")
                text_label.setFont(QFont("Segoe UI", 8))
                
                item_layout.addWidget(color_label)
                item_layout.addWidget(text_label)
                item_layout.addStretch()
                item_frame.setLayout(item_layout)
                
                layout.addWidget(item_frame)

    def _update_status_analysis_tab(self):
        """Update detailed status analysis tab"""
        m = self.metrics
        
        # Update status progress bars
        self._clear_layout(self.status_progress_layout)
        
        total = m["passed"] + m["failed"] + m["warning"] + m["ted"] + m["to_check"]
        
        if total > 0:
            status_data = [
                ("Good Dimensions", m["passed"], "#27ae60", "✅"),
                ("Failed Dimensions", m["failed"], "#e74c3c", "❌"),
                ("Warning Dimensions", m["warning"], "#f39c12", "⚠️"),
                ("T.E.D. Dimensions", m["ted"], "#3498db", "ℹ️"),
                ("To Check Dimensions", m["to_check"], "#f39c12", "🔍")
            ]
            
            for name, count, color, icon in status_data:
                if count > 0:
                    percentage = int((count / total) * 100)
                    
                    progress_frame = QFrame()
                    progress_layout = QHBoxLayout()
                    progress_layout.setContentsMargins(8, 4, 8, 4)
                    
                    # Icon and label
                    label = QLabel(f"{icon} {name}")
                    label.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    label.setMinimumWidth(150)
                    
                    # Progress bar
                    progress = QProgressBar()
                    progress.setMaximum(100)
                    progress.setValue(percentage)
                    progress.setMaximumHeight(20)
                    progress.setStyleSheet(f"""
                        QProgressBar::chunk {{
                            background-color: {color};
                            border-radius: 2px;
                        }}
                        QProgressBar {{
                            border: 1px solid #ddd;
                            border-radius: 2px;
                            text-align: center;
                            font-size: 9px;
                            font-weight: bold;
                        }}
                    """)
                    progress.setFormat(f"{count} ({percentage}%)")
                    
                    progress_layout.addWidget(label)
                    progress_layout.addWidget(progress, 1)
                    progress_frame.setLayout(progress_layout)
                    self.status_progress_layout.addWidget(progress_frame)
        
        # Update status matrix table
        self._update_status_matrix_table()
        
        # Update status recommendations
        self._update_status_recommendations()

    def _update_status_matrix_table(self):
        """Update status by evaluation type matrix"""
        m = self.metrics
        eval_type_status = m.get("eval_type_status", {})
        
        # Clear and set up table
        self.status_matrix_table.setRowCount(0)
        
        if not eval_type_status:
            return
        
        # Add rows for each evaluation type
        row = 0
        for eval_type, status_data in eval_type_status.items():
            if status_data.get("TOTAL", 0) > 0:
                self.status_matrix_table.insertRow(row)
                
                # Evaluation type
                self.status_matrix_table.setItem(row, 0, QTableWidgetItem(eval_type))
                
                # Counts
                self.status_matrix_table.setItem(row, 1, QTableWidgetItem(str(status_data["TOTAL"])))
                self.status_matrix_table.setItem(row, 2, QTableWidgetItem(str(status_data["GOOD"])))
                self.status_matrix_table.setItem(row, 3, QTableWidgetItem(str(status_data["BAD"])))
                self.status_matrix_table.setItem(row, 4, QTableWidgetItem(str(status_data["WARNING"])))
                self.status_matrix_table.setItem(row, 5, QTableWidgetItem(str(status_data["TED"])))
                self.status_matrix_table.setItem(row, 6, QTableWidgetItem(str(status_data["TO_CHECK"])))
                
                # Color code cells based on status
                for col in range(7):
                    item = self.status_matrix_table.item(row, col)
                    if item:
                        if col == 2 and status_data["GOOD"] > 0:  # Good column
                            item.setBackground(QColor(230, 255, 230))
                        elif col == 3 and status_data["BAD"] > 0:  # Failed column
                            item.setBackground(QColor(255, 230, 230))
                        elif col == 4 and status_data["WARNING"] > 0:  # Warning column
                            item.setBackground(QColor(255, 245, 230))
                        elif col == 5 and status_data["TED"] > 0:  # TED column
                            item.setBackground(QColor(230, 245, 255))
                        elif col == 6 and status_data["TO_CHECK"] > 0:  # To Check column
                            item.setBackground(QColor(255, 250, 230))
                
                row += 1

    def _update_status_recommendations(self):
        """Update status analysis recommendations"""
        m = self.metrics
        recommendations = []
        
        # Generate intelligent recommendations based on status analysis
        if m["success_rate"] < 95 and m["success_rate"] >= 80:
            recommendations.append("⚠️ SUCCESS RATE ATTENTION: Current success rate is below target (95%). Review failed dimensions for systematic issues.")
        elif m["success_rate"] < 80:
            recommendations.append("🚨 CRITICAL SUCCESS RATE: Success rate is critically low (<80%). Immediate process review and corrective actions required.")
        elif m["success_rate"] >= 95:
            recommendations.append("✅ EXCELLENT SUCCESS RATE: Process is performing well with >95% success rate.")
        
        if m["failed"] > 0:
            recommendations.append(f"❌ FAILED DIMENSIONS: {m['failed']} dimensions are out of tolerance. Check Quality Issues tab for details.")
        
        if m["warning"] > 0:
            recommendations.append(f"⚠️ WARNING DIMENSIONS: {m['warning']} dimensions show warning status. Review for potential process drift.")
        
        if m["to_check"] > 0:
            recommendations.append(f"🔍 MANUAL REVIEW REQUIRED: {m['to_check']} dimensions require manual verification (Notes).")
        
        if m["completeness"] < 90:
            recommendations.append(f"📊 DATA COMPLETENESS: Only {m['completeness']:.1f}% of measurements are complete. Consider increasing sample sizes.")
        
        # Evaluation type specific recommendations
        eval_type_status = m.get("eval_type_status", {})
        for eval_type, status_data in eval_type_status.items():
            if eval_type in ["Normal", "GD&T"] and status_data.get("BAD", 0) > 0:
                total_evaluable = status_data.get("GOOD", 0) + status_data.get("BAD", 0) + status_data.get("WARNING", 0)
                if total_evaluable > 0:
                    failure_rate = (status_data["BAD"] / total_evaluable) * 100
                    if failure_rate > 20:
                        recommendations.append(f"🔧 {eval_type.upper()} ISSUES: High failure rate ({failure_rate:.1f}%) in {eval_type} dimensions.")
        
        if not recommendations:
            recommendations.append("✅ All status metrics look good! Continue monitoring process performance.")
        
        # Update recommendations text
        rec_text = "\n\n".join(recommendations)
        self.status_recommendations.setPlainText(rec_text)

    def _update_quality_tab(self):
        """Update quality issues tab with proper failed dimensions display"""
        self._update_failed_dimensions_summary()
        self._update_failed_dimensions_table()
        self._update_warning_dimensions_table()
        self._update_quality_insights_tab()  # Add this line

    def _update_failed_dimensions_summary(self):
        """Update failed dimensions summary"""
        m = self.metrics
        failed_count = m["failed"]
        total_evaluable = m["passed"] + m["failed"] + m["warning"]
        
        if failed_count == 0:
            self.failed_summary_label.setText("✅ No failed dimensions - All measurements within tolerance!")
            self.failed_summary_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            failure_rate = (failed_count / total_evaluable * 100) if total_evaluable > 0 else 0
            self.failed_summary_label.setText(f"❌ {failed_count} failed dimensions ({failure_rate:.1f}% failure rate)")
            self.failed_summary_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def _update_failed_dimensions_table(self):
        """Enhanced failed dimensions table update with proper data display"""
        self.failed_table.setRowCount(0)
        
        if not self.results:
            # Show message when no analysis has been run
            self.failed_table.setRowCount(1)
            items = [
                QTableWidgetItem("No Analysis"),
                QTableWidgetItem("Run dimensional study first"),
                QTableWidgetItem(""),
                QTableWidgetItem(""),
                QTableWidgetItem(""),
                QTableWidgetItem(""),
                QTableWidgetItem(""),
                QTableWidgetItem("Pending")
            ]
            
            for col, item in enumerate(items):
                item.setBackground(QColor(240, 248, 255))
                item.setForeground(QColor(52, 152, 219))
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item.setTextAlignment(Qt.AlignCenter)
                self.failed_table.setItem(0, col, item)
            return
        
        # Get actual failed dimensions
        failed_results = []
        for result in self.results:
            status = result.status.value if hasattr(result.status, "value") else str(result.status)
            if status in ["BAD", "FAIL", "OUT_OF_SPEC"]:
                failed_results.append(result)
        
        if not failed_results:
            # Show success message when no failed dimensions
            self.failed_table.setRowCount(1)
            items = [
                QTableWidgetItem("✅ SUCCESS"),
                QTableWidgetItem("No failed dimensions found"),
                QTableWidgetItem("All"),
                QTableWidgetItem("All"),
                QTableWidgetItem("All Types"),
                QTableWidgetItem("All measurements within tolerance"),
                QTableWidgetItem("Within Spec"),
                QTableWidgetItem("✅ PASS")
            ]
            
            for col, item in enumerate(items):
                item.setBackground(QColor(230, 255, 230))
                item.setForeground(QColor(27, 174, 96))
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item.setTextAlignment(Qt.AlignCenter)
                self.failed_table.setItem(0, col, item)
            return
        
        # Display actual failed dimensions
        self.failed_table.setRowCount(len(failed_results))
        
        for row, result in enumerate(failed_results):
            try:
                # Element ID
                element_item = QTableWidgetItem(str(result.element_id))
                element_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.failed_table.setItem(row, 0, element_item)
                
                # Description (truncated for display)
                description = str(result.description)
                if len(description) > 25:
                    description = description[:22] + "..."
                desc_item = QTableWidgetItem(description)
                desc_item.setToolTip(str(result.description))  # Full description in tooltip
                self.failed_table.setItem(row, 1, desc_item)
                
                # Cavity
                cavity = getattr(result, 'cavity', 'N/A')
                cavity_item = QTableWidgetItem(str(cavity))
                cavity_item.setTextAlignment(Qt.AlignCenter)
                self.failed_table.setItem(row, 2, cavity_item)
                
                # Class with color coding
                classe = getattr(result, 'classe', 'N/A')
                class_item = QTableWidgetItem(str(classe))
                class_item.setTextAlignment(Qt.AlignCenter)
                class_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                # Color code by class criticality
                if classe == "CC":
                    class_item.setBackground(QColor(255, 235, 235))
                    class_item.setForeground(QColor(220, 53, 69))
                elif classe == "SC":
                    class_item.setBackground(QColor(255, 243, 205))
                    class_item.setForeground(QColor(255, 193, 7))
                elif classe == "IC":
                    class_item.setBackground(QColor(212, 237, 218))
                    class_item.setForeground(QColor(25, 135, 84))
                
                self.failed_table.setItem(row, 3, class_item)
                
                # Evaluation Type
                eval_type = getattr(result, 'evaluation_type', 'Normal')
                eval_item = QTableWidgetItem(eval_type)
                eval_item.setTextAlignment(Qt.AlignCenter)
                self.failed_table.setItem(row, 4, eval_item)
                
                # Out of spec measurements with details
                out_of_spec_details = self._get_out_of_spec_details(result)
                spec_item = QTableWidgetItem(out_of_spec_details)
                spec_item.setFont(QFont("Segoe UI", 8))
                self.failed_table.setItem(row, 5, spec_item)
                
                # Deviation information
                deviation_info = self._get_deviation_info(result)
                dev_item = QTableWidgetItem(deviation_info)
                dev_item.setTextAlignment(Qt.AlignCenter)
                dev_item.setFont(QFont("Segoe UI", 9))
                self.failed_table.setItem(row, 6, dev_item)
                
                # Status with strong visual indication
                status_item = QTableWidgetItem("❌ FAILED")
                status_item.setBackground(QColor(248, 215, 218))
                status_item.setForeground(QColor(220, 53, 69))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setToolTip("Dimension is out of tolerance")
                self.failed_table.setItem(row, 7, status_item)
                
                # Highlight entire row for failed dimension
                for col in range(8):
                    item = self.failed_table.item(row, col)
                    if item and col != 3:  # Don't override class color coding
                        current_bg = item.background()
                        if current_bg == QColor():  # No background set
                            item.setBackground(QColor(253, 242, 242))
                            
            except Exception as e:
                self._log_message(f"Error displaying failed dimension {result.element_id}: {str(e)}", "ERROR")
                continue

    def _get_deviation_info(self, result: 'DimensionalResult') -> str:
        """Get deviation information for failed dimension"""
        try:
            if not hasattr(result, 'deviation') or not result.deviation:
                return "N/A"
            
            # Find maximum absolute deviation
            deviations = [d for d in result.deviation if d is not None]
            if not deviations:
                return "N/A"
            
            max_positive = max([d for d in deviations if d > 0], default=0)
            max_negative = min([d for d in deviations if d < 0], default=0)
            
            if max_positive > 0 and max_negative < 0:
                return f"+{max_positive:.3f}/{max_negative:.3f}"
            elif max_positive > 0:
                return f"+{max_positive:.3f}"
            elif max_negative < 0:
                return f"{max_negative:.3f}"
            else:
                return "±0.000"
                
        except Exception:
            return "N/A"

    def _get_out_of_spec_details(self, result: 'DimensionalResult') -> str:
        """Get detailed out of spec measurements info"""
        if not result.measurements or not hasattr(result, 'nominal'):
            return "No measurements"
        
        try:
            out_of_spec_measurements = []
            
            # Calculate limits
            nominal = float(result.nominal)
            lower_tol = result.lower_tolerance
            upper_tol = result.upper_tolerance
            
            if lower_tol is None and upper_tol is None:
                return "No tolerances defined"
            
            # Handle different tolerance scenarios
            for i, meas in enumerate(result.measurements):
                if meas is None:
                    continue
                    
                meas_float = float(meas)
                is_out_of_spec = False
                
                # Zero nominal GD&T case
                if abs(nominal) < 0.0001 and lower_tol == 0.0 and upper_tol and upper_tol > 0.0:
                    is_out_of_spec = meas_float < 0 or meas_float > upper_tol
                # Zero nominal bilateral case
                elif abs(nominal) < 0.0001 and lower_tol and lower_tol < 0.0 and upper_tol and upper_tol > 0.0:
                    max_tolerance = max(abs(lower_tol), abs(upper_tol))
                    is_out_of_spec = abs(meas_float) > max_tolerance
                # Standard case
                else:
                    lower_limit = nominal + (lower_tol or 0)
                    upper_limit = nominal + (upper_tol or 0)
                    is_out_of_spec = not (lower_limit <= meas_float <= upper_limit)
                
                if is_out_of_spec:
                    out_of_spec_measurements.append(f"M{i+1}:{meas_float:.3f}")
            
            if not out_of_spec_measurements:
                return "All within spec"
            
            # Return first 3 measurements that are out of spec
            result_text = "; ".join(out_of_spec_measurements[:3])
            if len(out_of_spec_measurements) > 3:
                result_text += f" (+{len(out_of_spec_measurements)-3})"
            
            return result_text
            
        except Exception as e:
            return f"Error: {str(e)}"
        
    def _update_quality_insights_tab(self):
        """Update quality insights with enhanced metrics"""
        m = self.metrics
        
        # Update quality metric cards
        total_evaluable = m["passed"] + m["failed"] + m["warning"]
        
        if total_evaluable > 0:
            failure_rate = (m["failed"] / total_evaluable) * 100
            warning_rate = (m["warning"] / total_evaluable) * 100
            
            # Update metric cards
            self.quality_metric_cards["failure_rate"].update_value(f"{failure_rate:.1f}%")
            self.quality_metric_cards["warning_rate"].update_value(f"{warning_rate:.1f}%")
            self.quality_metric_cards["critical_fails"].update_value(str(m["failed"]))
            
            # Calculate quality score (100 - failure_rate)
            quality_score = max(0, 100 - failure_rate)
            self.quality_metric_cards["quality_score"].update_value(f"{quality_score:.0f}")
        else:
            # No evaluable data yet
            for card in self.quality_metric_cards.values():
                card.update_value("TBD")
        
        # Update quality insights text
        self._generate_quality_insights()

    def _generate_quality_insights(self):
        """Generate intelligent quality insights based on analysis"""
        m = self.metrics
        insights = []
        
        insights.append("🔍 QUALITY ANALYSIS INSIGHTS")
        insights.append("=" * 50)
        
        total_evaluable = m["passed"] + m["failed"] + m["warning"]
        
        if total_evaluable == 0:
            insights.append("⏳ No dimensional studies completed yet.")
            insights.append("Run a dimensional study to generate quality insights.")
        else:
            failure_rate = (m["failed"] / total_evaluable) * 100
            
            # Overall quality assessment
            if failure_rate == 0:
                insights.append("🎉 PERFECT QUALITY: No failed dimensions detected!")
                insights.append("✅ All measured dimensions are within specification.")
            elif failure_rate < 5:
                insights.append("🟢 EXCELLENT QUALITY: Very low failure rate (<5%)")
                insights.append("Minor issues detected - continue monitoring.")
            elif failure_rate < 15:
                insights.append("🟡 GOOD QUALITY: Acceptable failure rate (<15%)")
                insights.append("Some process attention may be needed.")
            elif failure_rate < 30:
                insights.append("🟠 MARGINAL QUALITY: High failure rate (15-30%)")
                insights.append("Process improvement actions recommended.")
            else:
                insights.append("🔴 POOR QUALITY: Very high failure rate (>30%)")
                insights.append("Immediate corrective actions required!")
            
            insights.append("")
            
            # Detailed breakdown
            if m["failed"] > 0:
                insights.append(f"❌ FAILED DIMENSIONS: {m['failed']}")
                
                # Check if we have classification data
                cc_failed = 0  # Would need to analyze results by class
                sc_failed = 0
                ic_failed = 0
                
                # This would require analyzing self.results for failed dimensions by class
                if self.results:
                    for result in self.results:
                        status = result.status.value if hasattr(result.status, "value") else str(result.status)
                        if status in ["BAD", "FAIL", "OUT_OF_SPEC"]:
                            classe = getattr(result, 'classe', None)
                            if classe == "CC":
                                cc_failed += 1
                            elif classe == "SC":
                                sc_failed += 1
                            elif classe == "IC":
                                ic_failed += 1
                
                if cc_failed > 0:
                    insights.append(f"  🚨 Critical Characteristics (CC): {cc_failed} failures")
                if sc_failed > 0:
                    insights.append(f"  ⚠️ Significant Characteristics (SC): {sc_failed} failures")
                if ic_failed > 0:
                    insights.append(f"  ℹ️ Important Characteristics (IC): {ic_failed} failures")
            
            if m["warning"] > 0:
                warning_rate = (m["warning"] / total_evaluable) * 100
                insights.append(f"⚠️ WARNING DIMENSIONS: {m['warning']} ({warning_rate:.1f}%)")
                insights.append("  These dimensions are close to tolerance limits.")
            
            insights.append("")
            
            # Recommendations
            insights.append("💡 RECOMMENDATIONS")
            insights.append("=" * 30)
            
            if failure_rate > 20:
                insights.append("🔧 Immediate Actions Required:")
                insights.append("  • Review failed dimensions in Quality Issues tab")
                insights.append("  • Investigate root causes for high failure rate")
                insights.append("  • Consider process parameter adjustments")
                insights.append("  • Increase measurement frequency for monitoring")
            elif failure_rate > 5:
                insights.append("📊 Process Monitoring:")
                insights.append("  • Monitor failed dimensions for patterns")
                insights.append("  • Check measurement system capability")
                insights.append("  • Review process control parameters")
            else:
                insights.append("✅ Continue Current Operations:")
                insights.append("  • Maintain current process parameters")
                insights.append("  • Continue regular monitoring")
                insights.append("  • Consider process optimization opportunities")
            
            # Capability insights
            if m["capability_count"] > 0:
                insights.append("")
                insights.append("📈 PROCESS CAPABILITY INSIGHTS:")
                if m["avg_ppk"] >= 1.33:
                    insights.append("✅ Process capability is adequate for production.")
                else:
                    insights.append("⚠️ Process capability improvement recommended.")
                    insights.append("  Consider reducing process variation.")
        
        # Display insights
        self.quality_insights_text.setPlainText("\n".join(insights))

    def _update_warning_dimensions_table(self):
        """Update warning dimensions table"""
        self.warning_table.setRowCount(0)
        
        if not self.results:
            return
        
        # Get warning dimensions from results
        warning_results = []
        for result in self.results:
            status = result.status.value if hasattr(result.status, "value") else str(result.status)
            if status in ["WARNING", "WARN"]:
                warning_results.append(result)
        
        if not warning_results:
            self.warning_table.setRowCount(1)
            self.warning_table.setItem(0, 0, QTableWidgetItem("✅ No warning dimensions"))
            self.warning_table.setItem(0, 1, QTableWidgetItem("All dimensions are clearly pass/fail"))
            for col in range(2, 6):
                self.warning_table.setItem(0, col, QTableWidgetItem(""))
        else:
            self.warning_table.setRowCount(len(warning_results))
            
            for row, result in enumerate(warning_results):
                # Element ID
                self.warning_table.setItem(row, 0, QTableWidgetItem(str(result.element_id)))
                
                # Description
                description = str(result.description)[:30] + "..." if len(str(result.description)) > 30 else str(result.description)
                self.warning_table.setItem(row, 1, QTableWidgetItem(description))
                
                # Cavity
                cavity = getattr(result, 'cavity', 'N/A')
                self.warning_table.setItem(row, 2, QTableWidgetItem(str(cavity)))
                
                # Class
                classe = getattr(result, 'classe', 'N/A')
                self.warning_table.setItem(row, 3, QTableWidgetItem(str(classe)))
                
                # Issue description
                issue = "Borderline measurements - review process stability"
                self.warning_table.setItem(row, 4, QTableWidgetItem(issue))
                
                # Recommendation
                recommendation = "Monitor closely, check measurement repeatability"
                self.warning_table.setItem(row, 5, QTableWidgetItem(recommendation))
                
                # Color the row
                for col in range(6):
                    item = self.warning_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 250, 230))

    def _refresh_quality_analysis(self):
        """Refresh quality analysis manually"""
        try:
            # Force update of quality tab
            self._update_quality_tab()
            self._log_message("🔄 Quality analysis refreshed", "INFO")
        except Exception as e:
            self._log_message(f"❌ Error refreshing quality analysis: {str(e)}", "ERROR")

    def _update_capability_tab(self):
        """Update process capability analysis tab"""
        m = self.metrics
        
        # Update capability circles
        pp_value = m["avg_pp"] if m["capability_count"] > 0 else 0
        ppk_value = m["avg_ppk"] if m["capability_count"] > 0 else 0
        
        # Convert to percentage for display (assuming max capability of 2.0)
        pp_percentage = min(100, (pp_value / 2.0) * 100)
        ppk_percentage = min(100, (ppk_value / 2.0) * 100)
        
        self.pp_circle.update_value(pp_percentage, f"{pp_value:.3f}")
        self.ppk_circle.update_value(ppk_percentage, f"{ppk_value:.3f}")
        
        # Update capability interpretation
        if m["capability_count"] == 0:
            interpretation = "🔍 No capability data available\n\nCapability analysis requires:\n• CC, SC, or IC classified dimensions\n• Multiple measurements per dimension\n• Completed dimensional study"
            self.capability_interpretation.setStyleSheet("color: #6c757d;")
        else:
            if ppk_value >= 1.67:
                interpretation = "🟢 EXCELLENT CAPABILITY\n\nPpk ≥ 1.67 indicates excellent process performance. Process is highly capable with minimal variation."
                self.capability_interpretation.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif ppk_value >= 1.33:
                interpretation = "🟡 ADEQUATE CAPABILITY\n\nPpk ≥ 1.33 indicates acceptable process performance. Monitor for consistency."
                self.capability_interpretation.setStyleSheet("color: #f39c12; font-weight: bold;")
            elif ppk_value >= 1.0:
                interpretation = "🟠 MARGINAL CAPABILITY\n\nPpk ≥ 1.0 indicates marginal performance. Process improvement recommended."
                self.capability_interpretation.setStyleSheet("color: #e67e22; font-weight: bold;")
            else:
                interpretation = "🔴 POOR CAPABILITY\n\nPpk < 1.0 indicates poor process performance. Immediate corrective action required."
                self.capability_interpretation.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        self.capability_interpretation.setText(interpretation)
        
        # Update capability details table
        self._update_capability_table()

    def _update_capability_table(self):
        """Update capability details table"""
        self.capability_table.setRowCount(0)
        
        if not self.results:
            return
        
        # Get dimensions with capability data
        capability_results = []
        for result in self.results:
            if (hasattr(result, "classe") and result.classe and 
                result.classe.upper() in ["CC", "SC", "IC"] and
                (hasattr(result, "pp") and result.pp is not None or
                 hasattr(result, "ppk") and result.ppk is not None)):
                capability_results.append(result)
        
        if not capability_results:
            self.capability_table.setRowCount(1)
            self.capability_table.setItem(0, 0, QTableWidgetItem("No capability data"))
            self.capability_table.setItem(0, 1, QTableWidgetItem("N/A"))
            self.capability_table.setItem(0, 2, QTableWidgetItem("Apply study to CC, SC, IC dimensions"))
            for col in range(3, 6):
                self.capability_table.setItem(0, col, QTableWidgetItem(""))
            return
        
        # Sort by Ppk value (highest first)
        capability_results.sort(key=lambda x: getattr(x, "ppk", 0) or 0, reverse=True)
        
        self.capability_table.setRowCount(len(capability_results))
        
        for row, result in enumerate(capability_results):
            # Element ID
            self.capability_table.setItem(row, 0, QTableWidgetItem(str(result.element_id)))
            
            # Class
            classe = getattr(result, 'classe', 'N/A')
            class_item = QTableWidgetItem(str(classe))
            if classe == "CC":
                class_item.setBackground(QColor(255, 230, 230))  # Red
                class_item.setForeground(QColor(139, 21, 56))
            elif classe == "SC":
                class_item.setBackground(QColor(255, 245, 230))  # Orange
                class_item.setForeground(QColor(184, 134, 11))
            elif classe == "IC":
                class_item.setBackground(QColor(230, 255, 230))  # Green
                class_item.setForeground(QColor(27, 93, 46))
            class_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.capability_table.setItem(row, 1, class_item)
            
            # Description
            description = str(result.description)[:40] + "..." if len(str(result.description)) > 40 else str(result.description)
            self.capability_table.setItem(row, 2, QTableWidgetItem(description))
            
            # Pp
            pp_value = getattr(result, "pp", None)
            pp_text = f"{pp_value:.3f}" if pp_value is not None else "N/A"
            self.capability_table.setItem(row, 3, QTableWidgetItem(pp_text))
            
            # Ppk
            ppk_value = getattr(result, "ppk", None)
            ppk_text = f"{ppk_value:.3f}" if ppk_value is not None else "N/A"
            ppk_item = QTableWidgetItem(ppk_text)
            
            # Color code Ppk based on capability level
            if ppk_value is not None:
                if ppk_value >= 1.67:
                    ppk_item.setBackground(QColor(230, 255, 230))  # Green
                    ppk_item.setForeground(QColor(27, 174, 96))
                elif ppk_value >= 1.33:
                    ppk_item.setBackground(QColor(255, 255, 230))  # Yellow
                    ppk_item.setForeground(QColor(243, 156, 18))
                elif ppk_value >= 1.0:
                    ppk_item.setBackground(QColor(255, 245, 230))  # Orange
                    ppk_item.setForeground(QColor(230, 126, 34))
                else:
                    ppk_item.setBackground(QColor(255, 230, 230))  # Red
                    ppk_item.setForeground(QColor(231, 76, 60))
            
            ppk_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.capability_table.setItem(row, 4, ppk_item)
            
            # Capability level
            if ppk_value is not None:
                if ppk_value >= 1.67:
                    level = "Excellent"
                elif ppk_value >= 1.33:
                    level = "Adequate"
                elif ppk_value >= 1.0:
                    level = "Marginal"
                else:
                    level = "Poor"
            else:
                level = "N/A"
            
            self.capability_table.setItem(row, 5, QTableWidgetItem(level))

    def _update_evaluation_tab(self):
        """Update evaluation types analysis tab"""
        m = self.metrics
        
        # Update evaluation type summary cards
        eval_updates = {
            "normal": str(m["normal_dimensions"]),
            "gd&t": str(m["gdt_dimensions"]),
            "basic": str(m["basic_dimensions"]),
            "informative": str(m["informative_dimensions"]),
            "note": str(m["note_dimensions"])
        }
        
        for key, value in eval_updates.items():
            if key in self.eval_summary_cards:
                self.eval_summary_cards[key].update_value(value)
        
        # Update detailed evaluation table
        self._update_evaluation_table()
        
        # Update special analysis
        self._update_special_analysis()

    def _update_evaluation_table(self):
        """Update detailed evaluation type table"""
        m = self.metrics
        eval_type_status = m.get("eval_type_status", {})
        
        eval_data = [
            ("Normal", m["normal_dimensions"]),
            ("GD&T", m["gdt_dimensions"]),
            ("Basic", m["basic_dimensions"]),
            ("Informative", m["informative_dimensions"]),
            ("Note", m["note_dimensions"])
        ]
        
        rows_with_data = [x for x in eval_data if x[1] > 0]
        self.eval_table.setRowCount(len(rows_with_data))
        
        row = 0
        for eval_type, count in eval_data:
            if count > 0:
                self.eval_table.setItem(row, 0, QTableWidgetItem(eval_type))
                self.eval_table.setItem(row, 1, QTableWidgetItem(str(count)))
                
                # Get status breakdown for this evaluation type
                if eval_type in eval_type_status:
                    status_data = eval_type_status[eval_type]
                    good = status_data.get("GOOD", 0)
                    bad = status_data.get("BAD", 0)
                    warning = status_data.get("WARNING", 0)
                    ted = status_data.get("TED", 0)
                    to_check = status_data.get("TO_CHECK", 0)
                    
                    self.eval_table.setItem(row, 2, QTableWidgetItem(str(good)))
                    self.eval_table.setItem(row, 3, QTableWidgetItem(str(bad)))
                    self.eval_table.setItem(row, 4, QTableWidgetItem(str(warning)))
                    self.eval_table.setItem(row, 5, QTableWidgetItem(str(ted)))
                    self.eval_table.setItem(row, 6, QTableWidgetItem(str(to_check)))
                    
                    # Calculate success rate for this evaluation type
                    total_evaluable = good + bad + warning
                    if total_evaluable > 0:
                        success_rate = (good / total_evaluable) * 100
                        success_item = QTableWidgetItem(f"{success_rate:.1f}%")
                        
                        # Color code success rate
                        if success_rate >= 95:
                            success_item.setBackground(QColor(230, 255, 230))
                        elif success_rate >= 80:
                            success_item.setBackground(QColor(255, 255, 230))
                        else:
                            success_item.setBackground(QColor(255, 230, 230))
                        
                        self.eval_table.setItem(row, 7, success_item)
                    else:
                        # Non-evaluable types
                        if eval_type in ["Basic", "Informative"]:
                            self.eval_table.setItem(row, 7, QTableWidgetItem("T.E.D."))
                        elif eval_type == "Note":
                            self.eval_table.setItem(row, 7, QTableWidgetItem("Manual"))
                        else:
                            self.eval_table.setItem(row, 7, QTableWidgetItem("N/A"))
                else:
                    # No results data yet
                    for col in range(2, 8):
                        self.eval_table.setItem(row, col, QTableWidgetItem("TBD"))
                
                row += 1

    def _update_special_analysis(self):
        """Update special analysis text"""
        m = self.metrics
        analysis_parts = []
        
        # Tolerance distribution analysis
        total_dims = m["total_dimensions"]
        if total_dims > 0:
            bilateral_pct = (m["bilateral_tolerances"] / total_dims) * 100
            unilateral_pct = (m["unilateral_tolerances"] / total_dims) * 100
            
            analysis_parts.append("📐 TOLERANCE DISTRIBUTION ANALYSIS")
            analysis_parts.append("=" * 50)
            analysis_parts.append(f"• Bilateral Tolerances: {m['bilateral_tolerances']} ({bilateral_pct:.1f}%)")
            analysis_parts.append("  └─ Standard ±tolerance specifications")
            analysis_parts.append(f"• Unilateral Tolerances: {m['unilateral_tolerances']} ({unilateral_pct:.1f}%)")
            analysis_parts.append("  └─ Single-direction tolerance limits")
            analysis_parts.append(f"• Zero Nominal GD&T: {m['zero_nominal_gdt']} dimensions")
            analysis_parts.append("  └─ Typical for form/position tolerances")
            analysis_parts.append("")
        
        # Evaluation type insights
        analysis_parts.append("🔍 EVALUATION TYPE INSIGHTS")
        analysis_parts.append("=" * 50)
        
        if m["normal_dimensions"] > 0:
            analysis_parts.append(f"• Normal Dimensions: {m['normal_dimensions']}")
            analysis_parts.append("  └─ Standard measurement evaluation with statistical analysis")
        
        if m["gdt_dimensions"] > 0:
            analysis_parts.append(f"• GD&T Features: {m['gdt_dimensions']}")
            analysis_parts.append("  └─ Geometric dimensioning & tolerancing specifications")
        
        if m["basic_dimensions"] > 0:
            analysis_parts.append(f"• Basic Dimensions: {m['basic_dimensions']}")
            analysis_parts.append("  └─ Reference dimensions (T.E.D. - Theoretically Exact)")
        
        if m["informative_dimensions"] > 0:
            analysis_parts.append(f"• Informative Dimensions: {m['informative_dimensions']}")
            analysis_parts.append("  └─ Information only (T.E.D. - Not for evaluation)")
        
        if m["note_dimensions"] > 0:
            analysis_parts.append(f"• Note Dimensions: {m['note_dimensions']}")
            analysis_parts.append("  └─ Require manual review and verification")
        
        analysis_parts.append("")
        
        # Quality insights
        if m["studies_run"] > 0:
            analysis_parts.append("🎯 QUALITY INSIGHTS")
            analysis_parts.append("=" * 50)
            
            if m["success_rate"] >= 95:
                analysis_parts.append("✅ Process is performing excellently (≥95% success rate)")
            elif m["success_rate"] >= 80:
                analysis_parts.append("⚠️ Process performance is acceptable but monitor closely")
            else:
                analysis_parts.append("🚨 Process performance requires immediate attention")
            
            if m["capability_count"] > 0:
                analysis_parts.append(f"📊 Process capability calculated for {m['capability_count']} critical dimensions")
                if m["avg_ppk"] >= 1.33:
                    analysis_parts.append("✅ Overall process capability is adequate")
                else:
                    analysis_parts.append("⚠️ Process capability improvement needed")
        
        # Combine and display
        self.special_analysis_text.setPlainText("\n".join(analysis_parts))

    def _update_comparison_tab(self):
        """Update data comparison tab"""
        if not self.session_loaded:
            # Show message about no session loaded
            self.session_info_text.setPlainText("📋 No session loaded for comparison\n\nLoad a session file to enable data change tracking and comparison features.")
            return
        
        # Update change summary cards
        m = self.metrics
        change_updates = {
            "modified": str(m["dimensions_modified"]),
            "added": str(m["dimensions_added"]),
            "deleted": str(m["dimensions_deleted"])
        }
        
        for key, value in change_updates.items():
            if key in self.change_summary_cards:
                self.change_summary_cards[key].update_value(value)
        
        # Update modifications table
        self._update_modifications_table()
        
        # Update session info
        self._update_session_info()

    def _update_modifications_table(self):
        """Update detailed modifications table"""
        m = self.metrics
        modifications = m.get("modification_details", [])
        
        self.modifications_table.setRowCount(0)
        
        if not modifications:
            self.modifications_table.setRowCount(1)
            self.modifications_table.setItem(0, 0, QTableWidgetItem("No modifications detected"))
            self.modifications_table.setItem(0, 1, QTableWidgetItem(""))
            self.modifications_table.setItem(0, 2, QTableWidgetItem(""))
            self.modifications_table.setItem(0, 3, QTableWidgetItem("Data unchanged since session load"))
            return
        
        # Expand modifications to show individual changes
        table_rows = []
        for mod in modifications:
            element_id = mod["element_id"]
            changes = mod["changes"]
            
            for change in changes:
                if ":" in change:
                    field, change_detail = change.split(":", 1)
                    table_rows.append({
                        "element_id": element_id,
                        "change_type": "Modified",
                        "field": field.strip(),
                        "details": change_detail.strip()
                    })
        
        # Add entries for added/deleted dimensions
        if m["dimensions_added"] > 0:
            table_rows.append({
                "element_id": "Multiple",
                "change_type": "Added",
                "field": "New Dimensions",
                "details": f"{m['dimensions_added']} dimensions added"
            })
        
        if m["dimensions_deleted"] > 0:
            table_rows.append({
                "element_id": "Multiple", 
                "change_type": "Deleted",
                "field": "Removed Dimensions",
                "details": f"{m['dimensions_deleted']} dimensions removed"
            })
        
        # Populate table
        self.modifications_table.setRowCount(len(table_rows))
        
        for row, row_data in enumerate(table_rows):
            self.modifications_table.setItem(row, 0, QTableWidgetItem(row_data["element_id"]))
            
            # Change type with color coding
            change_type_item = QTableWidgetItem(row_data["change_type"])
            if row_data["change_type"] == "Modified":
                change_type_item.setBackground(QColor(255, 245, 230))
                change_type_item.setForeground(QColor(230, 126, 34))
            elif row_data["change_type"] == "Added":
                change_type_item.setBackground(QColor(230, 255, 230))
                change_type_item.setForeground(QColor(27, 174, 96))
            elif row_data["change_type"] == "Deleted":
                change_type_item.setBackground(QColor(255, 230, 230))
                change_type_item.setForeground(QColor(231, 76, 60))
            change_type_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.modifications_table.setItem(row, 1, change_type_item)
            
            self.modifications_table.setItem(row, 2, QTableWidgetItem(row_data["field"]))
            self.modifications_table.setItem(row, 3, QTableWidgetItem(row_data["details"]))

    def _update_session_info(self):
        """Update session information text"""
        m = self.metrics
        
        session_start = m.get("session_start", datetime.now())
        if isinstance(session_start, str):
            try:
                session_start = datetime.fromisoformat(session_start)
            except Exception:
                session_start = datetime.now()
        
        duration = datetime.now() - session_start
        duration_str = str(duration).split('.')[0]
        
        info_parts = []
        info_parts.append("📊 SESSION INFORMATION")
        info_parts.append("=" * 50)
        info_parts.append(f"Session Duration: {duration_str}")
        info_parts.append(f"Original Data Dimensions: {len(self.original_data)}")
        info_parts.append(f"Current Data Dimensions: {m['total_dimensions']}")
        info_parts.append(f"Studies Executed: {m['studies_run']}")
        info_parts.append("")
        
        info_parts.append("🔄 CHANGE SUMMARY")
        info_parts.append("=" * 50)
        
        total_changes = m["dimensions_modified"] + m["dimensions_added"] + m["dimensions_deleted"]
        if total_changes == 0:
            info_parts.append("✅ No changes detected - Data integrity maintained")
        else:
            info_parts.append(f"📝 Total Changes: {total_changes}")
            if m["dimensions_modified"] > 0:
                info_parts.append(f"  • Modified: {m['dimensions_modified']} dimensions")
            if m["dimensions_added"] > 0:
                info_parts.append(f"  • Added: {m['dimensions_added']} dimensions")
            if m["dimensions_deleted"] > 0:
                info_parts.append(f"  • Deleted: {m['dimensions_deleted']} dimensions")
        
        info_parts.append("")
        
        # Add data quality metrics
        info_parts.append("📈 DATA QUALITY METRICS")
        info_parts.append("=" * 50)
        info_parts.append(f"Data Completeness: {m['completeness']:.1f}%")
        info_parts.append(f"Measurements Available: {m['total_measurements']}")
        info_parts.append(f"Dimensions with Data: {m['dimensions_with_measurements']}")
        
        if m['studies_run'] > 0:
            info_parts.append("")
            info_parts.append("🎯 PERFORMANCE SUMMARY")
            info_parts.append("=" * 50)
            info_parts.append(f"Overall Success Rate: {m['success_rate']:.1f}%")
            info_parts.append(f"Passed Dimensions: {m['passed']}")
            info_parts.append(f"Failed Dimensions: {m['failed']}")
            info_parts.append(f"Warning Dimensions: {m['warning']}")
            
            if m['capability_count'] > 0:
                info_parts.append(f"Process Capability (Avg Pp): {m['avg_pp']:.3f}")
                info_parts.append(f"Process Capability (Avg Ppk): {m['avg_ppk']:.3f}")
        
        # Combine and display
        self.session_info_text.setPlainText("\n".join(info_parts))
