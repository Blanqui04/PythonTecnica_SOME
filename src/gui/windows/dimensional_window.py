# src/gui/windows/enhanced_dimensional_window.py
from PyQt5.QtWidgets import (
    QMainWindow,
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
    QGroupBox,
    QTabWidget,
    QAbstractItemView,
    QMenu,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
import pandas as pd
import logging
import json
import os
import sip  # type: ignore
from datetime import datetime
from typing import List, Optional

from src.services.dimensional_service import DimensionalService
from src.services.dim_data_export_service import DataExportService
from src.models.dimensional.dimensional_result import DimensionalResult


class ProcessingThread(QThread):
    """Thread for processing dimensional analysis to prevent UI freezing"""

    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df

    def run(self):
        try:
            service = DimensionalService()
            results = service.process_dataframe(
                self.df, progress_callback=self.progress_updated.emit
            )
            self.processing_finished.emit(results)
        except Exception as e:
            error_msg = f"Failed to save session: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Save Error", error_msg)

    def _handle_gdt_input(self, description: str) -> str:
        """
        Handle GD&T input in description field

        Args:
            description: Raw description text

        Returns:
            Processed description with GD&T symbols preserved
        """
        # Define GD&T symbol mappings
        gdt_mappings = {
            # Geometric symbols
            "position": "⌖",
            "concentricity": "◎",
            "symmetry": "≡",
            "parallelism": "∥",
            "perpendicularity": "⊥",
            "angularity": "∠",
            "profile line": "⌒",
            "profile surface": "⌓",
            "circularity": "○",
            "cylindricity": "⌭",
            "flatness": "⏤",
            "straightness": "⏤",
            "runout": "↗",
            "total runout": "↗↗",
            # Material condition modifiers
            "(M)": "Ⓜ",
            "(L)": "Ⓛ",
            "(S)": "Ⓢ",
            # Diameter symbol
            "diameter": "Ø",
            "dia": "Ø",
            "diam": "Ø",
            "ø": "Ø",
        }

        processed_description = description

        # Apply mappings (case insensitive)
        for text, symbol in gdt_mappings.items():
            processed_description = processed_description.replace(text.lower(), symbol)
            processed_description = processed_description.replace(text.upper(), symbol)
            processed_description = processed_description.replace(text.title(), symbol)

        return processed_description

    def _validate_gdt_description(self, description: str) -> tuple[bool, list[str]]:
        """
        Validate GD&T description format

        Args:
            description: Description text to validate

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []

        # Check for common GD&T patterns
        gdt_patterns = [
            r"position\s+[\d.,]+\s*\([MLS]\)",  # position 0.5(M)
            r"parallelism\s+[\d.,]+",  # parallelism 0.1
            r"perpendicularity\s+[\d.,]+",  # perpendicularity 0.05
            r"profile\s+[\d.,]+",  # profile 0.2
            r"flatness\s+[\d.,]+",  # flatness 0.01
            r"circularity\s+[\d.,]+",  # circularity 0.05
        ]

        import re

        # Check if description contains GD&T elements
        has_gdt = any(
            re.search(pattern, description.lower()) for pattern in gdt_patterns
        )

        if has_gdt:
            # Validate datum references
            datum_pattern = r"[A-Z]\s*[A-Z]?\s*[A-Z]?"
            datums = re.findall(datum_pattern, description.upper())

            if len(datums) > 3:
                warnings.append(
                    "More than 3 datum references found - verify correctness"
                )

            # Check for material condition without tolerance
            if re.search(r"\([MLS]\)", description) and not re.search(
                r"[\d.,]+", description
            ):
                warnings.append(
                    "Material condition modifier found without tolerance value"
                )

        return True, warnings  # Always valid, but may have warnings

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            if self.unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before closing?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )

                if reply == QMessageBox.Yes:
                    if self.session_file:
                        self._save_session_to_file(self.session_file)
                    else:
                        self._save_session()
                    event.accept()
                elif reply == QMessageBox.No:
                    event.accept()
                else:
                    event.ignore()
                    return

            if self.processing_thread and self.processing_thread.isRunning():
                reply = QMessageBox.question(
                    self,
                    "Processing in Progress",
                    "Analysis is still running. Are you sure you want to close?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                else:
                    self.processing_thread.terminate()
                    self.processing_thread.wait()

            # Stop auto-save timer
            self.auto_save_timer.stop()

            self._log_message("Enhanced Dimensional Study window closed")
            event.accept()

        except Exception as e:
            logging.error(f"Processing thread error: {str(e)}")
            self.error_occurred.emit(str(e))


class DimensionalStudyWindow(QMainWindow):
    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__()
        self.setWindowTitle("Enhanced Dimensional Study")
        self.setMinimumSize(1400, 900)

        # Store parameters
        self.client_name = client
        self.project_ref = ref_project
        self.batch_number = batch_number
        self.results: List[DimensionalResult] = []
        self.manual_mode = False
        self.processing_thread: Optional[ProcessingThread] = None
        self.session_file = None
        self.unsaved_changes = False

        # Define simplified column structure
        self.display_columns = [
            "element_id",
            "batch",
            "cavity",
            "class",
            "description",
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
        ]

        # Column headers for display
        self.column_headers = [
            "Element ID",
            "Batch",
            "Cavity",
            "Class",
            "Description",
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
        ]

        # Expected columns for dimensional analysis (original structure)
        self.required_columns = [
            "element_id",
            "batch",
            "cavity",
            "class",
            "description",
            "nominal",
            "lower_tolerance",
            "upper_tolerance",
        ]

        self.measurement_columns = [
            "measurement_1",
            "measurement_2",
            "measurement_3",
            "measurement_4",
            "measurement_5",
        ]

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_session)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes

        # Setup logging
        self._setup_logging()
        self._init_ui()
        self._load_last_session()

    def _setup_logging(self):
        """Setup logging for the dimensional study"""
        self.logger = logging.getLogger(
            f"EnhancedDimensionalStudy_{self.client_name}_{self.project_ref}"
        )
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Header info with report type
        header_group = QGroupBox("Study Information")
        header_layout = QVBoxLayout()

        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"<b>Client:</b> {self.client_name}"))
        info_layout.addWidget(QLabel(f"<b>Project Ref:</b> {self.project_ref}"))
        info_layout.addWidget(QLabel(f"<b>Batch:</b> {self.batch_number}"))

        # Report type selector
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            ["Standard", "PPAP", "FOT", "Initial Sample", "Process Validation"]
        )
        report_layout.addWidget(self.report_type_combo)
        report_layout.addStretch()

        header_layout.addLayout(info_layout)
        header_layout.addLayout(report_layout)
        header_group.setLayout(header_layout)
        main_layout.addWidget(header_group)

        # Control buttons
        control_group = QGroupBox("Controls")
        button_layout = QHBoxLayout()

        # Mode toggle
        self.mode_toggle = QPushButton("Switch to Manual Entry")
        self.mode_toggle.clicked.connect(self._toggle_mode)
        button_layout.addWidget(self.mode_toggle)

        # File operations
        self.load_file_button = QPushButton("Load File")
        self.load_file_button.clicked.connect(self._load_file)
        button_layout.addWidget(self.load_file_button)

        # Row operations (for manual mode)
        self.add_row_button = QPushButton("Add Row")
        self.add_row_button.clicked.connect(self._add_manual_row)
        self.add_row_button.setVisible(False)
        button_layout.addWidget(self.add_row_button)

        self.duplicate_row_button = QPushButton("Duplicate Row")
        self.duplicate_row_button.clicked.connect(self._duplicate_row)
        self.duplicate_row_button.setVisible(False)
        button_layout.addWidget(self.duplicate_row_button)

        self.delete_row_button = QPushButton("Delete Row")
        self.delete_row_button.clicked.connect(self._delete_row)
        self.delete_row_button.setVisible(False)
        button_layout.addWidget(self.delete_row_button)

        button_layout.addStretch()

        # Analysis and export
        self.run_button = QPushButton("Run Dimensional Study")
        self.run_button.clicked.connect(self._run_study)
        self.run_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        button_layout.addWidget(self.run_button)

        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self._export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)

        # Session management
        session_layout = QHBoxLayout()
        self.save_session_button = QPushButton("Save Session")
        self.save_session_button.clicked.connect(self._save_session)
        session_layout.addWidget(self.save_session_button)

        self.load_session_button = QPushButton("Load Session")
        self.load_session_button.clicked.connect(self._load_session)
        session_layout.addWidget(self.load_session_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_data)
        session_layout.addWidget(self.clear_button)

        button_layout.addLayout(session_layout)

        control_group.setLayout(button_layout)
        main_layout.addWidget(control_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Create tabbed interface for different cavity views
        self.results_tabs = QTabWidget()

        # Add summary tab
        self.summary_widget = self._create_summary_widget()
        self.results_tabs.addTab(self.summary_widget, "📊 Summary")

        main_layout.addWidget(self.results_tabs)

        # Log area
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(120)
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.logger.info(
            f"Initialized Enhanced Dimensional Study for {self.client_name} - {self.project_ref} - Batch {self.batch_number}"
        )

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
                    self,
                    "Restore Session",
                    f"Found auto-saved session from {os.path.getctime(latest_path)}.\n"
                    f"Would you like to restore it?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    self._load_session_from_file(latest_path)

        except Exception as e:
            self._log_message(f"Failed to load last session: {str(e)}", "WARNING")

    def _load_session(self):
        """Load session from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", "", "JSON Files (*.json)"
        )

        if file_path:
            self._load_session_from_file(file_path)

    def _load_session_from_file(self, file_path: str):
        """Load session data from file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Validate session data
            if "metadata" not in session_data or "table_data" not in session_data:
                raise ValueError("Invalid session file format")

            metadata = session_data["metadata"]

            # Update UI with metadata
            if "report_type" in metadata:
                index = self.report_type_combo.findText(metadata["report_type"])
                if index >= 0:
                    self.report_type_combo.setCurrentIndex(index)

            # Set mode
            if metadata.get("manual_mode", False):
                if not self.manual_mode:
                    self._toggle_mode()
            else:
                if self.manual_mode:
                    self._toggle_mode()

            # Clear existing data
            self.results_tabs.clear()

            # Load table data
            for tab_data in session_data["table_data"]:
                table = self._create_results_table()
                table.setRowCount(len(tab_data["rows"]))

                for row_idx, row_data in enumerate(tab_data["rows"]):
                    for col_idx, cell_value in enumerate(row_data):
                        if col_idx < table.columnCount():
                            item = QTableWidgetItem(str(cell_value))

                            # Make calculated columns read-only
                            if col_idx >= 13:
                                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                                item.setBackground(QColor(240, 240, 240))

                            table.setItem(row_idx, col_idx, item)

                self.results_tabs.addTab(table, tab_data["tab_name"])

            self.session_file = file_path
            self._clear_unsaved_changes()
            self._log_message(f"Session loaded from {file_path}")

        except Exception as e:
            error_msg = f"Failed to load session: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Load Error", error_msg)

    def _safe_clear_layout(self, layout):
        if layout and not sip.isdeleted(layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget and not sip.isdeleted(widget):
                    widget.setParent(None)

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

    def _log_message(self, message: str, level: str = "INFO"):
        """Add message to log area and logger"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] [{level}] {message}")
        getattr(self.logger, level.lower())(message)

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
            self._clear_data()
            self.add_row_button.setVisible(False)
            self.duplicate_row_button.setVisible(False)
            self.delete_row_button.setVisible(False)
            self.load_file_button.setVisible(True)
            self._log_message("Switched to file mode")

    def _prepare_manual_table(self):
        """Prepare table for manual data entry"""
        # Clear existing tabs except summary
        while self.results_tabs.count() > 1:
            self.results_tabs.removeTab(1)

        # Create main data entry table
        main_table = self._create_results_table()
        self.results_tabs.addTab(main_table, "📝 Data Entry")

        # Add initial row
        main_table.setRowCount(1)
        self._populate_default_row(main_table, 0)

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
            6: 80,  # lower_tolerance
            7: 80,  # upper_tolerance
            8: 80,  # measurement_1
            9: 80,  # measurement_2
            10: 80,  # measurement_3
            11: 80,  # measurement_4
            12: 80,  # measurement_5
            13: 70,  # minimum
            14: 70,  # maximum
            15: 70,  # mean
            16: 70,  # std_deviation
            17: 70,  # status
        }

        for col, width in column_widths.items():
            table.setColumnWidth(col, width)

        # Connect cell changed signal
        table.cellChanged.connect(self._on_cell_changed)

        return table

    def _show_context_menu(self, table: QTableWidget, position):
        """Show context menu for table operations"""
        if not self.manual_mode:
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

    def _show_gdt_helper(self, table: QTableWidget):
        """Show GD&T helper dialog"""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row first.")
            return

        # Simple GD&T helper dialog
        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QTextEdit,
            QPushButton,
        )

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
        for col in range(13, 18):  # columns 13-17 are calculated
            item = QTableWidgetItem("")
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            item.setBackground(QColor(240, 240, 240))
            table.setItem(row, col, item)

    def _add_manual_row(self):
        """Add a new row for manual entry"""
        current_table = self.results_tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        row_count = current_table.rowCount()
        current_table.insertRow(row_count)
        self._populate_default_row(current_table, row_count)
        self._mark_unsaved_changes()

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

        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "File Load Error", error_msg)

    def _populate_table_from_dataframe(self, df: pd.DataFrame):
        """Populate table from dataframe, organizing by cavities"""
        # Clear existing tabs except summary
        while self.results_tabs.count() > 1:
            self.results_tabs.removeTab(1)

        # Group by cavity if cavity column exists
        if "cavity" in df.columns:
            cavities = sorted(df["cavity"].unique())
        else:
            cavities = [1]  # Default single cavity
            df["cavity"] = 1

        for cavity in cavities:
            cavity_df = df[df["cavity"] == cavity] if "cavity" in df.columns else df

            # Create table for this cavity
            table = self._create_results_table()
            table.setRowCount(len(cavity_df))

            # Populate table
            for row_idx, (_, row) in enumerate(cavity_df.iterrows()):
                for col_idx, col_name in enumerate(self.display_columns):
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

            # Add tab for this cavity with better naming and icons
            if len(cavities) > 1:
                tab_name = f"🔧 Cavity {cavity} ({len(cavity_df)} items)"
            else:
                tab_name = f"📋 All Data ({len(cavity_df)} items)"
            self.results_tabs.addTab(table, tab_name)

    def _on_cell_changed(self, row: int, col: int):
        """Handle cell value changes"""
        self._mark_unsaved_changes()

        current_table = self.results_tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        # If description changed, validate GD&T and format
        if col == 4:  # description column
            item = current_table.item(row, col)
            if item:
                description = item.text()
                # Format GD&T symbols
                from src.models.dimensional.gdt_interpreter import (
                    GDTInterpreter,
                )

                gdt_interpreter = GDTInterpreter()
                formatted_desc = gdt_interpreter.format_gdt_display(description)

                if formatted_desc != description:
                    item.setText(formatted_desc)

                # Validate GD&T
                gdt_info = gdt_interpreter.parse_gdt_description(formatted_desc)
                if gdt_info.get("warnings"):
                    warning_msg = "; ".join(gdt_info["warnings"])
                    self._log_message(
                        f"GD&T Warning for row {row + 1}: {warning_msg}", "WARNING"
                    )

        # If a measurement value changed, clear calculated results for this row
        if 8 <= col <= 12:  # measurement columns
            for calc_col in range(13, 18):  # clear calculated columns
                item = current_table.item(row, calc_col)
                if item:
                    item.setText("")

    def _create_summary_widget(self) -> QWidget:
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

    def _update_summary_display(self, results: List[DimensionalResult]):
        """Update the summary display with analysis results"""
        if not results:
            return

        # Get enhanced summary
        from src.services.dimensional_service import EnhancedDimensionalService

        service = EnhancedDimensionalService()
        summary = service.get_processing_summary(results)

        # Update main statistics
        stats_text = f"""
        <b>Analysis Results</b><br>
        Total Elements: {summary["total"]}<br>
        ✅ Passed: {summary["good"]} ({summary["success_rate"]:.1f}%)<br>
        ❌ Failed: {summary["bad"]}<br>
        ⚠️ Warnings: {summary["warning"]}<br>
        🔧 GD&T Features: {summary["gdt_count"]} ({summary["gdt_percentage"]:.1f}%)
        """
        self.stats_label.setText(stats_text)

        # Clear previous cavity info
        for i in reversed(range(self.cavity_layout.count())):
            self.cavity_layout.itemAt(i).widget().setParent(None)

        # Update cavity comparison
        cavity_summary = summary["cavity_summary"]
        for cavity, stats in cavity_summary.items():
            success_rate = (
                (stats["good"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            )
            cavity_label = QLabel(
                f"Cavity {cavity}: {stats['good']}/{stats['total']} passed ({success_rate:.1f}%)"
            )

            # Color code based on success rate
            if success_rate >= 95:
                color = "#4CAF50"  # Green
            elif success_rate >= 80:
                color = "#FF9800"  # Orange
            else:
                color = "#F44336"  # Red

            cavity_label.setStyleSheet(
                f"QLabel {{ color: {color}; font-weight: bold; padding: 5px; }}"
            )
            self.cavity_layout.addWidget(cavity_label)

        # Clear previous feature info
        for i in reversed(range(self.feature_layout.count())):
            self.feature_layout.itemAt(i).widget().setParent(None)

        # Update feature type breakdown
        feature_types = summary["feature_types"]
        for feature_type, count in feature_types.items():
            percentage = (count / summary["total"]) * 100
            feature_label = QLabel(
                f"{feature_type.title()}: {count} ({percentage:.1f}%)"
            )
            feature_label.setStyleSheet("QLabel { padding: 2px; }")
            self.feature_layout.addWidget(feature_label)

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

    def _update_summary_display(self, results: List[DimensionalResult]):
        """Update the summary display with analysis results"""
        if not results:
            return

        # Get enhanced summary
        from src.services.dimensional_service import EnhancedDimensionalService

        service = EnhancedDimensionalService()
        summary = service.get_processing_summary(results)

        # Update main statistics
        stats_text = f"""
        <b>Analysis Results</b><br>
        Total Elements: {summary["total"]}<br>
        ✅ Passed: {summary["good"]} ({summary["success_rate"]:.1f}%)<br>
        ❌ Failed: {summary["bad"]}<br>
        ⚠️ Warnings: {summary["warning"]}<br>
        🔧 GD&T Features: {summary["gdt_count"]} ({summary["gdt_percentage"]:.1f}%)
        """
        self.stats_label.setText(stats_text)

        # Clear previous cavity info
        for i in reversed(range(self.cavity_layout.count())):
            self.cavity_layout.itemAt(i).widget().setParent(None)

        # Update cavity comparison
        cavity_summary = summary["cavity_summary"]
        for cavity, stats in cavity_summary.items():
            success_rate = (
                (stats["good"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            )
            cavity_label = QLabel(
                f"Cavity {cavity}: {stats['good']}/{stats['total']} passed ({success_rate:.1f}%)"
            )

            # Color code based on success rate
            if success_rate >= 95:
                color = "#4CAF50"  # Green
            elif success_rate >= 80:
                color = "#FF9800"  # Orange
            else:
                color = "#F44336"  # Red

            cavity_label.setStyleSheet(
                f"QLabel {{ color: {color}; font-weight: bold; padding: 5px; }}"
            )
            self.cavity_layout.addWidget(cavity_label)

        # Clear previous feature info
        for i in reversed(range(self.feature_layout.count())):
            self.feature_layout.itemAt(i).widget().setParent(None)

        # Update feature type breakdown
        feature_types = summary["feature_types"]
        for feature_type, count in feature_types.items():
            percentage = (count / summary["total"]) * 100
            feature_label = QLabel(
                f"{feature_type.title()}: {count} ({percentage:.1f}%)"
            )
            feature_label.setStyleSheet("QLabel { padding: 2px; }")
            self.feature_layout.addWidget(feature_label)
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + " *")

    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.unsaved_changes = False
        title = self.windowTitle()
        if title.endswith(" *"):
            self.setWindowTitle(title[:-2])

    def _run_study(self):
        """Execute the dimensional study"""
        try:
            # Get dataframe from current table data
            df = self._get_dataframe_from_tables()
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

    def _get_dataframe_from_tables(self) -> pd.DataFrame:
        """Extract dataframe from all tables"""
        all_data = []

        for tab_idx in range(self.results_tabs.count()):
            table = self.results_tabs.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue

            for row in range(table.rowCount()):
                row_data = {}
                valid_row = False

                for col, col_name in enumerate(
                    self.display_columns[:13]
                ):  # Only input columns
                    item = table.item(row, col)
                    value = item.text().strip() if item and item.text() else None

                    # Check if we have essential data
                    if col_name in ["element_id", "description", "nominal"] and value:
                        valid_row = True

                    row_data[col_name] = value

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number

                # Only add rows with essential data
                if valid_row:
                    all_data.append(row_data)

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        # Convert numeric columns
        numeric_columns = [
            "nominal",
            "lower_tolerance",
            "upper_tolerance",
        ] + self.measurement_columns
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

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
        self._update_tables_with_results(results)
        self.export_button.setEnabled(True)
        self._auto_save_session()

    def _update_tables_with_results(self, results: List[DimensionalResult]):
        """Update tables with analysis results"""
        # Create a lookup dict for results
        results_dict = {(r.element_id, str(r.batch), str(r.cavity)): r for r in results}

        # Update each table
        for tab_idx in range(self.results_tabs.count()):
            table = self.results_tabs.widget(tab_idx)
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
                        col_idx = 13 + i  # Start from calculated columns
                        item = table.item(row, col_idx)
                        if not item:
                            item = QTableWidgetItem()
                            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                            table.setItem(row, col_idx, item)

                        item.setText(str(value))

                        # Color code status
                        if col_idx == 17:  # status column
                            if value == "GOOD":
                                item.setBackground(QColor(144, 238, 144))  # Light green
                            elif value == "BAD":
                                item.setBackground(QColor(255, 182, 193))  # Light red
                            else:
                                item.setBackground(
                                    QColor(255, 255, 224)
                                )  # Light yellow

    def _on_processing_error(self, error_message: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        self._log_message(f"Processing failed: {error_message}", "ERROR")
        QMessageBox.critical(
            self, "Processing Error", f"Analysis failed: {error_message}"
        )

    def _set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements during processing"""
        self.run_button.setEnabled(enabled)
        self.mode_toggle.setEnabled(enabled)
        self.add_row_button.setEnabled(enabled)
        self.duplicate_row_button.setEnabled(enabled)
        self.delete_row_button.setEnabled(enabled)
        self.load_file_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)

    def _export_results(self):
        """Export results to files"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No results available to export.")
            return

        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory"
            )
            if not export_dir:
                return

            # Generate base filename with report type
            report_type = self.report_type_combo.currentText().replace(" ", "_")
            base_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}_{report_type}_dimensional_results"

            self._log_message(f"Exporting {len(self.results)} results to {export_dir}")

            # Export using the service
            export_service = DataExportService()
            json_path, csv_path = export_service.export_results(
                self.results, export_dir, base_filename
            )

            success_msg = f"Results exported successfully:\n- JSON: {json_path}\n- CSV: {csv_path}"
            self._log_message("Export completed successfully")
            QMessageBox.information(self, "Export Successful", success_msg)

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Export Error", error_msg)

    def _save_session(self):
        """Save current session to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
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
                    "report_type": self.report_type_combo.currentText(),
                    "manual_mode": self.manual_mode,
                    "save_timestamp": datetime.now().isoformat(),
                },
                "table_data": [],
            }

            # Save data from all tables
            for tab_idx in range(self.results_tabs.count()):
                table = self.results_tabs.widget(tab_idx)
                if isinstance(table, QTableWidget):
                    tab_data = {
                        "tab_name": self.results_tabs.tabText(tab_idx),
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

            self.session_file = file_path
            self._clear_unsaved_changes()
            self._log_message(f"Session saved to {file_path}")

        except Exception as e:
            logging.debug(f"error saving: {e}")
