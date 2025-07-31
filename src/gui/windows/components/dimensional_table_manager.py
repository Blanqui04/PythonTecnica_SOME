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
                    self._update_row_optimized(table, row, result)
                    updated_count += 1
        
        finally:
            # Re-enable updates and refresh
            table.setUpdatesEnabled(True)
            table.viewport().update()
        
        return updated_count

    def _update_row_optimized(self, table: QTableWidget, row: int, result: DimensionalResult):
        """Optimized single row update with evaluation type support"""
        # Get evaluation type
        eval_combo = table.cellWidget(row, 8)
        evaluation_type = eval_combo.currentText() if isinstance(eval_combo, QComboBox) else "Normal"
        
        # Format values once
        def format_val(val):
            if val is None or val == "":
                return ""
            try:
                return f"{float(val):.3f}"
            except (ValueError, TypeError):
                return str(val)
        
        # Determine what statistics to show based on evaluation type
        if evaluation_type == "Note":
            if result.measurements:
                # Note with measurements - show statistics
                min_val = format_val(min(result.measurements))
                max_val = format_val(max(result.measurements))
                mean_val = format_val(result.mean)
                std_val = format_val(result.std_dev)
            else:
                # Note without measurements - empty statistics
                min_val = max_val = mean_val = std_val = ""
        else:
            # All other types show statistics if measurements exist
            min_val = format_val(min(result.measurements)) if result.measurements else ""
            max_val = format_val(max(result.measurements)) if result.measurements else ""
            mean_val = format_val(result.mean) if result.mean is not None else ""
            std_val = format_val(result.std_dev) if result.std_dev is not None else ""
        
        # Update statistics columns in batch
        stat_data = [
            (17, min_val),   # minimum
            (18, max_val),   # maximum  
            (19, mean_val),  # mean
            (20, std_val),   # std_deviation
        ]
        
        for col_idx, value in stat_data:
            item = table.item(row, col_idx)
            if not item:
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
            
            item.setText(str(value))
            # Apply consistent styling for statistics
            item.setBackground(QColor(248, 249, 250))
            item.setForeground(QColor(52, 58, 64))
        
        # Handle status based on evaluation type
        self._update_status_optimized(table, row, result, evaluation_type)
        
        # Highlight violations efficiently
        self._highlight_violations_optimized(table, row, result, evaluation_type)

    def _update_status_optimized(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """Optimized status update with evaluation type support"""
        status_item = table.item(row, 21)
        if not status_item:
            status_item = QTableWidgetItem()
            status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 21, status_item)
        
        # Determine final status based on evaluation type
        if evaluation_type in ["Basic", "Informative"]:
            final_status = "T.E.D."  # Theoretical Exact Dimension
            tooltip = "T.E.D. - Not evaluable (Basic/Informative dimension)"
            color = self.colors["primary"]
            text_color = self.colors["white"]
            
        elif evaluation_type == "Note":
            # Notes use force status or default to GOOD
            force_combo = table.cellWidget(row, 22)
            force_status = force_combo.currentText() if isinstance(force_combo, QComboBox) else "AUTO"
            
            if force_status == "BAD":
                final_status = "BAD"
                tooltip = "Note - Forced BAD"
                color = self.colors["bad"]
                text_color = self.colors["white"]
            else:
                final_status = "GOOD"
                tooltip = "Note - Default GOOD"
                color = self.colors["good"]
                text_color = self.colors["white"]
                
        else:
            # Normal and GD&T evaluations
            force_combo = table.cellWidget(row, 22)
            force_status = force_combo.currentText() if isinstance(force_combo, QComboBox) else "AUTO"
            
            if force_status == "GOOD":
                final_status = "GOOD"
                tooltip = "Forced GOOD"
                color = self.colors["good"]
                text_color = self.colors["white"]
            elif force_status == "BAD":
                final_status = "BAD"
                tooltip = "Forced BAD"
                color = self.colors["bad"]
                text_color = self.colors["white"]
            else:
                # Use calculated status
                final_status = result.status.value
                if final_status == "GOOD":
                    tooltip = "All measurements within tolerance"
                    color = self.colors["good"]
                    text_color = self.colors["white"]
                elif final_status == "BAD":
                    tooltip = "One or more measurements out of tolerance"
                    color = self.colors["bad"]
                    text_color = self.colors["white"]
                else:
                    tooltip = f"Status: {final_status}"
                    color = self.colors["warning"]
                    text_color = self.colors["black"]
        
        # Apply status styling efficiently
        status_item.setText(final_status)
        status_item.setBackground(color)
        status_item.setForeground(text_color)
        status_item.setToolTip(tooltip)
        status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))

    def _highlight_violations_optimized(self, table: QTableWidget, row: int, result: DimensionalResult, evaluation_type: str):
        """Optimized violation highlighting"""
        # Skip for Basic/Informative (no tolerance evaluation)
        if evaluation_type in ["Basic", "Informative"]:
            return
        
        if not result.measurements or (result.lower_tolerance is None and result.upper_tolerance is None):
            return
        
        measurement_cols = [12, 13, 14, 15, 16]
        
        # Calculate limits once
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
                
                # Check if violation
                if evaluation_type == "Normal" or evaluation_type == "GD&T":
                    if result.nominal == 0.0 and result.lower_tolerance == 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
                        # Unilateral tolerance for nominal=0
                        is_violation = value < 0 or value > result.upper_tolerance
                    elif result.nominal == 0.0 and result.lower_tolerance and result.lower_tolerance < 0.0 and result.upper_tolerance and result.upper_tolerance > 0.0:
                        # Bilateral tolerance for nominal=0
                        is_violation = abs(value) > max(abs(result.lower_tolerance), abs(result.upper_tolerance))
                    else:
                        # Standard tolerance check
                        is_violation = not (lower_limit <= value <= upper_limit)
                else:
                    is_violation = False
                
                # Apply color coding
                if is_violation:
                    item.setForeground(self.colors["bad"])  # Red for violations
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    item.setToolTip(f"Out of tolerance: {formatted_value}")
                else:
                    item.setForeground(self.colors["good"])  # Green for good
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
                if self._validate_row_optimized(row_data):
                    all_data.append(row_data)
        
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()

    def _validate_row_optimized(self, row_data: dict) -> bool:
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
        """Optimized note entry handling"""
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
                
                # Determine status based on evaluation type
                if evaluation_type in ["Basic", "Informative"]:
                    status = DimensionalStatus.GOOD  # Will show as T.E.D. in UI
                elif evaluation_type == "Note":
                    status = DimensionalStatus.GOOD if force_status != "BAD" else DimensionalStatus.BAD
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
                    measuring_instrument=row.get("measuring_instrument", "")
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