# src/gui/windows/dimensional_study_window.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QTabWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
import pandas as pd
import os
from typing import List

from .base_dimensional_window import BaseDimensionalWindow
from .components.dimensional_table_manager import DimensionalTableManager
from .components.dimensional_session_manager import SessionManager
from src.models.dimensional.dimensional_result import DimensionalResult
from ..workers.dimensional_processing_thread import ProcessingThread


class DimensionalStudyWindow(BaseDimensionalWindow):
    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__(client, ref_project, batch_number)

        self.unsaved_changes = False
        # Initialize managers
        self.table_manager = DimensionalTableManager(
            display_columns=[
                "element_id",
                "batch",
                "cavity",
                "class",
                "description",
                "measuring_instrument",  # Added missing comma
                "nominal",
                "lower_tolerance",
                "upper_tolerance",
                "measurement_1",
                "measurement_2",
                "measurement_3",
                "measurement_4",
                "measurement_5",
                "minimum",
                "maximum",
                "mean",
                "std_deviation",
                "status",
                "force_status",
            ],
            column_headers=[
                "Element ID",
                "Batch",
                "Cavity",
                "Class",
                "Description",
                "Measuring Inst.",
                "Nominal",
                "Lower Tol",
                "Upper Tol",
                "Meas 1",
                "Meas 2",
                "Meas 3",
                "Meas 4",
                "Meas 5",
                "Min",
                "Max",
                "Mean",
                "Std Dev",
                "Status",
                "Force Status",
            ],
            required_columns=[
                "element_id",
                "batch",
                "cavity",
                "class",
                "description",
                "measuring_instrument",  # Added missing comma
                "nominal",
                "lower_tolerance",
                "upper_tolerance",
            ],
            measurement_columns=[
                "measurement_1",
                "measurement_2",
                "measurement_3",
                "measurement_4",
                "measurement_5",
            ],
            batch_number=batch_number,
        )
        self.table_manager.set_parent_window(self)
        self.session_manager = SessionManager(
            client,
            ref_project,
            batch_number,
            log_callback=self._log_message,
            parent=self,
        )
        self.processing_thread = None
        self.results = []
        self.manual_mode = False

        # Setup UI
        self.setWindowTitle("Dimensional Study")
        self.setMinimumSize(1400, 900)
        self._init_ui()
        self.session_manager._load_last_session()

    def _init_ui(self):
        self.setWindowTitle("Dimensional Study")
        self.resize(1400, 900)

        main_layout = QVBoxLayout()

        # ───── TOP HEADER ─────
        header_layout = QHBoxLayout()

        # LEFT INFO BLOCK (client, project, batch)
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"<b>Client:</b> {self.client_name}"))
        info_layout.addWidget(QLabel(f"<b>Project Ref:</b> {self.project_ref}"))
        info_layout.addWidget(QLabel(f"<b>Batch:</b> {self.batch_number}"))

        # CENTER CONTROLS
        control_layout = QVBoxLayout()
        type_label = QLabel("Report Type:")
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            ["PPAP", "FOT", "Intern audit", "Process validation"]
        )
        control_layout.addWidget(type_label)
        control_layout.addWidget(self.report_type_combo)

        # Mode selector buttons
        mode_layout = QHBoxLayout()
        control_layout.addLayout(mode_layout)

        # RIGHT LOGO
        logo_label = QLabel()
        logo_path = (
            "assets/images/gui/logo_some.png"  # Adjust if your logo is elsewhere
        )
        if os.path.exists(logo_path):
            logo_label.setPixmap(
                QPixmap(logo_path).scaled(
                    160, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        header_layout.addLayout(info_layout)
        header_layout.addStretch(1)
        header_layout.addLayout(control_layout)
        header_layout.addStretch(1)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)

        # ───── ACTION BUTTONS ─────
        # Mode toggle and controls
        mode_layout = QHBoxLayout()
        self.mode_toggle = QPushButton("Switch to Manual Entry")
        self.load_file_button = QPushButton("📁 Load File")
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addWidget(self.load_file_button)

        # Manual mode buttons (initially hidden)
        self.add_row_button = QPushButton("➕ Add Row")
        self.duplicate_row_button = QPushButton("📋 Duplicate Row")
        self.delete_row_button = QPushButton("🗑️ Delete Row")
        self.add_row_button.setVisible(False)
        self.duplicate_row_button.setVisible(False)
        self.delete_row_button.setVisible(False)

        mode_layout.addWidget(self.add_row_button)
        mode_layout.addWidget(self.duplicate_row_button)
        mode_layout.addWidget(self.delete_row_button)
        control_layout.addLayout(mode_layout)

        buttons_layout = QHBoxLayout()
        # Add Run Study button
        self.run_study_button = QPushButton("🔬 Run Dimensional Study")
        self.run_study_button.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.run_study_button)
        self.save_session_button = QPushButton("💾 Save Session")
        self.load_session_button = QPushButton("📂 Load Session")
        self.export_data_button = QPushButton("📤 Export Data")
        self.clear_button = QPushButton("🧹 Clear All")

        buttons_layout.addWidget(self.save_session_button)
        buttons_layout.addWidget(self.load_session_button)
        buttons_layout.addWidget(self.export_data_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Processing...")

        buttons_layout.addWidget(self.progress_bar)
        main_layout.addLayout(buttons_layout)

        # ───── RESULTS AREA ─────
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabsClosable(True)
        self.results_tabs.tabCloseRequested.connect(self._remove_tab)
        main_layout.addWidget(self.results_tabs)

        # ───── LOG OUTPUT ─────
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(120)
        self.log_area.setStyleSheet("background-color: #f9f9f9;")
        main_layout.addWidget(self.log_area)

        # Finalize
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Mode and file operations
        self.mode_toggle.clicked.connect(self._toggle_mode)
        self.load_file_button.clicked.connect(self.session_manager._load_file)

        # Manual mode buttons
        self.add_row_button.clicked.connect(self._add_manual_row)
        self.duplicate_row_button.clicked.connect(self._duplicate_row)
        self.delete_row_button.clicked.connect(self._delete_row)

        # Run study button
        self.run_study_button.clicked.connect(self._run_study)

        # Session buttons stay the same
        self.save_session_button.clicked.connect(self.session_manager._save_session)
        self.load_session_button.clicked.connect(self.session_manager._load_session)
        self.export_data_button.clicked.connect(self.session_manager._export_data)
        self.clear_button.clicked.connect(self._clear_all)

    def _remove_tab(self, index: int):
        """Removes the tab at the given index from the results tab widget."""
        if 0 <= index < self.results_tabs.count():
            widget = self.results_tabs.widget(index)
            self.results_tabs.removeTab(index)
            widget.deleteLater()
            self._log_message(f"Closed results tab #{index}")

    def _run_study(self):
        """Execute the dimensional study"""
        try:
            # Get dataframe from current table data
            df = self.table_manager._get_dataframe_from_tables()
            if df.empty:
                QMessageBox.warning(self, "No Data", "No valid data found to process.")
                return

            self._log_message(f"Starting dimensional analysis on {len(df)} records")

            # Disable UI during processing
            self._set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Start processing in thread
            self.processing_thread = ProcessingThread(df)
            self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.processing_thread.processing_finished.connect(
                self._on_processing_finished
            )
            self.processing_thread.error_occurred.connect(self._on_processing_error)
            self.processing_thread.start()

        except Exception as e:
            error_msg = f"Error starting dimensional study: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Processing Error", error_msg)
            self._set_ui_enabled(True)

    def _start_processing_thread(self, df: pd.DataFrame):
        """Start the processing thread with the given dataframe"""
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)

        self.processing_thread = ProcessingThread(df)
        self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processing_thread.processing_finished.connect(self._on_processing_finished)
        self.processing_thread.error_occurred.connect(self._on_processing_error)
        self.processing_thread.start()

    def _on_processing_finished(self, results: List[DimensionalResult]):
        """Handle completion of processing"""
        self.results = results
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)

        if not results:
            self._log_message("No valid results generated", "WARNING")
            QMessageBox.information(
                self,
                "No Results",
                "No valid results were generated from the input data.",
            )
            return

        self._log_message(
            f"Analysis completed successfully. Generated {len(results)} results"
        )
        self.table_manager._update_tables_with_results(results)
        self.export_data_button.setEnabled(True)
        self.session_manager._auto_save_session()

    def _handle_error(self, context: str, error: Exception):
        """Centralized error handling"""
        error_msg = f"{context}: {str(error)}"
        self._log_message(error_msg, "ERROR")
        QMessageBox.critical(self, "Error", error_msg)

    def _clear_all(self):
        """Clear all UI elements, tabs, logs, and internal states."""
        reply = QMessageBox.question(
            self,
            "Clear All?",
            "Are you sure you want to clear all data, results, and logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear result tabs
                while self.results_tabs.count():
                    widget = self.results_tabs.widget(0)
                    self.results_tabs.removeTab(0)
                    widget.deleteLater()

                # Clear the log area
                self.log_area.clear()

                # Reset any data structures
                self.results = []

                # Call your (placeholder) table manager reset
                self.table_manager.clear_all_tables()

                self._clear_unsaved_changes()
                self._log_message("All data cleared.")
            except Exception as e:
                self._handle_error("Clear All", e)

    def _toggle_mode(self):
        """Toggle between file and manual entry modes"""
        self.manual_mode = not self.manual_mode
        if self.manual_mode:
            self.mode_toggle.setText("Switch to File Mode")
            self._prepare_manual_table()
            self.add_row_button.setVisible(True)
            self.duplicate_row_button.setVisible(True)
            self.delete_row_button.setVisible(True)
            self.load_file_button.setVisible(False)
            self._log_message("Switched to manual entry mode")
        else:
            self.mode_toggle.setText("Switch to Manual Entry")
            self._clear_current_data()  # Use a simpler clear method
            self.add_row_button.setVisible(False)
            self.duplicate_row_button.setVisible(False)
            self.delete_row_button.setVisible(False)
            self.load_file_button.setVisible(True)
            self.run_study_button.setEnabled(False)  # Disable run button
            self._log_message("Switched to file mode")

    def _clear_current_data(self):
        """Clear current data without confirmation dialog"""
        try:
            # Clear all tabs
            while self.results_tabs.count():
                widget = self.results_tabs.widget(0)
                self.results_tabs.removeTab(0)
                widget.deleteLater()

            # Reset data structures
            self.results = []
            self.run_study_button.setEnabled(False)
            self._clear_unsaved_changes()
            self._log_message("Data cleared for mode switch")

        except Exception as e:
            self._handle_error("Clear Current Data", e)

    def _on_processing_error(self, error_msg: str):
        """Handle processing thread errors"""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        self._log_message(f"Processing error: {error_msg}", "ERROR")
        QMessageBox.critical(self, "Processing Error", f"Analysis failed:\n{error_msg}")

    def _prepare_manual_table(self):
        """Prepare table for manual data entry"""
        # Clear existing tabs except summary
        while self.results_tabs.count() > 1:
            self.results_tabs.removeTab(1)

        # Create main data entry table
        main_table = self.table_manager._create_results_table()
        self.results_tabs.addTab(main_table, "📝 Data Entry")

        # Add initial row
        main_table.setRowCount(1)
        self.table_manager._populate_default_row(main_table, 0)

    def _add_manual_row(self):
        """Add a new row for manual entry"""
        current_table = self.results_tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        row_count = current_table.rowCount()
        current_table.insertRow(row_count)
        self.table_manager._populate_default_row(current_table, row_count)
        self._mark_unsaved_changes()
        self.run_study_button.setEnabled(True)  # Enable run button when data exists

    def _duplicate_row(self):
        """Duplicate the currently selected row"""
        current_table = self.results_tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        current_row = current_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a row to duplicate."
            )
            return

        # Insert new row
        current_table.insertRow(current_row + 1)

        # Copy data from current row
        for col in range(current_table.columnCount()):
            item = current_table.item(current_row, col)
            if item and col < 13:  # Don't copy calculated columns
                new_item = QTableWidgetItem(item.text())
                current_table.setItem(current_row + 1, col, new_item)
            elif col >= 13:  # Set up calculated columns
                calc_item = QTableWidgetItem("")
                calc_item.setFlags(calc_item.flags() ^ Qt.ItemIsEditable)
                calc_item.setBackground(QColor(240, 240, 240))
                current_table.setItem(current_row + 1, col, calc_item)

        self._mark_unsaved_changes()

    def _delete_row(self):
        """Delete the currently selected row"""
        current_table = self.results_tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        current_row = current_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a row to delete."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this row?"
        )
        if reply == QMessageBox.Yes:
            current_table.removeRow(current_row)
            self._mark_unsaved_changes()

    def _load_file(self):
        """Load measurement data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
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

            self._populate_table_from_dataframe(df)
            self._log_message(f"Successfully loaded {len(df)} rows from file")
            self.run_study_button.setEnabled(True)  # Enable run button

        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "File Load Error", error_msg)

    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        title = self.windowTitle()
        if not title.endswith(" *"):
            self.setWindowTitle(title + " *")

    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.unsaved_changes = False
        title = self.windowTitle()
        if title.endswith(" *"):
            self.setWindowTitle(title[:-2])

    def _populate_table_from_dataframe(self, df: pd.DataFrame):
        """Populate table from dataframe, organizing by cavities"""
        # Clear existing tabs
        while self.results_tabs.count():
            self.results_tabs.removeTab(0)

        # Group by cavity if cavity column exists
        if "cavity" in df.columns:
            cavities = sorted(df["cavity"].unique())
        else:
            cavities = [1]  # Default single cavity
            df["cavity"] = 1

        for cavity in cavities:
            cavity_df = df[df["cavity"] == cavity] if "cavity" in df.columns else df

            # Create table for this cavity
            table = self.table_manager._create_results_table()
            table.setRowCount(len(cavity_df))

            # Populate table
            for row_idx, (_, row) in enumerate(cavity_df.iterrows()):
                for col_idx, col_name in enumerate(self.table_manager.display_columns):
                    if col_name in row.index and pd.notna(row[col_name]):
                        value = str(row[col_name])
                    else:
                        value = ""

                    item = QTableWidgetItem(value)

                    # Make calculated columns read-only
                    if col_idx >= 13:  # calculated columns
                        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                        item.setBackground(QColor(240, 240, 240))

                    table.setItem(row_idx, col_idx, item)

            # Add tab for this cavity
            if len(cavities) > 1:
                tab_name = f"🔧 Cavity {cavity} ({len(cavity_df)} items)"
            else:
                tab_name = f"📋 All Data ({len(cavity_df)} items)"
            self.results_tabs.addTab(table, tab_name)

    def _set_ui_enabled(self, enabled: bool):
        """Enable/disable UI during processing"""
        self.mode_toggle.setEnabled(enabled)
        self.load_file_button.setEnabled(enabled)
        self.add_row_button.setEnabled(enabled)
        self.duplicate_row_button.setEnabled(enabled)
        self.delete_row_button.setEnabled(enabled)
        self.run_study_button.setEnabled(enabled)
        self.save_session_button.setEnabled(enabled)
        self.load_session_button.setEnabled(enabled)
