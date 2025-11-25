"""
Enhanced Features for Element Input Widget
==========================================

1. Copy/Paste Support (Ctrl+C/Ctrl+V)
2. Template for Reference → LOT analysis
3. Search History with Autocomplete
4. Multi-LOT Automatic Comparison

Author: Enhanced Features Module
Date: November 2025
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QGroupBox, QMessageBox, QLineEdit, QCheckBox,
    QSplitter, QTabWidget, QWidget, QTextEdit, QApplication,
    QFormLayout, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class SearchHistoryManager:
    """Manager for search history and autocomplete"""
    
    def __init__(self, history_file: str = None):
        if history_file is None:
            # Default location in user's data directory
            data_dir = Path.home() / ".pythontecnica" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = data_dir / "search_history.json"
        else:
            self.history_file = Path(history_file)
        
        self.history = self._load_history()
        self.max_history = 50  # Keep last 50 searches
    
    def _load_history(self) -> List[Dict]:
        """Load search history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('searches', [])
        except Exception as e:
            logger.error(f"Error loading search history: {e}")
        return []
    
    def _save_history(self):
        """Save search history to file"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'searches': self.history}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
    
    def add_search(self, client: str, reference: str, lot: str = None, machine: str = 'all'):
        """Add a search to history"""
        search_entry = {
            'client': client,
            'reference': reference,
            'lot': lot,
            'machine': machine,
            'timestamp': datetime.now().isoformat()
        }
        
        # Remove duplicates (same client + reference)
        self.history = [h for h in self.history 
                       if not (h['client'] == client and h['reference'] == reference)]
        
        # Add to beginning
        self.history.insert(0, search_entry)
        
        # Limit history size
        self.history = self.history[:self.max_history]
        
        self._save_history()
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent searches"""
        return self.history[:limit]
    
    def get_suggestions(self, query: str, field: str = 'reference') -> List[str]:
        """Get autocomplete suggestions"""
        query = query.lower()
        suggestions = set()
        
        for entry in self.history:
            value = entry.get(field, '')
            if value and query in value.lower():
                suggestions.add(value)
        
        return sorted(list(suggestions))[:10]
    
    def get_clients(self) -> List[str]:
        """Get unique clients from history"""
        clients = set(h['client'] for h in self.history if h.get('client'))
        return sorted(list(clients))
    
    def clear_history(self):
        """Clear all search history"""
        self.history = []
        self._save_history()


