# src/gui/windows/components/dimensional_summary_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QGroupBox, QHBoxLayout,
    QTextEdit, QProgressBar, QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime
import pandas as pd
from typing import List, Optional, Dict, Any
from src.models.dimensional.dimensional_result import DimensionalResult
from .summary_components import MetricCard, ModernGroupBox, DataProcessor
from .summary_analysis import SummaryAnalyzer
import threading
import queue


class SummaryWidget(QWidget):
    """High-performance, beautiful dimensional summary widget"""
    update_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._reset_metrics()
        self._last_update = datetime.now()
        self._update_threshold = 0.8  # Balanced threshold
        
        # Performance optimization components
        self._update_pending = False
        self._processing_thread = None
        self._update_queue = queue.Queue()
        self._cache = {}
        self._cache_timeout = 25  # seconds
        
        # Analysis engine
        self.analyzer = SummaryAnalyzer()
        
        # Initialize UI with modern design
        self._init_ui()
        
        # Setup intelligent update timer
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._process_queued_updates)
        
        # Data tracking
        self.original_data = {}
        self.comparison_data = {
            "original_vs_final": {},
            "modifications": [],
            "additions": [],
            "deletions": [],
        }

    def _init_ui(self):
        """Initialize modern, responsive UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Create elegant tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self._get_tab_stylesheet())

        # Smart tab loading - only create content when accessed
        self.tab_widgets = {}
        self.tab_contents = {}
        
        tab_config = [
            ("📊 Dashboard", "dashboard", "🎯 Real-time dimensional analysis overview"),
            ("🔍 Quality", "quality", "📈 Comprehensive quality metrics and analysis"),
            ("📋 Data Health", "integrity", "🔧 Data completeness and modification tracking"),
            ("⚡ Performance", "performance", "📊 Session metrics and efficiency analysis"),
            ("🔬 Deep Dive", "detailed", "🎲 Advanced analytics and comparisons")
        ]
        
        for title, key, tooltip in tab_config:
            placeholder = self._create_loading_placeholder(tooltip)
            self.tabs.addTab(placeholder, title)
            self.tab_widgets[key] = None
            self.tab_contents[key] = None

        # Enhanced tab change handling
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Pre-load first tab for immediate display
        self._load_tab_content(0)

    def _get_tab_stylesheet(self):
        """Modern tab styling with enhanced visual appeal"""
        return """
            QTabWidget::pane {
                border: 2px solid #e3f2fd;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9ff);
                padding: 8px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f6fa, stop:1 #e8eaf6);
                color: #546e7a;
                border: 2px solid #e1e5e9;
                border-bottom: none;
                border-radius: 8px 8px 0px 0px;
                padding: 12px 20px;
                margin: 0px 2px;
                font-weight: 600;
                font-size: 11px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f7ff);
                color: #1976d2;
                border-color: #2196f3;
                border-bottom: 2px solid #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafbfc, stop:1 #f0f4f8);
                color: #37474f;
                border-color: #90caf9;
            }
        """

    def _create_loading_placeholder(self, description):
        """Create attractive loading placeholder"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Loading animation placeholder
        loading_frame = QFrame()
        loading_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e3f2fd, stop:1 #f3e5f5);
                border: 2px dashed #90caf9;
                border-radius: 12px;
                padding: 24px;
                margin: 20px;
            }
        """)
        loading_layout = QVBoxLayout()
        
        icon_label = QLabel("⏳")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        
        text_label = QLabel("Loading Advanced Analytics...")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        text_label.setStyleSheet("color: #1976d2; margin: 8px;")
        
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #546e7a; margin: 4px;")
        desc_label.setWordWrap(True)
        
        loading_layout.addWidget(icon_label)
        loading_layout.addWidget(text_label)
        loading_layout.addWidget(desc_label)
        loading_frame.setLayout(loading_layout)
        
        layout.addWidget(loading_frame)
        widget.setLayout(layout)
        return widget

    def _on_tab_changed(self, index):
        """Intelligent tab switching with lazy loading"""
        self._load_tab_content(index)

    def _load_tab_content(self, index):
        """Smart content loading with caching"""
        if index < 0 or index >= len(self.tab_widgets):
            return
            
        tab_keys = list(self.tab_widgets.keys())
        tab_key = tab_keys[index]
        
        # Use cached content if available and fresh
        if (self.tab_contents.get(tab_key) and 
            self._is_cache_fresh(f"tab_content_{tab_key}")):
            if self.tab_widgets[tab_key] is None:
                self._replace_tab_widget(index, tab_key, self.tab_contents[tab_key])
            return
        
        # Create new content
        if self.tab_widgets[tab_key] is None:
            content_widget = self._create_tab_content(tab_key)
            if content_widget:
                self.tab_contents[tab_key] = content_widget
                self._cache[f"tab_content_{tab_key}"] = {
                    'timestamp': datetime.now(),
                    'data': True
                }
                self._replace_tab_widget(index, tab_key, content_widget)

    def _replace_tab_widget(self, index, tab_key, widget):
        """Replace placeholder with actual content"""
        tab_titles = [
            "📊 Dashboard", "🔍 Quality", "📋 Data Health", 
            "⚡ Performance", "🔬 Deep Dive"
        ]
        
        # Remove placeholder and insert new widget
        old_widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, widget, tab_titles[index])
        self.tabs.setCurrentIndex(index)
        self.tab_widgets[tab_key] = widget
        
        # Clean up old widget
        if old_widget:
            old_widget.deleteLater()

    def _create_tab_content(self, tab_key):
        """Factory method for creating tab content"""
        creators = {
            "dashboard": self._create_dashboard_tab,
            "quality": self._create_quality_tab,
            "integrity": self._create_integrity_tab,
            "performance": self._create_performance_tab,
            "detailed": self._create_detailed_tab
        }
        
        creator = creators.get(tab_key)
        if creator:
            return creator()
        return None

    def _create_dashboard_tab(self):
        """Create beautiful, information-rich dashboard"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Session header with elegant design
        session_frame = QFrame()
        session_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 12px;
                color: white;
                padding: 16px;
                margin: 4px;
            }
        """)
        session_layout = QHBoxLayout()
        session_layout.setContentsMargins(16, 12, 16, 12)

        # Dynamic session info
        self.session_info_label = QLabel()
        self.session_info_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.session_info_label.setStyleSheet("color: white; background: transparent;")
        
        session_layout.addWidget(self.session_info_label)
        session_layout.addStretch()
        
        # Add status indicator
        self.status_indicator = QLabel("🟢 Active")
        self.status_indicator.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.status_indicator.setStyleSheet("color: #4caf50; background: transparent;")
        session_layout.addWidget(self.status_indicator)
        
        session_frame.setLayout(session_layout)
        layout.addWidget(session_frame)

        # Enhanced metrics grid with modern cards
        metrics_container = QFrame()
        metrics_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 12px;
                margin: 4px;
            }
        """)
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(12)
        self.metrics_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create enhanced metric cards
        self.metric_cards = {}
        self._create_dashboard_cards()
        
        metrics_container.setLayout(self.metrics_layout)
        layout.addWidget(metrics_container)

        # Status breakdown with modern visualization
        self.status_group = ModernGroupBox("📊 Status Distribution")
        self.status_layout = QVBoxLayout()
        self.status_group.setLayout(self.status_layout)
        layout.addWidget(self.status_group)

        # Cavity performance comparison
        self.cavity_group = ModernGroupBox("🏭 Cavity Performance Analysis")
        self.cavity_layout = QVBoxLayout()
        self.cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(self.cavity_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_dashboard_cards(self):
        """Create beautiful metric cards for dashboard"""
        cards_config = [
            ("Total Dimensions", "total_dimensions", "📏", "#1976d2", "0"),
            ("Success Rate", "success_rate", "📊", "#388e3c", "0%"),
            ("Studies Run", "studies_run", "🔬", "#7b1fa2", "0"),
            ("Data Completeness", "completeness", "📈", "#f57c00", "0%"),
            ("Passed Tests", "passed", "✅", "#4caf50", "0"),
            ("Failed Tests", "failed", "❌", "#f44336", "0"),
            ("Warnings", "warning", "⚠️", "#ff9800", "0"),
            ("Total Edits", "edits_made", "✏️", "#607d8b", "0"),
        ]

        for i, (title, key, icon, color, default_value) in enumerate(cards_config):
            card = MetricCard(title, default_value, icon, color, enhanced=True)
            self.metric_cards[key] = card
            row, col = divmod(i, 4)
            self.metrics_layout.addWidget(card, row, col)

    # Continue with other tab creation methods...
    def _create_quality_tab(self):
        """Create comprehensive quality analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Quality overview with KPIs
        quality_header = ModernGroupBox("🎯 Quality Overview")
        self.quality_summary_layout = QVBoxLayout()
        quality_header.setLayout(self.quality_summary_layout)
        layout.addWidget(quality_header)

        # Failed dimensions table with enhanced styling
        failed_group = ModernGroupBox("❌ Critical Issues")
        failed_layout = QVBoxLayout()
        
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(5)
        self.failed_table.setHorizontalHeaderLabels([
            "Element ID", "Description", "Cavity", "Out of Spec", "Priority"
        ])
        self.failed_table.setAlternatingRowColors(True)
        self.failed_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #495057;
                padding: 10px;
                border: none;
                font-weight: 600;
            }
        """)
        self.failed_table.setMaximumHeight(300)
        
        failed_layout.addWidget(self.failed_table)
        failed_group.setLayout(failed_layout)
        layout.addWidget(failed_group)

        # Quality recommendations
        rec_group = ModernGroupBox("💡 Intelligent Recommendations")
        self.recommendations_layout = QVBoxLayout()
        rec_group.setLayout(self.recommendations_layout)
        layout.addWidget(rec_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_integrity_tab(self):
        """Create data integrity monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Data health indicators
        health_group = ModernGroupBox("💊 Data Health Indicators")
        self.health_layout = QGridLayout()
        health_group.setLayout(self.health_layout)
        layout.addWidget(health_group)

        # Measurement completeness visualization
        completeness_group = ModernGroupBox("📊 Measurement Completeness")
        self.completeness_layout = QVBoxLayout()
        completeness_group.setLayout(self.completeness_layout)
        layout.addWidget(completeness_group)

        # Change tracking
        changes_group = ModernGroupBox("📝 Recent Changes")
        changes_layout = QVBoxLayout()
        
        self.changes_display = QTextEdit()
        self.changes_display.setMaximumHeight(200)
        self.changes_display.setReadOnly(True)
        self.changes_display.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                line-height: 1.4;
            }
        """)
        
        changes_layout.addWidget(self.changes_display)
        changes_group.setLayout(changes_layout)
        layout.addWidget(changes_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_performance_tab(self):
        """Create performance monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Session performance metrics
        perf_group = ModernGroupBox("⚡ Session Performance")
        self.performance_layout = QGridLayout()
        perf_group.setLayout(self.performance_layout)
        layout.addWidget(perf_group)

        # Study history with trend visualization
        history_group = ModernGroupBox("📈 Study History & Trends")
        self.history_layout = QVBoxLayout()
        history_group.setLayout(self.history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_detailed_tab(self):
        """Create detailed analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Evaluation type analysis
        eval_group = ModernGroupBox("🔧 Evaluation Type Breakdown")
        self.eval_layout = QVBoxLayout()
        eval_group.setLayout(self.eval_layout)
        layout.addWidget(eval_group)

        # Data comparison
        comparison_group = ModernGroupBox("📊 Data Comparison Analysis")
        self.comparison_layout = QVBoxLayout()
        comparison_group.setLayout(self.comparison_layout)
        layout.addWidget(comparison_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # Continue in next part due to length...
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
            "failed_dimensions": [],
            "warning_dimensions": [],
            "measurement_stats": {},
            "tolerance_analysis": {},
            "force_status_usage": {},
            "edit_history": [],
            "study_history": [],
        }
        self.session_start_time = datetime.now()
        self._clear_cache()

    def _clear_cache(self):
        """Clear performance cache"""
        self._cache = {}

    def _is_cache_fresh(self, cache_key):
        """Check if cache entry is still fresh"""
        if cache_key not in self._cache:
            return False
        
        age = (datetime.now() - self._cache[cache_key]['timestamp']).total_seconds()
        return age < self._cache_timeout

    def _log_message(self, message: str, level: str = "INFO"):
        """Safe logging with null checks"""
        try:
            if (hasattr(self, "parent_window") and self.parent_window and 
                hasattr(self.parent_window, "_log_message")):
                self.parent_window._log_message(message, level)
            else:
                print(f"[{level}] {message}")
        except Exception:
            print(f"[{level}] {message}")

    def update_summary(self,
                      results: Optional[List[DimensionalResult]] = None,
                      table_data: Optional[pd.DataFrame] = None,
                      force_refresh: bool = False,
                      store_original: bool = False):
        """Intelligent summary update with performance optimization"""
        try:
            now = datetime.now()
            
            # Handle None results gracefully
            if results is None:
                results = []

            # Smart throttling - allow force refresh or significant changes
            if (not force_refresh and 
                (now - self._last_update).total_seconds() < self._update_threshold):
                self._queue_update(results, table_data, store_original)
                return
                
            self._last_update = now

            # Store original data for comparison
            if store_original and table_data is not None:
                self.store_original_data(table_data)

            # Use background processing for heavy operations
            if results or (table_data is not None and not table_data.empty):
                self._start_background_processing(results, table_data)
            else:
                # Light update for UI refresh only
                self._update_visible_tab_only()

            self._log_message(f"📊 Processing {len(results)} results...", "DEBUG")

        except Exception as e:
            self._log_message(f"Error updating summary: {str(e)}", "ERROR")

    def _queue_update(self, results, table_data, store_original):
        """Intelligent update queuing"""
        try:
            # Clear old queued updates
            while not self._update_queue.empty():
                try:
                    self._update_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Queue new update
            self._update_queue.put({
                'results': results,
                'table_data': table_data,
                'store_original': store_original,
                'timestamp': datetime.now()
            })
            
            # Start delayed processing timer
            self._update_timer.start(600)  # 600ms delay for batching
            
        except Exception as e:
            self._log_message(f"Error queuing update: {str(e)}", "ERROR")

    def _process_queued_updates(self):
        """Process queued updates intelligently"""
        try:
            if self._update_queue.empty():
                return
            
            # Get most recent update only
            latest_update = None
            while not self._update_queue.empty():
                try:
                    latest_update = self._update_queue.get_nowait()
                except queue.Empty:
                    break
            
            if latest_update:
                self.update_summary(
                    results=latest_update['results'],
                    table_data=latest_update['table_data'], 
                    store_original=latest_update['store_original'],
                    force_refresh=True
                )
                
        except Exception as e:
            self._log_message(f"Error processing queued updates: {str(e)}", "ERROR")

    def _start_background_processing(self, results, table_data):
        """Start intelligent background processing"""
        try:
            # Stop existing processing
            if self._processing_thread and self._processing_thread.isRunning():
                self._processing_thread.stop()
                self._processing_thread.wait(1000)
            
            # Start new processing thread
            self._processing_thread = DataProcessor(results, table_data)
            self._processing_thread.processing_complete.connect(self._on_processing_complete)
            self._processing_thread.start()
            
        except Exception as e:
            self._log_message(f"Error starting background processing: {str(e)}", "ERROR")

    @pyqtSlot(dict)
    def _on_processing_complete(self, processed_data):
        """Handle completion of background processing"""
        try:
            # Update metrics with processed data
            self._update_metrics_from_processed_data(processed_data)
            
            # Update only visible tab for performance
            self._update_visible_tab_only()
            
            # Clear cache since data changed
            self._clear_cache()
            
            # Emit completion signal
            self.update_complete.emit()
            
        except Exception as e:
            self._log_message(f"Error handling background processing: {str(e)}", "ERROR")

    def _update_metrics_from_processed_data(self, data):
        """Update internal metrics from processed data"""
        if 'status_counts' in data:
            self.metrics.update({
                'passed': data['status_counts'].get('GOOD', 0),
                'failed': data['status_counts'].get('BAD', 0),
                'warning': data['status_counts'].get('WARNING', 0),
                'not_evaluable': data['status_counts'].get('NOT_EVALUABLE', 0),
            })
            
            total = sum(data['status_counts'].values())
            if total > 0:
                self.metrics['success_rate'] = (self.metrics['passed'] / total) * 100
                self.metrics['total_dimensions'] = total
                self.metrics['studies_run'] += 1

        # Update other metrics
        for key in ['cavity_stats', 'failed_dimensions', 'warning_dimensions']:
            if key in data:
                self.metrics[key.replace('_stats', '_breakdown')] = data[key]

        if 'data_completeness' in data:
            self.metrics['completeness'] = data['data_completeness'].get('overall', 0)

    def _update_visible_tab_only(self):
        """Update only the currently visible tab for optimal performance"""
        try:
            current_index = self.tabs.currentIndex()
            if current_index < 0:
                return
                
            tab_keys = list(self.tab_widgets.keys())
            if current_index >= len(tab_keys):
                return
                
            current_tab_key = tab_keys[current_index]
            
            # Update only if tab is loaded
            if self.tab_widgets[current_tab_key] is not None:
                update_methods = {
                    "dashboard": self._update_dashboard_content,
                    "quality": self._update_quality_content,
                    "integrity": self._update_integrity_content,
                    "performance": self._update_performance_content,
                    "detailed": self._update_detailed_content
                }
                
                update_method = update_methods.get(current_tab_key)
                if update_method:
                    update_method()
                    
        except Exception as e:
            self._log_message(f"Error updating visible tab: {str(e)}", "ERROR")

    def _update_dashboard_content(self):
        """Update dashboard tab with beautiful, comprehensive information"""
        try:
            m = self.metrics
            
            # Update session info with rich details
            session_duration = datetime.now() - self.session_start_time
            hours = int(session_duration.total_seconds() // 3600)
            minutes = int((session_duration.total_seconds() % 3600) // 60)
            
            session_text = (
                f"🕐 Active Session: {hours}h {minutes}m | "
                f"📊 Studies: {m['studies_run']} | "
                f"📅 Started: {self.session_start_time.strftime('%H:%M')}"
            )
            self.session_info_label.setText(session_text)

            # Update enhanced metric cards with trends
            card_updates = {
                'total_dimensions': (str(m['total_dimensions']), ""),
                'success_rate': (f"{m['success_rate']:.1f}%", self._get_trend_indicator('success_rate')),
                'studies_run': (str(m['studies_run']), ""),
                'completeness': (f"{m['completeness']:.1f}%", self._get_trend_indicator('completeness')),
                'passed': (str(m['passed']), "✓" if m['passed'] > 0 else ""),
                'failed': (str(m['failed']), "⚠" if m['failed'] > 0 else ""),
                'warning': (str(m['warning']), "!" if m['warning'] > 0 else ""),
                'edits_made': (str(m['edits_made']), "")
            }

            for key, (value, trend) in card_updates.items():
                if key in self.metric_cards:
                    self.metric_cards[key].update_value(value, trend)
                    
                    # Set alert state for critical values
                    if key == 'failed' and m['failed'] > 0:
                        self.metric_cards[key].set_alert_state(True)

            # Update status breakdown with beautiful progress bars
            self._update_status_breakdown()
            
            # Update cavity performance with detailed analysis
            self._update_cavity_performance()

        except Exception as e:
            self._log_message(f"Error updating dashboard: {str(e)}", "ERROR")

    def _update_status_breakdown(self):
        """Update status breakdown with modern visualization"""
        try:
            self._clear_layout(self.status_layout)
            m = self.metrics
            
            total = m['passed'] + m['failed'] + m['warning'] + m['not_evaluable']
            if total == 0:
                no_data_label = QLabel("📊 No analysis data available")
                no_data_label.setAlignment(Qt.AlignCenter)
                no_data_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
                self.status_layout.addWidget(no_data_label)
                return

            # Create beautiful progress bars for each status
            status_config = [
                ("Passed", m['passed'], "✅", "#4caf50"),
                ("Failed", m['failed'], "❌", "#f44336"), 
                ("Warnings", m['warning'], "⚠️", "#ff9800"),
                ("Not Evaluable", m['not_evaluable'], "ℹ️", "#9e9e9e")
            ]

            for status_name, count, icon, color in status_config:
                if count > 0:
                    progress_bar = StatusProgressBar(
                        f"{icon} {status_name}",
                        count,
                        total,
                        color
                    )
                    self.status_layout.addWidget(progress_bar)

        except Exception as e:
            self._log_message(f"Error updating status breakdown: {str(e)}", "ERROR")

    def _update_cavity_performance(self):
        """Update cavity performance with detailed insights"""
        try:
            self._clear_layout(self.cavity_layout)
            m = self.metrics
            
            cavity_breakdown = m.get('cavity_breakdown', {})
            if not cavity_breakdown:
                no_data_label = QLabel("🏭 No cavity data available")
                no_data_label.setAlignment(Qt.AlignCenter)
                no_data_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
                self.cavity_layout.addWidget(no_data_label)
                return

            # Create performance cards for each cavity
            for cavity, stats in cavity_breakdown.items():
                if stats.get('total', 0) > 0:
                    success_rate = (stats.get('passed', 0) / stats['total']) * 100
                    
                    # Performance card
                    cavity_frame = QFrame()
                    cavity_frame.setStyleSheet(f"""
                        QFrame {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(255, 255, 255, 0.9),
                                stop:1 rgba(248, 249, 250, 0.8));
                            border: 1px solid {"#4caf50" if success_rate >= 95 else "#f44336" if success_rate < 80 else "#ff9800"};
                            border-radius: 8px;
                            margin: 4px;
                            padding: 8px;
                        }}
                    """)
                    
                    cavity_layout = QHBoxLayout()
                    cavity_layout.setContentsMargins(12, 8, 12, 8)

                    # Cavity info
                    info_label = QLabel(
                        f"🏭 <b>Cavity {cavity}</b><br>"
                        f"<span style='font-size: 10px; color: #546e7a;'>"
                        f"{stats.get('passed', 0)}/{stats['total']} passed</span>"
                    )
                    info_label.setFont(QFont("Segoe UI", 9))

                    # Success rate with visual indicator
                    rate_color = "#4caf50" if success_rate >= 95 else "#f44336" if success_rate < 80 else "#ff9800"
                    rate_label = QLabel(f"<b style='color: {rate_color};'>{success_rate:.1f}%</b>")
                    rate_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
                    rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    cavity_layout.addWidget(info_label)
                    cavity_layout.addStretch()
                    cavity_layout.addWidget(rate_label)
                    cavity_frame.setLayout(cavity_layout)
                    self.cavity_layout.addWidget(cavity_frame)

        except Exception as e:
            self._log_message(f"Error updating cavity performance: {str(e)}", "ERROR")

    def _update_quality_content(self):
        """Update quality analysis with comprehensive insights"""
        try:
            # Use analyzer for intelligent quality insights
            quality_analysis = self.analyzer.analyze_quality_metrics(
                self._get_current_results()
            )
            
            self._update_quality_overview(quality_analysis)
            self._update_failed_dimensions_table()
            self._update_quality_recommendations(quality_analysis)

        except Exception as e:
            self._log_message(f"Error updating quality content: {str(e)}", "ERROR")

    def _update_integrity_content(self):
        """Update data integrity with health indicators"""
        try:
            # Analyze data integrity
            integrity_analysis = self.analyzer.analyze_data_integrity(
                self._get_current_table_data(),
                self.original_data
            )
            
            self._update_data_health_indicators(integrity_analysis)
            self._update_completeness_visualization(integrity_analysis)
            self._update_change_tracking()

        except Exception as e:
            self._log_message(f"Error updating integrity content: {str(e)}", "ERROR")

    def _update_performance_content(self):
        """Update performance metrics with efficiency insights"""
        try:
            session_data = self._get_session_data()
            performance_analysis = self.analyzer.analyze_performance_metrics(session_data)
            
            self._update_performance_indicators(performance_analysis)
            self._update_study_history_visualization()

        except Exception as e:
            self._log_message(f"Error updating performance content: {str(e)}", "ERROR")

    def _update_detailed_content(self):
        """Update detailed analysis with advanced insights"""
        try:
            self._update_evaluation_type_analysis()
            self._update_data_comparison_analysis()

        except Exception as e:
            self._log_message(f"Error updating detailed content: {str(e)}", "ERROR")

    # Helper methods for data retrieval and utilities
    def _get_trend_indicator(self, metric_key: str) -> str:
        """Get trend indicator for metric"""
        # Placeholder for trend analysis
        return ""

    def _get_current_results(self) -> List[DimensionalResult]:
        """Get current dimensional results"""
        return []  # Placeholder - would get from parent window

    def _get_current_table_data(self) -> pd.DataFrame:
        """Get current table data"""
        return pd.DataFrame()  # Placeholder - would get from parent window

    def _get_session_data(self) -> Dict[str, Any]:
        """Get current session data"""
        session_duration = datetime.now() - self.session_start_time
        return {
            'session_hours': session_duration.total_seconds() / 3600,
            'session_minutes': session_duration.total_seconds() / 60,
            'studies_run': self.metrics['studies_run'],
            'total_dimensions': self.metrics['total_dimensions'],
            'success_rate': self.metrics['success_rate'],
            'data_completeness': self.metrics['completeness'],
            'avg_study_time': 0.0,  # Would calculate from actual data
            'cache_hit_rate': 0.0,  # Would get from performance monitor
            'avg_update_time': 0.0  # Would get from performance monitor
        }

    def store_original_data(self, table_data: pd.DataFrame):
        """Store original data for comparison tracking"""
        if table_data is None or table_data.empty:
            return

        try:
            stored_count = 0
            for _, row in table_data.iterrows():
                element_id = row.get("element_id")
                if element_id and element_id not in self.original_data:
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
                    stored_count += 1

            if stored_count > 0:
                self._log_message(f"📋 Stored original data for {stored_count} new dimensions", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error storing original data: {str(e)}", "ERROR")

    def record_edit(self, description: str):
        """Record edit with intelligent tracking"""
        try:
            self.metrics["edits_made"] += 1
            edit_record = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "description": description,
                "session_time": str(datetime.now() - self.session_start_time).split(".")[0]
            }
            
            if 'edit_history' not in self.metrics:
                self.metrics['edit_history'] = []
                
            self.metrics["edit_history"].append(edit_record)
            
            # Keep only last 30 edits for performance
            if len(self.metrics["edit_history"]) > 30:
                self.metrics["edit_history"] = self.metrics["edit_history"][-30:]

            # Update integrity tab if visible
            current_index = self.tabs.currentIndex()
            if current_index == 2:  # Integrity tab
                self._update_integrity_content()

        except Exception as e:
            self._log_message(f"❌ Error recording edit: {str(e)}", "ERROR")

    def _clear_layout(self, layout):
        """Safely clear layout contents"""
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            self._log_message(f"Error clearing layout: {str(e)}", "DEBUG")

    def reset_widget(self):
        """Reset widget with cleanup"""
        try:
            # Stop background processing
            if self._processing_thread and self._processing_thread.isRunning():
                self._processing_thread.stop()
                self._processing_thread.wait(1000)

            # Reset all data
            self._reset_metrics()
            
            # Clear update queue
            while not self._update_queue.empty():
                try:
                    self._update_queue.get_nowait()
                except queue.Empty:
                    break

            # Update visible tab
            self._update_visible_tab_only()
            self._log_message("🔄 Summary widget reset successfully", "INFO")
            
        except Exception as e:
            self._log_message(f"Error resetting widget: {str(e)}", "ERROR")

    def cleanup(self):
        """Comprehensive cleanup"""
        try:
            # Stop all background processes
            if self._processing_thread and self._processing_thread.isRunning():
                self._processing_thread.stop()
                self._processing_thread.wait(2000)

            # Stop timers
            if hasattr(self, '_update_timer'):
                self._update_timer.stop()

            # Clear caches and queues
            self._clear_cache()
            while not self._update_queue.empty():
                try:
                    self._update_queue.get_nowait()
                except queue.Empty:
                    break

            self._log_message("Summary widget cleanup completed", "DEBUG")
            
        except Exception as e:
            self._log_message(f"Error during cleanup: {str(e)}", "ERROR")

    def __del__(self):
        """Destructor with safe cleanup"""
        try:
            self.cleanup()
        except Exception:
            pass  # Fail silently during destruction
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
            "failed_dimensions": [],
            "warning_dimensions": [],
            "measurement_stats": {},
            "tolerance_analysis": {},
            "force_status_usage": {},
            "edit_history": [],
            "study_history": [],
        }
        self.session_start_time = datetime.now()
        self._clear_cache()

    def _clear_cache(self):
        """Clear performance cache"""
        self._cache = {}

    def _is_cache_fresh(self, cache_key):
        """Check if cache entry is still fresh"""
        if cache_key not in self._cache:
            return False
        
        age = (datetime.now() - self._cache[cache_key]['timestamp']).total_seconds()
        return age < self._cache_timeout

    def _log_message(self, message: str, level: str = "INFO"):
        """Safe logging with null checks"""
        try:
            if (hasattr(self, "parent_window") and self.parent_window and 
                hasattr(self.parent_window, "_log_message")):
                self.parent_window._log_message(message, level)
            else:
                print(f"[{level}] {message}")
        except Exception:
            print(f"[{level}] {message}")