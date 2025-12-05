# src/gui/widgets/element_metrics_widget.py - IMPROVED READABLE CARD
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
import math
from scipy import stats
import logging

from src.gui.utils.responsive_utils import ResponsiveWidget

logger = logging.getLogger(__name__)


class ElementMetricsWidget(QFrame, ResponsiveWidget):
    """Improved readable widget to display element info"""
    metricsChanged = pyqtSignal(str, dict)
    removeRequested = pyqtSignal(object)
    valuesChanged = pyqtSignal(str, list)
    
    def __init__(self, element_data, parent=None):
        super().__init__(parent)
        ResponsiveWidget.__init__(self)
        self.element_data = element_data.copy()
        self.element_id = element_data['element_id']
        self.sigma = element_data.get('sigma', '6σ')
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
        """Setup improved readable UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin: 3px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # HEADER ROW - Prominent Element Info
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Element ID - Large and Bold
        element_label = QLabel(f"📋 {self.element_id}")
        element_label.setFont(QFont("Segoe UI", self.get_responsive_font_size(11), QFont.Bold))
        element_label.setStyleSheet("color: #2c3e50; background: transparent; border: none;")
        header_layout.addWidget(element_label)
        
        if self.has_extrapolation:
            extrap_badge = QLabel("🔬")
            extrap_badge.setFont(QFont("Segoe UI", self.get_responsive_font_size(10)))
            extrap_badge.setStyleSheet("color: #17a2b8; background: transparent; border: none;")
            extrap_badge.setToolTip(f"Extrapolated: {len(self.extrapolated_values)} values")
            header_layout.addWidget(extrap_badge)
        
        header_layout.addStretch()
        
        # Action buttons
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit Values & Metrics")
        edit_btn.setFixedSize(*self.screen_utils.scale_size(28, 28))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        edit_btn.clicked.connect(self._edit_element)
        header_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("🗑️")
        remove_btn.setToolTip("Remove")
        remove_btn.setFixedSize(*self.screen_utils.scale_size(28, 28))
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        remove_btn.clicked.connect(self._request_remove)
        header_layout.addWidget(remove_btn)
        
        layout.addLayout(header_layout)
        
        # KEY INFO ROW - Most Important Data
        key_info_layout = QGridLayout()
        key_info_layout.setSpacing(8)
        key_info_layout.setVerticalSpacing(12)
        
        # Nominal
        nom_lbl = QLabel("Nominal:")
        nom_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(nom_lbl, 0, 0)
        
        nom_val = QLabel(f"{self.element_data['nominal']:.4f}")
        nom_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(nom_val, 0, 1)
        
        # Class
        class_lbl = QLabel("Class:")
        class_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(class_lbl, 0, 2)
        
        class_val = QLabel(self.element_data.get('class', 'N/A'))
        class_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(class_val, 0, 3)
        
        # Sigma
        sigma_lbl = QLabel("Sigma:")
        sigma_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(sigma_lbl, 0, 4)
        
        sigma_val = QLabel(self.sigma)
        sigma_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(sigma_val, 0, 5)
        
        # Cavity
        cav_lbl = QLabel("Cavity:")
        cav_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(cav_lbl, 1, 0)
        
        cav_val = QLabel(str(self.element_data.get('cavity', 'N/A')))
        cav_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(cav_val, 1, 1)
        
        # Average - will be filled after calculation
        avg_lbl = QLabel("Average:")
        avg_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(avg_lbl, 1, 2)
        
        self.avg_val = QLabel("0.0000")
        self.avg_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(self.avg_val, 1, 3)
        
        # Sample size
        n_lbl = QLabel("n:")
        n_lbl.setStyleSheet("color: #6c757d; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(n_lbl, 1, 4)
        
        self.n_val = QLabel(str(len(self.element_data['values'])))
        self.n_val.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt; background: transparent; border: none;")
        key_info_layout.addWidget(self.n_val, 1, 5)
        
        layout.addLayout(key_info_layout)
        
        # CAPABILITY METRICS ROW - Compact
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(6)
        layout.addLayout(self.metrics_layout)
        
        self.setLayout(layout)
        self.setFixedHeight(int(200 * self.screen_utils.scale_factor))
    
    def calculate_and_display_metrics(self):
        """Calculate metrics and update display"""
        self.metrics = self._calculate_all_metrics()
        self._display_metrics()
    
    def _calculate_all_metrics(self):
        """Calculate metrics from CURRENT values"""
        values = self.element_data['values']
        n = len(values)

        if n == 0:
            return self._get_empty_metrics()
        
        average = sum(values) / n
        variance = sum((x - average) ** 2 for x in values) / (n - 1) if n > 1 else 0
        sigma_long = math.sqrt(variance)
        
        if n > 1:
            moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, n)]
            avg_mr = sum(moving_ranges) / len(moving_ranges) if moving_ranges else 0
            sigma_short = avg_mr / 1.128
        else:
            sigma_short = 0
        
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
        """Display key metrics in compact format"""
        # Update average in key info
        self.avg_val.setText(f"{self.metrics['average']:.4f}")
        self.n_val.setText(str(self.metrics['sample_size']))
        
        # Clear metrics layout
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Key capability metrics only
        key_metrics = [
            ('Cpk', self.metrics['cpk'], True, False),
            ('Ppk', self.metrics['ppk'], True, True),
            ('Cp', self.metrics['cp'], False, False),
            ('Pp', self.metrics['pp'], False, True),
        ]
        
        for label, value, color_code, is_long_term in key_metrics:
            container = QFrame()
            container.setStyleSheet("background: transparent; border: none;")
            cont_layout = QHBoxLayout(container)
            cont_layout.setContentsMargins(0, 0, 0, 0)
            cont_layout.setSpacing(3)
            
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #495057; font-size: 8pt; background: transparent; border: none;")
            cont_layout.addWidget(lbl)
            
            value_text = f"{value:.2f}" if abs(value) >= 0.01 else f"{value:.3f}"
            color = self._get_metric_color(label, value, is_long_term) if color_code else "#495057"
            
            value_lbl = QLabel(value_text)
            value_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 8pt; background: transparent; border: none;")
            cont_layout.addWidget(value_lbl)
            
            self.metrics_layout.addWidget(container)
        
        self.metrics_layout.addStretch()
    
    def _get_metric_color(self, metric_type, value, is_long_term=False):
        """Get color based on metric value and sigma setting"""
        if any(x in metric_type.lower() for x in ['cp', 'pp']):
            if self.sigma == '6σ':
                excellent = 2.0
                good = 1.67
                acceptable = 1.33
            else:  # 5σ
                excellent = 1.67
                good = 1.33
                acceptable = 1.0
            
            if value >= excellent:
                return "#28a745"
            elif value >= good:
                return "#17a2b8"
            elif value >= acceptable:
                return "#ffc107"
            else:
                return "#dc3545"
        return "#495057"
    
    def _edit_element(self):
        """Edit element"""
        from .element_edit_dialog import ElementEditDialog
        
        dialog = ElementEditDialog(
            element_id=self.element_id,
            element_data=self.element_data.copy(),
            metrics=self.metrics.copy(),
            parent=self
        )
        
        if dialog.exec_():
            updated = dialog.get_updated_data()
            
            self.element_data['values'] = updated['values']
            self.element_data['original_values'] = updated['original_values']
            self.element_data['extrapolated_values'] = updated['extrapolated_values']
            self.element_data['has_extrapolation'] = updated['has_extrapolation']
            
            self.original_values = updated['original_values']
            self.extrapolated_values = updated['extrapolated_values']
            self.has_extrapolation = updated['has_extrapolation']
            
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
        """Get complete element data"""
        return {
            'element_id': self.element_id,
            'cavity': self.element_data.get('cavity', ''),
            'class': self.element_data.get('class', ''),
            'sigma': self.sigma,
            'instrument': self.element_data.get('instrument', '3D Scanner'),
            'nominal': self.element_data['nominal'],
            'tol_minus': self.element_data['tol_minus'],
            'tol_plus': self.element_data['tol_plus'],
            'values': self.element_data['values'],
            'original_values': self.original_values,
            'has_extrapolation': self.has_extrapolation,
            'extrapolated_values': self.extrapolated_values,
            'metrics': self.element_data.get('metrics'),
        }