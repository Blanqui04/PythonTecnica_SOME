# src/gui/windows/components/dimensional_summary_widget.py - ENHANCED OPTIMIZED VERSION
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QGroupBox, QHBoxLayout, 
    QTextEdit, QProgressBar, QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QSplitter, QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import pandas as pd
from typing import List, Optional
from src.models.dimensional.dimensional_result import DimensionalResult


class MetricCard(QFrame):
    """Professional automotive-styled metric display card"""
    
    def __init__(self, title: str, value: str, icon: str = "📊", color: str = "#1B365D"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(80)
        self.setFixedWidth(140)  # Fixed width to prevent overlapping
        
        # Professional automotive color scheme
        automotive_colors = {
            "#3498db": "#1B365D",  # Deep blue
            "#9b59b6": "#5D1B36",  # Deep purple
            "#27ae60": "#1B5D2E",  # Deep green
            "#f39c12": "#B8860B",  # Deep gold
            "#e67e22": "#8B4513",  # Deep orange
            "#e74c3c": "#8B1538"   # Deep red
        }
        
        prof_color = automotive_colors.get(color, color)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {prof_color}10, stop:1 {prof_color}05);
                border: 2px solid {prof_color};
                border-radius: 8px;
                margin: 2px;
            }}
            QFrame:hover {{
                border: 3px solid {prof_color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {prof_color}20, stop:1 {prof_color}08);
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {prof_color}; border: none;")
        self.title_label.setWordWrap(True)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {prof_color}; border: none;")
        self.value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def update_value(self, value: str):
        """Update card value"""
        self.value_label.setText(str(value))


class CompactProgressBar(QFrame):
    """Compact progress bar with label and value"""
    
    def __init__(self, label: str, value: int, color: str = "#3498db", icon: str = ""):
        super().__init__()
        self.setFixedHeight(28)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Label
        label_widget = QLabel(f"{icon} {label}")
        label_widget.setFont(QFont("Segoe UI", 8, QFont.Bold))
        label_widget.setMinimumWidth(100)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(value)
        self.progress.setMaximumHeight(18)
        self.progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 2px;
                text-align: center;
                font-size: 8px;
                font-weight: bold;
            }}
        """)
        
        # Value label
        self.value_label = QLabel(f"{value}%")
        self.value_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.value_label.setMinimumWidth(40)
        self.value_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(label_widget)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
    
    def update_value(self, value: int):
        """Update progress value"""
        self.progress.setValue(value)
        self.value_label.setText(f"{value}%")


class SummaryWidget(QWidget):
    """Enhanced summary widget with unified design and comprehensive analysis"""
    
    update_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._reset_metrics()
        self._last_update = datetime.now()
        self._update_threshold = 1.0
        
        # Data tracking for comparisons
        self.original_data = {}  # Data when session is first loaded
        self.current_data = {}   # Current working data
        self.session_loaded = False
        
        # Initialize UI
        self._init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._periodic_refresh)
        self.refresh_timer.start(3000)

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
            "ted": 0,  # T.E.D. (Basic/Informative)
            "to_check": 0,  # Notes and other review items
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
            "session_start": datetime.now()
        }

    def _init_ui(self):
        """Initialize optimized UI with unified design"""
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Session header
        self.session_header = self._create_session_header()
        layout.addWidget(self.session_header)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Key metrics and quick stats
        left_panel = self._create_metrics_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Detailed analysis tabs
        right_panel = self._create_analysis_tabs()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% - 70%)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        self.setLayout(layout)

    def _create_session_header(self) -> QWidget:
        """Create session info header"""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setMaximumHeight(45)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2c3e50, stop:1 #3498db);
                color: white;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        
        # Session info
        self.session_label = QLabel("🕐 Session: Just started")
        self.session_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        # Quick stats
        self.quick_stats_label = QLabel("📊 No data loaded")
        self.quick_stats_label.setFont(QFont("Segoe UI", 9))
        
        layout.addWidget(self.session_label)
        layout.addStretch()
        layout.addWidget(self.quick_stats_label)
        
        header.setLayout(layout)
        return header

    def _create_metrics_panel(self) -> QWidget:
        """Create key metrics panel with improved layout"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame { 
                background-color: #f8f9fa; 
                border-radius: 6px; 
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Title with professional automotive styling
        title = QLabel("📊 Key Metrics")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #1B365D; padding: 6px; background: #E8F4FD; border-radius: 4px;")
        layout.addWidget(title)
        
        # Metric cards in a scrollable area to prevent overlapping
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(200)
        
        cards_widget = QWidget()
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(6)
        cards_widget.setLayout(self.metrics_grid)
        scroll_area.setWidget(cards_widget)
        
        layout.addWidget(scroll_area)
        
        # Create metric cards with automotive colors
        self.metric_cards = {}
        self._create_metric_cards()
        
        # Status breakdown section with fixed height
        status_group = QGroupBox("📈 Status Overview")
        status_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                color: #1B365D; 
                background: #F0F8FF;
                border: 1px solid #B0C4DE;
                border-radius: 6px;
                padding-top: 10px;
            }
        """)
        status_group.setFixedHeight(150)
        self.status_layout = QVBoxLayout()
        self.status_layout.setSpacing(4)
        status_group.setLayout(self.status_layout)
        layout.addWidget(status_group)
        
        # Process capability section with fixed height
        capability_group = QGroupBox("🎯 Process Capability (CC/SC/IC)")
        capability_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                color: #5D1B36; 
                background: #FFF0F8;
                border: 1px solid #DEB0C4;
                border-radius: 6px;
                padding-top: 10px;
            }
        """)
        capability_group.setFixedHeight(140)
        self.capability_layout = QVBoxLayout()
        self.capability_layout.setSpacing(4)
        capability_group.setLayout(self.capability_layout)
        layout.addWidget(capability_group)
        
        # Change tracking section with fixed height
        changes_group = QGroupBox("🔄 Data Changes")
        changes_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                color: #B8860B; 
                background: #FFFAF0;
                border: 1px solid #DDD;
                border-radius: 6px;
                padding-top: 10px;
            }
        """)
        changes_group.setFixedHeight(120)
        self.changes_layout = QVBoxLayout()
        self.changes_layout.setSpacing(4)
        changes_group.setLayout(self.changes_layout)
        layout.addWidget(changes_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_metric_cards(self):
        """Create optimized metric cards"""
        cards_data = [
            ("Total Dimensions", "0", "📏", "#3498db"),
            ("Studies Run", "0", "🔬", "#9b59b6"),
            ("Success Rate", "0%", "✅", "#27ae60"),
            ("Completeness", "0%", "📊", "#f39c12"),
            ("GD&T Count", "0", "🔧", "#e67e22"),
            ("Changes Made", "0", "✏️", "#e74c3c"),
        ]

        for i, (title, value, icon, color) in enumerate(cards_data):
            card = MetricCard(title, value, icon, color)
            key = title.lower().replace(" ", "_").replace("&", "")
            self.metric_cards[key] = card
            row, col = divmod(i, 2)
            self.metrics_grid.addWidget(card, row, col)

    def _create_analysis_tabs(self) -> QWidget:
        """Create unified analysis tabs"""
        tabs = QTabWidget()
        tabs.setStyleSheet("""
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
                padding: 8px 12px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5dbdb;
            }
        """)

        # Overview tab
        tabs.addTab(self._create_overview_tab(), "📊 Overview")
        
        # Quality analysis tab
        tabs.addTab(self._create_quality_tab(), "🎯 Quality")
        
        # Evaluation types tab
        tabs.addTab(self._create_evaluation_tab(), "🔧 Evaluation Types")
        
        # Data comparison tab
        tabs.addTab(self._create_comparison_tab(), "🔄 Comparisons")

        return tabs

    def _create_overview_tab(self) -> QWidget:
        """Create overview tab with cavity and tolerance analysis"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Cavity breakdown
        cavity_group = QGroupBox("🏭 Cavity Analysis")
        cavity_group.setStyleSheet("QGroupBox { font-weight: bold; color: #34495e; }")
        self.cavity_layout = QVBoxLayout()
        cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(cavity_group)

        # Tolerance analysis
        tol_group = QGroupBox("📐 Tolerance Analysis")
        tol_group.setStyleSheet("QGroupBox { font-weight: bold; color: #16a085; }")
        self.tolerance_layout = QVBoxLayout()
        tol_group.setLayout(self.tolerance_layout)
        layout.addWidget(tol_group)

        # Classification breakdown (CC, SC, IC)
        class_group = QGroupBox("📋 Classification Breakdown")
        class_group.setStyleSheet("QGroupBox { font-weight: bold; color: #8e44ad; }")
        self.classification_layout = QVBoxLayout()
        class_group.setLayout(self.classification_layout)
        layout.addWidget(class_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_quality_tab(self) -> QWidget:
        """Create quality analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Failed dimensions table
        failed_group = QGroupBox("❌ Failed Dimensions")
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(5)
        self.failed_table.setHorizontalHeaderLabels(
            ["Element ID", "Description", "Cavity", "Out of Spec", "Type"]
        )
        self.failed_table.horizontalHeader().setStretchLastSection(True)
        self.failed_table.setMaximumHeight(200)
        self.failed_table.setAlternatingRowColors(True)
        failed_layout = QVBoxLayout()
        failed_layout.addWidget(self.failed_table)
        failed_group.setLayout(failed_layout)
        layout.addWidget(failed_group)

        # Recommendations
        rec_group = QGroupBox("💡 Quality Recommendations")
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(150)
        self.recommendations_text.setReadOnly(True)
        rec_layout = QVBoxLayout()
        rec_layout.addWidget(self.recommendations_text)
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_evaluation_tab(self) -> QWidget:
        """Create evaluation types analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Evaluation type breakdown table
        eval_group = QGroupBox("🔧 Evaluation Type Breakdown")
        self.eval_table = QTableWidget()
        self.eval_table.setColumnCount(6)
        self.eval_table.setHorizontalHeaderLabels(
            ["Type", "Count", "Passed", "Failed", "Other", "Success Rate"]
        )
        self.eval_table.horizontalHeader().setStretchLastSection(True)
        self.eval_table.setMaximumHeight(200)
        self.eval_table.setAlternatingRowColors(True)
        eval_layout = QVBoxLayout()
        eval_layout.addWidget(self.eval_table)
        eval_group.setLayout(eval_layout)
        layout.addWidget(eval_group)

        # Special analysis for GD&T vs Unilateral
        special_group = QGroupBox("🎯 Special Analysis")
        self.special_layout = QVBoxLayout()
        special_group.setLayout(self.special_layout)
        layout.addWidget(special_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_comparison_tab(self) -> QWidget:
        """Create data comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Comparison summary
        comp_group = QGroupBox("📊 Original vs Current Comparison")
        self.comparison_layout = QVBoxLayout()
        comp_group.setLayout(self.comparison_layout)
        layout.addWidget(comp_group)

        # Modification details
        mod_group = QGroupBox("📝 Modification Details")
        self.modifications_text = QTextEdit()
        self.modifications_text.setMaximumHeight(200)
        self.modifications_text.setReadOnly(True)
        self.modifications_text.setFont(QFont("Consolas", 9))
        mod_layout = QVBoxLayout()
        mod_layout.addWidget(self.modifications_text)
        mod_group.setLayout(mod_layout)
        layout.addWidget(mod_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def ensure_visibility(self):
        """Ensure summary widget is visible and accessible - NEW FUNCTION"""
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
            self._log_message(
                f"❌ Error ensuring summary visibility: {str(e)}", "ERROR"
            )

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

            # Update with results
            if results:
                self._analyze_results(results)

            # Update all UI components
            self._update_all_content()
            
            self.update_complete.emit()

        except Exception as e:
            self._log_message(f"❌ Error updating summary: {str(e)}", "ERROR")

    def _analyze_table_data(self, table_data: pd.DataFrame):
        """Comprehensive table data analysis with fixed tolerance detection"""
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
        
        # FIXED: Tolerance analysis
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
            
            # Count tolerance types correctly
            if lower_tol is not None and upper_tol is not None and lower_tol != upper_tol:
                m["bilateral_tolerances"] += 1
            elif (lower_tol is not None and upper_tol is None) or (lower_tol is None and upper_tol is not None):
                m["unilateral_tolerances"] += 1
            elif lower_tol is not None and upper_tol is not None and lower_tol == upper_tol:
                m["unilateral_tolerances"] += 1  # Same tolerance value = unilateral
            
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
        """Analyze dimensional results for status and capability with proper evaluation type tracking"""
        if not results:
            return

        m = self.metrics
        m["studies_run"] += 1
        
        # Status counts with evaluation type tracking
        status_counts = {"GOOD": 0, "BAD": 0, "WARNING": 0, "TED": 0, "TO_CHECK": 0}
        eval_type_status = {}  # Track status by evaluation type
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
        
        # Store which dimensions have capability data
        m["capability_dimensions"] = []
        for result in results:
            if (hasattr(result, "classe") and result.classe and 
                result.classe.upper() in ["CC", "SC", "IC"] and
                (hasattr(result, "pp") or hasattr(result, "ppk"))):
                m["capability_dimensions"].append({
                    "id": result.element_id,
                    "class": result.classe,
                    "pp": getattr(result, "pp", None),
                    "ppk": getattr(result, "ppk", None)
                })

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
            
            # Find modifications (exclude NaN to NaN changes)
            for _, row in current_data.iterrows():
                element_id = row.get("element_id")
                if element_id in self.original_data:
                    original = self.original_data[element_id]
                    changes = []
                    
                    # Check measurements
                    for i in range(1, 6):
                        orig_val = original["measurements"].get(f"measurement_{i}")
                        curr_val = row.get(f"measurement_{i}")
                        
                        # Skip NaN to NaN comparisons
                        if pd.isna(orig_val) and pd.isna(curr_val):
                            continue
                        
                        if pd.notna(orig_val) and pd.notna(curr_val):
                            if abs(float(orig_val) - float(curr_val)) > 0.001:  # Tolerance for float comparison
                                changes.append(f"M{i}: {orig_val:.3f} → {curr_val:.3f}")
                        elif pd.isna(orig_val) and pd.notna(curr_val):
                            changes.append(f"M{i}: empty → {curr_val:.3f}")
                        elif pd.notna(orig_val) and pd.isna(curr_val):
                            changes.append(f"M{i}: {orig_val:.3f} → empty")
                    
                    # Check other key fields
                    for field in ["nominal", "lower_tolerance", "upper_tolerance", "force_status"]:
                        orig_val = original.get(field)
                        curr_val = row.get(field)
                        
                        # Skip NaN to NaN comparisons
                        if pd.isna(orig_val) and pd.isna(curr_val):
                            continue
                        
                        if orig_val != curr_val:
                            changes.append(f"{field}: {orig_val} → {curr_val}")
                    
                    if changes:
                        modifications.append({
                            "element_id": element_id,
                            "changes": changes[:5],  # Limit to first 5 changes
                            "change_count": len(changes)
                        })
            
            self.metrics["dimensions_modified"] = len(modifications)
            self.metrics["modification_details"] = modifications[:20]  # Keep last 20
            
        except Exception as e:
            self._log_message(f"❌ Error tracking changes: {str(e)}", "ERROR")

    def _update_all_content(self):
        """Update all UI content"""
        try:
            self._update_session_header()
            self._update_metric_cards()
            self._update_status_breakdown()
            self._update_capability_section()
            self._update_changes_section()
            self._update_tabs_content()
        except Exception as e:
            self._log_message(f"❌ Error updating content: {str(e)}", "ERROR")

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

    def _update_metric_cards(self):
        """Update metric cards with current values"""
        m = self.metrics
        
        updates = {
            "total_dimensions": str(m["total_dimensions"]),
            "studies_run": str(m["studies_run"]),
            "success_rate": f"{m['success_rate']:.1f}%",
            "completeness": f"{m['completeness']:.1f}%",
            "gdt_count": str(m["gdt_dimensions"]),
            "changes_made": str(m["dimensions_modified"] + m["dimensions_added"] + m["dimensions_deleted"])
        }
        
        for key, value in updates.items():
            if key in self.metric_cards:
                self.metric_cards[key].update_value(value)

    def _update_status_breakdown(self):
        """Update status breakdown with progress bars"""
        self._clear_layout(self.status_layout)
        
        m = self.metrics
        total = m["passed"] + m["failed"] + m["warning"] + m["ted"] + m["to_check"]
        
        if total > 0:
            status_data = [
                ("Passed", m["passed"], "#27ae60", "✅"),
                ("Failed", m["failed"], "#e74c3c", "❌"),
                ("Warnings", m["warning"], "#f39c12", "⚠️"),
                ("T.E.D.", m["ted"], "#3498db", "ℹ️"),
                ("To Check", m["to_check"], "#f39c12", "🔍")
            ]
            
            for name, count, color, icon in status_data:
                if count > 0:
                    percentage = int((count / total) * 100)
                    progress_bar = CompactProgressBar(name, percentage, color, icon)
                    self.status_layout.addWidget(progress_bar)
        else:
            no_data_label = QLabel("📊 No status data available")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.status_layout.addWidget(no_data_label)

    def _update_capability_section(self):
        """Update process capability section for CC, SC, IC dimensions with better formatting"""
        self._clear_layout(self.capability_layout)
        
        m = self.metrics
        
        # Classification counts with better visual layout
        class_data = [
            ("Critical (CC)", m["cc_dimensions"], "#8B1538", "🔴"),
            ("Significant (SC)", m["sc_dimensions"], "#B8860B", "🟡"),
            ("Important (IC)", m["ic_dimensions"], "#1B5D2E", "🟢")
        ]
        
        for label, count, color, icon in class_data:
            if count > 0:
                class_bar = CompactProgressBar(
                    label, 
                    min(100, int((count / m["total_dimensions"]) * 100)) if m["total_dimensions"] > 0 else 0,
                    color, 
                    icon
                )
                self.capability_layout.addWidget(class_bar)
        
        # Capability statistics with detailed information
        if m["capability_count"] > 0:
            cap_frame = QFrame()
            cap_layout = QVBoxLayout()
            cap_layout.setSpacing(4)
            
            cap_title = QLabel(f"📊 SPC Analysis ({m['capability_count']} dimensions)")
            cap_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
            cap_title.setStyleSheet("color: #5D1B36;")
            cap_layout.addWidget(cap_title)
            
            # PP and PPK values
            pp_label = QLabel(f"Pp (Process Performance): {m['avg_pp']:.3f}")
            pp_label.setFont(QFont("Segoe UI", 8))
            ppk_label = QLabel(f"Ppk (Process Performance Index): {m['avg_ppk']:.3f}")
            ppk_label.setFont(QFont("Segoe UI", 8))
            
            cap_layout.addWidget(pp_label)
            cap_layout.addWidget(ppk_label)
            
            # Capability interpretation
            if m["avg_ppk"] >= 1.67:
                interp = "🟢 Excellent capability"
            elif m["avg_ppk"] >= 1.33:
                interp = "🟡 Adequate capability"
            elif m["avg_ppk"] >= 1.0:
                interp = "🟠 Marginal capability"
            else:
                interp = "🔴 Poor capability - Action required"
            
            interp_label = QLabel(interp)
            interp_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
            cap_layout.addWidget(interp_label)
            
            cap_frame.setLayout(cap_layout)
            self.capability_layout.addWidget(cap_frame)
        else:
            no_cap_label = QLabel("📊 No SPC data available\n(Apply to CC, SC, IC dimensions)")
            no_cap_label.setAlignment(Qt.AlignCenter)
            no_cap_label.setFont(QFont("Segoe UI", 9))
            self.capability_layout.addWidget(no_cap_label)

    def _update_changes_section(self):
        """Update changes tracking section"""
        self._clear_layout(self.changes_layout)
        
        m = self.metrics
        
        if not self.session_loaded:
            no_orig_label = QLabel("📋 No original data for comparison")
            no_orig_label.setAlignment(Qt.AlignCenter)
            self.changes_layout.addWidget(no_orig_label)
            return
        
        # Change summary
        changes_summary = QLabel(f"""📊 Change Summary:
• Modified: {m["dimensions_modified"]} dimensions
• Added: {m["dimensions_added"]} dimensions  
• Deleted: {m["dimensions_deleted"]} dimensions""")
        changes_summary.setFont(QFont("Segoe UI", 9))
        changes_summary.setWordWrap(True)
        self.changes_layout.addWidget(changes_summary)
        
        # Progress indicator for modifications
        if m["total_dimensions"] > 0:
            mod_percentage = int((m["dimensions_modified"] / m["total_dimensions"]) * 100)
            mod_progress = CompactProgressBar("Modified", mod_percentage, "#e74c3c", "✏️")
            self.changes_layout.addWidget(mod_progress)

    def _update_tabs_content(self):
        """Update content in all tabs"""
        # Overview tab content
        self._update_cavity_breakdown()
        self._update_tolerance_analysis()
        self._update_classification_breakdown()
        
        # Quality tab content
        self._update_failed_table()
        self._update_recommendations()
        
        # Evaluation tab content
        self._update_evaluation_table()
        self._update_special_analysis()
        
        # Comparison tab content
        self._update_comparison_content()
        self._update_modification_details()

    def _update_cavity_breakdown(self):
        """Update cavity analysis"""
        self._clear_layout(self.cavity_layout)
        
        m = self.metrics
        cavity_data = m.get("cavity_breakdown", {})
        
        if cavity_data:
            for cavity, count in cavity_data.items():
                cavity_frame = QFrame()
                cavity_layout = QHBoxLayout()
                cavity_layout.setContentsMargins(4, 2, 4, 2)
                
                cavity_label = QLabel(f"🏭 Cavity {cavity}")
                cavity_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                count_label = QLabel(f"{count} dimensions")
                count_label.setFont(QFont("Segoe UI", 9))
                
                cavity_layout.addWidget(cavity_label)
                cavity_layout.addStretch()
                cavity_layout.addWidget(count_label)
                cavity_frame.setLayout(cavity_layout)
                self.cavity_layout.addWidget(cavity_frame)
        else:
            no_cavity_label = QLabel("🏭 No cavity data available")
            no_cavity_label.setAlignment(Qt.AlignCenter)
            self.cavity_layout.addWidget(no_cavity_label)

    def _update_tolerance_analysis(self):
        """Update tolerance analysis"""
        self._clear_layout(self.tolerance_layout)
        
        m = self.metrics
        
        tol_info = [
            ("Bilateral Tolerances", m["bilateral_tolerances"], "⚖️"),
            ("Unilateral Tolerances", m["unilateral_tolerances"], "➡️"),
            ("Zero Nominal GD&T", m["zero_nominal_gdt"], "🎯")
        ]
        
        for label, count, icon in tol_info:
            tol_frame = QFrame()
            tol_layout = QHBoxLayout()
            tol_layout.setContentsMargins(4, 2, 4, 2)
            
            tol_label = QLabel(f"{icon} {label}")
            tol_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            
            count_label = QLabel(str(count))
            count_label.setFont(QFont("Segoe UI", 9))
            
            tol_layout.addWidget(tol_label)
            tol_layout.addStretch()
            tol_layout.addWidget(count_label)
            tol_frame.setLayout(tol_layout)
            self.tolerance_layout.addWidget(tol_frame)

    def _update_classification_breakdown(self):
        """Update classification breakdown"""
        self._clear_layout(self.classification_layout)
        
        m = self.metrics

        # Ensure all counts are integers and handle None safely
        cc = int(m.get("cc_dimensions", 0) or 0)
        sc = int(m.get("sc_dimensions", 0) or 0)
        ic = int(m.get("ic_dimensions", 0) or 0)
        total = int(m.get("total_dimensions", 0) or 0)
        other = total - cc - sc - ic if total - cc - sc - ic > 0 else 0

        class_info = [
            ("Critical Characteristics (CC)", cc, "🔴"),
            ("Significant Characteristics (SC)", sc, "🟡"),
            ("Important Characteristics (IC)", ic, "🟢"),
            ("Other Dimensions", other, "⚪")
        ]
        
        for label, count, icon in class_info:
            if count > 0:
                class_frame = QFrame()
                class_layout = QHBoxLayout()
                class_layout.setContentsMargins(4, 2, 4, 2)
                
                class_label = QLabel(f"{icon} {label}")
                class_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                count_label = QLabel(str(count))
                count_label.setFont(QFont("Segoe UI", 9))
                
                class_layout.addWidget(class_label)
                class_layout.addStretch()
                class_layout.addWidget(count_label)
                class_frame.setLayout(class_layout)
                self.classification_layout.addWidget(class_frame)

    def _update_failed_table(self):
        """Update failed dimensions table with actual data"""
        self.failed_table.setRowCount(0)
        
        if not hasattr(self, 'results') or not self.results:
            return
        
        # Get failed dimensions
        failed_results = [r for r in self.results if r.status.value in ["BAD", "FAIL", "OUT_OF_SPEC"]]
        
        if failed_results:
            self.failed_table.setRowCount(len(failed_results))
            
            for row, result in enumerate(failed_results):
                # Element ID
                self.failed_table.setItem(row, 0, QTableWidgetItem(str(result.element_id)))
                
                # Description
                self.failed_table.setItem(row, 1, QTableWidgetItem(str(result.description)[:50] + "..." if len(str(result.description)) > 50 else str(result.description)))
                
                # Cavity
                cavity = getattr(result, 'cavity', 'N/A')
                self.failed_table.setItem(row, 2, QTableWidgetItem(str(cavity)))
                
                # Out of spec details
                out_of_spec = []
                if hasattr(result, 'measurements') and result.measurements:
                    for i, meas in enumerate(result.measurements):
                        if meas is not None:
                            if result.lower_tolerance is not None and meas < (result.nominal + result.lower_tolerance):
                                out_of_spec.append(f"M{i+1}: {meas:.3f} < {result.nominal + result.lower_tolerance:.3f}")
                            elif result.upper_tolerance is not None and meas > (result.nominal + result.upper_tolerance):
                                out_of_spec.append(f"M{i+1}: {meas:.3f} > {result.nominal + result.upper_tolerance:.3f}")
                
                self.failed_table.setItem(row, 3, QTableWidgetItem("; ".join(out_of_spec[:2]) + ("..." if len(out_of_spec) > 2 else "")))
                
                # Type
                eval_type = getattr(result, 'evaluation_type', 'Normal')
                self.failed_table.setItem(row, 4, QTableWidgetItem(eval_type))
                
                # Color code the row
                for col in range(5):
                    item = self.failed_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 230, 230))  # Light red background
        else:
            # Show message when no failed dimensions
            self.failed_table.setRowCount(1)
            self.failed_table.setItem(0, 0, QTableWidgetItem("No failed dimensions"))
            self.failed_table.setItem(0, 1, QTableWidgetItem("All dimensions passed"))
            self.failed_table.setItem(0, 2, QTableWidgetItem(""))
            self.failed_table.setItem(0, 3, QTableWidgetItem(""))
            self.failed_table.setItem(0, 4, QTableWidgetItem(""))
            
            for col in range(5):
                item = self.failed_table.item(0, col)
                if item:
                    item.setBackground(QColor(230, 255, 230))  # Light green background

    def _update_recommendations(self):
        """Update quality recommendations"""
        m = self.metrics
        recommendations = []
        
        # Generate intelligent recommendations
        if m["success_rate"] < 95 and m["success_rate"] >= 80:
            recommendations.append("⚠️ Success rate below 95% - Review failed dimensions for improvement opportunities.")
        elif m["success_rate"] < 80:
            recommendations.append("🚨 CRITICAL: Success rate below 80% - Immediate process review required.")
        
        if m["completeness"] < 90:
            recommendations.append("📊 Measurement completeness below 90% - Consider increasing sample sizes.")
        
        if m["capability_count"] > 0 and m["avg_ppk"] < 1.33:
            recommendations.append("🎯 Process capability below target - Review CC, SC, IC dimensions.")
        
        if m["dimensions_modified"] > m["total_dimensions"] * 0.1:
            recommendations.append("✏️ High modification rate detected - Verify data consistency.")
        
        if not recommendations:
            recommendations.append("✅ All quality metrics look good! Continue monitoring.")
        
        # Update recommendations text
        rec_text = "\n\n".join(recommendations)
        self.recommendations_text.setPlainText(rec_text)

    def _update_evaluation_table(self):
        """Update evaluation types table with correct status tracking"""
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
                    passed = status_data.get("GOOD", 0)
                    failed = status_data.get("BAD", 0)
                    other = status_data.get("WARNING", 0) + status_data.get("TED", 0) + status_data.get("TO_CHECK", 0)
                    
                    self.eval_table.setItem(row, 2, QTableWidgetItem(str(passed)))
                    self.eval_table.setItem(row, 3, QTableWidgetItem(str(failed)))
                    self.eval_table.setItem(row, 4, QTableWidgetItem(str(other)))
                    
                    # Calculate success rate for this evaluation type
                    total_evaluable = passed + failed
                    if total_evaluable > 0:
                        success_rate = (passed / total_evaluable) * 100
                        self.eval_table.setItem(row, 5, QTableWidgetItem(f"{success_rate:.1f}%"))
                    else:
                        if eval_type in ["Basic", "Informative"]:
                            self.eval_table.setItem(row, 5, QTableWidgetItem("T.E.D."))
                        elif eval_type == "Note":
                            self.eval_table.setItem(row, 5, QTableWidgetItem("To Check"))
                        else:
                            self.eval_table.setItem(row, 5, QTableWidgetItem("N/A"))
                else:
                    # No results data yet
                    for col in range(2, 6):
                        self.eval_table.setItem(row, col, QTableWidgetItem("TBD"))
                
                row += 1

    def _update_special_analysis(self):
        """Update special analysis section with corrected information"""
        self._clear_layout(self.special_layout)
        
        m = self.metrics
        
        # Create analysis widget
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()
        analysis_layout.setSpacing(8)
        
        # Tolerance Distribution Analysis
        tolerance_frame = QFrame()
        tolerance_frame.setStyleSheet("background: #F0F8FF; border: 1px solid #B0C4DE; border-radius: 4px; padding: 8px;")
        tolerance_layout = QVBoxLayout()
        
        tolerance_title = QLabel("📐 Tolerance Distribution Analysis")
        tolerance_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        tolerance_title.setStyleSheet("color: #1B365D;")
        tolerance_layout.addWidget(tolerance_title)
        
        # Tolerance breakdown
        tol_info = QLabel(f"""• Bilateral Tolerances: {m["bilateral_tolerances"]} dimensions (±tolerance)
    • Unilateral Tolerances: {m["unilateral_tolerances"]} dimensions (+ or - only)
    • Zero Nominal GD&T: {m["zero_nominal_gdt"]} dimensions (typical for form/position)""")
        
        tol_info.setFont(QFont("Segoe UI", 9))
        tol_info.setWordWrap(True)
        tolerance_layout.addWidget(tol_info)
        
        tolerance_frame.setLayout(tolerance_layout)
        analysis_layout.addWidget(tolerance_frame)
        
        # Evaluation Type Insights
        insights_frame = QFrame()
        insights_frame.setStyleSheet("background: #FFF8F0; border: 1px solid #DEB887; border-radius: 4px; padding: 8px;")
        insights_layout = QVBoxLayout()
        
        insights_title = QLabel("🔍 Evaluation Type Insights")
        insights_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        insights_title.setStyleSheet("color: #8B4513;")
        insights_layout.addWidget(insights_title)
        
        insights_info = QLabel(f"""• Normal Dimensions: {m["normal_dimensions"]} (standard measurement evaluation)
    • GD&T Features: {m["gdt_dimensions"]} (geometric dimensioning & tolerancing)
    • Basic Dimensions: {m["basic_dimensions"]} (reference only, T.E.D.)
    • Informative Dimensions: {m["informative_dimensions"]} (information only, T.E.D.)
    • Note Dimensions: {m["note_dimensions"]} (require manual review)""")
        
        insights_info.setFont(QFont("Segoe UI", 9))
        insights_info.setWordWrap(True)
        insights_layout.addWidget(insights_info)
        
        insights_frame.setLayout(insights_layout)
        analysis_layout.addWidget(insights_frame)
        
        analysis_widget.setLayout(analysis_layout)
        self.special_layout.addWidget(analysis_widget)

    def _update_comparison_content(self):
        """Update comparison content"""
        self._clear_layout(self.comparison_layout)
        
        if not self.session_loaded:
            no_comp_label = QLabel("📋 Load a session file to enable comparison tracking")
            no_comp_label.setAlignment(Qt.AlignCenter)
            self.comparison_layout.addWidget(no_comp_label)
            return
        
        m = self.metrics
        
        # Comparison summary with progress bars
        comp_summary = QLabel("📊 Data Changes Since Session Load:")
        comp_summary.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.comparison_layout.addWidget(comp_summary)
        
        # Change statistics
        changes_info = [
            ("Dimensions Modified", m["dimensions_modified"], "#e74c3c", "✏️"),
            ("Dimensions Added", m["dimensions_added"], "#27ae60", "➕"),
            ("Dimensions Deleted", m["dimensions_deleted"], "#e67e22", "🗑️")
        ]
        
        for label, count, color, icon in changes_info:
            change_frame = QFrame()
            change_layout = QHBoxLayout()
            change_layout.setContentsMargins(4, 2, 4, 2)
            
            change_label = QLabel(f"{icon} {label}")
            change_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            
            count_label = QLabel(str(count))
            count_label.setFont(QFont("Segoe UI", 9))
            count_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            change_layout.addWidget(change_label)
            change_layout.addStretch()
            change_layout.addWidget(count_label)
            change_frame.setLayout(change_layout)
            self.comparison_layout.addWidget(change_frame)

    def _update_modification_details(self):
        """Update modification details"""
        m = self.metrics
        modifications = m.get("modification_details", [])
        
        if modifications:
            details_text = "📝 Recent Modifications:\n" + "="*50 + "\n\n"
            
            for mod in modifications:
                element_id = mod["element_id"]
                changes = mod["changes"]
                change_count = mod["change_count"]
                
                details_text += f"🔧 {element_id}:\n"
                for change in changes:
                    details_text += f"   • {change}\n"
                
                if change_count > len(changes):
                    details_text += f"   ... and {change_count - len(changes)} more changes\n"
                
                details_text += "\n"
            
            self.modifications_text.setPlainText(details_text)
        else:
            self.modifications_text.setPlainText("📋 No modifications detected since session load.")

    def _periodic_refresh(self):
        """Periodic refresh for real-time updates"""
        try:
            if (hasattr(self, 'parent_window') and self.parent_window and
                hasattr(self.parent_window, 'table_manager')):
                
                # Get current table data
                df = self.parent_window.table_manager._get_dataframe_from_tables()
                if not df.empty:
                    self._analyze_table_data(df)
                    self._track_data_changes(df)
                    self._update_session_header()
                    self._update_metric_cards()
                    
        except Exception:
            pass  # Fail silently to avoid spam

    def record_edit(self, description: str):
        """Record an edit action"""
        try:
            self.metrics["edits_made"] += 1
            self._log_message(f"✏️ Edit recorded: {description}")
        except Exception as e:
            self._log_message(f"❌ Error recording edit: {str(e)}", "ERROR")

    def _clear_layout(self, layout):
        """Safely clear a layout"""
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception:
            pass

    def _log_message(self, message: str, level: str = "INFO"):
        """Safe logging with null checks and reduced verbosity"""
        # Only log important events, not every update
        important_levels = {"ERROR", "WARNING", "INFO"}
        if level in important_levels or "restored" in message or "reset" in message or "edit" in message.lower():
            try:
                if (hasattr(self, "parent_window") and self.parent_window and 
                    hasattr(self.parent_window, "_log_message")):
                    self.parent_window._log_message(message, level)
                else:
                    print(f"[{level}] {message}")
            except Exception:
                print(f"[{level}] {message}")
        # Otherwise, skip debug/periodic update logs

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

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, "refresh_timer"):
                self.refresh_timer.stop()
            self._log_message("Summary widget cleanup completed")
        except Exception as e:
            self._log_message(f"❌ Error during cleanup: {str(e)}", "ERROR")