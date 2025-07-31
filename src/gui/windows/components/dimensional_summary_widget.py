# src/gui/windows/components/dimensional_summary_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QGroupBox,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QFrame,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import pandas as pd
from typing import List, Optional
from src.models.dimensional.dimensional_result import DimensionalResult


class ModernGroupBox(QGroupBox):
    """Enhanced group box with modern styling"""

    def __init__(self, title: str):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
        """)


class MetricCard(QFrame):
    """Modern metric display card"""

    def __init__(
        self, title: str, value: str, icon: str = "📊", color: str = "#3498db"
    ):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {color};
                border-radius: 10px;
                margin: 4px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background-color: #f8f9fa;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        # Title with icon
        title_label = QLabel(f"{icon} {title}")
        title_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; margin-bottom: 2px;")

        # Value
        value_label = QLabel(str(value))
        value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        value_label.setStyleSheet("color: #2c3e50;")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        self.setLayout(layout)

        # Store references for updates
        self.title_label = title_label
        self.value_label = value_label

    def update_value(self, value: str):
        """Update the card value"""
        self.value_label.setText(str(value))


class SummaryWidget(QWidget):
    update_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._reset_metrics()
        self._last_update = datetime.now()
        self._update_threshold = 0.3

        # Initialize UI
        self._init_ui()

        # Store original data for comparison tracking
        self.original_data = {}
        self.comparison_data = {
            "original_vs_final": {},
            "modifications": [],
            "additions": [],
            "deletions": [],
        }

    def _init_ui(self):
        """Initialize the enhanced UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-bottom-color: transparent;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
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

        # Add tabs
        self.tabs.addTab(self._create_overview_tab(), "📊 Overview")
        self.tabs.addTab(self._create_quality_tab(), "🎯 Quality Analysis")
        self.tabs.addTab(self._create_integrity_tab(), "📝 Data Integrity")
        self.tabs.addTab(self._create_performance_tab(), "📈 Performance")
        self.tabs.addTab(self._create_detailed_analysis_tab(), "🔍 Detailed Analysis")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _reset_metrics(self):
        """Reset all metrics to default values"""
        self.metrics = {
            "total_dimensions": 0,
            "studies_run": 0,
            "edits_made": 0,
            "dimensions_added": 0,
            "dimensions_deleted": 0,
            "dimensions_modified": 0,
            "passed": 0,
            "failed": 0,
            "warning": 0,
            "not_evaluable": 0,
            "success_rate": 0.0,
            "completeness": 0.0,
            "cavity_breakdown": {},
            "evaltype_breakdown": {},
            "original_vs_final": {},
            "edit_history": [],
            "study_history": [],
            "failed_dimensions": [],
            "warning_dimensions": [],
            "measurement_stats": {},
            "tolerance_analysis": {},
            "force_status_usage": {},
        }
        self.session_start_time = datetime.now()
        self.original_data = {}
        self.comparison_data = {
            "original_vs_final": {},
            "modifications": [],
            "additions": [],
            "deletions": [],
        }

    def _log_message(self, message: str, level: str = "INFO"):
        """Safe logging with null checks"""
        try:
            if (
                hasattr(self, "parent_window")
                and self.parent_window
                and hasattr(self.parent_window, "_log_message")
            ):
                self.parent_window._log_message(message, level)
            else:
                print(f"[{level}] {message}")
        except Exception:
            print(f"[{level}] {message}")

    def store_original_data(self, table_data: pd.DataFrame):
        """Store original values for comparison tracking - ENHANCED"""
        if table_data is None or table_data.empty:
            return

        try:
            for _, row in table_data.iterrows():
                element_id = row.get("element_id")
                if element_id and element_id not in self.original_data:
                    # Store comprehensive original values
                    original_values = {
                        "measurements": {
                            f"measurement_{i}": row.get(f"measurement_{i}")
                            for i in range(1, 6)
                        },
                        "nominal": row.get("nominal"),
                        "lower_tolerance": row.get("lower_tolerance"),
                        "upper_tolerance": row.get("upper_tolerance"),
                        "description": row.get("description"),
                        "cavity": row.get("cavity"),
                        "class": row.get("class"),
                        "evaluation_type": row.get("evaluation_type"),
                        "stored_at": datetime.now().isoformat(),
                    }
                    self.original_data[element_id] = original_values

            self._log_message(
                f"📋 Stored original data for {len(self.original_data)} dimensions",
                "INFO",
            )

        except Exception as e:
            self._log_message(f"❌ Error storing original data: {str(e)}", "ERROR")

    def compare_data_changes(self, current_data: pd.DataFrame):
        """Compare current data with original and track changes - NEW FUNCTION"""
        if current_data is None or current_data.empty or not self.original_data:
            return

        try:
            modifications = []
            additions = []
            deletions = []

            # Current element IDs
            current_ids = set(current_data["element_id"].dropna().unique())
            original_ids = set(self.original_data.keys())

            # Find additions (new dimensions)
            new_ids = current_ids - original_ids
            additions = list(new_ids)

            # Find deletions (removed dimensions)
            deleted_ids = original_ids - current_ids
            deletions = list(deleted_ids)

            # Find modifications (changed values)
            for _, row in current_data.iterrows():
                element_id = row.get("element_id")
                if element_id in self.original_data:
                    original = self.original_data[element_id]
                    changes = []

                    # Check measurements
                    for i in range(1, 6):
                        orig_val = original["measurements"].get(f"measurement_{i}")
                        curr_val = row.get(f"measurement_{i}")

                        if pd.notna(orig_val) and pd.notna(curr_val):
                            if float(orig_val) != float(curr_val):
                                changes.append(
                                    f"measurement_{i}: {orig_val} → {curr_val}"
                                )
                        elif pd.isna(orig_val) and pd.notna(curr_val):
                            changes.append(f"measurement_{i}: empty → {curr_val}")
                        elif pd.notna(orig_val) and pd.isna(curr_val):
                            changes.append(f"measurement_{i}: {orig_val} → empty")

                    # Check other key fields
                    key_fields = [
                        "nominal",
                        "lower_tolerance",
                        "upper_tolerance",
                        "description",
                    ]
                    for field in key_fields:
                        orig_val = original.get(field)
                        curr_val = row.get(field)
                        if orig_val != curr_val:
                            changes.append(f"{field}: {orig_val} → {curr_val}")

                    if changes:
                        modifications.append(
                            {
                                "element_id": element_id,
                                "changes": changes,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

            # Update comparison data
            self.comparison_data.update(
                {
                    "modifications": modifications,
                    "additions": additions,
                    "deletions": deletions,
                    "last_comparison": datetime.now().isoformat(),
                }
            )

            # Update metrics
            self.metrics["dimensions_modified"] = len(modifications)
            self.metrics["dimensions_added"] = len(additions)
            self.metrics["dimensions_deleted"] = len(deletions)

            self._log_message(
                f"📊 Data comparison: {len(modifications)} modified, {len(additions)} added, {len(deletions)} deleted",
                "INFO",
            )

        except Exception as e:
            self._log_message(f"❌ Error comparing data changes: {str(e)}", "ERROR")

    def update_summary(
        self,
        results: Optional[List[DimensionalResult]] = None,
        table_data: Optional[pd.DataFrame] = None,
        force_refresh: bool = False,
        store_original: bool = False,
    ):
        """Update summary with comprehensive error handling - ENHANCED"""
        try:
            now = datetime.now()

            # Handle None results gracefully
            if results is None:
                results = []

            self._log_message(f"Processing {len(results)} results...", "DEBUG")

            # Throttling check (but allow force refresh)
            if (
                not force_refresh
                and (now - self._last_update).total_seconds() < self._update_threshold
            ):
                return
            self._last_update = now

            # Store original data if requested (first time loading data)
            if store_original and table_data is not None:
                self.store_original_data(table_data)

            # Update with results if provided
            if results:
                self._update_with_results(results)

            # Update with table data if provided
            if table_data is not None:
                self._update_with_table_data(table_data)
                # Compare with original data to track changes
                self.compare_data_changes(table_data)

            # Update all tab contents
            self._update_all_tabs()

            self.update_complete.emit()

        except Exception as e:
            self._log_message(f"Error updating summary: {str(e)}", "ERROR")

    def _update_with_results(self, results: List[DimensionalResult]):
        """Update metrics with analysis results"""
        if not results:
            return

        m = self.metrics
        m["studies_run"] += 1

        # Count statuses
        status_counts = {"GOOD": 0, "BAD": 0, "WARNING": 0, "NOT_EVALUABLE": 0}
        failed_dims = []
        warning_dims = []

        for r in results:
            status = r.status.value if hasattr(r.status, "value") else str(r.status)
            status_counts[status] = status_counts.get(status, 0) + 1

            if status == "BAD":
                failed_dims.append(
                    {
                        "element_id": r.element_id,
                        "description": r.description,
                        "cavity": str(r.cavity) if r.cavity else "1",
                        "out_of_spec_count": getattr(r, "out_of_spec_count", 0),
                    }
                )
            elif status == "WARNING":
                warning_dims.append(
                    {
                        "element_id": r.element_id,
                        "description": r.description,
                        "warnings": getattr(r, "warnings", []),
                    }
                )

        m["passed"] = status_counts["GOOD"]
        m["failed"] = status_counts["BAD"]
        m["warning"] = status_counts["WARNING"]
        m["not_evaluable"] = status_counts["NOT_EVALUABLE"]
        m["success_rate"] = (m["passed"] / len(results)) * 100 if results else 0
        m["failed_dimensions"] = failed_dims
        m["warning_dimensions"] = warning_dims

        # Cavity breakdown analysis
        self._analyze_cavities(results)

        # Evaluation type breakdown
        self._analyze_evaluation_types(results)

        # Measurement statistics
        self._analyze_measurements(results)

        # Tolerance analysis
        self._analyze_tolerances(results)

        # Update study history
        study_record = {
            "timestamp": datetime.now(),
            "total": len(results),
            "passed": m["passed"],
            "failed": m["failed"],
            "warning": m["warning"],
            "not_evaluable": m["not_evaluable"],
            "success_rate": m["success_rate"],
        }
        m["study_history"].append(study_record)

        # Keep only last 20 studies
        if len(m["study_history"]) > 20:
            m["study_history"] = m["study_history"][-20:]

        m["total_dimensions"] = len(results)

    def _analyze_cavities(self, results: List[DimensionalResult]):
        """Analyze results by cavity"""
        cavity_stats = {}
        for r in results:
            cavity = str(r.cavity) if r.cavity else "1"
            if cavity not in cavity_stats:
                cavity_stats[cavity] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "warning": 0,
                    "not_evaluable": 0,
                }

            cavity_stats[cavity]["total"] += 1
            status = r.status.value if hasattr(r.status, "value") else str(r.status)

            if status == "GOOD":
                cavity_stats[cavity]["passed"] += 1
            elif status == "BAD":
                cavity_stats[cavity]["failed"] += 1
            elif status == "WARNING":
                cavity_stats[cavity]["warning"] += 1
            else:
                cavity_stats[cavity]["not_evaluable"] += 1

        self.metrics["cavity_breakdown"] = cavity_stats

    def _analyze_evaluation_types(self, results: List[DimensionalResult]):
        """Analyze results by evaluation type - FIXED GD&T detection"""
        eval_stats = {}
        for r in results:
            # Better GD&T detection
            etype = (
                getattr(r, "evaluation_type", None)
                or getattr(r, "feature_type", None)
                or "Normal"
            )

            # Additional GD&T detection logic
            if etype == "Normal" and (
                r.nominal == 0.0
                or any(flag for flag in getattr(r, "gdt_flags", {}).values())
                or "GD&T" in str(r.description).upper()
                or any(
                    symbol in str(r.description) for symbol in ["⌖", "⊥", "∥", "○", "◎"]
                )
            ):
                etype = "GD&T"

            if etype not in eval_stats:
                eval_stats[etype] = {
                    "count": 0,
                    "passed": 0,
                    "failed": 0,
                    "warning": 0,
                    "not_evaluable": 0,
                }

            eval_stats[etype]["count"] += 1
            status = r.status.value if hasattr(r.status, "value") else str(r.status)

            if status == "GOOD":
                eval_stats[etype]["passed"] += 1
            elif status == "BAD":
                eval_stats[etype]["failed"] += 1
            elif status == "WARNING":
                eval_stats[etype]["warning"] += 1
            else:
                eval_stats[etype]["not_evaluable"] += 1

        self.metrics["evaltype_breakdown"] = eval_stats

    def _analyze_measurements(self, results: List[DimensionalResult]):
        """Analyze measurement statistics"""
        measurement_stats = {
            "total_measurements": 0,
            "avg_measurements_per_dimension": 0.0,
            "dimensions_with_full_measurements": 0,
            "measurement_ranges": {},
            "out_of_spec_measurements": 0,
        }

        total_meas = 0
        full_meas_count = 0
        out_of_spec_total = 0

        for r in results:
            if hasattr(r, "measurements") and r.measurements:
                meas_count = len(r.measurements)
                total_meas += meas_count

                if meas_count == 5:  # Full set of measurements
                    full_meas_count += 1

                # Track out of spec measurements
                if hasattr(r, "out_of_spec_count"):
                    out_of_spec_total += r.out_of_spec_count or 0

        measurement_stats["total_measurements"] = total_meas
        measurement_stats["avg_measurements_per_dimension"] = (
            total_meas / len(results) if results else 0
        )
        measurement_stats["dimensions_with_full_measurements"] = full_meas_count
        measurement_stats["out_of_spec_measurements"] = out_of_spec_total

        self.metrics["measurement_stats"] = measurement_stats

    def _analyze_tolerances(self, results: List[DimensionalResult]):
        """Analyze tolerance information"""
        tolerance_stats = {
            "with_tolerances": 0,
            "without_tolerances": 0,
            "bilateral_tolerances": 0,
            "unilateral_tolerances": 0,
            "zero_nominal_dimensions": 0,
            "gdt_dimensions": 0,
        }

        for r in results:
            has_lower = r.lower_tolerance is not None
            has_upper = r.upper_tolerance is not None

            if has_lower or has_upper:
                tolerance_stats["with_tolerances"] += 1

                if has_lower and has_upper:
                    tolerance_stats["bilateral_tolerances"] += 1
                else:
                    tolerance_stats["unilateral_tolerances"] += 1
            else:
                tolerance_stats["without_tolerances"] += 1

            if r.nominal == 0.0:
                tolerance_stats["zero_nominal_dimensions"] += 1

            if getattr(r, "feature_type", "") == "GD&T":
                tolerance_stats["gdt_dimensions"] += 1

        self.metrics["tolerance_analysis"] = tolerance_stats

    def _update_with_table_data(self, table_data: pd.DataFrame):
        """Update metrics with table data"""
        if table_data is None or table_data.empty:
            self.metrics["completeness"] = 0.0
            self.metrics["total_dimensions"] = 0
            return

        # Calculate completeness
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        total_measurements = 0
        total_possible = len(table_data) * 5

        for col in measurement_cols:
            if col in table_data.columns:
                total_measurements += table_data[col].notna().sum()

        self.metrics["completeness"] = (
            (total_measurements / total_possible) * 100 if total_possible else 0
        )
        self.metrics["total_dimensions"] = len(table_data)

        # Analyze force status usage
        if "force_status" in table_data.columns:
            force_status_counts = table_data["force_status"].value_counts().to_dict()
            self.metrics["force_status_usage"] = force_status_counts

    def _create_overview_tab(self):
        """Create enhanced overview tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Session info header
        session_frame = QFrame()
        session_frame.setFrameStyle(QFrame.StyledPanel)
        session_frame.setStyleSheet(
            "background-color: #2c3e50; color: white; border-radius: 8px; padding: 8px;"
        )
        session_layout = QHBoxLayout()

        session_time = datetime.now() - self.session_start_time
        session_info = QLabel(
            f"🕐 Session Time: {str(session_time).split('.')[0]} | 📅 Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        session_info.setFont(QFont("Segoe UI", 9, QFont.Bold))
        session_layout.addWidget(session_info)
        session_frame.setLayout(session_layout)
        layout.addWidget(session_frame)

        # Main metrics cards
        self.overview_cards_layout = QGridLayout()
        layout.addLayout(self.overview_cards_layout)

        # Create metric cards
        self.metric_cards = {}
        self._create_metric_cards()

        # Status breakdown
        status_group = ModernGroupBox("📊 Status Breakdown")
        self.status_layout = QVBoxLayout()
        status_group.setLayout(self.status_layout)
        layout.addWidget(status_group)

        # Cavity comparison
        cavity_group = ModernGroupBox("🏭 Cavity Comparison")
        self.cavity_layout = QVBoxLayout()
        cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(cavity_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_metric_cards(self):
        """Create metric display cards"""
        cards_data = [
            ("Total Dimensions", "0", "📏", "#3498db"),
            ("Studies Run", "0", "🔬", "#9b59b6"),
            ("Success Rate", "0%", "📊", "#27ae60"),
            ("Completeness", "0%", "📈", "#f39c12"),
            ("Passed", "0", "✅", "#27ae60"),
            ("Failed", "0", "❌", "#e74c3c"),
            ("Warnings", "0", "⚠️", "#f39c12"),
            ("Edits Made", "0", "✏️", "#34495e"),
        ]

        for i, (title, value, icon, color) in enumerate(cards_data):
            card = MetricCard(title, value, icon, color)
            self.metric_cards[title.lower().replace(" ", "_")] = card
            row, col = divmod(i, 4)
            self.overview_cards_layout.addWidget(card, row, col)

    def _create_quality_tab(self):
        """Create enhanced quality analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Quality metrics
        metrics_group = ModernGroupBox("🎯 Quality Metrics")
        self.quality_metrics_layout = QVBoxLayout()
        metrics_group.setLayout(self.quality_metrics_layout)
        layout.addWidget(metrics_group)

        # Failed dimensions table
        failed_group = ModernGroupBox("❌ Failed Dimensions")
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(4)
        self.failed_table.setHorizontalHeaderLabels(
            ["Element ID", "Description", "Cavity", "Out of Spec"]
        )
        self.failed_table.horizontalHeader().setStretchLastSection(True)
        self.failed_table.setMaximumHeight(200)
        self.failed_table.setAlternatingRowColors(True)
        failed_group_layout = QVBoxLayout()
        failed_group_layout.addWidget(self.failed_table)
        failed_group.setLayout(failed_group_layout)
        layout.addWidget(failed_group)

        # Recommendations
        rec_group = ModernGroupBox("💡 Quality Recommendations")
        self.recommendations_layout = QVBoxLayout()
        rec_group.setLayout(self.recommendations_layout)
        layout.addWidget(rec_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_integrity_tab(self):
        """Create data integrity analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Measurement statistics
        meas_group = ModernGroupBox("📏 Measurement Statistics")
        self.measurement_stats_layout = QVBoxLayout()
        meas_group.setLayout(self.measurement_stats_layout)
        layout.addWidget(meas_group)

        # Tolerance analysis
        tol_group = ModernGroupBox("📐 Tolerance Analysis")
        self.tolerance_analysis_layout = QVBoxLayout()
        tol_group.setLayout(self.tolerance_analysis_layout)
        layout.addWidget(tol_group)

        # Edit history
        edit_group = ModernGroupBox("✏️ Recent Changes")
        self.edit_area = QTextEdit()
        self.edit_area.setMaximumHeight(150)
        self.edit_area.setReadOnly(True)
        self.edit_area.setFont(QFont("Consolas", 9))
        edit_group_layout = QVBoxLayout()
        edit_group_layout.addWidget(self.edit_area)
        edit_group.setLayout(edit_group_layout)
        layout.addWidget(edit_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_performance_tab(self):
        """Create performance analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Study history chart (simplified)
        history_group = ModernGroupBox("📈 Study History")
        self.study_history_layout = QVBoxLayout()
        history_group.setLayout(self.study_history_layout)
        layout.addWidget(history_group)

        # Performance metrics
        perf_group = ModernGroupBox("⚡ Performance Metrics")
        self.performance_layout = QVBoxLayout()
        perf_group.setLayout(self.performance_layout)
        layout.addWidget(perf_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_detailed_analysis_tab(self):
        """Create detailed analysis tab with comparison data - ENHANCED"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Evaluation type breakdown
        eval_group = ModernGroupBox("🔧 Evaluation Type Analysis")
        self.evaltype_layout = QVBoxLayout()
        eval_group.setLayout(self.evaltype_layout)
        layout.addWidget(eval_group)

        # Force status usage
        force_group = ModernGroupBox("🔄 Force Status Usage")
        self.force_status_layout = QVBoxLayout()
        force_group.setLayout(self.force_status_layout)
        layout.addWidget(force_group)

        # NEW: Data Comparison Section
        comparison_group = ModernGroupBox("📊 Original vs Current Data Comparison")
        self.comparison_layout = QVBoxLayout()
        comparison_group.setLayout(self.comparison_layout)
        layout.addWidget(comparison_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _update_all_tabs(self):
        """Update all tab contents"""
        try:
            self._update_overview_tab_content()
            self._update_quality_tab_content()
            self._update_integrity_tab_content()
            self._update_performance_tab_content()
            self._update_detailed_analysis_tab_content()
        except Exception as e:
            self._log_message(f"Error updating tabs: {str(e)}", "ERROR")

    def _update_overview_tab_content(self):
        """Update overview tab with current metrics"""
        m = self.metrics

        # Update metric cards
        if hasattr(self, "metric_cards"):
            self.metric_cards["total_dimensions"].update_value(m["total_dimensions"])
            self.metric_cards["studies_run"].update_value(m["studies_run"])
            self.metric_cards["success_rate"].update_value(f"{m['success_rate']:.1f}%")
            self.metric_cards["completeness"].update_value(f"{m['completeness']:.1f}%")
            self.metric_cards["passed"].update_value(m["passed"])
            self.metric_cards["failed"].update_value(m["failed"])
            self.metric_cards["warnings"].update_value(m["warning"])
            self.metric_cards["edits_made"].update_value(m["edits_made"])

        # Update status breakdown
        self._clear_layout(self.status_layout)
        total = m["passed"] + m["failed"] + m["warning"] + m["not_evaluable"]

        if total > 0:
            # Create progress bars for each status
            status_data = [
                ("Passed", m["passed"], "#27ae60", "✅"),
                ("Failed", m["failed"], "#e74c3c", "❌"),
                ("Warnings", m["warning"], "#f39c12", "⚠️"),
                ("Not Evaluable", m["not_evaluable"], "#95a5a6", "ℹ️"),
            ]

            for status_name, count, color, icon in status_data:
                if count > 0:
                    percentage = (count / total) * 100

                    status_frame = QFrame()
                    status_layout = QHBoxLayout()
                    status_layout.setContentsMargins(5, 5, 5, 5)

                    label = QLabel(f"{icon} {status_name}: {count} ({percentage:.1f}%)")
                    label.setFont(QFont("Segoe UI", 9, QFont.Bold))

                    progress = QProgressBar()
                    progress.setMaximum(100)
                    progress.setValue(int(percentage))
                    progress.setStyleSheet(f"""
                        QProgressBar::chunk {{
                            background-color: {color};
                            border-radius: 3px;
                        }}
                    """)

                    status_layout.addWidget(label, 1)
                    status_layout.addWidget(progress, 2)
                    status_frame.setLayout(status_layout)
                    self.status_layout.addWidget(status_frame)

        # Update cavity comparison
        self._clear_layout(self.cavity_layout)
        if m["cavity_breakdown"]:
            for cavity, stats in m["cavity_breakdown"].items():
                if stats["total"] > 0:
                    success_rate = (stats["passed"] / stats["total"]) * 100

                    cavity_frame = QFrame()
                    cavity_layout = QHBoxLayout()

                    info_label = QLabel(
                        f"🏭 Cavity {cavity}: {stats['passed']}/{stats['total']} passed"
                    )
                    info_label.setFont(QFont("Segoe UI", 9))

                    rate_label = QLabel(f"{success_rate:.1f}%")
                    rate_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    rate_label.setStyleSheet(
                        f"color: {'#27ae60' if success_rate >= 95 else '#e74c3c' if success_rate < 80 else '#f39c12'};"
                    )

                    cavity_layout.addWidget(info_label)
                    cavity_layout.addStretch()
                    cavity_layout.addWidget(rate_label)
                    cavity_frame.setLayout(cavity_layout)
                    self.cavity_layout.addWidget(cavity_frame)

    def _update_quality_tab_content(self):
        """Update quality analysis tab"""
        m = self.metrics

        # Update quality metrics
        self._clear_layout(self.quality_metrics_layout)

        metrics_frame = QFrame()
        metrics_layout = QGridLayout()

        quality_metrics = [
            ("Success Rate", f"{m['success_rate']:.1f}%", "📊"),
            ("Passed Dimensions", str(m["passed"]), "✅"),
            ("Failed Dimensions", str(m["failed"]), "❌"),
            ("Warning Dimensions", str(m["warning"]), "⚠️"),
        ]

        for i, (metric, value, icon) in enumerate(quality_metrics):
            label = QLabel(f"{icon} <b>{metric}:</b> {value}")
            label.setFont(QFont("Segoe UI", 10))
            row, col = divmod(i, 2)
            metrics_layout.addWidget(label, row, col)

        metrics_frame.setLayout(metrics_layout)
        self.quality_metrics_layout.addWidget(metrics_frame)

        # Update failed dimensions table
        self.failed_table.setRowCount(len(m["failed_dimensions"]))
        for i, dim in enumerate(m["failed_dimensions"]):
            self.failed_table.setItem(i, 0, QTableWidgetItem(dim["element_id"]))
            self.failed_table.setItem(i, 1, QTableWidgetItem(dim["description"]))
            self.failed_table.setItem(i, 2, QTableWidgetItem(dim["cavity"]))
            self.failed_table.setItem(
                i, 3, QTableWidgetItem(str(dim["out_of_spec_count"]))
            )

        # Update recommendations
        self._clear_layout(self.recommendations_layout)
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            rec_label = QLabel(rec)
            rec_label.setWordWrap(True)
            rec_label.setFont(QFont("Segoe UI", 9))
            self.recommendations_layout.addWidget(rec_label)

    def _update_integrity_tab_content(self):
        """Update data integrity tab"""
        m = self.metrics

        # Update measurement statistics
        self._clear_layout(self.measurement_stats_layout)
        meas_stats = m.get("measurement_stats", {})

        meas_info = [
            ("Total Measurements", str(meas_stats.get("total_measurements", 0)), "📏"),
            (
                "Avg per Dimension",
                f"{meas_stats.get('avg_measurements_per_dimension', 0):.1f}",
                "📊",
            ),
            (
                "Full Measurement Sets",
                str(meas_stats.get("dimensions_with_full_measurements", 0)),
                "✅",
            ),
            (
                "Out of Spec Measurements",
                str(meas_stats.get("out_of_spec_measurements", 0)),
                "❌",
            ),
        ]

        meas_frame = QFrame()
        meas_layout = QGridLayout()

        for i, (label, value, icon) in enumerate(meas_info):
            info_label = QLabel(f"{icon} <b>{label}:</b> {value}")
            info_label.setFont(QFont("Segoe UI", 9))
            row, col = divmod(i, 2)
            meas_layout.addWidget(info_label, row, col)

        meas_frame.setLayout(meas_layout)
        self.measurement_stats_layout.addWidget(meas_frame)

        # Update tolerance analysis
        self._clear_layout(self.tolerance_analysis_layout)
        tol_stats = m.get("tolerance_analysis", {})

        tol_info = [
            ("With Tolerances", str(tol_stats.get("with_tolerances", 0)), "📐"),
            ("Without Tolerances", str(tol_stats.get("without_tolerances", 0)), "⚠️"),
            (
                "Bilateral Tolerances",
                str(tol_stats.get("bilateral_tolerances", 0)),
                "⚖️",
            ),
            (
                "Unilateral Tolerances",
                str(tol_stats.get("unilateral_tolerances", 0)),
                "➡️",
            ),
            ("Zero Nominal", str(tol_stats.get("zero_nominal_dimensions", 0)), "🎯"),
            ("GD&T Dimensions", str(tol_stats.get("gdt_dimensions", 0)), "🔧"),
        ]

        tol_frame = QFrame()
        tol_layout = QGridLayout()

        for i, (label, value, icon) in enumerate(tol_info):
            info_label = QLabel(f"{icon} <b>{label}:</b> {value}")
            info_label.setFont(QFont("Segoe UI", 9))
            row, col = divmod(i, 3)
            tol_layout.addWidget(info_label, row, col)

        tol_frame.setLayout(tol_layout)
        self.tolerance_analysis_layout.addWidget(tol_frame)

        # Update edit history
        self.edit_area.clear()
        if m["edit_history"]:
            self.edit_area.append("📝 Recent Changes:")
            self.edit_area.append("-" * 40)
            for edit in m["edit_history"][-10:]:  # Show last 10 edits
                timestamp = edit.get("timestamp", "Unknown")
                description = edit.get("description", "No description")
                self.edit_area.append(f"[{timestamp}] {description}")
        else:
            self.edit_area.append("No recent changes recorded.")

    def _update_performance_tab_content(self):
        """Update performance analysis tab"""
        m = self.metrics

        # Update study history
        self._clear_layout(self.study_history_layout)

        if m["study_history"]:
            history_table = QTableWidget()
            history_table.setColumnCount(6)
            history_table.setHorizontalHeaderLabels(
                ["Time", "Total", "Passed", "Failed", "Warnings", "Success Rate"]
            )
            history_table.setRowCount(
                min(10, len(m["study_history"]))
            )  # Show last 10 studies
            history_table.setMaximumHeight(300)
            history_table.setAlternatingRowColors(True)

            for i, study in enumerate(m["study_history"][-10:]):
                timestamp = (
                    study["timestamp"].strftime("%H:%M:%S")
                    if isinstance(study["timestamp"], datetime)
                    else str(study["timestamp"])
                )
                history_table.setItem(i, 0, QTableWidgetItem(timestamp))
                history_table.setItem(i, 1, QTableWidgetItem(str(study["total"])))
                history_table.setItem(i, 2, QTableWidgetItem(str(study["passed"])))
                history_table.setItem(i, 3, QTableWidgetItem(str(study["failed"])))
                history_table.setItem(i, 4, QTableWidgetItem(str(study["warning"])))
                history_table.setItem(
                    i, 5, QTableWidgetItem(f"{study['success_rate']:.1f}%")
                )

            history_table.resizeColumnsToContents()
            self.study_history_layout.addWidget(history_table)
        else:
            no_history_label = QLabel("📊 No study history available yet.")
            no_history_label.setAlignment(Qt.AlignCenter)
            no_history_label.setFont(QFont("Segoe UI", 10))
            self.study_history_layout.addWidget(no_history_label)

        # Update performance metrics
        self._clear_layout(self.performance_layout)

        session_duration = datetime.now() - self.session_start_time
        avg_study_time = session_duration.total_seconds() / max(m["studies_run"], 1)

        perf_metrics = [
            ("Session Duration", str(session_duration).split(".")[0], "🕐"),
            ("Studies Completed", str(m["studies_run"]), "🔬"),
            ("Avg Study Time", f"{avg_study_time:.1f}s", "⚡"),
            ("Data Completeness", f"{m['completeness']:.1f}%", "📈"),
            ("Dimensions Added", str(m["dimensions_added"]), "➕"),
            ("Dimensions Deleted", str(m["dimensions_deleted"]), "🗑️"),
        ]

        perf_frame = QFrame()
        perf_layout = QGridLayout()

        for i, (metric, value, icon) in enumerate(perf_metrics):
            label = QLabel(f"{icon} <b>{metric}:</b> {value}")
            label.setFont(QFont("Segoe UI", 9))
            row, col = divmod(i, 2)
            perf_layout.addWidget(label, row, col)

        perf_frame.setLayout(perf_layout)
        self.performance_layout.addWidget(perf_frame)

    def _update_detailed_analysis_tab_content(self):
        """Update detailed analysis tab"""
        m = self.metrics
        self._clear_layout(self.evaltype_layout)  # Update evaluation type breakdown

        if m["evaltype_breakdown"]:
            eval_table = QTableWidget()
            eval_table.setColumnCount(6)
            eval_table.setHorizontalHeaderLabels(
                [
                    "Evaluation Type",
                    "Count",
                    "Passed",
                    "Failed",
                    "Warnings",
                    "Success Rate",
                ]
            )
            eval_table.setRowCount(len(m["evaltype_breakdown"]))
            eval_table.setMaximumHeight(200)
            eval_table.setAlternatingRowColors(True)

            for i, (eval_type, stats) in enumerate(m["evaltype_breakdown"].items()):
                success_rate = (
                    (stats["passed"] / stats["count"]) * 100
                    if stats["count"] > 0
                    else 0
                )

                eval_table.setItem(i, 0, QTableWidgetItem(eval_type))
                eval_table.setItem(i, 1, QTableWidgetItem(str(stats["count"])))
                eval_table.setItem(i, 2, QTableWidgetItem(str(stats["passed"])))
                eval_table.setItem(i, 3, QTableWidgetItem(str(stats["failed"])))
                eval_table.setItem(i, 4, QTableWidgetItem(str(stats["warning"])))

                rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
                if success_rate >= 95:
                    rate_item.setBackground(QColor("#d4edda"))
                elif success_rate < 80:
                    rate_item.setBackground(QColor("#f8d7da"))
                else:
                    rate_item.setBackground(QColor("#fff3cd"))
                eval_table.setItem(i, 5, rate_item)

            eval_table.resizeColumnsToContents()
            self.evaltype_layout.addWidget(eval_table)
        else:
            no_eval_label = QLabel("🔧 No evaluation type data available.")
            no_eval_label.setAlignment(Qt.AlignCenter)
            self.evaltype_layout.addWidget(no_eval_label)

        # Update force status usage
        self._clear_layout(self.force_status_layout)

        force_usage = m.get("force_status_usage", {})
        if force_usage:
            total_force = sum(force_usage.values())

            for status, count in force_usage.items():
                percentage = (count / total_force) * 100 if total_force > 0 else 0

                status_frame = QFrame()
                status_layout = QHBoxLayout()

                # Choose appropriate icon and color
                if status == "AUTO":
                    icon, color = "🤖", "#3498db"
                elif status == "GOOD":
                    icon, color = "✅", "#27ae60"
                elif status == "BAD":
                    icon, color = "❌", "#e74c3c"
                else:
                    icon, color = "❓", "#95a5a6"

                label = QLabel(f"{icon} <b>{status}:</b> {count} ({percentage:.1f}%)")
                label.setFont(QFont("Segoe UI", 9))
                label.setStyleSheet(f"color: {color};")

                progress = QProgressBar()
                progress.setMaximum(100)
                progress.setValue(int(percentage))
                progress.setStyleSheet(f"""
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 3px;
                    }}
                """)

                status_layout.addWidget(label, 1)
                status_layout.addWidget(progress, 2)
                status_frame.setLayout(status_layout)
                self.force_status_layout.addWidget(status_frame)
        else:
            no_force_label = QLabel("🔄 No force status data available.")
            no_force_label.setAlignment(Qt.AlignCenter)
            self.force_status_layout.addWidget(no_force_label)

        # NEW: Update comparison data
        self._clear_layout(self.comparison_layout)

        comparison_frame = QFrame()
        comparison_layout = QVBoxLayout()

        # Summary stats
        summary_label = QLabel(f"""
        📈 <b>Change Summary:</b><br>
        • Modified: {len(self.comparison_data.get("modifications", []))} dimensions<br>
        • Added: {len(self.comparison_data.get("additions", []))} dimensions<br>
        • Deleted: {len(self.comparison_data.get("deletions", []))} dimensions
        """)
        summary_label.setFont(QFont("Segoe UI", 9))
        summary_label.setWordWrap(True)
        comparison_layout.addWidget(summary_label)

        # Show recent modifications
        if self.comparison_data.get("modifications"):
            modifications_label = QLabel("<b>Recent Modifications:</b>")
            modifications_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            comparison_layout.addWidget(modifications_label)

            for mod in self.comparison_data["modifications"][-5:]:  # Show last 5
                mod_text = f"• {mod['element_id']}: {'; '.join(mod['changes'][:3])}..."
                if len(mod["changes"]) > 3:
                    mod_text += f" (+{len(mod['changes']) - 3} more)"

                mod_label = QLabel(mod_text)
                mod_label.setFont(QFont("Consolas", 8))
                mod_label.setWordWrap(True)
                comparison_layout.addWidget(mod_label)

        comparison_frame.setLayout(comparison_layout)
        self.comparison_layout.addWidget(comparison_frame)

    def _generate_recommendations(self) -> List[str]:
        """Generate intelligent quality recommendations"""
        m = self.metrics
        recommendations = []

        # Success rate recommendations
        if m["success_rate"] < 95 and m["success_rate"] >= 80:
            recommendations.append(
                "⚠️ Success rate below 95% - Review failed dimensions and consider process improvements."
            )
        elif m["success_rate"] < 80:
            recommendations.append(
                "🚨 CRITICAL: Success rate below 80% - Immediate process review and corrective actions required."
            )

        # Completeness recommendations
        if m["completeness"] < 90:
            recommendations.append(
                "📊 Incomplete measurement data detected - Consider adding more measurement points for better statistical analysis."
            )
        elif m["completeness"] < 70:
            recommendations.append(
                "🚨 LOW DATA COMPLETENESS: Less than 70% measurement coverage - Data quality may be compromised."
            )

        # Failed dimensions recommendations
        if m["failed"]:
            recommendations.append(
                f"❌ {m['failed']} dimensions failed - Prioritize investigation of root causes for failed measurements."
            )

        # Cavity-specific recommendations
        cavity_issues = []
        for cavity, stats in m.get("cavity_breakdown", {}).items():
            if stats["total"] > 0:
                success_rate = (stats["passed"] / stats["total"]) * 100
                if success_rate < 80:
                    cavity_issues.append(f"Cavity {cavity} ({success_rate:.1f}%)")

        if cavity_issues:
            recommendations.append(
                f"🏭 Poor performance in cavities: {', '.join(cavity_issues)} - Check tooling and process parameters."
            )

        # Measurement recommendations
        meas_stats = m.get("measurement_stats", {})
        if meas_stats.get("avg_measurements_per_dimension", 0) < 3:
            recommendations.append(
                "📏 Low measurement count per dimension - Consider increasing sample size for better statistical confidence."
            )

        # Tolerance recommendations
        tol_stats = m.get("tolerance_analysis", {})
        if tol_stats.get("without_tolerances", 0) > 0:
            recommendations.append(
                f"📐 {tol_stats['without_tolerances']} dimensions without tolerances - Review specification requirements."
            )

        # Warning dimensions
        if m["warning"]:
            recommendations.append(
                f"⚠️ {m['warning']} dimensions with warnings - Review warning conditions and consider corrective actions."
            )

        # Default positive feedback
        if not recommendations:
            recommendations.append(
                "✅ Excellent! All quality metrics are within acceptable ranges. Continue maintaining current standards."
            )

        return recommendations

    # def _periodic_refresh(self):
    #    """Periodic refresh for real-time updates"""
    #    try:
    #        # Only refresh if we have a parent window and data
    #        if (hasattr(self, 'parent_window') and self.parent_window and
    #            hasattr(self.parent_window, 'table_manager')):
    #
    #            # Get current table data for completeness calculation
    #            try:
    #                df = self.parent_window.table_manager._get_dataframe_from_tables()
    #                if not df.empty:
    #                    self._update_with_table_data(df)
    #                    # Only update overview tab for performance
    #                    self._update_overview_tab_content()
    #            except Exception:
    #                pass  # Fail silently to avoid spam
    #
    #    except Exception as e:
    #        self._log_message(f"Periodic refresh error: {str(e)}", "DEBUG")

    def record_edit(self, description: str):
        """Record an edit action - IMPROVED"""
        try:
            self.metrics["edits_made"] += 1
            edit_record = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "description": description,
                "session_time": str(datetime.now() - self.session_start_time).split(
                    "."
                )[0],
            }
            self.metrics["edit_history"].append(edit_record)

            # Keep only last 50 edits for performance
            if len(self.metrics["edit_history"]) > 50:
                self.metrics["edit_history"] = self.metrics["edit_history"][-50:]

            # Update integrity tab if visible
            try:
                self._update_integrity_tab_content()
            except Exception:
                pass  # Fail silently if tab not ready

            self._log_message(f"✏️ Edit recorded: {description}", "DEBUG")

        except Exception as e:
            self._log_message(f"❌ Error recording edit: {str(e)}", "ERROR")

    def get_summary_data(self) -> dict:
        """Get complete summary data for export - NEW FUNCTION"""
        try:
            return {
                "session_info": {
                    "start_time": self.session_start_time.isoformat(),
                    "duration": str(datetime.now() - self.session_start_time).split(
                        "."
                    )[0],
                    "last_update": self._last_update.isoformat(),
                },
                "metrics": self.metrics.copy(),
                "original_data": self.original_data.copy(),
                "comparison_data": self.comparison_data.copy(),
                "export_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self._log_message(f"❌ Error getting summary data: {str(e)}", "ERROR")
            return {}

    def restore_summary_data(self, summary_data: dict):
        """Restore summary data from saved session - NEW FUNCTION"""
        try:
            if "session_info" in summary_data:
                session_info = summary_data["session_info"]
                if "start_time" in session_info:
                    self.session_start_time = datetime.fromisoformat(
                        session_info["start_time"]
                    )

            if "metrics" in summary_data:
                self.metrics.update(summary_data["metrics"])

            if "original_data" in summary_data:
                self.original_data = summary_data["original_data"]

            if "comparison_data" in summary_data:
                self.comparison_data = summary_data["comparison_data"]

            # Force refresh display
            self._update_all_tabs()

            self._log_message("📂 Summary data restored from session", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error restoring summary data: {str(e)}", "ERROR")

    def _clear_layout(self, layout):
        """Safely clear a layout"""
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            self._log_message(f"Error clearing layout: {str(e)}", "DEBUG")

    def reset_widget(self):
        """Reset the widget to initial state - IMPROVED"""
        try:
            self._reset_metrics()
            self._update_all_tabs()
            self._log_message("🔄 Summary widget reset successfully", "INFO")
        except Exception as e:
            self._log_message(f"Error resetting widget: {str(e)}", "ERROR")

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

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, "refresh_timer"):
                self.refresh_timer.stop()
            self._log_message("Summary widget cleanup completed", "DEBUG")
        except Exception as e:
            self._log_message(f"Error during cleanup: {str(e)}", "ERROR")

    def __del__(self):
        """Destructor"""
        try:
            self.cleanup()
        except Exception:
            pass  # Fail silently during destruction
