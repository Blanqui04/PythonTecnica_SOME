# src/gui/widgets/element_input_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QFrame,
    QGridLayout,
    QScrollArea,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QObject, pyqtSlot
from PyQt5.QtGui import QFont
from src.gui.utils.element_input_styles import (
    get_element_input_styles,
    get_message_box_style,
)
from .buttons import ModernButton, ActionButton, CompactButton
from .inputs import ModernLineEdit, ModernComboBox
from src.services.measurement_history_service import MeasurementHistoryService
import logging

logger = logging.getLogger(__name__)


class DatabaseSearchWorker(QObject):
    """Worker per cercar dades a la base de dades en background"""
    finished = pyqtSignal(list)  # Elements trobats
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, client, project_reference, batch_lot=None):
        super().__init__()
        self.client = client
        self.project_reference = project_reference
        self.batch_lot = batch_lot
    
    @pyqtSlot()
    def search_measurements(self):
        """Cerca les mesures a la base de dades"""
        try:
            service = MeasurementHistoryService()
            elements = service.get_measurement_history(self.client, self.project_reference, limit=10, batch_lot=self.batch_lot)
            service.close()
            self.finished.emit(elements)
        except Exception as e:
            logger.error(f"Error cercant mesures: {e}")
            self.error.emit(str(e))


class ElementDataSearchWorker(QObject):
    """Worker per cercar dades específiques d'un element a la base de dades"""
    finished = pyqtSignal(list)  # Registres trobats per l'element
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, client, project_reference, element_id, batch_lot=None, limit=10):
        super().__init__()
        self.client = client
        self.project_reference = project_reference
        self.element_id = element_id
        self.batch_lot = batch_lot
        self.limit = limit
    
    @pyqtSlot()
    def search_element_data(self):
        """Cerca les últimes N mesures d'un element específic"""
        try:
            service = MeasurementHistoryService()
            # Obtenir només les dades d'aquest element específic
            measurements = service.get_element_measurement_history(
                self.client, 
                self.project_reference, 
                self.element_id, 
                limit=self.limit,
                batch_lot=self.batch_lot
            )
            service.close()
            self.finished.emit(measurements)
        except Exception as e:
            logger.error(f"Error cercant dades per element {self.element_id}: {e}")
            self.error.emit(str(e))


class AvailableElementsWorker(QObject):
    """Worker per cercar elements disponibles a la base de dades"""
    finished = pyqtSignal(list)  # Elements disponibles trobats
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, client, project_reference, batch_lot=None):
        super().__init__()
        self.client = client
        self.project_reference = project_reference
        self.batch_lot = batch_lot
    
    @pyqtSlot()
    def search_available_elements(self):
        """Cerca tots els elements disponibles per client/projecte"""
        try:
            service = MeasurementHistoryService()
            elements = service.get_available_elements(self.client, self.project_reference, batch_lot=self.batch_lot)
            service.close()
            self.finished.emit(elements)
        except Exception as e:
            logger.error(f"Error cercant elements disponibles: {e}")
            self.error.emit(str(e))


