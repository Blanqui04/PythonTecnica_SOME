# src/gui/windows/components/dimensional_session_manager.py
from PyQt5.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pandas as pd
import json
import os
from datetime import datetime
from typing import Optional

from src.services.dim_data_export_service import DataExportService


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

    def _log_message(self, message: str, level: str = "INFO"):
        """Add message to log area and logger"""
        self._log(message, level)
        # timestamp = datetime.now().strftime("%H:%M:%S")
        # self.log_area.append(f"[{timestamp}] [{level}] {message}")
        # getattr(self.logger, level.lower())(message)

    def _save_session(self):
        """Save current session to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Save Session",
            f"{self.client_name}_{self.project_ref}_{self.batch_number}_session.json",
            "JSON Files (*.json)",
        )

        if file_path:
            self._save_session_to_file(file_path)

    def _save_session_to_file(self, file_path: str):
        """Save session data to file"""
        try:
            session_data = {
                "metadata": {
                    "client_name": self.client_name,
                    "project_ref": self.project_ref,
                    "batch_number": self.batch_number,
                    "report_type": self._parent.report_type_combo.currentText(),  # Fix: access via parent
                    "manual_mode": self._parent.manual_mode,  # Fix: access via parent
                    "save_timestamp": datetime.now().isoformat(),
                },
                "table_data": [],
            }

            # Save data from all tables
            for tab_idx in range(
                self._parent.results_tabs.count()
            ):  # Fix: access via parent
                table = self._parent.results_tabs.widget(tab_idx)
                if isinstance(table, QTableWidget):
                    tab_data = {
                        "tab_name": self._parent.results_tabs.tabText(tab_idx),
                        "rows": [],
                    }

                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        tab_data["rows"].append(row_data)

                    session_data["table_data"].append(tab_data)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            # Fix: access session_file via parent if it exists
            if hasattr(self._parent, "session_file"):
                self._parent.session_file = file_path

            # Fix: call parent's method if it exists
            if hasattr(self._parent, "_clear_unsaved_changes"):
                self._parent._clear_unsaved_changes()

            self._log_message(f"Session saved to {file_path}")

        except Exception as e:
            error_msg = f"Failed to save session: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Save Error", error_msg)

    def _load_session(self):
        """Load session from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent, "Load Session", "", "JSON Files (*.json)"
        )

        if file_path:
            self._load_session_from_file(file_path)

    def _load_last_session(self):
        """Load the most recent auto-saved session"""
        auto_save_dir = os.path.join(
            os.path.expanduser("~"), ".dimensional_studio", "autosave"
        )
        if not os.path.exists(auto_save_dir):
            return

        try:
            # Find most recent auto-save file for this project
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

                # Ask user if they want to restore
                reply = QMessageBox.question(
                    self._parent,  # Use self._parent instead of self
                    "Restore Session",
                    f"Found auto-saved session from {datetime.fromtimestamp(os.path.getctime(latest_path)).strftime('%Y-%m-%d %H:%M:%S')}.\n"
                    f"Would you like to restore it?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    self._load_session_from_file(latest_path)

        except Exception as e:
            self._log_message(f"Failed to load last session: {str(e)}", "WARNING")

    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.unsaved_changes = False
        title = self.windowTitle()
        if title.endswith(" *"):
            self.setWindowTitle(title[:-2])

    def _load_file(self):
        """Load measurement data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Select Measurement File",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            self._log_message(f"Loading file: {file_path}")

            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, engine="openpyxl")

            # Call the parent's method instead
            self._parent._populate_table_from_dataframe(df)
            self._log_message(f"Successfully loaded {len(df)} rows from file")
            self._parent.run_study_button.setEnabled(True)  # Enable run button

        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(
                self._parent, "File Load Error", error_msg
            )  # Use self._parent

    def _load_session_from_file(self, file_path: str):
        """Load session data from file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Validate session data
            if "metadata" not in session_data or "table_data" not in session_data:
                raise ValueError("Invalid session file format")

            metadata = session_data["metadata"]

            # Update UI with metadata - access via parent
            if "report_type" in metadata and hasattr(self._parent, "report_type_combo"):
                index = self._parent.report_type_combo.findText(metadata["report_type"])
                if index >= 0:
                    self._parent.report_type_combo.setCurrentIndex(index)

            # Set mode - access via parent
            if metadata.get("manual_mode", False):
                if not self._parent.manual_mode:
                    self._parent._toggle_mode()
            else:
                if self._parent.manual_mode:
                    self._parent._toggle_mode()

            # Clear existing data
            self._parent.results_tabs.clear()

            # Load table data
            for tab_data in session_data["table_data"]:
                table = (
                    self._parent.table_manager._create_results_table()
                )  # Access via parent's table_manager
                table.setRowCount(len(tab_data["rows"]))

                for row_idx, row_data in enumerate(tab_data["rows"]):
                    for col_idx, cell_value in enumerate(row_data):
                        if col_idx < table.columnCount():
                            item = QTableWidgetItem(str(cell_value))

                            # Make calculated columns read-only (columns 14-19)
                            if col_idx >= 14:
                                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                                item.setBackground(QColor(240, 240, 240))

                            table.setItem(row_idx, col_idx, item)

                self._parent.results_tabs.addTab(table, tab_data["tab_name"])

            # Set session file and clear unsaved changes via parent
            if hasattr(self._parent, "session_file"):
                self._parent.session_file = file_path
            if hasattr(self._parent, "_clear_unsaved_changes"):
                self._parent._clear_unsaved_changes()

            self._log_message(f"Session loaded from {file_path}")

        except Exception as e:
            error_msg = f"Failed to load session: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(
                self._parent, "Load Error", error_msg
            )  # Use self._parent instead of self

    def _auto_save_session(self):
        """Auto-save current session"""
        if self.unsaved_changes:
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

            try:
                self._save_session_to_file(auto_save_file)
                self._log_message("Auto-saved session")
            except Exception as e:
                self._log_message(f"Auto-save failed: {str(e)}", "WARNING")

    def _export_data(self):
        """Export results to files"""
        # Fix: Access results through parent window
        if not hasattr(self._parent, 'results') or not self._parent.results:
            QMessageBox.warning(self._parent, "No Results", "No results available to export.")
            return

        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(
                self._parent, "Select Export Directory"
            )
            if not export_dir:
                return

            # Generate base filename with report type - access via parent
            report_type = self._parent.report_type_combo.currentText().replace(" ", "_")
            base_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}_{report_type}_dimensional_results"

            self._log_message(f"Exporting {len(self._parent.results)} results to {export_dir}")

            # Export using the service
            export_service = DataExportService()
            json_path, csv_path = export_service.export_results(
                self._parent.results, export_dir, base_filename  # Use parent's results
            )

            success_msg = f"Results exported successfully:\n- JSON: {json_path}\n- CSV: {csv_path}"
            self._log_message("Export completed successfully")
            QMessageBox.information(self._parent, "Export Successful", success_msg)

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self._parent, "Export Error", error_msg)
