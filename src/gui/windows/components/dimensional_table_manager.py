# src/gui/windows/components/dimensional_table_manager.py
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import pandas as pd
from typing import List
from src.models.dimensional.dimensional_result import (
    DimensionalResult,
    DimensionalStatus,
)
from .dimensional_table_ui import DimensionalTableUI


class DimensionalTableManager(DimensionalTableUI):
    """Enhanced table manager with professional styling and improved functionality"""

    def __init__(self, display_columns, column_headers, required_columns, measurement_columns, batch_number):
        super().__init__(display_columns, column_headers, required_columns, measurement_columns, batch_number)
        self.results: List[DimensionalResult] = []

    def _update_tables_with_results(self, results: List[DimensionalResult]):
        """Enhanced results update with comprehensive logging - FIXED VERSION"""
        self._log_message("🔄 STARTING TABLE UPDATE WITH RESULTS", "INFO")
        self._log_message("=" * 50, "INFO")

        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            self._log_message("❌ No parent window or results tabs available", "ERROR")
            return

        # Create results lookup dictionary
        results_dict = {}
        for r in results:
            key = (r.element_id, str(r.batch), str(r.cavity))
            results_dict[key] = r
            self._log_message(f"📋 Result key: {key} -> Status: {r.status.value}", "DEBUG")

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
                    self._log_message(f"⚠️ Row {row + 1}: Missing identifier items", "WARNING")
                    continue

                element_id = element_id_item.text()
                batch = batch_item.text()
                cavity = cavity_item.text()
                key = (element_id, batch, cavity)
                result = results_dict.get(key)

                if result:
                    self._log_message(f"✅ Row {row + 1}: Found result for {element_id}", "DEBUG")
                    self._update_row_with_result(table, row, result)
                    updated_count += 1
                else:
                    self._log_message(f"❌ Row {row + 1}: No result found for key {key}", "WARNING")
                    not_found_count += 1

        # Final summary
        self._log_message("=" * 50, "INFO")
        self._log_message("📊 TABLE UPDATE SUMMARY:", "INFO")
        self._log_message(f"  Rows updated: {updated_count}", "INFO")
        self._log_message(f"  Rows not found: {not_found_count}", "INFO")

        if updated_count > 0:
            self._log_message(f"✅ Successfully updated {updated_count} rows with results", "INFO")
        else:
            self._log_message("❌ No rows were updated - check data matching", "ERROR")

    def _update_row_with_result(self, table: QTableWidget, row: int, result: DimensionalResult):
        """Update single row with result - ENHANCED for all evaluation types"""
        element_id = result.element_id
        self._log_message(f"🔧 Updating {element_id} with result:", "DEBUG")

        # Get evaluation type to determine how to handle this row
        eval_combo = table.cellWidget(row, 8)  # evaluation_type column
        evaluation_type = (eval_combo.currentText() if isinstance(eval_combo, QComboBox) else "Normal")

        self._log_message(f"📋 Evaluation Type: {evaluation_type}", "INFO")

        def format_value(val):
            if val is None or val == "":
                return ""
            try:
                return f"{float(val):.3f}"
            except (ValueError, TypeError):
                return str(val)

        # For Note evaluation type, only show statistics if there are measurements
        if evaluation_type == "Note":
            if result.measurements:
                # Note with measurements - show all statistics
                min_val = format_value(min(result.measurements))
                max_val = format_value(max(result.measurements))
                mean_val = format_value(result.mean) if result.mean is not None else ""
                std_val = format_value(result.std_dev) if result.std_dev is not None else ""
                self._log_message("📝 Note evaluation with measurements: Showing all statistics", "INFO")
            else:
                # Note with no measurements - show nothing
                min_val = ""
                max_val = ""
                mean_val = ""
                std_val = ""
                self._log_message("📝 Note evaluation with no measurements: Setting all statistics to empty", "INFO")
        else:
            # Normal, GD&T, Basic, Informative - show all statistics
            min_val = format_value(min(result.measurements)) if result.measurements else ""
            max_val = format_value(max(result.measurements)) if result.measurements else ""
            mean_val = format_value(result.mean) if result.mean is not None else ""
            std_val = format_value(result.std_dev) if result.std_dev is not None else ""

        # Update statistical columns
        stat_updates = [
            (17, min_val),  # minimum
            (18, max_val),  # maximum
            (19, mean_val),  # mean
            (20, std_val),  # std_deviation
        ]

        for col_idx, value in stat_updates:
            item = table.item(row, col_idx)
            if not item:
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Make read-only
                table.setItem(row, col_idx, item)

            item.setText(str(value))
            # Style statistics columns
            item.setBackground(QColor(248, 249, 250))  # Light gray
            item.setForeground(QColor(52, 58, 64))  # Dark gray text
            font = QFont("Segoe UI", 9)
            item.setFont(font)

        # Handle STATUS column based on evaluation type
        status_item = table.item(row, 21)  # status column
        if not status_item:
            status_item = QTableWidgetItem()
            status_item.setFlags(
                status_item.flags() ^ Qt.ItemIsEditable
            )  # Make read-only
            table.setItem(row, 21, status_item)

        if evaluation_type in ["Basic", "Informative"]:
            # Basic/Informative: No status evaluation, use special status
            status_item.setText("T.E.D.")  # Not Evaluable
            self._apply_status_styling(status_item, "T.E.D.", row, 21)
            self._log_message(
                f"✅ Set T.E.D. status for {evaluation_type} evaluation", "INFO"
            )

        elif evaluation_type == "Note":
            # Notes: Always use force status or default to GOOD
            force_combo = table.cellWidget(row, 22)  # force_status column
            force_status = (
                force_combo.currentText()
                if isinstance(force_combo, QComboBox)
                else "AUTO"
            )

            if force_status == "GOOD":
                final_status = "GOOD"
            elif force_status == "BAD":
                final_status = "BAD"
            else:
                final_status = "GOOD"  # Notes default to GOOD unless forced

            status_item.setText(final_status)
            self._apply_status_styling(status_item, final_status, row, 21)

        else:  # Normal and GD&T evaluations
            # Get force status
            force_combo = table.cellWidget(row, 22)  # force_status column
            force_status = (
                force_combo.currentText()
                if isinstance(force_combo, QComboBox)
                else "AUTO"
            )

            if force_status == "GOOD":
                final_status = "GOOD"
            elif force_status == "BAD":
                final_status = "BAD"
            else:  # AUTO - use calculated status
                final_status = result.status.value

            status_item.setText(final_status)
            self._apply_status_styling(status_item, final_status, row, 21)

        self._log_message(f"📊 Final Status for {element_id}: {status_item.text()}", "INFO")

        self._highlight_measurement_violations(table, row, result, evaluation_type)     # Highlight measurement violations with RED FONT COLOR

    def _apply_status_styling(self, item, status, row, col):
        """Apply status cell coloring - FIXED VERSION with strong colors that override table styles"""
        if not item:
            self._log_message("❌ No item to style!", "ERROR")
            return

        self._log_message(f"🎨 Applying styling - Status: '{status}', Row: {row}, Col: {col}", "INFO")

        original_flags = item.flags()
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

        # Clear any existing styling completely
        item.setData(Qt.BackgroundRole, None)
        item.setData(Qt.ForegroundRole, None)
        item.setData(Qt.FontRole, None)

        # Set font first - bold and slightly larger
        font = QFont("Segoe UI", 10, QFont.Bold)
        item.setFont(font)

        # Apply STRONG colors based on status - using QColor with explicit RGB values
        if status == "GOOD":
            # STRONG GREEN - Forest Green
            bg_color = self.colors["good"]  # Forest Green
            fg_color = self.colors["white"]  # Pure White
            tooltip = "✅ GOOD - All measurements within tolerance"
            self._log_message("🟢 Setting GOOD styling: Forest Green background", "INFO")

        elif status == "BAD":
            # STRONG RED - Fire Brick Red
            bg_color = self.colors["bad"]  # Fire Brick Red
            fg_color = self.colors["white"]  # Pure White
            tooltip = "❌ BAD - One or more measurements out of tolerance"
            self._log_message("🔴 Setting BAD styling: Fire Brick Red background", "INFO")

        elif status == "T.E.D.":  # Not Evaluable (Basic/Informative)
            # STRONG BLUE
            bg_color = self.colors["primary"]  # Strong Blue
            fg_color = self.colors["white"]  # Pure White
            tooltip = "ℹ️ T.E.D. - Theoretical exact dimension is not evaluable (Basic|Informative dimension)"
            self._log_message("🔵 Setting T.E.D. styling: Strong Blue background", "INFO")

        else:  # WARNING/UNKNOWN status
            # STRONG YELLOW/ORANGE
            bg_color = self.colors["warning"]  # Dark Orange
            fg_color = self.colors["black"]  # Black text for contrast
            tooltip = f"⚠️ WARNING - Status: {status}"
            self._log_message("🟡 Setting WARNING styling: Dark Orange background", "INFO")

        # Apply the styling with FORCE - using setData to ensure it sticks
        try:
            # Method 1: Use setData (most reliable)
            item.setData(Qt.BackgroundRole, bg_color)
            item.setData(Qt.ForegroundRole, fg_color)
            item.setData(Qt.ToolTipRole, tooltip)

            # Method 2: Also use direct methods as backup
            item.setBackground(bg_color)
            item.setForeground(fg_color)
            item.setToolTip(tooltip)

            self._log_message(f"✅ Applied colors - BG: RGB({bg_color.red()}, {bg_color.green()}, {bg_color.blue()})", "INFO")
            self._log_message(f"- FG: RGB({fg_color.red()}, {fg_color.green()}, {fg_color.blue()})", "INFO")

            item.setFlags(original_flags)     # CRITICAL: Restore original flags AFTER styling

            # Force immediate visual update
            if hasattr(item, "tableWidget") and item.tableWidget():
                table_widget = item.tableWidget()
                # Update the specific cell
                table_widget.updateItem(item)
                # Force viewport repaint
                table_widget.viewport().update()
                # Additional forced refresh
                table_widget.repaint()
                self._log_message("🔄 Forced table repaint and update", "INFO")

            self._log_message("✅ Status styling applied successfully!", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error applying styling: {str(e)}", "ERROR")
            item.setFlags(original_flags)   # Restore flags even if styling failed

    def _highlight_measurement_violations(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str = "Normal"):
        """Highlight measurement violations - unified logic for GD&T and Normal, tracks original/edited values"""
        measurement_cols = [12, 13, 14, 15, 16]  # measurement columns
        violations_found = 0

        # Skip violation highlighting for Basic/Informative
        if evaluation_type in ["Basic", "Informative"]:
            self._log_message(f"⏭️ Skipping violation check for {evaluation_type} evaluation", "DEBUG")
            return

        # Unified tolerance calculation
        lower_limit = result.nominal + (result.lower_tolerance if result.lower_tolerance is not None else 0)
        upper_limit = result.nominal + (result.upper_tolerance if result.upper_tolerance is not None else 0)
        self._log_message(f"📏 Tolerances - Lower: {result.lower_tolerance}, Upper: {result.upper_tolerance}", "INFO")
        self._log_message(f"📏 Tolerance range: {lower_limit} to {upper_limit}", "INFO")

        for idx, col in enumerate(measurement_cols):
            item = table.item(row, col)
            if not item or not item.text():
                continue
            try:
                value = float(item.text())
                is_violation = not (lower_limit <= value <= upper_limit)
                formatted_value = f"{value:.3f}"
                item.setText(formatted_value)

                key = (row, col)
                og_value = self._original_measurements.get(key)
                if og_value is None:
                    # First run: store original value
                    self._original_measurements[key] = formatted_value
                    og_value = formatted_value
                    was_violation = is_violation
                    is_edited = False
                else:
                    was_violation = not (lower_limit <= float(og_value) <= upper_limit)
                    is_edited = formatted_value != og_value

                # Color logic
                if not is_edited:
                    # Original value
                    if is_violation:
                        item.setForeground(self.colors["bad"])  # Red
                        item.setToolTip("Original measurement violates tolerance")
                        violations_found += 1
                    else:
                        item.setForeground(self.colors["good"])  # Green
                        item.setToolTip("Original measurement within tolerance")
                else:
                    # Edited value
                    if was_violation:
                        item.setForeground(QColor(128, 0, 128))  # Purple
                        item.setToolTip("Edited value (was out of spec)")
                    else:
                        item.setForeground(self.colors["primary"])  # Blue
                        item.setToolTip("Edited value (was in spec or newly added)")

                # Font logic
                if is_violation or is_edited:
                    font = QFont("Segoe UI", 9, QFont.Bold)
                else:
                    font = QFont("Segoe UI", 9)
                item.setFont(font)

            except ValueError:
                self._log_message(f"⚠️ Invalid measurement value in column {col}", "WARNING")

        if violations_found > 0:
            self._log_message(f"🚨 {violations_found} measurement violations found for {result.element_id}", "WARNING")

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Enhanced dataframe extraction with comprehensive logging - FIXED VERSION"""
        self._log_message("🔍 STARTING DATA EXTRACTION FROM TABLES", "INFO")
        self._log_message("=" * 50, "INFO")

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
                self._log_message(
                    f"⚠️ Tab {tab_idx} is not a QTableWidget, skipping", "WARNING"
                )
                continue

            tab_name = self.parent_window.results_tabs.tabText(tab_idx)
            self._log_message(
                f"📋 Processing Tab: {tab_name} ({table.rowCount()} rows)", "INFO"
            )

            # Process each row in the table
            for row in range(table.rowCount()):
                total_rows_processed += 1
                row_data = {}

                self._log_message(f"🔍 Processing Row {row + 1}:", "DEBUG")

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
                        self._log_message(
                            f"📝 {col_name} (dropdown): '{value}'", "DEBUG"
                        )
                    else:
                        # Handle regular table items
                        item = table.item(row, col)
                        value = item.text().strip() if item and item.text() else None
                        if value == "":
                            value = None
                        self._log_message(f"📝 {col_name}: '{value}'", "DEBUG")

                    # Process the value
                    if value is None:
                        row_data[col_name] = None
                    else:
                        # Enhanced numeric validation
                        numeric_columns = [
                            "nominal",
                            "lower_tolerance",
                            "upper_tolerance",
                        ] + self.measurement_columns
                        if col_name in numeric_columns:
                            try:
                                numeric_value = float(value)
                                row_data[col_name] = numeric_value
                                self._log_message(
                                    f" ✅ Converted to numeric: {numeric_value}",
                                    "DEBUG",
                                )
                            except (ValueError, TypeError):
                                self._log_message(
                                    f"❌ Invalid numeric value: {value}",
                                    "WARNING",
                                )
                                row_data[col_name] = None
                        else:
                            row_data[col_name] = value

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number
                    self._log_message(
                        f"🔧 Auto-filled batch: {self.batch_number}", "DEBUG"
                    )

                # Validation logic
                is_valid_row = self._validate_row_data(row_data, row + 1)

                if is_valid_row:
                    all_data.append(row_data)
                    valid_rows += 1
                    self._log_message(f"✅ Row {row + 1} added to dataset", "INFO")
                else:
                    skipped_rows += 1
                    self._log_message(
                        f"❌ Row {row + 1} skipped (validation failed)", "WARNING"
                    )

        # Final logging
        self._log_message("=" * 50, "INFO")
        self._log_message("📊 DATA EXTRACTION SUMMARY:", "INFO")
        self._log_message(f"Total rows processed: {total_rows_processed}", "INFO")
        self._log_message(f"Valid rows: {valid_rows}", "INFO")
        self._log_message(f"Skipped rows: {skipped_rows}", "INFO")
        self._log_message("=" * 50, "INFO")

        if not all_data:
            self._log_message("❌ No valid data extracted", "ERROR")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        self._log_message(f"✅ DataFrame created with {len(df)} records", "INFO")

        # Log column information
        self._log_message("📋 DataFrame columns:", "INFO")
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            self._log_message(
                f"{col}: {non_null_count}/{len(df)} non-null values", "INFO"
            )
        return df

    def _validate_row_data(self, row_data: dict, row_number: int) -> bool:
        """Validate row data with comprehensive logging - FIXED VERSION"""
        self._log_message(f"🔍 Validating Row {row_number}:", "DEBUG")

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

        # For Notes, we only need element_id and description
        if evaluation_type == "Note":
            self._log_message("✅ Note entry - basic validation passed", "DEBUG")
            return True

        # For all other types, check nominal and measurements
        nominal = row_data.get("nominal")

        # CRITICAL FIX: Explicitly check for None, not falsy values
        if nominal is None:
            self._log_message("❌ Missing nominal value", "WARNING")
            return False

        # Additional explicit check to ensure it's a valid number
        try:
            nominal_float = float(nominal)
            self._log_message(
                f"nominal: {nominal_float} (✅ Valid number, including zero)", "DEBUG"
            )
        except (ValueError, TypeError):
            self._log_message(f"❌ Invalid nominal value: {nominal}", "WARNING")
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

        self._log_message(f"measurements: {measurement_count}/5 provided", "DEBUG")

        if not has_measurements:
            self._log_message("❌ No measurements provided", "WARNING")
            return False

        # Check tolerances (optional but log if missing)
        lower_tol = row_data.get("lower_tolerance")
        upper_tol = row_data.get("upper_tolerance")

        if lower_tol is None and upper_tol is None:
            self._log_message(
                "⚠️ No tolerances provided - will use force_status or default evaluation",
                "WARNING",
            )
        else:
            self._log_message(f"tolerances: {lower_tol} / {upper_tol}", "DEBUG")

        self._log_message("✅ Validation passed", "DEBUG")
        return True

    def _filter_dimensions_for_evaluation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter dataframe to only include dimensions that should be evaluated"""
        if "evaluation_type" not in df.columns:
            return df

        # Only process Normal, Note, and GD&T dimensions for status evaluation
        # Basic and Informative get calculations but NO status
        evaluation_df = df[
            df["evaluation_type"].isin(["Normal", "Note", "GD&T"])
        ].copy()

        self._log_message(
            f"Filtered {len(df)} total dimensions to {len(evaluation_df)} for evaluation "
            + f"({len(df[df['evaluation_type'] == 'Basic'])} Basic, "
            + f"{len(df[df['evaluation_type'] == 'Informative'])} Informative excluded from status evaluation)"
        )

        return evaluation_df

    def _handle_note_entries(self, results):
        """Handle all entry types and create appropriate DimensionalResult objects"""
        all_results = []

        for result in results:
            if hasattr(result, "to_dict"):
                row = result.to_dict()
            else:
                row = result

            try:
                # Extract measurements from the row data
                measurements = []
                for i in range(1, 6):  # measurement_1 to measurement_5
                    meas_key = f"measurement_{i}"
                    if meas_key in row and row[meas_key] is not None:
                        try:
                            measurements.append(float(row[meas_key]))
                        except (ValueError, TypeError):
                            continue

                # Calculate mean and std_dev if measurements exist
                if measurements:
                    mean_val = sum(measurements) / len(measurements)
                    if len(measurements) > 1:
                        variance = sum((x - mean_val) ** 2 for x in measurements) / (
                            len(measurements) - 1
                        )
                        std_dev_val = variance**0.5
                    else:
                        std_dev_val = 0.0
                else:
                    mean_val = 0.0
                    std_dev_val = 0.0
                    measurements = []

                # Get evaluation type
                evaluation_type = row.get("evaluation_type", "Normal")
                nominal_val = float(row.get("nominal", 0))
                lower_tol = row.get("lower_tolerance")
                upper_tol = row.get("upper_tolerance")

                # Calculate deviations and check tolerances
                deviations = [meas - nominal_val for meas in measurements]
                out_of_spec_count = 0

                if lower_tol is not None and upper_tol is not None and measurements:
                    try:
                        lower_tol = float(lower_tol)
                        upper_tol = float(upper_tol)

                        for meas in measurements:
                            if evaluation_type == "GD&T" and nominal_val == 0.0:
                                # GD&T with zero nominal
                                if lower_tol == 0.0:
                                    # Unilateral tolerance
                                    if abs(meas) > upper_tol:
                                        out_of_spec_count += 1
                                else:
                                    # Bilateral tolerance around zero
                                    if not (lower_tol <= meas <= upper_tol):
                                        out_of_spec_count += 1
                            else:
                                # Normal tolerance check
                                if meas < (nominal_val + lower_tol) or meas > (
                                    nominal_val + upper_tol
                                ):
                                    out_of_spec_count += 1

                    except (ValueError, TypeError):
                        pass

                # Determine status based on evaluation type
                force_status = row.get("force_status", "AUTO")

                if evaluation_type in ["Basic", "Informative"]:
                    # These types are not evaluable
                    status = (
                        DimensionalStatus.GOOD
                    )  # Placeholder, will be overridden with "T.E.D."
                elif force_status == "GOOD":
                    status = DimensionalStatus.GOOD
                elif force_status == "BAD":
                    status = DimensionalStatus.BAD
                elif evaluation_type == "Note":
                    status = DimensionalStatus.GOOD  # Notes default to GOOD
                else:
                    # Auto-determine based on out-of-spec count
                    status = (
                        DimensionalStatus.BAD
                        if out_of_spec_count > 0
                        else DimensionalStatus.GOOD
                    )

                # Create DimensionalResult
                note_result = DimensionalResult(
                    element_id=row.get("element_id", ""),
                    batch=row.get("batch", ""),
                    cavity=row.get("cavity", ""),
                    classe=row.get("class", ""),
                    description=row.get("description", ""),
                    nominal=nominal_val,
                    lower_tolerance=lower_tol,
                    upper_tolerance=upper_tol,
                    measurements=measurements,
                    deviation=deviations,
                    mean=mean_val,
                    std_dev=std_dev_val,
                    out_of_spec_count=out_of_spec_count,
                    status=status,
                    gdt_flags={},
                    datum_element_id=row.get("datum"),
                    feature_type=evaluation_type,
                    warnings=[],
                )

                all_results.append(note_result)

            except Exception as e:
                self._log_message(
                    f"Error creating DimensionalResult: {str(e)}", "ERROR"
                )
                continue

        return all_results

    def _get_processed_dataframe(self) -> pd.DataFrame:
        """Get dataframe ready for processing with proper filtering"""
        df = self._get_dataframe_from_tables()

        if df.empty:
            return df

        # Filter for evaluation
        filtered_df = self._filter_dimensions_for_evaluation(df)
        processing_df = filtered_df[
            filtered_df["evaluation_type"] != "Note"
        ].copy()  # Remove Note entries from processing (they'll be handled separately)

        return processing_df