class ElementInputWidget(QWidget):
    # Signal that will be emitted when the study should be started
    study_requested = pyqtSignal(list, dict)  # Emits (elements, extrapolation_config)

    def __init__(self, parent=None, client=None, project_reference=None, batch_lot=None):
        super().__init__(parent)
        self.elements = []  # Llista per guardar els elements
        self.client = client
        self.project_reference = project_reference
        self.batch_lot = batch_lot
        self.measurement_service = None
        
        # Separar workers per evitar conflictes
        self.elements_worker = None
        self.elements_thread = None
        self.data_worker = None
        self.data_thread = None
        
        self.setStyleSheet(get_element_input_styles())
        self.init_ui()
        
        # Habilitar botó Load Elements si tenim client i projecte
        if self.client and self.project_reference:
            self.load_elements_button.setEnabled(True)
            self.load_elements_button.setToolTip(f"Load elements for {self.client} - {self.project_reference}")

    def init_ui(self):
        # Create main scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Main content widget
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("Element Input & Capacity Study Configuration")
        header_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 10px;
                padding: 10px;
                background-color: #ffffff;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
            }
        """)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # --- Element Input Form ---
        self._create_element_input_form(main_layout)

        # --- Elements Table ---
        self._create_elements_table(main_layout)

        # --- Extrapolation Configuration ---
        self._create_extrapolation_config(main_layout)

        # --- Action Buttons ---
        self._create_action_buttons(main_layout)

        # Set up scroll area
        scroll_area.setWidget(content_widget)

        # Main widget layout
        widget_layout = QVBoxLayout(self)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(scroll_area)

    def _create_element_input_form(self, main_layout):
        """Create the element input form section"""
        form_group = QGroupBox("Element Configuration")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(16)

        # Basic Information Row
        basic_info_frame = QFrame()
        basic_info_frame.setObjectName("card")
        basic_info_layout = QGridLayout(basic_info_frame)
        basic_info_layout.setSpacing(16)

        # Element Selector
        basic_info_layout.addWidget(QLabel("Element:"), 0, 0)
        self.element_selector = ModernComboBox()
        self.element_selector.addItem("Select an element...")
        basic_info_layout.addWidget(self.element_selector, 0, 1)
        
        # Connect signal to enable/disable Load Data button
        self.element_selector.currentTextChanged.connect(self._on_element_selection_changed)
        
        # Load Elements Button (to populate the selector)
        self.load_elements_button = CompactButton("📋 Load Elements")
        self.load_elements_button.setToolTip("Load available elements for this client/project")
        self.load_elements_button.clicked.connect(self._load_available_elements)
        self.load_elements_button.setEnabled(False)  # Disabled until client/project available
        basic_info_layout.addWidget(self.load_elements_button, 0, 2)
        
        # Load Data Button
        self.load_data_button = CompactButton("🔄 Load Data")
        self.load_data_button.setToolTip("Load measurement data for selected element")
        self.load_data_button.clicked.connect(self._load_element_data)
        self.load_data_button.setEnabled(False)  # Disabled until element is selected
        basic_info_layout.addWidget(self.load_data_button, 0, 3)

        # Number of measurements selector
        basic_info_layout.addWidget(QLabel("Num. measures:"), 1, 2)
        self.num_measurements_combo = ModernComboBox()
        self.num_measurements_combo.addItems(["5", "10", "15", "20", "30", "50"])
        self.num_measurements_combo.setCurrentText("10")  # Default value
        self.num_measurements_combo.setToolTip("Number of latest measurements to load")
        basic_info_layout.addWidget(self.num_measurements_combo, 1, 3)

        # Class
        basic_info_layout.addWidget(QLabel("Class:"), 0, 4)
        self.class_combo = ModernComboBox()
        self.class_combo.addItems(["CC", "SC", "IC", "None"])
        basic_info_layout.addWidget(self.class_combo, 0, 5)

        # Cavity
        basic_info_layout.addWidget(QLabel("Cavity:"), 1, 0)
        self.cavity_input = ModernComboBox()
        self.cavity_input.addItems(["1", "2", "3", "4", ""])
        basic_info_layout.addWidget(self.cavity_input, 1, 1, 1, 1)  # Span 1 columns

        form_layout.addWidget(basic_info_frame)

        # Tolerances Row
        tolerance_frame = QFrame()
        tolerance_frame.setObjectName("card")
        tolerance_layout = QGridLayout(tolerance_frame)
        tolerance_layout.setSpacing(16)

        # Nominal Value
        tolerance_layout.addWidget(QLabel("Nominal Value:"), 0, 0)
        self.nominal_input = ModernLineEdit("0.000")
        tolerance_layout.addWidget(self.nominal_input, 0, 1)

        # Lower Tolerance
        tolerance_layout.addWidget(QLabel("Lower Tolerance:"), 0, 2)
        self.tol_minus_input = ModernLineEdit("-0.000")
        tolerance_layout.addWidget(self.tol_minus_input, 0, 3)

        # Upper Tolerance
        tolerance_layout.addWidget(QLabel("Upper Tolerance:"), 0, 4)
        self.tol_plus_input = ModernLineEdit("+0.000")
        tolerance_layout.addWidget(self.tol_plus_input, 0, 5)

        form_layout.addWidget(tolerance_frame)

        # Measured Values Section
        values_frame = QFrame()
        values_frame.setObjectName("card")
        values_layout = QVBoxLayout(values_frame)

        values_label = QLabel("Measured Values (10 required):")
        values_label.setStyleSheet("QLabel { font-weight: 600; margin-bottom: 8px; }")
        values_layout.addWidget(values_label)

        # Create grid for measured values
        values_grid = QGridLayout()
        values_grid.setSpacing(8)
        self.values_inputs = []

        for i in range(10):
            row = i // 5
            col = i % 5

            # Label for each input
            label = QLabel(f"Value {i + 1}:")
            label.setStyleSheet("QLabel { font-size: 9px; color: #7f8c8d; }")
            values_grid.addWidget(label, row * 2, col)

            # Input field
            inp = ModernLineEdit("0.000")
            inp.setMinimumWidth(80)
            inp.setMaximumWidth(120)
            self.values_inputs.append(inp)
            values_grid.addWidget(inp, row * 2 + 1, col)

        values_layout.addLayout(values_grid)
        form_layout.addWidget(values_frame)

        # Add Element Button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.add_button = ActionButton("Add Element")
        self.add_button.clicked.connect(self.add_element)
        button_layout.addWidget(self.add_button)

        button_layout.addStretch()
        form_layout.addLayout(button_layout)

        main_layout.addWidget(form_group)

    def _create_elements_table(self, main_layout):
        """Create the elements table section"""
        table_group = QGroupBox("Added Elements")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(16)

        # Table - Updated to remove Batch column and emphasize Cavity
        self.table = QTableWidget(0, 8)  # Reduced from 9 to 8 columns
        self.table.setHorizontalHeaderLabels(
            [
                "Element ID",
                "Cavity",  # Moved to second position for emphasis
                "Class",
                "Nominal",
                "Tol. -",
                "Tol. +",
                "Measured Values",
                "Actions",
            ]
        )

        # Set table properties
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMinimumHeight(400)

        # Set specific column widths - updated for new layout
        self.table.setColumnWidth(0, 120)  # Element ID
        self.table.setColumnWidth(1, 60)   # Cavity (emphasized)
        self.table.setColumnWidth(2, 40)   # Class
        self.table.setColumnWidth(3, 70)   # Nominal
        self.table.setColumnWidth(4, 40)   # Tol. -
        self.table.setColumnWidth(5, 40)   # Tol. +
        self.table.setColumnWidth(6, 250)  # Measured Values (increased width)
        self.table.setColumnWidth(7, 80)   # Actions

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def _create_extrapolation_config(self, main_layout):
        """Create the extrapolation configuration section - UPDATED with real values option"""
        extrap_group = QGroupBox("Extrapolation Configuration")
        extrap_layout = QVBoxLayout(extrap_group)
        extrap_layout.setSpacing(16)

        # Enable extrapolation checkbox
        checkbox_layout = QHBoxLayout()
        self.enable_extrapolation = QCheckBox("Enable Extrapolation Analysis")
        self.enable_extrapolation.setChecked(True)
        self.enable_extrapolation.toggled.connect(self.toggle_extrapolation_controls)
        checkbox_layout.addWidget(self.enable_extrapolation)
        checkbox_layout.addStretch()
        extrap_layout.addLayout(checkbox_layout)

        # NEW: Real values option
        real_values_layout = QHBoxLayout()
        self.use_real_values = QCheckBox("Use Real Values (when > 10 samples)")
        self.use_real_values.setChecked(False)
        self.use_real_values.setToolTip(
            "When enabled and real sample size > 10, use actual measured values instead of extrapolating"
        )
        self.use_real_values.toggled.connect(self.toggle_real_values_option)
        real_values_layout.addWidget(self.use_real_values)
        real_values_layout.addStretch()
        extrap_layout.addLayout(real_values_layout)

        # Extrapolation parameters frame
        self.extrap_params_frame = QFrame()
        self.extrap_params_frame.setObjectName("card")
        extrap_params_layout = QGridLayout(self.extrap_params_frame)
        extrap_params_layout.setSpacing(16)

        # Target sample size
        extrap_params_layout.addWidget(QLabel("Target Sample Size:"), 0, 0)
        self.target_size_combo = ModernComboBox()
        self.target_size_combo.addItems(
            ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "125", "150"]
        )
        self.target_size_combo.setCurrentText("100")
        extrap_params_layout.addWidget(self.target_size_combo, 0, 1)

        # Target p-value
        extrap_params_layout.addWidget(QLabel("Target P-Value:"), 0, 2)
        self.target_p_value = QDoubleSpinBox()
        self.target_p_value.setRange(0.01, 0.99)
        self.target_p_value.setSingleStep(0.01)
        self.target_p_value.setValue(0.05)
        self.target_p_value.setDecimals(2)
        extrap_params_layout.addWidget(self.target_p_value, 0, 3)

        # Max attempts
        extrap_params_layout.addWidget(QLabel("Maximum Attempts:"), 1, 0)
        self.max_attempts = QSpinBox()
        self.max_attempts.setRange(10, 1000)
        self.max_attempts.setValue(20)
        extrap_params_layout.addWidget(self.max_attempts, 1, 1)

        # Info label - updated
        self.info_label = QLabel(
            "Extrapolation will extend the sample size to achieve the target statistical significance."
        )
        self.info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                font-style: italic;
                margin-top: 8px;
            }
        """)
        extrap_params_layout.addWidget(self.info_label, 2, 0, 1, 4)

        extrap_layout.addWidget(self.extrap_params_frame)
        main_layout.addWidget(extrap_group)

    def _create_action_buttons(self, main_layout):
        """Create the action buttons section"""
        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        main_layout.addWidget(separator)

        # Auto-load section (només si tenim dades de client i projecte)
        if self.client and self.project_reference:
            auto_load_group = QGroupBox("Database Auto-Load")
            auto_load_layout = QVBoxLayout(auto_load_group)
            
            # Info label - updated to show batch comes from main window
            batch_info = " | Batch: From main window" if self.batch_lot else ""
            info_label = QLabel(f"Client: {self.client} | Project: {self.project_reference}{batch_info}")
            info_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-weight: 600;
                    font-size: 11px;
                    margin-bottom: 8px;
                }
            """)
            auto_load_layout.addWidget(info_label)
            
            # Auto-load button
            auto_load_btn_layout = QHBoxLayout()
            self.auto_load_btn = ActionButton("🔄 Load Latest Measurements")
            self.auto_load_btn.clicked.connect(self.manual_load_database_measurements)
            auto_load_btn_layout.addWidget(self.auto_load_btn)
            auto_load_btn_layout.addStretch()
            
            auto_load_layout.addLayout(auto_load_btn_layout)
            main_layout.addWidget(auto_load_group)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)

        # Clear all button
        clear_button = CompactButton("Clear All")
        clear_button.clicked.connect(self.clear_all_elements)
        button_layout.addWidget(clear_button)

        button_layout.addStretch()

        # Run study button
        self.run_button = ModernButton("Start Capacity Study", primary=True)
        self.run_button.clicked.connect(self.run_study)
        self.run_button.setMinimumHeight(52)
        self.run_button.setFont(QFont("Segoe UI", 11, QFont.Medium))
        button_layout.addWidget(self.run_button)

        main_layout.addLayout(button_layout)

    def toggle_extrapolation_controls(self, enabled):
        """Toggle extrapolation controls based on checkbox state"""
        self.extrap_params_frame.setEnabled(enabled)
        if not enabled:
            self.use_real_values.setEnabled(False)
            self.use_real_values.setChecked(False)
        else:
            self.use_real_values.setEnabled(True)

    def toggle_real_values_option(self, enabled):
        """Toggle between real values and extrapolation"""
        if enabled:
            # Disable extrapolation parameters when using real values
            for i in range(self.extrap_params_frame.layout().count()):
                widget = self.extrap_params_frame.layout().itemAt(i).widget()
                if widget and not isinstance(widget, QLabel):
                    widget.setEnabled(False)
            
            self.info_label.setText(
                "Real measured values will be used when sample size > 10 (no extrapolation performed)."
            )
        else:
            # Enable extrapolation parameters
            for i in range(self.extrap_params_frame.layout().count()):
                widget = self.extrap_params_frame.layout().itemAt(i).widget()
                if widget and not isinstance(widget, QLabel):
                    widget.setEnabled(True)
                    
            self.info_label.setText(
                "Extrapolation will extend the sample size to achieve the target statistical significance."
            )

    def add_element(self):
        # Validació i agregació
        # Obtenir element seleccionat del selector
        selected_element = self.element_selector.currentText()
        if selected_element == "Select an element...":
            element_id = ""
        else:
            # Extreure el nom de l'element (abans del primer ' - ')
            element_id = selected_element.split(' - ')[0] if ' - ' in selected_element else selected_element.split(' (')[0]
        
        element_type = self.class_combo.currentText()
        cavity = self.cavity_input.currentText()
        nominal = self.nominal_input.text().strip()
        tol_minus = self.tol_minus_input.text().strip()
        tol_plus = self.tol_plus_input.text().strip()
        values = [inp.text().strip() for inp in self.values_inputs]

        # Validacions bàsiques - Enhanced cavity validation
        if not element_id:
            self._show_error("Element ID cannot be empty.")
            return
        if not cavity:
            self._show_error("Cavity is required. This field identifies the specific dimension being analyzed.")
            return
        
        # Check for duplicate element_id + cavity combination
        for existing_element in self.elements:
            if (existing_element["element_id"] == element_id and 
                existing_element["cavity"] == cavity):
                self._show_error(f"Element '{element_id}' with cavity '{cavity}' already exists. Each element-cavity combination must be unique.")
                return
        
        try:
            nominal_f = float(nominal)
            tol_minus_f = float(tol_minus)
            tol_plus_f = float(tol_plus)
            values_f = [float(v) for v in values if v]
            if len(values_f) != 10:
                self._show_error("Please enter a minimum of 10 measured values.")
                return
        except ValueError:
            self._show_error("Please enter valid numeric values.")
            return

        # Afegim element a la llista - Updated structure without batch
        element = {
            "element_id": element_id,
            "cavity": cavity,  # Cavity as key identifier
            "class": element_type,
            "nominal": nominal_f,
            "tol_minus": tol_minus_f,
            "tol_plus": tol_plus_f,
            "values": values_f,
        }
        self.elements.append(element)

        # Actualitzar taula
        self._update_table()

        # Netejar inputs
        self._clear_inputs()

    def _update_table(self):
        """Update the table with all elements - Updated for new column structure"""
        self.table.setRowCount(len(self.elements))

        for row, element in enumerate(self.elements):
            self.table.setItem(row, 0, QTableWidgetItem(element["element_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(element["cavity"]))  # Cavity now in column 1
            self.table.setItem(row, 2, QTableWidgetItem(element["class"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{element['nominal']:.3f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{element['tol_minus']:.3f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{element['tol_plus']:.3f}"))
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(", ".join(f"{v:.3f}" for v in element["values"])),
            )

            # Delete button - Enhanced styling
            btn_delete = QPushButton("✕")
            btn_delete.setProperty("class", "remove-btn")
            btn_delete.setToolTip("Remove this element")
            btn_delete.clicked.connect(lambda _, r=row: self._remove_element(r))
            self.table.setCellWidget(row, 7, btn_delete)  # Updated column index

    def _remove_element(self, row):
        """Remove element and update table"""
        if 0 <= row < len(self.elements):
            del self.elements[row]
            self._update_table()

    def clear_all_elements(self):
        """Clear all elements from the table"""
        if self.elements:
            reply = self._show_question(
                "Clear All Elements",
                "Are you sure you want to remove all elements?",
                "This action cannot be undone.",
            )
            if reply == QMessageBox.Yes:
                self.elements.clear()
                self._update_table()

    def _clear_inputs(self):
        """Clear all input fields"""
        self.element_selector.setCurrentIndex(0)  # Reset to "Select an element..."
        # FIX: Don't clear the cavity combo, just reset selection to empty
        self.cavity_input.setCurrentText("")  # Reset to empty selection instead of clearing all items
        self.nominal_input.clear()
        self.tol_minus_input.clear()
        self.tol_plus_input.clear()
        for inp in self.values_inputs:
            inp.clear()

    def _show_error(self, title, message="", details=""):
        """Show error message with enhanced styling"""
        if not message:
            message = title
            title = "Input Error"

        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        if details:
            error_box.setInformativeText(details)
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.setStyleSheet(get_message_box_style("error"))
        error_box.exec_()

    def _show_warning(self, title, message, details=""):
        """Show warning message with enhanced styling"""
        warning_box = QMessageBox(self)
        warning_box.setIcon(QMessageBox.Warning)
        warning_box.setWindowTitle(title)
        warning_box.setText(message)
        if details:
            warning_box.setInformativeText(details)
        warning_box.setStandardButtons(QMessageBox.Ok)
        warning_box.setStyleSheet(get_message_box_style("warning"))
        warning_box.exec_()

    def _show_question(self, title, message, details=""):
        """Show question dialog with enhanced styling"""
        question_box = QMessageBox(self)
        question_box.setIcon(QMessageBox.Question)
        question_box.setWindowTitle(title)
        question_box.setText(message)
        if details:
            question_box.setInformativeText(details)
        question_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        question_box.setDefaultButton(QMessageBox.No)
        question_box.setStyleSheet(get_message_box_style("question"))
        return question_box.exec_()

    def _show_info(self, title, message, details=""):
        """Show info message with enhanced styling"""
        info_box = QMessageBox(self)
        info_box.setIcon(QMessageBox.Information)
        info_box.setWindowTitle(title)
        info_box.setText(message)
        if details:
            info_box.setInformativeText(details)
        info_box.setStandardButtons(QMessageBox.Ok)
        info_box.setStyleSheet(get_message_box_style("info"))
        info_box.exec_()

    def get_extrapolation_config(self):
        """Get the extrapolation configuration from GUI"""
        if not self.enable_extrapolation.isChecked():
            return {"include_extrapolation": False, "extrapolation_config": None}

        return {
            "include_extrapolation": True,
            "extrapolation_config": {
                "target_size": int(self.target_size_combo.currentText()),
                "target_p_value": self.target_p_value.value(),
                "max_attempts": self.max_attempts.value(),
            },
        }

    def run_study(self):
        """Emit signal to request study execution"""
        if not self.elements:
            self._show_error("No elements have been added to the study.")
            return

        # Get extrapolation configuration
        extrap_config = self.get_extrapolation_config()

        # Emit the signal with the elements list and extrapolation config
        self.study_requested.emit(self.elements, extrap_config)

    def _on_element_selection_changed(self, selected_text):
        """Activar/desactivar botó Load Data quan canvia la selecció d'element"""
        is_valid_selection = bool(selected_text and selected_text != "Select an element...")
        has_context = bool(self.client and self.project_reference)
        self.load_data_button.setEnabled(is_valid_selection and has_context)
        
        # Update tooltip based on state
        if not is_valid_selection:
            self.load_data_button.setToolTip("Select an element first")
        elif not has_context:
            self.load_data_button.setToolTip("Client and Project Reference required")
        else:
            self.load_data_button.setToolTip(f"Load data for element '{selected_text}'")

    def _load_available_elements(self):
        """Carrega la llista d'elements disponibles per al client/projecte"""
        if not self.client or not self.project_reference:
            self._show_warning(
                "Missing Information", 
                "Client and Project Reference are required to load available elements."
            )
            return
            
        logger.info(f"Carregant elements disponibles per Client: {self.client}, Projecte: {self.project_reference}")
        
        # Neteja workers anteriors d'elements si existeixen
        if self.elements_worker:
            try:
                self.elements_worker.deleteLater()
            except RuntimeError:
                # Worker ja ha estat eliminat
                pass
            
        if self.elements_thread:
            try:
                if self.elements_thread.isRunning():
                    self.elements_thread.quit()
                    self.elements_thread.wait()
            except RuntimeError:
                # Thread ja ha estat eliminat
                pass
            
        # Crear nous workers per elements
        self.elements_thread = QThread()
        self.elements_worker = AvailableElementsWorker(self.client, self.project_reference, self.batch_lot)
        self.elements_worker.moveToThread(self.elements_thread)
        
        # Connections
        self.elements_thread.started.connect(self.elements_worker.search_available_elements)
        self.elements_worker.finished.connect(self._on_available_elements_loaded)
        self.elements_worker.error.connect(self._on_database_search_error)
        self.elements_worker.finished.connect(self.elements_thread.quit)
        self.elements_worker.finished.connect(self.elements_worker.deleteLater)
        self.elements_thread.finished.connect(self.elements_thread.deleteLater)
        
        # Disable button and start
        self.load_elements_button.setEnabled(False)
        self.load_elements_button.setText("Loading...")
        self.elements_thread.start()

    def _load_element_data(self):
        """Carrega les dades específiques de l'element seleccionat"""
        selected_element = self.element_selector.currentText()
        
        if not selected_element or selected_element == "Select an element...":
            self._show_warning("Missing Element", "Please select an element first.")
            return
            
        if not self.client or not self.project_reference:
            self._show_warning(
                "Missing Information", 
                "Client and Project Reference are required to load element data."
            )
            return
        
        # Obtenir l'ID complet de l'element del userData
        element_id = self.element_selector.currentData()
        if not element_id:
            self._show_error("Element ID Error", "Could not retrieve element ID. Please reload elements list.")
            return
        
        # Obtenir el nombre de mesures seleccionat
        num_measurements = int(self.num_measurements_combo.currentText())
            
        logger.info(f"Carregant {num_measurements} mesures per Element ID: {element_id}, Client: {self.client}, Projecte: {self.project_reference}")
        
        # Neteja workers anteriors de dades si existeixen
        if self.data_worker:
            try:
                self.data_worker.deleteLater()
            except RuntimeError:
                # Worker ja ha estat eliminat
                pass
            
        if self.data_thread:
            try:
                if self.data_thread.isRunning():
                    self.data_thread.quit()
                    self.data_thread.wait()
            except RuntimeError:
                # Thread ja ha estat eliminat
                pass
            
        # Crear nous workers per dades
        self.data_thread = QThread()
        self.data_worker = ElementDataSearchWorker(self.client, self.project_reference, element_id, self.batch_lot, num_measurements)
        self.data_worker.moveToThread(self.data_thread)
        
        # Connections
        self.data_thread.started.connect(self.data_worker.search_element_data)
        self.data_worker.finished.connect(self._on_element_data_loaded)
        self.data_worker.error.connect(self._on_database_search_error)
        self.data_worker.finished.connect(self.data_thread.quit)
        self.data_worker.finished.connect(self.data_worker.deleteLater)
        self.data_thread.finished.connect(self.data_thread.deleteLater)
        
        # Disable button and start
        self.load_data_button.setEnabled(False)
        self.load_data_button.setText("Loading...")
        self.data_thread.start()

    def auto_load_database_measurements(self):
        """Carrega automàticament les mesures de la base de dades al iniciar"""
        if not self.client or not self.project_reference:
            logger.warning("No es pot carregar automàticament: falten dades del client o projecte")
            return
            
        logger.info(f"Auto-carregant mesures per Client: {self.client}, Projecte: {self.project_reference}")
        self._start_database_search()

    def manual_load_database_measurements(self):
        """Carrega manualment les mesures quan es prem el botó"""
        if not self.client or not self.project_reference:
            self._show_warning(
                "Missing Information",
                "Client and Project Reference are required to load measurements from database."
            )
            return
            
        # Preguntar si vol esborrar els elements existents
        if self.elements:
            reply = self._show_question(
                "Load Database Measurements",
                "Do you want to replace existing elements with database measurements?",
                "This will clear all current elements and load the latest measurements from the database."
            )
            if reply != QMessageBox.Yes:
                return
        
        self._start_database_search()

    def _start_database_search(self):
        """Inicia la cerca a la base de dades en background"""
        try:
            # Desactivar botó durant la cerca
            if hasattr(self, 'auto_load_btn'):
                self.auto_load_btn.setText("🔄 Loading...")
                self.auto_load_btn.setEnabled(False)
            
            # Crear worker i thread
            self.search_thread = QThread()
            self.search_worker = DatabaseSearchWorker(self.client, self.project_reference, self.batch_lot)
            self.search_worker.moveToThread(self.search_thread)
            
            # Connectar signals
            self.search_thread.started.connect(self.search_worker.search_measurements)
            self.search_worker.finished.connect(self._on_database_search_finished)
            self.search_worker.error.connect(self._on_database_search_error)
            self.search_worker.finished.connect(self.search_thread.quit)
            self.search_worker.finished.connect(self.search_worker.deleteLater)
            self.search_thread.finished.connect(self.search_thread.deleteLater)
            
            # Iniciar thread
            self.search_thread.start()
            
        except Exception as e:
            logger.error(f"Error iniciant cerca a la base de dades: {e}")
            self._show_error("Database Search Error", f"Could not start database search: {e}")
            self._reset_load_button()

    def _on_database_search_finished(self, elements):
        """Gestiona els resultats de la cerca a la base de dades"""
        try:
            self._reset_load_button()
            
            if not elements:
                self._show_info(
                    "Database Search Complete",
                    "No measurements found in database for this client and project reference.",
                    "You can add elements manually using the form above."
                )
                return
            
            # Esborrar elements existents
            self.elements.clear()
            
            # Convertir elements de la base de dades al format del widget
            for db_element in elements:
                try:
                    # Validar que tenim suficients mesures
                    measurements = db_element.get('measurements', [])
                    if len(measurements) < 10:
                        # Completar amb valors nominals si no hi ha suficients mesures
                        nominal = db_element.get('nominal', 0.0)
                        measurements.extend([nominal] * (10 - len(measurements)))
                    
                    # Prendre només les primeres 10 mesures
                    measurements = measurements[:10]
                    
                    element = {
                        "element_id": db_element.get('element_id', 'Unknown'),
                        "cavity": db_element.get('cavity', ''),  # Include cavity from database
                        "class": "CC",  # Valor per defecte
                        "nominal": db_element.get('nominal', 0.0),
                        "tol_minus": db_element.get('tolerance_minus', 0.0),
                        "tol_plus": db_element.get('tolerance_plus', 0.0),
                        "values": measurements
                    }
                    
                    self.elements.append(element)
                    
                except Exception as e:
                    logger.warning(f"Error processant element {db_element}: {e}")
                    continue
            
            # Actualitzar taula
            self._update_table()
            
            # Mostrar missatge d'èxit amb més detalls
            total_measurements = sum(len(elem.get('measurements', [])) for elem in elements)
            info_text = f"Successfully loaded {len(self.elements)} elements from database.\n\n"
            info_text += f"Total measurements loaded: {total_measurements}\n"
            info_text += f"Source: {self.client} - {self.project_reference}\n\n"
            info_text += "Elements loaded:\n"
            for elem in self.elements[:5]:  # Mostrar només els primers 5
                info_text += f"• {elem['element_id']} - Cavity: {elem['cavity']} (Nominal: {elem['nominal']:.3f})\n"
            if len(self.elements) > 5:
                info_text += f"• ... and {len(self.elements) - 5} more elements"
            
            self._show_info(
                "Database Load Complete",
                info_text
            )
            
            logger.info(f"S'han carregat {len(self.elements)} elements des de la base de dades")
            
        except Exception as e:
            logger.error(f"Error processant resultats de la base de dades: {e}")
            self._show_error("Database Processing Error", f"Error processing database results: {e}")

    def _on_database_search_error(self, error_message):
        """Gestiona errors de la cerca a la base de dades"""
        self._reset_load_button()
        logger.error(f"Error en la cerca a la base de dades: {error_message}")
        self._show_error(
            "Database Search Error",
            "Could not load measurements from database.",
            f"Error details: {error_message}"
        )

    def _on_available_elements_loaded(self, elements):
        """Gestiona els elements disponibles carregats"""
        try:
            self._reset_load_elements_button()
            
            if not elements:
                self._show_info(
                    "No Elements Found",
                    f"No elements found for {self.client} - {self.project_reference}"
                )
                return
            
            # Neteja el selector i afegeix els nous elements
            self.element_selector.clear()
            self.element_selector.addItem("Select an element...")
            
            # Afegir elements ordenats
            for element_data in sorted(elements, key=lambda x: x['element']):
                # Construir l'ID complet per l'element
                element_id = f"{element_data['element']}|{element_data['pieza']}|{element_data['datum']}|{element_data['property']}"
                count = element_data['count']
                
                # Mostrar informació més detallada de l'element
                display_text = f"{element_data['element']} - {element_data['datum']} ({count} measurements)"
                
                # Guardar l'ID complet com userData
                self.element_selector.addItem(display_text, element_id)
            
            self._show_info(
                "Elements Loaded",
                f"Found {len(elements)} elements for {self.client} - {self.project_reference}"
            )
            
            logger.info(f"Carregats {len(elements)} elements al selector")
            
        except Exception as e:
            logger.error(f"Error processant elements disponibles: {e}")
            self._show_error("Elements Processing Error", f"Error processing available elements: {e}")

    def _on_element_data_loaded(self, measurements):
        """Gestiona les dades carregades d'un element específic"""
        try:
            self._reset_element_load_button()
            
            if not measurements:
                selected_element = self.element_selector.currentText()
                element_name = selected_element.split(' - ')[0] if ' - ' in selected_element else selected_element.split(' (')[0]
                self._show_info(
                    "No Data Found",
                    f"No measurement data found for element '{element_name}'"
                )
                return
            
            # Mostrar informació de les dades trobades
            element_id = measurements[0]['element']
            datum = measurements[0]['datum']
            num_requested = int(self.num_measurements_combo.currentText())
            
            self._show_info(
                "Data Loaded",
                f"Found {len(measurements)} measurements for element '{element_id} - {datum}'\n"
                f"Latest measurement: {measurements[0]['data_hora']}\n"
                f"Value: {measurements[0]['valor_mesura']}\n"
                f"Nominal: {measurements[0]['nominal']}\n"
                f"Tolerance: -{measurements[0]['tol_neg']} / +{measurements[0]['tol_pos']}\n"
                f"Requested: {num_requested}, Available: {len(measurements)}"
            )
            
            # Auto-poblar els camps amb les dades de la primera mesura (més recent)
            latest_measurement = measurements[0]
            
            # Setear valors als camps corresponents
            self.nominal_input.setText(str(latest_measurement['nominal']))
            self.tol_minus_input.setText(str(latest_measurement['tol_neg']))  # Ja és positiu des del servei
            self.tol_plus_input.setText(str(latest_measurement['tol_pos']))
            
            # Si hi ha camps de cavitat, també els podem omplir
            if latest_measurement.get('cavitat'):
                self.cavity_input.setCurrentText(latest_measurement['cavitat'])
            
            # Omplir els camps de valors amb les mesures obtingudes
            measurement_values = [m['valor_mesura'] for m in measurements]
            
            # Assegurar-se que tenim els 10 camps per als valors
            for i in range(10):
                if i < len(measurement_values):
                    self.values_inputs[i].setText(str(measurement_values[i]))
                else:
                    self.values_inputs[i].setText("")
            
            # Si tenim més de 10 mesures, mostrar avís
            if len(measurement_values) > 10:
                self._show_info(
                    "Data Loaded", 
                    f"Only the first 10 measurements have been loaded into the form.\n"
                    f"Total measurements available: {len(measurement_values)}"
                )
            
            logger.info(f"Dades carregades per element {element_id}: {len(measurements)} mesures")
            
        except Exception as e:
            logger.error(f"Error processant dades de l'element: {e}")
            import traceback
            logger.error(f"Traceback complet: {traceback.format_exc()}")
            self._show_error("Data Processing Error", f"Error processing element data: {e}")

    def _reset_load_button(self):
        """Restaura l'estat del botó de càrrega"""
        if hasattr(self, 'auto_load_btn'):
            self.auto_load_btn.setText("🔄 Load Latest Measurements")
            self.auto_load_btn.setEnabled(True)

    def _reset_element_load_button(self):
        """Restaura l'estat del botó Load Data"""
        self.load_data_button.setText("🔄 Load Data")
        selected_element = self.element_selector.currentText()
        is_valid_selection = bool(selected_element and selected_element != "Select an element...")
        has_context = bool(self.client and self.project_reference)
        self.load_data_button.setEnabled(is_valid_selection and has_context)

    def _reset_load_elements_button(self):
        """Restaura l'estat del botó Load Elements"""
        self.load_elements_button.setText("📋 Load Elements")
        has_context = bool(self.client and self.project_reference)
        self.load_elements_button.setEnabled(has_context)

    def set_client_and_project(self, client, project_reference):
        """Estableix el client i la referència del projecte"""
        self.client = client
        self.project_reference = project_reference
        
        # Si ja està inicialitzat, auto-carregar dades
        if hasattr(self, 'auto_load_btn'):
            self.auto_load_database_measurements()