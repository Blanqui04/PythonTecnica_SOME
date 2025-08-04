# src/gui/windows/components/dimensional_session_manager.py
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
from PyQt5.QtGui import QColor
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

    def _save_session(self):
        """Save current session to file - ENHANCED with complete summary integration"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self._parent,
                "Save Session",
                f"{self.client_name}_{self.project_ref}_{self.batch_number}_session.json",
                "JSON Files (*.json)",
            )

            if file_path:
                self._save_session_to_file(file_path)
                self.session_file = file_path

            # Mark as saved
            self.unsaved_changes = False
            if hasattr(self._parent, "setWindowTitle"):
                title = self._parent.windowTitle()
                if "*" in title:
                    self._parent.setWindowTitle(title.replace(" *", ""))

            self._log("💾 Session saved successfully", "INFO")

        except Exception as e:
            self._log(f"❌ Error saving session: {str(e)}", "ERROR")

    def _save_summary_metrics(self):
        """Save summary metrics efficiently"""
        try:
            summary_widget = self._parent.summary_widget
            session_data = {
                "metrics": summary_widget.metrics,
                "study_history": summary_widget.study_history[
                    -5:
                ],  # Only last 5 for performance
                "edit_history": summary_widget.edit_history[
                    -10:
                ],  # Only last 10 for performance
                "session_start_time": summary_widget.session_start_time.isoformat(),
            }

            # Save to file
            session_file = f"sessions/{self.client_name}_{self.project_ref}_{self.batch_number}_summary.json"
            os.makedirs("sessions", exist_ok=True)

            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2, default=str)

            self._log_message("💾 Summary metrics saved efficiently", "INFO")

        except Exception as e:
            self._log_message(f"❌ Error saving summary metrics: {str(e)}", "ERROR")

    def _save_session_to_file(self, file_path: str):
        """Save session data to file with complete summary integration - ENHANCED"""
        try:
            session_data = {
                "metadata": {
                    "client_name": self.client_name,
                    "project_ref": self.project_ref,
                    "batch_number": self.batch_number,
                    "report_type": self._parent.report_type_combo.currentText(),
                    "manual_mode": self._parent.manual_mode,
                    "save_timestamp": datetime.now().isoformat(),
                    "version": "2.0",  # Updated version for enhanced format
                },
                "table_data": [],
                "summary_data": {},  # NEW: Complete summary data
                "results_data": [],  # NEW: Analysis results if available
            }

            # Save data from all tables (existing logic but improved)
            for tab_idx in range(self._parent.results_tabs.count()):
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
                            cell_widget = widget.cellWidget(row, col)
                            if isinstance(cell_widget, QComboBox):
                                dropdown_data[col] = cell_widget.currentText()
                                row_data.append("")
                            else:
                                item = widget.item(row, col)
                                row_data.append(item.text() if item else "")

                        tab_data["rows"].append(
                            {"cells": row_data, "dropdowns": dropdown_data}
                        )

                    session_data["table_data"].append(tab_data)

            # NEW: Save complete summary data
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                session_data["summary_data"] = (
                    self._parent.summary_widget.get_summary_data()
                )
                self._log("📊 Summary data included in session", "DEBUG")

            # NEW: Save analysis results if available
            if hasattr(self._parent, "results") and self._parent.results:
                try:
                    session_data["results_data"] = [
                        r.to_dict() for r in self._parent.results
                    ]
                    self._log(
                        f"📈 {len(self._parent.results)} analysis results included",
                        "DEBUG",
                    )
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
                self._parent, "Load Session", "", "JSON Files (*.json)"
            )

            if file_path:
                self._load_session_from_file(file_path)
                self.session_file = file_path

        except Exception as e:
            self._log(f"❌ Error loading session: {str(e)}", "ERROR")

    def _update_summary_from_tables(self):
        """Update summary widget with current table data"""
        if not hasattr(self, "summary_widget"):
            return

        try:
            df = self.table_manager._get_dataframe_from_tables()
            if not df.empty:
                self.summary_widget.update_summary(table_data=df)
        except Exception as e:
            self._log_message(f"❌ Error updating summary: {str(e)}", "ERROR")

    def _load_last_session(self):
        """Load the most recent auto-saved session - ENHANCED"""
        auto_save_dir = os.path.join(
            os.path.expanduser("~"), ".dimensional_studio", "autosave"
        )
        if not os.path.exists(auto_save_dir):
            return

        try:
            pattern = (
                f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_"
            )
            auto_save_files = [
                f
                for f in os.listdir(auto_save_dir)
                if f.startswith(pattern) and f.endswith(".json")
            ]

            if auto_save_files:
                # Get most recent file
                latest_file = max(
                    auto_save_files,
                    key=lambda f: os.path.getctime(os.path.join(auto_save_dir, f)),
                )
                latest_path = os.path.join(auto_save_dir, latest_file)

                # Check if file is recent (within last 24 hours)
                file_age = datetime.now() - datetime.fromtimestamp(
                    os.path.getctime(latest_path)
                )
                if file_age.total_seconds() > 24 * 3600:  # 24 hours
                    self._log("📅 Auto-save file too old, skipping restore", "DEBUG")
                    return

                # Ask user if they want to restore
                reply = QMessageBox.question(
                    self._parent,
                    "Restore Session",
                    f"Found auto-saved session from {datetime.fromtimestamp(os.path.getctime(latest_path)).strftime('%Y-%m-%d %H:%M:%S')}.\n"
                    f"Would you like to restore it?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    self._load_session_from_file(latest_path)
                    self._log("♻️ Auto-saved session restored", "INFO")

        except Exception as e:
            self._log(f"⚠️ Failed to load last session: {str(e)}", "WARNING")

    def closeEvent(self, event):
        """Handle window close event - ENHANCED with summary saving"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self._save_session()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return

        # Clean up summary widget timer
        if hasattr(self, "summary_widget") and hasattr(
            self.summary_widget, "refresh_timer"
        ):
            self.summary_widget.refresh_timer.stop()

        # Clean up processing thread if running
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()

        event.accept()

    def _update_status_from_summary(self):
        """Update status bar with summary information"""
        if not hasattr(self, "summary_widget"):
            return

        try:
            total_dims = self.summary_widget.metrics.get("total_dimensions", 0)
            studies_run = self.summary_widget.metrics.get("total_studies_run", 0)
            edits_made = self.summary_widget.metrics.get("dimensions_edited", 0)

            # Calculate success rate from latest study
            success_rate = 0
            if self.summary_widget.study_history:
                latest = self.summary_widget.study_history[-1]
                if latest["total_dimensions"] > 0:
                    success_rate = (latest["good"] / latest["total_dimensions"]) * 100

            status_text = f"📊 {total_dims} dims | {studies_run} studies | {success_rate:.1f}% success"
            if edits_made > 0:
                status_text += f" | {edits_made} edits"

            self.stats_label.setText(status_text)

        except Exception as e:
            self._log_message(
                f"❌ Error updating status from summary: {str(e)}", "ERROR"
            )

    def _store_original_values(self, table_data: pd.DataFrame):
        """Store original values for comparison tracking"""
        if not hasattr(self, "summary_widget"):
            return

        for _, row in table_data.iterrows():
            element_id = row.get("element_id")
            if element_id and element_id not in self.summary_widget.original_data:
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
                self.summary_widget.original_data[element_id] = original_values

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
            self._parent._populate_table_from_dataframe(df)

            # Store original data and update summary
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
                self._parent.summary_widget.update_summary(
                    table_data=df,
                    store_original=True,  # Mark as original data
                    force_refresh=True,
                )
                self._parent.summary_widget.record_edit(
                    f"Loaded data file: {os.path.basename(file_path)} ({len(df)} records)"
                )

            self._log(f"✅ Successfully loaded {len(df)} rows from file")
            self._parent.run_study_button.setEnabled(True)

        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "File Load Error", error_msg)

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
                index = self._parent.report_type_combo.findText(metadata["report_type"])
                if index >= 0:
                    self._parent.report_type_combo.setCurrentIndex(index)

            # Set mode
            target_manual_mode = metadata.get("manual_mode", False)
            if self._parent.manual_mode != target_manual_mode:
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
                ):
                    self._parent.summary_widget.restore_summary_data(
                        session_data["summary_data"]
                    )
                    self._log("📊 Summary data restored", "INFO")

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
            # Find and preserve summary tab
            summary_widget = None
            # summary_tab_index = -1

            for i in range(self._parent.results_tabs.count()):
                if "Summary" in self._parent.results_tabs.tabText(i):
                    summary_widget = self._parent.results_tabs.widget(i)
                    # summary_tab_index = i
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
                self._parent._init_summary_widget()

            # Ensure it's in the tabs
            self._parent.summary_widget.ensure_visibility()

        except Exception as e:
            self._log(f"❌ Error ensuring summary widget: {str(e)}", "ERROR")

    def _restore_table_data(self, table_data_list: list):
        """Restore table data from session"""
        try:
            for tab_data in table_data_list:
                table = self._parent.table_manager._create_results_table()
                table.setRowCount(len(tab_data["rows"]))

                for row_idx, row_info in enumerate(tab_data["rows"]):
                    # Handle both old and new format
                    if isinstance(row_info, dict):
                        row_data = row_info.get("cells", [])
                        dropdown_data = row_info.get("dropdowns", {})
                    else:
                        row_data = row_info
                        dropdown_data = {}

                    # Set regular cell data
                    for col_idx, cell_value in enumerate(row_data):
                        if col_idx < table.columnCount():
                            item = QTableWidgetItem(str(cell_value))

                            # Make calculated columns read-only
                            if col_idx >= 17 and col_idx != 22:
                                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                                item.setBackground(QColor(240, 240, 240))

                            table.setItem(row_idx, col_idx, item)

                    # Set dropdown data
                    self._restore_dropdown_data(table, row_idx, dropdown_data)

                self._parent.results_tabs.addTab(table, tab_data["tab_name"])

            # Enable run button if data was loaded
            if table_data_list:
                self._parent.run_study_button.setEnabled(True)

        except Exception as e:
            self._log(f"❌ Error restoring table data: {str(e)}", "ERROR")

    def _restore_dropdown_data(
        self, table: QTableWidget, row_idx: int, dropdown_data: dict
    ):
        """Restore dropdown data for a table row"""
        dropdown_columns = {
            3: ("class", self._parent.table_manager.class_options),
            5: ("measuring_instrument", self._parent.table_manager.instrument_options),
            6: ("unit", self._parent.table_manager.unit_options),
            7: ("datum", self._parent.table_manager.datum_options),
            8: ("evaluation_type", self._parent.table_manager.evaluation_options),
            22: ("force_status", self._parent.table_manager.force_status_options),
        }

        for col_idx_str, dropdown_value in dropdown_data.items():
            col_idx = int(col_idx_str)
            if col_idx in dropdown_columns:
                dropdown_info = dropdown_columns[col_idx]
                combo = QComboBox()
                combo.addItems(dropdown_info[1])
                combo.setCurrentText(dropdown_value)
                combo.setStyleSheet(self._parent.table_manager._get_combo_style())
                combo.setMaximumHeight(30)
                table.setCellWidget(row_idx, col_idx, combo)

    def _update_summary_from_current_tables(self):
        """Update summary widget with current table data"""
        try:
            if hasattr(self._parent, "summary_widget") and hasattr(
                self._parent, "table_manager"
            ):
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
        """Auto-save current session - ENHANCED"""
        if not self.unsaved_changes:
            return

        try:
            # Create auto-save directory
            auto_save_dir = os.path.join(
                os.path.expanduser("~"), ".dimensional_studio", "autosave"
            )
            os.makedirs(auto_save_dir, exist_ok=True)

            # Generate auto-save filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_save_file = os.path.join(
                auto_save_dir,
                f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_{timestamp}.json",
            )

            # Clean up old auto-save files (keep only last 5)
            self._cleanup_old_autosaves(auto_save_dir)

            # Save session
            self._save_session_to_file(auto_save_file)
            self._log(
                f"💾 Auto-saved session: {os.path.basename(auto_save_file)}", "DEBUG"
            )

        except Exception as e:
            self._log(f"⚠️ Auto-save failed: {str(e)}", "WARNING")

    def _cleanup_old_autosaves(self, auto_save_dir: str):
        """Clean up old auto-save files"""
        try:
            pattern = (
                f"autosave_{self.client_name}_{self.project_ref}_{self.batch_number}_"
            )
            auto_save_files = [
                os.path.join(auto_save_dir, f)
                for f in os.listdir(auto_save_dir)
                if f.startswith(pattern) and f.endswith(".json")
            ]

            # Sort by modification time, newest first
            auto_save_files.sort(key=os.path.getmtime, reverse=True)

            # Remove files beyond the 5 most recent
            for old_file in auto_save_files[5:]:
                try:
                    os.remove(old_file)
                    self._log(
                        f"🗑️ Cleaned up old auto-save: {os.path.basename(old_file)}",
                        "DEBUG",
                    )
                except Exception:
                    pass

        except Exception as e:
            self._log(f"⚠️ Auto-save cleanup failed: {str(e)}", "DEBUG")

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
        """Main export method - optimized for professional PPAP reports"""
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

            self._log("🚀 Starting professional PPAP export...", "INFO")
            
            # Prepare export data
            export_data = self._prepare_export_data()
            
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

            # Show success message
            self._show_export_success(export_paths, export_dir)
            self._log("✅ Professional PPAP export completed successfully!", "INFO")

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self._log(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Export Error", error_msg)

    def _validate_export_data(self) -> bool:
        """Validate data before export"""
        # Check if we have results or table data
        has_results = hasattr(self._parent, "results") and self._parent.results
        has_table_data = False
        
        if not has_results:
            try:
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

    def _prepare_export_data(self) -> Dict[str, Any]:
        """Prepare all export data with optimized gathering"""
        # Get results or convert table data
        results = self._get_results_for_export()
        
        # Generate base filename
        report_type = self._parent.report_type_combo.currentText().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}_{report_type}_{timestamp}"

        # Gather metadata with database enhancement
        metadata = self._gather_comprehensive_metadata()

        # Get summary data if available
        summary_data = None
        if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
            try:
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

    def _get_results_for_export(self) -> list:
        """Get results for export with fallback to table data"""
        if hasattr(self._parent, "results") and self._parent.results:
            return self._parent.results

        # Convert table data to results format
        try:
            df = self._parent.table_manager._get_dataframe_from_tables()
            return self._convert_dataframe_to_results(df)
        except Exception as e:
            self._log(f"❌ Error converting table data: {str(e)}", "ERROR")
            return []

    def _convert_dataframe_to_results(self, df: pd.DataFrame) -> list:
        """Convert DataFrame to DimensionalResult-like objects for export"""
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

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if pd.notna(value) and value != '':
                return float(value)
        except (ValueError, TypeError):
            pass
        return None

    def _gather_comprehensive_metadata(self) -> Dict[str, Any]:
        """Gather comprehensive metadata with user input for missing fields"""
        base_metadata = {
            'client_name': self.client_name,
            'project_ref': self.project_ref,
            'part_number': self.project_ref,
            'batch_number': self.batch_number,
            'report_type': self._parent.report_type_combo.currentText(),
            'tolerance_standard': self._parent.tolerance_combo.currentText(),  # NEW: Get from UI
            'manual_mode': getattr(self._parent, 'manual_mode', False),
            'export_timestamp': datetime.now().isoformat(),
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'software_version': '2.0'
        }

        # Ask user for critical missing information
        enhanced_metadata = self._collect_missing_metadata(base_metadata)
        
        return enhanced_metadata

    def _collect_missing_metadata(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Collect missing metadata through user dialogs"""
        metadata = base_metadata.copy()
        
        try:
            # Drawing number
            drawing_number, ok = QInputDialog.getText(
                self._parent,
                'Export Setup - Drawing Information',
                'Drawing Number (optional):',
                text=metadata.get('drawing_number', '')
            )
            if ok:
                metadata['drawing_number'] = drawing_number.strip()

            # Project leader
            project_leader, ok = QInputDialog.getText(
                self._parent,
                'Export Setup - Quality Team',
                'Project Leader Name:',
                text=metadata.get('project_leader_name', '')
            )
            if ok:
                metadata['project_leader_name'] = project_leader.strip()

            # Quality facility
            quality_facility, ok = QInputDialog.getText(
                self._parent,
                'Export Setup - Facility',
                'Quality Facility:',
                text=metadata.get('quality_facility', '')
            )
            if ok:
                metadata['quality_facility'] = quality_facility.strip()

            # Normative standard
            normative_options = [
                'ISO 2768-m', 'ISO 1101', 'ASME Y14.5', 'DIN 7167', 
                'JIS B 0621', 'ISO 5459', 'ASME Y14.5M'
            ]
            
            normative, ok = QInputDialog.getItem(
                self._parent,
                'Export Setup - Standards',
                'Normative Standard:',
                normative_options,
                0,
                False
            )
            if ok:
                metadata['normative'] = normative

            # Set default values for remaining fields
            metadata.setdefault('project_leader_title', 'Quality Engineer')
            metadata.setdefault('inspector', metadata.get('project_leader_name', ''))
            metadata.setdefault('quotation_number', '')

        except Exception as e:
            self._log(f"⚠️ Error collecting metadata: {str(e)}", "WARNING")

        return metadata

    def _show_export_success(self, export_paths: Dict[str, str], export_dir: str):
        """Show professional export success message"""
        file_count = len(export_paths)
        
        # Create file list
        file_info = []
        if 'excel_report' in export_paths:
            file_info.append(f"📊 Excel PPAP Report: {os.path.basename(export_paths['excel_report'])}")
        if 'json_data' in export_paths:
            file_info.append(f"📁 JSON Data: {os.path.basename(export_paths['json_data'])}")
        
        success_msg = (
            f"🎉 PROFESSIONAL PPAP EXPORT COMPLETED SUCCESSFULLY!\n\n"
            f"📂 Export Location: {export_dir}\n"
            f"📋 Files Generated: {file_count}\n\n"
            f"Generated Files:\n" + "\n".join(file_info) + "\n\n"
            "✨ The Excel report includes:\n"
            "   • Professional PPAP-compliant header\n"
            "   • Complete dimensional analysis data\n"
            "   • Cavity-specific sheets (if applicable)\n"
            "   • Analysis summary and statistics\n"
            "   • Signature areas for quality approval\n\n"
            "📤 Ready for client presentation and regulatory submission!"
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
            if hasattr(self._parent, 'table_manager'):
                df = self._parent.table_manager._get_dataframe_from_tables()
                return df.to_dict('records')
        except Exception as e:
            self._log(f"⚠️ Could not extract table data: {str(e)}", "WARNING")
        return []

    def _extract_summary_data(self) -> dict:
        """Extract summary data for session saving"""
        try:
            if hasattr(self._parent, "summary_widget") and self._parent.summary_widget:
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