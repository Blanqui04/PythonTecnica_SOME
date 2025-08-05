# src/gui/windows/components/dimensional_table_manager.py - OPTIMIZED VERSION
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
        """Update single table with batch operations"""
        updated_count = 0
        
        # Disable updates during batch operation
        table.setUpdatesEnabled(False)
        
        try:
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
                    self._update_row(table, row, result)
                    updated_count += 1
        
        finally:
            # Re-enable updates and refresh
            table.setUpdatesEnabled(True)
            table.viewport().update()
        
        return updated_count

    def _update_row(self, table: QTableWidget, row: int, result: DimensionalResult):
        """Optimized single row update: use DimensionalResult values directly, especially status"""
        eval_combo = table.cellWidget(row, 8)
        evaluation_type = eval_combo.currentText() if isinstance(eval_combo, QComboBox) else "Normal"

        # For Note: always empty statistics/measurements, status TO CHECK
        if evaluation_type == "Note":
            stat_data = [
                (17, ""),   # minimum
                (18, ""),   # maximum  
                (19, ""),   # mean
                (20, ""),   # std_deviation
                (21, ""),   # Pp
                (22, ""),   # Ppk
            ]
        else:
            stat_data = [
                (17, f"{result.mean:.3f}" if result.mean is not None else ""),
                (18, f"{result.std_dev:.3f}" if result.std_dev is not None else ""),
                (19, f"{min(result.measurements):.3f}" if result.measurements else ""),
                (20, f"{max(result.measurements):.3f}" if result.measurements else ""),
                (21, f"{result.pp:.3f}" if result.pp is not None else ""),
                (22, f"{result.ppk:.3f}" if result.ppk is not None else ""),
            ]

        # Write statistics to table
        for col_idx, value in stat_data:
            if col_idx < table.columnCount():
                item = table.item(row, col_idx)
                if not item:
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(row, col_idx, item)
                item.setText(str(value))
                item.setBackground(QColor(248, 249, 250))
                item.setForeground(QColor(52, 58, 64))

        self._update_status(table, row, result, evaluation_type)
        self._highlight_violations(table, row, result, evaluation_type)

    def _update_status(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """Set status cell using DimensionalResult.status directly"""
        status_col = 23  # Assume status column is 23, adjust as needed
        if status_col >= table.columnCount():
            return

        status_item = table.item(row, status_col)
        if not status_item:
            status_item = QTableWidgetItem()
            status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, status_col, status_item)

        # Always use status from DimensionalResult
        if evaluation_type == "Note":
            final_status = "TO CHECK"
        else:
            final_status = result.status.value if hasattr(result.status, "value") else str(result.status)

        print(f"[TABLE] Row {row} | element_id={result.element_id} | eval_type={evaluation_type} | status={final_status}")
        import logging
        logging.getLogger("dimensional.table").warning(f"[TABLE] Row {row} | element_id={result.element_id} | eval_type={evaluation_type} | status={final_status}")

        # Color logic (unchanged)
        if final_status in ["T.E.D.", "TED"]:
            tooltip = "T.E.D. - Not evaluable (Basic/Informative dimension)"
            color = self.colors["primary"]
            text_color = self.colors["white"]
        elif final_status == "BAD":
            tooltip = "One or more measurements out of tolerance"
            color = self.colors["bad"]
            text_color = self.colors["white"]
        elif final_status == "GOOD":
            tooltip = "All measurements within tolerance"
            color = self.colors["good"]
            text_color = self.colors["white"]
        elif final_status == "WARNING":
            tooltip = "Measurements may be borderline, check!"
            color = self.colors["warning"]
            text_color = self.colors["black"]
        elif final_status == "TO CHECK":
            tooltip = "Note - Requires review"
            color = QColor(255, 193, 7)
            text_color = self.colors["black"]
        else:
            tooltip = f"Status: {final_status}"
            color = self.colors["warning"]
            text_color = self.colors["black"]

        status_item.setText(final_status)
        status_item.setBackground(color)
        status_item.setForeground(text_color)
        status_item.setToolTip(tooltip)
        status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))

    def _highlight_violations(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """Optimized violation highlighting: skip for notes, use result.measurements directly"""
        if evaluation_type in ["Basic", "Informative", "Note"]:
            return

        if not result.measurements or (result.lower_tolerance is None and result.upper_tolerance is None):
            return

        measurement_cols = [12, 13, 14, 15, 16]
        lower_limit = result.nominal + (result.lower_tolerance or 0)
        upper_limit = result.nominal + (result.upper_tolerance or 0)

        for idx, col in enumerate(measurement_cols):
            if idx >= len(result.measurements):
                break
            item = table.item(row, col)
            if not item:
                continue
            try:
                value = result.measurements[idx]
                formatted_value = f"{value:.3f}"
                item.setText(formatted_value)
                if result.nominal == 0.0 and result.lower_tolerance == 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
                    is_violation = value < 0 or value > result.upper_tolerance
                elif result.nominal == 0.0 and result.lower_tolerance and result.lower_tolerance < 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
                    is_violation = abs(value) > max(abs(result.lower_tolerance), abs(result.upper_tolerance))
                else:
                    is_violation = not (lower_limit <= value <= upper_limit)
                if is_violation:
                    item.setForeground(self.colors["bad"])
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    item.setToolTip(f"Out of tolerance: {formatted_value}")
                else:
                    item.setForeground(self.colors["good"])
                    item.setFont(QFont("Segoe UI", 9))
                    item.setToolTip(f"Within tolerance: {formatted_value}")
            except (ValueError, IndexError):
                continue

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Optimized DataFrame extraction"""
        if not self.parent_window or not hasattr(self.parent_window, "results_tabs"):
            return pd.DataFrame()
        
        all_data = []
        
        for tab_idx in range(self.parent_window.results_tabs.count()):
            table = self.parent_window.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue
            
            # Extract data from table efficiently
            for row in range(table.rowCount()):
                row_data = {}
                
                for col, col_name in enumerate(self.display_columns):
                    if col >= len(self.display_columns):
                        break
                    
                    # Handle dropdown widgets
                    cell_widget = table.cellWidget(row, col)
                    if isinstance(cell_widget, QComboBox):
                        value = cell_widget.currentText().strip()
                    else:
                        # Handle regular items
                        item = table.item(row, col)
                        value = item.text().strip() if item and item.text() else None
                    
                    # Convert empty strings to None
                    if value == "":
                        value = None
                    
                    # Handle numeric columns
                    if value is not None and col_name in ["nominal", "lower_tolerance", "upper_tolerance"] + self.measurement_columns:
                        try:
                            row_data[col_name] = float(value)
                        except (ValueError, TypeError):
                            row_data[col_name] = None
                    else:
                        row_data[col_name] = value
                
                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number
                
                # Validate and add row
                if self._validate_row(row_data):
                    all_data.append(row_data)
        
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()

    def _validate_row(self, row_data: dict) -> bool:
        """Fast row validation"""
        # Basic required fields
        if not row_data.get("element_id") or not row_data.get("description"):
            return False
        
        evaluation_type = row_data.get("evaluation_type", "Normal")
        
        # For Notes, basic validation is enough
        if evaluation_type == "Note":
            return True
        
        # For Basic/Informative, check nominal
        if evaluation_type in ["Basic", "Informative"]:
            return row_data.get("nominal") is not None
        
        # For Normal/GD&T, check nominal and measurements
        if row_data.get("nominal") is None:
            return False
        
        # Check for at least one measurement
        has_measurements = any(row_data.get(f"measurement_{i}") is not None for i in range(1, 6))
        
        return has_measurements

    def _handle_note_entries(self, results):
        """Optimized note entry handling with TO CHECK status"""
        all_results = []
        
        for result in results:
            if hasattr(result, "to_dict"):
                row = result.to_dict()
            else:
                row = result
            
            try:
                # Extract measurements efficiently
                measurements = []
                for i in range(1, 6):
                    meas_key = f"measurement_{i}"
                    if meas_key in row and row[meas_key] is not None:
                        try:
                            measurements.append(float(row[meas_key]))
                        except (ValueError, TypeError):
                            continue
                
                # Calculate statistics
                if measurements:
                    mean_val = sum(measurements) / len(measurements)
                    std_dev_val = (sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)) ** 0.5 if len(measurements) > 1 else 0.0
                else:
                    mean_val = std_dev_val = 0.0
                
                # Get evaluation type and handle status
                evaluation_type = row.get("evaluation_type", "Normal")
                force_status = row.get("force_status", "AUTO")
                nominal_val = float(row.get("nominal", 0))
                classe = row.get("class", "")
                
                # Calculate process capability for classified dimensions
                pp = ppk = None
                if (classe and classe.upper() in ["CC", "SC", "IC"] and 
                    evaluation_type not in ["Note", "Basic", "Informative"] and 
                    len(measurements) > 1 and std_dev_val > 0):
                    
                    lower_tol = row.get("lower_tolerance")
                    upper_tol = row.get("upper_tolerance")
                    
                    if lower_tol is not None and upper_tol is not None:
                        try:
                            lower_tol = float(lower_tol)
                            upper_tol = float(upper_tol)
                            
                            # Calculate Pp and Ppk
                            tolerance_range = abs(upper_tol - lower_tol)
                            pp = tolerance_range / (6 * std_dev_val)
                            
                            lsl = nominal_val + lower_tol
                            usl = nominal_val + upper_tol
                            ppu = (usl - mean_val) / (3 * std_dev_val)
                            ppl = (mean_val - lsl) / (3 * std_dev_val)
                            ppk = min(ppu, ppl)
                            
                            pp = round(pp, 3)
                            ppk = round(ppk, 3)
                        except (ValueError, ZeroDivisionError):
                            pp = ppk = None
                
                # Determine status based on evaluation type
                if evaluation_type in ["Basic", "Informative"]:
                    status = DimensionalStatus.TED  # Will show as T.E.D. in UI
                elif evaluation_type == "Note":
                    if force_status == "GOOD":
                        status = DimensionalStatus.GOOD
                    elif force_status == "BAD":
                        status = DimensionalStatus.BAD
                    else:
                        status = DimensionalStatus.TO_CHECK  # Default for notes
                elif force_status == "GOOD":
                    status = DimensionalStatus.GOOD
                elif force_status == "BAD":
                    status = DimensionalStatus.BAD
                else:
                    # Auto-determine for Normal/GD&T
                    status = DimensionalStatus.GOOD  # Default, will be recalculated if needed
                
                # Create result
                note_result = DimensionalResult(
                    element_id=row.get("element_id", ""),
                    batch=row.get("batch", ""),
                    cavity=row.get("cavity", ""),
                    classe=row.get("class", ""),
                    description=row.get("description", ""),
                    nominal=nominal_val,
                    lower_tolerance=row.get("lower_tolerance"),
                    upper_tolerance=row.get("upper_tolerance"),
                    measurements=measurements,
                    deviation=[m - nominal_val for m in measurements],
                    mean=mean_val,
                    std_dev=std_dev_val,
                    out_of_spec_count=0,  # Will be calculated if needed
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

    def _get_processed_dataframe(self) -> pd.DataFrame:
        """Get dataframe ready for processing with evaluation type filtering"""
        df = self._get_dataframe_from_tables()
        
        if df.empty:
            return df
        
        # Filter based on evaluation type
        # Process Normal and GD&T through analyzer
        # Handle Basic, Informative, and Note separately
        processing_df = df[df["evaluation_type"].isin(["Normal", "GD&T"])].copy()
        
        return processing_df