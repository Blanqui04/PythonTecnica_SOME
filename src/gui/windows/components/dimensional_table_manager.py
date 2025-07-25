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
from src.models.dimensional.dimensional_result import DimensionalResult


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

        # Enhanced dropdown options
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

        # Optimized column widths
        column_widths = {
            0: 90,  # element_id
            1: 60,  # batch
            2: 60,  # cavity
            3: 80,  # class
            4: 220,  # description
            5: 120,  # measuring_instrument
            6: 80,  # nominal
            7: 90,  # lower_tolerance
            8: 90,  # upper_tolerance
            9: 85,  # measurement_1
            10: 85,  # measurement_2
            11: 85,  # measurement_3
            12: 85,  # measurement_4
            13: 85,  # measurement_5
            14: 75,  # minimum
            15: 75,  # maximum
            16: 75,  # mean
            17: 85,  # std_deviation
            18: 80,  # status
            19: 100,  # force_status
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
        }

        for col, value in defaults.items():
            item = QTableWidgetItem(str(value))
            table.setItem(row, col, item)

        # Add enhanced dropdown widgets
        self._add_enhanced_dropdowns(table, row)

        # Style calculated columns as read-only
        for col in range(14, 20):  # calculated columns
            item = QTableWidgetItem("")
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            item.setBackground(self.colors["readonly"])
            item.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
            table.setItem(row, col, item)

    def _add_enhanced_dropdowns(self, table: QTableWidget, row: int):
        """Add professional dropdown widgets to specific columns"""
        # Class dropdown (column 3)
        class_combo = QComboBox()
        class_combo.addItems(self.class_options)
        class_combo.setStyleSheet(self._get_combo_style())
        table.setCellWidget(row, 3, class_combo)

        # Measuring instrument dropdown (column 5)
        instrument_combo = QComboBox()
        instrument_combo.addItems(self.instrument_options)
        instrument_combo.setStyleSheet(self._get_combo_style())
        table.setCellWidget(row, 5, instrument_combo)

        # Force status dropdown (column 19)
        force_combo = QComboBox()
        force_combo.addItems(self.force_status_options)
        force_combo.setCurrentText("AUTO")  # Default to AUTO
        force_combo.setStyleSheet(self._get_combo_style())
        table.setCellWidget(row, 19, force_combo)

    def _get_combo_style(self) -> str:
        """Professional combobox styling"""
        return """
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 8px;
                color: #495057;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                min-height: 20px;
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
                width: 20px;
                border-left: 1px solid #ced4da;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOSA0IiBzdHJva2U9IiM2Yzc1N2QiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                outline: none;
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

        return f"ELEM_{next_num:03d}"

    def _duplicate_row(self, table: QTableWidget):
        """Enhanced duplicate row with proper dropdown handling"""
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
            elif col in [3, 5, 19]:  # Dropdown columns
                if col == 3:  # class
                    combo = QComboBox()
                    combo.addItems(self.class_options)
                    combo.setCurrentText(value)
                    combo.setStyleSheet(self._get_combo_style())
                    table.setCellWidget(new_row, col, combo)
                elif col == 5:  # measuring_instrument
                    combo = QComboBox()
                    combo.addItems(self.instrument_options)
                    combo.setCurrentText(value)
                    combo.setStyleSheet(self._get_combo_style())
                    table.setCellWidget(new_row, col, combo)
                elif col == 19:  # force_status
                    combo = QComboBox()
                    combo.addItems(self.force_status_options)
                    combo.setCurrentText(value if value else "AUTO")
                    combo.setStyleSheet(self._get_combo_style())
                    table.setCellWidget(new_row, col, combo)
            elif col >= 14:  # Calculated columns - make read-only
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
        """Enhanced results update with tolerance violation highlighting"""
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            return

        results_dict = {(r.element_id, str(r.batch), str(r.cavity)): r for r in results}

        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            for row in range(table.rowCount()):
                # Get row identifiers
                element_id_item = table.item(row, 0)
                batch_item = table.item(row, 1)
                cavity_item = table.item(row, 2)

                if not all([element_id_item, batch_item, cavity_item]):
                    continue

                key = (element_id_item.text(), batch_item.text(), cavity_item.text())
                result = results_dict.get(key)

                if result:
                    self._update_row_with_result(table, row, result)

        if self.parent_window:
            self.parent_window._log_message(
                f"✅ Updated tables with {len(results)} results"
            )

    def _update_row_with_result(
        self, table: QTableWidget, row: int, result: DimensionalResult
    ):
        """Update single row with result and highlight violations"""
        # Get tolerance values for violation checking
        lower_tol_item = table.item(row, 7)
        upper_tol_item = table.item(row, 8)

        lower_tol = None
        upper_tol = None

        try:
            if lower_tol_item and lower_tol_item.text():
                lower_tol = float(lower_tol_item.text())
            if upper_tol_item and upper_tol_item.text():
                upper_tol = float(upper_tol_item.text())
        except ValueError:
            pass

        # Update calculated columns with enhanced formatting
        calc_data = [
            (
                14,
                f"{min(result.measurements):.4f}" if result.measurements else "",
                min(result.measurements) if result.measurements else None,
            ),
            (
                15,
                f"{max(result.measurements):.4f}" if result.measurements else "",
                max(result.measurements) if result.measurements else None,
            ),
            (16, f"{result.mean:.4f}" if result.mean else "", result.mean),
            (17, f"{result.std_dev:.4f}" if result.std_dev else "", result.std_dev),
            (18, result.status.value, None),
        ]

        for col_idx, display_value, numeric_value in calc_data:
            item = table.item(row, col_idx)
            if not item:
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)

            item.setText(str(display_value))
            item.setFont(QFont("Segoe UI", 9, QFont.DemiBold))

            # Enhanced status coloring
            if col_idx == 18:  # status column
                if display_value == "GOOD":
                    item.setBackground(self.colors["good"])
                    item.setForeground(QColor(39, 174, 96))  # Dark green text
                elif display_value == "BAD":
                    item.setBackground(self.colors["bad"])
                    item.setForeground(QColor(231, 76, 60))  # Dark red text
                else:
                    item.setBackground(self.colors["warning"])
                    item.setForeground(QColor(243, 156, 18))  # Dark orange text

            # Highlight tolerance violations in measurement columns
            elif col_idx in [14, 15, 16] and numeric_value is not None:
                if self._is_outside_tolerance(numeric_value, lower_tol, upper_tol):
                    item.setBackground(self.colors["bad"])
                    item.setForeground(QColor(255, 255, 255))  # White text for contrast
                    item.setToolTip(
                        f"⚠️ Value {numeric_value:.4f} is outside tolerance!"
                    )
                else:
                    item.setBackground(self.colors["readonly"])
                    item.setForeground(
                        QColor(39, 174, 96)
                    )  # Green text for good values

        # Also highlight individual measurement violations
        self._highlight_measurement_violations(table, row, result, lower_tol, upper_tol)

    def _highlight_measurement_violations(
        self,
        table: QTableWidget,
        row: int,
        result: DimensionalResult,
        lower_tol,
        upper_tol,
    ):
        """Highlight individual measurement cells that violate tolerance"""
        measurement_cols = [9, 10, 11, 12, 13]  # measurement columns

        for i, col in enumerate(measurement_cols):
            item = table.item(row, col)
            if item and item.text():
                try:
                    value = float(item.text())
                    if self._is_outside_tolerance(value, lower_tol, upper_tol):
                        item.setBackground(self.colors["bad"])
                        item.setForeground(QColor(255, 255, 255))
                        item.setToolTip(
                            f"⚠️ Measurement {value:.4f} violates tolerance!"
                        )
                        # Add bold font for emphasis
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    else:
                        # Reset to normal styling for good values
                        item.setBackground(self.colors["white"])
                        item.setForeground(QColor(52, 73, 94))
                        item.setToolTip("")
                except ValueError:
                    pass

    def _is_outside_tolerance(self, value: float, lower_tol, upper_tol) -> bool:
        """Check if value is outside tolerance range"""
        if lower_tol is not None and value < lower_tol:
            return True
        if upper_tol is not None and value > upper_tol:
            return True
        return False

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Enhanced dataframe extraction with dropdown value handling"""
        all_data = []

        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            return pd.DataFrame()

        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            for row in range(table.rowCount()):
                row_data = {}
                valid_row = False

                for col, col_name in enumerate(self.display_columns[:20]):
                    # Handle dropdown widgets
                    cell_widget = table.cellWidget(row, col)
                    if isinstance(cell_widget, QComboBox):
                        value = cell_widget.currentText().strip()
                        if not value or value == "":
                            value = None
                    else:
                        # Handle regular table items
                        item = table.item(row, col)
                        value = item.text().strip() if item and item.text() else None

                    if not value:
                        value = None
                    else:
                        # Enhanced numeric validation
                        if (
                            col_name
                            in ["nominal", "lower_tolerance", "upper_tolerance"]
                            + self.measurement_columns
                        ):
                            try:
                                numeric_value = float(value)
                                row_data[col_name] = numeric_value
                                if col_name == "nominal":
                                    valid_row = True
                            except (ValueError, TypeError):
                                if self.parent_window:
                                    self.parent_window._log_message(
                                        f"⚠️ Invalid numeric value in row {row + 1}, column {col_name}: {value}",
                                        "WARNING",
                                    )
                                row_data[col_name] = None
                        else:
                            row_data[col_name] = value
                            if col_name in ["element_id", "description"] and value:
                                valid_row = True

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number

                # Enhanced validation
                has_element_id = row_data.get("element_id") is not None
                has_description = row_data.get("description") is not None
                has_nominal = row_data.get("nominal") is not None
                has_measurements = any(
                    row_data.get(f"measurement_{i}") is not None for i in range(1, 6)
                )

                if (
                    has_element_id
                    and has_description
                    and has_nominal
                    and has_measurements
                ):
                    all_data.append(row_data)
                elif valid_row:
                    missing = []
                    if not has_element_id:
                        missing.append("element_id")
                    if not has_description:
                        missing.append("description")
                    if not has_nominal:
                        missing.append("nominal")
                    if not has_measurements:
                        missing.append("measurements")

                    if self.parent_window:
                        self.parent_window._log_message(
                            f"⚠️ Skipping row {row + 1}: missing {', '.join(missing)}",
                            "WARNING",
                        )

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        if self.parent_window:
            self.parent_window._log_message(
                f"📊 Extracted {len(df)} valid records for processing"
            )

        return df

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
                    item.setText(f"{value:.4f}")
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

                    lower_item.setText(f"{lower_tol:.4f}")
                    upper_item.setText(f"{upper_tol:.4f}")

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
