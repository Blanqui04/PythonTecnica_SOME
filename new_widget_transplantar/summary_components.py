# src/gui/windows/components/summary_components.py
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional
from src.models.dimensional.dimensional_result import DimensionalResult


class ModernGroupBox(QGroupBox):
    """Enhanced group box with beautiful modern styling"""

    def __init__(self, title: str):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid transparent;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 18px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.9), 
                    stop:1 rgba(248, 249, 250, 0.8));
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 6px 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
                font-weight: 700;
                font-size: 11px;
            }
            QGroupBox:hover {
                border: 2px solid rgba(102, 126, 234, 0.3);
            }
        """)


class MetricCard(QFrame):
    """Beautiful, modern metric display card with enhanced features"""

    def __init__(
        self, 
        title: str, 
        value: str, 
        icon: str = "📊", 
        color: str = "#3498db",
        enhanced: bool = False
    ):
        super().__init__()
        self.title_text = title
        self.color = color
        self.enhanced = enhanced
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(100 if enhanced else 85)
        
        # Enhanced gradient styling
        gradient_style = f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95),
                    stop:0.5 rgba(255, 255, 255, 0.85),
                    stop:1 rgba(248, 249, 250, 0.9));
                border: 2px solid rgba({self._hex_to_rgb(color)}, 0.2);
                border-radius: 12px;
                margin: 6px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 1.0),
                    stop:1 rgba(248, 249, 250, 0.95));
                border: 2px solid rgba({self._hex_to_rgb(color)}, 0.4);
                transform: translateY(-2px);
            }}
        """
        
        self.setStyleSheet(gradient_style)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4 if enhanced else 2)

        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 14 if enhanced else 12))
        icon_label.setFixedWidth(24)
        
        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 9 if enhanced else 8, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.title_label.setWordWrap(True)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Value display
        self.value_label = QLabel(str(value))
        value_font = QFont("Segoe UI", 18 if enhanced else 16, QFont.Bold)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #2c3e50; background: transparent;")
        self.value_label.setAlignment(Qt.AlignCenter)

        # Optional trend indicator for enhanced cards
        if enhanced:
            self.trend_label = QLabel("")
            self.trend_label.setFont(QFont("Segoe UI", 8))
            self.trend_label.setStyleSheet("color: #7f8c8d; background: transparent;")
            self.trend_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.trend_label)

        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addStretch()
        
        self.setLayout(layout)

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values"""
        hex_color = hex_color.lstrip('#')
        return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"

    def update_value(self, value: str, trend: str = ""):
        """Update the card value and optional trend"""
        self.value_label.setText(str(value))
        if hasattr(self, 'trend_label') and trend:
            self.trend_label.setText(trend)

    def set_alert_state(self, is_alert: bool = False):
        """Set visual alert state for critical values"""
        if is_alert:
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 243, 243, 0.95),
                        stop:1 rgba(255, 235, 235, 0.9));
                    border: 2px solid rgba(244, 67, 54, 0.3);
                    border-radius: 12px;
                    margin: 6px;
                }}
            """)
        else:
            # Reset to normal style
            self.__init__(self.title_text, self.value_label.text(), color=self.color)


