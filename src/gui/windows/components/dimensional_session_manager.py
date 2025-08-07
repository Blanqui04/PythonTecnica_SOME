# src/gui/windows/components/dimensional_session_manager.py - SAVE FUNCTIONS DON'T WORK WELL (newer version)
from PyQt5.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from src.services.dimensional_export_service import DataExportService
#from src.database.database_connection import PostgresConn


class SessionManager:
    """Handles session saving/loading operations"""

    def __init__(
        self,
        client_name: str,
        project_ref: str,
        batch_number: str,
        log_callback: Optional[callable] = None,
        parent: Optional[QWidget] = None,
    ):
        self.client_name = client_name
        self.project_ref = project_ref
        self.batch_number = batch_number
        self._log = log_callback or (
            lambda msg, level="INFO": print(f"[{level}] {msg}")
        )
        self._parent = parent
        self.unsaved_changes = False
        self.session_file = None

    def _log_message(self, message: str, level: str = "INFO"):
        """Add message to log area and logger"""
        self._log(message, level)

    def save_session(self):
        """PUBLIC: Save session with file dialog - THIS IS THE METHOD THE BUTTON SHOULD CALL"""
        try:
            if self.session_file:
                # Save to existing file
                self._save_session_to_file(self.session_file)
                self._clear_unsaved_changes()
                self._log(f"💾 Session saved to: {self.session_file}", "INFO")
            else:
                # Show save dialog for new file
                sessions_dir = "sessions"
                os.makedirs(sessions_dir, exist_ok=True)
                
                default_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}.json"
                default_path = os.path.join(sessions_dir, default_filename)
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self._parent,
                    "Save Session",
                    default_path,
                    "JSON Files (*.json)"
                )
                
                if file_path:
                    self._save_session_to_file(file_path)
                    self.session_file = file_path
                    self._clear_unsaved_changes()
                    self._log(f"💾 Session saved to: {file_path}", "INFO")
                    
        except Exception as e:
            self._handle_session_error("Save session", e)

    def _save_session_optimized(self, file_path: str, auto_save: bool = False):
        """FIXED: Optimized save method with proper dropdown handling"""
        # Validate file path first
        if not file_path or not isinstance(file_path, str) or len(file_path.strip()) == 0:
            raise ValueError(f"Invalid file path provided: {repr(file_path)}")
            
        try:
            # Ensure the file path is absolute and directory exists
            file_path = os.path.abspath(file_path.strip())
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)
            
            session_data = {
                "metadata": {
                    "client_name": self.client_name,
                    "project_ref": self.project_ref,
                    "batch_number": self.batch_number,
                    "report_type": getattr(self._parent.report_type_combo, 'currentText', lambda: 'Unknown')(),
                    "tolerance_standard": getattr(self._parent.tolerance_combo, 'currentText', lambda: 'ISO 2768-m')(),
                    "manual_mode": getattr(self._parent, 'manual_mode', False),
                    "save_timestamp": datetime.now().isoformat(),
                    "version": "3.0",
                    "auto_save": auto_save,
                },
                "table_data": [],
            }

            # FIXED: Save table data efficiently with proper dropdown handling
            if hasattr(self._parent, 'results_tabs'):
                for tab_idx in range(self._parent.results_tabs.count()):
                    widget = self._parent.results_tabs.widget(tab_idx)
                    tab_name = self._parent.results_tabs.tabText(tab_idx)

                    if "Summary" in tab_name:
                        continue

                    if isinstance(widget, QTableWidget):
                        tab_data = {
                            "tab_name": tab_name,
                            "row_count": widget.rowCount(),
                            "column_count": widget.columnCount(),
                            "rows": []
                        }

                        # FIXED: Save only non-empty rows with proper dropdown handling
                        for row in range(widget.rowCount()):
                            row_has_data = False
                            row_data = {"cells": {}, "dropdowns": {}}
                            
                            for col in range(widget.columnCount()):
                                try:
                                    cell_widget = widget.cellWidget(row, col)
                                    if isinstance(cell_widget, QComboBox):
                                        # FIXED: Properly save ALL dropdown values including column 24
                                        current_text = cell_widget.currentText()
                                        if current_text and current_text.strip():
                                            row_data["dropdowns"][col] = current_text
                                            row_has_data = True
                                            if not auto_save:  # Only log for manual saves
                                                self._log(f"💾 Optimized save dropdown col {col}: '{current_text}'", "DEBUG")
                                    else:
                                        item = widget.item(row, col)
                                        if item and item.text().strip():
                                            row_data["cells"][col] = item.text()
                                            row_has_data = True
                                except Exception as e:
                                    if not auto_save:
                                        self._log(f"⚠️ Skipping cell ({row},{col}): {str(e)}", "DEBUG")
                                    continue
                            
                            if row_has_data:
                                tab_data["rows"].append(row_data)

                        if tab_data["rows"]:
                            session_data["table_data"].append(tab_data)

            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=1 if auto_save else 2, ensure_ascii=False, default=str)
                
            if not auto_save:
                self._log(f"💾 Session saved: {os.path.basename(file_path)}", "INFO")

        except Exception as e:
            raise Exception(f"Optimized save failed: {str(e)}")

    def _save_summary_metrics(self):
        """Save summary metrics efficiently"""
        try:
            if not hasattr(self._parent, "summary_widget") or not self._parent.summary_widget:
                return
                
            summary_widget = self._parent.summary_widget
            session_data = {
                "metrics": getattr(summary_widget, 'metrics', {}),
                "study_history": getattr(summary_widget, 'study_history', [])[-5:],  # Only last 5 for performance
                "edit_history": getattr(summary_widget, 'edit_history', [])[-10:],  # Only last 10 for performance
                "session_start_time": getattr(summary_widget, 'session_start_time', datetime.now()).isoformat(),
            }

            # Save to file
            sessions_dir = "sessions"
            os.makedirs(sessions_dir, exist_ok=True)
            session_file = os.path.join(sessions_dir, f"{self.client_name}_{self.project_ref}_{self.batch_number}_summary.json")

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, default=str)

            self._log_message("💾 Summary metrics saved efficiently", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error saving summary metrics: {str(e)}", "ERROR")

    def _save_session_to_file(self, file_path: str):
        """Save session data to file with FIXED dropdown handling"""
        try:
            # Validate and ensure directory exists
            if not file_path or not isinstance(file_path, str):
                raise ValueError("Invalid file path provided")
                
            file_path = os.path.abspath(file_path)
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)
            
            session_data = {
                "metadata": {
                    "client_name": self.client_name,
                    "project_ref": self.project_ref,
                    "batch_number": self.batch_number,
                    "report_type": getattr(self._parent.report_type_combo, 'currentText', lambda: 'Unknown')(),
                    "manual_mode": getattr(self._parent, 'manual_mode', False),
                    "save_timestamp": datetime.now().isoformat(),
                    "version": "2.0",
                },
                "table_data": [],
                "summary_data": {},
                "results_data": [],
            }

            # Save data from all tables with FIXED dropdown handling
            if hasattr(self._parent, 'results_tabs'):
                for tab_idx in range(self._parent.results_tabs.count()):
                    try:
                        widget = self._parent.results_tabs.widget(tab_idx)
                        tab_name = self._parent.results_tabs.tabText(tab_idx)

                        # Skip summary tab - we save its data separately
                        if "Summary" in tab_name:
                            continue

                        if isinstance(widget, QTableWidget):
                            tab_data = {
                                "tab_name": tab_name,
                                "rows": [],
                            }

                            for row in range(widget.rowCount()):
                                row_data = []
                                dropdown_data = {}

                                for col in range(widget.columnCount()):
                                    try:
                                        cell_widget = widget.cellWidget(row, col)
                                        if isinstance(cell_widget, QComboBox):
                                            # FIXED: Save dropdown value properly
                                            current_text = cell_widget.currentText()
                                            dropdown_data[col] = current_text
                                            row_data.append("")  # Empty string for cell data
                                            self._log(f"💾 Saving dropdown col {col}: '{current_text}'", "DEBUG")
                                        else:
                                            item = widget.item(row, col)
                                            cell_text = item.text() if item else ""
                                            row_data.append(cell_text)
                                    except Exception as e:
                                        self._log(f"⚠️ Error saving cell ({row},{col}): {str(e)}", "DEBUG")
                                        row_data.append("")

                                tab_data["rows"].append(
                                    {"cells": row_data, "dropdowns": dropdown_data}
                                )

                            session_data["table_data"].append(tab_data)
                    except Exception as e:
                        self._log(f"⚠️ Error saving tab {tab_idx}: {str(e)}", "WARNING")
                        continue

            # Save summary data
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                try:
                    session_data["summary_data"] = self._parent.summary_widget.get_summary_data()
                    self._log("📊 Summary data included in session", "DEBUG")
                except Exception as e:
                    self._log(f"⚠️ Could not save summary data: {str(e)}", "WARNING")

            # Save analysis results if available
            if hasattr(self._parent, "results") and self._parent.results:
                try:
                    session_data["results_data"] = [
                        r.to_dict() if hasattr(r, 'to_dict') else str(r) for r in self._parent.results
                    ]
                    self._log(f"📈 {len(self._parent.results)} analysis results included", "DEBUG")
                except Exception as e:
                    self._log(f"⚠️ Could not save analysis results: {str(e)}", "WARNING")

            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)

            self._log(f"💾 Session saved to {file_path}")

        except Exception as e:
            error_msg = f"Failed to save session: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Save Error", error_msg)

    def _load_session(self):
        """Load session from file - ENHANCED with complete restoration"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self._parent, "Load Session", "sessions/", "JSON Files (*.json)"
            )

            if file_path:
                self._load_session_from_file(file_path)
                self.session_file = file_path

        except Exception as e:
            self._log(f"❌ Error loading session: {str(e)}", "ERROR")

    def _update_summary_from_tables(self):
        """Update summary widget with current table data"""
        if not hasattr(self._parent, "summary_widget") or not self._parent.summary_widget:
            return

        try:
            if hasattr(self._parent, 'table_manager'):
                df = self._parent.table_manager._get_dataframe_from_tables()
                if not df.empty:
                    self._parent.summary_widget.update_summary(table_data=df)
        except Exception as e:
            self._log_message(f"❌ Error updating summary: {str(e)}", "ERROR")

    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        if hasattr(self._parent, "setWindowTitle"):
            title = self._parent.windowTitle()
            if not title.endswith(" *"):
                self._parent.setWindowTitle(title + " *")

    def _get_safe_file_path(self, suggested_path: str = None) -> str:
        """Get a safe file path for saving, with fallback options"""
        if suggested_path and isinstance(suggested_path, str) and len(suggested_path.strip()) > 0:
            # Ensure directory exists
            suggested_path = os.path.abspath(suggested_path.strip())
            directory = os.path.dirname(suggested_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            return suggested_path
        
        # Fallback to default location
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "DimensionalStudio", "sessions")
        os.makedirs(default_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(default_dir, f"session_{self.client_name}_{self.project_ref}_{timestamp}.json")

    def _load_last_session(self):
        """OPTIMIZED: Load the most recent auto-saved session with better performance"""
        auto_save_dir = os.path.join(
            os.path.expanduser("~"), ".dimensional_studio", "autosave"
        )
        if not os.path.exists(auto_save_dir):
            return

        try:
            pattern = f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_"
            auto_save_files = []
            
            # Get all matching files with their timestamps
            for f in os.listdir(auto_save_dir):
                if f.startswith(pattern) and f.endswith(".json"):
                    file_path = os.path.join(auto_save_dir, f)
                    try:
                        # Validate the file before adding to list
                        if self._validate_session_file(file_path):
                            mtime = os.path.getctime(file_path)
                            auto_save_files.append((file_path, mtime, f))
                    except OSError:
                        continue

            if not auto_save_files:
                return

            # Get most recent file
            latest_file_info = max(auto_save_files, key=lambda x: x[1])
            latest_path, latest_time, latest_name = latest_file_info

            # Check if file is recent (within last 24 hours)
            file_age = datetime.now() - datetime.fromtimestamp(latest_time)
            if file_age.total_seconds() > 24 * 3600:  # 24 hours
                self._log("📅 Auto-save file too old, skipping restore", "DEBUG")
                return

            # Check file size to ensure it's not corrupted
            file_size = os.path.getsize(latest_path)
            if file_size < 100:  # Less than 100 bytes is likely corrupted
                self._log("⚠️ Auto-save file appears corrupted, skipping restore", "WARNING")
                return

            # Ask user if they want to restore
            reply = QMessageBox.question(
                self._parent,
                "Restore Auto-saved Session",
                f"Found auto-saved session from {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}.\n"
                f"File: {latest_name}\n"
                f"Size: {file_size:,} bytes\n\n"
                f"Would you like to restore it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self._load_session_from_file(latest_path)
                self._log("♻️ Auto-saved session restored successfully", "INFO")

        except Exception as e:
            self._log(f"⚠️ Failed to load last session: {str(e)}", "WARNING")

    def closeEvent(self, event):
        """Handle window close event - ENHANCED with summary saving"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self._parent,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.save_session()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return

        # Clean up summary widget timer
        if hasattr(self._parent, "summary_widget") and hasattr(
            self._parent.summary_widget, "refresh_timer"
        ):
            self._parent.summary_widget.refresh_timer.stop()

        # Clean up processing thread if running
        if hasattr(self._parent, 'processing_thread') and self._parent.processing_thread and self._parent.processing_thread.isRunning():
            self._parent.processing_thread.terminate()
            self._parent.processing_thread.wait()

        event.accept()

    def _update_status_from_summary(self):
        """Update status bar with summary information"""
        if not hasattr(self._parent, "summary_widget") or not self._parent.summary_widget:
            return

        try:
            summary_widget = self._parent.summary_widget
            total_dims = getattr(summary_widget, 'metrics', {}).get("total_dimensions", 0)
            studies_run = getattr(summary_widget, 'metrics', {}).get("total_studies_run", 0)
            edits_made = getattr(summary_widget, 'metrics', {}).get("dimensions_edited", 0)

            # Calculate success rate from latest study
            success_rate = 0
            study_history = getattr(summary_widget, 'study_history', [])
            if study_history:
                latest = study_history[-1]
                if latest.get("total_dimensions", 0) > 0:
                    success_rate = (latest.get("good", 0) / latest["total_dimensions"]) * 100

            status_text = f"📊 {total_dims} dims | {studies_run} studies | {success_rate:.1f}% success"
            if edits_made > 0:
                status_text += f" | {edits_made} edits"

            if hasattr(self._parent, 'stats_label'):
                self._parent.stats_label.setText(status_text)

        except Exception as e:
            self._log_message(
                f"❌ Error updating status from summary: {str(e)}", "ERROR"
            )

    def _store_original_values(self, table_data: pd.DataFrame):
        """Store original values for comparison tracking"""
        if not hasattr(self._parent, "summary_widget") or not self._parent.summary_widget:
            return

        try:
            summary_widget = self._parent.summary_widget
            for _, row in table_data.iterrows():
                element_id = row.get("element_id")
                if element_id and hasattr(summary_widget, 'original_data') and element_id not in summary_widget.original_data:
                    # Store original measurements and key values
                    original_values = {
                        "measurements": {
                            f"measurement_{i}": row.get(f"measurement_{i}")
                            for i in range(1, 6)
                        },
                        "nominal": row.get("nominal"),
                        "lower_tolerance": row.get("lower_tolerance"),
                        "upper_tolerance": row.get("upper_tolerance"),
                        "description": row.get("description"),
                        "stored_at": datetime.now().isoformat(),
                    }
                    summary_widget.original_data[element_id] = original_values
        except Exception as e:
            self._log(f"⚠️ Error storing original values: {str(e)}", "WARNING")

    def _load_file(self):
        """Load measurement data from file - ENHANCED for database integration"""
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Select Measurement File",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;Database Files (*.db *.sqlite);;All Files (*)",
        )

        if not file_path:
            return

        try:
            self._log(f"📁 Loading file: {file_path}")

            # Determine file type and load accordingly
            file_ext = file_path.lower()

            if file_ext.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_ext.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path, engine="openpyxl")
            elif file_ext.endswith((".db", ".sqlite")):
                # NEW: Database support
                df = self._load_from_database(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Clear existing data but preserve summary
            self._clear_data_tabs_only()

            # Ensure summary widget exists
            self._ensure_summary_widget()

            # Populate tables with loaded data
            if hasattr(self._parent, '_populate_table_from_dataframe'):
                self._parent._populate_table_from_dataframe(df)

            # Store original data and update summary
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                try:
                    self._parent.summary_widget.update_summary(
                        table_data=df,
                        store_original=True,  # Mark as original data
                        force_refresh=True,
                    )
                    if hasattr(self._parent.summary_widget, 'record_edit'):
                        self._parent.summary_widget.record_edit(
                            f"Loaded data file: {os.path.basename(file_path)} ({len(df)} records)"
                        )
                except Exception as e:
                    self._log(f"⚠️ Could not update summary: {str(e)}", "WARNING")

            self._log(f"✅ Successfully loaded {len(df)} rows from file")
            if hasattr(self._parent, 'run_study_button'):
                self._parent.run_study_button.setEnabled(True)

        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "File Load Error", error_msg)

    def _populate_table_from_dataframe(self, df: pd.DataFrame):
        """Populate table from DataFrame with CONSISTENT FORMATTING (for database loading)"""
        try:
            if df.empty:
                self._log("No data to populate", "WARNING")
                return

            # Clear existing tabs except summary
            self._clear_data_tabs_only()

            # Ensure we have the required display columns including Pp/Ppk
            expected_columns = [
                "element_id", "batch", "cavity", "class", "description",
                "measuring_instrument", "unit", "datum", "evaluation_type",
                "nominal", "lower_tolerance", "upper_tolerance",
                "measurement_1", "measurement_2", "measurement_3", "measurement_4", "measurement_5",
                "minimum", "maximum", "mean", "std_deviation", "pp", "ppk", "status", "force_status"
            ]

            # Group by cavity for multiple tables
            if 'cavity' in df.columns:
                cavities = sorted(df['cavity'].unique())
            else:
                cavities = [1]
                df['cavity'] = 1

            for cavity in cavities:
                try:
                    # Filter data for this cavity
                    cavity_data = df[df['cavity'] == cavity] if 'cavity' in df.columns else df
                    
                    if cavity_data.empty:
                        continue

                    # Create table with proper formatting
                    table = self._parent.table_manager._create_results_table()
                    table.setRowCount(len(cavity_data))

                    # Populate each row with consistent formatting
                    for row_idx, (_, row) in enumerate(cavity_data.iterrows()):
                        self._populate_database_row(table, row_idx, row, expected_columns)

                    # Add tab
                    tab_name = f"📊 Cavity {cavity}" if len(cavities) > 1 else "📊 Data"
                    self._parent.results_tabs.addTab(table, tab_name)

                except Exception as e:
                    self._log(f"⚠️ Error creating table for cavity {cavity}: {str(e)}", "WARNING")
                    continue

            # Enable analysis
            if hasattr(self._parent, 'run_study_button'):
                self._parent.run_study_button.setEnabled(True)

            self._log(f"✅ Database data loaded with consistent formatting for {len(cavities)} cavities")

        except Exception as e:
            self._log(f"❌ Error populating table from DataFrame: {str(e)}", "ERROR")

    def _populate_database_row(self, table: QTableWidget, row: int, data_row: pd.Series, expected_columns: list):
        """Populate row from database data with CONSISTENT formatting"""
        try:
            # Columns that should be centered, bold, dropdown, calculated
            centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]
            bold_columns = [9, 10, 11]
            dropdown_columns = [3, 5, 6, 7, 8, 24]
            calculated_columns = [17, 18, 19, 20, 21, 22, 23]

            # Disable updates during batch operation
            table.setUpdatesEnabled(False)

            try:
                for col_idx, col_name in enumerate(expected_columns):
                    if col_idx >= table.columnCount():
                        break

                    # Get value from data
                    cell_value = data_row.get(col_name, "")
                    if pd.isna(cell_value):
                        cell_value = ""

                    if col_idx in dropdown_columns:
                        # Create dropdown with database value
                        self._create_formatted_dropdown(table, row, col_idx, str(cell_value))
                        
                    elif col_idx in calculated_columns:
                        # Create calculated column (may have pre-calculated values from database)
                        item = QTableWidgetItem(str(cell_value))
                        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                        
                        # Apply consistent calculated column styling
                        if col_idx == 23:  # Status column
                            item.setTextAlignment(Qt.AlignCenter)
                            item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                            item.setForeground(QColor(40, 44, 52))
                            # Apply status-specific color if we have a status
                            if str(cell_value).upper() in ['GOOD', 'OK']:
                                item.setBackground(QColor(46, 125, 50))
                                item.setForeground(QColor(255, 255, 255))
                            elif str(cell_value).upper() in ['BAD', 'NOK']:
                                item.setBackground(QColor(183, 28, 28))
                                item.setForeground(QColor(255, 255, 255))
                        elif col_idx in [21, 22]:  # Pp, Ppk columns
                            item.setTextAlignment(Qt.AlignCenter)
                            item.setBackground(QColor(248, 240, 255))
                            item.setForeground(QColor(138, 43, 226))
                            item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                        else:  # Other calculated columns
                            if col_idx in centered_columns:
                                item.setTextAlignment(Qt.AlignCenter)
                            item.setBackground(QColor(240, 242, 245))
                            item.setForeground(QColor(40, 44, 52))
                            item.setFont(QFont("Segoe UI", 9))
                            
                        table.setItem(row, col_idx, item)
                        
                    else:
                        # Create regular cell with proper formatting
                        item = QTableWidgetItem(str(cell_value))
                        self._apply_consistent_cell_style(item, col_idx, centered_columns, bold_columns)
                        table.setItem(row, col_idx, item)

            finally:
                table.setUpdatesEnabled(True)

        except Exception as e:
            self._log(f"⚠️ Error populating database row {row}: {str(e)}", "WARNING")



    def _load_from_database(self, db_path: str) -> pd.DataFrame:
        """Load data from database file - NEW FUNCTION"""
        try:
            import sqlite3

            conn = sqlite3.connect(db_path)

            # Try common table names for dimensional data
            table_names = ["dimensional_data", "measurements", "results", "data"]
            df = pd.DataFrame()

            for table_name in table_names:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                    if not df.empty:
                        self._log(f"📊 Loaded data from table: {table_name}")
                        break
                except Exception:
                    continue

            conn.close()

            if df.empty:
                # Show available tables to user
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()

                if tables:
                    table_name, ok = QInputDialog.getItem(
                        self._parent,
                        "Select Table",
                        f"Available tables: {', '.join(tables)}\nSelect table to load:",
                        tables,
                        0,
                        False,
                    )
                    if ok:
                        conn = sqlite3.connect(db_path)
                        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                        conn.close()

            return df

        except Exception as e:
            raise Exception(f"Database loading failed: {str(e)}")

    def _load_session_from_file(self, file_path: str):
        """Load session data from file with complete restoration - ENHANCED"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Validate session data
            if "metadata" not in session_data:
                raise ValueError("Invalid session file format")

            metadata = session_data["metadata"]
            self._log(
                f"📂 Loading session: {metadata.get('client_name', 'Unknown')} - {metadata.get('project_ref', 'Unknown')}"
            )

            # Update UI with metadata
            if "report_type" in metadata and hasattr(self._parent, "report_type_combo"):
                try:
                    index = self._parent.report_type_combo.findText(metadata["report_type"])
                    if index >= 0:
                        self._parent.report_type_combo.setCurrentIndex(index)
                except Exception as e:
                    self._log(f"⚠️ Could not set report type: {str(e)}", "WARNING")

            # Set mode
            target_manual_mode = metadata.get("manual_mode", False)
            if hasattr(self._parent, 'manual_mode') and self._parent.manual_mode != target_manual_mode:
                if hasattr(self._parent, '_toggle_mode'):
                    self._parent._toggle_mode()

            # Clear existing data but preserve summary
            self._clear_data_tabs_only()

            # Ensure summary widget exists
            self._ensure_summary_widget()

            # Load table data
            if "table_data" in session_data:
                self._restore_table_data(session_data["table_data"])

            # NEW: Restore summary data
            if "summary_data" in session_data and session_data["summary_data"]:
                if (
                    hasattr(self._parent, "summary_widget")
                    and self._parent.summary_widget
                    and hasattr(self._parent.summary_widget, 'restore_summary_data')
                ):
                    try:
                        self._parent.summary_widget.restore_summary_data(
                            session_data["summary_data"]
                        )
                        self._log("📊 Summary data restored", "INFO")
                    except Exception as e:
                        self._log(f"⚠️ Could not restore summary data: {str(e)}", "WARNING")

            # NEW: Restore analysis results
            if "results_data" in session_data and session_data["results_data"]:
                try:
                    # Convert dict results back to DimensionalResult objects if needed
                    self._parent.results = session_data[
                        "results_data"
                    ]  # Store as dicts for now
                    self._log(
                        f"📈 {len(session_data['results_data'])} analysis results restored",
                        "INFO",
                    )
                except Exception as e:
                    self._log(
                        f"⚠️ Could not restore analysis results: {str(e)}", "WARNING"
                    )

            # Update summary with current table data
            self._update_summary_from_current_tables()

            # Clear unsaved changes flag
            self._clear_unsaved_changes()

            self._log(f"✅ Session loaded successfully from {file_path}")

        except Exception as e:
            error_msg = f"Failed to load session: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Load Error", error_msg)

    def _clear_data_tabs_only(self):
        """Clear only data tabs, preserve summary tab"""
        try:
            if not hasattr(self._parent, 'results_tabs'):
                return
                
            # Find and preserve summary tab
            summary_widget = None

            for i in range(self._parent.results_tabs.count()):
                if "Summary" in self._parent.results_tabs.tabText(i):
                    summary_widget = self._parent.results_tabs.widget(i)
                    break

            # Remove all tabs
            while self._parent.results_tabs.count():
                widget = self._parent.results_tabs.widget(0)
                self._parent.results_tabs.removeTab(0)
                if widget != summary_widget:  # Don't delete summary widget
                    widget.deleteLater()

            # Restore summary tab as first tab
            if summary_widget:
                self._parent.results_tabs.insertTab(
                    0, summary_widget, "📊 Enhanced Summary"
                )
                self._parent.results_tabs.setCurrentIndex(0)

        except Exception as e:
            self._log(f"❌ Error clearing data tabs: {str(e)}", "ERROR")

    def _ensure_summary_widget(self):
        """Ensure summary widget exists and is properly positioned"""
        try:
            if (
                not hasattr(self._parent, "summary_widget")
                or not self._parent.summary_widget
            ):
                if hasattr(self._parent, '_init_summary_widget'):
                    self._parent._init_summary_widget()

            # Ensure it's in the tabs
            if hasattr(self._parent.summary_widget, 'ensure_visibility'):
                self._parent.summary_widget.ensure_visibility()

        except Exception as e:
            self._log(f"❌ Error ensuring summary widget: {str(e)}", "ERROR")

    def _restore_table_data(self, table_data_list: list):
        """Restore table data from session with CONSISTENT FORMATTING"""
        try:
            if not hasattr(self._parent, 'table_manager') or not hasattr(self._parent, 'results_tabs'):
                self._log("❌ Missing required parent components for table restoration", "ERROR")
                return
                
            for tab_data in table_data_list:
                try:
                    # Create table using the table manager's method to ensure consistency
                    table = self._parent.table_manager._create_results_table()
                    
                    # Set row count
                    row_count = len(tab_data["rows"])
                    table.setRowCount(row_count)

                    # Restore each row with PROPER FORMATTING
                    for row_idx, row_info in enumerate(tab_data["rows"]):
                        # Handle both old and new format
                        if isinstance(row_info, dict):
                            row_data = row_info.get("cells", [])
                            dropdown_data = row_info.get("dropdowns", {})
                        else:
                            row_data = row_info
                            dropdown_data = {}

                        # POPULATE ROW WITH CONSISTENT FORMATTING
                        self._populate_restored_row(table, row_idx, row_data, dropdown_data)

                    # Add tab to results
                    self._parent.results_tabs.addTab(table, tab_data["tab_name"])
                    
                except Exception as e:
                    self._log(f"⚠️ Error restoring table '{tab_data.get('tab_name', 'Unknown')}': {str(e)}", "WARNING")
                    continue

            # Enable run button if data was loaded
            if table_data_list and hasattr(self._parent, 'run_study_button'):
                self._parent.run_study_button.setEnabled(True)

        except Exception as e:
            self._log(f"❌ Error restoring table data: {str(e)}", "ERROR")

    def _populate_restored_row(self, table: QTableWidget, row: int, row_data: list, dropdown_data: dict):
        """FIXED: Populate restored row with correct dropdown handling"""
        try:
            # Get the display columns and ensure we have the UI manager
            display_columns = self._parent.table_manager.display_columns
            
            # FIXED: Correct dropdown columns mapping
            dropdown_columns = [3, 5, 6, 7, 8, 24]  # Including column 24 (force_status)
            calculated_columns = [17, 18, 19, 20, 21, 22, 23]
            centered_columns = [2, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23]
            bold_columns = [9, 10, 11]

            # Disable updates during batch operation
            table.setUpdatesEnabled(False)

            try:
                for col_idx in range(len(display_columns)):
                    if col_idx >= table.columnCount():
                        break

                    if col_idx in dropdown_columns:
                        # FIXED: Create dropdown with correct value from saved data
                        saved_value = dropdown_data.get(str(col_idx), dropdown_data.get(col_idx, ""))
                        self._create_formatted_dropdown_with_value(table, row, col_idx, saved_value)
                        self._log(f"🔄 Restored dropdown col {col_idx}: '{saved_value}'", "DEBUG")
                        
                    elif col_idx in calculated_columns:
                        # Create calculated column with proper read-only styling
                        self._create_calculated_column_item(table, row, col_idx, row_data, centered_columns)
                        
                    else:
                        # Create regular cell with proper formatting
                        cell_value = row_data[col_idx] if col_idx < len(row_data) else ""
                        item = QTableWidgetItem(str(cell_value))
                        
                        # Apply consistent styling
                        self._apply_consistent_cell_style(item, col_idx, centered_columns, bold_columns)
                        table.setItem(row, col_idx, item)

            finally:
                table.setUpdatesEnabled(True)

        except Exception as e:
            self._log(f"⚠️ Error populating restored row {row}: {str(e)}", "WARNING")

    def _create_formatted_dropdown_with_value(self, table: QTableWidget, row: int, col: int, value: str):
        """FIXED: Create dropdown with correct value restoration"""
        try:
            # Get the dropdown style
            dropdown_style = self._get_consistent_combo_style()
            combo = None
            
            # FIXED: Create appropriate dropdown based on column with correct options
            if col == 3:  # class
                combo = QComboBox()
                combo.addItems(["", "CC", "SC", "IC"])
                if value in ["", "CC", "SC", "IC"]:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("")
                    self._log(f"⚠️ Invalid class value '{value}', defaulting to empty", "WARNING")
                    
            elif col == 5:  # measuring_instrument
                instrument_options = [
                    "", "3D Scanbox", "CMM", "Visual", "Caliper", "Micrometer", "Vision System",
                    "Laser Scanner", "Optical Comparator", "Height Gauge", "Pin Gauge",
                    "Thread Gauge", "Go/No-Go Gauge", "Surface Roughness Tester", "Hardness Tester",
                    "Coordinate Measuring Arm", "Portable CMM", "Profile Projector"
                ]
                combo = QComboBox()
                combo.addItems(instrument_options)
                if value in instrument_options:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("3D Scanbox")
                    self._log(f"⚠️ Invalid instrument value '{value}', defaulting to 3D Scanbox", "WARNING")
                    
            elif col == 6:  # unit
                combo = QComboBox()
                combo.addItems(["", "mm", "°", "μm", "cm", "in"])
                if value in ["", "mm", "°", "μm", "cm", "in"]:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("mm")
                    self._log(f"⚠️ Invalid unit value '{value}', defaulting to mm", "WARNING")
                    
            elif col == 7:  # datum
                combo = QComboBox()
                combo.addItems(["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
                if value in ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("")
                    self._log(f"⚠️ Invalid datum value '{value}', defaulting to empty", "WARNING")
                    
            elif col == 8:  # evaluation_type
                combo = QComboBox()
                combo.addItems(["Normal", "Basic", "Informative", "Note", "GD&T"])
                if value in ["Normal", "Basic", "Informative", "Note", "GD&T"]:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("Normal")
                    self._log(f"⚠️ Invalid evaluation_type value '{value}', defaulting to Normal", "WARNING")
                    
            elif col == 24:  # FIXED: force_status (the critical missing dropdown)
                combo = QComboBox()
                combo.addItems(["AUTO", "GOOD", "BAD", "T.E.D."])
                if value in ["AUTO", "GOOD", "BAD", "T.E.D."]:
                    combo.setCurrentText(value)
                else:
                    combo.setCurrentText("AUTO")
                    self._log(f"⚠️ Invalid force_status value '{value}', defaulting to AUTO", "WARNING")
            
            if combo:
                combo.setStyleSheet(dropdown_style)
                combo.setMaximumHeight(30)
                table.setCellWidget(row, col, combo)
                self._log(f"✅ Created dropdown col {col} with value '{combo.currentText()}'", "DEBUG")
                    
        except Exception as e:
            self._log(f"⚠️ Error creating dropdown for col {col}: {str(e)}", "DEBUG")

    def _apply_consistent_cell_style(self, item: QTableWidgetItem, col: int, centered_columns: list, bold_columns: list):
        """Apply consistent styling to regular cells matching dimensional_table_ui.py"""
        try:
            # Apply centering for specific columns
            if col in centered_columns:
                item.setTextAlignment(Qt.AlignCenter)
            
            # Apply font styling
            if col in bold_columns:
                font = QFont("Segoe UI", 9, QFont.Bold)
            else:
                font = QFont("Segoe UI", 9)
            
            item.setFont(font)
            item.setForeground(QColor(40, 44, 52))  # text_dark color
            
        except Exception as e:
            self._log(f"⚠️ Error applying cell style for col {col}: {str(e)}", "DEBUG")

    def _create_calculated_column_item(self, table: QTableWidget, row: int, col: int, row_data: list, centered_columns: list):
        """Create calculated column item with consistent read-only styling"""
        try:
            # Get existing value if any
            cell_value = row_data[col] if col < len(row_data) else ""
            item = QTableWidgetItem(str(cell_value))
            
            # Make it read-only
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            
            # Apply consistent styling based on column type (matching dimensional_table_ui.py)
            if col == 23:  # Status column
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item.setForeground(QColor(40, 44, 52))  # text_dark
            elif col in [21, 22]:  # Pp, Ppk columns - special purple styling
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(248, 240, 255))  # Light purple background
                item.setForeground(QColor(138, 43, 226))  # Purple text (process_capability)
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:  # Other calculated columns (min, max, mean, std)
                if col in centered_columns:
                    item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(240, 242, 245))  # readonly color
                item.setForeground(QColor(40, 44, 52))  # text_dark
                item.setFont(QFont("Segoe UI", 9))  # Regular font, not bold
            
            table.setItem(row, col, item)
            
        except Exception as e:
            self._log(f"⚠️ Error creating calculated column item for col {col}: {str(e)}", "DEBUG")

    def _create_formatted_dropdown(self, table: QTableWidget, row: int, col: int, value: str):
        """Create dropdown with consistent formatting matching dimensional_table_ui.py"""
        try:
            # Get the dropdown style from table manager
            dropdown_style = self._get_consistent_combo_style()
            combo = None
            
            # Create appropriate dropdown based on column (matching dimensional_table_ui.py)
            if col == 3:  # class
                combo = QComboBox()
                combo.addItems(["", "CC", "SC", "IC"])
                combo.setCurrentText(value if value in ["", "CC", "SC", "IC"] else "")
            elif col == 5:  # measuring_instrument
                instrument_options = [
                    "", "3D Scanbox", "CMM", "Visual", "Caliper", "Micrometer", "Vision System",
                    "Laser Scanner", "Optical Comparator", "Height Gauge", "Pin Gauge",
                    "Thread Gauge", "Go/No-Go Gauge", "Surface Roughness Tester", "Hardness Tester",
                    "Coordinate Measuring Arm", "Portable CMM", "Profile Projector"
                ]
                combo = QComboBox()
                combo.addItems(instrument_options)
                combo.setCurrentText(value if value in instrument_options else "3D Scanbox")
            elif col == 6:  # unit
                combo = QComboBox()
                combo.addItems(["", "mm", "°", "μm", "cm", "in"])
                combo.setCurrentText(value if value in ["", "mm", "°", "μm", "cm", "in"] else "mm")
            elif col == 7:  # datum
                combo = QComboBox()
                combo.addItems(["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
                combo.setCurrentText(value if value in ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"] else "")
            elif col == 8:  # evaluation_type
                combo = QComboBox()
                combo.addItems(["Normal", "Basic", "Informative", "Note", "GD&T"])
                combo.setCurrentText(value if value in ["Normal", "Basic", "Informative", "Note", "GD&T"] else "Normal")
            elif col == 24:  # force_status
                combo = QComboBox()
                combo.addItems(["AUTO", "GOOD", "BAD", "T.E.D."])
                combo.setCurrentText(value if value in ["AUTO", "GOOD", "BAD", "T.E.D."] else "AUTO")
            
            if combo:
                combo.setStyleSheet(dropdown_style)
                combo.setMaximumHeight(30)
                table.setCellWidget(row, col, combo)
                
        except Exception as e:
            self._log(f"⚠️ Error creating dropdown for col {col}: {str(e)}", "DEBUG")

    def _get_consistent_combo_style(self) -> str:
        """Get consistent combo style matching dimensional_table_ui.py"""
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

    def _restore_dropdown_data(self, table: QTableWidget, row_idx: int, dropdown_data: dict):
        """Restore dropdown data for a table row"""
        try:
            if not hasattr(self._parent, 'table_manager'):
                return
                
            dropdown_columns = {
                3: ("class", getattr(self._parent.table_manager, 'class_options', ['Unknown'])),
                5: ("measuring_instrument", getattr(self._parent.table_manager, 'instrument_options', ['ScanBox'])),
                6: ("unit", getattr(self._parent.table_manager, 'unit_options', ['mm'])),
                7: ("datum", getattr(self._parent.table_manager, 'datum_options', ['A'])),
                8: ("evaluation_type", getattr(self._parent.table_manager, 'evaluation_options', ['Feature'])),
                22: ("force_status", getattr(self._parent.table_manager, 'force_status_options', ['OK', 'NOK'])),
            }

            for col_idx_str, dropdown_value in dropdown_data.items():
                try:
                    col_idx = int(col_idx_str)
                    if col_idx in dropdown_columns:
                        dropdown_info = dropdown_columns[col_idx]
                        combo = QComboBox()
                        combo.addItems(dropdown_info[1])
                        combo.setCurrentText(dropdown_value)
                        if hasattr(self._parent.table_manager, '_get_combo_style'):
                            combo.setStyleSheet(self._parent.table_manager._get_combo_style())
                        combo.setMaximumHeight(30)
                        table.setCellWidget(row_idx, col_idx, combo)
                except Exception as e:
                    self._log(f"⚠️ Error restoring dropdown ({row_idx},{col_idx_str}): {str(e)}", "DEBUG")
        except Exception as e:
            self._log(f"⚠️ Error in dropdown restoration: {str(e)}", "DEBUG")

    def _update_summary_from_current_tables(self):
        """Update summary widget with current table data"""
        try:
            if hasattr(self._parent, "summary_widget") and hasattr(self._parent, "table_manager"):
                if self._parent.summary_widget and hasattr(self._parent.table_manager, '_get_dataframe_from_tables'):
                    df = self._parent.table_manager._get_dataframe_from_tables()
                    if not df.empty:
                        # Store as original data if this is first load
                        self._parent.summary_widget.update_summary(
                            table_data=df,
                            store_original=True,  # Mark as original data
                            force_refresh=True,
                        )
                        self._log("📊 Summary updated with loaded table data", "INFO")
        except Exception as e:
            self._log(f"❌ Error updating summary from tables: {str(e)}", "ERROR")

    def _auto_save_session(self):
        """Auto-save current session with proper file path generation"""
        if not hasattr(self, "unsaved_changes") or not self.unsaved_changes:
            return

        try:
            # Create auto-save directory
            auto_save_dir = os.path.join(
                os.path.expanduser("~"), ".dimensional_studio", "autosave"
            )
            os.makedirs(auto_save_dir, exist_ok=True)

            # Generate auto-save filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_save_file = os.path.join(
                auto_save_dir,
                f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_{timestamp}.json",
            )

            # Clean up old auto-save files
            self._cleanup_old_autosaves(auto_save_dir)

            # Use the optimized save method with proper file path
            self._save_session_optimized(auto_save_file, auto_save=True)
            self._log(f"💾 Auto-saved: {os.path.basename(auto_save_file)}", "DEBUG")

        except Exception as e:
            self._log(f"⚠️ Auto-save failed: {str(e)}", "WARNING")

    def _cleanup_old_autosaves(self, auto_save_dir: str):
        """OPTIMIZED: Clean up old auto-save files with better error handling"""
        try:
            pattern = f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_"
            auto_save_files = []

            # Collect all matching files with their modification times
            for f in os.listdir(auto_save_dir):
                if f.startswith(pattern) and f.endswith(".json"):
                    file_path = os.path.join(auto_save_dir, f)
                    try:
                        mtime = os.path.getmtime(file_path)
                        auto_save_files.append((file_path, mtime))
                    except OSError:
                        # File might be in use or corrupted, skip it
                        continue

            # Sort by modification time, newest first
            auto_save_files.sort(key=lambda x: x[1], reverse=True)

            # Remove files beyond the 5 most recent
            removed_count = 0
            for file_path, _ in auto_save_files[5:]:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    self._log(f"🗑️ Cleaned up: {os.path.basename(file_path)}", "DEBUG")
                except OSError as e:
                    self._log(f"⚠️ Could not remove {os.path.basename(file_path)}: {str(e)}", "DEBUG")

            if removed_count > 0:
                self._log(f"🧹 Cleaned up {removed_count} old auto-save files", "DEBUG")

        except Exception as e:
            self._log(f"⚠️ Auto-save cleanup failed: {str(e)}", "DEBUG")

    def _validate_session_file(self, file_path: str) -> bool:
        """Validate session file before loading"""
        try:
            # Check file exists and has reasonable size
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < 50:  # Too small to be valid
                self._log(f"⚠️ Session file too small: {file_size} bytes", "WARNING")
                return False
            
            if file_size > 50 * 1024 * 1024:  # Larger than 50MB seems excessive
                self._log(f"⚠️ Session file very large: {file_size:,} bytes", "WARNING")
                return False

            # Try to parse JSON
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            # Basic structure validation
            if not isinstance(session_data, dict):
                return False
            
            if "metadata" not in session_data:
                return False
                
            return True

        except json.JSONDecodeError:
            self._log(f"⚠️ Invalid JSON in session file: {file_path}", "WARNING")
            return False
        except Exception as e:
            self._log(f"⚠️ Error validating session file: {str(e)}", "WARNING")
            return False
        
    def _get_session_info(self, file_path: str) -> dict:
        """Get basic information about a session file without loading it fully"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Read only the beginning to get metadata
                content = f.read(2048)  # First 2KB should contain metadata
                
            # Try to extract basic info
            if '"metadata"' in content:
                # Find metadata section
                start = content.find('"metadata"')
                if start > -1:
                    # This is a simplified approach - for production you might want
                    # to use a streaming JSON parser
                    try:
                        session_data = json.loads(content + '}}')  # Close any open brackets
                        metadata = session_data.get("metadata", {})
                        return {
                            "client_name": metadata.get("client_name", "Unknown"),
                            "project_ref": metadata.get("project_ref", "Unknown"),
                            "batch_number": metadata.get("batch_number", "Unknown"),
                            "save_timestamp": metadata.get("save_timestamp", "Unknown"),
                            "version": metadata.get("version", "1.0"),
                            "file_size": os.path.getsize(file_path)
                        }
                    except Exception as e:
                        self._log(f"⚠️ Error parsing session metadata: {str(e)}", "DEBUG")
                        pass
            
            return {
                "client_name": "Unknown",
                "project_ref": "Unknown", 
                "batch_number": "Unknown",
                "save_timestamp": "Unknown",
                "version": "Unknown",
                "file_size": os.path.getsize(file_path)
            }

        except Exception as e:
            self._log(f"⚠️ Error getting session info: {str(e)}", "DEBUG")
            return {}
        
    def _handle_session_error(self, operation: str, error: Exception, file_path: str = None):
        """Centralized error handling for session operations"""
        error_msg = f"{operation} failed: {str(error)}"
        self._log(error_msg, "ERROR")
        
        # Different handling based on operation type
        if "save" in operation.lower():
            QMessageBox.critical(
                self._parent, 
                "Save Error", 
                f"Could not save session.\n\n"
                f"Error: {str(error)}\n\n"
                f"Please check:\n"
                f"• Disk space availability\n"
                f"• File permissions\n"
                f"• Path accessibility"
            )
        elif "load" in operation.lower():
            QMessageBox.critical(
                self._parent,
                "Load Error",
                f"Could not load session.\n\n"
                f"Error: {str(error)}\n\n"
                f"The session file may be:\n"
                f"• Corrupted\n"
                f"• From an incompatible version\n"
                f"• Inaccessible due to permissions"
            )
        else:
            QMessageBox.critical(self._parent, "Session Error", error_msg)

    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.unsaved_changes = False
        if hasattr(self._parent, "setWindowTitle"):
            title = self._parent.windowTitle()
            if title.endswith(" *"):
                self._parent.setWindowTitle(title[:-2])

    def _get_logo_path(self) -> Optional[str]:
        """Get logo path with fallback options"""
        possible_paths = [
            "./assets/images/gui/logo_some.png",
            "./assets/images/logo.png",
            "./images/logo.png",
            "./logo.png"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _export_data(self):
        """Main export method - NO USER PROMPTS, streamlined professional export"""
        if not self._validate_export_data():
            return

        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(
                self._parent, 
                "Select Export Directory",
                os.path.expanduser("~/Documents")
            )
            if not export_dir:
                return

            self._log("🚀 Starting professional PPAP export (streamlined)...", "INFO")
            
            # Prepare export data with smart defaults
            export_data = self._prepare_streamlined_export_data()
            
            # Create export service and generate reports
            export_service = DataExportService()
            export_paths = export_service.export_dimensional_report(
                results=export_data['results'],
                export_dir=export_dir,
                base_filename=export_data['base_filename'],
                metadata=export_data['metadata'],
                summary_data=export_data['summary_data'],
                logo_path=export_data['logo_path'],
                db_config_path=export_data['db_config_path'],
                db_key="primary"
            )

            # Generate and save export summary
            summary_text = export_service.generate_export_summary(export_paths, export_data['metadata'])
            summary_path = os.path.join(export_dir, f"{export_data['base_filename']}_EXPORT_SUMMARY.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_text)

            # Show streamlined success message
            self._show_streamlined_export_success(export_paths, export_dir)
            self._log("✅ Professional PPAP export completed successfully!", "INFO")

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Export Error", error_msg)

    def _prepare_streamlined_export_data(self) -> Dict[str, Any]:
        """Prepare all export data with smart defaults - NO USER INTERACTION"""
        # Get results or convert table data
        results = self._get_results_for_export()
        
        # Generate base filename
        report_type = getattr(self._parent.report_type_combo, 'currentText', lambda: 'Report')().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}_{report_type}_{timestamp}"

        # Gather metadata with smart defaults
        metadata = self._gather_comprehensive_metadata()

        # Get summary data if available
        summary_data = None
        if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
            try:
                if hasattr(self._parent.summary_widget, 'get_summary_data'):
                    summary_data = self._parent.summary_widget.get_summary_data()
            except Exception as e:
                self._log(f"⚠️ Could not get summary data: {str(e)}", "WARNING")

        # Set paths
        logo_path = self._get_logo_path()
        db_config_path = os.path.join("./config/database", "db_config.json")

        return {
            'results': results,
            'base_filename': base_filename,
            'metadata': metadata,
            'summary_data': summary_data,
            'logo_path': logo_path,
            'db_config_path': db_config_path
        }

    def _validate_export_data(self) -> bool:
        """Validate data before export"""
        # Check if we have results or table data
        has_results = hasattr(self._parent, "results") and self._parent.results
        has_table_data = False
        
        if not has_results:
            try:
                if hasattr(self._parent, 'table_manager') and hasattr(self._parent.table_manager, '_get_dataframe_from_tables'):
                    df = self._parent.table_manager._get_dataframe_from_tables()
                    has_table_data = not df.empty
            except Exception:
                pass

        if not has_results and not has_table_data:
            QMessageBox.warning(
                self._parent, 
                "No Data", 
                "No dimensional analysis data available for export.\n\n"
                "Please load data and run analysis before exporting."
            )
            return False

        return True

    def _get_results_for_export(self) -> list:
        """Get results for export with fallback to table data"""
        if hasattr(self._parent, "results") and self._parent.results:
            return self._parent.results

        # Convert table data to results format
        try:
            if hasattr(self._parent, 'table_manager') and hasattr(self._parent.table_manager, '_get_dataframe_from_tables'):
                df = self._parent.table_manager._get_dataframe_from_tables()
                return self._convert_dataframe_to_results(df)
        except Exception as e:
            self._log(f"❌ Error converting table data: {str(e)}", "ERROR")
            return []

    def _convert_dataframe_to_results(self, df: pd.DataFrame) -> list:
        """Convert DataFrame to DimensionalResult-like objects for export"""
        try:
            from src.models.dimensional.dimensional_result import DimensionalResult
            
            results = []
            for _, row in df.iterrows():
                try:
                    # Extract measurements
                    measurements = []
                    for i in range(1, 6):  # M1 to M5
                        val = row.get(f'measurement_{i}')
                        if pd.notna(val) and val != '':
                            measurements.append(float(val))

                    # Create result object
                    result = DimensionalResult(
                        element_id=str(row.get('element_id', '')),
                        measurements=measurements,
                        status=row.get('force_status', 'NOK')
                    )
                    
                    # Add additional attributes
                    result.description = str(row.get('description', ''))
                    result.nominal = self._safe_float(row.get('nominal'))
                    result.lower_tolerance = self._safe_float(row.get('lower_tolerance'))
                    result.upper_tolerance = self._safe_float(row.get('upper_tolerance'))
                    result.measuring_instrument = str(row.get('measuring_instrument', 'ScanBox'))
                    result.unit = str(row.get('unit', 'mm'))
                    result.cavity = int(row.get('cavity', 1)) if pd.notna(row.get('cavity')) else 1
                    
                    results.append(result)
                    
                except Exception as e:
                    self._log(f"⚠️ Error converting row {row.get('element_id', 'unknown')}: {str(e)}", "WARNING")
                    continue

            return results
        except ImportError:
            self._log("❌ Could not import DimensionalResult for export", "ERROR")
            return []

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if pd.notna(value) and value != '':
                return float(value)
        except (ValueError, TypeError):
            pass
        return None

    def _gather_comprehensive_metadata(self) -> Dict[str, Any]:
        """Gather comprehensive metadata with smart defaults - NO USER PROMPTS"""
        base_metadata = {
            'client_name': self.client_name,
            'project_ref': self.project_ref,
            'part_number': self.project_ref,
            'batch_number': self.batch_number,
            'report_type': getattr(self._parent.report_type_combo, 'currentText', lambda: 'Report')(),
            'tolerance_standard': getattr(self._parent.tolerance_combo, 'currentText', lambda: 'ISO 2768-m')(),
            'manual_mode': getattr(self._parent, 'manual_mode', False),
            'export_timestamp': datetime.now().isoformat(),
            'report_date': datetime.now().strftime('%d/%m/%Y'),
            'software_version': '2.0',
            # Professional defaults - no user prompts needed
            'drawing_number': 'TBD',
            'project_leader_name': 'Quality Engineer',
            'project_leader_title': 'Quality Engineer', 
            'quality_facility': 'Quality Lab 1',
            'normative': getattr(self._parent.tolerance_combo, 'currentText', lambda: 'ISO 2768-m')(),
            'inspector': 'Quality Team',
            'quotation_number': self._generate_smart_quotation_number(),
            'part_description': self._generate_smart_part_description(),
            'cavity_count': self._determine_cavity_count(),
            'current_cavity': getattr(self._parent, 'current_cavity', None)
        }
        
        return base_metadata

    def _generate_smart_quotation_number(self) -> str:
        """Generate intelligent quotation number"""
        try:
            # Use project reference and date to create professional quotation number
            date_part = datetime.now().strftime('%y%m')
            batch_part = self.batch_number[-3:] if len(self.batch_number) >= 3 else self.batch_number
            return f"QT-{self.project_ref}-{date_part}-{batch_part}"
        except Exception:
            return f"QT-{self.project_ref}-{datetime.now().strftime('%y%m')}"

    def _generate_smart_part_description(self) -> str:
        """Generate intelligent part description"""
        try:
            if self.client_name and self.project_ref:
                return f"Component for {self.client_name} - Project {self.project_ref}"
            elif self.project_ref:
                return f"Component {self.project_ref}"
            else:
                return "Production Component"
        except Exception:
            return "Production Component"

    def _determine_cavity_count(self) -> int:
        """Determine cavity count from data"""
        try:
            if hasattr(self._parent, "results") and self._parent.results:
                cavities = set()
                for result in self._parent.results:
                    cavity = getattr(result, 'cavity', 1)
                    if cavity:
                        cavities.add(int(cavity))
                return len(cavities)
            else:
                # Try to determine from table data
                if hasattr(self._parent, 'table_manager') and hasattr(self._parent.table_manager, '_get_dataframe_from_tables'):
                    df = self._parent.table_manager._get_dataframe_from_tables()
                    if 'cavity' in df.columns:
                        unique_cavities = df['cavity'].nunique()
                        return max(1, unique_cavities)
        except Exception:
            pass
        return 1

    def _show_streamlined_export_success(self, export_paths: Dict[str, str], export_dir: str):
        """Show streamlined professional export success message"""
        file_count = len(export_paths)
        
        # Create file list
        file_info = []
        if 'excel_report' in export_paths:
            file_info.append(f"📊 Professional PPAP Report: {os.path.basename(export_paths['excel_report'])}")
        if 'json_data' in export_paths:
            file_info.append(f"📁 Complete Data: {os.path.basename(export_paths['json_data'])}")
        
        success_msg = (
            f"🎉 PROFESSIONAL PPAP EXPORT COMPLETED!\n\n"
            f"📂 Location: {export_dir}\n"
            f"📋 Files: {file_count} generated\n\n"
            f"Generated:\n" + "\n".join(file_info) + "\n\n"
            "✨ Professional Features:\n"
            "   • Enhanced automotive-standard header\n"
            "   • Smart metadata generation\n"
            "   • Professional layout and formatting\n"
            "   • Ready for client presentation\n\n"
            "📤 Export ready for automotive industry submission!"
        )

        QMessageBox.information(self._parent, "Export Successful ✅", success_msg)

    def quick_export_current_data(self):
        """Quick export without extensive user prompts"""
        if not self._validate_export_data():
            return

        try:
            # Get quick export directory
            export_dir = QFileDialog.getExistingDirectory(
                self._parent,
                "Quick Export - Select Directory"
            )
            if not export_dir:
                return

            # Prepare minimal export data
            results = self._get_results_for_export()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            base_filename = f"{self.client_name}_{self.project_ref}_QUICK_{timestamp}"

            # Minimal metadata
            metadata = {
                'client_name': self.client_name,
                'project_ref': self.project_ref,
                'part_number': self.project_ref,
                'batch_number': self.batch_number,
                'report_type': 'QUICK_EXPORT',
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'project_leader_name': 'N/A',
                'quality_facility': 'N/A',
                'normative': 'ISO 2768-m'
            }

            # Get summary data if available
            summary_data = None
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                try:
                    if hasattr(self._parent.summary_widget, 'get_summary_data'):
                        summary_data = self._parent.summary_widget.get_summary_data()
                except Exception:
                    pass

            # Export
            export_service = DataExportService()
            export_paths = export_service.export_dimensional_report(
                results=results,
                export_dir=export_dir,
                base_filename=base_filename,
                metadata=metadata,
                summary_data=summary_data,
                logo_path=self._get_logo_path()
            )

            # Quick success message
            QMessageBox.information(
                self._parent,
                "Quick Export Complete",
                f"Quick export completed successfully!\n\n"
                f"Files saved to: {export_dir}\n"
                f"Excel report: {os.path.basename(export_paths.get('excel_report', 'N/A'))}"
            )

            self._log("⚡ Quick export completed successfully!", "INFO")

        except Exception as e:
            error_msg = f"Quick export failed: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Quick Export Error", error_msg)

    def _extract_table_data(self) -> list:
        """Extract table data for session saving"""
        try:
            if hasattr(self._parent, 'table_manager') and hasattr(self._parent.table_manager, '_get_dataframe_from_tables'):
                df = self._parent.table_manager._get_dataframe_from_tables()
                return df.to_dict('records')
        except Exception as e:
            self._log(f"⚠️ Could not extract table data: {str(e)}", "WARNING")
        return []

    def _extract_summary_data(self) -> dict:
        """Extract summary data for session saving"""
        try:
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                if hasattr(self._parent.summary_widget, 'get_summary_data'):
                    return self._parent.summary_widget.get_summary_data()
        except Exception as e:
            self._log(f"⚠️ Could not extract summary data: {str(e)}", "WARNING")
        return {}

    def _extract_results_data(self) -> list:
        """Extract results data for session saving"""
        try:
            if hasattr(self._parent, "results") and self._parent.results:
                return [r.to_dict() if hasattr(r, 'to_dict') else str(r) for r in self._parent.results]
        except Exception as e:
            self._log(f"⚠️ Could not extract results data: {str(e)}", "WARNING")
        return []