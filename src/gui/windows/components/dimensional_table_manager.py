# src/gui/windows/components/dimensional_table_manager.py
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import pandas as pd
from typing import List, Dict
from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus
from .dimensional_table_ui import DimensionalTableUI
from datetime import datetime

class DimensionalTableManager(DimensionalTableUI):
    """Optimized table manager with improved performance"""

    def __init__(self, display_columns, column_headers, required_columns, measurement_columns, batch_number):
        super().__init__(display_columns, column_headers, required_columns, measurement_columns, batch_number)
        self.results: List[DimensionalResult] = []
        self._original_measurements = {}
        self._last_update_time = datetime.now()
        self._update_threshold = 2.0  # Reduce update frequency

    def _log_message(self, message: str, level: str = "INFO"):
        """Minimal logging for performance"""
        if level in ["ERROR", "WARNING"]:
            if hasattr(self, 'parent_window') and self.parent_window:
                if hasattr(self.parent_window, '_log_message'):
                    self.parent_window._log_message(message, level)

    def _update_tables_with_results(self, results: List[DimensionalResult]):
        """Optimized table update with batch operations"""
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            self._log_message("No parent window available", "ERROR")
            return

        # Create lookup dictionary once
        results_dict = {(r.element_id, str(r.batch), str(r.cavity)): r for r in results}
        
        updated_count = 0
        
        # Process all tabs
        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue
            
            # Batch update for this table
            updated_count += self._update_single_table(table, results_dict)
        
        if updated_count == 0:
            self._log_message("No rows were updated - check data matching", "WARNING")

    def _update_single_table(self, table: QTableWidget, results_dict: Dict) -> int:
        """OPTIMIZED: Update single table with minimal operations"""
        updated_count = 0
        
        # Disable updates during batch operation for performance
        table.setUpdatesEnabled(False)
        
        try:
            # Pre-fetch all items to avoid repeated lookups
            row_data = []
            for row in range(table.rowCount()):
                element_id_item = table.item(row, 0)
                batch_item = table.item(row, 1)
                cavity_item = table.item(row, 2)
                
                if all([element_id_item, batch_item, cavity_item]):
                    key = (element_id_item.text(), batch_item.text(), cavity_item.text())
                    result = results_dict.get(key)
                    if result:
                        row_data.append((row, result))
            
            # Batch update all matching rows
            for row, result in row_data:
                self._update_row(table, row, result)
                updated_count += 1
        
        finally:
            # Re-enable updates and refresh once
            table.setUpdatesEnabled(True)
            table.viewport().update()
        
        return updated_count

    def _update_row(self, table: QTableWidget, row: int, result: DimensionalResult):
        """OPTIMIZED: Single row update with minimal object creation"""
        # Get evaluation type once
        eval_combo = table.cellWidget(row, 8)
        evaluation_type = eval_combo.currentText() if isinstance(eval_combo, QComboBox) else "Normal"

        # Prepare statistics data - use list comprehension for efficiency
        if evaluation_type == "Note":
            stat_data = [(col, "") for col in [17, 18, 19, 20, 21, 22]]
        else:
            stat_data = [
                (17, f"{result.mean:.3f}" if result.mean is not None else ""),
                (18, f"{result.std_dev:.3f}" if result.std_dev is not None else ""),
                (19, f"{min(result.measurements):.3f}" if result.measurements else ""),
                (20, f"{max(result.measurements):.3f}" if result.measurements else ""),
                (21, f"{result.pp:.3f}" if result.pp is not None else ""),
                (22, f"{result.ppk:.3f}" if result.ppk is not None else ""),
            ]

        # Batch update statistics columns
        for col_idx, value in stat_data:
            if col_idx < table.columnCount():
                item = table.item(row, col_idx)
                if not item:
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(row, col_idx, item)
                item.setText(str(value))
                # Apply consistent styling
                self._apply_calculated_cell_style(item, col_idx)

        # Update status and highlighting
        self._update_status(table, row, result, evaluation_type)
        self._highlight_violations(table, row, result, evaluation_type)
    
    def _apply_calculated_cell_style(self, item: QTableWidgetItem, col_idx: int):
        """Apply consistent styling to calculated cells"""
        item.setTextAlignment(Qt.AlignCenter)
        
        if col_idx in [21, 22]:  # Pp, Ppk columns
            item.setBackground(QColor(248, 240, 255))  # Light purple
            item.setForeground(self.colors["process_capability"])
            font = QFont("Segoe UI", 9, QFont.Bold)
        else:
            item.setBackground(QColor(248, 249, 250))  # Light gray
            item.setForeground(QColor(52, 58, 64))
            font = QFont("Segoe UI", 9)
        
        item.setFont(font)

    def _update_status(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """OPTIMIZED: Set status cell with minimal object creation"""
        status_col = 23
        if status_col >= table.columnCount():
            return

        status_item = table.item(row, status_col)
        if not status_item:
            status_item = QTableWidgetItem()
            status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, status_col, status_item)

        # Determine final status
        if evaluation_type == "Note":
            final_status = "TO CHECK"
        else:
            final_status = result.status.value if hasattr(result.status, "value") else str(result.status)

        # Apply status styling - use dictionary lookup for efficiency
        status_styles = {
            "T.E.D.": (self.colors["primary"], self.colors["white"], "T.E.D. - Not evaluable (Basic/Informative dimension)"),
            "TED": (self.colors["primary"], self.colors["white"], "T.E.D. - Not evaluable (Basic/Informative dimension)"),
            "BAD": (self.colors["bad"], self.colors["white"], "One or more measurements out of tolerance"),
            "GOOD": (self.colors["good"], self.colors["white"], "All measurements within tolerance"),
            "WARNING": (self.colors["warning"], self.colors["black"], "Measurements may be borderline, check!"),
            "TO CHECK": (QColor(255, 193, 7), self.colors["black"], "Note - Requires review"),
        }

        color, text_color, tooltip = status_styles.get(final_status, (self.colors["warning"], self.colors["black"], f"Status: {final_status}"))

        # Apply styling in one go
        status_item.setText(final_status)
        status_item.setBackground(color)
        status_item.setForeground(text_color)
        status_item.setToolTip(tooltip)
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))

    def _highlight_violations(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """OPTIMIZED: Violation highlighting with reduced operations"""
        if evaluation_type in ["Basic", "Informative", "Note"] or not result.measurements:
            return

        if result.lower_tolerance is None and result.upper_tolerance is None:
            return

        measurement_cols = [12, 13, 14, 15, 16]
        lower_limit = result.nominal + (result.lower_tolerance or 0)
        upper_limit = result.nominal + (result.upper_tolerance or 0)

        # Pre-calculate violation check function
        if result.nominal == 0.0 and result.lower_tolerance == 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
            def violation_check(value):
                return value < 0 or value > result.upper_tolerance
        elif result.nominal == 0.0 and result.lower_tolerance and result.lower_tolerance < 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
            max_tolerance = max(abs(result.lower_tolerance), abs(result.upper_tolerance))
            def violation_check(value):
                return abs(value) > max_tolerance
        else:
            def violation_check(value):
                return not (lower_limit <= value <= upper_limit)

        # Process measurements in batch
        for idx, col in enumerate(measurement_cols[:len(result.measurements)]):
            item = table.item(row, col)
            if not item:
                continue
            
            value = result.measurements[idx]
            formatted_value = f"{value:.3f}"
            item.setText(formatted_value)
            
            is_violation = violation_check(value)
            
            if is_violation:
                item.setForeground(self.colors["bad"])
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item.setToolTip(f"Out of tolerance: {formatted_value}")
            else:
                item.setForeground(self.colors["good"])
                item.setFont(QFont("Segoe UI", 9))
                item.setToolTip(f"Within tolerance: {formatted_value}")


    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """OPTIMIZED: DataFrame extraction with improved performance"""
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            return pd.DataFrame()
        
        all_data = []
        expected_columns = len(self.display_columns)
        
        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget) or "Summary" in self.parent_window.results_tabs.tabText(tab_idx):
                continue
            
            # Pre-allocate row data structure for performance
            for row in range(table.rowCount()):
                row_data = {}
                
                # Process all columns efficiently with single loop
                for col in range(min(table.columnCount(), expected_columns)):
                    col_name = self.display_columns[col] if col < len(self.display_columns) else f"col_{col}"
                    
                    # Handle widgets vs items
                    cell_widget = table.cellWidget(row, col)
                    if isinstance(cell_widget, QComboBox):
                        value = cell_widget.currentText().strip()
                    else:
                        item = table.item(row, col)
                        value = item.text().strip() if item and item.text() else ""
                    
                    # Convert values efficiently
                    if value == "":
                        value = None
                    elif value is not None and col_name in ["nominal", "lower_tolerance", "upper_tolerance"] + self.measurement_columns + ["pp", "ppk"]:
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            value = None
                    
                    row_data[col_name] = value
                
                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number
                
                # Quick validation
                if self._validate_row_fast(row_data):
                    all_data.append(row_data)
        
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()

    def _validate_row_fast(self, row_data: dict) -> bool:
        """Fast row validation with minimal checks"""
        # Basic required fields check
        if not (row_data.get("element_id") and row_data.get("description")):
            return False
        
        evaluation_type = row_data.get("evaluation_type", "Normal")
        
        # Fast return for Notes
        if evaluation_type == "Note":
            return True
        
        # Check nominal for dimensional types
        if evaluation_type in ["Basic", "Informative", "Normal", "GD&T"] and row_data.get("nominal") is None:
            return False
        
        # Quick measurement check for Normal/GD&T
        if evaluation_type in ["Normal", "GD&T"]:
            return any(row_data.get(f"measurement_{i}") is not None for i in range(1, 6))
        
        return True

    def _handle_note_entries(self, results):
        """OPTIMIZED: Note entry handling with reduced object creation"""
        all_results = []
        
        for result in results:
            row = result.to_dict() if hasattr(result, "to_dict") else result
            
            try:
                # Extract measurements efficiently using list comprehension
                measurements = [
                    float(row[f"measurement_{i}"]) 
                    for i in range(1, 6) 
                    if f"measurement_{i}" in row and row[f"measurement_{i}"] is not None
                    if self._safe_float_conversion(row[f"measurement_{i}"]) is not None
                ]

                # Quick statistics calculation
                if measurements:
                    mean_val = sum(measurements) / len(measurements)
                    std_dev_val = (sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)) ** 0.5 if len(measurements) > 1 else 0.0
                else:
                    mean_val = std_dev_val = 0.0

                # Get basic values with defaults
                evaluation_type = row.get("evaluation_type", "Normal")
                force_status = row.get("force_status", "AUTO")
                nominal_val = float(row.get("nominal", 0))
                classe = row.get("class", "")

                # Process capability calculation - optimized
                pp = ppk = None
                if (classe and classe.upper() in ["CC", "SC", "IC"] and 
                    evaluation_type not in ["Note", "Basic", "Informative"] and 
                    len(measurements) > 1 and std_dev_val > 0):
                    
                    try:
                        lower_tol = float(row.get("lower_tolerance", 0))
                        upper_tol = float(row.get("upper_tolerance", 0))
                        
                        if lower_tol != 0 and upper_tol != 0:
                            tolerance_range = abs(upper_tol - lower_tol)
                            pp = tolerance_range / (6 * std_dev_val)
                            
                            lsl = nominal_val + lower_tol
                            usl = nominal_val + upper_tol
                            ppu = (usl - mean_val) / (3 * std_dev_val)
                            ppl = (mean_val - lsl) / (3 * std_dev_val)
                            ppk = min(ppu, ppl)
                            
                            pp = round(pp, 3)
                            ppk = round(ppk, 3)
                    except (ValueError, ZeroDivisionError, TypeError):
                        pp = ppk = None

                # Determine status efficiently
                status_map = {
                    "Basic": DimensionalStatus.TED,
                    "Informative": DimensionalStatus.TED,
                }
                
                if evaluation_type in status_map:
                    status = status_map[evaluation_type]
                elif evaluation_type == "Note":
                    status_map_note = {
                        "GOOD": DimensionalStatus.GOOD,
                        "BAD": DimensionalStatus.BAD,
                    }
                    status = status_map_note.get(force_status, DimensionalStatus.TO_CHECK)
                else:
                    status_map_force = {
                        "GOOD": DimensionalStatus.GOOD,
                        "BAD": DimensionalStatus.BAD,
                    }
                    status = status_map_force.get(force_status, DimensionalStatus.GOOD)

                # Create result object
                note_result = DimensionalResult(
                    element_id=row.get("element_id", ""),
                    batch=row.get("batch", ""),
                    cavity=row.get("cavity", ""),
                    classe=classe,
                    description=row.get("description", ""),
                    nominal=nominal_val,
                    lower_tolerance=row.get("lower_tolerance"),
                    upper_tolerance=row.get("upper_tolerance"),
                    measurements=measurements,
                    deviation=[m - nominal_val for m in measurements],
                    mean=mean_val,
                    std_dev=std_dev_val,
                    out_of_spec_count=0,
                    status=status,
                    gdt_flags={},
                    datum_element_id=row.get("datum"),
                    feature_type=evaluation_type.lower() if evaluation_type in ["Basic", "Informative", "Note"] else "dimension",
                    warnings=[],
                    evaluation_type=evaluation_type,
                    measuring_instrument=row.get("measuring_instrument", ""),
                    pp=pp,
                    ppk=ppk
                )
                
                all_results.append(note_result)
                
            except Exception as e:
                self._log_message(f"Error creating result: {str(e)}", "ERROR")
                continue
        
        return all_results
    
    def _safe_float_conversion(self, value):
        """Safe float conversion with minimal overhead"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_processed_dataframe(self) -> pd.DataFrame:
        """Get dataframe ready for processing with evaluation type filtering"""
        df = self._get_dataframe_from_tables()
        
        if df.empty:
            return df

        processing_df = df[df["evaluation_type"].isin(["Normal", "GD&T"])].copy()
        
        return processing_df