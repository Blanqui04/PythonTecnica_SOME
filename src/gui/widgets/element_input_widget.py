# src/gui/widgets/element_input_widget.py - FIXED VERSION
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFrame, QGridLayout, QScrollArea, QPushButton, 
    QCheckBox, QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QSplitter, QTabWidget, QTableWidgetItem, QComboBox, QTableWidget, QApplication
)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QObject, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence
from src.gui.utils.element_input_styles import get_element_input_styles
from ..utils.responsive_utils import ResponsiveWidget, ScreenUtils
from .buttons import ModernButton, CompactButton
from .inputs import ModernLineEdit, ModernComboBox
from src.services.measurement_history_service import MeasurementHistoryService
from .enhanced_features import (
    SearchHistoryManager,
    SearchHistoryDialog,
    MultiLOTComparisonDialog,
    ReferenceTemplateDialog,
    DimensionalTemplateByLotDialog
)
import logging
import math
from scipy import stats

logger = logging.getLogger(__name__)


class PasteableTableWidget(QTableWidget):
    """
    Custom QTableWidget that supports full clipboard operations:
    - Ctrl+C: Copy selected cells to clipboard
    - Ctrl+V: Paste from clipboard
    - Ctrl+X: Cut (copy and clear)
    - Delete/Backspace: Clear selected cells
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numeric_only = True  # Only accept numeric values
        self.decimal_places = 3
        
    def keyPressEvent(self, event):
        """Handle key press events for clipboard operations"""
        # Ctrl+C - Copy
        if event.matches(QKeySequence.Copy):
            self._copy_to_clipboard()
            return
            
        # Ctrl+V - Paste
        if event.matches(QKeySequence.Paste):
            self._paste_from_clipboard()
            return
        
        # Ctrl+X - Cut
        if event.matches(QKeySequence.Cut):
            self._copy_to_clipboard()
            self._clear_selected_cells()
            return
        
        # Ctrl+A - Select All
        if event.matches(QKeySequence.SelectAll):
            self.selectAll()
            return
        
        # Delete/Backspace - Clear
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self._clear_selected_cells()
            return
            
        super().keyPressEvent(event)
    
    def _copy_to_clipboard(self):
        """Copy selected cells to clipboard"""
        selected = self.selectedIndexes()
        if not selected:
            return
        
        # Get selection bounds
        rows = sorted(set(index.row() for index in selected))
        cols = sorted(set(index.column() for index in selected))
        
        # Build text matrix
        clipboard_text = []
        for row in rows:
            row_data = []
            for col in cols:
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            clipboard_text.append("\t".join(row_data))
        
        # Set clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(clipboard_text))
        
        logger.info(f"Copied {len(rows)} row(s) to clipboard")
    
    def _paste_from_clipboard(self):
        """Paste data from clipboard into table"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        # Split by newlines and tabs/commas
        lines = text.strip().split('\n')
        
        # Get current selection or start from row 0
        selected = self.selectedIndexes()
        if selected:
            start_row = min(idx.row() for idx in selected)
            start_col = min(idx.column() for idx in selected)
        else:
            start_row = 0
            start_col = 0
        
        # Paste values
        pasted_count = 0
        skipped_count = 0
        
        for row_offset, line in enumerate(lines):
            target_row = start_row + row_offset
            
            if target_row >= self.rowCount():
                # Add more rows if needed
                self.setRowCount(target_row + 10)
                for new_row in range(self.rowCount() - 10, self.rowCount()):
                    new_item = QTableWidgetItem("")
                    new_item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(new_row, 0, new_item)
            
            # Split by tab, comma, or semicolon (Excel/CSV compatibility)
            values = line.replace(';', '\t').replace(',', '\t').split('\t')
            
            for col_offset, value in enumerate(values):
                target_col = start_col + col_offset
                
                if target_col >= self.columnCount():
                    continue
                
                value = value.strip()
                
                if not value:
                    continue
                
                # Validate numeric if required
                if self.numeric_only:
                    try:
                        # Handle different decimal separators
                        numeric_val = float(value.replace(',', '.'))
                        value = f"{numeric_val:.{self.decimal_places}f}"
                    except ValueError:
                        skipped_count += 1
                        continue
                
                item = self.item(target_row, target_col)
                if not item:
                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(target_row, target_col, item)
                
                item.setText(value)
                pasted_count += 1
        
        if pasted_count > 0:
            message = f"Enganxats {pasted_count} valor(s)"
            if skipped_count > 0:
                message += f" ({skipped_count} valor(s) no numèric(s) omès(os))"
            logger.info(message)
            QMessageBox.information(
                self, 
                "Valors Enganxats", 
                message
            )
    
    def _clear_selected_cells(self):
        """Clear content of selected cells"""
        selected = self.selectedIndexes()
        for index in selected:
            item = self.item(index.row(), index.column())
            if item:
                item.setText("")