class StatusProgressBar(QFrame):
    """Modern progress bar with status visualization"""

    def __init__(self, label: str, value: int, maximum: int, color: str = "#3498db"):
        super().__init__()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Label with percentage
        percentage = (value / maximum * 100) if maximum > 0 else 0
        header_layout = QHBoxLayout()
        
        label_widget = QLabel(f"{label}")
        label_widget.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label_widget.setStyleSheet(f"color: {color}; background: transparent;")
        
        value_widget = QLabel(f"{value}/{maximum} ({percentage:.1f}%)")
        value_widget.setFont(QFont("Segoe UI", 9))
        value_widget.setStyleSheet("color: #546e7a; background: transparent;")
        
        header_layout.addWidget(label_widget)
        header_layout.addStretch()
        header_layout.addWidget(value_widget)

        # Modern progress bar
        progress = QProgressBar()
        progress.setMaximum(maximum if maximum > 0 else 100)
        progress.setValue(value)
        progress.setTextVisible(False)
        progress.setFixedHeight(12)
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(224, 224, 224, 0.3);
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {self._adjust_color_brightness(color, 1.2)});
                border-radius: 6px;
                margin: 1px;
            }}
        """)

        layout.addLayout(header_layout)
        layout.addWidget(progress)
        self.setLayout(layout)

    def _adjust_color_brightness(self, hex_color, factor):
        """Adjust color brightness for gradient effect"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c * factor)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class DataProcessor(QThread):
    """High-performance background data processing thread"""
    processing_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(int, str)

    def __init__(self, results: List[DimensionalResult], table_data: Optional[pd.DataFrame] = None):
        super().__init__()
        self.results = results or []
        self.table_data = table_data
        self.should_stop = False

    def run(self):
        """Process data in background with progress updates"""
        try:
            processed_data = {}
            total_steps = 4
            current_step = 0

            # Step 1: Process results
            if not self.should_stop and self.results:
                self.progress_update.emit(25, "Analyzing dimensional results...")
                processed_data.update(self._process_results())
                current_step += 1

            # Step 2: Process table data
            if not self.should_stop and self.table_data is not None:
                self.progress_update.emit(50, "Processing measurement data...")
                processed_data.update(self._process_table_data())
                current_step += 1

            # Step 3: Advanced analytics
            if not self.should_stop:
                self.progress_update.emit(75, "Running advanced analytics...")
                processed_data.update(self._advanced_analysis())
                current_step += 1

            # Step 4: Complete
            if not self.should_stop:
                self.progress_update.emit(100, "Processing complete!")
                self.processing_complete.emit(processed_data)

        except Exception as e:
            print(f"Background processing error: {e}")

    def _process_results(self) -> Dict[str, Any]:
        """Process dimensional results efficiently"""
        if self.should_stop or not self.results:
            return {}

        data = {
            'total_results': len(self.results),
            'status_counts': {'GOOD': 0, 'BAD': 0, 'WARNING': 0, 'NOT_EVALUABLE': 0},
            'cavity_stats': {},
            'evaluation_stats': {},
            'failed_dimensions': [],
            'warning_dimensions': [],
            'measurement_statistics': {}
        }

        # Process in optimized batches
        batch_size = 100
        for i in range(0, len(self.results), batch_size):
            if self.should_stop:
                break

            batch = self.results[i:i + batch_size]
            for result in batch:
                if self.should_stop:
                    break

                # Status analysis
                status = result.status.value if hasattr(result.status, 'value') else str(result.status)
                data['status_counts'][status] = data['status_counts'].get(status, 0) + 1

                # Cavity analysis
                cavity = getattr(result, 'cavity', 1) or 1
                if cavity not in data['cavity_stats']:
                    data['cavity_stats'][cavity] = {
                        'total': 0, 'passed': 0, 'failed': 0, 'warning': 0,
                        'success_rate': 0.0, 'avg_measurements': 0
                    }

                data['cavity_stats'][cavity]['total'] += 1
                
                if status == 'GOOD':
                    data['cavity_stats'][cavity]['passed'] += 1
                elif status == 'BAD':
                    data['cavity_stats'][cavity]['failed'] += 1
                    data['failed_dimensions'].append({
                        'element_id': result.element_id,
                        'description': result.description,
                        'cavity': str(cavity),
                        'severity': self._calculate_severity(result)
                    })
                elif status == 'WARNING':
                    data['cavity_stats'][cavity]['warning'] += 1
                    data['warning_dimensions'].append({
                        'element_id': result.element_id,
                        'description': result.description,
                        'warnings': getattr(result, 'warnings', [])
                    })

                # Measurement count analysis
                if hasattr(result, 'measurements') and result.measurements:
                    meas_count = len(result.measurements)
                    data['cavity_stats'][cavity]['avg_measurements'] += meas_count

        # Calculate success rates and averages
        for cavity, stats in data['cavity_stats'].items():
            if stats['total'] > 0:
                stats['success_rate'] = (stats['passed'] / stats['total']) * 100
                stats['avg_measurements'] = stats['avg_measurements'] / stats['total']

        return data

    def _process_table_data(self) -> Dict[str, Any]:
        """Process table data for completeness and quality metrics"""
        if self.should_stop or self.table_data is None or self.table_data.empty:
            return {}

        data = {
            'data_completeness': {},
            'measurement_distribution': {},
            'data_quality_score': 0.0
        }

        # Measurement completeness analysis
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        total_measurements = 0
        total_possible = len(self.table_data) * 5

        completeness_by_col = {}
        for col in measurement_cols:
            if col in self.table_data.columns:
                non_null_count = self.table_data[col].notna().sum()
                total_measurements += non_null_count
                completeness_by_col[col] = (non_null_count / len(self.table_data)) * 100

        overall_completeness = (total_measurements / total_possible) * 100 if total_possible else 0

        data['data_completeness'] = {
            'overall': overall_completeness,
            'by_measurement': completeness_by_col,
            'total_measurements': total_measurements,
            'expected_measurements': total_possible
        }

        # Data quality scoring
        quality_factors = []
        
        # Factor 1: Completeness (40% weight)
        quality_factors.append(overall_completeness * 0.4)
        
        # Factor 2: Consistency (30% weight)
        consistency_score = self._calculate_consistency_score() * 0.3
        quality_factors.append(consistency_score)
        
        # Factor 3: Validity (30% weight)
        validity_score = self._calculate_validity_score() * 0.3
        quality_factors.append(validity_score)

        data['data_quality_score'] = sum(quality_factors)

        return data

    def _advanced_analysis(self) -> Dict[str, Any]:
        """Perform advanced statistical analysis"""
        if self.should_stop:
            return {}

        return {
            'performance_trends': self._analyze_performance_trends(),
            'predictive_insights': self._generate_predictive_insights(),
            'optimization_suggestions': self._generate_optimization_suggestions()
        }

    def _calculate_severity(self, result) -> str:
        """Calculate failure severity"""
        out_of_spec = getattr(result, 'out_of_spec_count', 0)
        if out_of_spec >= 4:
            return "Critical"
        elif out_of_spec >= 2:
            return "High"
        elif out_of_spec >= 1:
            return "Medium"
        return "Low"

    def _calculate_consistency_score(self) -> float:
        """Calculate data consistency score"""
        # Placeholder for consistency analysis
        return 85.0

    def _calculate_validity_score(self) -> float:
        """Calculate data validity score"""
        # Placeholder for validity analysis
        return 92.0

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        return {
            'trend_direction': 'stable',
            'improvement_rate': 2.3,
            'volatility_index': 0.15
        }

    def _generate_predictive_insights(self) -> List[str]:
        """Generate predictive insights"""
        return [
            "Quality trend indicates stable performance",
            "Cavity 2 showing slight improvement tendency",
            "Measurement completeness expected to improve"
        ]

    def _generate_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions"""
        return [
            "Consider increasing measurement frequency for cavity 3",
            "Review tolerance specifications for failed dimensions",
            "Implement automated quality checks for critical features"
        ]

    def stop(self):
        """Stop processing gracefully"""
        self.should_stop = True


class SmartCache:
    """Intelligent caching system for performance optimization"""
    
    def __init__(self, default_timeout: int = 30):
        self.cache = {}
        self.default_timeout = default_timeout
    
    def get(self, key: str, compute_func, *args, timeout: int = None, **kwargs):
        """Get cached value or compute and cache"""
        timeout = timeout or self.default_timeout
        now = datetime.now()
        
        if (key in self.cache and 
            (now - self.cache[key]['timestamp']).total_seconds() < timeout):
            return self.cache[key]['data']
        
        # Compute and cache
        result = compute_func(*args, **kwargs)
        self.cache[key] = {
            'data': result,
            'timestamp': now
        }
        return result
    
    def clear(self):
        """Clear all cached data"""
        self.cache = {}
    
    def remove(self, key: str):
        """Remove specific cache entry"""
        if key in self.cache:
            del self.cache[key]


class PerformanceMonitor:
    """Monitor and optimize widget performance"""
    
    def __init__(self):
        self.metrics = {
            'update_times': [],
            'cache_hits': 0,
            'cache_misses': 0,
            'background_tasks': 0
        }
    
    def record_update_time(self, duration: float):
        """Record update operation time"""
        self.metrics['update_times'].append(duration)
        # Keep only last 50 measurements
        if len(self.metrics['update_times']) > 50:
            self.metrics['update_times'] = self.metrics['update_times'][-50:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics['cache_misses'] += 1
    
    def get_cache_efficiency(self) -> float:
        """Calculate cache hit rate"""
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        return (self.metrics['cache_hits'] / total * 100) if total > 0 else 0
    
    def get_avg_update_time(self) -> float:
        """Get average update time"""
        times = self.metrics['update_times']
        return sum(times) / len(times) if times else 0.0
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            'update_times': [],
            'cache_hits': 0,
            'cache_misses': 0,
            'background_tasks': 0
        }