# src/gui/widgets/element_input_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFrame, QGridLayout, QScrollArea, QPushButton, 
    QCheckBox, QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QSplitter, QTabWidget
)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QObject, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor
from src.gui.utils.element_input_styles import get_element_input_styles
from .buttons import ModernButton, CompactButton
from .inputs import ModernLineEdit, ModernComboBox
from src.services.measurement_history_service import MeasurementHistoryService
import logging
import math
from scipy import stats

logger = logging.getLogger(__name__)


class ElementMetricsWidget(QFrame):
    """Compact widget to display metrics for a single element"""
    metricsChanged = pyqtSignal(str, dict)
    removeRequested = pyqtSignal(object)
    editRequested = pyqtSignal(object)
    
    def __init__(self, element_data, parent=None):
        super().__init__(parent)
        self.element_data = element_data
        self.element_id = element_data['element_id']
        self.metrics_inputs = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                margin: 3px;
            }
            QFrame:hover {
                border-color: #3498db;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Compact header
        header_layout = QHBoxLayout()
        header = QLabel(f"{self.element_id}")
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; background: transparent; border: none;")
        header_layout.addWidget(header)
        
        # Cavity and class info inline
        info = QLabel(f"Cav: {self.element_data.get('cavity', 'N/A')} | {self.element_data.get('class', 'N/A')}")
        info.setFont(QFont("Segoe UI", 8))
        info.setStyleSheet("color: #6c757d; background: transparent; border: none;")
        header_layout.addWidget(info)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Compact metrics in 2 columns
        metrics = self._calculate_metrics()
        
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(5)
        metrics_layout.setVerticalSpacing(3)
        
        metric_items = [
            ('Cp', metrics['cp']),
            ('Cpk', metrics['cpk']),
            ('σ', metrics['sigma_short']),
            ('PPM', f"{int(metrics['ppm_short']):,}")
        ]
        
        for i, (label, value) in enumerate(metric_items):
            row = i // 2
            col = (i % 2) * 2
            
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #495057; font-size: 8pt; background: transparent; border: none;")
            metrics_layout.addWidget(lbl, row, col)
            
            if isinstance(value, str):
                value_text = value
                color = "#495057"
            else:
                value_text = f"{value:.3f}"
                color = self._get_metric_color(label, value)
            
            value_lbl = QLabel(value_text)
            value_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 8pt; background: transparent; border: none;")
            metrics_layout.addWidget(value_lbl, row, col + 1)
            
            self.metrics_inputs[label.lower().replace('σ', 'sigma')] = value if not isinstance(value, str) else 0
        
        layout.addLayout(metrics_layout)
        
        # Compact action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit Values")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        edit_btn.clicked.connect(self._edit_values)
        
        remove_btn = QPushButton("🗑️")
        remove_btn.setToolTip("Remove")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(self._request_remove)
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.setFixedHeight(110)  # Compact height
    
    def _calculate_metrics(self):
        """Calculate all statistical metrics"""
        values = self.element_data['values']
        n = len(values)
        
        if n == 0:
            return self._get_empty_metrics()
        
        # Basic statistics
        average = sum(values) / n
        variance = sum((x - average) ** 2 for x in values) / (n - 1) if n > 1 else 0
        sigma_long = math.sqrt(variance)
        
        # Sigma short (moving range method)
        if n > 1:
            moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, n)]
            avg_mr = sum(moving_ranges) / len(moving_ranges) if moving_ranges else 0
            sigma_short = avg_mr / 1.128
        else:
            sigma_short = 0
        
        # Tolerances
        nominal = self.element_data['nominal']
        tol_minus = abs(self.element_data['tol_minus'])
        tol_plus = abs(self.element_data['tol_plus'])
        USL = nominal + tol_plus
        LSL = nominal - tol_minus
        tolerance = USL - LSL
        
        # Capability indices
        if sigma_short > 0:
            cp = tolerance / (6 * sigma_short)
            cpu = (USL - average) / (3 * sigma_short)
            cpl = (average - LSL) / (3 * sigma_short)
            cpk = min(cpu, cpl)
        else:
            cp = cpk = 0
        
        if sigma_long > 0:
            pp = tolerance / (6 * sigma_long)
            ppu = (USL - average) / (3 * sigma_long)
            ppl = (average - LSL) / (3 * sigma_long)
            ppk = min(ppu, ppl)
        else:
            pp = ppk = 0
        
        # PPM calculations
        if sigma_short > 0:
            z_usl_short = (USL - average) / sigma_short
            z_lsl_short = (average - LSL) / sigma_short
            ppm_short = (stats.norm.cdf(-z_lsl_short) + (1 - stats.norm.cdf(z_usl_short))) * 1e6
        else:
            ppm_short = 0
        
        return {
            'average': average,
            'sigma_long': sigma_long,
            'sigma_short': sigma_short,
            'cp': cp,
            'cpk': cpk,
            'pp': pp,
            'ppk': ppk,
            'ppm_short': ppm_short
        }
    
    def _get_empty_metrics(self):
        """Return zero metrics"""
        return {
            'average': 0, 'sigma_long': 0, 'sigma_short': 0,
            'cp': 0, 'cpk': 0, 'pp': 0, 'ppk': 0,
            'ppm_short': 0
        }
    
    def _get_metric_color(self, metric_type, value):
        """Get color coding for metrics"""
        if any(x in metric_type.lower() for x in ['cp', 'pp']):
            if value >= 1.67:
                return "#28a745"
            elif value >= 1.33:
                return "#17a2b8"
            elif value >= 1.0:
                return "#ffc107"
            else:
                return "#dc3545"
        return "#495057"
    
    def _edit_values(self):
        """Open dialog to edit element values"""
        from .element_edit_dialog import ElementEditDialog
        dialog = ElementEditDialog(
            self.element_id,
            self.element_data['values'],
            {
                'nominal': self.element_data['nominal'],
                'tol_minus': self.element_data['tol_minus'],
                'tol_plus': self.element_data['tol_plus']
            },
            self
        )
        if dialog.exec_():
            new_values = dialog.get_values()
            self.element_data['values'] = new_values
            # Refresh display
            parent = self.parent()
            self.setParent(None)
            self.__init__(self.element_data, parent)
            self.metricsChanged.emit(self.element_id, self._calculate_metrics())
    
    def _request_remove(self):
        """Request removal of this element"""
        reply = QMessageBox.question(
            self, 'Remove Element',
            f'Remove element {self.element_id}?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.removeRequested.emit(self)
    
    def get_element_data(self):
        """Return current element data with metrics"""
        return {
            **self.element_data,
            'metrics': self.metrics_inputs
        }


class ElementInputWidget(QWidget):
    study_requested = pyqtSignal(list, dict)
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, client=None, project_reference=None, batch_lot=None):
        super().__init__(parent)
        self.elements = []
        self.element_widgets = []
        self.client = client
        self.project_reference = project_reference
        self.batch_lot = batch_lot
        
        self.setStyleSheet(get_element_input_styles())
        self.init_ui()
        
        if self.client and self.project_reference:
            self.load_elements_button.setEnabled(True)
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create main splitter for better layout
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Input form
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        self._create_input_form(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel - Elements and extrapolation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        self._create_elements_area(right_layout)
        self._create_extrapolation_config(right_layout)
        self._create_action_buttons(right_layout)
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([500, 700])
        main_layout.addWidget(splitter)
    
    def _create_input_form(self, main_layout):
        """Create enhanced input form"""
        form_group = QGroupBox("📝 Add Element")
        form_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        form_group.setStyleSheet("""
            QGroupBox {
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(form_group)
        layout.setSpacing(15)
        
        # Mode selection
        mode_frame = QFrame()
        mode_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        mode_layout = QVBoxLayout(mode_frame)
        
        mode_label = QLabel("Data Entry Mode:")
        mode_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        mode_layout.addWidget(mode_label)
        
        mode_btn_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()
        
        self.manual_radio = QRadioButton("✏️ Manual Entry")
        self.manual_radio.setChecked(True)
        self.manual_radio.toggled.connect(self._toggle_entry_mode)
        self.mode_group.addButton(self.manual_radio)
        mode_btn_layout.addWidget(self.manual_radio)
        
        self.database_radio = QRadioButton("🗄️ Load from Database")
        self.database_radio.toggled.connect(self._toggle_entry_mode)
        self.mode_group.addButton(self.database_radio)
        mode_btn_layout.addWidget(self.database_radio)
        
        mode_layout.addLayout(mode_btn_layout)
        layout.addWidget(mode_frame)
        
        # Element information section
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
            }
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(10)
        
        # Row 1: Element name/selector
        info_layout.addWidget(QLabel("Element:"), 0, 0)
        self.element_name_input = ModernLineEdit("Enter element name")
        self.element_selector = ModernComboBox()
        self.element_selector.addItem("Select an element...")
        self.element_selector.hide()
        info_layout.addWidget(self.element_name_input, 0, 1, 1, 2)
        info_layout.addWidget(self.element_selector, 0, 1, 1, 2)
        
        # Row 2: Cavity
        info_layout.addWidget(QLabel("Cavity:"), 1, 0)
        self.cavity_input = ModernLineEdit("e.g., A, B, C...")
        info_layout.addWidget(self.cavity_input, 1, 1, 1, 2)
        
        # Row 3: Class and Sigma
        info_layout.addWidget(QLabel("Class:"), 2, 0)
        self.class_input = ModernLineEdit("Enter class")
        info_layout.addWidget(self.class_input, 2, 1)
        
        self.sigma_combo = ModernComboBox()
        self.sigma_combo.addItems(["5σ", "6σ"])
        self.sigma_combo.setCurrentIndex(1)  # Default to 6σ
        info_layout.addWidget(self.sigma_combo, 2, 2)
        
        # Row 4: Nominal and tolerances
        info_layout.addWidget(QLabel("Nominal:"), 3, 0)
        self.nominal_input = ModernLineEdit("0.0000")
        info_layout.addWidget(self.nominal_input, 3, 1, 1, 2)
        
        info_layout.addWidget(QLabel("Tolerance -:"), 4, 0)
        self.tol_minus_input = ModernLineEdit("-0.0000")
        info_layout.addWidget(self.tol_minus_input, 4, 1, 1, 2)
        
        info_layout.addWidget(QLabel("Tolerance +:"), 5, 0)
        self.tol_plus_input = ModernLineEdit("+0.0000")
        info_layout.addWidget(self.tol_plus_input, 5, 1, 1, 2)
        
        layout.addWidget(info_frame)
        
        # Database buttons
        self.db_buttons_frame = QFrame()
        self.db_buttons_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        db_btn_layout = QHBoxLayout(self.db_buttons_frame)
        
        self.load_elements_button = QPushButton("📋 Load Elements")
        self.load_elements_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.load_elements_button.clicked.connect(self._load_available_elements)
        self.load_elements_button.setEnabled(False)
        db_btn_layout.addWidget(self.load_elements_button)
        
        self.load_data_button = QPushButton("🔄 Load Values")
        self.load_data_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.load_data_button.clicked.connect(self._load_element_data)
        self.load_data_button.setEnabled(False)
        db_btn_layout.addWidget(self.load_data_button)
        
        self.db_buttons_frame.hide()
        layout.addWidget(self.db_buttons_frame)
        
        # Values section
        values_frame = QFrame()
        values_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
            }
        """)
        values_layout = QVBoxLayout(values_frame)
        
        values_header = QHBoxLayout()
        values_label = QLabel("📊 Measured Values (min. 5)")
        values_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        values_header.addWidget(values_label)
        
        add_values_btn = QPushButton("➕ Add More")
        add_values_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        add_values_btn.clicked.connect(lambda: self._add_value_inputs(5))
        values_header.addWidget(add_values_btn)
        values_header.addStretch()
        
        values_layout.addLayout(values_header)
        
        # Scrollable values area
        values_scroll = QScrollArea()
        values_scroll.setWidgetResizable(True)
        values_scroll.setMaximumHeight(200)
        values_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        self.values_widget = QWidget()
        self.values_layout = QGridLayout()
        self.values_layout.setSpacing(8)
        self.values_inputs = []
        self._add_value_inputs(10)  # Start with 10 inputs
        
        self.values_widget.setLayout(self.values_layout)
        values_scroll.setWidget(self.values_widget)
        values_layout.addWidget(values_scroll)
        
        layout.addWidget(values_frame)
        
        # Add element button
        add_element_btn = QPushButton("✅ Add Element to Study")
        add_element_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_element_btn.clicked.connect(self.add_element)
        layout.addWidget(add_element_btn)
        
        main_layout.addWidget(form_group)
    
    def _add_value_inputs(self, count):
        """Add value input fields"""
        current = len(self.values_inputs)
        for i in range(count):
            row = (current + i) // 5
            col = (current + i) % 5
            
            value_input = ModernLineEdit()
            value_input.setPlaceholderText(f"V{current + i + 1}")
            value_input.setMaximumWidth(100)
            self.values_inputs.append(value_input)
            self.values_layout.addWidget(value_input, row, col)
    
    def _create_elements_area(self, main_layout):
        """Create scrollable area for element widgets"""
        group = QGroupBox("📦 Added Elements")
        group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        container = QWidget()
        self.elements_layout = QVBoxLayout()
        self.elements_layout.setSpacing(10)
        self.elements_layout.setAlignment(Qt.AlignTop)
        container.setLayout(self.elements_layout)
        
        # Add placeholder
        self.elements_placeholder = QLabel("No elements added yet.\nAdd elements using the form on the left.")
        self.elements_placeholder.setAlignment(Qt.AlignCenter)
        self.elements_placeholder.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10pt;
                padding: 40px;
                font-style: italic;
            }
        """)
        self.elements_layout.addWidget(self.elements_placeholder)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        group.setLayout(layout)
        main_layout.addWidget(group)
    
    def _create_extrapolation_config(self, main_layout):
        """Enhanced extrapolation configuration"""
        group = QGroupBox("🔬 Extrapolation Settings")
        group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                color: #2c3e50;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Enable extrapolation
        self.extrap_checkbox = QCheckBox("Enable Extrapolation for Normality")
        self.extrap_checkbox.setFont(QFont("Segoe UI", 10))
        self.extrap_checkbox.toggled.connect(self._toggle_extrapolation_settings)
        layout.addWidget(self.extrap_checkbox)
        
        # Settings frame
        self.extrap_settings_frame = QFrame()
        self.extrap_settings_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.extrap_settings_frame.setEnabled(False)
        
        settings_layout = QGridLayout(self.extrap_settings_frame)
        
        # Target values
        settings_layout.addWidget(QLabel("Target Values:"), 0, 0)
        self.target_values_spin = QSpinBox()
        self.target_values_spin.setRange(10, 200)
        self.target_values_spin.setValue(50)
        self.target_values_spin.setSuffix(" values")
        settings_layout.addWidget(self.target_values_spin, 0, 1)
        
        # Max attempts
        settings_layout.addWidget(QLabel("Max Attempts:"), 1, 0)
        self.max_attempts_spin = QSpinBox()
        self.max_attempts_spin.setRange(10, 200)
        self.max_attempts_spin.setValue(100)
        self.max_attempts_spin.setSuffix(" attempts")
        settings_layout.addWidget(self.max_attempts_spin, 1, 1)
        
        # P-value objective
        settings_layout.addWidget(QLabel("P-value Target:"), 2, 0)
        self.p_value_spin = QDoubleSpinBox()
        self.p_value_spin.setRange(0.01, 0.10)
        self.p_value_spin.setValue(0.05)
        self.p_value_spin.setDecimals(3)
        self.p_value_spin.setSingleStep(0.01)
        settings_layout.addWidget(self.p_value_spin, 2, 1)
        
        layout.addWidget(self.extrap_settings_frame)
        group.setLayout(layout)
        main_layout.addWidget(group)
    
    def _create_action_buttons(self, main_layout):
        """Create action buttons"""
        btn_frame = QFrame()
        btn_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(15)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_elements)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        run_btn = QPushButton("▶️ Run Study")
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        run_btn.clicked.connect(self.run_study)
        btn_layout.addWidget(run_btn)
        
        main_layout.addWidget(btn_frame)
    
    def _toggle_entry_mode(self):
        """Toggle between manual and database entry modes"""
        is_manual = self.manual_radio.isChecked()
        
        # Toggle visibility of inputs
        self.element_name_input.setVisible(is_manual)
        self.element_selector.setVisible(not is_manual)
        self.db_buttons_frame.setVisible(not is_manual)
        
        # Enable/disable database buttons
        if not is_manual and self.client and self.project_reference:
            self.load_elements_button.setEnabled(True)
    
    def _toggle_extrapolation_settings(self, checked):
        """Enable/disable extrapolation settings"""
        self.extrap_settings_frame.setEnabled(checked)
    
    def add_element(self):
        """Add element to the study"""
        try:
            # Get element identifier
            if self.manual_radio.isChecked():
                element_id = self.element_name_input.text().strip()
                if not element_id:
                    QMessageBox.warning(self, "Missing Data", "Element name is required")
                    return
            else:
                element_id = self.element_selector.currentText()
                if element_id == "Select an element...":
                    QMessageBox.warning(self, "Missing Data", "Please select an element")
                    return
            
            # Get other fields
            cavity = self.cavity_input.text().strip()
            class_name = self.class_input.text().strip()
            sigma = self.sigma_combo.currentText()
            
            # Validate tolerances
            try:
                nominal = float(self.nominal_input.text())
                tol_minus = float(self.tol_minus_input.text())
                tol_plus = float(self.tol_plus_input.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Data", "Nominal and tolerances must be numbers")
                return
            
            # Get measured values
            values = []
            for inp in self.values_inputs:
                text = inp.text().strip()
                if text:
                    try:
                        values.append(float(text))
                    except ValueError:
                        pass
            
            if len(values) < 5:
                QMessageBox.warning(self, "Insufficient Data", "At least 5 values required")
                return
            
            # Check for duplicate element (same element_id + cavity)
            for elem in self.elements:
                if elem['element_id'] == element_id and elem['cavity'] == cavity:
                    QMessageBox.warning(
                        self, "Duplicate Element", 
                        f"Element '{element_id}' with cavity '{cavity}' already exists"
                    )
                    return
            
            # Create element data
            element_data = {
                'element_id': element_id,
                'cavity': cavity,
                'class': class_name,
                'sigma': sigma,
                'nominal': nominal,
                'tol_minus': tol_minus,
                'tol_plus': tol_plus,
                'values': values
            }
            
            # Remove placeholder if present
            if self.elements_placeholder.parent():
                self.elements_placeholder.setParent(None)
            
            # Create and add widget
            widget = ElementMetricsWidget(element_data, self)
            widget.removeRequested.connect(self._remove_element_widget)
            widget.metricsChanged.connect(self._on_metrics_changed)
            
            self.elements_layout.addWidget(widget)
            self.element_widgets.append(widget)
            self.elements.append(element_data)
            
            # Clear inputs
            self._clear_inputs()
            self._emit_summary_metrics()
            
            QMessageBox.information(
                self, "Success", 
                f"Element '{element_id}' (Cavity: {cavity}) added successfully!"
            )
            
        except Exception as e:
            logger.error(f"Error adding element: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add element: {e}")
    
    def _remove_element_widget(self, widget):
        """Remove an element widget"""
        if widget in self.element_widgets:
            self.element_widgets.remove(widget)
            
            # Remove from elements list
            for i, elem in enumerate(self.elements):
                if (elem['element_id'] == widget.element_data['element_id'] and 
                    elem['cavity'] == widget.element_data['cavity']):
                    self.elements.pop(i)
                    break
            
            widget.setParent(None)
            widget.deleteLater()
            
            # Add placeholder if no elements
            if not self.element_widgets:
                self.elements_layout.addWidget(self.elements_placeholder)
            
            # Update summary
            self._emit_summary_metrics()
    
    def _on_metrics_changed(self, element_id, metrics):
        """Handle metrics changes"""
        self._emit_summary_metrics()
    
    def _emit_summary_metrics(self):
        """Calculate and emit summary metrics for all elements"""
        if not self.element_widgets:
            self.metrics_updated.emit({})
            return
        
        total_elements = len(self.element_widgets)
        cp_values = []
        cpk_values = []
        ppm_values = []
        sigma_values = []
        
        for widget in self.element_widgets:
            metrics = widget.metrics_inputs
            cp_values.append(metrics.get('cp', 0))
            cpk_values.append(metrics.get('cpk', 0))
            ppm_values.append(metrics.get('ppm_short', 0))
            sigma_values.append(metrics.get('sigma_short', 0))
        
        summary = {
            'total_elements': total_elements,
            'avg_cp': sum(cp_values) / total_elements if cp_values else 0,
            'avg_cpk': sum(cpk_values) / total_elements if cpk_values else 0,
            'total_ppm': sum(ppm_values),
            'avg_deviation': sum(sigma_values) / total_elements if sigma_values else 0
        }
        
        self.metrics_updated.emit(summary)
    
    def clear_all_elements(self):
        """Remove all elements"""
        if not self.element_widgets:
            return
            
        reply = QMessageBox.question(
            self, 'Clear All',
            f'Remove all {len(self.element_widgets)} element(s)?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for widget in self.element_widgets[:]:
                widget.setParent(None)
                widget.deleteLater()
            self.element_widgets.clear()
            self.elements.clear()
            self.elements_layout.addWidget(self.elements_placeholder)
            self._emit_summary_metrics()
    
    def run_study(self):
        """Run the capability study"""
        if not self.elements:
            QMessageBox.warning(self, "No Data", "Please add at least one element")
            return
        
        # Collect current data from widgets
        elements_data = []
        for widget in self.element_widgets:
            elements_data.append(widget.get_element_data())
        
        # Extrapolation configuration
        extrap_config = {
            'include_extrapolation': self.extrap_checkbox.isChecked(),
            'target_values': self.target_values_spin.value() if self.extrap_checkbox.isChecked() else 50,
            'max_attempts': self.max_attempts_spin.value() if self.extrap_checkbox.isChecked() else 100,
            'p_value_target': self.p_value_spin.value() if self.extrap_checkbox.isChecked() else 0.05
        }
        
        logger.info(f"Running study with {len(elements_data)} elements")
        logger.info(f"Extrapolation config: {extrap_config}")
        
        self.study_requested.emit(elements_data, extrap_config)
    
    def _clear_inputs(self):
        """Clear input fields"""
        if self.manual_radio.isChecked():
            self.element_name_input.clear()
        else:
            self.element_selector.setCurrentIndex(0)
        
        self.cavity_input.clear()
        self.class_input.clear()
        self.nominal_input.clear()
        self.tol_minus_input.clear()
        self.tol_plus_input.clear()
        
        for inp in self.values_inputs:
            inp.clear()
    
    def _load_available_elements(self):
        """Load available elements from database"""
        if not self.client or not self.project_reference:
            QMessageBox.warning(self, "Missing Info", "Client and Project required")
            return
        
        try:
            service = MeasurementHistoryService()
            elements = service.get_available_elements(
                self.client, self.project_reference, batch_lot=self.batch_lot
            )
            service.close()
            
            self.element_selector.clear()
            self.element_selector.addItem("Select an element...")
            for elem in elements:
                self.element_selector.addItem(elem['element_id'])
            
            self.element_selector.setEnabled(True)
            self.load_data_button.setEnabled(True)
            
            logger.info(f"Loaded {len(elements)} available elements")
            QMessageBox.information(
                self, "Success", 
                f"Loaded {len(elements)} elements from database"
            )
            
        except Exception as e:
            logger.error(f"Error loading elements: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load elements: {e}")
    
    def _load_element_data(self):
        """Load data for selected element"""
        element_id = self.element_selector.currentText()
        if element_id == "Select an element...":
            return
        
        try:
            service = MeasurementHistoryService()
            measurements = service.get_element_measurement_history(
                self.client, self.project_reference, element_id, 
                limit=50, batch_lot=self.batch_lot
            )
            service.close()
            
            if measurements:
                # Auto-fill form with loaded data
                first_measurement = measurements[0]
                self.cavity_input.setText(str(first_measurement.get('cavity', '')))
                self.nominal_input.setText(str(first_measurement.get('nominal', '')))
                self.tol_minus_input.setText(str(first_measurement.get('tol_minus', '')))
                self.tol_plus_input.setText(str(first_measurement.get('tol_plus', '')))
                
                # Fill values - ensure we have enough input fields
                values = [m.get('value', 0) for m in measurements]
                if len(values) > len(self.values_inputs):
                    self._add_value_inputs(len(values) - len(self.values_inputs))
                
                for i, value in enumerate(values):
                    if i < len(self.values_inputs):
                        self.values_inputs[i].setText(str(value))
                
                logger.info(f"Loaded {len(values)} measurements for {element_id}")
                QMessageBox.information(
                    self, "Data Loaded", 
                    f"Loaded {len(values)} measurements for {element_id}"
                )
            else:
                QMessageBox.warning(self, "No Data", f"No measurements found for {element_id}")
                
        except Exception as e:
            logger.error(f"Error loading element data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load element data: {e}")
    
    def get_study_data(self):
        """Get all study data for session saving"""
        return {
            'elements': self.elements,
            'extrapolation': {
                'enabled': self.extrap_checkbox.isChecked(),
                'target_values': self.target_values_spin.value(),
                'max_attempts': self.max_attempts_spin.value(),
                'p_value_target': self.p_value_spin.value()
            }
        }
    
    def load_study_data(self, data):
        """Load study data from session"""
        # Clear existing elements
        self.clear_all_elements()
        
        # Load elements
        for elem_data in data.get('elements', []):
            # Remove placeholder if present
            if self.elements_placeholder.parent():
                self.elements_placeholder.setParent(None)
            
            # Create and add widget
            widget = ElementMetricsWidget(elem_data, self)
            widget.removeRequested.connect(self._remove_element_widget)
            widget.metricsChanged.connect(self._on_metrics_changed)
            
            self.elements_layout.addWidget(widget)
            self.element_widgets.append(widget)
            self.elements.append(elem_data)
        
        # Load extrapolation settings
        extrap = data.get('extrapolation', {})
        self.extrap_checkbox.setChecked(extrap.get('enabled', False))
        self.target_values_spin.setValue(extrap.get('target_values', 50))
        self.max_attempts_spin.setValue(extrap.get('max_attempts', 100))
        self.p_value_spin.setValue(extrap.get('p_value_target', 0.05))
        
        self._emit_summary_metrics()