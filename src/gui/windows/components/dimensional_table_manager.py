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

# Simple GD&T helper dialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pandas as pd

import sip
from typing import List


from src.models.dimensional.dimensional_result import DimensionalResult


class DimensionalTableManager:
    """Manages table operations and data handling"""

    def __init__(
        self,
        display_columns,
        column_headers,
        required_columns,
        measurement_columns,
        batch_number,
    ):
        self.parent_window = None  # Will be set by main window
        self.display_columns = display_columns
        self.column_headers = column_headers
        self.required_columns = required_columns
        self.measurement_columns = measurement_columns
        self.batch_number = batch_number
        self.results_tabs = QTabWidget()
        self.results: List[DimensionalResult] = []

    def set_parent_window(self, parent):
        self.parent_window = parent

    def _create_results_table(self) -> QTableWidget:
        """Create a results table with proper configuration"""
        table = QTableWidget()
        table.setColumnCount(len(self.display_columns))
        table.setHorizontalHeaderLabels(self.column_headers)

        # Configure table
        table.setSortingEnabled(False)  # Disable during editing
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(table, pos)
        )

        # Set column widths
        header = table.horizontalHeader()
        header.setStretchLastSection(True)

        # Set specific column widths
        column_widths = {
            0: 80,  # element_id
            1: 60,  # batch
            2: 60,  # cavity
            3: 60,  # class
            4: 200,  # description
            5: 80,  # nominal
            6: 120,  # measuring_instrument
            7: 80,  # lower_tolerance
            8: 80,  # upper_tolerance
            9: 80,  # measurement_1
            10: 80,  # measurement_2
            11: 80,  # measurement_3
            12: 80,  # measurement_4
            13: 80,  # measurement_5
            14: 70,  # minimum
            15: 70,  # maximum
            16: 70,  # mean
            17: 70,  # std_deviation
            18: 70,  # status
            19: 90,  # force_status
        }

        for col, width in column_widths.items():
            table.setColumnWidth(col, width)

        # Connect cell changed signal
        table.cellChanged.connect(self._on_cell_changed)

        return table

    def _mark_unsaved_changes(self):
        """Create summary widget for overall statistics"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Statistics display
        self.stats_label = QLabel("No analysis performed yet")
        self.stats_label.setStyleSheet(
            "QLabel { font-size: 14px; padding: 10px; background-color: #f0f0f0; }"
        )
        layout.addWidget(self.stats_label)

        # Cavity comparison
        self.cavity_group = QGroupBox("Cavity Comparison")
        self.cavity_layout = QVBoxLayout()
        self.cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(self.cavity_group)

        # Feature type breakdown
        self.feature_group = QGroupBox("Feature Type Breakdown")
        self.feature_layout = QVBoxLayout()
        self.feature_group.setLayout(self.feature_layout)
        layout.addWidget(self.feature_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _show_context_menu(self, table: QTableWidget, position):
        """Show context menu for table operations"""
        if not self.parent_window.manual_mode:
            return

        menu = QMenu()

        # Add row operations
        add_row_action = menu.addAction("➕ Add Row")
        add_row_action.triggered.connect(self._add_manual_row)

        duplicate_row_action = menu.addAction("📋 Duplicate Row")
        duplicate_row_action.triggered.connect(self._duplicate_row)

        delete_row_action = menu.addAction("🗑️ Delete Row")
        delete_row_action.triggered.connect(self._delete_row)

        menu.addSeparator()

        # GD&T helper
        gdt_helper_action = menu.addAction("🔧 GD&T Helper")
        gdt_helper_action.triggered.connect(lambda: self._show_gdt_helper(table))

        # Copy/paste operations
        menu.addSeparator()
        copy_action = menu.addAction("📄 Copy Row")
        copy_action.triggered.connect(lambda: self._copy_row(table))

        paste_action = menu.addAction("📄 Paste Row")
        paste_action.triggered.connect(lambda: self._paste_row(table))

        menu.exec_(table.mapToGlobal(position))

    def _on_cell_changed(self, row: int, col: int):
        """Handle cell value changes"""
        if self.parent_window:
            self.parent_window._mark_unsaved_changes()

        # FIX: Access results_tabs through parent_window
        current_table = (
            self.parent_window.results_tabs.currentWidget()
            if self.parent_window
            else None
        )
        if not isinstance(current_table, QTableWidget):
            return

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Extract dataframe from all tables with proper validation"""
        all_data = []

        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            for row in range(table.rowCount()):
                row_data = {}
                valid_row = False

                for col, col_name in enumerate(
                    self.display_columns[:15]
                ):  # Only input columns (0-13)
                    item = table.item(row, col)
                    value = item.text().strip() if item and item.text() else None

                    # Handle empty values
                    if not value:
                        value = None
                    else:
                        # Special handling for numeric columns
                        if (
                            col_name
                            in ["nominal", "lower_tolerance", "upper_tolerance"]
                            + self.measurement_columns
                        ):
                            try:
                                # Try to convert to float
                                numeric_value = float(value)
                                row_data[col_name] = numeric_value
                                # Check if we have essential data
                                if col_name == "nominal":
                                    valid_row = True
                            except (ValueError, TypeError):
                                self.parent_window._log_message(
                                    f"Invalid numeric value in row {row + 1}, column {col_name}: {value}",
                                    "WARNING",
                                )
                                row_data[col_name] = None
                        else:
                            # String columns
                            row_data[col_name] = value
                            # Check if we have essential data
                            if col_name in ["element_id", "description"] and value:
                                valid_row = True

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number

                # Validate that we have minimum required data
                has_element_id = row_data.get("element_id") is not None
                has_description = row_data.get("description") is not None
                has_nominal = row_data.get("nominal") is not None
                has_measurements = any(
                    row_data.get(f"measurement_{i}") is not None for i in range(1, 6)
                )

                # Only add rows with essential data
                if (
                    has_element_id
                    and has_description
                    and has_nominal
                    and has_measurements
                ):
                    all_data.append(row_data)
                elif valid_row:  # Log why row was skipped
                    missing = []
                    if not has_element_id:
                        missing.append("element_id")
                    if not has_description:
                        missing.append("description")
                    if not has_nominal:
                        missing.append("nominal")
                    if not has_measurements:
                        missing.append("measurements")
                    self.parent_window._log_message(
                        f"Skipping row {row + 1}: missing {', '.join(missing)}",
                        "WARNING",
                    )

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        # Log the data being processed
        self.parent_window._log_message(
            f"Extracted {len(df)} valid records for processing"
        )

        return df

    def _update_tables_with_results(self, results: List[DimensionalResult]):
        """Update tables with analysis results"""
        # Create a lookup dict for results
        results_dict = {(r.element_id, str(r.batch), str(r.cavity)): r for r in results}

        # Update each table - FIX: Access results_tabs through parent_window
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            self.parent_window._log_message(
                "No parent window or results_tabs found", "ERROR"
            )
            return

        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)

            if not isinstance(table, QTableWidget):
                continue

            for row in range(table.rowCount()):
                # Get row identifier
                element_id_item = table.item(row, 0)
                batch_item = table.item(row, 1)
                cavity_item = table.item(row, 2)

                if not all([element_id_item, batch_item, cavity_item]):
                    continue

                key = (element_id_item.text(), batch_item.text(), cavity_item.text())
                result = results_dict.get(key)

                if result:
                    # Update calculated columns
                    calc_values = [
                        f"{min(result.measurements):.4f}"
                        if result.measurements
                        else "",
                        f"{max(result.measurements):.4f}"
                        if result.measurements
                        else "",
                        f"{result.mean:.4f}" if result.mean else "",
                        f"{result.std_dev:.4f}" if result.std_dev else "",
                        result.status.value,
                    ]

                    for i, value in enumerate(calc_values):
                        col_idx = 14 + i  # Start from calculated columns
                        item = table.item(row, col_idx)
                        if not item:
                            item = QTableWidgetItem()
                            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                            table.setItem(row, col_idx, item)

                        item.setText(str(value))

                        # Color code status
                        if col_idx == 18:  # status column
                            if value == "GOOD":
                                item.setBackground(QColor(144, 238, 144))  # Light green
                            elif value == "BAD":
                                item.setBackground(QColor(255, 182, 193))  # Light red
                            else:
                                item.setBackground(
                                    QColor(255, 255, 224)
                                )  # Light yellow
                else:
                    # Log when no matching result is found
                    self.parent_window._log_message(
                        f"No result found for key: {key}", "WARNING"
                    )

        self.parent_window._log_message(f"Updated tables with {len(results)} results")

    def _safe_clear_layout(self, layout):
        if layout and not sip.isdeleted(layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget and not sip.isdeleted(widget):
                    widget.setParent(None)

    def clear_all_tables(self):
        """Clear all tables and reset state"""
        if self.parent_window:
            # Clear all tabs
            while self.parent_window.results_tabs.count():
                widget = self.parent_window.results_tabs.widget(0)
                self.parent_window.results_tabs.removeTab(0)
                if widget:
                    widget.deleteLater()

            self.parent_window._log_message("All tables cleared")

    def _clear_data(self):
        """Clear all data from tables"""
        try:
            reply = QMessageBox.question(
                self,
                "Clear All Data",
                "Are you sure you want to clear all data? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Clear all tabs except summary
                while self.results_tabs.count() > 1:
                    self.results_tabs.removeTab(1)

                # 🛡️ Check if stats_label still exists and is valid
                if self.stats_label and not sip.isdeleted(self.stats_label):
                    self.stats_label.setText("No analysis performed yet")

                # ✅ Safely clear layouts using helper
                self._safe_clear_layout(self.cavity_layout)
                self._safe_clear_layout(self.feature_layout)

                self.results = []
                if self.export_button and not sip.isdeleted(self.export_button):
                    self.export_button.setEnabled(False)

                self._clear_unsaved_changes()
                self._log_message("All data cleared")

                # If in manual mode, add empty table
                if self.manual_mode:
                    self._prepare_manual_table()

        except RuntimeError as e:
            self._log_message(f"Clear data error: {e}", "WARNING")

    def _show_gdt_helper(self, table: QTableWidget):
        """Show GD&T helper dialog"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("GD&T Helper")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel("""
        <b>GD&T Input Examples:</b><br>
        • position 0.5(M) A B C<br>
        • parallelism 0.1 A<br>
        • flatness 0.05<br>
        • circularity 0.02<br>
        • profile 0.2 A B<br><br>
        <b>Material Conditions:</b><br>
        • (M) = Maximum Material Condition<br>
        • (L) = Least Material Condition<br>
        • (S) = Regardless of Feature Size
        """)
        layout.addWidget(instructions)

        # Text input
        layout.addWidget(QLabel("Enter GD&T Description:"))
        text_input = QTextEdit()
        text_input.setMaximumHeight(80)
        layout.addWidget(text_input)

        # Buttons
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply to Row")
        apply_btn.clicked.connect(
            lambda: self._apply_gdt_to_row(
                table, current_row, text_input.toPlainText(), dialog
            )
        )
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _apply_gdt_to_row(self, table: QTableWidget, row: int, gdt_text: str, dialog):
        """Apply GD&T text to table row"""
        if gdt_text.strip():
            # Format the GD&T text
            from src.models.dimensional.gdt_interpreter import GDTInterpreter

            gdt_interpreter = GDTInterpreter()
            formatted_text = gdt_interpreter.format_gdt_display(gdt_text)

            # Apply to description column
            desc_item = table.item(row, 4)  # description column
            if not desc_item:
                desc_item = QTableWidgetItem()
                table.setItem(row, 4, desc_item)

            desc_item.setText(formatted_text)

            # Parse GD&T for tolerance if applicable
            gdt_info = gdt_interpreter.parse_gdt_description(formatted_text)
            if gdt_info.get("has_gdt") and gdt_info.get("tolerance_value"):
                # Apply tolerance to tolerance columns if they're empty
                lower_item = table.item(row, 6)  # lower_tolerance
                upper_item = table.item(row, 7)  # upper_tolerance

                if (not lower_item or not lower_item.text()) and (
                    not upper_item or not upper_item.text()
                ):
                    nominal_item = table.item(row, 5)
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
                        table.setItem(row, 6, lower_item)
                    if not upper_item:
                        upper_item = QTableWidgetItem()
                        table.setItem(row, 7, upper_item)

                    lower_item.setText(str(lower_tol))
                    upper_item.setText(str(upper_tol))

            self._mark_unsaved_changes()

        dialog.accept()

    def _copy_row(self, table: QTableWidget):
        """Copy current row to clipboard"""
        current_row = table.currentRow()
        if current_row < 0:
            return

        row_data = []
        for col in range(table.columnCount()):
            item = table.item(current_row, col)
            row_data.append(item.text() if item else "")

        # Store in instance variable for simple paste operation
        self._copied_row_data = row_data
        self._log_message(f"Copied row {current_row + 1}")

    def _paste_row(self, table: QTableWidget):
        """Paste copied row data"""
        if not hasattr(self, "_copied_row_data"):
            QMessageBox.information(self, "No Data", "No row data copied.")
            return

        current_row = table.currentRow()
        if current_row < 0:
            return

        for col, value in enumerate(self._copied_row_data):
            if col < 13:  # Only paste input columns, not calculated ones
                item = table.item(current_row, col)
                if not item:
                    item = QTableWidgetItem()
                    table.setItem(current_row, col, item)
                item.setText(value)

        self._mark_unsaved_changes()
        self._log_message(f"Pasted data to row {current_row + 1}")

    def _populate_default_row(self, table: QTableWidget, row: int):
        """Populate a row with default values"""
        defaults = {
            1: str(self.batch_number),  # batch
            2: "1",  # cavity (default to 1)
        }

        for col, value in defaults.items():
            item = QTableWidgetItem(str(value))
            table.setItem(row, col, item)

        # Make calculated columns read-only (min, max, mean, std_dev, status)
        for col in range(14, 19):  # columns 13-17 are calculated
            item = QTableWidgetItem("")
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            item.setBackground(QColor(240, 240, 240))
            table.setItem(row, col, item)