class SearchHistoryDialog(QDialog):
    """Dialog to show and select from search history"""
    
    search_selected = pyqtSignal(dict)
    
    def __init__(self, history_manager: SearchHistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("Search History")
        self.setMinimumSize(600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Recent Searches")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Search filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self._filter_history)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Client", "Reference", "LOT", "Machine"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        self.history_table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.history_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._select_search)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(select_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self._populate_table()
    
    def _populate_table(self, filter_text: str = ""):
        """Populate history table"""
        searches = self.history_manager.get_recent_searches(50)
        
        # Apply filter
        if filter_text:
            filter_text = filter_text.lower()
            searches = [s for s in searches if 
                       filter_text in s.get('client', '').lower() or
                       filter_text in s.get('reference', '').lower() or
                       filter_text in s.get('lot', '').lower()]
        
        self.history_table.setRowCount(len(searches))
        
        for row, search in enumerate(searches):
            # Date
            timestamp = datetime.fromisoformat(search['timestamp'])
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            self.history_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Client
            self.history_table.setItem(row, 1, QTableWidgetItem(search.get('client', '')))
            
            # Reference
            self.history_table.setItem(row, 2, QTableWidgetItem(search.get('reference', '')))
            
            # LOT
            self.history_table.setItem(row, 3, QTableWidgetItem(search.get('lot', '') or '-'))
            
            # Machine
            self.history_table.setItem(row, 4, QTableWidgetItem(search.get('machine', 'all')))
    
    def _filter_history(self, text: str):
        """Filter history based on text"""
        self._populate_table(text)
    
    def _select_search(self):
        """Select current search"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            searches = self.history_manager.get_recent_searches(50)
            if current_row < len(searches):
                self.search_selected.emit(searches[current_row])
                self.accept()
    
    def _on_double_click(self):
        """Handle double click"""
        self._select_search()
    
    def _clear_history(self):
        """Clear search history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all search history?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self._populate_table()


class MultiLOTComparisonDialog(QDialog):
    """Dialog for multi-LOT comparison"""
    
    def __init__(self, client: str, reference: str, machine: str, parent=None):
        super().__init__(parent)
        self.client = client
        self.reference = reference
        self.machine = machine
        self.lots = []
        
        self.setWindowTitle(f"Multi-LOT Comparison - {reference}")
        self.setMinimumSize(900, 600)
        self.init_ui()
        self.load_available_lots()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"Compare Multiple LOTs for {self.client} - {self.reference}")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Splitter for LOT list and results
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: LOT selection
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        lot_label = QLabel("Available LOTs:")
        lot_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(lot_label)
        
        self.lot_list = QListWidget()
        self.lot_list.setSelectionMode(QListWidget.MultiSelection)
        left_layout.addWidget(self.lot_list)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_lots)
        left_layout.addWidget(select_all_btn)
        
        compare_btn = QPushButton("Compare Selected LOTs")
        compare_btn.clicked.connect(self._compare_lots)
        left_layout.addWidget(compare_btn)
        
        splitter.addWidget(left_widget)
        
        # Right: Comparison results
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        results_label = QLabel("Comparison Results:")
        results_label.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "LOT", "Elements", "Measurements", "Avg Cp", "Avg Cpk", 
            "Min Cpk", "Status", "Date"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.results_table)
        
        # Export button
        export_btn = QPushButton("Export Comparison")
        export_btn.clicked.connect(self._export_comparison)
        right_layout.addWidget(export_btn)
        
        splitter.addWidget(right_widget)
        
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_available_lots(self):
        """Load available LOTs for the reference"""
        try:
            from src.services.measurement_history_service import MeasurementHistoryService
            
            service = MeasurementHistoryService(machine=self.machine)
            
            # Get distinct LOTs for this client and reference
            lots = service.get_distinct_lots(
                client=self.client,
                project_reference=self.reference
            )
            
            service.close()
            
            if lots:
                self.lot_list.addItems(sorted(lots))
                logger.info(f"Loaded {len(lots)} LOTs for {self.client}/{self.reference}")
            else:
                self.lot_list.addItem("No LOTs found")
                logger.warning(f"No LOTs found for {self.client}/{self.reference}")
            
        except Exception as e:
            logger.error(f"Error loading LOTs: {e}")
            QMessageBox.warning(self, "Error", f"Could not load LOTs: {e}")
    
    def _select_all_lots(self):
        """Select all LOTs in the list"""
        for i in range(self.lot_list.count()):
            self.lot_list.item(i).setSelected(True)
    
    def _compare_lots(self):
        """Compare selected LOTs with real capability calculations"""
        selected_items = self.lot_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one LOT")
            return
        
        selected_lots = [item.text() for item in selected_items]
        
        if "No LOTs found" in selected_lots:
            QMessageBox.warning(self, "Invalid Selection", "No valid LOTs to compare")
            return
        
        try:
            from src.services.measurement_history_service import MeasurementHistoryService
            from src.services.capability_calculation_service import CapabilityCalculationService
            import numpy as np
            
            # Clear previous results
            self.results_table.setRowCount(0)
            
            service = MeasurementHistoryService(machine=self.machine)
            calc_service = CapabilityCalculationService()
            
            for lot in selected_lots:
                # Get all elements for this LOT
                elements = service.get_available_elements(
                    client=self.client,
                    project_reference=self.reference,
                    lot=lot
                )
                
                if not elements:
                    continue
                
                # Calculate statistics for each element in this LOT
                lot_cps = []
                lot_cpks = []
                total_measurements = 0
                
                for element in elements:
                    # Get measurements for this element
                    measurements = service.get_measurements(
                        client=self.client,
                        project_reference=self.reference,
                        element_name=element['name'],
                        lot=lot
                    )
                    
                    if not measurements or len(measurements) < 2:
                        continue
                    
                    total_measurements += len(measurements)
                    
                    # Get tolerance for this element
                    tolerance = element.get('tolerance', 0)
                    nominal = element.get('nominal', 0)
                    
                    if tolerance > 0:
                        usl = nominal + tolerance
                        lsl = nominal - tolerance
                        
                        # Calculate Cp and Cpk
                        values = np.array(measurements)
                        mean = np.mean(values)
                        std = np.std(values, ddof=1)
                        
                        if std > 0:
                            cp = (usl - lsl) / (6 * std)
                            cpu = (usl - mean) / (3 * std)
                            cpl = (mean - lsl) / (3 * std)
                            cpk = min(cpu, cpl)
                            
                            lot_cps.append(cp)
                            lot_cpks.append(cpk)
                
                # Calculate average statistics for this LOT
                if lot_cps and lot_cpks:
                    avg_cp = np.mean(lot_cps)
                    avg_cpk = np.mean(lot_cpks)
                    min_cpk = np.min(lot_cpks)
                    
                    # Determine status
                    if min_cpk >= 1.33:
                        status = "✅ Capable"
                    elif min_cpk >= 1.0:
                        status = "⚠️ Marginal"
                    else:
                        status = "❌ Not Capable"
                    
                    # Add row to results table
                    row = self.results_table.rowCount()
                    self.results_table.insertRow(row)
                    
                    self.results_table.setItem(row, 0, QTableWidgetItem(lot))
                    self.results_table.setItem(row, 1, QTableWidgetItem(str(len(elements))))
                    self.results_table.setItem(row, 2, QTableWidgetItem(str(total_measurements)))
                    self.results_table.setItem(row, 3, QTableWidgetItem(f"{avg_cp:.3f}"))
                    self.results_table.setItem(row, 4, QTableWidgetItem(f"{avg_cpk:.3f}"))
                    self.results_table.setItem(row, 5, QTableWidgetItem(f"{min_cpk:.3f}"))
                    self.results_table.setItem(row, 6, QTableWidgetItem(status))
                    self.results_table.setItem(row, 7, QTableWidgetItem(
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
            
            service.close()
            
            if self.results_table.rowCount() == 0:
                QMessageBox.information(
                    self,
                    "No Results",
                    "No capability data found for selected LOTs"
                )
            else:
                QMessageBox.information(
                    self,
                    "Comparison Complete",
                    f"Successfully compared {self.results_table.rowCount()} LOTs"
                )
            
        except Exception as e:
            logger.error(f"Error comparing LOTs: {e}")
            QMessageBox.critical(
                self,
                "Comparison Error",
                f"Error during LOT comparison:\n{str(e)}"
            )
    
    def _export_comparison(self):
        """Export comparison results to CSV"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No comparison results to export")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            # Ask user for save location
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Comparison Results",
                f"LOT_Comparison_{self.client}_{self.reference}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not filename:
                return
            
            # Export to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                headers = []
                for col in range(self.results_table.columnCount()):
                    headers.append(self.results_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.results_table.rowCount()):
                    row_data = []
                    for col in range(self.results_table.columnCount()):
                        item = self.results_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Comparison results exported to:\n{filename}"
            )
            logger.info(f"Exported comparison results to: {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting comparison: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting results:\n{str(e)}"
            )


class ReferenceTemplateDialog(QDialog):
    """Dialog for creating reference-based templates"""
    
    template_created = pyqtSignal(dict)
    
    def __init__(self, client: str, reference: str, machine: str, parent=None):
        super().__init__(parent)
        self.client = client
        self.reference = reference
        self.machine = machine
        
        self.setWindowTitle(f"Create Template - {reference}")
        self.setMinimumSize(700, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"Dimensional Template for {self.reference}")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        info = QLabel(
            "This template will use the reference configuration and "
            "allow you to select specific LOTs for analysis."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Template configuration
        config_group = QGroupBox("Template Configuration")
        config_layout = QVBoxLayout()
        
        # Machine
        machine_layout = QHBoxLayout()
        machine_layout.addWidget(QLabel("Machine:"))
        self.machine_combo = QComboBox()
        self.machine_combo.addItems([
            'gompc_projectes', 'gompc_nou', 'hoytom', 'torsio', 'all'
        ])
        self.machine_combo.setCurrentText(self.machine)
        machine_layout.addWidget(self.machine_combo)
        machine_layout.addStretch()
        config_layout.addLayout(machine_layout)
        
        # Include all elements checkbox
        self.include_all_checkbox = QCheckBox("Include all available elements")
        self.include_all_checkbox.setChecked(True)
        config_layout.addWidget(self.include_all_checkbox)
        
        # LOT selection mode
        lot_mode_layout = QHBoxLayout()
        lot_mode_layout.addWidget(QLabel("LOT Selection:"))
        self.lot_mode_combo = QComboBox()
        self.lot_mode_combo.addItems([
            "All LOTs",
            "Select specific LOT",
            "Compare multiple LOTs"
        ])
        lot_mode_layout.addWidget(self.lot_mode_combo)
        lot_mode_layout.addStretch()
        config_layout.addLayout(lot_mode_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Template name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Template Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(f"{self.reference}_Template")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Notes
        notes_label = QLabel("Notes:")
        layout.addWidget(notes_label)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Template")
        create_btn.clicked.connect(self._create_template)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def _create_template(self):
        """Create the template"""
        template = {
            'name': self.name_input.text(),
            'client': self.client,
            'reference': self.reference,
            'machine': self.machine_combo.currentText(),
            'include_all_elements': self.include_all_checkbox.isChecked(),
            'lot_mode': self.lot_mode_combo.currentText(),
            'notes': self.notes_input.toPlainText(),
            'created_at': datetime.now().isoformat()
        }
        
        self.template_created.emit(template)
        self.accept()
        
        QMessageBox.information(
            self,
            "Template Created",
            f"Template '{template['name']}' has been created successfully!"
        )


class DimensionalTemplateByLotDialog(QDialog):
    """
    Dialog per gestionar Plantilles Dimensionals per Referència i treballar per LOT.
    
    FLUX DE TREBALL:
    ================
    1. CREAR/CARREGAR PLANTILLA BASE (per Client + Referència)
       - Defineix tots els elements dimensionals
       - Configura toleràncies, instruments, descripcions
       - Guarda la plantilla per reutilitzar-la
    
    2. SELECCIONAR LOT per treballar
       - Carrega la plantilla base
       - Escull un LOT específic
       - Treballa amb les mesures d'aquell LOT
    
    3. GUARDAR/CARREGAR ESTUDIS per LOT
       - Cada LOT pot tenir el seu propi estudi guardat
       - Les mesures es guarden per LOT
       - La plantilla base es manté igual
    
    Features:
    - Gestió de plantilles base (crear, guardar, carregar, eliminar)
    - Selecció de LOT per treballar
    - Estudis per LOT independents
    - Previsualització d'elements
    """
    
    # Signals
    template_loaded = pyqtSignal(dict)  # Emitted when a template is loaded
    lot_selected = pyqtSignal(str, dict)  # Emitted when a LOT is selected (lot_id, template_data)
    study_loaded = pyqtSignal(str, dict)  # Emitted when a study is loaded (lot_id, study_data)
    
    # Templates directory
    TEMPLATES_DIR = "data/templates/dimensional"
    STUDIES_DIR = "data/studies/dimensional"
    
    def __init__(self, client: str = "", reference: str = "", machine: str = "all",
                 current_elements: list = None, available_lots: list = None, parent=None):
        super().__init__(parent)
        self.client = client
        self.reference = reference
        self.machine = machine
        self.current_elements = current_elements or []
        self.available_lots = available_lots or []
        self.loaded_template = None
        self.current_lot = None
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.setWindowTitle("📋 Gestió de Plantilles Dimensionals per Referència i LOT")
        self.setMinimumSize(1100, 750)
        self._apply_styling()
        self.init_ui()
        self._load_saved_templates_list()
    
    def _ensure_directories(self):
        """Ensure templates and studies directories exist"""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.templates_path = os.path.join(base_path, self.TEMPLATES_DIR)
        self.studies_path = os.path.join(base_path, self.STUDIES_DIR)
        os.makedirs(self.templates_path, exist_ok=True)
        os.makedirs(self.studies_path, exist_ok=True)
    
    def _apply_styling(self):
        """Apply professional styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d6d9dc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f3f4;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8f4fc;
            }
            QLineEdit, QComboBox {
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #f1f3f4;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("📐 Gestió de Plantilles Dimensionals per Referència i LOT")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Tab widget for different sections
        self.tabs = QTabWidget()
        
        # Tab 1: Template Management (Crear/Carregar Plantilla Base)
        self.tabs.addTab(self._create_template_tab(), "📋 Plantilles Base")
        
        # Tab 2: LOT Selection and Work
        self.tabs.addTab(self._create_lot_tab(), "📦 Treballar per LOT")
        
        # Tab 3: Studies Management
        self.tabs.addTab(self._create_studies_tab(), "📊 Estudis per LOT")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("❌ Tancar")
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("background-color: #6c757d;")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_template_tab(self):
        """Create the template management tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)
        
        # Left side - Saved templates list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        saved_group = QGroupBox("💾 Plantilles Guardades")
        saved_layout = QVBoxLayout()
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("🔍"))
        self.template_filter = QLineEdit()
        self.template_filter.setPlaceholderText("Filtrar plantilles...")
        self.template_filter.textChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.template_filter)
        saved_layout.addLayout(filter_layout)
        
        # Templates list
        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self._on_template_selected)
        self.templates_list.itemDoubleClicked.connect(self._load_selected_template)
        saved_layout.addWidget(self.templates_list)
        
        # Template list buttons
        list_btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📂 Carregar")
        load_btn.clicked.connect(self._load_selected_template)
        load_btn.setStyleSheet("background-color: #28a745;")
        list_btn_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.clicked.connect(self._delete_selected_template)
        delete_btn.setStyleSheet("background-color: #dc3545;")
        list_btn_layout.addWidget(delete_btn)
        
        saved_layout.addLayout(list_btn_layout)
        saved_group.setLayout(saved_layout)
        left_layout.addWidget(saved_group)
        
        layout.addWidget(left_panel, 1)
        
        # Right side - Template editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Template info
        info_group = QGroupBox("📝 Informació de la Plantilla")
        info_layout = QFormLayout()
        
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("Nom de la plantilla...")
        info_layout.addRow("Nom:", self.template_name_edit)
        
        self.template_client_edit = QLineEdit(self.client)
        info_layout.addRow("Client:", self.template_client_edit)
        
        self.template_reference_edit = QLineEdit(self.reference)
        info_layout.addRow("Referència:", self.template_reference_edit)
        
        self.template_machine_combo = QComboBox()
        self.template_machine_combo.addItems(['all', 'gompc_projectes', 'gompc_nou', 'hoytom', 'torsio'])
        self.template_machine_combo.setCurrentText(self.machine)
        info_layout.addRow("Màquina:", self.template_machine_combo)
        
        self.template_description = QLineEdit()
        self.template_description.setPlaceholderText("Descripció opcional...")
        info_layout.addRow("Descripció:", self.template_description)
        
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        # Elements preview
        elements_group = QGroupBox("📐 Elements de la Plantilla (Configuració Actual)")
        elements_layout = QVBoxLayout()
        
        self.elements_preview_table = QTableWidget()
        self.elements_preview_table.setColumnCount(6)
        self.elements_preview_table.setHorizontalHeaderLabels([
            "ID", "Descripció", "Nominal", "Tol. Sup.", "Tol. Inf.", "Instrument"
        ])
        self.elements_preview_table.horizontalHeader().setStretchLastSection(True)
        self.elements_preview_table.setMinimumHeight(200)
        elements_layout.addWidget(self.elements_preview_table)
        
        self._populate_elements_preview()
        
        elements_label = QLabel(f"📊 Total elements: {len(self.current_elements)}")
        elements_label.setStyleSheet("color: #6c757d; font-style: italic;")
        elements_layout.addWidget(elements_label)
        
        elements_group.setLayout(elements_layout)
        right_layout.addWidget(elements_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_new_btn = QPushButton("💾 Guardar com a Nova Plantilla")
        save_new_btn.clicked.connect(self._save_new_template)
        save_new_btn.setStyleSheet("background-color: #28a745; min-width: 200px;")
        save_layout.addWidget(save_new_btn)
        
        right_layout.addLayout(save_layout)
        
        layout.addWidget(right_panel, 2)
        
        return widget
    
    def _create_lot_tab(self):
        """Create the LOT selection and work tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Current template info
        current_group = QGroupBox("📋 Plantilla Actual Carregada")
        current_layout = QHBoxLayout()
        
        self.current_template_label = QLabel("Cap plantilla carregada")
        self.current_template_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        current_layout.addWidget(self.current_template_label)
        
        current_layout.addStretch()
        
        change_template_btn = QPushButton("📂 Carregar Plantilla")
        change_template_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        change_template_btn.setStyleSheet("background-color: #17a2b8;")
        current_layout.addWidget(change_template_btn)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left - LOT list
        lot_group = QGroupBox("📦 Seleccionar LOT per Treballar")
        lot_layout = QVBoxLayout()
        
        # Filter
        lot_filter_layout = QHBoxLayout()
        lot_filter_layout.addWidget(QLabel("🔍 Filtrar:"))
        self.lot_filter = QLineEdit()
        self.lot_filter.setPlaceholderText("Cercar LOT...")
        self.lot_filter.textChanged.connect(self._filter_lots)
        lot_filter_layout.addWidget(self.lot_filter)
        lot_layout.addLayout(lot_filter_layout)
        
        # LOT list
        self.lot_list = QListWidget()
        self.lot_list.setSelectionMode(QListWidget.SingleSelection)
        self._populate_lot_list()
        lot_layout.addWidget(self.lot_list)
        
        # Manual LOT entry
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("LOT manual:"))
        self.manual_lot_edit = QLineEdit()
        self.manual_lot_edit.setPlaceholderText("Introduir LOT...")
        manual_layout.addWidget(self.manual_lot_edit)
        lot_layout.addLayout(manual_layout)
        
        lot_group.setLayout(lot_layout)
        content_layout.addWidget(lot_group, 1)
        
        # Right - Actions and info
        actions_group = QGroupBox("⚙️ Accions")
        actions_layout = QVBoxLayout()
        
        # Status
        self.lot_status_label = QLabel("Estat: Esperant selecció de LOT")
        self.lot_status_label.setStyleSheet("font-weight: bold; color: #6c757d; margin: 10px 0;")
        actions_layout.addWidget(self.lot_status_label)
        
        # Info about what will happen
        info_text = QLabel(
            "ℹ️ En seleccionar un LOT:\n"
            "• Es carregarà la plantilla base\n"
            "• Es prepararà l'estudi dimensional per aquest LOT\n"
            "• Podràs introduir les mesures específiques\n"
            "• L'estudi es podrà guardar per aquest LOT"
        )
        info_text.setStyleSheet("color: #495057; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
        info_text.setWordWrap(True)
        actions_layout.addWidget(info_text)
        
        actions_layout.addStretch()
        
        # Apply button
        self.apply_lot_btn = QPushButton("✅ Treballar amb aquest LOT")
        self.apply_lot_btn.clicked.connect(self._apply_lot_selection)
        self.apply_lot_btn.setStyleSheet("background-color: #28a745; min-width: 200px; padding: 15px;")
        self.apply_lot_btn.setEnabled(False)
        actions_layout.addWidget(self.apply_lot_btn)
        
        actions_group.setLayout(actions_layout)
        content_layout.addWidget(actions_group, 1)
        
        layout.addLayout(content_layout)
        
        # Connect signals
        self.lot_list.itemSelectionChanged.connect(self._on_lot_selected)
        self.manual_lot_edit.textChanged.connect(self._on_manual_lot_changed)
        
        return widget
    
    def _create_studies_tab(self):
        """Create the studies management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Current context
        context_group = QGroupBox("📋 Context Actual")
        context_layout = QHBoxLayout()
        
        self.studies_template_label = QLabel("Plantilla: -")
        context_layout.addWidget(self.studies_template_label)
        
        self.studies_lot_label = QLabel("LOT: -")
        context_layout.addWidget(self.studies_lot_label)
        
        context_layout.addStretch()
        context_group.setLayout(context_layout)
        layout.addWidget(context_group)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left - Saved studies list
        studies_group = QGroupBox("💾 Estudis Guardats per LOT")
        studies_layout = QVBoxLayout()
        
        # Filter
        studies_filter_layout = QHBoxLayout()
        studies_filter_layout.addWidget(QLabel("🔍"))
        self.studies_filter = QLineEdit()
        self.studies_filter.setPlaceholderText("Filtrar estudis...")
        self.studies_filter.textChanged.connect(self._filter_studies)
        studies_filter_layout.addWidget(self.studies_filter)
        studies_layout.addLayout(studies_filter_layout)
        
        # Studies list
        self.studies_list = QListWidget()
        self.studies_list.itemDoubleClicked.connect(self._load_selected_study)
        studies_layout.addWidget(self.studies_list)
        
        # Study buttons
        study_btn_layout = QHBoxLayout()
        
        load_study_btn = QPushButton("📂 Carregar Estudi")
        load_study_btn.clicked.connect(self._load_selected_study)
        load_study_btn.setStyleSheet("background-color: #28a745;")
        study_btn_layout.addWidget(load_study_btn)
        
        delete_study_btn = QPushButton("🗑️ Eliminar")
        delete_study_btn.clicked.connect(self._delete_selected_study)
        delete_study_btn.setStyleSheet("background-color: #dc3545;")
        study_btn_layout.addWidget(delete_study_btn)
        
        studies_layout.addLayout(study_btn_layout)
        studies_group.setLayout(studies_layout)
        content_layout.addWidget(studies_group, 1)
        
        # Right - Study info
        info_group = QGroupBox("📊 Informació de l'Estudi")
        info_layout = QVBoxLayout()
        
        self.study_info_text = QLabel(
            "Selecciona un estudi per veure la informació.\n\n"
            "Els estudis es guarden automàticament per:\n"
            "• Client + Referència (Plantilla)\n"
            "• LOT específic\n"
            "• Data i hora de creació"
        )
        self.study_info_text.setStyleSheet("color: #495057; padding: 15px;")
        self.study_info_text.setWordWrap(True)
        info_layout.addWidget(self.study_info_text)
        
        info_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Actualitzar Llista")
        refresh_btn.clicked.connect(self._refresh_studies_list)
        refresh_btn.setStyleSheet("background-color: #17a2b8;")
        info_layout.addWidget(refresh_btn)
        
        info_group.setLayout(info_layout)
        content_layout.addWidget(info_group, 1)
        
        layout.addLayout(content_layout)
        
        return widget
    
    def _populate_elements_preview(self):
        """Populate elements preview table with current configuration"""
        self.elements_preview_table.setRowCount(len(self.current_elements))
        
        for row, element in enumerate(self.current_elements):
            if isinstance(element, dict):
                items = [
                    element.get('element_id', f'E{row+1}'),
                    element.get('description', ''),
                    str(element.get('nominal', '')),
                    str(element.get('tolerance_upper', '')),
                    str(element.get('tolerance_lower', '')),
                    element.get('instrument', '')
                ]
            else:
                items = [str(element)] + [''] * 5
            
            for col, value in enumerate(items):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.elements_preview_table.setItem(row, col, item)
    
    def _populate_lot_list(self):
        """Populate LOT list"""
        self.lot_list.clear()
        for lot in self.available_lots:
            self.lot_list.addItem(str(lot))
    
    def _filter_templates(self, text):
        """Filter templates list"""
        text = text.lower()
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            item.setHidden(text not in item.text().lower())
    
    def _filter_lots(self, text):
        """Filter LOT list"""
        text = text.lower()
        for i in range(self.lot_list.count()):
            item = self.lot_list.item(i)
            item.setHidden(text not in item.text().lower())
    
    def _filter_studies(self, text):
        """Filter studies list"""
        text = text.lower()
        for i in range(self.studies_list.count()):
            item = self.studies_list.item(i)
            item.setHidden(text not in item.text().lower())
    
    def _load_saved_templates_list(self):
        """Load list of saved templates"""
        import os
        import glob
        
        self.templates_list.clear()
        template_files = glob.glob(os.path.join(self.templates_path, "*.json"))
        
        for template_file in sorted(template_files):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('name', os.path.basename(template_file))
                client = data.get('client', '')
                reference = data.get('reference', '')
                display = f"{name} ({client} - {reference})"
                
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, template_file)
                self.templates_list.addItem(item)
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")
    
    def _on_template_selected(self):
        """Handle template selection"""
        selected = self.templates_list.selectedItems()
        if selected:
            template_path = selected[0].data(Qt.UserRole)
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.template_name_edit.setText(data.get('name', ''))
                self.template_client_edit.setText(data.get('client', ''))
                self.template_reference_edit.setText(data.get('reference', ''))
                self.template_machine_combo.setCurrentText(data.get('machine', 'all'))
                self.template_description.setText(data.get('description', ''))
                
                # Update elements preview
                elements = data.get('elements', [])
                self.current_elements = elements
                self._populate_elements_preview()
                
            except Exception as e:
                logger.error(f"Error reading template: {e}")
    
    def _load_selected_template(self):
        """Load the selected template"""
        selected = self.templates_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Cap Selecció", "Selecciona una plantilla per carregar.")
            return
        
        template_path = selected[0].data(Qt.UserRole)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.loaded_template = json.load(f)
            
            # Update UI
            name = self.loaded_template.get('name', 'Sense nom')
            client = self.loaded_template.get('client', '')
            reference = self.loaded_template.get('reference', '')
            
            self.current_template_label.setText(
                f"✅ <b>{name}</b> (Client: {client}, Ref: {reference})"
            )
            self.current_template_label.setStyleSheet("font-size: 14px; color: #28a745;")
            
            self.studies_template_label.setText(f"Plantilla: {name}")
            
            # Enable LOT selection
            self.apply_lot_btn.setEnabled(True)
            
            # Emit signal
            self.template_loaded.emit(self.loaded_template)
            
            QMessageBox.information(
                self, 
                "Plantilla Carregada",
                f"Plantilla '{name}' carregada correctament.\n\n"
                f"Ara pots seleccionar un LOT per treballar."
            )
            
            # Switch to LOT tab
            self.tabs.setCurrentIndex(1)
            
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            QMessageBox.critical(self, "Error", f"Error carregant plantilla: {e}")
    
    def _delete_selected_template(self):
        """Delete the selected template"""
        import os
        
        selected = self.templates_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Cap Selecció", "Selecciona una plantilla per eliminar.")
            return
        
        template_path = selected[0].data(Qt.UserRole)
        template_name = selected[0].text()
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminació",
            f"Estàs segur que vols eliminar la plantilla:\n\n{template_name}?\n\n"
            "Aquesta acció no es pot desfer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(template_path)
                self._load_saved_templates_list()
                QMessageBox.information(self, "Eliminat", "Plantilla eliminada correctament.")
            except Exception as e:
                logger.error(f"Error deleting template: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminant plantilla: {e}")
    
    def _save_new_template(self):
        """Save current configuration as new template"""
        name = self.template_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom Requerit", "Introdueix un nom per la plantilla.")
            return
        
        client = self.template_client_edit.text().strip()
        reference = self.template_reference_edit.text().strip()
        
        if not client or not reference:
            QMessageBox.warning(
                self, 
                "Dades Requerides", 
                "Introdueix el client i la referència."
            )
            return
        
        # Build template data
        template_data = {
            'name': name,
            'client': client,
            'reference': reference,
            'machine': self.template_machine_combo.currentText(),
            'description': self.template_description.text().strip(),
            'elements': self.current_elements,
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Generate filename
        import re
        safe_name = re.sub(r'[^\w\-_]', '_', f"{client}_{reference}_{name}")
        filename = os.path.join(self.templates_path, f"{safe_name}.json")
        
        # Check if exists
        if os.path.exists(filename):
            reply = QMessageBox.question(
                self,
                "Plantilla Existent",
                f"Ja existeix una plantilla amb aquest nom.\nVols sobreescriure-la?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            self._load_saved_templates_list()
            
            QMessageBox.information(
                self,
                "Plantilla Guardada",
                f"Plantilla '{name}' guardada correctament.\n\n"
                f"Ubicació: {filename}"
            )
            
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            QMessageBox.critical(self, "Error", f"Error guardant plantilla: {e}")
    
    def _on_lot_selected(self):
        """Handle LOT selection from list"""
        selected = self.lot_list.selectedItems()
        if selected:
            lot = selected[0].text()
            self.manual_lot_edit.setText(lot)
            self._update_lot_status(lot)
    
    def _on_manual_lot_changed(self, text):
        """Handle manual LOT entry"""
        if text.strip():
            self._update_lot_status(text.strip())
    
    def _update_lot_status(self, lot):
        """Update LOT status display"""
        if self.loaded_template:
            self.lot_status_label.setText(f"Estat: Preparat per treballar amb LOT: {lot}")
            self.lot_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
            self.apply_lot_btn.setEnabled(True)
            self.studies_lot_label.setText(f"LOT: {lot}")
        else:
            self.lot_status_label.setText("Estat: Cal carregar una plantilla primer")
            self.lot_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
            self.apply_lot_btn.setEnabled(False)
    
    def _apply_lot_selection(self):
        """Apply the selected LOT and close dialog"""
        lot = self.manual_lot_edit.text().strip()
        
        if not lot:
            selected = self.lot_list.selectedItems()
            if selected:
                lot = selected[0].text()
        
        if not lot:
            QMessageBox.warning(self, "Cap LOT", "Selecciona o introdueix un LOT.")
            return
        
        if not self.loaded_template:
            QMessageBox.warning(self, "Cap Plantilla", "Cal carregar una plantilla primer.")
            return
        
        self.current_lot = lot
        
        # Emit signal with lot and template
        self.lot_selected.emit(lot, self.loaded_template)
        
        QMessageBox.information(
            self,
            "LOT Seleccionat",
            f"Treballant amb:\n\n"
            f"📋 Plantilla: {self.loaded_template.get('name', '-')}\n"
            f"📦 LOT: {lot}\n\n"
            "La finestra dimensional s'actualitzarà amb aquesta configuració."
        )
        
        self.accept()
    
    def _refresh_studies_list(self):
        """Refresh the list of saved studies"""
        import os
        import glob
        
        self.studies_list.clear()
        study_files = glob.glob(os.path.join(self.studies_path, "*.json"))
        
        for study_file in sorted(study_files, reverse=True):
            try:
                with open(study_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                lot = data.get('lot', '-')
                template = data.get('template_name', '-')
                date = data.get('created_at', '')[:10]
                display = f"LOT {lot} - {template} ({date})"
                
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, study_file)
                self.studies_list.addItem(item)
            except Exception as e:
                logger.error(f"Error loading study {study_file}: {e}")
    
    def _load_selected_study(self):
        """Load the selected study"""
        selected = self.studies_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Cap Selecció", "Selecciona un estudi per carregar.")
            return
        
        study_path = selected[0].data(Qt.UserRole)
        try:
            with open(study_path, 'r', encoding='utf-8') as f:
                study_data = json.load(f)
            
            lot = study_data.get('lot', '-')
            self.study_loaded.emit(lot, study_data)
            
            QMessageBox.information(
                self,
                "Estudi Carregat",
                f"Estudi del LOT {lot} carregat correctament."
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Error loading study: {e}")
            QMessageBox.critical(self, "Error", f"Error carregant estudi: {e}")
    
    def _delete_selected_study(self):
        """Delete the selected study"""
        import os
        
        selected = self.studies_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Cap Selecció", "Selecciona un estudi per eliminar.")
            return
        
        study_path = selected[0].data(Qt.UserRole)
        study_name = selected[0].text()
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminació",
            f"Estàs segur que vols eliminar l'estudi:\n\n{study_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(study_path)
                self._refresh_studies_list()
                QMessageBox.information(self, "Eliminat", "Estudi eliminat correctament.")
            except Exception as e:
                logger.error(f"Error deleting study: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminant estudi: {e}")
    
    # === PUBLIC METHODS ===
    
    def set_current_elements(self, elements: list):
        """Set the current elements configuration"""
        self.current_elements = elements
        self._populate_elements_preview()
    
    def set_available_lots(self, lots: list):
        """Update the available LOTs list"""
        self.available_lots = lots
        self._populate_lot_list()
    
    def get_loaded_template(self):
        """Get the currently loaded template"""
        return self.loaded_template
    
    def get_current_lot(self):
        """Get the currently selected LOT"""
        return self.current_lot
    
    def save_study_for_lot(self, lot: str, measurements: list, results: dict = None):
        """
        Save a study for a specific LOT.
        Call this from the dimensional window when saving.
        
        Args:
            lot: The LOT identifier
            measurements: List of measurements data
            results: Optional dict with calculated results
        """
        if not self.loaded_template:
            raise ValueError("No template loaded")
        
        import re
        
        study_data = {
            'template_name': self.loaded_template.get('name', ''),
            'template_client': self.loaded_template.get('client', ''),
            'template_reference': self.loaded_template.get('reference', ''),
            'lot': lot,
            'measurements': measurements,
            'results': results or {},
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Generate filename
        client = self.loaded_template.get('client', 'unknown')
        reference = self.loaded_template.get('reference', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = re.sub(r'[^\w\-_]', '_', f"{client}_{reference}_LOT{lot}_{timestamp}")
        filename = os.path.join(self.studies_path, f"{safe_name}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(study_data, f, indent=2, ensure_ascii=False)
        
        return filename


# Export classes
__all__ = [
    'SearchHistoryManager',
    'SearchHistoryDialog',
    'MultiLOTComparisonDialog',
    'ReferenceTemplateDialog',
    'DimensionalTemplateByLotDialog'
]
