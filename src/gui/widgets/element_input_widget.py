# src/gui/widgets/element_input_widget.py - FIXED VERSION
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFrame, QGridLayout, QScrollArea, QPushButton, 
    QCheckBox, QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QSplitter, QTabWidget, QTableWidgetItem
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
        self._create_chart_type_selection(right_layout)
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
        layout.setSpacing(10)
        
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

        # Row 4: NEW - Measuring Instrument
        info_layout.addWidget(QLabel("Instrument:"), 3, 0)
        self.instrument_combo = ModernComboBox()
        self.instrument_combo.addItems([
            "3D Scanner",  # Default
            "CMM (Coordinate Measuring Machine)",
            "Optical CMM",
            "Laser Scanner",
            "Caliper",
            "Micrometer",
            "Height Gauge",
            "Manual Measurement",
            "Other"
        ])
        self.instrument_combo.setCurrentIndex(0)  # Default to 3D Scanner
        info_layout.addWidget(self.instrument_combo, 3, 1, 1, 2)
        
        # Row 4: Nominal and tolerances
        info_layout.addWidget(QLabel("Nominal:"), 4, 0)
        self.nominal_input = ModernLineEdit("0.0000")
        info_layout.addWidget(self.nominal_input, 4, 1, 1, 2)

        info_layout.addWidget(QLabel("Tolerance -:"), 5, 0)
        self.tol_minus_input = ModernLineEdit("-0.0000")
        info_layout.addWidget(self.tol_minus_input, 5, 1, 1, 2)

        info_layout.addWidget(QLabel("Tolerance +:"), 6, 0)
        self.tol_plus_input = ModernLineEdit("+0.0000")
        info_layout.addWidget(self.tol_plus_input, 6, 1, 1, 2)

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
        
        # VALUES SECTION - OPTIMIZED
        values_frame = QFrame()
        values_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        values_layout = QVBoxLayout(values_frame)
        values_layout.setSpacing(5)
        
        values_header = QHBoxLayout()
        values_label = QLabel("📊 Measured Values")
        values_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        values_header.addWidget(values_label)
        
        add_rows_btn = QPushButton("➕ Add 10")
        add_rows_btn.setMaximumWidth(80)
        add_rows_btn.clicked.connect(lambda: self._add_value_rows(10))
        values_header.addWidget(add_rows_btn)
        
        clear_values_btn = QPushButton("🗑️")
        clear_values_btn.setMaximumWidth(40)
        clear_values_btn.clicked.connect(self._clear_value_table)
        values_header.addWidget(clear_values_btn)
        values_header.addStretch()
        
        values_layout.addLayout(values_header)
        
        # TABLE FOR VALUES - MAXIMIZED HEIGHT
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(1)
        self.values_table.setHorizontalHeaderLabels(["Value"])
        self.values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.values_table.setRowCount(20)  # Start with 20 rows
        self.values_table.setMinimumHeight(400)  # Use available space
        self.values_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 6px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Initialize empty cells
        for row in range(20):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.values_table.setItem(row, 0, item)
        
        values_layout.addWidget(self.values_table)
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

    def _add_value_rows(self, count):
        """Add more rows to value table"""
        current_rows = self.values_table.rowCount()
        self.values_table.setRowCount(current_rows + count)
        for row in range(current_rows, current_rows + count):
            item = QTableWidgetItem("")
            self.values_table.setItem(row, 0, item)

    def _clear_value_table(self):
        """Clear all values in table"""
        for row in range(self.values_table.rowCount()):
            self.values_table.setItem(row, 0, QTableWidgetItem(""))
    
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
        """Create scrollable area for element widgets - FIXED"""
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
        scroll.setMinimumHeight(250)  # Reduced from 400
        scroll.setMaximumHeight(350)  # Added maximum height
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        container = QWidget()
        self.elements_layout = QVBoxLayout()
        self.elements_layout.setSpacing(5)  # Reduced spacing
        self.elements_layout.setAlignment(Qt.AlignTop)
        self.elements_layout.setContentsMargins(5, 5, 5, 5)
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
    
    def _create_chart_type_selection(self, main_layout):
        """Create chart type selection - REPLACES extrapolation config"""
        group = QGroupBox("📊 Charts to Generate")
        group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                color: #2c3e50;
                border: 2px solid #17a2b8;
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
        layout.setSpacing(10)
        
        # Chart type selection with radio buttons
        self.chart_type_group = QButtonGroup()
        
        # I-MR Charts (default - for individual measurements)
        self.i_mr_radio = QRadioButton("I + MR Charts (Individual + Moving Range)")
        self.i_mr_radio.setChecked(True)
        self.i_mr_radio.setToolTip("For individual measurements - most common")
        self.chart_type_group.addButton(self.i_mr_radio)
        layout.addWidget(self.i_mr_radio)
        
        # X-R Charts (for subgroups)
        xr_container = QWidget()
        xr_layout = QHBoxLayout(xr_container)
        xr_layout.setContentsMargins(0, 0, 0, 0)
        
        self.xr_radio = QRadioButton("X̄-R Charts (Average + Range)")
        self.xr_radio.setToolTip("For subgroup data - requires group size")
        self.chart_type_group.addButton(self.xr_radio)
        xr_layout.addWidget(self.xr_radio)
        
        xr_layout.addWidget(QLabel("Group size:"))
        self.xr_group_size_spin = QSpinBox()
        self.xr_group_size_spin.setRange(2, 10)
        self.xr_group_size_spin.setValue(5)
        self.xr_group_size_spin.setEnabled(False)
        xr_layout.addWidget(self.xr_group_size_spin)
        xr_layout.addStretch()
        
        layout.addWidget(xr_container)
        
        # X-S Charts (for subgroups with std dev)
        xs_container = QWidget()
        xs_layout = QHBoxLayout(xs_container)
        xs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.xs_radio = QRadioButton("X̄-S Charts (Average + Std Dev)")
        self.xs_radio.setToolTip("For subgroup data - requires group size")
        self.chart_type_group.addButton(self.xs_radio)
        xs_layout.addWidget(self.xs_radio)
        
        xs_layout.addWidget(QLabel("Group size:"))
        self.xs_group_size_spin = QSpinBox()
        self.xs_group_size_spin.setRange(2, 10)
        self.xs_group_size_spin.setValue(5)
        self.xs_group_size_spin.setEnabled(False)
        xs_layout.addWidget(self.xs_group_size_spin)
        xs_layout.addStretch()
        
        layout.addWidget(xs_container)
        
        # Connect signals to enable/disable group size inputs
        self.i_mr_radio.toggled.connect(lambda checked: self._on_chart_type_changed())
        self.xr_radio.toggled.connect(lambda checked: self._on_chart_type_changed())
        self.xs_radio.toggled.connect(lambda checked: self._on_chart_type_changed())
        
        group.setLayout(layout)
        main_layout.addWidget(group)

    def _on_chart_type_changed(self):
        """Enable/disable group size inputs based on chart type"""
        self.xr_group_size_spin.setEnabled(self.xr_radio.isChecked())
        self.xs_group_size_spin.setEnabled(self.xs_radio.isChecked())
    
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
            instrument = self.instrument_combo.currentText()

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
            for row in range(self.values_table.rowCount()):
                item = self.values_table.item(row, 0)
                if item and item.text().strip():
                    try:
                        values.append(float(item.text().strip()))
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
            
            # Create element data with proper structure
            element_data = {
                'element_id': element_id,
                'cavity': cavity,
                'class': class_name,
                'sigma': sigma,
                'instrument': instrument,  # NEW
                'nominal': nominal,
                'tol_minus': tol_minus,
                'tol_plus': tol_plus,
                'values': values.copy(),
                'original_values': values.copy(),
                'has_extrapolation': False,
                'extrapolated_values': []
            }
            
            # Remove placeholder if present
            if self.elements_placeholder.parent():
                self.elements_placeholder.setParent(None)
            
            # Import the enhanced widget
            from .element_metrics_widget import ElementMetricsWidget
            
            # Create and add widget
            widget = ElementMetricsWidget(element_data, self)
            widget.removeRequested.connect(self._remove_element_widget)
            widget.metricsChanged.connect(self._on_metrics_changed)
            widget.valuesChanged.connect(self._on_values_changed)
            
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
            logger.error(f"Error adding element: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to add element: {e}")
    
    def _remove_element_widget(self, widget):
        """Remove an element widget"""
        if widget in self.element_widgets:
            self.element_widgets.remove(widget)
            
            # Remove from elements list
            for i, elem in enumerate(self.elements):
                if (elem['element_id'] == widget.element_data['element_id'] and 
                    elem['cavity'] == widget.element_data.get('cavity', '')):
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
        """Handle metrics changes from widget"""
        # Update the element data in the list
        for elem in self.elements:
            if elem['element_id'] == element_id:
                # FIXED: Ensure metrics exists and handle None case
                if elem.get('metrics') is None:
                    elem['metrics'] = {}
                elem['metrics'].update(metrics)
                break
        
        self._emit_summary_metrics()

    def _on_values_changed(self, element_id, values):
        """Handle value changes from widget"""
        # Update the element values in the list
        for elem in self.elements:
            if elem['element_id'] == element_id:
                elem['values'] = values.copy()
                logger.info(f"Updated values for {element_id}: {len(values)} values")
                break
    
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
            metrics = widget.metrics
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
        """Run the capability study - ABSOLUTELY FINAL FIX"""
        if not self.elements:
            QMessageBox.warning(self, "No Data", "Please add at least one element")
            return
        
        elements_data = []
        for widget in self.element_widgets:
            widget_data = widget.get_element_data()
            
            # Get all value arrays
            original_values = list(widget_data.get('original_values', []))
            extrapolated_values = list(widget_data.get('extrapolated_values', []))
            has_extrapolation = widget_data.get('has_extrapolation', False)
            
            # CRITICAL: Combine for study
            if has_extrapolation and len(extrapolated_values) > 0:
                all_values_for_study = original_values + extrapolated_values
            else:
                all_values_for_study = original_values
            
            logger.info(f"═══ STUDY PREP: {widget_data['element_id']} ═══")
            logger.info(f"  Original: {len(original_values)}")
            logger.info(f"  Extrapolated: {len(extrapolated_values)}")
            logger.info(f"  Total for study: {len(all_values_for_study)}")
            logger.info(f"  Has extrap flag: {has_extrapolation}")
            
            # Build complete element data
            element_study_data = {
                'element_id': widget_data['element_id'],
                'cavity': widget_data.get('cavity', ''),
                'class': widget_data.get('class', ''),
                'sigma': widget_data.get('sigma', '6σ'),
                'instrument': widget_data.get('instrument', '3D Scanner'),
                'nominal': widget_data['nominal'],
                'tol_minus': widget_data['tol_minus'],
                'tol_plus': widget_data['tol_plus'],
                'values': all_values_for_study,  # Combined values
                'has_extrapolation': has_extrapolation,
                'extrapolated_values': extrapolated_values,  # Separate for tracking
                'original_values': original_values,  # Separate for reference
                'metrics': widget_data.get('metrics')  # Custom metrics if edited
            }
            
            elements_data.append(element_study_data)
        
        # Get chart configuration
        chart_config = self.get_study_data()['chart_config']
        
        logger.info(f"═══ RUNNING STUDY ═══")
        logger.info(f"  Elements: {len(elements_data)}")
        logger.info(f"  Chart config: {chart_config}")
        
        self.study_requested.emit(elements_data, chart_config)

    def _on_element_data_changed(self, element_id, element_data):
        """Handle element data changes from child widgets"""
        # Find and update the element in our list
        for i, elem in enumerate(self.elements):
            if elem.get('element_id') == element_id:
                # Update with new data
                self.elements[i] = element_data
                logger.info(f"Parent updated element {element_id} data")
                logger.info(f"  has_extrapolation: {element_data.get('has_extrapolation')}")
                logger.info(f"  extrapolated_values: {len(element_data.get('extrapolated_values', []))}")
                break
    
    def _clear_inputs(self):
        """Clear input fields - FIXED for table"""
        if self.manual_radio.isChecked():
            self.element_name_input.clear()
        else:
            self.element_selector.setCurrentIndex(0)
        
        self.cavity_input.clear()
        self.class_input.clear()
        self.instrument_combo.setCurrentIndex(0)  # Reset to 3D Scanner
        self.nominal_input.clear()
        self.tol_minus_input.clear()
        self.tol_plus_input.clear()
        
        # Clear values table instead of values_inputs
        if hasattr(self, 'values_table'):
            for row in range(self.values_table.rowCount()):
                self.values_table.setItem(row, 0, QTableWidgetItem(""))
    
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
                
                # Fill values
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
        """Get all study data for session saving - FIXED"""
        elements_data = []
        for widget in self.element_widgets:
            widget_data = widget.get_element_data()
            
            # CRITICAL: Include all extrapolation data
            element_save_data = {
                'element_id': widget_data['element_id'],
                'cavity': widget_data.get('cavity', ''),
                'class': widget_data.get('class', ''),
                'sigma': widget_data.get('sigma', '6σ'),
                'nominal': widget_data['nominal'],
                'tol_minus': widget_data['tol_minus'],
                'tol_plus': widget_data['tol_plus'],
                'values': widget_data.get('values', []),
                'original_values': widget_data.get('original_values', []),  # CRITICAL
                'has_extrapolation': widget_data.get('has_extrapolation', False),  # CRITICAL
                'extrapolated_values': widget_data.get('extrapolated_values', []),  # CRITICAL
                'metrics': widget_data.get('metrics')  # CRITICAL
            }
            elements_data.append(element_save_data)
        
        # Get chart type configuration
        chart_config = {
            'type': 'i_mr',  # default
            'group_size': None
        }
        
        if hasattr(self, 'xr_radio') and self.xr_radio.isChecked():
            chart_config['type'] = 'xr'
            chart_config['group_size'] = self.xr_group_size_spin.value()
        elif hasattr(self, 'xs_radio') and self.xs_radio.isChecked():
            chart_config['type'] = 'xs'
            chart_config['group_size'] = self.xs_group_size_spin.value()
        
        return {
            'elements': elements_data,
            'chart_config': chart_config
        }
    
    def set_study_data(self, elements, extrapolation):
        """Load study data"""
        self.load_study_data({'elements': elements, 'extrapolation': extrapolation})
    
    def load_study_data(self, data):
        """Load study data from session - FIXED with instrument"""
        # Clear existing elements
        self.clear_all_elements()
        
        # Import the enhanced widget
        from .element_metrics_widget import ElementMetricsWidget
        
        # Load elements
        for elem_data in data.get('elements', []):
            # Remove placeholder if present
            if self.elements_placeholder.parent():
                self.elements_placeholder.setParent(None)
            
            # Ensure instrument field exists (for backward compatibility)
            if 'instrument' not in elem_data:
                elem_data['instrument'] = '3D Scanner'
            
            # Create and add widget
            widget = ElementMetricsWidget(elem_data, self)
            widget.removeRequested.connect(self._remove_element_widget)
            widget.metricsChanged.connect(self._on_metrics_changed)
            widget.valuesChanged.connect(self._on_values_changed)
            
            self.elements_layout.addWidget(widget)
            self.element_widgets.append(widget)
            self.elements.append(elem_data)
        
        # Load chart configuration
        chart_config = data.get('chart_config', {})
        if hasattr(self, 'i_mr_radio'):
            chart_type = chart_config.get('type', 'i_mr')
            
            if chart_type == 'i_mr':
                self.i_mr_radio.setChecked(True)
            elif chart_type == 'xr':
                self.xr_radio.setChecked(True)
                if 'group_size' in chart_config:
                    self.xr_group_size_spin.setValue(chart_config['group_size'])
            elif chart_type == 'xs':
                self.xs_radio.setChecked(True)
                if 'group_size' in chart_config:
                    self.xs_group_size_spin.setValue(chart_config['group_size'])
        
        self._emit_summary_metrics()