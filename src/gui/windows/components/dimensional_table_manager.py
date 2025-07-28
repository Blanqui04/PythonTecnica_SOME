# src/gui/windows/dimensional_table_manager.py
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
import pandas as pd
import sip  # type: ignore
from typing import List, Dict, Any
from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus

class DimensionalTableManager:
    """Enhanced table manager with professional styling and improved functionality"""

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
        self.results: List[DimensionalResult] = []
        self._copied_row_data = None

        # Updated dropdown options
        self.class_options = ["", "None", "SC", "CC", "IC"]
        self.instrument_options = [
            "",
            "Scanbox",
            "CMM",
            "Caliper",
            "Micrometer",
            "Gauge",
            "Vision System",
        ]
        self.force_status_options = ["AUTO", "GOOD", "BAD"]
        
        # NEW: Add unit options
        self.unit_options = ["","mm", "°", "μm", "inch", "mil"]
        
        # NEW: Add datum options
        self.datum_options = ["", "A", "B", "C", "D", "E", "F", "G", "H"]
        
        # NEW: Add evaluation options
        self.evaluation_options = ["Normal", "Basic", "Informative", "Note"]

        # Styling constants
        self.colors = {
            "good": QColor(144, 238, 144),  # Light green
            "bad": QColor(255, 182, 193),  # Light red
            "warning": QColor(255, 255, 224),  # Light yellow
            "readonly": QColor(248, 249, 250),  # Light gray
            "header": QColor(52, 73, 94),  # Dark blue-gray
            "primary": QColor(52, 152, 219),  # Blue
            "white": QColor(255, 255, 255),
        }

    def set_parent_window(self, parent):
        self.parent_window = parent

    def _log_message(self, message: str, level: str = "INFO"):
        """Delegate logging to parent window if available"""
        if self.parent_window and hasattr(self.parent_window, '_log_message'):
            self.parent_window._log_message(message, level)
        else:
            # Fallback to print if no parent logging available
            print(f"[{level}] {message}")

    def _create_results_table(self) -> QTableWidget:
        """Create a professionally styled results table"""
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

        # Professional styling
        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                gridline-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: #ffffff;
            }
        """)

        # Enhanced header styling
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #34495e;
                color: #ffffff;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #2c3e50;
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
            }
            QHeaderView::section:hover {
                background-color: #2c3e50;
            }
        """)

        # Updated column widths for new columns
        column_widths = {
            0: 80,   # element_id
            1: 80,   # batch
            2: 50,   # cavity
            3: 60,   # class
            4: 220,  # description
            5: 100,  # measuring_instrument
            6: 70,   # unit
            7: 40,   # datum
            8: 90,   # evaluation_type
            9: 70,   # nominal
            10: 70,  # lower_tolerance
            11: 70,  # upper_tolerance
            12: 75,  # measurement_1
            13: 75,  # measurement_2
            14: 75,  # measurement_3
            15: 75,  # measurement_4
            16: 75,  # measurement_5
            17: 65,  # minimum
            18: 65,  # maximum
            19: 70,  # mean
            20: 75,  # std_deviation
            21: 90,  # status
            22: 100, # force_status
        }

        for col, width in column_widths.items():
            if col < table.columnCount():
                table.setColumnWidth(col, width)

        table.cellChanged.connect(self._on_cell_changed)
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

        # Enhanced menu actions
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
        """Populate row with defaults and enhanced UI elements"""
        # Set basic defaults
        defaults = {
            0: self._get_next_element_id(table),  # Auto-increment element_id
            1: str(self.batch_number),  # batch
            2: "1",  # cavity (default to 1)
            6: "mm",  # default unit
            8: "Normal",  # default evaluation type
        }

        for col, value in defaults.items():
            item = QTableWidgetItem(str(value))
            table.setItem(row, col, item)

        # Add enhanced dropdown widgets
        self._add_enhanced_dropdowns(table, row)

        # Style calculated columns as read-only (updated column indices)
        for col in range(17, 23):  # calculated columns (min, max, mean, std, status, force_status)
            if col != 22:  # force_status is editable
                item = QTableWidgetItem("")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setBackground(self.colors["readonly"])
                item.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
                table.setItem(row, col, item)

    def _add_enhanced_dropdowns(self, table: QTableWidget, row: int):
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
        instrument_combo.setCurrentText("")  # Default empty
        instrument_combo.setStyleSheet(dropdown_style)
        instrument_combo.setMaximumHeight(30)
        table.setCellWidget(row, 5, instrument_combo)
        
        # NEW: Unit dropdown (column 6)
        unit_combo = QComboBox()
        unit_combo.addItems(self.unit_options)
        unit_combo.setCurrentText("mm")  # Default to mm
        unit_combo.setStyleSheet(dropdown_style)
        unit_combo.setMaximumHeight(30)
        table.setCellWidget(row, 6, unit_combo)
        
        # NEW: Datum dropdown (column 7)
        datum_combo = QComboBox()
        datum_combo.addItems(self.datum_options)
        datum_combo.setCurrentText("")  # Default empty
        datum_combo.setStyleSheet(dropdown_style)
        datum_combo.setMaximumHeight(30)
        table.setCellWidget(row, 7, datum_combo)
        
        # NEW: Evaluation type dropdown (column 8)
        eval_combo = QComboBox()
        eval_combo.addItems(self.evaluation_options)
        eval_combo.setCurrentText("Normal")  # Default to Normal
        eval_combo.setStyleSheet(dropdown_style)
        eval_combo.setMaximumHeight(30)
        table.setCellWidget(row, 8, eval_combo)

        # Force status dropdown (column 22) - MOVED
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
        """Generate sequential element_id"""
        existing_ids = set()

        # Collect existing IDs from current table
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.text():
                try:
                    # Extract numeric part if format is like "E001", "ELEM_001", etc.
                    text = item.text().strip()
                    if text.replace("_", "").replace("-", "").isalnum():
                        # Extract numbers from the ID
                        numbers = "".join(filter(str.isdigit, text))
                        if numbers:
                            existing_ids.add(int(numbers))
                except (ValueError, AttributeError):
                    pass

        # Also check other tabs in parent window
        if self.parent_window and hasattr(self.parent_window, "results_tabs"):
            for tab_idx in range(self.parent_window.results_tabs.count()):
                tab_table = self.parent_window.results_tabs.widget(tab_idx)
                if isinstance(tab_table, QTableWidget) and tab_table != table:
                    for row in range(tab_table.rowCount()):
                        item = tab_table.item(row, 0)
                        if item and item.text():
                            try:
                                text = item.text().strip()
                                numbers = "".join(filter(str.isdigit, text))
                                if numbers:
                                    existing_ids.add(int(numbers))
                            except (ValueError, AttributeError):
                                pass

        # Generate next sequential ID
        next_num = 1
        while next_num in existing_ids:
            next_num += 1

        return f"Nº {next_num:03d}"

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

        # Create new row
        new_row = table.rowCount()
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

    def _update_tables_with_results(self, results: List[DimensionalResult]):
        """Enhanced results update with comprehensive logging - FIXED VERSION"""
        self._log_message("🔄 STARTING TABLE UPDATE WITH RESULTS", "INFO")
        self._log_message("="*50, "INFO")
        
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            self._log_message("❌ No parent window or results tabs available", "ERROR")
            return

        # Create results lookup dictionary
        results_dict = {}
        for r in results:
            key = (r.element_id, str(r.batch), str(r.cavity))
            results_dict[key] = r
            self._log_message(f"  📋 Result key: {key} -> Status: {r.status.value}", "DEBUG")

        self._log_message(f"📊 Total results to apply: {len(results)}", "INFO")
        
        updated_count = 0
        not_found_count = 0

        # Process each tab
        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            tab_name = self.parent_window.results_tabs.tabText(tab_idx)
            self._log_message(f"🔧 Updating Tab: {tab_name}", "INFO")

            # Process each row in the table
            for row in range(table.rowCount()):
                # Get row identifiers
                element_id_item = table.item(row, 0)
                batch_item = table.item(row, 1)
                cavity_item = table.item(row, 2)

                if not all([element_id_item, batch_item, cavity_item]):
                    self._log_message(f" ⚠️ Row {row + 1}: Missing identifier items", "WARNING")
                    continue

                element_id = element_id_item.text()
                batch = batch_item.text()
                cavity = cavity_item.text()
                
                key = (element_id, batch, cavity)
                result = results_dict.get(key)

                if result:
                    self._log_message(f"    ✅ Row {row + 1}: Found result for {element_id}", "DEBUG")
                    self._update_row_with_result(table, row, result)
                    updated_count += 1
                else:
                    self._log_message(f"    ❌ Row {row + 1}: No result found for key {key}", "WARNING")
                    not_found_count += 1

        # Final summary
        self._log_message("="*50, "INFO")
        self._log_message("📊 TABLE UPDATE SUMMARY:", "INFO")
        self._log_message(f"  Rows updated: {updated_count}", "INFO")
        self._log_message(f"  Rows not found: {not_found_count}", "INFO")
        self._log_message("="*50, "INFO")

        if updated_count > 0:
            self._log_message(f"✅ Successfully updated {updated_count} rows with results", "INFO")
        else:
            self._log_message("❌ No rows were updated - check data matching", "ERROR")


    def _update_row_with_result(self, table: QTableWidget, row: int, result: DimensionalResult):
        """Update single row with result - with enhanced styling and debugging"""
        element_id = result.element_id
        self._log_message(f"      🔧 Updating {element_id} with result:", "DEBUG")
        
        # Get force status from dropdown
        force_combo = table.cellWidget(row, 22)  # force_status column
        force_status = force_combo.currentText() if isinstance(force_combo, QComboBox) else "AUTO"
        
        # Determine final status
        if force_status == "GOOD":
            final_status = "GOOD"
        elif force_status == "BAD":
            final_status = "BAD"
        else:  # AUTO
            eval_combo = table.cellWidget(row, 8)  # evaluation_type column
            evaluation_type = eval_combo.currentText() if isinstance(eval_combo, QComboBox) else "Normal"
            final_status = "GOOD" if evaluation_type == "Note" else result.status.value

        # Update calculated columns
        updates = [
            (17, f"{min(result.measurements):.4f}" if result.measurements else ""),  # minimum
            (18, f"{max(result.measurements):.4f}" if result.measurements else ""),  # maximum
            (19, f"{result.mean:.4f}" if result.mean else ""),  # mean
            (20, f"{result.std_dev:.4f}" if result.std_dev else ""),  # std_deviation
            (21, final_status),  # status
        ]

        for col_idx, value in updates:
            item = table.item(row, col_idx)
            if not item:
                item = QTableWidgetItem()
                if col_idx != 21:  # Don't make status read-only
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)

            item.setText(str(value))
            
            # DEBUG: Log before applying styles
            self._log_message(f"        Applying styles to row {row}, col {col_idx} (value: {value})", "DEBUG")
            
            if col_idx == 21:  # status column
                # Apply status background colors
                if final_status in ["GOOD", "OK"]:
                    item.setBackground(QColor(144, 238, 144))  # Light green
                    self._log_message("          Setting GOOD/OK status (green)", "DEBUG")
                elif final_status == "BAD":
                    item.setBackground(QColor(255, 182, 193))  # Light red
                    self._log_message("          Setting BAD status (red)", "DEBUG")
                else:
                    item.setBackground(QColor(255, 255, 224))  # Light yellow
                    self._log_message("          Setting other status (yellow)", "DEBUG")
                
                # Status text styling
                item.setForeground(QColor(0, 0, 0))  # Black text
                font = QFont("Segoe UI", 9)
                item.setFont(font)
            else:
                # Statistics columns (min, max, mean, std)
                item.setBackground(QColor(240, 240, 240))  # Light gray
                item.setForeground(QColor(0, 0, 0))  # Black text
                font = QFont("Segoe UI", 9)
                item.setFont(font)

        # Highlight measurement violations with more debugging
        self._highlight_measurement_violations_with_logging(table, row, result, element_id)


    def _highlight_measurement_violations_with_logging(self, table: QTableWidget, row: int, 
                                                    result: DimensionalResult, element_id: str):
        """Highlight measurement violations with enhanced debugging"""
        measurement_cols = [12, 13, 14, 15, 16]  # measurement columns
        violations_found = 0
        
        # Get tolerance information
        lower_limit = None
        upper_limit = None
        
        if result.lower_tolerance is not None and result.upper_tolerance is not None:
            if result.nominal == 0.0 and result.lower_tolerance == 0.0:
                upper_limit = result.upper_tolerance
            else:
                lower_limit = result.nominal + result.lower_tolerance
                upper_limit = result.nominal + result.upper_tolerance

        for i, col in enumerate(measurement_cols):
            item = table.item(row, col)
            if not item:
                continue
                
            self._log_message(f"        Processing measurement {i+1} in column {col}", "DEBUG")
            
            if not item.text():
                self._log_message("          Empty measurement - skipping", "DEBUG")
                continue

            try:
                value = float(item.text())
                is_violation = False
                
                if result.nominal == 0.0 and result.lower_tolerance == 0.0 and upper_limit is not None:
                    is_violation = abs(value) > upper_limit
                elif lower_limit is not None and upper_limit is not None:
                    is_violation = not (lower_limit <= value <= upper_limit)
                
                if is_violation:
                    self._log_message(f"          VIOLATION: {value} out of tolerance", "DEBUG")
                    item.setBackground(QColor(255, 182, 193))  # Light red
                    item.setForeground(QColor(0, 0, 0))  # Black text
                    item.setToolTip(f"⚠️ Measurement {value:.3f} violates tolerance!")
                    violations_found += 1
                else:
                    self._log_message(f"          OK: {value} within tolerance", "DEBUG")
                    item.setBackground(QColor(255, 255, 255))  # White
                    item.setForeground(QColor(0, 0, 0))  # Black text
                    item.setToolTip("")
                
                # Apply regular font
                font = QFont("Segoe UI", 9)
                item.setFont(font)
                
            except ValueError:
                self._log_message(f"⚠️ Invalid measurement value in column {col}", "WARNING")

        if violations_found > 0:
            self._log_message(f"🚨 {violations_found} measurement violations found for {element_id}", "WARNING")

    def _is_outside_tolerance(self, value: float, lower_tol, upper_tol, nominal=None) -> bool:
        """Check if value is outside tolerance range, handling GD&T cases"""
        # Handle GD&T case where nominal = 0
        if nominal == 0.0 and upper_tol is not None:
            # For GD&T, check if absolute value exceeds upper tolerance
            if abs(value) > upper_tol:
                return True
            return False
        
        # Standard tolerance checking
        if lower_tol is not None and value < lower_tol:
            return True
        if upper_tol is not None and value > upper_tol:
            return True
        return False

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Enhanced dataframe extraction with comprehensive logging - FIXED VERSION"""
        self._log_message("🔍 STARTING DATA EXTRACTION FROM TABLES", "INFO")
        self._log_message("="*50, "INFO")
        
        all_data = []
        total_rows_processed = 0
        valid_rows = 0
        skipped_rows = 0

        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            self._log_message("❌ No parent window or results tabs found", "ERROR")
            return pd.DataFrame()

        # Process each tab
        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                self._log_message(f"⚠️ Tab {tab_idx} is not a QTableWidget, skipping", "WARNING")
                continue

            tab_name = self.parent_window.results_tabs.tabText(tab_idx)
            self._log_message(f"📋 Processing Tab: {tab_name} ({table.rowCount()} rows)", "INFO")

            # Process each row in the table
            for row in range(table.rowCount()):
                total_rows_processed += 1
                row_data = {}
                
                self._log_message(f"  🔍 Processing Row {row + 1}:", "DEBUG")

                # Extract data from each column
                for col, col_name in enumerate(self.display_columns):
                    if col >= len(self.display_columns):
                        break
                        
                    # Handle dropdown widgets
                    cell_widget = table.cellWidget(row, col)
                    if isinstance(cell_widget, QComboBox):
                        value = cell_widget.currentText().strip()
                        if not value or value == "":
                            value = None
                        self._log_message(f"    📝 {col_name} (dropdown): '{value}'", "DEBUG")
                    else:
                        # Handle regular table items
                        item = table.item(row, col)
                        value = item.text().strip() if item and item.text() else None
                        if value == "":
                            value = None
                        self._log_message(f"    📝 {col_name}: '{value}'", "DEBUG")

                    # Process the value
                    if value is None:
                        row_data[col_name] = None
                    else:
                        # Enhanced numeric validation
                        numeric_columns = ["nominal", "lower_tolerance", "upper_tolerance"] + self.measurement_columns
                        if col_name in numeric_columns:
                            try:
                                numeric_value = float(value)
                                row_data[col_name] = numeric_value
                                self._log_message(f"      ✅ Converted to numeric: {numeric_value}", "DEBUG")
                            except (ValueError, TypeError):
                                self._log_message(f"      ❌ Invalid numeric value: {value}", "WARNING")
                                row_data[col_name] = None
                        else:
                            row_data[col_name] = value

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number
                    self._log_message(f"    🔧 Auto-filled batch: {self.batch_number}", "DEBUG")

                # FIXED: Enhanced validation logic
                is_valid_row = self._validate_row_data(row_data, row + 1)
                
                if is_valid_row:
                    all_data.append(row_data)
                    valid_rows += 1
                    self._log_message(f"    ✅ Row {row + 1} added to dataset", "INFO")
                else:
                    skipped_rows += 1
                    self._log_message(f"    ❌ Row {row + 1} skipped (validation failed)", "WARNING")

        # Final logging
        self._log_message("="*50, "INFO")
        self._log_message("📊 DATA EXTRACTION SUMMARY:", "INFO")
        self._log_message(f"  Total rows processed: {total_rows_processed}", "INFO")
        self._log_message(f"  Valid rows: {valid_rows}", "INFO")
        self._log_message(f"  Skipped rows: {skipped_rows}", "INFO")
        self._log_message("="*50, "INFO")

        if not all_data:
            self._log_message("❌ No valid data extracted", "ERROR")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        self._log_message(f"✅ DataFrame created with {len(df)} records", "INFO")
        
        # Log column information
        self._log_message("📋 DataFrame columns:", "INFO")
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            self._log_message(f"  {col}: {non_null_count}/{len(df)} non-null values", "INFO")

        return df
    
    def _validate_row_data(self, row_data: dict, row_number: int) -> bool:
        """Validate row data with comprehensive logging - FIXED VERSION"""
        self._log_message(f"    🔍 Validating Row {row_number}:", "DEBUG")
        
        # Basic required fields
        element_id = row_data.get("element_id")
        description = row_data.get("description")
        evaluation_type = row_data.get("evaluation_type", "Normal")
        
        self._log_message(f"element_id: '{element_id}'", "DEBUG")
        self._log_message(f"description: '{description}'", "DEBUG")
        self._log_message(f"evaluation_type: '{evaluation_type}'", "DEBUG")
        
        # Check basic requirements
        if not element_id:
            self._log_message("❌ Missing element_id", "WARNING")
            return False
            
        if not description:
            self._log_message("❌ Missing description", "WARNING")
            return False

        # FIXED: Handle different evaluation types
        if evaluation_type == "Note":
            # For Notes, we only need element_id and description
            self._log_message("✅ Note entry - basic validation passed", "DEBUG")
            return True
        
        # For Normal/Basic/Informative entries, check nominal and measurements
        nominal = row_data.get("nominal")
        
        # FIXED: Allow nominal = 0 (it's valid for GD&T)
        if nominal is None:
            self._log_message("❌ Missing nominal value", "WARNING")
            return False

        self._log_message(f"nominal: {nominal} (✅ Valid, including zero)", "DEBUG")

        # Check for at least one measurement
        has_measurements = False
        measurement_count = 0
        for i in range(1, 6):
            meas_val = row_data.get(f"measurement_{i}")
            if meas_val is not None:
                has_measurements = True
                measurement_count += 1

        self._log_message(f"      measurements: {measurement_count}/5 provided", "DEBUG")

        if not has_measurements:
            self._log_message("❌ No measurements provided", "WARNING")
            return False

        # Check tolerances (optional but log if missing)
        lower_tol = row_data.get("lower_tolerance")
        upper_tol = row_data.get("upper_tolerance")
        
        if lower_tol is None and upper_tol is None:
            self._log_message("⚠️ No tolerances provided - will use force_status or default evaluation", "WARNING")
        else:
            self._log_message(f"tolerances: {lower_tol} / {upper_tol}", "DEBUG")

        self._log_message("✅ Validation passed", "DEBUG")
        return True

    def _on_cell_changed(self, row: int, col: int):
        """Enhanced cell change handler"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

        current_table = (
            self.parent_window.results_tabs.currentWidget()
            if self.parent_window
            else None
        )
        if not isinstance(current_table, QTableWidget):
            return

        # Auto-formatting for specific columns
        item = current_table.item(row, col)
        if item:
            # Format numeric columns
            if col in [6, 7, 8, 9, 10, 11, 12, 13]:  # nominal, tolerances, measurements
                try:
                    value = float(item.text())
                    item.setText(f"{value:.3f}")
                except ValueError:
                    pass

    def _mark_unsaved_changes(self):
        """Mark unsaved changes"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

    def _add_manual_row(self):
        """Add manual row - delegated to parent window"""
        if self.parent_window:
            self.parent_window._add_manual_row()

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
            from src.models.dimensional.gdt_interpreter import GDTInterpreter

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
            self.results = []
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

# Add method to filter dimensions based on evaluation type:
    def _filter_dimensions_for_evaluation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter dataframe to only include dimensions that should be evaluated"""
        if 'evaluation_type' not in df.columns:
            return df
        
        # Only process Normal dimensions and Notes (Notes get forced status)
        evaluation_df = df[df['evaluation_type'].isin(['Normal', 'Note'])].copy()
        
        self._log_message(
            f"Filtered {len(df)} total dimensions to {len(evaluation_df)} for evaluation " +
            f"({len(df[df['evaluation_type'] == 'Basic'])} Basic, " + 
            f"{len(df[df['evaluation_type'] == 'Informative'])} Informative excluded)"
        )
        
        return evaluation_df

    def _handle_note_entries(self, results):
        """Handle note entries and create appropriate DimensionalResult objects"""
        all_results = []
        
        for result in results:
            if hasattr(result, 'to_dict'):
                row = result.to_dict()
            else:
                row = result
                
            try:
                # Extract measurements from the row data
                measurements = []
                for i in range(1, 6):  # measurement_1 to measurement_5
                    meas_key = f'measurement_{i}'
                    if meas_key in row and row[meas_key] is not None:
                        try:
                            measurements.append(float(row[meas_key]))
                        except (ValueError, TypeError):
                            continue
                
                # Calculate mean and std_dev if measurements exist
                if measurements:
                    mean_val = sum(measurements) / len(measurements)
                    if len(measurements) > 1:
                        variance = sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)
                        std_dev_val = variance ** 0.5
                    else:
                        std_dev_val = 0.0
                else:
                    mean_val = 0.0
                    std_dev_val = 0.0
                    measurements = []
                
                # Calculate deviations from nominal
                nominal_val = float(row.get('nominal', 0))
                deviations = [meas - nominal_val for meas in measurements]
                
                # Check tolerances and count out-of-spec measurements
                lower_tol = row.get('lower_tolerance')
                upper_tol = row.get('upper_tolerance')
                out_of_spec_count = 0
                
                if lower_tol is not None and upper_tol is not None:
                    try:
                        lower_tol = float(lower_tol)
                        upper_tol = float(upper_tol)
                        for meas in measurements:
                            if meas < (nominal_val + lower_tol) or meas > (nominal_val + upper_tol):
                                out_of_spec_count += 1
                    except (ValueError, TypeError):
                        pass
                
                # Determine status
                force_status = row.get('force_status', 'AUTO')
                if force_status == 'GOOD':
                    status = DimensionalStatus.GOOD
                elif force_status == 'BAD':
                    status = DimensionalStatus.BAD
                else:
                    # Auto-determine based on out-of-spec count
                    status = DimensionalStatus.BAD if out_of_spec_count > 0 else DimensionalStatus.GOOD
                
                # Create DimensionalResult with correct parameters
                note_result = DimensionalResult(
                    element_id=row.get('element_id', ''),
                    batch=row.get('batch', ''),
                    cavity=row.get('cavity', ''),
                    classe=row.get('class', ''),  # Note: 'classe' not 'class'
                    description=row.get('description', ''),
                    nominal=nominal_val,
                    lower_tolerance=lower_tol,
                    upper_tolerance=upper_tol,
                    measurements=measurements,
                    deviation=deviations,
                    mean=mean_val,
                    std_dev=std_dev_val,
                    out_of_spec_count=out_of_spec_count,
                    status=status,
                    gdt_flags={},  # Initialize empty dict
                    datum_element_id=row.get('datum'),
                    feature_type=row.get('evaluation_type'),
                    warnings=[]
                )
                
                all_results.append(note_result)
                
            except Exception as e:
                self._log_message(f"Error creating DimensionalResult: {str(e)}", "ERROR")
                continue
        
        return all_results

    # Update the method that calls processing to use filtering:

    def _get_processed_dataframe(self) -> pd.DataFrame:
        """Get dataframe ready for processing with proper filtering"""
        df = self._get_dataframe_from_tables()
        
        if df.empty:
            return df
            
        # Filter for evaluation
        filtered_df = self._filter_dimensions_for_evaluation(df)
        
        # Remove Note entries from processing (they'll be handled separately)
        processing_df = filtered_df[filtered_df['evaluation_type'] != 'Note'].copy()
        
        return processing_df

    # ADD TO dimensional_table_manager.py - Update GD&T helper for new column indices:

    def _apply_gdt_to_row(self, table: QTableWidget, row: int, gdt_text: str, dialog):
        """Apply GD&T text to table row with enhanced formatting (updated column indices)"""
        if not gdt_text.strip():
            dialog.accept()
            return

        try:
            from src.models.dimensional.gdt_interpreter import GDTInterpreter

            gdt_interpreter = GDTInterpreter()
            formatted_text = gdt_interpreter.format_gdt_display(gdt_text)

            # Apply to description column (column 4)
            desc_item = table.item(row, 4)
            if not desc_item:
                desc_item = QTableWidgetItem()
                table.setItem(row, 4, desc_item)

            desc_item.setText(formatted_text)

            # Enhanced GD&T parsing and tolerance application
            gdt_info = gdt_interpreter.parse_gdt_description(formatted_text)
            if gdt_info.get("has_gdt") and gdt_info.get("tolerance_value"):
                # Updated column indices for tolerances
                lower_item = table.item(row, 10)  # lower_tolerance
                upper_item = table.item(row, 11)  # upper_tolerance

                if (not lower_item or not lower_item.text()) and (
                    not upper_item or not upper_item.text()
                ):
                    nominal_item = table.item(row, 9)  # nominal
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