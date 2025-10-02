# src/gui/widgets/element_metrics_widget.py - FIXED COMPACT VERSION
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
import math
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class ElementMetricsWidget(QFrame):
    """Compact widget to display and edit metrics for a single element"""
    metricsChanged = pyqtSignal(str, dict)
    removeRequested = pyqtSignal(object)
    valuesChanged = pyqtSignal(str, list)
    
    def __init__(self, element_data, parent=None):
        super().__init__(parent)
        self.element_data = element_data.copy()
        self.element_id = element_data['element_id']
        self.sigma = element_data.get('sigma', '6σ')  # Get sigma from element data
        self.metrics = {}
        self.has_extrapolation = element_data.get('has_extrapolation', False)
        self.extrapolated_values = element_data.get('extrapolated_values', [])
        self.original_values = element_data.get('original_values', element_data['values'].copy())
        
        if 'original_values' not in element_data:
            self.element_data['original_values'] = element_data['values'].copy()
            self.original_values = element_data['values'].copy()
        
        self.setup_ui()
        self.calculate_and_display_metrics()
    
    def setup_ui(self):
        """Setup compact UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
            QFrame:hover {
                border-color: #3498db;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header - more compact
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        header = QLabel(f"{self.element_id}")
        header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; background: transparent; border: none;")
        header_layout.addWidget(header)
        
        info = QLabel(f"Cav:{self.element_data.get('cavity', 'N/A')} | {self.element_data.get('class', 'N/A')} | {self.sigma}")
        info.setFont(QFont("Segoe UI", 7))
        info.setStyleSheet("color: #6c757d; background: transparent; border: none;")
        header_layout.addWidget(info)
        
        if self.has_extrapolation:
            extrap_label = QLabel("🔬")
            extrap_label.setFont(QFont("Segoe UI", 8))
            extrap_label.setStyleSheet("color: #17a2b8; background: transparent; border: none;")
            extrap_label.setToolTip("Extrapolated")
            header_layout.addWidget(extrap_label)
        
        header_layout.addStretch()
        
        # Action buttons - inline
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit Values & Metrics")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        edit_btn.clicked.connect(self._edit_element)
        header_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("🗑️")
        remove_btn.setToolTip("Remove")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        remove_btn.clicked.connect(self._request_remove)
        header_layout.addWidget(remove_btn)
        
        layout.addLayout(header_layout)
        
        # Compact metrics in single grid
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(3)
        self.metrics_layout.setVerticalSpacing(2)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.metrics_layout)
        
        self.setLayout(layout)
        self.setFixedHeight(85)  # Compact fixed height
    
    def calculate_and_display_metrics(self):
        """Calculate metrics and update display"""
        self.metrics = self._calculate_all_metrics()
        self._display_metrics()
    
    def _calculate_all_metrics(self):
        """Calculate metrics from CURRENT values (including extrapolated)"""
        # Use self.element_data['values'] which includes extrapolated if present
        values = self.element_data['values']
        n = len(values)

        logger.debug(f"Calculating metrics from {n} values (has_extrap={self.has_extrapolation})")

        if n == 0:
            return self._get_empty_metrics()
        
        # Calculate from ALL current values
        average = sum(values) / n
        variance = sum((x - average) ** 2 for x in values) / (n - 1) if n > 1 else 0
        sigma_long = math.sqrt(variance)
        
        if n > 1:
            moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, n)]
            avg_mr = sum(moving_ranges) / len(moving_ranges) if moving_ranges else 0
            sigma_short = avg_mr / 1.128
        else:
            sigma_short = 0
        
        # Calculate capability indices
        nominal = self.element_data['nominal']
        tol_minus = abs(self.element_data['tol_minus'])
        tol_plus = abs(self.element_data['tol_plus'])
        USL = nominal + tol_plus
        LSL = nominal - tol_minus
        tolerance = USL - LSL
        
        # Short-term
        if sigma_short > 0:
            cp = tolerance / (6 * sigma_short)
            cpu = (USL - average) / (3 * sigma_short)
            cpl = (average - LSL) / (3 * sigma_short)
            cpk = min(cpu, cpl)
            z_usl_short = (USL - average) / sigma_short
            z_lsl_short = (average - LSL) / sigma_short
            ppm_short = (stats.norm.cdf(-z_lsl_short) + (1 - stats.norm.cdf(z_usl_short))) * 1e6
        else:
            cp = cpk = ppm_short = 0
        
        # Long-term
        if sigma_long > 0:
            pp = tolerance / (6 * sigma_long)
            ppu = (USL - average) / (3 * sigma_long)
            ppl = (average - LSL) / (3 * sigma_long)
            ppk = min(ppu, ppl)
            z_usl_long = (USL - average) / sigma_long
            z_lsl_long = (average - LSL) / sigma_long
            ppm_long = (stats.norm.cdf(-z_lsl_long) + (1 - stats.norm.cdf(z_usl_long))) * 1e6
        else:
            pp = ppk = ppm_long = 0
        
        return {
            'average': average,
            'sigma_short': sigma_short,
            'sigma_long': sigma_long,
            'cp': cp,
            'cpk': cpk,
            'pp': pp,
            'ppk': ppk,
            'ppm_short': ppm_short,
            'ppm_long': ppm_long,
            'sample_size': n
        }
    
    def _get_empty_metrics(self):
        return {
            'average': 0, 'sigma_short': 0, 'sigma_long': 0,
            'cp': 0, 'cpk': 0, 'pp': 0, 'ppk': 0,
            'ppm_short': 0, 'ppm_long': 0, 'sample_size': 0
        }
    
    def _display_metrics(self):
        """Display metrics in compact format"""
        self._clear_layout(self.metrics_layout)
        
        # All metrics in 2 rows
        all_metrics = [
            ('Avg', self.metrics['average'], False, False),
            ('σs', self.metrics['sigma_short'], False, False),
            ('Cp', self.metrics['cp'], True, False),
            ('Cpk', self.metrics['cpk'], True, False),
            ('n', self.metrics['sample_size'], False, False),
            ('σl', self.metrics['sigma_long'], False, False),
            ('Pp', self.metrics['pp'], True, True),
            ('Ppk', self.metrics['ppk'], True, True),
            ('PPM', f"{int(self.metrics['ppm_short']):,}", False, False),
        ]
        
        for i, (label, value, color_code, is_long_term) in enumerate(all_metrics):
            row = i // 5
            col = (i % 5) * 2
            
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #495057; font-size: 7pt; background: transparent; border: none;")
            lbl.setFixedWidth(25)
            self.metrics_layout.addWidget(lbl, row, col)
            
            if isinstance(value, str):
                value_text = value
                color = "#495057"
            else:
                value_text = f"{value:.2f}" if abs(value) >= 0.01 else f"{value:.3f}"
                color = self._get_metric_color(label, value, is_long_term) if color_code else "#495057"
            
            value_lbl = QLabel(value_text)
            value_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 7pt; background: transparent; border: none;")
            value_lbl.setFixedWidth(35)
            self.metrics_layout.addWidget(value_lbl, row, col + 1)
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _get_metric_color(self, metric_type, value, is_long_term=False):
        """Get color based on metric value and sigma setting - FIXED"""
        if any(x in metric_type.lower() for x in ['cp', 'pp']):
            # Determine thresholds based on sigma
            if self.sigma == '6σ':
                excellent = 2.0
                good = 1.67
                acceptable = 1.33
            else:  # 5σ
                excellent = 1.67
                good = 1.33
                acceptable = 1.0
            
            if value >= excellent:
                return "#28a745"  # Green
            elif value >= good:
                return "#17a2b8"  # Cyan
            elif value >= acceptable:
                return "#ffc107"  # Yellow
            else:
                return "#dc3545"  # Red
        return "#495057"
    
    def _edit_element(self):
        """Edit element - NO MORE BUGS"""
        from .element_edit_dialog import EnhancedElementEditDialog
        
        dialog = EnhancedElementEditDialog(
            element_id=self.element_id,
            element_data=self.element_data.copy(),  # Pass copy
            metrics=self.metrics.copy(),
            parent=self
        )
        
        if dialog.exec_():
            updated = dialog.get_updated_data()
            
            logger.info(f"=== WIDGET RECEIVED UPDATE: {self.element_id} ===")
            logger.info(f"  values: {len(updated['values'])}")
            logger.info(f"  original: {len(updated['original_values'])}")
            logger.info(f"  extrapolated: {len(updated['extrapolated_values'])}")
            logger.info(f"  has_extrapolation: {updated['has_extrapolation']}")
            
            # Update EVERYTHING
            self.element_data['values'] = updated['values']
            self.element_data['original_values'] = updated['original_values']
            self.element_data['extrapolated_values'] = updated['extrapolated_values']
            self.element_data['has_extrapolation'] = updated['has_extrapolation']
            
            self.original_values = updated['original_values']
            self.extrapolated_values = updated['extrapolated_values']
            self.has_extrapolation = updated['has_extrapolation']
            
            # Metrics
            if updated.get('custom_metrics'):
                self.element_data['metrics'] = updated['custom_metrics']
                self.metrics.update(updated['custom_metrics'])
                self._recalculate_capability_with_custom_metrics(updated['custom_metrics'])
            else:
                if 'metrics' in self.element_data:
                    del self.element_data['metrics']
                self.metrics = self._calculate_all_metrics()
            
            self._display_metrics()
            self.metricsChanged.emit(self.element_id, self.metrics)
            self.valuesChanged.emit(self.element_id, updated['values'])
            
            logger.info(f"✓✓✓ SAVED: extrap={self.has_extrapolation}, values={len(updated['values'])}")

    
    def _recalculate_capability_with_custom_metrics(self, custom_metrics):
        """Recalculate capability indices using custom metrics"""
        average = custom_metrics['average']
        sigma_short = custom_metrics['sigma_short']
        sigma_long = custom_metrics['sigma_long']
        
        nominal = self.element_data['nominal']
        tol_minus = abs(self.element_data['tol_minus'])
        tol_plus = abs(self.element_data['tol_plus'])
        USL = nominal + tol_plus
        LSL = nominal - tol_minus
        tolerance = USL - LSL
        
        # Short-term
        if sigma_short > 0:
            cp = tolerance / (6 * sigma_short)
            cpu = (USL - average) / (3 * sigma_short)
            cpl = (average - LSL) / (3 * sigma_short)
            cpk = min(cpu, cpl)
            
            z_usl = (USL - average) / sigma_short
            z_lsl = (average - LSL) / sigma_short
            ppm_short = (stats.norm.cdf(-z_lsl) + (1 - stats.norm.cdf(z_usl))) * 1e6
        else:
            cp = cpk = ppm_short = 0
        
        # Long-term
        if sigma_long > 0:
            pp = tolerance / (6 * sigma_long)
            ppu = (USL - average) / (3 * sigma_long)
            ppl = (average - LSL) / (3 * sigma_long)
            ppk = min(ppu, ppl)
            
            z_usl_long = (USL - average) / sigma_long
            z_lsl_long = (average - LSL) / sigma_long
            ppm_long = (stats.norm.cdf(-z_lsl_long) + (1 - stats.norm.cdf(z_usl_long))) * 1e6
        else:
            pp = ppk = ppm_long = 0
        
        # Update metrics
        self.metrics.update({
            'cp': cp,
            'cpk': cpk,
            'pp': pp,
            'ppk': ppk,
            'ppm_short': ppm_short,
            'ppm_long': ppm_long
        })
    
    def _request_remove(self):
        reply = QMessageBox.question(
            self, 'Remove Element',
            f'Remove element {self.element_id}?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.removeRequested.emit(self)
    
    def get_element_data(self):
        """Get complete element data - ENSURE ALL FIELDS"""
        return {
            'element_id': self.element_id,
            'cavity': self.element_data.get('cavity', ''),
            'class': self.element_data.get('class', ''),
            'sigma': self.sigma,
            'instrument': self.element_data.get('instrument', '3D Scanner'),  # NEW
            'nominal': self.element_data['nominal'],
            'tol_minus': self.element_data['tol_minus'],
            'tol_plus': self.element_data['tol_plus'],
            'values': self.element_data['values'],
            'original_values': self.original_values,
            'has_extrapolation': self.has_extrapolation,
            'extrapolated_values': self.extrapolated_values,
            'metrics': self.element_data.get('metrics'),  # Custom metrics if edited
        }