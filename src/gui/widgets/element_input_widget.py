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
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from src.gui.utils.element_input_styles import (
    get_element_input_styles,
    get_message_box_style,
)
from .buttons import ModernButton, ActionButton, CompactButton
from .inputs import ModernLineEdit, ModernComboBox


class ElementInputWidget(QWidget):
    # Signal that will be emitted when the study should be started
    study_requested = pyqtSignal(list, dict)  # Emits (elements, extrapolation_config)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.elements = []  # Llista per guardar els elements
        self.setStyleSheet(get_element_input_styles())
        self.init_ui()

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

        # Element ID
        basic_info_layout.addWidget(QLabel("Element ID:"), 0, 0)
        self.element_id_input = ModernLineEdit("Enter element identifier")
        basic_info_layout.addWidget(self.element_id_input, 0, 1)

        # Class
        basic_info_layout.addWidget(QLabel("Class:"), 0, 2)
        self.class_combo = ModernComboBox()
        self.class_combo.addItems(["CC", "SC", "IC", "None"])
        basic_info_layout.addWidget(self.class_combo, 0, 3)

        # Cavity
        basic_info_layout.addWidget(QLabel("Cavity:"), 1, 0)
        self.cavity_input = ModernLineEdit("Enter cavity information")
        basic_info_layout.addWidget(self.cavity_input, 1, 1)

        # Batch
        basic_info_layout.addWidget(QLabel("Batch (Optional):"), 1, 2)
        self.batch_input = ModernLineEdit("Enter batch number")
        basic_info_layout.addWidget(self.batch_input, 1, 3)

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

        # Table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Element ID",
                "Class",
                "Cavity",
                "Batch",
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

        # Set specific column widths
        self.table.setColumnWidth(0, 120)  # Element ID
        self.table.setColumnWidth(1, 40)  # Class
        self.table.setColumnWidth(2, 30)  # Cavity
        self.table.setColumnWidth(3, 80)  # Batch
        self.table.setColumnWidth(4, 70)  # Nominal
        self.table.setColumnWidth(5, 40)  # Tol. -
        self.table.setColumnWidth(6, 40)  # Tol. +
        self.table.setColumnWidth(7, 220)  # Measured Values
        self.table.setColumnWidth(8, 80)  # Actions

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def _create_extrapolation_config(self, main_layout):
        """Create the extrapolation configuration section"""
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

        # Extrapolation parameters frame
        self.extrap_params_frame = QFrame()
        self.extrap_params_frame.setObjectName("card")
        extrap_params_layout = QGridLayout(self.extrap_params_frame)
        extrap_params_layout.setSpacing(16)

        # Target sample size
        extrap_params_layout.addWidget(QLabel("Target Sample Size:"), 0, 0)
        self.target_size_combo = ModernComboBox()
        self.target_size_combo.addItems(["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "125", "150"])
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

        # Info label
        info_label = QLabel(
            "Extrapolation will extend the sample size to achieve the target statistical significance."
        )
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                font-style: italic;
                margin-top: 8px;
            }
        """)
        extrap_params_layout.addWidget(info_label, 2, 0, 1, 4)

        extrap_layout.addWidget(self.extrap_params_frame)
        main_layout.addWidget(extrap_group)

    def _create_action_buttons(self, main_layout):
        """Create the action buttons section"""
        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        main_layout.addWidget(separator)

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
        """Enable/disable extrapolation controls based on checkbox"""
        self.extrap_params_frame.setEnabled(enabled)
        self.target_size_combo.setEnabled(enabled)
        self.target_p_value.setEnabled(enabled)
        self.max_attempts.setEnabled(enabled)

    def add_element(self):
        # Validació i agregació
        element_id = self.element_id_input.text().strip()
        element_type = self.class_combo.currentText()
        cavity = self.cavity_input.text().strip()
        batch = self.batch_input.text().strip()
        nominal = self.nominal_input.text().strip()
        tol_minus = self.tol_minus_input.text().strip()
        tol_plus = self.tol_plus_input.text().strip()
        values = [inp.text().strip() for inp in self.values_inputs]

        # Validacions bàsiques
        if not element_id:
            self._show_error("Element ID cannot be empty.")
            return
        if not cavity:
            self._show_error("Cavity cannot be empty.")
            return
        try:
            nominal_f = float(nominal)
            tol_minus_f = float(tol_minus)
            tol_plus_f = float(tol_plus)
            values_f = [float(v) for v in values if v]
            if len(values_f) != 10:
                self._show_error("Please enter exactly 10 measured values.")
                return
        except ValueError:
            self._show_error("Please enter valid numeric values.")
            return

        # Afegim element a la llista
        element = {
            "element_id": element_id,
            "class": element_type,
            "cavity": cavity,
            "batch": batch,
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
        """Update the table with all elements"""
        self.table.setRowCount(len(self.elements))

        for row, element in enumerate(self.elements):
            self.table.setItem(row, 0, QTableWidgetItem(element["element_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(element["class"]))
            self.table.setItem(row, 2, QTableWidgetItem(element["cavity"]))
            self.table.setItem(row, 3, QTableWidgetItem(element["batch"]))
            self.table.setItem(row, 4, QTableWidgetItem(f"{element['nominal']:.3f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{element['tol_minus']:.3f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{element['tol_plus']:.3f}"))
            self.table.setItem(
                row,
                7,
                QTableWidgetItem(", ".join(f"{v:.3f}" for v in element["values"])),
            )

            # Delete button - Enhanced styling
            btn_delete = QPushButton("✕")
            btn_delete.setProperty("class", "remove-btn")
            btn_delete.setToolTip("Remove this element")
            btn_delete.clicked.connect(lambda _, r=row: self._remove_element(r))
            self.table.setCellWidget(row, 8, btn_delete)

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
        self.element_id_input.clear()
        self.cavity_input.clear()
        self.batch_input.clear()
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
