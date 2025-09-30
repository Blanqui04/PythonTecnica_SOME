#src/gui/widgets/element_edit_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QDoubleSpinBox, QGroupBox, QHBoxLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import math


class ElementEditDialog(QDialog):
    """Dialog for editing element measured values"""
    
    def __init__(self, element_id, values, tolerances, parent=None):
        super().__init__(parent)
        self.element_id = element_id
        self.original_values = values
        self.tolerances = tolerances
        self.value_inputs = []
        
        self.setWindowTitle(f"Edit Values - {element_id}")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = QLabel(f"Edit Measured Values: {self.element_id}")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
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
        main_layout.addWidget(tol_frame)
        
        # Values editing area
        values_group = QGroupBox("Measured Values")
        values_main_layout = QVBoxLayout()
        
        # Scrollable area for values
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        values_widget = QWidget()
        values_layout = QGridLayout()
        values_layout.setSpacing(10)
        
        # Create value inputs in a grid (5 columns)
        for i, value in enumerate(self.original_values):
            row = i // 5
            col = i % 5
            
            # Value container
            value_container = QWidget()
            value_container_layout = QVBoxLayout()
            value_container_layout.setSpacing(5)
            value_container_layout.setContentsMargins(5, 5, 5, 5)
            
            # Label
            label = QLabel(f"Value {i+1}")
            label.setFont(QFont("Segoe UI", 9))
            label.setStyleSheet("color: #6c757d;")
            label.setAlignment(Qt.AlignCenter)
            value_container_layout.addWidget(label)
            
            # Input
            value_input = QDoubleSpinBox()
            value_input.setDecimals(4)
            value_input.setRange(-999999, 999999)
            value_input.setValue(value)
            value_input.setMinimumHeight(32)
            value_input.setFont(QFont("Segoe UI", 10))
            value_input.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: white;
                    border: 2px solid #dee2e6;
                    border-radius: 4px;
                    padding: 4px;
                }
                QDoubleSpinBox:focus {
                    border-color: #3498db;
                }
            """)
            value_input.valueChanged.connect(self.on_value_changed)
            self.value_inputs.append(value_input)
            value_container_layout.addWidget(value_input)
            
            value_container.setLayout(value_container_layout)
            values_layout.addWidget(value_container, row, col)
        
        values_widget.setLayout(values_layout)
        scroll.setWidget(values_widget)
        values_main_layout.addWidget(scroll)
        
        values_group.setLayout(values_main_layout)
        main_layout.addWidget(values_group)
        
        # Statistics display
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        
        # Create stat labels
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
        main_layout.addWidget(stats_group)
        
        # Calculate initial statistics
        self.update_statistics()
        
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
            QPushButton:hover {
                background-color: #5a6268;
            }
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
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
        
    def on_value_changed(self):
        """Update statistics when values change"""
        self.update_statistics()
        
    def update_statistics(self):
        """Calculate and display statistics"""
        try:
            values = [inp.value() for inp in self.value_inputs]
            n = len(values)
            
            if n == 0:
                return
            
            # Basic statistics
            mean = sum(values) / n
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            
            # Standard deviation
            if n > 1:
                variance = sum((x - mean) ** 2 for x in values) / (n - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0
            
            # Update labels
            self.stat_labels['count'].setText(str(n))
            self.stat_labels['mean'].setText(f"{mean:.4f}")
            self.stat_labels['std_dev'].setText(f"{std_dev:.4f}")
            self.stat_labels['min'].setText(f"{min_val:.4f}")
            self.stat_labels['max'].setText(f"{max_val:.4f}")
            self.stat_labels['range'].setText(f"{range_val:.4f}")
            
            # Color code based on tolerance
            nominal = self.tolerances['nominal']
            tol_minus = abs(self.tolerances['tol_minus'])
            tol_plus = abs(self.tolerances['tol_plus'])
            
            # Check if mean is within tolerance
            if nominal - tol_minus <= mean <= nominal + tol_plus:
                self.stat_labels['mean'].setStyleSheet(
                    "color: #28a745; font-weight: 600;"
                )
            else:
                self.stat_labels['mean'].setStyleSheet(
                    "color: #dc3545; font-weight: 600;"
                )
                
        except Exception as e:
            print(f"Error updating statistics: {e}")
        
    def get_values(self):
        """Return the current values"""
        return [inp.value() for inp in self.value_inputs]