class ElementInputWidget(QWidget, ResponsiveWidget):
    study_requested = pyqtSignal(list, dict)
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, client=None, project_reference=None, batch_lot=None, machine='all'):
        QWidget.__init__(self, parent)
        ResponsiveWidget.__init__(self)
        self.elements = []
        self.element_widgets = []
        self.client = client
        self.project_reference = project_reference
        self.batch_lot = batch_lot
        self.machine = machine  # Selected machine for measurements
        
        # Initialize input collections
        self.values_inputs = []  # For compatibility with existing code
        self.values_layout = None  # Will be set during UI initialization
        self.measurement_limit = 10  # Default measurement limit
        
        # NEW: Initialize enhanced features
        self.search_history = SearchHistoryManager()
        
        self.setStyleSheet(get_element_input_styles())
        self.init_ui()
        
        # Apply responsive scaling
        self.apply_responsive_scaling()
        
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
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container widget for scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)
        
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
        
        # Machine selection
        machine_frame = QFrame()
        machine_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        machine_layout = QVBoxLayout(machine_frame)
        
        machine_label = QLabel("🔧 Màquina / Machine:")
        machine_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        machine_layout.addWidget(machine_label)
        
        self.machine_combo = ModernComboBox()
        # Get available machines from service
        from src.services.measurement_history_service import MeasurementHistoryService
        available_machines = MeasurementHistoryService.get_available_machines()
        for key, info in available_machines.items():
            self.machine_combo.addItem(info['name'], key)
        # Set default to 'all'
        default_index = self.machine_combo.findData('all')
        if default_index >= 0:
            self.machine_combo.setCurrentIndex(default_index)
        self.machine_combo.currentIndexChanged.connect(self._on_machine_changed)
        machine_layout.addWidget(self.machine_combo)
        
        layout.addWidget(machine_frame)
        
        # Element information section
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
            }
        """)
        info_layout = QGridLayout(self.info_frame)
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

        # Row 4: Measuring Instrument
        info_layout.addWidget(QLabel("Instrument:"), 3, 0)
        self.instrument_combo = ModernComboBox()
        self.instrument_combo.addItems([
            "3D Scanner",
            "Caliper",
            "Micrometer",
            "Projector",
            "CMM",
            "Radius gages",
            "Height Gauge",
            "Salt spray chamber",
            "Climatic chamber",
            "Microscope",
            "Dial comparator",
            "Plug gauge",
            "Thickness detector",
            "Traction Machine",
            "Hardness machine",
            "Vision system",
            "Torquemeter",
            "Threat gauge",
            "Other"
        ])
        self.instrument_combo.setCurrentIndex(0)  # Default to 3D Scanner
        self.instrument_combo.currentIndexChanged.connect(self._on_instrument_changed)
        info_layout.addWidget(self.instrument_combo, 3, 1, 1, 2)
        
        # Row 5: Nominal
        info_layout.addWidget(QLabel("Nominal:"), 4, 0)
        self.nominal_input = ModernLineEdit("0.0000")
        info_layout.addWidget(self.nominal_input, 4, 1, 1, 2)

        # Row 6: Tolerance + (with checkbox)
        tol_plus_layout = QHBoxLayout()
        self.tol_plus_check = QCheckBox("Tolerance +:")
        self.tol_plus_check.setChecked(True)  # Active by default
        self.tol_plus_check.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-weight: normal;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 2px solid #28a745;
            }
            QCheckBox::indicator:unchecked {
                background-color: #e9ecef;
                border: 2px solid #ced4da;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #218838;
                border: 2px solid #218838;
            }
        """)
        self.tol_plus_check.stateChanged.connect(self._toggle_tol_plus)
        tol_plus_layout.addWidget(self.tol_plus_check)
        info_layout.addLayout(tol_plus_layout, 5, 0)
        
        self.tol_plus_input = ModernLineEdit("+0.0000")
        info_layout.addWidget(self.tol_plus_input, 5, 1, 1, 2)

        # Row 7: Tolerance - (with checkbox)
        tol_minus_layout = QHBoxLayout()
        self.tol_minus_check = QCheckBox("Tolerance -:")
        self.tol_minus_check.setChecked(True)  # Active by default
        self.tol_minus_check.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-weight: normal;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 2px solid #28a745;
            }
            QCheckBox::indicator:unchecked {
                background-color: #e9ecef;
                border: 2px solid #ced4da;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #218838;
                border: 2px solid #218838;
            }
        """)
        self.tol_minus_check.stateChanged.connect(self._toggle_tol_minus)
        tol_minus_layout.addWidget(self.tol_minus_check)
        info_layout.addLayout(tol_minus_layout, 6, 0)
        
        self.tol_minus_input = ModernLineEdit("-0.0000")
        info_layout.addWidget(self.tol_minus_input, 6, 1, 1, 2)

        layout.addWidget(self.info_frame)
        
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
        
        # NEW: Search History button
        self.history_button = QPushButton("📜 History")
        self.history_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.history_button.clicked.connect(self._show_search_history)
        db_btn_layout.addWidget(self.history_button)
        
        # Measurement quantity selector
        db_btn_layout.addWidget(QLabel("Measurements:"))
        self.quantity_selector = QComboBox()
        self.quantity_selector.addItems(["5", "10", "15", "20", "All"])
        self.quantity_selector.setCurrentText("10")
        self.quantity_selector.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #80bdff;
            }
        """)
        self.quantity_selector.currentTextChanged.connect(self._on_quantity_changed)
        db_btn_layout.addWidget(self.quantity_selector)
        
        self.db_buttons_frame.hide()
        layout.addWidget(self.db_buttons_frame)
        
        # NEW: Advanced features buttons (second row)
        self.advanced_buttons_frame = QFrame()
        self.advanced_buttons_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        advanced_btn_layout = QHBoxLayout(self.advanced_buttons_frame)
        
        # Template button
        self.template_button = QPushButton("📋 Create Template")
        self.template_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.template_button.clicked.connect(self._create_reference_template)
        self.template_button.setEnabled(False)
        advanced_btn_layout.addWidget(self.template_button)
        
        # Multi-LOT comparison button
        self.compare_lots_button = QPushButton("📊 Compare LOTs")
        self.compare_lots_button.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8590c;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.compare_lots_button.clicked.connect(self._compare_multiple_lots)
        self.compare_lots_button.setEnabled(False)
        advanced_btn_layout.addWidget(self.compare_lots_button)
        
        advanced_btn_layout.addStretch()
        
        self.advanced_buttons_frame.hide()
        layout.addWidget(self.advanced_buttons_frame)
        
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
        self.values_layout = QVBoxLayout(values_frame)
        self.values_layout.setSpacing(5)
        
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
        
        self.values_layout.addLayout(values_header)
        
        # TABLE FOR VALUES - MAXIMIZED HEIGHT with Paste Support
        from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
        
        self.values_table = PasteableTableWidget()
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
        
        self.values_layout.addWidget(self.values_table)
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
        
        # Add form_group to scroll layout
        scroll_layout.addWidget(form_group)
        scroll_layout.addStretch()
        
        # Set scroll widget and add to main layout
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

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
        """Add value input fields (compatibility method)"""
        # This method is kept for compatibility but now works with the table
        current_rows = self.values_table.rowCount()
        required_rows = current_rows + count
        self.values_table.setRowCount(required_rows)
    
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
        
        # Force layout update to prevent overlapping/cut-off elements
        self.info_frame.layout().activate()
        self.info_frame.updateGeometry()
        self.updateGeometry()
        if self.parent():
            self.parent().updateGeometry()
        self.update()
    
    def _on_machine_changed(self):
        """Handle machine selection change"""
        # Get selected machine key from combo data
        selected_machine = self.machine_combo.currentData()
        if selected_machine:
            self.machine = selected_machine
            logger.info(f"Machine changed to: {self.machine_combo.currentText()} ({selected_machine})")
            
            # If in database mode, reload elements with new machine
            if self.database_radio.isChecked():
                # Clear current elements
                self.element_selector.clear()
                self.element_selector.addItem("Select an element...")
                # Notify user to reload
                logger.info("Machine changed. Please reload elements from database.")
    
    def _on_instrument_changed(self, index):
        """Handle instrument selection change - make editable when 'Other' is selected"""
        selected_text = self.instrument_combo.itemText(index)
        if selected_text == "Other":
            self.instrument_combo.setEditable(True)
            # Clear the text and set focus for immediate typing
            self.instrument_combo.setCurrentText("")
            self.instrument_combo.setFocus()
        else:
            self.instrument_combo.setEditable(False)
    
    def _toggle_tol_minus(self, state):
        """Enable/disable lower tolerance field"""
        is_checked = (state == 2)  # Qt.Checked = 2
        self.tol_minus_input.setEnabled(is_checked)
        
        # Visual feedback - change checkbox color and style
        if is_checked:
            self.tol_minus_check.setStyleSheet("""
                QCheckBox {
                    color: #2c3e50;
                    font-weight: normal;
                }
                QCheckBox::indicator:checked {
                    background-color: #28a745;
                    border: 2px solid #28a745;
                }
            """)
        else:
            self.tol_minus_input.setText("0.0000")
            self.tol_minus_check.setStyleSheet("""
                QCheckBox {
                    color: #6c757d;
                    font-weight: normal;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #e9ecef;
                    border: 2px solid #ced4da;
                }
            """)
    
    def _toggle_tol_plus(self, state):
        """Enable/disable upper tolerance field"""
        is_checked = (state == 2)  # Qt.Checked = 2
        self.tol_plus_input.setEnabled(is_checked)
        
        # Visual feedback - change checkbox color and style
        if is_checked:
            self.tol_plus_check.setStyleSheet("""
                QCheckBox {
                    color: #2c3e50;
                    font-weight: normal;
                }
                QCheckBox::indicator:checked {
                    background-color: #28a745;
                    border: 2px solid #28a745;
                }
            """)
        else:
            self.tol_plus_input.setText("0.0000")
            self.tol_plus_check.setStyleSheet("""
                QCheckBox {
                    color: #6c757d;
                    font-weight: normal;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #e9ecef;
                    border: 2px solid #ced4da;
                }
            """)
    
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

            # Validate tolerances based on selection
            try:
                nominal = float(self.nominal_input.text())
                
                # Get tolerance values based on checkbox state
                if self.tol_minus_check.isChecked():
                    tol_minus = float(self.tol_minus_input.text())
                else:
                    tol_minus = 0.0  # Lower tolerance not used
                
                if self.tol_plus_check.isChecked():
                    tol_plus = float(self.tol_plus_input.text())
                else:
                    tol_plus = 0.0  # Upper tolerance not used
                    
            except ValueError:
                QMessageBox.warning(self, "Invalid Data", "Nominal and active tolerances must be numbers")
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
            
            # Get tolerance type based on checkboxes
            tol_minus_active = self.tol_minus_check.isChecked()
            tol_plus_active = self.tol_plus_check.isChecked()
            
            if tol_minus_active and tol_plus_active:
                tolerance_type = 'both'
            elif tol_minus_active:
                tolerance_type = 'lower'
            elif tol_plus_active:
                tolerance_type = 'upper'
            else:
                QMessageBox.warning(self, "Invalid Data", "At least one tolerance must be active")
                return
            
            # Create element data with proper structure
            element_data = {
                'element_id': element_id,
                'cavity': cavity,
                'class': class_name,
                'sigma': sigma,
                'instrument': instrument,
                'nominal': nominal,
                'tol_minus': tol_minus,
                'tol_plus': tol_plus,
                'tolerance_type': tolerance_type,
                'tol_minus_active': tol_minus_active,
                'tol_plus_active': tol_plus_active,
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
        
        # Reset tolerance checkboxes to both active
        self.tol_minus_check.setChecked(True)
        self.tol_plus_check.setChecked(True)
        
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
            service = MeasurementHistoryService(machine=self.machine)
            elements = service.get_available_elements(
                self.client, self.project_reference, batch_lot=self.batch_lot
            )
            service.close()
            
            self.element_selector.clear()
            self.element_selector.addItem("Select an element...")
            
            # Store elements for later reference
            self.available_elements = elements
            
            for elem in elements:
                # Use 'element' field instead of 'element_id'
                element_name = elem.get('element', 'Unknown')
                property_name = elem.get('property', '')
                count = elem.get('count', 0)
                
                # Create descriptive display name
                display_name = f"{element_name}"
                if property_name and property_name != 'N/A':
                    display_name += f" ({property_name})"
                display_name += f" [{count} mesures]"
                
                self.element_selector.addItem(display_name)
            
            self.element_selector.setEnabled(True)
            self.load_data_button.setEnabled(True)
            
            # NEW: Enable advanced features and save to history
            self._enable_advanced_features()
            self._save_current_search()
            
            logger.info(f"Loaded {len(elements)} available elements")
            QMessageBox.information(
                self, "Success", 
                f"Loaded {len(elements)} elements from database"
            )
            
        except Exception as e:
            logger.error(f"Error loading elements: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load elements: {e}")
    
    def _on_quantity_changed(self, quantity_text):
        """Handle measurement quantity selection change"""
        if quantity_text == "All":
            self.measurement_limit = None  # No limit for "All"
        else:
            self.measurement_limit = int(quantity_text)
        logger.info(f"Measurement limit changed to: {self.measurement_limit}")
    
    def _load_element_data(self):
        """Load data for selected element"""
        selected_text = self.element_selector.currentText()
        if selected_text == "Select an element...":
            return
        
        try:
            # Find the selected element from stored data
            selected_element = None
            selected_index = self.element_selector.currentIndex() - 1  # -1 because first item is "Select..."
            
            if 0 <= selected_index < len(self.available_elements):
                selected_element = self.available_elements[selected_index]
                element_name = selected_element['element']
                property_name = selected_element.get('property', '')
                
                logger.info(f"Loading data for element: {element_name}, property: {property_name}")
                
                # Use the new specific element method
                service = MeasurementHistoryService(machine=self.machine)
                # Set limit based on selection (None for "All" means no limit)
                limit = self.measurement_limit if self.measurement_limit is not None else 10000
                filtered_measurements = service.get_element_measurements(
                    self.client, self.project_reference, 
                    element_name, property_name,
                    batch_lot=self.batch_lot,
                    limit=limit
                )
                service.close()
                
                if filtered_measurements:
                    # Auto-fill form with loaded data
                    first_measurement = filtered_measurements[0]
                    
                    # Use correct field names from the service
                    self.nominal_input.setText(str(first_measurement.get('nominal', '')))
                    
                    # Calculate tolerances from the data
                    tol_neg = first_measurement.get('tolerancia_negativa', '')
                    tol_pos = first_measurement.get('tolerancia_positiva', '')
                    self.tol_minus_input.setText(str(tol_neg) if tol_neg else '')
                    self.tol_plus_input.setText(str(tol_pos) if tol_pos else '')
                    
                    # Fill actual values in the table
                    values = []
                    for m in filtered_measurements:
                        actual_value = m.get('actual')
                        if actual_value is not None:
                            values.append(actual_value)
                    
                    if values:
                        # Clear existing table content
                        self.values_table.setRowCount(0)
                        
                        # Ensure we have enough rows
                        required_rows = max(len(values), 20)  # Minimum 20 rows
                        self.values_table.setRowCount(required_rows)
                        
                        # Fill the table with values
                        for i, value in enumerate(values):
                            item = QTableWidgetItem(str(value))
                            self.values_table.setItem(i, 0, item)
                        
                        requested_qty = "All" if self.measurement_limit is None else str(self.measurement_limit)
                        logger.info(f"Loaded {len(values)} measurements for {element_name}")
                        QMessageBox.information(
                            self, "Data Loaded", 
                            f"Loaded {len(values)} measurements for {element_name} ({property_name})\n"
                            f"Requested: {requested_qty} | Obtained: {len(values)}"
                        )
                    else:
                        QMessageBox.warning(self, "No Values", f"No actual values found for {element_name}")
                else:
                    QMessageBox.warning(self, "No Data", f"No measurements found for {element_name}")
                
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
    
    def apply_responsive_scaling(self):
        """Apply responsive scaling to the widget"""
        try:
            screen_utils = ScreenUtils()
            scale_factor = screen_utils.scale_factor
            
            # Apply scaling to fonts
            self.scale_fonts(scale_factor)
            
            # Apply scaling to spacing and margins
            self.scale_spacing_and_margins(scale_factor)
            
            # Apply scaling to minimum sizes
            self.scale_widget_sizes(scale_factor)
            
        except Exception as e:
            logger.warning(f"Could not apply responsive scaling: {e}")
    
    def scale_fonts(self, scale_factor):
        """Scale fonts based on screen size"""
        try:
            # Scale main widget font
            current_font = self.font()
            new_size = max(8, int(current_font.pointSize() * scale_factor))
            current_font.setPointSize(new_size)
            self.setFont(current_font)
            
            # Scale input field fonts
            for widget in self.findChildren(ModernLineEdit):
                font = widget.font()
                new_size = max(8, int(font.pointSize() * scale_factor))
                font.setPointSize(new_size)
                widget.setFont(font)
            
            # Scale button fonts  
            for widget in self.findChildren(ModernButton):
                font = widget.font()
                new_size = max(8, int(font.pointSize() * scale_factor))
                font.setPointSize(new_size)
                widget.setFont(font)
                
        except Exception as e:
            logger.warning(f"Could not scale fonts: {e}")
    
    def scale_spacing_and_margins(self, scale_factor):
        """Scale spacing and margins"""
        try:
            # Scale main layout margins
            if self.layout():
                margins = self.layout().contentsMargins()
                new_margins = [max(5, int(m * scale_factor)) for m in [margins.left(), margins.top(), margins.right(), margins.bottom()]]
                self.layout().setContentsMargins(*new_margins)
                
                # Scale spacing
                if hasattr(self.layout(), 'setSpacing'):
                    new_spacing = max(5, int(15 * scale_factor))
                    self.layout().setSpacing(new_spacing)
                    
        except Exception as e:
            logger.warning(f"Could not scale spacing: {e}")
    
    def scale_widget_sizes(self, scale_factor):
        """Scale widget minimum sizes"""
        try:
            # Scale minimum widget size
            min_width = max(400, int(600 * scale_factor))
            min_height = max(300, int(500 * scale_factor))
            self.setMinimumSize(min_width, min_height)
            
            # Scale input field sizes
            for widget in self.findChildren(ModernLineEdit):
                current_height = widget.minimumHeight()
                new_height = max(25, int(current_height * scale_factor))
                widget.setMinimumHeight(new_height)
                
        except Exception as e:
            logger.warning(f"Could not scale widget sizes: {e}")
    
    # ==================== NEW ENHANCED FEATURES ====================
    
    def _show_search_history(self):
        """Show search history dialog"""
        try:
            dialog = SearchHistoryDialog(self.search_history, self)
            dialog.search_selected.connect(self._apply_history_search)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing search history: {e}")
            QMessageBox.warning(self, "Error", f"Could not show search history: {e}")
    
    def _apply_history_search(self, search: dict):
        """Apply a search from history"""
        try:
            # Update input fields
            if search.get('client'):
                # Find and set client in combo or input
                pass  # Would need to update client input
            
            if search.get('reference'):
                # Set reference
                pass  # Would need to update reference input
            
            if search.get('lot'):
                # Set LOT
                pass  # Would need to update LOT input
            
            if search.get('machine'):
                # Set machine
                machine_key = search['machine']
                index = self.machine_combo.findData(machine_key)
                if index >= 0:
                    self.machine_combo.setCurrentIndex(index)
            
            QMessageBox.information(
                self,
                "Search Applied",
                f"Applied search: {search['client']} - {search['reference']}"
            )
            
        except Exception as e:
            logger.error(f"Error applying history search: {e}")
            QMessageBox.warning(self, "Error", f"Could not apply search: {e}")
    
    def _create_reference_template(self):
        """Create a template for reference-based analysis"""
        try:
            if not self.client or not self.project_reference:
                QMessageBox.warning(
                    self,
                    "Missing Information",
                    "Please load elements first (client and reference required)"
                )
                return
            
            dialog = ReferenceTemplateDialog(
                self.client,
                self.project_reference,
                self.machine,
                self
            )
            dialog.template_created.connect(self._apply_template)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            QMessageBox.warning(self, "Error", f"Could not create template: {e}")
    
    def _apply_template(self, template: dict):
        """Apply a template configuration"""
        try:
            logger.info(f"Applying template: {template['name']}")
            
            # Set machine
            machine_key = template['machine']
            index = self.machine_combo.findData(machine_key)
            if index >= 0:
                self.machine_combo.setCurrentIndex(index)
            
            # Load elements if configured
            if template['include_all_elements']:
                self._load_available_elements()
            
            # Handle LOT mode
            lot_mode = template.get('lot_mode')
            if lot_mode == "Compare multiple LOTs":
                # Trigger multi-LOT comparison
                self._compare_multiple_lots()
            
        except Exception as e:
            logger.error(f"Error applying template: {e}")
            QMessageBox.warning(self, "Error", f"Could not apply template: {e}")
    
    def _compare_multiple_lots(self):
        """Open multi-LOT comparison dialog"""
        try:
            if not self.client or not self.project_reference:
                QMessageBox.warning(
                    self,
                    "Missing Information",
                    "Please load elements first (client and reference required)"
                )
                return
            
            dialog = MultiLOTComparisonDialog(
                self.client,
                self.project_reference,
                self.machine,
                self
            )
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error opening multi-LOT comparison: {e}")
            QMessageBox.warning(self, "Error", f"Could not open comparison: {e}")
    
    def _enable_advanced_features(self):
        """Enable advanced feature buttons when data is loaded"""
        if self.client and self.project_reference:
            self.template_button.setEnabled(True)
            self.compare_lots_button.setEnabled(True)
            self.advanced_buttons_frame.show()
    
    def _save_current_search(self):
        """Save current search to history"""
        if self.client and self.project_reference:
            self.search_history.add_search(
                client=self.client,
                reference=self.project_reference,
                lot=self.batch_lot,
                machine=self.machine
            )