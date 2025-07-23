# src/gui/windows/dimensional_window.
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QHBoxLayout,
    QProgressBar, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pandas as pd
import logging
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
            results = service.process_dataframe(self.df, progress_callback=self.progress_updated.emit)
            self.processing_finished.emit(results)
        except Exception as e:
            logging.error(f"Processing thread error: {str(e)}")
            self.error_occurred.emit(str(e))


class DimensionalStudyWindow(QMainWindow):
    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__()
        self.setWindowTitle("Dimensional Study")
        self.setMinimumSize(1200, 800)
        
        # Store parameters
        self.client_name = client
        self.project_ref = ref_project
        self.batch_number = batch_number
        self.results: List[DimensionalResult] = []
        self.manual_mode = False
        self.processing_thread: Optional[ProcessingThread] = None

        # Expected columns for dimensional analysis
        self.required_columns = [
            "element_id", "batch", "cavity", "description", "nominal",
            "lower_tolerance", "upper_tolerance"
        ]
        
        self.measurement_columns = [
            "measurement_1", "measurement_2", "measurement_3", "measurement_4", "measurement_5"
        ]
        
        self.all_columns = self.required_columns + self.measurement_columns

        # Setup logging
        self._setup_logging()
        self._init_ui()

    def _setup_logging(self):
        """Setup logging for the dimensional study"""
        self.logger = logging.getLogger(f"DimensionalStudy_{self.client_name}_{self.project_ref}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Header info
        header_layout = QVBoxLayout()
        header_layout.addWidget(QLabel(f"<b>Client:</b> {self.client_name}"))
        header_layout.addWidget(QLabel(f"<b>Project Ref:</b> {self.project_ref}"))
        header_layout.addWidget(QLabel(f"<b>Batch:</b> {self.batch_number}"))
        main_layout.addLayout(header_layout)

        # Mode toggle
        self.mode_toggle = QPushButton("Switch to Manual Entry")
        self.mode_toggle.clicked.connect(self._toggle_mode)
        main_layout.addWidget(self.mode_toggle)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Dimensional Study")
        self.run_button.clicked.connect(self._run_study)
        button_layout.addWidget(self.run_button)

        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self._export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)

        self.add_row_button = QPushButton("Add Row")
        self.add_row_button.clicked.connect(self._add_manual_row)
        self.add_row_button.setVisible(False)
        button_layout.addWidget(self.add_row_button)

        self.clear_button = QPushButton("Clear Data")
        self.clear_button.clicked.connect(self._clear_data)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Create splitter for table and log
        splitter = QSplitter(Qt.Vertical)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setSortingEnabled(True)
        splitter.addWidget(self.results_table)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        splitter.addWidget(self.log_area)
        
        splitter.setStretchFactor(0, 3)  # Table gets more space
        splitter.setStretchFactor(1, 1)  # Log gets less space
        
        main_layout.addWidget(splitter)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.logger.info(f"Initialized Dimensional Study for {self.client_name} - {self.project_ref} - Batch {self.batch_number}")

    def _log_message(self, message: str, level: str = "INFO"):
        """Add message to log area and logger"""
        self.log_area.append(f"[{level}] {message}")
        getattr(self.logger, level.lower())(message)

    def _toggle_mode(self):
        self.manual_mode = not self.manual_mode
        if self.manual_mode:
            self.mode_toggle.setText("Switch to File Mode")
            self._prepare_manual_table()
            self.add_row_button.setVisible(True)
            self._log_message("Switched to manual entry mode")
        else:
            self.mode_toggle.setText("Switch to Manual Entry")
            self._clear_data()
            self.add_row_button.setVisible(False)
            self._log_message("Switched to file mode")

    def _prepare_manual_table(self):
        """Prepare table for manual data entry"""
        self.results_table.clear()
        self.results_table.setColumnCount(len(self.all_columns))
        self.results_table.setHorizontalHeaderLabels(self.all_columns)
        self.results_table.setRowCount(1)
        
        # Set default batch number
        batch_item = QTableWidgetItem(str(self.batch_number))
        self.results_table.setItem(0, 1, batch_item)  # batch column

    def _add_manual_row(self):
        """Add a new row for manual entry"""
        row_count = self.results_table.rowCount()
        self.results_table.insertRow(row_count)
        
        # Set default batch number for new row
        batch_item = QTableWidgetItem(str(self.batch_number))
        self.results_table.setItem(row_count, 1, batch_item)

    def _clear_data(self):
        """Clear all data from the table"""
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.results = []
        self.export_button.setEnabled(False)
        self._log_message("Data cleared")

    def _validate_dataframe(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate the dataframe has required columns and data"""
        if df.empty:
            return False, "Dataframe is empty"

        # Check required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        # Check if we have at least some measurement columns
        measurement_cols_present = [col for col in self.measurement_columns if col in df.columns]
        if not measurement_cols_present:
            return False, "No measurement columns found"

        # Check for required data
        if df[self.required_columns].isnull().all().any():
            return False, "Required columns contain only null values"

        return True, "Validation passed"

    def _get_measurement_dataframe(self) -> pd.DataFrame:
        """Get dataframe from either manual entry or file"""
        if self.manual_mode:
            return self._get_manual_dataframe()
        else:
            return self._get_file_dataframe()

    def _get_manual_dataframe(self) -> pd.DataFrame:
        """Extract data from manual entry table"""
        try:
            data = []
            for row in range(self.results_table.rowCount()):
                row_data = {}
                valid_row = False
                
                for col, key in enumerate(self.all_columns):
                    item = self.results_table.item(row, col)
                    value = item.text().strip() if item and item.text() else None
                    
                    # Check if we have some essential data
                    if key in ["element_id", "description", "nominal"] and value:
                        valid_row = True
                    
                    row_data[key] = value

                # Auto-fill batch if empty
                if not row_data.get("batch"):
                    row_data["batch"] = self.batch_number

                # Only add rows that have some essential data
                if valid_row:
                    data.append(row_data)

            if not data:
                self._log_message("No valid data found in manual entry", "WARNING")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            
            # Convert numeric columns
            numeric_columns = ["nominal", "lower_tolerance", "upper_tolerance"] + self.measurement_columns
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            self._log_message(f"Created dataframe from manual entry with {len(df)} rows")
            return df

        except Exception as e:
            self._log_message(f"Error processing manual data: {str(e)}", "ERROR")
            return pd.DataFrame()

    def _get_file_dataframe(self) -> pd.DataFrame:
        """Load dataframe from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Measurement File", 
            "", 
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            self._log_message("No file selected", "WARNING")
            return pd.DataFrame()

        try:
            self._log_message(f"Loading file: {file_path}")
            
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
            
            self._log_message(f"Successfully loaded file with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "File Load Error", error_msg)
            return pd.DataFrame()

    def _run_study(self):
        """Execute the dimensional study"""
        try:
            # Get dataframe
            df = self._get_measurement_dataframe()
            if df.empty:
                QMessageBox.warning(self, "No Data", "No valid data found to process.")
                return

            # Validate dataframe
            is_valid, validation_msg = self._validate_dataframe(df)
            if not is_valid:
                error_msg = f"Data validation failed: {validation_msg}"
                self._log_message(error_msg, "ERROR")
                QMessageBox.critical(self, "Validation Error", error_msg)
                return

            self._log_message(f"Starting dimensional analysis on {len(df)} records")
            
            # Disable UI during processing
            self._set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Start processing in thread
            self.processing_thread = ProcessingThread(df)
            self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.processing_thread.processing_finished.connect(self._on_processing_finished)
            self.processing_thread.error_occurred.connect(self._on_processing_error)
            self.processing_thread.start()

        except Exception as e:
            error_msg = f"Error starting dimensional study: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Processing Error", error_msg)
            self._set_ui_enabled(True)

    def _on_processing_finished(self, results: List[DimensionalResult]):
        """Handle completion of processing"""
        self.results = results
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        
        if not results:
            self._log_message("No valid results generated", "WARNING")
            QMessageBox.information(self, "No Results", "No valid results were generated from the input data.")
            return

        self._log_message(f"Analysis completed successfully. Generated {len(results)} results")
        self._populate_results_table(results)
        self.export_button.setEnabled(True)

    def _on_processing_error(self, error_message: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        self._log_message(f"Processing failed: {error_message}", "ERROR")
        QMessageBox.critical(self, "Processing Error", f"Analysis failed: {error_message}")

    def _set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements during processing"""
        self.run_button.setEnabled(enabled)
        self.mode_toggle.setEnabled(enabled)
        self.add_row_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)

    def _populate_results_table(self, results: List[DimensionalResult]):
        """Populate the results table with analysis results"""
        if not results:
            return

        try:
            # Get all keys from first result
            sample_dict = results[0].to_dict()
            headers = list(sample_dict.keys())
            
            self.results_table.clear()
            self.results_table.setRowCount(len(results))
            self.results_table.setColumnCount(len(headers))
            self.results_table.setHorizontalHeaderLabels(headers)

            for row_idx, result in enumerate(results):
                result_dict = result.to_dict()
                for col_idx, key in enumerate(headers):
                    value = result_dict.get(key, "")
                    
                    # Format different data types appropriately
                    if isinstance(value, list):
                        display_value = "; ".join(str(v) for v in value)
                    elif isinstance(value, float):
                        display_value = f"{value:.4f}"
                    else:
                        display_value = str(value)
                    
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Make read-only
                    
                    # Color code based on status
                    if key == "status":
                        if value == "GOOD":
                            item.setBackground(Qt.green)
                        elif value == "BAD":
                            item.setBackground(Qt.red)
                        elif value == "WARNING":
                            item.setBackground(Qt.yellow)
                    
                    self.results_table.setItem(row_idx, col_idx, item)

            # Auto-resize columns
            self.results_table.resizeColumnsToContents()
            
            # Generate summary
            good_count = sum(1 for r in results if r.status.value == "GOOD")
            bad_count = sum(1 for r in results if r.status.value == "BAD")
            warning_count = sum(1 for r in results if r.status.value == "WARNING")
            
            summary = f"Results: {len(results)} total, {good_count} GOOD, {bad_count} BAD, {warning_count} WARNING"
            self._log_message(summary)

        except Exception as e:
            error_msg = f"Error populating results table: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Display Error", error_msg)

    def _export_results(self):
        """Export results to files"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No results available to export.")
            return

        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
            if not export_dir:
                return

            # Generate base filename
            base_filename = f"{self.client_name}_{self.project_ref}_{self.batch_number}_dimensional_results"
            
            self._log_message(f"Exporting {len(self.results)} results to {export_dir}")

            # Export using the service
            export_service = DataExportService()
            json_path, csv_path = export_service.export_results(
                self.results, 
                export_dir, 
                base_filename
            )

            success_msg = f"Results exported successfully:\n- JSON: {json_path}\n- CSV: {csv_path}"
            self._log_message("Export completed successfully")
            QMessageBox.information(self, "Export Successful", success_msg)

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self._log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "Export Error", error_msg)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, 
                "Processing in Progress", 
                "Analysis is still running. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.processing_thread.terminate()
                self.processing_thread.wait()
        
        self._log_message("Dimensional Study window closed")
        event.accept()