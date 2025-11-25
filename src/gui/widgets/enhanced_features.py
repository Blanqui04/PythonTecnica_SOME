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
    QSplitter, QTabWidget, QWidget, QTextEdit, QApplication
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
    Dialog for Dimensional template organized by Reference first, then by LOT.
    
    Workflow:
    1. Select/load reference configuration (elements, tolerances, etc.)
    2. Browse and select LOTs for that reference
    3. Apply template to selected LOT(s)
    
    Features:
    - Reference-first approach
    - LOT browser with filtering
    - Template persistence
    - Quick LOT switching
    """
    
    template_applied = pyqtSignal(dict)  # Emitted when template is applied to a LOT
    
    def __init__(self, client: str, reference: str, machine: str, 
                 available_lots: list = None, parent=None):
        super().__init__(parent)
        self.client = client
        self.reference = reference
        self.machine = machine
        self.available_lots = available_lots or []
        self.selected_lots = []
        self.template_data = None
        
        self.setWindowTitle(f"📋 Plantilla Dimensional - {reference}")
        self.setMinimumSize(900, 650)
        self._apply_styling()
        self.init_ui()
        self._load_template_data()
    
    def _apply_styling(self):
        """Apply professional styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', sans-serif;
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
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4fc;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header with reference info
        header_layout = QHBoxLayout()
        
        header_label = QLabel(f"📐 Plantilla per Referència: <b>{self.reference}</b>")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(header_label)
        
        client_label = QLabel(f"Client: {self.client}")
        client_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        header_layout.addWidget(client_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - LOT Selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        lot_group = QGroupBox("📦 Selecció de LOTs")
        lot_layout = QVBoxLayout()
        
        # Search/filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("🔍 Filtrar:"))
        self.lot_filter = QLineEdit()
        self.lot_filter.setPlaceholderText("Cercar LOT...")
        self.lot_filter.textChanged.connect(self._filter_lots)
        filter_layout.addWidget(self.lot_filter)
        lot_layout.addLayout(filter_layout)
        
        # LOT list
        self.lot_list = QListWidget()
        self.lot_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._populate_lot_list()
        lot_layout.addWidget(self.lot_list)
        
        # LOT action buttons
        lot_btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Seleccionar Tot")
        select_all_btn.clicked.connect(self._select_all_lots)
        select_all_btn.setStyleSheet("background-color: #6c757d;")
        lot_btn_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("Netejar Selecció")
        clear_btn.clicked.connect(self._clear_lot_selection)
        clear_btn.setStyleSheet("background-color: #dc3545;")
        lot_btn_layout.addWidget(clear_btn)
        
        lot_layout.addLayout(lot_btn_layout)
        lot_group.setLayout(lot_layout)
        left_layout.addWidget(lot_group)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Template preview and options
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Template info group
        template_group = QGroupBox("📋 Configuració de Plantilla")
        template_layout = QVBoxLayout()
        
        # Reference elements summary
        self.elements_label = QLabel("Elements: Carregant...")
        template_layout.addWidget(self.elements_label)
        
        # Machine selection
        machine_layout = QHBoxLayout()
        machine_layout.addWidget(QLabel("Màquina:"))
        self.machine_combo = QComboBox()
        self.machine_combo.addItems([
            'all', 'gompc_projectes', 'gompc_nou', 'hoytom', 'torsio'
        ])
        self.machine_combo.setCurrentText(self.machine)
        machine_layout.addWidget(self.machine_combo)
        machine_layout.addStretch()
        template_layout.addLayout(machine_layout)
        
        # Options
        self.copy_config_checkbox = QCheckBox("Copiar configuració d'elements (toleràncies, instruments)")
        self.copy_config_checkbox.setChecked(True)
        template_layout.addWidget(self.copy_config_checkbox)
        
        self.preserve_measurements_checkbox = QCheckBox("Preservar mesures existents al canviar de LOT")
        self.preserve_measurements_checkbox.setChecked(False)
        template_layout.addWidget(self.preserve_measurements_checkbox)
        
        template_group.setLayout(template_layout)
        right_layout.addWidget(template_group)
        
        # Preview group
        preview_group = QGroupBox("👁️ Previsualització")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels([
            "Element ID", "Descripció", "Nominal", "Tolerància", "Instrument"
        ])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # Selected LOTs summary
        self.selection_label = QLabel("LOTs seleccionats: 0")
        self.selection_label.setStyleSheet("font-weight: bold; color: #3498db;")
        right_layout.addWidget(self.selection_label)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([350, 550])
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualitzar LOTs")
        refresh_btn.clicked.connect(self._refresh_lots)
        refresh_btn.setStyleSheet("background-color: #17a2b8;")
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        apply_btn = QPushButton("✅ Aplicar Plantilla")
        apply_btn.clicked.connect(self._apply_template)
        apply_btn.setStyleSheet("background-color: #28a745; min-width: 150px;")
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("❌ Cancel·lar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #6c757d;")
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection changes
        self.lot_list.itemSelectionChanged.connect(self._update_selection_summary)
    
    def _populate_lot_list(self):
        """Populate LOT list"""
        self.lot_list.clear()
        for lot in self.available_lots:
            self.lot_list.addItem(str(lot))
    
    def _filter_lots(self, text):
        """Filter LOT list based on search text"""
        text = text.lower()
        for i in range(self.lot_list.count()):
            item = self.lot_list.item(i)
            item.setHidden(text not in item.text().lower())
    
    def _select_all_lots(self):
        """Select all visible LOTs"""
        for i in range(self.lot_list.count()):
            item = self.lot_list.item(i)
            if not item.isHidden():
                item.setSelected(True)
    
    def _clear_lot_selection(self):
        """Clear LOT selection"""
        self.lot_list.clearSelection()
    
    def _update_selection_summary(self):
        """Update selection summary label"""
        selected = self.lot_list.selectedItems()
        self.selection_label.setText(f"LOTs seleccionats: {len(selected)}")
    
    def _refresh_lots(self):
        """Refresh LOT list from database"""
        try:
            # This would normally query the database for available LOTs
            # For now, emit a signal that can be handled by the parent
            QMessageBox.information(
                self,
                "Actualització",
                "La llista de LOTs s'actualitzarà des de la base de dades."
            )
        except Exception as e:
            logger.error(f"Error refreshing LOTs: {e}")
    
    def _load_template_data(self):
        """Load template data for the reference"""
        try:
            # This would normally load from database/service
            # For now, set placeholder data
            self.elements_label.setText(
                f"Elements: Configuració carregada per {self.reference}"
            )
            
            # Populate preview table with sample data
            self.preview_table.setRowCount(3)
            sample_data = [
                ["Nº001", "Diàmetre exterior", "25.000", "±0.050", "CMM"],
                ["Nº002", "Longitud total", "100.000", "±0.100", "3D Scanbox"],
                ["Nº003", "Planitud superfície", "-", "0.020", "CMM"],
            ]
            for row, data in enumerate(sample_data):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.preview_table.setItem(row, col, item)
                    
        except Exception as e:
            logger.error(f"Error loading template data: {e}")
            self.elements_label.setText("Elements: Error al carregar")
    
    def _apply_template(self):
        """Apply template to selected LOTs"""
        selected_items = self.lot_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self,
                "Cap LOT Seleccionat",
                "Si us plau, selecciona almenys un LOT per aplicar la plantilla."
            )
            return
        
        selected_lots = [item.text() for item in selected_items]
        
        template_config = {
            'client': self.client,
            'reference': self.reference,
            'machine': self.machine_combo.currentText(),
            'lots': selected_lots,
            'copy_config': self.copy_config_checkbox.isChecked(),
            'preserve_measurements': self.preserve_measurements_checkbox.isChecked(),
            'created_at': datetime.now().isoformat()
        }
        
        self.template_applied.emit(template_config)
        
        QMessageBox.information(
            self,
            "Plantilla Aplicada",
            f"Plantilla aplicada correctament a {len(selected_lots)} LOT(s):\n" + 
            "\n".join(f"  • {lot}" for lot in selected_lots[:5]) +
            (f"\n  ... i {len(selected_lots) - 5} més" if len(selected_lots) > 5 else "")
        )
        
        self.accept()
    
    def set_available_lots(self, lots: list):
        """Update the available LOTs list"""
        self.available_lots = lots
        self._populate_lot_list()


# Export classes
__all__ = [
    'SearchHistoryManager',
    'SearchHistoryDialog',
    'MultiLOTComparisonDialog',
    'ReferenceTemplateDialog',
    'DimensionalTemplateByLotDialog'
]
