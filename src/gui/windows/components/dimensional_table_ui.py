# src/gui/windows/components/dimensional_table_ui.py - FIXED CONSISTENT OPERATIONS
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QTextEdit,
    QComboBox,
    QTabWidget,
    QAbstractItemView,
    QMenu,
    QDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import sip  # type: ignore

from src.models.dimensional.gdt_interpreter import GDTInterpreter


class DimensionalTableUI:
    """Enhanced UI components with FIXED consistent formatting operations"""

    def __init__(
        self,
        display_columns,
        column_headers,
        required_columns,
        measurement_columns,
        batch_number,
    ):
        self.parent_window = None
        self.display_columns = display_columns
        self.column_headers = column_headers
        self.required_columns = required_columns
        self.measurement_columns = measurement_columns
        self.batch_number = batch_number
        self.results_tabs = QTabWidget()
        self._copied_row_data = None
        self._original_measurements = {}

        # Ensure process capability columns are included
        self._ensure_process_capability_columns()

        # UI Options
        self.class_options = ["", "CC", "SC", "IC"]
        self.instrument_options = [
            "",
            "3D Scanbox",
            "CMM",
            "Visual",
            "Caliper",
            "Micrometer",
            "Vision System",
            "Laser Scanner",
            "Optical Comparator",
            "Height Gauge",
            "Pin Gauge",
            "Thread Gauge",
            "Go/No-Go Gauge",
            "Surface Roughness Tester",
            "Hardness Tester",
            "Coordinate Measuring Arm",
            "Portable CMM",
            "Profile Projector",
        ]
        self.force_status_options = ["AUTO", "GOOD", "BAD", "T.E.D."]
        self.unit_options = ["", "mm", "°", "μm", "cm", "in"]
        self.datum_options = ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        self.evaluation_options = ["Normal", "Basic", "Informative", "Note", "GD&T"]

        # Enhanced UI Colors
        self.colors = {
            "good": QColor(46, 125, 50),        # Strong green
            "bad": QColor(183, 28, 28),         # Strong red
            "warning": QColor(255, 152, 0),     # Strong orange
            "readonly": QColor(240, 242, 245),  # Light gray for calculated fields
            "header": QColor(44, 62, 80),       # Dark blue-gray
            "primary": QColor(21, 101, 192),    # Strong blue
            "white": QColor(255, 255, 255),     # White
            "black": QColor(33, 37, 41),        # Strong black
            "text_dark": QColor(40, 44, 52),    # Dark text
            "process_capability": QColor(138, 43, 226),  # Purple for Pp/Ppk
            "to_check": QColor(255, 193, 7),    # Yellow/orange for TO CHECK
        }

    def _ensure_process_capability_columns(self):
        """Ensure Pp and Ppk columns are included in display columns"""
        if "pp" not in self.display_columns:
            std_idx = 20 if len(self.display_columns) > 20 else len(self.display_columns)
            self.display_columns.insert(std_idx + 1, "pp")
            self.display_columns.insert(std_idx + 2, "ppk")
            
        if "ppk" not in self.display_columns and "pp" in self.display_columns:
            pp_idx = self.display_columns.index("pp")
            self.display_columns.insert(pp_idx + 1, "ppk")

        # Update headers accordingly
        expected_headers = [
            "Element ID", "Batch", "Cavity", "Class", "Description",
            "Measuring Instrument", "Unit", "Datum", "Evaluation Type",
            "Nominal", "Lower Tolerance", "Upper Tolerance",
            "Measurement 1", "Measurement 2", "Measurement 3", "Measurement 4", "Measurement 5",
            "Minimum", "Maximum", "Mean", "Std Deviation", "Pp", "Ppk", "Status", "Force Status"
        ]
        
        if len(self.column_headers) != len(self.display_columns):
            self.column_headers = expected_headers[:len(self.display_columns)]

    def set_parent_window(self, parent):
        self.parent_window = parent

    def _log_message(self, message: str, level: str = "INFO"):
        """Delegate logging to parent window if available"""
        if self.parent_window and hasattr(self.parent_window, "_log_message"):
            self.parent_window._log_message(message, level)
        else:
            print(f"[{level}] {message}")

    def _create_results_table(self) -> QTableWidget:
        """Create enhanced results table with process capability columns"""
        table = QTableWidget()
        table.setColumnCount(len(self.display_columns))
        table.setHorizontalHeaderLabels(self.column_headers)

        # Enhanced table configuration
        table.setSortingEnabled(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(table, pos)
        )
        
        # Enhanced header styling with process capability highlight
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ffffff;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #1a252f;
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                font-family: 'Segoe UI', sans-serif;
            }
            QHeaderView::section:hover {
                background-color: #1a252f;
            }
        """)

        # Enhanced column widths including Pp/Ppk
        column_widths = {
            0: 70,   # element_id
            1: 60,   # batch
            2: 50,   # cavity
            3: 45,   # class
            4: 180,  # description
            5: 85,   # measuring_instrument
            6: 45,   # unit
            7: 50,   # datum
            8: 75,   # evaluation_type
            9: 65,   # nominal
            10: 70,  # lower_tolerance
            11: 70,  # upper_tolerance
            12: 65,  # measurement_1
            13: 65,  # measurement_2
            14: 65,  # measurement_3
            15: 65,  # measurement_4
            16: 65,  # measurement_5
            17: 55,  # minimum
            18: 55,  # maximum
            19: 55,  # mean
            20: 55,  # std_deviation
            21: 50,  # pp
            22: 50,  # ppk
            23: 70,  # status
            24: 80,  # force_status
        }

        for col, width in column_widths.items():
            if col < table.columnCount():
                table.setColumnWidth(col, width)

        # Set consistent row height
        table.verticalHeader().setDefaultSectionSize(32)
        table.setWordWrap(True)
        table.cellChanged.connect(self._on_cell_changed)
        
        # Set default font
        table_font = QFont("Segoe UI", 9)
        table.setFont(table_font)
        
        return table

    def _populate_default_row(self, table: QTableWidget, row: int):
        """FIXED: Populate row with consistent defaults and styling"""
        # Set basic defaults
        defaults = {
            0: self._get_next_element_id(table),  # Auto-increment element_id
            1: str(self.batch_number),  # batch
            2: "1",  # cavity (default to 1)
            6: "mm",  # default unit
            8: "Normal",  # default evaluation type
        }

        # Columns that should be centered
        centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]
        # Columns that should be bold (nominal and tolerances)
        bold_columns = [9, 10, 11]

        # Create items for regular columns first
        for col in range(len(self.display_columns)):
            # Skip dropdown columns - they'll be handled separately
            if col in [3, 5, 6, 7, 8, 24]:
                continue
                
            # Skip calculated columns - they'll be handled separately
            if col in [17, 18, 19, 20, 21, 22, 23]:
                continue
            
            # Get default value
            value = defaults.get(col, "")
            item = QTableWidgetItem(str(value))
            
            # Apply styling consistently
            self._apply_standard_cell_style(item, col, centered_columns, bold_columns)
            table.setItem(row, col, item)

        # Add dropdowns with consistent styling
        self._add_dropdowns(table, row)

        # Add calculated columns with consistent read-only styling
        self._add_calculated_columns(table, row, centered_columns)

    def _apply_standard_cell_style(self, item: QTableWidgetItem, col: int, centered_columns: list, bold_columns: list):
        """Apply consistent styling to standard cells"""
        # Apply centering for specific columns
        if col in centered_columns:
            item.setTextAlignment(Qt.AlignCenter)
        
        # Apply font styling
        if col in bold_columns:
            font = QFont("Segoe UI", 9, QFont.Bold)
        else:
            font = QFont("Segoe UI", 9)
        
        item.setFont(font)
        item.setForeground(self.colors["text_dark"])

    def _add_calculated_columns(self, table: QTableWidget, row: int, centered_columns: list):
        """Add calculated columns with consistent read-only styling"""
        calculated_cols = [17, 18, 19, 20, 21, 22, 23]  # min, max, mean, std, pp, ppk, status
        
        for col in calculated_cols:
            item = QTableWidgetItem("")
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            
            # Apply consistent styling based on column type
            if col == 23:  # Status column
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item.setForeground(self.colors["text_dark"])
            elif col in [21, 22]:  # Pp, Ppk columns - special styling
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(248, 240, 255))  # Light purple background
                item.setForeground(self.colors["process_capability"])
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:  # Other calculated columns (min, max, mean, std)
                if col in centered_columns:
                    item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(self.colors["readonly"])
                item.setForeground(self.colors["text_dark"])
                item.setFont(QFont("Segoe UI", 9))  # Regular font, not bold
            
            table.setItem(row, col, item)

    def _add_dropdowns(self, table: QTableWidget, row: int):
        """Add professional dropdown widgets with consistent styling"""
        dropdown_style = self._get_combo_style()

        # Class dropdown (column 3)
        class_combo = QComboBox()
        class_combo.addItems(self.class_options)
        class_combo.setCurrentText("")
        class_combo.setStyleSheet(dropdown_style)
        class_combo.setMaximumHeight(30)
        table.setCellWidget(row, 3, class_combo)

        # Measuring instrument dropdown (column 5)
        instrument_combo = QComboBox()
        instrument_combo.addItems(self.instrument_options)
        instrument_combo.setCurrentText("3D Scanbox")
        instrument_combo.setStyleSheet(dropdown_style)
        instrument_combo.setMaximumHeight(30)
        table.setCellWidget(row, 5, instrument_combo)

        # Unit dropdown (column 6)
        unit_combo = QComboBox()
        unit_combo.addItems(self.unit_options)
        unit_combo.setCurrentText("mm")
        unit_combo.setStyleSheet(dropdown_style)
        unit_combo.setMaximumHeight(30)
        table.setCellWidget(row, 6, unit_combo)

        # Datum dropdown (column 7)
        datum_combo = QComboBox()
        datum_combo.addItems(self.datum_options)
        datum_combo.setCurrentText("")
        datum_combo.setStyleSheet(dropdown_style)
        datum_combo.setMaximumHeight(30)
        table.setCellWidget(row, 7, datum_combo)

        # Evaluation type dropdown (column 8)
        eval_combo = QComboBox()
        eval_combo.addItems(self.evaluation_options)
        eval_combo.setCurrentText("Normal")
        eval_combo.setStyleSheet(dropdown_style)
        eval_combo.setMaximumHeight(30)
        table.setCellWidget(row, 8, eval_combo)

        # Force status dropdown (column 24)
        force_combo = QComboBox()
        force_combo.addItems(self.force_status_options)
        force_combo.setCurrentText("AUTO")
        force_combo.setStyleSheet(dropdown_style)
        force_combo.setMaximumHeight(30)
        table.setCellWidget(row, 24, force_combo)

    def _get_combo_style(self) -> str:
        """Enhanced combobox styling"""
        return """
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 6px;
                color: #495057;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10px;
                max-height: 20px;
                min-height: 10px;
            }
            QComboBox:hover {
                border-color: #3498db;
                background-color: #f8feff;
            }
            QComboBox:focus {
                border-color: #3498db;
                border-width: 2px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #ced4da;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                width: 8px;
                height: 8px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIgM0w1IDZMOCAzIiBzdHJva2U9IiM2Yzc1N2QiIHN0cm9rZS13aWR0aD0iMS4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                outline: none;
                font-size: 10px;
            }
        """

    def _duplicate_row(self, table: QTableWidget):
        """FIXED: Enhanced duplicate row with consistent formatting"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self.parent_window, "No Selection", "Please select a row to duplicate."
            )
            return

        # Get row data including dropdown values
        row_data = {}
        dropdown_data = {}
        
        for col in range(table.columnCount()):
            cell_widget = table.cellWidget(current_row, col)
            if isinstance(cell_widget, QComboBox):
                dropdown_data[col] = cell_widget.currentText()
            else:
                item = table.item(current_row, col)
                row_data[col] = item.text() if item else ""

        new_row = table.rowCount()
        table.insertRow(new_row)

        # Disable updates during batch operation
        table.setUpdatesEnabled(False)

        try:
            # Apply consistent formatting like _populate_default_row
            centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]
            bold_columns = [9, 10, 11]

            for col in range(len(self.display_columns)):
                if col >= table.columnCount():
                    break
                    
                if col == 0:  # Generate new element_id
                    item = QTableWidgetItem(self._get_next_element_id(table))
                    self._apply_standard_cell_style(item, col, centered_columns, bold_columns)
                    table.setItem(new_row, col, item)
                elif col in [3, 5, 6, 7, 8, 24]:  # Dropdown columns
                    self._create_dropdown_for_column(table, new_row, col, dropdown_data.get(col, ""))
                elif col in [17, 18, 19, 20, 21, 22, 23]:  # Calculated columns
                    item = QTableWidgetItem("")
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    
                    # Apply consistent calculated column styling
                    if col == 23:  # Status column
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                        item.setForeground(self.colors["text_dark"])
                    elif col in [21, 22]:  # Pp, Ppk columns
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor(248, 240, 255))  # Light purple
                        item.setForeground(self.colors["process_capability"])
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    else:  # Other calculated columns
                        if col in centered_columns:
                            item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(self.colors["readonly"])
                        item.setForeground(self.colors["text_dark"])
                        item.setFont(QFont("Segoe UI", 9))  # Regular font, not bold
                        
                    table.setItem(new_row, col, item)
                else:  # Regular input columns
                    value = row_data.get(col, "")
                    item = QTableWidgetItem(str(value))
                    self._apply_standard_cell_style(item, col, centered_columns, bold_columns)
                    table.setItem(new_row, col, item)

        finally:
            table.setUpdatesEnabled(True)

        self._mark_unsaved_changes()

    def _create_dropdown_for_column(self, table: QTableWidget, row: int, col: int, value: str):
        """FIXED: Helper to create dropdown for specific column with proper styling"""
        dropdown_style = self._get_combo_style()
        combo = None
        
        if col == 3:  # class
            combo = QComboBox()
            combo.addItems(self.class_options)
            combo.setCurrentText(value if value in self.class_options else "")
        elif col == 5:  # measuring_instrument
            combo = QComboBox()
            combo.addItems(self.instrument_options)
            combo.setCurrentText(value if value in self.instrument_options else "3D Scanbox")
        elif col == 6:  # unit
            combo = QComboBox()
            combo.addItems(self.unit_options)
            combo.setCurrentText(value if value in self.unit_options else "mm")
        elif col == 7:  # datum
            combo = QComboBox()
            combo.addItems(self.datum_options)
            combo.setCurrentText(value if value in self.datum_options else "")
        elif col == 8:  # evaluation_type
            combo = QComboBox()
            combo.addItems(self.evaluation_options)
            combo.setCurrentText(value if value in self.evaluation_options else "Normal")
        elif col == 24:  # force_status
            combo = QComboBox()
            combo.addItems(self.force_status_options)
            combo.setCurrentText(value if value in self.force_status_options else "AUTO")
        
        if combo:
            combo.setStyleSheet(dropdown_style)
            combo.setMaximumHeight(30)
            table.setCellWidget(row, col, combo)

    def _copy_row(self, table: QTableWidget):
        """FIXED: Enhanced copy row with complete data capture"""
        current_row = table.currentRow()
        if current_row < 0:
            return

        # Capture complete row data
        row_data = {"regular_cells": {}, "dropdown_cells": {}}
        
        for col in range(table.columnCount()):
            cell_widget = table.cellWidget(current_row, col)
            if isinstance(cell_widget, QComboBox):
                row_data["dropdown_cells"][col] = cell_widget.currentText()
            else:
                item = table.item(current_row, col)
                row_data["regular_cells"][col] = item.text() if item else ""
        
        # Store complete row information
        self._copied_row_data = {
            "data": row_data,
            "column_count": table.columnCount(),
            "source_element_id": row_data["regular_cells"].get(0, "Unknown")
        }
        
        if self.parent_window:
            element_id = row_data["regular_cells"].get(0, f"Row {current_row + 1}")
            self.parent_window._log_message(f"📋 Copied {element_id}")

    def _paste_row(self, table: QTableWidget):
        """FIXED: Enhanced paste row with consistent formatting restoration"""
        if not hasattr(self, "_copied_row_data") or not self._copied_row_data:
            QMessageBox.information(
                self.parent_window, "No Data", "No row data copied."
            )
            return

        current_row = table.currentRow()
        if current_row < 0:
            return

        copied_data = self._copied_row_data["data"]
        
        # Batch update - disable table updates for performance
        table.setUpdatesEnabled(False)
        
        try:
            # Apply consistent formatting
            centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]
            bold_columns = [9, 10, 11]
            
            for col in range(min(table.columnCount(), self._copied_row_data["column_count"])):
                # Skip calculated columns (they should remain empty)
                if col in [17, 18, 19, 20, 21, 22, 23]:
                    continue
                    
                if col in [3, 5, 6, 7, 8, 24]:  # Dropdown columns
                    dropdown_value = copied_data["dropdown_cells"].get(col, "")
                    cell_widget = table.cellWidget(current_row, col)
                    if isinstance(cell_widget, QComboBox):
                        # Check if value exists in combobox
                        items = [cell_widget.itemText(i) for i in range(cell_widget.count())]
                        if dropdown_value in items:
                            cell_widget.setCurrentText(dropdown_value)
                        else:
                            # Set to appropriate default
                            defaults = {
                                5: "3D Scanbox",  # measuring_instrument
                                6: "mm",          # unit
                                8: "Normal",      # evaluation_type
                                24: "AUTO"        # force_status
                            }
                            cell_widget.setCurrentText(defaults.get(col, items[0] if items else ""))
                else:  # Regular cells
                    cell_value = copied_data["regular_cells"].get(col, "")
                    item = table.item(current_row, col)
                    if not item:
                        item = QTableWidgetItem()
                        table.setItem(current_row, col, item)
                    
                    item.setText(str(cell_value))
                    # Apply consistent styling
                    self._apply_standard_cell_style(item, col, centered_columns, bold_columns)
        
        finally:
            # Re-enable updates and refresh
            table.setUpdatesEnabled(True)
            table.viewport().update()

        self._mark_unsaved_changes()
        if self.parent_window:
            source_id = self._copied_row_data.get("source_element_id", "Unknown")
            self.parent_window._log_message(f"📋 Pasted data from {source_id} to row {current_row + 1}")

    def _clear_calculated_columns(self, table: QTableWidget, row: int):
        """FIXED: Clear calculated columns with consistent styling"""
        calculated_cols = [17, 18, 19, 20, 21, 22, 23]  # min, max, mean, std, pp, ppk, status
        centered_columns = [17, 18, 19, 20, 21, 22, 23]

        self._log_message(f"🧹 CLEARING calculated columns for row {row + 1}", "INFO")

        for col in calculated_cols:
            item = table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col, item)

            # Clear the text
            item.setText("")
            
            # Apply consistent styling based on column type
            if col == 23:  # status column - CLEAR STYLING COMPLETELY
                item.setData(Qt.BackgroundRole, None)
                item.setData(Qt.ForegroundRole, None)
                item.setData(Qt.FontRole, None)
                item.setData(Qt.ToolTipRole, None)
                item.setBackground(QColor())
                item.setForeground(self.colors["text_dark"])
                item.setToolTip("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            elif col in [21, 22]:  # Pp, Ppk columns - consistent special styling
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(248, 240, 255))  # Light purple
                item.setForeground(self.colors["process_capability"])
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:  # Other statistics columns
                if col in centered_columns:
                    item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(self.colors["readonly"])
                item.setForeground(self.colors["text_dark"])
                item.setFont(QFont("Segoe UI", 9))  # Regular font, not bold

        # Force table update
        table.viewport().update()

    def _on_cell_changed(self, row: int, col: int):
        """Enhanced cell change handler with consistent formatting"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

        current_table = (
            self.parent_window.results_tabs.currentWidget()
            if self.parent_window
            else None
        )
        if not isinstance(current_table, QTableWidget):
            return

        item = current_table.item(row, col)
        if item:
            # Check if measurement column was cleared/modified
            if col in [12, 13, 14, 15, 16]:  # measurement columns
                self._log_message(
                    f"📝 Measurement column {col} changed in row {row + 1}: '{item.text()}'",
                    "DEBUG",
                )

                # Check if all measurements are empty
                all_measurements_empty = True
                for meas_col in [12, 13, 14, 15, 16]:
                    meas_item = current_table.item(row, meas_col)
                    if meas_item and meas_item.text().strip():
                        all_measurements_empty = False
                        break

                # If all measurements are empty, clear calculated columns
                if all_measurements_empty:
                    self._log_message(
                        "🧹 All measurements empty - clearing calculated columns",
                        "INFO",
                    )
                    self._clear_calculated_columns(current_table, row)
                    return

            # Auto-formatting for numeric columns
            if col in [9, 10, 11, 12, 13, 14, 15, 16]:  # nominal, tolerances, measurements
                try:
                    if item.text().strip():
                        value = float(item.text())
                        formatted = f"{value:.3f}"
                        if item.text() != formatted:
                            item.setText(formatted)
                except ValueError:
                    self._log_message(f"⚠️ Invalid numeric value in row {row + 1}, col {col}: '{item.text()}'", "WARNING")

    def _get_next_element_id(self, table: QTableWidget) -> str:
        """Generate sequential element_id based on existing data"""
        highest_number = 0
        
        # Check current table
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.text().strip():
                try:
                    text = item.text().strip()
                    if "º" in text:
                        number_part = text.split("º")[1]
                        number = int(number_part)
                        highest_number = max(highest_number, number)
                except (ValueError, IndexError):
                    pass
        
        # Check other tabs
        if self.parent_window and hasattr(self.parent_window, "results_tabs"):
            for tab_idx in range(self.parent_window.results_tabs.count()):
                tab_table = self.parent_window.results_tabs.widget(tab_idx)
                if isinstance(tab_table, QTableWidget) and tab_table != table:
                    for row in range(tab_table.rowCount()):
                        item = tab_table.item(row, 0)
                        if item and item.text().strip():
                            try:
                                text = item.text().strip()
                                if "º" in text:
                                    number_part = text.split("º")[1]
                                    number = int(number_part)
                                    highest_number = max(highest_number, number)
                            except (ValueError, IndexError):
                                pass
        
        # Generate next ID
        next_number = highest_number + 1
        return f"Nº{next_number:03d}"

    def _show_context_menu(self, table: QTableWidget, position):
        """Enhanced context menu with process capability info"""
        if not self.parent_window.manual_mode:
            return

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
                color: #2c3e50;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ecf0f1;
                margin: 4px 8px;
            }
        """)

        # Menu actions
        add_row_action = menu.addAction("➕ Add Row")
        add_row_action.triggered.connect(self._add_manual_row)
        duplicate_row_action = menu.addAction("📋 Duplicate Row")
        duplicate_row_action.triggered.connect(lambda: self._duplicate_row(table))
        delete_row_action = menu.addAction("🗑️ Delete Row")
        delete_row_action.triggered.connect(lambda: self._delete_row(table))
        menu.addSeparator()
        apply_gdt_action = menu.addAction("⚙️ Apply GD&T")
        apply_gdt_action.triggered.connect(lambda: self._show_gdt_helper(table))
        menu.addSeparator()
        copy_action = menu.addAction("📄 Copy Row")
        copy_action.triggered.connect(lambda: self._copy_row(table))
        paste_action = menu.addAction("📋 Paste Row")
        paste_action.triggered.connect(lambda: self._paste_row(table))

        menu.exec_(table.mapToGlobal(position))

    def _delete_row(self, table: QTableWidget):
        """Enhanced delete row with confirmation"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self.parent_window, "No Selection", "Please select a row to delete."
            )
            return

        # Get element ID for confirmation
        element_item = table.item(current_row, 0)
        element_id = element_item.text() if element_item else f"Row {current_row + 1}"

        reply = QMessageBox.question(
            self.parent_window,
            "Confirm Delete",
            f"Are you sure you want to delete {element_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            table.removeRow(current_row)
            self._mark_unsaved_changes()
            if self.parent_window:
                self.parent_window._log_message(f"Deleted {element_id}")

    def _show_gdt_helper(self, table: QTableWidget):
        """Enhanced GD&T helper dialog"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self.parent_window, "No Selection", "Please select a row first."
            )
            return

        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("🔧 GD&T Helper")
        dialog.setModal(True)
        dialog.resize(450, 350)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #495057;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        layout = QVBoxLayout()

        # Enhanced instructions
        instructions = QLabel("""
        <div style='background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;'>
        <h3 style='color: #2c3e50; margin-top: 0;'>🎯 GD&T Input Examples:</h3>
        <table style='width: 100%; color: #495057;'>
        <tr><td><b>Position:</b></td><td>⌖ 0.5(M) A B C</td></tr>
        <tr><td><b>Parallelism:</b></td><td>∥ 0.1 A</td></tr>
        <tr><td><b>Flatness:</b></td><td>⏸ 0.05</td></tr>
        <tr><td><b>Circularity:</b></td><td>○ 0.02</td></tr>
        <tr><td><b>Profile:</b></td><td>⌓ 0.2 A B</td></tr>
        </table>
        <br>
        <h4 style='color: #2c3e50;'>📏 Material Conditions:</h4>
        <ul style='color: #6c757d; margin: 0;'>
        <li><b>(M)</b> = Maximum Material Condition</li>
        <li><b>(L)</b> = Least Material Condition</li>
        <li><b>(S)</b> = Regardless of Feature Size</li>
        </ul>
        </div>
        """)
        layout.addWidget(instructions)

        # Enhanced text input
        layout.addWidget(QLabel("<b>Enter GD&T Description:</b>"))
        text_input = QTextEdit()
        text_input.setMaximumHeight(80)
        text_input.setPlaceholderText("Example: position 0.5(M) A B C")
        layout.addWidget(text_input)

        # Enhanced buttons
        button_layout = QHBoxLayout()

        apply_btn = QPushButton("✅ Apply to Row")
        apply_btn.clicked.connect(
            lambda: self._apply_gdt_to_row(
                table, current_row, text_input.toPlainText(), dialog
            )
        )
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _apply_gdt_to_row(self, table: QTableWidget, row: int, gdt_text: str, dialog):
        """Apply GD&T text to table row with enhanced formatting"""
        if not gdt_text.strip():
            dialog.accept()
            return

        try:
            gdt_interpreter = GDTInterpreter()
            formatted_text = gdt_interpreter.format_gdt_display(gdt_text)

            # Apply to description column
            desc_item = table.item(row, 4)
            if not desc_item:
                desc_item = QTableWidgetItem()
                table.setItem(row, 4, desc_item)

            desc_item.setText(formatted_text)

            # Enhanced GD&T parsing and tolerance application
            gdt_info = gdt_interpreter.parse_gdt_description(formatted_text)
            if gdt_info.get("has_gdt") and gdt_info.get("tolerance_value"):
                lower_item = table.item(row, 10)  # lower_tolerance (updated position)
                upper_item = table.item(row, 11)  # upper_tolerance (updated position)

                if (not lower_item or not lower_item.text()) and (
                    not upper_item or not upper_item.text()
                ):
                    nominal_item = table.item(row, 9)  # nominal (updated position)
                    nominal = (
                        float(nominal_item.text())
                        if nominal_item and nominal_item.text()
                        else 0.0
                    )

                    lower_tol, upper_tol = (
                        gdt_interpreter.convert_gdt_to_tolerance_range(
                            gdt_info, nominal
                        )
                    )

                    if not lower_item:
                        lower_item = QTableWidgetItem()
                        table.setItem(row, 10, lower_item)
                    if not upper_item:
                        upper_item = QTableWidgetItem()
                        table.setItem(row, 11, upper_item)

                    lower_item.setText(f"{lower_tol:.3f}")
                    upper_item.setText(f"{upper_tol:.3f}")

            self._mark_unsaved_changes()
            if self.parent_window:
                self.parent_window._log_message(f"🔧 Applied GD&T: {formatted_text}")

        except ImportError:
            QMessageBox.warning(
                self.parent_window, "GD&T Helper", "GD&T interpreter not available."
            )
        except Exception as e:
            if self.parent_window:
                self.parent_window._log_message(
                    f"❌ GD&T application error: {str(e)}", "ERROR"
                )

        dialog.accept()

    def _mark_unsaved_changes(self):
        """Mark unsaved changes"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

    def _add_manual_row(self):
        """Add manual row - delegated to parent window"""
        if self.parent_window:
            self.parent_window._add_manual_row()

    def clear_all_tables(self):
        """Enhanced clear all tables with better error handling"""
        if not self.parent_window:
            return

        try:
            # Clear all tabs except summary
            tabs_to_remove = []
            for i in range(self.parent_window.results_tabs.count()):
                if "Summary" not in self.parent_window.results_tabs.tabText(i):
                    tabs_to_remove.append(i)
            
            # Remove tabs in reverse order to maintain indices
            for i in reversed(tabs_to_remove):
                widget = self.parent_window.results_tabs.widget(i)
                self.parent_window.results_tabs.removeTab(i)
                if widget and not sip.isdeleted(widget):
                    widget.deleteLater()

            # Reset data structures
            self._copied_row_data = None

            if self.parent_window:
                self.parent_window._log_message("🧹 Data tables cleared (summary preserved)")

        except Exception as e:
            if self.parent_window:
                self.parent_window._log_message(
                    f"❌ Error clearing tables: {str(e)}", "ERROR"
                )