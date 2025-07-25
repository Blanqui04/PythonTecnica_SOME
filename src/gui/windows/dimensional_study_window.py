# src/gui/windows/dimensional_study_window.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QTabWidget,
    QFrame,
    QSplitter,
    QGroupBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPixmap, QFont
import pandas as pd
import os
from typing import List

from .base_dimensional_window import BaseDimensionalWindow
from .components.dimensional_table_manager import DimensionalTableManager
from .components.dimensional_session_manager import SessionManager
from .components.dimensional_summary_widget import SummaryWidget
from src.models.dimensional.dimensional_result import DimensionalResult
from ..workers.dimensional_processing_thread import ProcessingThread
from ..utils.styles import global_style, get_color_palette
from ..widgets.buttons import ModernButton, CompactButton  # , ActionButton


class DimensionalStudyWindow(BaseDimensionalWindow):
    """Enhanced dimensional study window with professional automotive styling"""

    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__(client, ref_project, batch_number)

        self.unsaved_changes = False
        self.manual_mode = False
        self.results = []
        self.processing_thread = None
        self._apply_professional_styling = global_style
        # Enhanced color scheme for automotive industry
        self.colors = get_color_palette

        # Initialize enhanced managers
        self._init_table_manager()
        self._init_session_manager()

        # Setup enhanced UI
        self.setWindowTitle("🔧 Dimensional Study - Professional Analysis Suite")
        self.setMinimumSize(1600, 1000)
        self._init_ui()
        self._apply_professional_styling()

        # Load last session
        QTimer.singleShot(100, self.session_manager._load_last_session)

    def _init_table_manager(self):
        """Initialize enhanced table manager"""
        self.table_manager = DimensionalTableManager(
            display_columns=[
                "element_id",
                "batch",
                "cavity",
                "class",
                "description",
                "measuring_instrument",
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
                "measuring_instrument",
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
            batch_number=self.batch_number,
        )
        self.table_manager.set_parent_window(self)

    def _init_session_manager(self):
        """Initialize session manager"""
        self.session_manager = SessionManager(
            self.client_name,
            self.project_ref,
            self.batch_number,
            log_callback=self._log_message,
            parent=self,
        )

    def _init_ui(self):
        """Initialize enhanced professional UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Enhanced header section
        header_frame = self._create_header_section()
        main_layout.addWidget(header_frame)

        # Enhanced control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Enhanced main content area with splitter
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter)

        # Enhanced status bar
        status_frame = self._create_status_section()
        main_layout.addWidget(status_frame)

        # Set main widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def _create_header_section(self) -> QFrame:
        """Create professional header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        header_frame.setFixedHeight(130)
        header_frame.setStyleSheet("background-color: #2c3e50;")  # Dark navy background

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)

        # Left: Project information
        info_group = QGroupBox("📋 Project Information")
        info_group.setStyleSheet("color: white; font-weight: bold;")
        info_layout = QGridLayout()

        # Enhanced labels with icons
        client_label = QLabel(f"🏢 <b>Client:</b> {self.client_name}")
        client_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        client_label.setStyleSheet("color: white;")

        project_label = QLabel(f"📁 <b>Project:</b> {self.project_ref}")
        project_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        project_label.setStyleSheet("color: white;")

        batch_label = QLabel(f"📦 <b>Batch:</b> {self.batch_number}")
        batch_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        batch_label.setStyleSheet("color: white;")

        info_layout.addWidget(client_label, 0, 0)
        info_layout.addWidget(project_label, 1, 0)
        info_layout.addWidget(batch_label, 2, 0)
        info_group.setLayout(info_layout)

        # Center: Report configuration
        config_group = QGroupBox("⚙️ Configuration")
        config_group.setStyleSheet("color: white")
        config_layout = QVBoxLayout()

        report_layout = QHBoxLayout()
        report_label = QLabel("📊 Report Type:")
        report_label.setStyleSheet("color: white;")
        report_layout.addWidget(report_label)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            ["PPAP", "FOT", "Intern audit", "Process validation"]
        )
        self.report_type_combo.setMinimumWidth(150)
        self.report_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #1B263B;
                color: white;
                padding: 6px 10px;
                border: 1px solid #415A77;
                border-radius: 6px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1B263B;
                selection-background-color: #415A77;
                color: white;
            }
        """)
        report_layout.addWidget(self.report_type_combo)
        report_layout.addStretch()

        config_layout.addLayout(report_layout)
        config_group.setLayout(config_layout)

        # Right: Company logo
        logo_frame = QFrame()
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        logo_label = QLabel()
        logo_path = "assets/images/gui/logo_some.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                280, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)
        else:
            # Fallback professional logo placeholder
            logo_label.setText("\U0001f3ed\nAUTOMOTIVE\nQUALITY")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("""
                QLabel {
                    background-color: #34495e;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)

        logo_layout.addWidget(logo_label)
        logo_frame.setLayout(logo_layout)

        layout.addWidget(info_group, 2)
        layout.addWidget(config_group, 2)
        layout.addWidget(logo_frame, 1)

        header_frame.setLayout(layout)
        return header_frame

    def _create_control_panel(self) -> QFrame:
        """Create enhanced control panel"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setFixedHeight(100)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)

        # Mode control group
        mode_group = QGroupBox("📝 Input Mode")
        mode_layout = QHBoxLayout()

        self.mode_toggle = ModernButton("🔄 Switch to Manual Entry")
        self.mode_toggle.setMinimumSize(180, 40)
        self.mode_toggle.clicked.connect(self._toggle_mode)

        self.load_file_button = ModernButton("📁 Load Data File")
        self.load_file_button.setMinimumSize(140, 40)
        self.load_file_button.clicked.connect(self.session_manager._load_file)

        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addWidget(self.load_file_button)
        mode_group.setLayout(mode_layout)

        # Manual mode controls (initially hidden)
        manual_group = QGroupBox("✏️ Manual Controls")
        manual_layout = QHBoxLayout()

        self.add_row_button = CompactButton("➕ Add Row")
        self.duplicate_row_button = CompactButton("📋 Duplicate")
        self.delete_row_button = CompactButton("🗑️ Delete")

        for btn in [
            self.add_row_button,
            self.duplicate_row_button,
            self.delete_row_button,
        ]:
            btn.setMinimumSize(100, 40)
            btn.setVisible(False)

        self.add_row_button.clicked.connect(self._add_manual_row)
        self.duplicate_row_button.clicked.connect(self._duplicate_row)
        self.delete_row_button.clicked.connect(self._delete_row)

        manual_layout.addWidget(self.add_row_button)
        manual_layout.addWidget(self.duplicate_row_button)
        manual_layout.addWidget(self.delete_row_button)
        manual_group.setLayout(manual_layout)

        # Analysis controls
        analysis_group = QGroupBox("🔬 Analysis")
        analysis_layout = QHBoxLayout()

        self.run_study_button = ModernButton(
            "\U0001f680 Run Dimensional Study", primary=True
        )
        self.run_study_button.setMinimumSize(170, 40)
        self.run_study_button.setEnabled(False)
        self.run_study_button.clicked.connect(self._run_study)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(25)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("🔄 Processing...")

        analysis_layout.addWidget(self.run_study_button)
        analysis_layout.addWidget(self.progress_bar)
        analysis_group.setLayout(analysis_layout)

        # Session controls
        session_group = QGroupBox("💾 Session")
        session_layout = QHBoxLayout()

        self.save_button = ModernButton("💾 Save")
        self.save_button.setMinimumSize(80, 40)
        self.save_button.clicked.connect(self.session_manager._save_session)
        session_layout.addWidget(self.save_button)

        self.load_button = ModernButton("📂 Load")
        self.load_button.setMinimumSize(80, 40)
        self.load_button.clicked.connect(self.session_manager._load_session)
        session_layout.addWidget(self.load_button)

        self.export_button = ModernButton("📤 Export")
        self.export_button.setMinimumSize(80, 40)
        self.export_button.clicked.connect(self.session_manager._export_data)
        session_layout.addWidget(self.export_button)

        self.clear_button = ModernButton("🧹 Clear")
        self.clear_button.setMinimumSize(80, 40)
        self.clear_button.clicked.connect(self._clear_all)
        session_layout.addWidget(self.clear_button)

        session_group.setLayout(session_layout)

        layout.addWidget(mode_group)
        layout.addWidget(manual_group)
        layout.addWidget(analysis_group)
        layout.addWidget(session_group)
        layout.addStretch()

        control_frame.setLayout(layout)
        return control_frame

    def _create_content_area(self) -> QSplitter:
        """Create enhanced content area with splitter"""
        splitter = QSplitter(Qt.Vertical)

        # Enhanced results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabsClosable(True)
        self.results_tabs.tabCloseRequested.connect(self._remove_tab)
        self.results_tabs.setMinimumHeight(400)

        # Add summary tab by default
        summary_widget = self.table_manager._create_summary_widget()
        self.results_tabs.addTab(summary_widget, "📊 Summary")

        splitter.addWidget(self.results_tabs)

        # Enhanced log area
        log_frame = QFrame()
        log_frame.setFrameStyle(QFrame.StyledPanel)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(10, 5, 10, 10)

        log_header = QLabel("📋 Activity Log")
        log_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        log_header.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setFont(QFont("Consolas", 9))

        log_layout.addWidget(log_header)
        log_layout.addWidget(self.log_area)
        log_frame.setLayout(log_layout)

        splitter.addWidget(log_frame)
        splitter.setSizes([700, 150])

        return splitter

    def _create_status_section(self) -> QFrame:
        """Create enhanced status section"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setFixedHeight(40)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)

        self.status_label = QLabel("✅ Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))

        self.stats_label = QLabel("📊 No data loaded")
        self.stats_label.setFont(QFont("Segoe UI", 9))

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.stats_label)

        status_frame.setLayout(layout)
        return status_frame

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
        self.export_button.setEnabled(True)
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
        if current_row == -1:
            QMessageBox.information(
                self, "No Selection", "Please select a row to duplicate."
            )
            return

        # Copy data from the selected row
        row_data = [
            current_table.item(current_row, col).text()
            if current_table.item(current_row, col)
            else ""
            for col in range(current_table.columnCount())
        ]

        # Insert new row
        new_row = current_table.rowCount()
        current_table.insertRow(new_row)

        for col, text in enumerate(row_data):
            item = QTableWidgetItem(text)
            current_table.setItem(new_row, col, item)

        # Generate a new Element ID
        current_table.setItem(
            new_row,
            0,
            QTableWidgetItem(self.table_manager._get_next_element_id(current_table)),
        )

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
        # self.save_session_button.setEnabled(enabled)
        # self.load_session_button.setEnabled(enabled)
