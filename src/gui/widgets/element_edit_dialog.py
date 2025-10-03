# src/gui/widgets/element_edit_dialog.py - FIXED VERSION
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton, QTabWidget,
    QDoubleSpinBox, QGroupBox, QHBoxLayout, QScrollArea, QWidget,
    QMessageBox, QSpinBox, QCheckBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import math
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class ElementEditDialog(QDialog):
    """Enhanced dialog for editing element values, metrics, and extrapolation"""
    
    def __init__(self, element_id, element_data, metrics, parent=None):
        super().__init__(parent)
        self.element_id = element_id
        self.element_data = element_data.copy()
        self.current_metrics = metrics.copy()
        self.original_calculated_metrics = metrics.copy()  # Store original calculated values
        self.metrics_were_edited = False  # Track if metrics were manually edited
        
        self.tolerances = {
            'nominal': element_data['nominal'],
            'tol_minus': element_data['tol_minus'],
            'tol_plus': element_data['tol_plus']
        }
        
        # Track values
        self.original_values = element_data.get('original_values', element_data['values'].copy())
        self.current_values = element_data['values'].copy()
        self.extrapolated_values = element_data.get('extrapolated_values', [])
        self.has_extrapolation = element_data.get('has_extrapolation', False)
        
        self.metric_inputs = {}
        
        self.setWindowTitle(f"Edit Element - {element_id}")
        self.setMinimumSize(800, 900)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = QLabel(f"Edit Element: {self.element_id}")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
        # Tabs for different edit modes
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 5px;
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                font-weight: bold;
            }
        """)
        
        # Tab 1: Values Editor
        values_tab = self._create_values_tab()
        tabs.addTab(values_tab, "📊 Measured Values")
        
        # Tab 2: Metrics Editor
        metrics_tab = self._create_metrics_tab()
        tabs.addTab(metrics_tab, "📈 Direct Metrics")
        
        # Tab 3: Extrapolation
        extrap_tab = self._create_extrapolation_tab()
        tabs.addTab(extrap_tab, "🔬 Extrapolation")
        
        main_layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(100, 36)
        cancel_btn.setFont(QFont("Segoe UI", 10))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setMinimumSize(120, 36)
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_values_tab(self):
        """Create tab for editing measured values - FIXED with table"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tolerance info
        tol_frame = QGroupBox("Tolerance Information")
        tol_layout = QHBoxLayout()
        
        nominal_label = QLabel(f"Nominal: {self.tolerances['nominal']:.4f}")
        tol_minus_label = QLabel(f"Tolerance -: {self.tolerances['tol_minus']:.4f}")
        tol_plus_label = QLabel(f"Tolerance +: {self.tolerances['tol_plus']:.4f}")
        
        for lbl in [nominal_label, tol_minus_label, tol_plus_label]:
            lbl.setFont(QFont("Segoe UI", 10, QFont.Medium))
            lbl.setStyleSheet("color: #495057; padding: 5px;")
            tol_layout.addWidget(lbl)
        
        tol_frame.setLayout(tol_layout)
        layout.addWidget(tol_frame)
        
        # Values editing with table
        values_group = QGroupBox("Measured Values")
        values_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()

        add_value_btn = QPushButton("➕ Add Value")
        add_value_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        add_value_btn.clicked.connect(self._add_new_value)
        btn_layout.addWidget(add_value_btn)
        
        remove_value_btn = QPushButton("➖ Remove Selected")
        remove_value_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        remove_value_btn.clicked.connect(self._remove_selected_value)
        btn_layout.addWidget(remove_value_btn)
        
        btn_layout.addStretch()
        values_layout.addLayout(btn_layout)
        
        # Show extrapolation status
        if self.has_extrapolation:
            extrap_info = QLabel(f"ℹ️ This element has {len(self.extrapolated_values)} extrapolated values")
            extrap_info.setStyleSheet("color: #17a2b8; font-weight: bold; padding: 5px;")
            values_layout.addWidget(extrap_info)
            
            show_original_btn = QPushButton("Show Original Values Only")
            show_original_btn.clicked.connect(self._show_original_values)
            show_original_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #138496; }
            """)
            values_layout.addWidget(show_original_btn)
        
        # Table for values - IMPROVED HEIGHT
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(2)
        self.values_table.setHorizontalHeaderLabels(["#", "Value"])
        self.values_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.values_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.values_table.setMinimumHeight(180)  # Show ~4 rows clearly
        self.values_table.setMaximumHeight(250)
        self.values_table.setRowCount(len(self.current_values))
        
        for i, value in enumerate(self.current_values):
            # Index label
            is_extrapolated = i >= len(self.original_values) and self.has_extrapolation
            label_text = f"V{i+1}"
            if is_extrapolated:
                label_text += " 🔬"
            
            index_item = QTableWidgetItem(label_text)
            index_item.setFlags(Qt.ItemIsEnabled)
            if is_extrapolated:
                index_item.setBackground(Qt.cyan)
            self.values_table.setItem(i, 0, index_item)
            
            # Value spinbox
            value_item = QTableWidgetItem(f"{value:.4f}")
            self.values_table.setItem(i, 1, value_item)
        
        self.values_table.cellChanged.connect(self._on_value_changed)
        values_layout.addWidget(self.values_table)
        
        values_group.setLayout(values_layout)
        layout.addWidget(values_group)
        
        # Live statistics
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        
        self.stat_labels = {}
        stat_items = [
            ('count', 'Count'),
            ('mean', 'Mean'),
            ('std_dev', 'Std Dev'),
            ('min', 'Min'),
            ('max', 'Max'),
            ('range', 'Range')
        ]
        
        for i, (key, display_name) in enumerate(stat_items):
            row = i // 3
            col = (i % 3) * 2
            
            label = QLabel(f"{display_name}:")
            label.setFont(QFont("Segoe UI", 10, QFont.Medium))
            label.setStyleSheet("color: #495057;")
            stats_layout.addWidget(label, row, col)
            
            value_label = QLabel("0.0000")
            value_label.setFont(QFont("Segoe UI", 10))
            value_label.setStyleSheet("color: #2c3e50; font-weight: 600;")
            self.stat_labels[key] = value_label
            stats_layout.addWidget(value_label, row, col + 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Calculate initial statistics
        self.update_statistics()
        
        return tab
    
    def _add_new_value(self):
        """Add a new value to the table"""
        from PyQt5.QtWidgets import QInputDialog
        
        value, ok = QInputDialog.getDouble(
            self, "Add New Value", 
            "Enter new measured value:", 
            decimals=4
        )
        
        if ok:
            # Disconnect signal temporarily
            self.values_table.cellChanged.disconnect(self._on_value_changed)
            
            row_count = self.values_table.rowCount()
            self.values_table.setRowCount(row_count + 1)
            
            index_item = QTableWidgetItem(f"V{row_count + 1}")
            index_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.values_table.setItem(row_count, 0, index_item)
            
            value_item = QTableWidgetItem(f"{value:.4f}")
            self.values_table.setItem(row_count, 1, value_item)
            
            # Add to current values
            self.current_values.append(value)
            self.original_values.append(value)  # Add to original too
            
            # Reconnect signal
            self.values_table.cellChanged.connect(self._on_value_changed)
            
            self.update_statistics()
            
            logger.info(f"Added new value: {value:.4f}")
    
    def _remove_selected_value(self):
        """Remove selected value from table"""
        current_row = self.values_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a value to remove")
            return
        
        if len(self.current_values) <= 5:
            QMessageBox.warning(self, "Minimum Values", "Cannot remove - minimum 5 values required")
            return
        
        reply = QMessageBox.question(
            self, 'Remove Value',
            f'Remove value at row {current_row + 1}?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Disconnect signal
            self.values_table.cellChanged.disconnect(self._on_value_changed)
            
            # Remove from lists
            del self.current_values[current_row]
            if current_row < len(self.original_values):
                del self.original_values[current_row]
            
            # Remove from table
            self.values_table.removeRow(current_row)
            
            # Renumber remaining rows
            for i in range(self.values_table.rowCount()):
                self.values_table.item(i, 0).setText(f"V{i+1}")
            
            # Reconnect signal
            self.values_table.cellChanged.connect(self._on_value_changed)
            
            self.update_statistics()
            
            logger.info(f"Removed value at row {current_row}")
    
    
    def _create_metrics_tab(self):
        """Create tab for directly editing metrics - FIXED with reset button"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel("⚠️ Direct metric editing - Changes here will be used for chart generation")
        info.setStyleSheet("color: #ffc107; font-weight: bold; padding: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Metrics editing
        metrics_group = QGroupBox("Statistical Metrics")
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(15)
        
        row = 0
        
        # Average
        metrics_layout.addWidget(QLabel("Average (μ):"), row, 0)
        self.metric_inputs['average'] = QDoubleSpinBox()
        self.metric_inputs['average'].setDecimals(4)
        self.metric_inputs['average'].setRange(-999999, 999999)
        self.metric_inputs['average'].setValue(self.current_metrics['average'])
        self.metric_inputs['average'].valueChanged.connect(self._on_metric_edited)
        metrics_layout.addWidget(self.metric_inputs['average'], row, 1)
        row += 1
        
        # Short-term deviation
        metrics_layout.addWidget(QLabel("Short-term Std Dev (σ short):"), row, 0)
        self.metric_inputs['sigma_short'] = QDoubleSpinBox()
        self.metric_inputs['sigma_short'].setDecimals(4)
        self.metric_inputs['sigma_short'].setRange(0, 999999)
        self.metric_inputs['sigma_short'].setValue(self.current_metrics['sigma_short'])
        self.metric_inputs['sigma_short'].valueChanged.connect(self._on_metric_edited)
        metrics_layout.addWidget(self.metric_inputs['sigma_short'], row, 1)
        row += 1
        
        # Long-term deviation
        metrics_layout.addWidget(QLabel("Long-term Std Dev (σ long):"), row, 0)
        self.metric_inputs['sigma_long'] = QDoubleSpinBox()
        self.metric_inputs['sigma_long'].setDecimals(4)
        self.metric_inputs['sigma_long'].setRange(0, 999999)
        self.metric_inputs['sigma_long'].setValue(self.current_metrics['sigma_long'])
        self.metric_inputs['sigma_long'].valueChanged.connect(self._on_metric_edited)
        metrics_layout.addWidget(self.metric_inputs['sigma_long'], row, 1)
        row += 1
        
        # Reset button
        reset_btn = QPushButton("🔄 Reset to Calculated Values")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #138496; }
        """)
        reset_btn.clicked.connect(self._reset_metrics)
        metrics_layout.addWidget(reset_btn, row, 0, 1, 2)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Calculated capability indices (read-only display)
        calc_group = QGroupBox("Calculated Capability Indices")
        calc_layout = QGridLayout()
        calc_layout.setSpacing(10)
        
        self.calc_labels = {}
        calc_metrics = [
            ('cp', 'Cp'), ('cpk', 'Cpk'), ('ppm_short', 'PPM Short'),
            ('pp', 'Pp'), ('ppk', 'Ppk'), ('ppm_long', 'PPM Long')
        ]
        
        for i, (key, label) in enumerate(calc_metrics):
            row = i // 2
            col = (i % 2) * 2
            
            calc_layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel(self._format_metric(key, self.current_metrics.get(key, 0)))
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            self.calc_labels[key] = value_label
            calc_layout.addWidget(value_label, row, col + 1)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)
        
        # Recalculate initially
        self._recalculate_capability()
        
        layout.addStretch()
        return tab
    
    def _create_extrapolation_tab(self):
        """Create tab for extrapolation configuration"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Current status
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        if self.has_extrapolation:
            status_label = QLabel(f"✅ Extrapolation Active - {len(self.extrapolated_values)} extrapolated values")
            status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            status_layout.addWidget(status_label)
            
            original_info = QLabel(f"Original values: {len(self.original_values)} | Current total: {len(self.current_values)}")
            original_info.setStyleSheet("color: #6c757d;")
            status_layout.addWidget(original_info)
        else:
            status_label = QLabel("❌ No extrapolation applied")
            status_label.setStyleSheet("color: #6c757d; font-weight: bold;")
            status_layout.addWidget(status_label)
        
        layout.addWidget(status_frame)
        
        # Extrapolation configuration
        config_group = QGroupBox("Extrapolation Configuration")
        config_layout = QGridLayout()
        config_layout.setSpacing(10)
        
        config_layout.addWidget(QLabel("Target Sample Size:"), 0, 0)
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 200)
        self.target_size_spin.setValue(100)
        self.target_size_spin.setSuffix(" values")
        config_layout.addWidget(self.target_size_spin, 0, 1)
        
        config_layout.addWidget(QLabel("P-value Target:"), 1, 0)
        self.p_value_spin = QDoubleSpinBox()
        self.p_value_spin.setRange(0.01, 0.10)
        self.p_value_spin.setValue(0.05)
        self.p_value_spin.setDecimals(3)
        config_layout.addWidget(self.p_value_spin, 1, 1)
        
        config_layout.addWidget(QLabel("Max Attempts:"), 2, 0)
        self.max_attempts_spin = QSpinBox()
        self.max_attempts_spin.setRange(10, 200)
        self.max_attempts_spin.setValue(10)
        config_layout.addWidget(self.max_attempts_spin, 2, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Extrapolation buttons
        btn_layout = QHBoxLayout()
        
        run_extrap_btn = QPushButton("🔬 Run Extrapolation")
        run_extrap_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #138496; }
        """)
        run_extrap_btn.clicked.connect(self._run_extrapolation)
        btn_layout.addWidget(run_extrap_btn)
        
        if self.has_extrapolation:
            remove_extrap_btn = QPushButton("❌ Remove Extrapolation")
            remove_extrap_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #c82333; }
            """)
            remove_extrap_btn.clicked.connect(self._remove_extrapolation)
            btn_layout.addWidget(remove_extrap_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        return tab
    
    def _on_value_changed(self):
        """Update statistics when values change"""
        self.update_statistics()
    
    def _on_metric_edited(self):
        """Track that metrics were manually edited"""
        self.metrics_were_edited = True
        self._recalculate_capability()
    
    def _reset_metrics(self):
        """Reset metrics to original calculated values"""
        reply = QMessageBox.question(
            self, 'Reset Metrics',
            'Reset all metrics to calculated values from current measurement data?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Recalculate from current values
            values = []
            for row in range(self.values_table.rowCount()):
                try:
                    val = float(self.values_table.item(row, 1).text())
                    values.append(val)
                except:
                    pass
            
            if values:
                # Recalculate metrics
                from src.services.capability_calculator_service import CapabilityCalculatorService
                calc_service = CapabilityCalculatorService()
                new_metrics = calc_service.calculate_metrics(
                    values,
                    self.tolerances['nominal'],
                    self.tolerances['tol_minus'],
                    self.tolerances['tol_plus']
                )
                
                # Update inputs
                self.metric_inputs['average'].setValue(new_metrics['mean'])
                self.metric_inputs['sigma_short'].setValue(new_metrics['sigma_short'])
                self.metric_inputs['sigma_long'].setValue(new_metrics['sigma_long'])
                
                self.metrics_were_edited = False
                self._recalculate_capability()
    
    def update_statistics(self):
        """Calculate and display statistics"""
        try:
            values = []
            for row in range(self.values_table.rowCount()):
                try:
                    val = float(self.values_table.item(row, 1).text())
                    values.append(val)
                except:
                    pass
            
            if not values:
                return
            
            n = len(values)
            mean = sum(values) / n
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            
            if n > 1:
                variance = sum((x - mean) ** 2 for x in values) / (n - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0
            
            self.stat_labels['count'].setText(str(n))
            self.stat_labels['mean'].setText(f"{mean:.4f}")
            self.stat_labels['std_dev'].setText(f"{std_dev:.4f}")
            self.stat_labels['min'].setText(f"{min_val:.4f}")
            self.stat_labels['max'].setText(f"{max_val:.4f}")
            self.stat_labels['range'].setText(f"{range_val:.4f}")
            
            nominal = self.tolerances['nominal']
            tol_minus = abs(self.tolerances['tol_minus'])
            tol_plus = abs(self.tolerances['tol_plus'])
            
            if nominal - tol_minus <= mean <= nominal + tol_plus:
                self.stat_labels['mean'].setStyleSheet("color: #28a745; font-weight: 600;")
            else:
                self.stat_labels['mean'].setStyleSheet("color: #dc3545; font-weight: 600;")
                
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    
    def _recalculate_capability(self):
        """Recalculate capability indices when metrics change"""
        try:
            average = self.metric_inputs['average'].value()
            sigma_short = self.metric_inputs['sigma_short'].value()
            sigma_long = self.metric_inputs['sigma_long'].value()
            
            nominal = self.tolerances['nominal']
            tol_minus = abs(self.tolerances['tol_minus'])
            tol_plus = abs(self.tolerances['tol_plus'])
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
            
            self.calc_labels['cp'].setText(self._format_metric('cp', cp))
            self.calc_labels['cpk'].setText(self._format_metric('cpk', cpk))
            self.calc_labels['ppm_short'].setText(self._format_metric('ppm_short', ppm_short))
            self.calc_labels['pp'].setText(self._format_metric('pp', pp))
            self.calc_labels['ppk'].setText(self._format_metric('ppk', ppk))
            self.calc_labels['ppm_long'].setText(self._format_metric('ppm_long', ppm_long))
            
        except Exception as e:
            logger.error(f"Error recalculating capability: {e}")
    
    def _format_metric(self, key, value):
        """Format metric value for display"""
        if 'ppm' in key:
            return f"{int(value):,}"
        else:
            return f"{value:.4f}"
    
    def _show_original_values(self):
        """Show only original values (remove extrapolated)"""
        reply = QMessageBox.question(
            self, 'Show Original Values',
            'This will remove extrapolated values and show only the original measured values. Continue?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_values = self.original_values.copy()
            self.has_extrapolation = False
            self.extrapolated_values = []
            
            # Refresh the dialog
            self.close()
            self.__init__(self.element_id, {**self.element_data, 'values': self.original_values, 'has_extrapolation': False}, self.current_metrics, self.parent())
            self.exec_()
    
    def _run_extrapolation(self):
        """Run extrapolation - COMPLETELY FIXED"""
        try:
            target_size = self.target_size_spin.value()
            p_value_target = self.p_value_spin.value()
            max_attempts = self.max_attempts_spin.value()
            
            # Get current values
            current_values = []
            for row in range(self.values_table.rowCount()):
                item = self.values_table.item(row, 1)
                if item and item.text().strip():
                    try:
                        current_values.append(float(item.text().strip()))
                    except:
                        pass
            
            if len(current_values) < 5:
                QMessageBox.warning(self, 'Insufficient Data', 'Need at least 5 values')
                return
            
            sigma_long = self.metric_inputs['sigma_long'].value()
            mean = self.metric_inputs['average'].value()
            
            if sigma_long <= 0:
                QMessageBox.warning(self, 'Invalid Deviation', 'Sigma must be > 0')
                return
            
            logger.info(f"Running extrapolation: target={target_size}, sigma={sigma_long:.4f}")
            
            # Store original if first time
            if not self.has_extrapolation:
                self.original_values = current_values.copy()
            
            n_extra = target_size - len(current_values)
            if n_extra <= 0:
                QMessageBox.warning(self, 'Invalid Target', 'Target must be > current size')
                return
            
            # Generate extrapolated values
            best_p_value = 0
            best_combined = None
            
            for attempt in range(max_attempts):
                new_vals = np.random.normal(mean, sigma_long, n_extra)
                combined = np.concatenate([current_values, new_vals])
                
                result = stats.anderson(combined, dist='norm')
                ad_stat = result.statistic
                
                if ad_stat >= 0.6:
                    p_value = np.exp(1.2937 - 5.709 * ad_stat + 0.0186 * ad_stat**2)
                elif 0.34 < ad_stat < 0.6:
                    p_value = np.exp(0.9177 - 4.279 * ad_stat - 1.38 * ad_stat**2)
                elif 0.2 < ad_stat <= 0.34:
                    p_value = 1 - np.exp(-8.318 + 42.796 * ad_stat - 59.938 * ad_stat**2)
                else:
                    p_value = 1 - np.exp(-13.436 + 101.14 * ad_stat - 223.73 * ad_stat**2)
                
                if p_value > best_p_value:
                    best_p_value = p_value
                    best_combined = combined.copy()
                
                if p_value >= p_value_target:
                    logger.info(f"Success at attempt {attempt + 1}: p={p_value:.4f}")
                    break
            
            if best_combined is not None:
                # CRITICAL: Update ALL state variables
                self.current_values = best_combined.tolist()
                self.extrapolated_values = best_combined[len(self.original_values):].tolist()
                self.has_extrapolation = True
                
                logger.info(f"EXTRAPOLATION COMPLETE:")
                logger.info(f"  Original: {len(self.original_values)}")
                logger.info(f"  Extrapolated: {len(self.extrapolated_values)}")
                logger.info(f"  Total: {len(self.current_values)}")
                logger.info(f"  Best p-value: {best_p_value:.4f}")
                
                QMessageBox.information(
                    self, 'Extrapolation Complete',
                    f'Successfully extrapolated to {len(best_combined)} values.\n\n'
                    f'Original: {len(self.original_values)}\n'
                    f'Extrapolated: {len(self.extrapolated_values)}\n'
                    f'Best P-value: {best_p_value:.4f}'
                )
                
                # Refresh dialog to show new values
                self.accept()
                self.__init__(
                    self.element_id,
                    {
                        **self.element_data,
                        'values': self.current_values,
                        'original_values': self.original_values,
                        'has_extrapolation': True,
                        'extrapolated_values': self.extrapolated_values
                    },
                    self.current_metrics,
                    self.parent()
                )
                self.exec_()
            else:
                QMessageBox.warning(self, 'Failed', 'Could not generate extrapolated values')
                
        except Exception as e:
            logger.error(f"Extrapolation error: {e}", exc_info=True)
            QMessageBox.critical(self, 'Error', f'Extrapolation failed: {e}')

    
    def _remove_extrapolation(self):
        """Remove extrapolation and return to original values"""
        reply = QMessageBox.question(
            self, 'Remove Extrapolation',
            'This will remove all extrapolated values and return to the original measurements. Continue?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_values = self.original_values.copy()
            self.has_extrapolation = False
            self.extrapolated_values = []
            
            self.close()
            self.__init__(
                self.element_id, 
                {**self.element_data, 'values': self.original_values, 'has_extrapolation': False}, 
                self.current_metrics, 
                self.parent()
            )
            self.exec_()
    
    def get_updated_data(self):
        """Get updated data - ABSOLUTE FINAL VERSION"""
        logger.info(f"=== GET UPDATED DATA: {self.element_id} ===")
        logger.info(f"  current_values: {len(self.current_values)}")
        logger.info(f"  original_values: {len(self.original_values)}")
        logger.info(f"  extrapolated_values: {len(self.extrapolated_values)}")
        logger.info(f"  has_extrapolation: {self.has_extrapolation}")
        
        return {
            'values': self.current_values,  # This is original + extrapolated
            'original_values': self.original_values.copy(),
            'extrapolated_values': self.extrapolated_values.copy(),
            'has_extrapolation': self.has_extrapolation,
            'custom_metrics': {
                'average': self.metric_inputs['average'].value(),
                'sigma_short': self.metric_inputs['sigma_short'].value(),
                'sigma_long': self.metric_inputs['sigma_long'].value()
            } if self.metrics_were_edited else None
        }