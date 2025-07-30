# src/gui/windows/components/dimensional_table_ui.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QTabWidget,
    QAbstractItemView,
    QMenu,
    QDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import sip  # type: ignore
from typing import Dict, Any

# from src.models.dimensional.dimensional_result import (DimensionalResult, DimensionalStatus)
from src.models.dimensional.gdt_interpreter import GDTInterpreter


class DimensionalTableUI:
    """UI components and widget management for dimensional tables"""

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
        self._original_measurements = {}  # {(row, col): value}

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

        # UI Colors
        self.colors = {
            "good": QColor(46, 125, 50),      # Strong green (Forest Green)
            "bad": QColor(183, 28, 28),       # Strong red (Dark Red)
            "warning": QColor(255, 152, 0),   # Strong orange
            "readonly": QColor(240, 242, 245), # Slightly darker light gray
            "header": QColor(44, 62, 80),     # Dark blue-gray
            "primary": QColor(21, 101, 192),  # Strong blue
            "white": QColor(255, 255, 255),   # White
            "black": QColor(33, 37, 41),      # Strong black
            "text_dark": QColor(40, 44, 52),  # Dark text
        }

    def set_parent_window(self, parent):
        self.parent_window = parent

    def _log_message(self, message: str, level: str = "INFO"):
        """Delegate logging to parent window if available"""
        if self.parent_window and hasattr(self.parent_window, "_log_message"):
            self.parent_window._log_message(message, level)
        else:
            print(
                f"[{level}] {message}"
            )  # Fallback to print if no parent logging available

    def _create_results_table(self) -> QTableWidget:
        """Create a professionally styled results table - ENHANCED with better styling"""
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
        
        # Enhanced header styling
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

        # Improved column widths for better fit
        column_widths = {
            0: 70,   # element_id - shorter
            1: 60,   # batch - shorter
            2: 50,   # cavity - shorter, will be centered
            3: 45,   # class - shorter
            4: 180,  # description - adjust for content
            5: 85,   # measuring_instrument
            6: 45,   # unit - shorter
            7: 50,   # datum
            8: 75,   # evaluation_type
            9: 65,   # nominal - will be centered and bold
            10: 70,  # lower_tolerance - will be centered and bold
            11: 70,  # upper_tolerance - will be centered and bold
            12: 65,  # measurement_1
            13: 65,  # measurement_2
            14: 65,  # measurement_3
            15: 65,  # measurement_4
            16: 65,  # measurement_5
            17: 55,  # minimum - will be centered
            18: 55,  # maximum - will be centered
            19: 55,  # mean - will be centered
            20: 55,  # std_deviation - will be centered
            21: 70,  # status - will be centered
            22: 80,  # force_status
        }

        for col, width in column_widths.items():
            if col < table.columnCount():
                table.setColumnWidth(col, width)

        # Set consistent row height
        table.verticalHeader().setDefaultSectionSize(32)
        table.setWordWrap(True)
        table.cellChanged.connect(self._on_cell_changed)
        
        # Set default font for the entire table
        table_font = QFont("Segoe UI", 9)
        table.setFont(table_font)
        
        return table

    def _create_summary_widget(self) -> QWidget:
        """Create enhanced summary widget with professional styling"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            QLabel {
                color: #2c3e50;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                color: #34495e;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout()
        # Enhanced statistics display
        self.stats_label = QLabel("📊 No analysis performed yet")
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 15px;
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                color: #495057;
            }
        """)
        layout.addWidget(self.stats_label)
        # Enhanced cavity comparison
        self.cavity_group = QGroupBox("🔧 Cavity Comparison")
        self.cavity_layout = QVBoxLayout()
        self.cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(self.cavity_group)
        # Enhanced feature breakdown
        self.feature_group = QGroupBox("📈 Feature Type Breakdown")
        self.feature_layout = QVBoxLayout()
        self.feature_group.setLayout(self.feature_layout)
        layout.addWidget(self.feature_group)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _show_context_menu(self, table: QTableWidget, position):
        """Enhanced context menu with professional styling"""
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

        gdt_helper_action = menu.addAction("🔧 GD&T Helper")
        gdt_helper_action.triggered.connect(lambda: self._show_gdt_helper(table))
        menu.addSeparator()

        copy_action = menu.addAction("📄 Copy Row")
        copy_action.triggered.connect(lambda: self._copy_row(table))
        paste_action = menu.addAction("📋 Paste Row")
        paste_action.triggered.connect(lambda: self._paste_row(table))

        menu.exec_(table.mapToGlobal(position))

    def _populate_default_row(self, table: QTableWidget, row: int):
        """Populate row with defaults and enhanced UI elements - ENHANCED with better styling"""
        # Set basic defaults
        defaults = {
            0: self._get_next_element_id(table),  # Auto-increment element_id
            1: str(self.batch_number),  # batch
            2: "1",  # cavity (default to 1)
            6: "mm",  # default unit
            8: "Normal",  # default evaluation type
        }

        # Columns that should be centered
        centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21]  # cavity, nominal, tolerances, min, max, mean, std, status
        # Columns that should be bold (nominal and tolerances)
        bold_columns = [9, 10, 11]  # nominal, lower_tolerance, upper_tolerance

        for col, value in defaults.items():
            item = QTableWidgetItem(str(value))
            
            # Apply centering for specific columns
            if col in centered_columns:
                item.setTextAlignment(Qt.AlignCenter)
            
            # Apply bold font for nominal and tolerance columns
            if col in bold_columns:
                font = QFont("Segoe UI", 9, QFont.Bold)
                item.setFont(font)
            else:
                font = QFont("Segoe UI", 9)
                item.setFont(font)
                
            table.setItem(row, col, item)

        self._add_dropdowns(table, row)  # Add enhanced dropdown widgets

        # Style calculated columns as read-only with better colors
        for col in range(17, 23):  # calculated columns (min, max, mean, std, status, force_status)
            if col != 22:  # force_status is editable
                item = QTableWidgetItem("")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                if col == 21:  # STATUS COLUMN - special handling
                    item.setTextAlignment(Qt.AlignCenter)
                    font = QFont("Segoe UI", 9, QFont.Bold)  # Smaller, bold font
                    item.setFont(font)
                    self._log_message(f"📋 Created empty status cell for row {row + 1}", "DEBUG")
                else:
                    # Other calculated columns get centering and styling
                    if col in centered_columns:
                        item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor(240, 242, 245))  # Slightly darker gray
                    item.setForeground(QColor(40, 44, 52))     # Darker text
                    font = QFont("Segoe UI", 9)
                    item.setFont(font)

                table.setItem(row, col, item)

    def _add_dropdowns(self, table: QTableWidget, row: int):
        """Add professional dropdown widgets to specific columns"""
        dropdown_style = self._get_combo_style()

        # Class dropdown (column 3)
        class_combo = QComboBox()
        class_combo.addItems(self.class_options)
        class_combo.setCurrentText("")  # Default empty
        class_combo.setStyleSheet(dropdown_style)
        class_combo.setMaximumHeight(30)  # FIX: Set proper height
        table.setCellWidget(row, 3, class_combo)

        # Measuring instrument dropdown (column 5)
        instrument_combo = QComboBox()
        instrument_combo.addItems(self.instrument_options)
        instrument_combo.setCurrentText("3D Scanbox")  # Default to scanbox
        instrument_combo.setStyleSheet(dropdown_style)
        instrument_combo.setMaximumHeight(30)
        table.setCellWidget(row, 5, instrument_combo)

        # Unit dropdown (column 6)
        unit_combo = QComboBox()
        unit_combo.addItems(self.unit_options)
        unit_combo.setCurrentText("mm")  # Default to mm
        unit_combo.setStyleSheet(dropdown_style)
        unit_combo.setMaximumHeight(30)
        table.setCellWidget(row, 6, unit_combo)

        # Datum dropdown (column 7)
        datum_combo = QComboBox()
        datum_combo.addItems(self.datum_options)
        datum_combo.setCurrentText("")  # Default empty
        datum_combo.setStyleSheet(dropdown_style)
        datum_combo.setMaximumHeight(30)
        table.setCellWidget(row, 7, datum_combo)

        # Evaluation type dropdown (column 8)
        eval_combo = QComboBox()
        eval_combo.addItems(self.evaluation_options)
        eval_combo.setCurrentText("Normal")  # Default to Normal
        eval_combo.setStyleSheet(dropdown_style)
        eval_combo.setMaximumHeight(30)
        table.setCellWidget(row, 8, eval_combo)

        # Force status dropdown (column 22)
        force_combo = QComboBox()
        force_combo.addItems(self.force_status_options)
        force_combo.setCurrentText("AUTO")  # Default to AUTO
        force_combo.setStyleSheet(dropdown_style)
        force_combo.setMaximumHeight(30)
        table.setCellWidget(row, 22, force_combo)

    def _get_combo_style(self) -> str:
        """Professional combobox styling with proper sizing"""
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

    def _get_next_element_id(self, table: QTableWidget) -> str:
        """Generate sequential element_id based on the last row's ID"""
        # First, try to get the ID from the previous row (most recent)
        if table.rowCount() > 0:
            last_row = table.rowCount() - 1
            last_item = table.item(last_row, 0)  # element_id column
            if last_item and last_item.text().strip():
                last_id = last_item.text().strip()
                # Extract number from format like "Nº100", "Nº001", etc.
                try:
                    if "º" in last_id:
                        number_part = last_id.split("º")[1]
                        last_number = int(number_part)
                        next_number = last_number + 1
                        return f"Nº{next_number:03d}"
                except (ValueError, IndexError):
                    pass
        
        # Fallback: scan all tables to find the highest number
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

    def _duplicate_row(self, table: QTableWidget):
        """Enhanced duplicate row with proper dropdown handling for new columns"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self.parent_window, "No Selection", "Please select a row to duplicate."
            )
            return

        # Get row data including dropdown values
        row_data = []
        for col in range(table.columnCount()):
            cell_widget = table.cellWidget(current_row, col)
            if isinstance(cell_widget, QComboBox):
                row_data.append(cell_widget.currentText())
            else:
                item = table.item(current_row, col)
                row_data.append(item.text() if item else "")

        new_row = table.rowCount()  # Create new row
        table.insertRow(new_row)

        # Populate new row with duplicated data
        for col, value in enumerate(row_data):
            if col == 0:  # Generate new element_id
                item = QTableWidgetItem(self._get_next_element_id(table))
                table.setItem(new_row, col, item)
            elif col in [3, 5, 6, 7, 8, 22]:  # Dropdown columns (updated)
                if col == 3:  # class
                    combo = QComboBox()
                    combo.addItems(self.class_options)
                    combo.setCurrentText(value)
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
                elif col == 5:  # measuring_instrument
                    combo = QComboBox()
                    combo.addItems(self.instrument_options)
                    combo.setCurrentText(value)
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
                elif col == 6:  # unit
                    combo = QComboBox()
                    combo.addItems(self.unit_options)
                    combo.setCurrentText(value if value else "mm")
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
                elif col == 7:  # datum
                    combo = QComboBox()
                    combo.addItems(self.datum_options)
                    combo.setCurrentText(value)
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
                elif col == 8:  # evaluation_type
                    combo = QComboBox()
                    combo.addItems(self.evaluation_options)
                    combo.setCurrentText(value if value else "Normal")
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
                elif col == 22:  # force_status
                    combo = QComboBox()
                    combo.addItems(self.force_status_options)
                    combo.setCurrentText(value if value else "AUTO")
                    combo.setStyleSheet(self._get_combo_style())
                    combo.setMaximumHeight(30)
                    table.setCellWidget(new_row, col, combo)
            elif col >= 17:  # Calculated columns - make read-only (updated)
                if col != 22:  # force_status is editable
                    item = QTableWidgetItem("")
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    item.setBackground(self.colors["readonly"])
                    table.setItem(new_row, col, item)
            else:  # Regular columns
                item = QTableWidgetItem(str(value))
                table.setItem(new_row, col, item)

        self._mark_unsaved_changes()
        if self.parent_window:
            self.parent_window._log_message(
                f"Row duplicated with new ID: {self._get_next_element_id(table)}"
            )

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

    def _copy_row(self, table: QTableWidget):
        """Enhanced copy row with dropdown support"""
        current_row = table.currentRow()
        if current_row < 0:
            return

        row_data = []
        for col in range(table.columnCount()):
            cell_widget = table.cellWidget(current_row, col)
            if isinstance(cell_widget, QComboBox):
                row_data.append(cell_widget.currentText())
            else:
                item = table.item(current_row, col)
                row_data.append(item.text() if item else "")

        self._copied_row_data = row_data
        if self.parent_window:
            self.parent_window._log_message(f"📋 Copied row {current_row + 1}")

    def _paste_row(self, table: QTableWidget):
        """Enhanced paste row with dropdown support"""
        if not hasattr(self, "_copied_row_data") or not self._copied_row_data:
            QMessageBox.information(
                self.parent_window, "No Data", "No row data copied."
            )
            return

        current_row = table.currentRow()
        if current_row < 0:
            return

        for col, value in enumerate(self._copied_row_data):
            if col < 14:  # Only paste input columns, not calculated ones
                if col in [3, 5, 19]:  # Dropdown columns
                    cell_widget = table.cellWidget(current_row, col)
                    if isinstance(cell_widget, QComboBox):
                        if value in [
                            cell_widget.itemText(i) for i in range(cell_widget.count())
                        ]:
                            cell_widget.setCurrentText(value)
                else:
                    item = table.item(current_row, col)
                    if not item:
                        item = QTableWidgetItem()
                        table.setItem(current_row, col, item)
                    item.setText(value)

        self._mark_unsaved_changes()
        if self.parent_window:
            self.parent_window._log_message(f"📋 Pasted data to row {current_row + 1}")

    def _show_gdt_helper(self, table: QTableWidget):
        """Enhanced GD&T helper dialog with professional styling"""
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
                lower_item = table.item(row, 7)
                upper_item = table.item(row, 8)

                if (not lower_item or not lower_item.text()) and (
                    not upper_item or not upper_item.text()
                ):
                    nominal_item = table.item(row, 6)
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
                        table.setItem(row, 7, lower_item)
                    if not upper_item:
                        upper_item = QTableWidgetItem()
                        table.setItem(row, 8, upper_item)

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

    def _on_evaluation_type_changed(
        self, table: QTableWidget, row: int, evaluation_type: str
    ):
        """Handle evaluation type change - auto-fill GD&T values"""
        self._log_message(
            f"🔧 Evaluation type changed to '{evaluation_type}' for row {row + 1}",
            "INFO",
        )

        if evaluation_type == "GD&T":
            # Auto-fill nominal with 0.00001
            nominal_item = table.item(row, 9)  # nominal column
            if not nominal_item:
                nominal_item = QTableWidgetItem()
                table.setItem(row, 9, nominal_item)
            nominal_item.setText("0.001")

            # Auto-fill lower tolerance with 0.000
            lower_tol_item = table.item(row, 10)  # lower_tolerance column
            if not lower_tol_item:
                lower_tol_item = QTableWidgetItem()
                table.setItem(row, 10, lower_tol_item)
            lower_tol_item.setText("0.000")

            self._log_message(
                "✅ Auto-filled GD&T values: nominal=0.00001, lower_tolerance=0.000",
                "INFO",
            )

            # Mark changes
            self._mark_unsaved_changes()

    def _on_cell_changed(self, row: int, col: int):
        """Enhanced cell change handler with measurement clearing detection"""
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
                measurement_count = 0
                for meas_col in [12, 13, 14, 15, 16]:
                    meas_item = current_table.item(row, meas_col)
                    if meas_item and meas_item.text().strip():
                        all_measurements_empty = False
                        measurement_count += 1

                self._log_message(
                    f"📊 Measurement status: {measurement_count}/5 measurements, all_empty={all_measurements_empty}",
                    "DEBUG",
                )

                # If all measurements are empty, clear calculated columns
                if all_measurements_empty:
                    self._log_message(
                        " 🧹 All measurements empty - clearing calculated columns",
                        "INFO",
                    )
                    self._clear_calculated_columns(current_table, row)
                    return

            # Auto-formatting for numeric columns (3 decimal places max)
            if col in [
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
            ]:  # nominal, tolerances, measurements
                try:
                    if item.text().strip():  # Only format non-empty values
                        value = float(item.text())
                        formatted = f"{value:.3f}"
                        if item.text() != formatted:  # Avoid infinite loop
                            item.setText(formatted)
                            self._log_message(
                                f"  📐 Formatted value: {item.text()} -> {formatted}",
                                "DEBUG",
                            )
                except ValueError:
                    self._log_message(f"⚠️ Invalid numeric value in row {row + 1}, col {col}: '{item.text()}'", "WARNING")
        # Track the edit in summary
        if hasattr(self, 'summary_widget'):
            current_table = self.results_tabs.currentWidget()
            if hasattr(current_table, 'item'):
                item = current_table.item(row, 0)  # Get element ID
                element_id = item.text() if item else f"Row {row+1}"
                
                # Get column name
                col_name = self.table_manager.column_headers[col] if col < len(self.table_manager.column_headers) else f"Col {col}"
                
                self.summary_widget.record_edit(f"Modified {col_name} in {element_id}")
                self._update_summary_from_tables()

    def _clear_calculated_columns(self, table: QTableWidget, row: int):
        """Clear calculated columns when measurements are removed - ENHANCED with better styling"""
        calculated_cols = [17, 18, 19, 20, 21]  # min, max, mean, std, status
        centered_columns = [17, 18, 19, 20, 21]

        self._log_message(f"🧹 CLEARING calculated columns for row {row + 1}", "INFO")

        for col in calculated_cols:
            item = table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                if col != 21:  # Don't make status read-only initially
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col, item)

            # Clear the text
            item.setText("")
            
            # Apply consistent styling
            if col in centered_columns:
                item.setTextAlignment(Qt.AlignCenter)

            if col == 21:  # status column - CLEAR STYLING COMPLETELY
                self._log_message(f"🎨 Clearing status cell styling for row {row + 1}", "INFO")

                # FORCE clear all styling data
                item.setData(Qt.BackgroundRole, None)
                item.setData(Qt.ForegroundRole, None)
                item.setData(Qt.FontRole, None)
                item.setData(Qt.ToolTipRole, None)

                # Set default styling
                item.setBackground(QColor())
                item.setForeground(self.colors["text_dark"])
                item.setToolTip("")
                item.setTextAlignment(Qt.AlignCenter)

                # Set smaller, normal font for status
                font = QFont("Segoe UI", 9)  # Smaller font
                item.setFont(font)

                # Make it read-only after clearing
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                self._log_message("✅ Status cell cleared and reset to neutral styling", "INFO")
            else:
                # Statistics columns - consistent styling
                item.setBackground(self.colors["readonly"])
                item.setForeground(self.colors["text_dark"])
                font = QFont("Segoe UI", 9)
                item.setFont(font)

        # Force table update after clearing
        table.viewport().update()
        table.repaint()
        self._log_message("🔄 Table viewport updated after clearing columns", "INFO")

    def clear_all_tables(self):
        """Enhanced clear all tables with better error handling"""
        if not self.parent_window:
            return

        try:
            # Clear all tabs
            while self.parent_window.results_tabs.count():
                widget = self.parent_window.results_tabs.widget(0)
                self.parent_window.results_tabs.removeTab(0)
                if widget and not sip.isdeleted(widget):
                    widget.deleteLater()

            # Reset data structures
            self._copied_row_data = None

            if self.parent_window:
                self.parent_window._log_message("🧹 All tables cleared")

        except Exception as e:
            if self.parent_window:
                self.parent_window._log_message(
                    f"❌ Error clearing tables: {str(e)}", "ERROR"
                )

    def _safe_clear_layout(self, layout):
        """Safely clear layout without SIP errors"""
        if not layout or sip.isdeleted(layout):
            return

        try:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and not sip.isdeleted(widget):
                        widget.setParent(None)
                        widget.deleteLater()
        except RuntimeError:
            pass  # Widget already deleted

    def _apply_styling_to_item(self, item: QTableWidgetItem, col: int):
        """Apply consistent styling to table items"""
        centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21]
        
        # Apply centering
        if col in centered_columns:
            item.setTextAlignment(Qt.AlignCenter)

        font = QFont("Segoe UI", 9)
        item.setFont(font)
        item.setForeground(self.colors["text_dark"])    # Apply text color for better contrast

    def get_table_statistics(self) -> Dict[str, Any]:
        """Get comprehensive table statistics for summary display"""
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            return {}

        stats = {
            "total_rows": 0,
            "total_measurements": 0,
            "cavities": set(),
            "classes": set(),
            "instruments": set(),
            "good_count": 0,
            "bad_count": 0,
            "warning_count": 0,
        }

        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            stats["total_rows"] += table.rowCount()

            for row in range(table.rowCount()):
                # Count measurements
                measurement_count = 0
                for col in range(9, 14):  # measurement columns
                    item = table.item(row, col)
                    if item and item.text().strip():
                        measurement_count += 1
                stats["total_measurements"] += measurement_count

                # Track cavities, classes, instruments
                cavity_item = table.item(row, 2)
                if cavity_item and cavity_item.text():
                    stats["cavities"].add(cavity_item.text())

                class_widget = table.cellWidget(row, 3)
                if isinstance(class_widget, QComboBox) and class_widget.currentText():
                    stats["classes"].add(class_widget.currentText())

                instrument_widget = table.cellWidget(row, 5)
                if (
                    isinstance(instrument_widget, QComboBox)
                    and instrument_widget.currentText()
                ):
                    stats["instruments"].add(instrument_widget.currentText())

                # Count status
                status_item = table.item(row, 18)
                if status_item and status_item.text():
                    status = status_item.text()
                    if status == "GOOD":
                        stats["good_count"] += 1
                    elif status == "BAD":
                        stats["bad_count"] += 1
                    else:
                        stats["warning_count"] += 1

        return stats

    def _mark_unsaved_changes(self):
        """Mark unsaved changes"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

    def _add_manual_row(self):
        """Add manual row - delegated to parent window"""
        if self.parent_window:
            self.parent_window._add_manual_row()
