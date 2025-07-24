"""
Finestra d'edició de base de dades

Permet veure, editar i manipular les taules de la base de dades de forma visual.
"""

import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QPushButton, QComboBox, QLabel, QMessageBox,
    QSplitter, QTextEdit, QGroupBox, QSpinBox, QCheckBox,
    QHeaderView, QProgressBar, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DatabaseLoadWorker(QThread):
    """Worker thread per carregar dades de la base de dades"""
    
    data_loaded = pyqtSignal(str, pd.DataFrame)  # table_name, dataframe
    error_occurred = pyqtSignal(str)
    finished_loading = pyqtSignal()
    
    def __init__(self, table_name, db_adapter, limit=None):
        super().__init__()
        self.table_name = table_name
        self.db_adapter = db_adapter
        self.limit = limit
    
    def run(self):
        try:
            # Carregar dades de la taula
            if self.limit:
                query = f"SELECT * FROM {self.table_name} LIMIT {self.limit}"
            else:
                query = f"SELECT * FROM {self.table_name}"
                
            df = self.db_adapter.execute_query_to_dataframe(query)
            self.data_loaded.emit(self.table_name, df)
        except Exception as e:
            self.error_occurred.emit(f"Error carregant taula {self.table_name}: {str(e)}")
        finally:
            self.finished_loading.emit()


class DatabaseEditor(QDialog):
    """Finestra principal d'edició de base de dades"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Base de Dades")
        self.setMinimumSize(1200, 800)
        
        # Variables
        self.db_adapter = None
        self.current_table = None
        self.current_dataframe = None
        self.modified_rows = set()
        
        self.init_ui()
        self.load_database_connection()
        
    def init_ui(self):
        """Inicialitza la interfície d'usuari"""
        layout = QVBoxLayout()
        
        # Header amb controls principals
        header_layout = QHBoxLayout()
        
        # Selector de taula
        self.table_combo = QComboBox()
        self.table_combo.currentTextChanged.connect(self.on_table_changed)
        header_layout.addWidget(QLabel("Taula:"))
        header_layout.addWidget(self.table_combo)
        
        # Botó de refresc
        self.refresh_btn = QPushButton("🔄 Refrescar")
        self.refresh_btn.clicked.connect(self.refresh_current_table)
        header_layout.addWidget(self.refresh_btn)
        
        # Estadístiques
        self.stats_label = QLabel("Files: 0 | Columnes: 0")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Barra de progrés
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)
        
        layout.addLayout(header_layout)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Vertical)
        
        # Taula principal
        self.table_widget = QTableWidget()
        self.table_widget.itemChanged.connect(self.on_item_changed)
        self.table_widget.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        main_splitter.addWidget(self.table_widget)
        
        # Panel inferior amb operacions
        bottom_panel = self.create_bottom_panel()
        main_splitter.addWidget(bottom_panel)
        
        # Configurar proporcions del splitter
        main_splitter.setSizes([600, 200])
        
        layout.addWidget(main_splitter)
        
        # Botons d'acció
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Guardar Canvis")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        self.add_row_btn = QPushButton("➕ Afegir Fila")
        self.add_row_btn.clicked.connect(self.add_new_row)
        buttons_layout.addWidget(self.add_row_btn)
        
        self.delete_row_btn = QPushButton("❌ Eliminar Fila")
        self.delete_row_btn.clicked.connect(self.delete_selected_rows)
        buttons_layout.addWidget(self.delete_row_btn)
        
        self.export_btn = QPushButton("📤 Exportar CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(self.export_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("❌ Tancar")
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def create_bottom_panel(self):
        """Crea el panel inferior amb informació i operacions"""
        widget = QGroupBox("Informació i Operacions")
        layout = QHBoxLayout()
        
        # Panel d'informació
        info_group = QGroupBox("Informació de la Taula")
        info_layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        info_group.setLayout(info_layout)
        
        # Panel d'operacions
        ops_group = QGroupBox("Operacions SQL")
        ops_layout = QVBoxLayout()
        
        # Query personalitzada
        query_layout = QHBoxLayout()
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("SELECT * FROM taula WHERE...")
        query_layout.addWidget(self.query_edit)
        
        self.execute_query_btn = QPushButton("▶️ Executar")
        self.execute_query_btn.clicked.connect(self.execute_custom_query)
        query_layout.addWidget(self.execute_query_btn)
        
        ops_layout.addLayout(query_layout)
        
        # Filtres ràpids
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Límit de files:"))
        
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(10, 10000)
        self.limit_spinbox.setValue(1000)
        self.limit_spinbox.valueChanged.connect(self.refresh_current_table)
        filter_layout.addWidget(self.limit_spinbox)
        
        self.show_all_checkbox = QCheckBox("Mostrar totes les files")
        self.show_all_checkbox.stateChanged.connect(self.on_show_all_changed)
        filter_layout.addWidget(self.show_all_checkbox)
        
        ops_layout.addLayout(filter_layout)
        ops_group.setLayout(ops_layout)
        
        layout.addWidget(info_group)
        layout.addWidget(ops_group)
        
        widget.setLayout(layout)
        return widget
    
    def load_database_connection(self):
        """Carrega la connexió a la base de dades"""
        try:
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            from src.services.network_scanner import NetworkScanner
            
            # Carregar configuració de la base de dades
            scanner = NetworkScanner()
            db_config = scanner.load_db_config()
            
            if not db_config:
                raise Exception("No s'ha pogut carregar la configuració de la base de dades")
            
            # Crear adaptador
            self.db_adapter = QualityMeasurementDBAdapter(db_config)
            
            if not self.db_adapter.connect():
                raise Exception("No s'ha pogut connectar a la base de dades")
            
            # Carregar llista de taules
            self.load_tables_list()
            
            self.info_text.append(f"✅ Connectat a la base de dades: {db_config['host']}:{db_config['port']}")
            logger.info("Connexió a la base de dades establerta correctament")
            
        except Exception as e:
            error_msg = f"Error connectant a la base de dades: {str(e)}"
            self.info_text.append(f"❌ {error_msg}")
            logger.error(error_msg)
            QMessageBox.critical(self, "Error de Connexió", error_msg)
    
    def load_tables_list(self):
        """Carrega la llista de taules disponibles"""
        try:
            # Query per obtenir taules
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
            
            result = self.db_adapter.execute_query(query)
            
            tables = [row[0] for row in result] if result else []
            
            self.table_combo.clear()
            self.table_combo.addItems(tables)
            
            self.info_text.append(f"📋 Taules trobades: {len(tables)}")
            
            if tables:
                self.table_combo.setCurrentText(tables[0])
            
        except Exception as e:
            error_msg = f"Error carregant llista de taules: {str(e)}"
            self.info_text.append(f"❌ {error_msg}")
            logger.error(error_msg)
    
    def on_table_changed(self, table_name):
        """Quan canvia la taula seleccionada"""
        if not table_name:
            return
            
        self.current_table = table_name
        self.load_table_data(table_name)
    
    def load_table_data(self, table_name):
        """Carrega les dades d'una taula"""
        if not self.db_adapter or not table_name:
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Mode indeterminat
            
            # Determinar límit
            if self.show_all_checkbox.isChecked():
                limit = None
            else:
                limit = self.limit_spinbox.value()
            
            # Modificar el worker per acceptar límit
            self.load_worker = DatabaseLoadWorker(table_name, self.db_adapter, limit)
            self.load_worker.data_loaded.connect(self.on_data_loaded)
            self.load_worker.error_occurred.connect(self.on_load_error)
            self.load_worker.finished_loading.connect(self.on_load_finished)
            self.load_worker.start()
            
        except Exception as e:
            self.on_load_error(f"Error iniciant càrrega: {str(e)}")
    
    def on_data_loaded(self, table_name, dataframe):
        """Quan les dades s'han carregat correctament"""
        self.current_dataframe = dataframe
        self.populate_table_widget(dataframe)
        self.update_stats(dataframe)
        self.modified_rows.clear()
        self.save_btn.setEnabled(False)
        
        # Actualitzar informació de la taula
        self.info_text.append(f"✅ Taula '{table_name}' carregada: {len(dataframe)} files")
        
        # Mostrar informació sobre les columnes
        if not dataframe.empty:
            self.info_text.append(f"📋 Columnes: {', '.join(dataframe.columns.tolist())}")
            
            # Detectar possibles claus primàries
            potential_keys = []
            for col in dataframe.columns:
                if 'id' in col.lower() or col.lower() in ['pk', 'key', 'primary_key']:
                    potential_keys.append(col)
            
            if potential_keys:
                self.info_text.append(f"🔑 Possibles claus primàries detectades: {', '.join(potential_keys)}")
            else:
                self.info_text.append(f"⚠️ No s'han detectat claus primàries obvies. S'usarà la primera columna: '{dataframe.columns[0]}'")
    
    def on_load_error(self, error_message):
        """Quan hi ha un error carregant dades"""
        self.info_text.append(f"❌ {error_message}")
        logger.error(error_message)
        QMessageBox.warning(self, "Error de Càrrega", error_message)
    
    def on_load_finished(self):
        """Quan acaba la càrrega (amb èxit o error)"""
        self.progress_bar.setVisible(False)
    
    def populate_table_widget(self, dataframe):
        """Omple el widget de taula amb les dades del DataFrame"""
        self.table_widget.clear()
        
        if dataframe.empty:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            return
        
        # Configurar files i columnes
        self.table_widget.setRowCount(len(dataframe))
        self.table_widget.setColumnCount(len(dataframe.columns))
        
        # Headers
        self.table_widget.setHorizontalHeaderLabels(dataframe.columns.tolist())
        
        # Emplenar dades
        for row in range(len(dataframe)):
            for col in range(len(dataframe.columns)):
                value = dataframe.iloc[row, col]
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                self.table_widget.setItem(row, col, item)
        
        # Ajustar columnes
        self.table_widget.resizeColumnsToContents()
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(True)
    
    def update_stats(self, dataframe):
        """Actualitza les estadístiques"""
        rows = len(dataframe)
        cols = len(dataframe.columns) if not dataframe.empty else 0
        self.stats_label.setText(f"Files: {rows:,} | Columnes: {cols}")
    
    def on_item_changed(self, item):
        """Quan un element de la taula canvia"""
        row = item.row()
        self.modified_rows.add(row)
        self.save_btn.setEnabled(True)
        
        # Determinar si és una fila nova o modificada
        is_new_row = row >= len(self.current_dataframe) if self.current_dataframe is not None else True
        
        # Marcar la fila com modificada amb colors diferents
        for col in range(self.table_widget.columnCount()):
            cell_item = self.table_widget.item(row, col)
            if cell_item:
                if is_new_row:
                    # Files noves en verd clar
                    cell_item.setBackground(Qt.green if hasattr(Qt, 'green') else Qt.lightGray)
                else:
                    # Files modificades en groc
                    cell_item.setBackground(Qt.yellow)
    
    def on_header_clicked(self, logical_index):
        """Quan es clica en un header de columna"""
        column_name = self.table_widget.horizontalHeaderItem(logical_index).text()
        self.info_text.append(f"📊 Columna seleccionada: {column_name}")
    
    def refresh_current_table(self):
        """Refresca la taula actual"""
        if self.current_table:
            self.load_table_data(self.current_table)
    
    def save_changes(self):
        """Guarda els canvis a la base de dades"""
        if not self.modified_rows or not self.current_table or self.current_dataframe is None:
            return
        
        try:
            reply = QMessageBox.question(
                self, 
                "Confirmar Canvis",
                f"Vols guardar {len(self.modified_rows)} files modificades?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            success_count = 0
            error_count = 0
            
            # Processar cada fila modificada
            for row in self.modified_rows:
                try:
                    # Detectar la clau primària de forma intel·ligent
                    primary_key_column, primary_key_value = self._get_primary_key_for_row(row)
                    
                    # Verificar si és una fila nova (fora del rang del DataFrame original)
                    is_new_row = row >= len(self.current_dataframe)
                    
                    if not primary_key_column or not primary_key_value:
                        if is_new_row:
                            # Nova fila sense clau primària - necessita inserció
                            self.info_text.append(f"➕ Fila {row + 1}: Preparant per inserció (nova fila)")
                            # Recopilar dades per inserció
                            new_record = self._collect_row_data(row)
                            if self._insert_new_record(new_record):
                                success_count += 1
                                self.info_text.append(f"✅ Nova fila {row + 1} inserida correctament")
                            else:
                                error_count += 1
                                self.info_text.append(f"❌ Error inserint nova fila {row + 1}")
                        else:
                            # Fila existent sense clau primària identificable
                            self.info_text.append(f"⚠️ Fila {row + 1}: No es pot identificar la clau primària")
                            error_count += 1
                        continue
                    
                    # Recopilar canvis per files existents
                    updates = {}
                    for col in range(self.table_widget.columnCount()):
                        header_item = self.table_widget.horizontalHeaderItem(col)
                        if header_item:
                            column_name = header_item.text()
                            cell_item = self.table_widget.item(row, col)
                            if cell_item:
                                new_value = cell_item.text()
                                
                                # Comparar amb valor original només si no és una fila nova
                                if is_new_row:
                                    # Per files noves, afegir tots els valors no buits
                                    if new_value.strip():
                                        converted_value = self._smart_type_conversion(new_value, column_name)
                                        updates[column_name] = converted_value
                                else:
                                    # Per files existents, comparar amb l'original
                                    original_value = str(self.current_dataframe.iloc[row, col]) if pd.notna(self.current_dataframe.iloc[row, col]) else ""
                                    if new_value != original_value:
                                        converted_value = self._smart_type_conversion(new_value, column_name)
                                        updates[column_name] = converted_value
                    
                    # Actualitzar registre si hi ha canvis
                    if updates:
                        if self.db_adapter.update_record_by_key(self.current_table, primary_key_column, primary_key_value, updates):
                            success_count += 1
                            self.info_text.append(f"✅ Fila {row + 1} ({primary_key_column}: {primary_key_value}) actualitzada")
                        else:
                            error_count += 1
                            self.info_text.append(f"❌ Error actualitzant fila {row + 1} ({primary_key_column}: {primary_key_value})")
                    else:
                        self.info_text.append(f"ℹ️ Fila {row + 1}: No hi ha canvis reals per guardar")
                    
                except Exception as e:
                    error_count += 1
                    self.info_text.append(f"❌ Error processant fila {row + 1}: {str(e)}")
            
            # Resultat final
            if success_count > 0:
                self.info_text.append(f"💾 {success_count} files guardades correctament")
            
            if error_count > 0:
                self.info_text.append(f"⚠️ {error_count} files amb errors")
            
            # Resetejar modificacions si tot ha anat bé
            if error_count == 0:
                self.modified_rows.clear()
                self.save_btn.setEnabled(False)
                
                # Eliminar colors de fons
                for row in range(self.table_widget.rowCount()):
                    for col in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, col)
                        if item:
                            item.setBackground(Qt.white)
                
                # Refrescar dades
                self.refresh_current_table()
                
                QMessageBox.information(self, "Guardat", f"Canvis guardats correctament!\n{success_count} files actualitzades")
            else:
                QMessageBox.warning(self, "Guardat Parcial", f"Guardat amb errors:\n✅ {success_count} èxits\n❌ {error_count} errors")
            
        except Exception as e:
            error_msg = f"Error guardant canvis: {str(e)}"
            self.info_text.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Error de Guardat", error_msg)
    
    def _smart_type_conversion(self, value, column_name):
        """
        Converteix un valor al tipus de dada apropiat per la base de dades
        
        Args:
            value: Valor a convertir
            column_name: Nom de la columna (per context)
            
        Returns:
            Valor convertit al tipus apropiat
        """
        if not value or value.strip() == "":
            return None
        
        value_str = value.strip()
        
        # Intentar convertir a número si sembla un número
        if value_str.replace('.', '').replace('-', '').replace('+', '').isdigit():
            try:
                # Si conté punt decimal, és un float
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            except ValueError:
                pass
        
        # Si el nom de columna suggereix una data
        if any(date_keyword in column_name.lower() for date_keyword in ['data', 'date', 'time', 'hora']):
            # Mantenir com a string per ara, la BD ho convertirà si és necessari
            return value_str
        
        # Si el nom de columna suggereix un booleà
        if any(bool_keyword in column_name.lower() for bool_keyword in ['active', 'enabled', 'valid', 'actiu']):
            if value_str.lower() in ['true', 't', '1', 'yes', 'sí', 'si']:
                return True
            elif value_str.lower() in ['false', 'f', '0', 'no']:
                return False
        
        # Per defecte, retornar com a string
        return value_str
    
    def _collect_row_data(self, row):
        """
        Recopila totes les dades d'una fila per inserció
        
        Args:
            row: Número de fila
            
        Returns:
            dict: Diccionari amb dades de la fila
        """
        row_data = {}
        
        for col in range(self.table_widget.columnCount()):
            header_item = self.table_widget.horizontalHeaderItem(col)
            if header_item:
                column_name = header_item.text()
                cell_item = self.table_widget.item(row, col)
                if cell_item and cell_item.text().strip():
                    value = cell_item.text().strip()
                    converted_value = self._smart_type_conversion(value, column_name)
                    row_data[column_name] = converted_value
                else:
                    row_data[column_name] = None
        
        return row_data
    
    def _insert_new_record(self, record_data):
        """
        Insereix un nou registre a la base de dades
        
        Args:
            record_data: Diccionari amb les dades del registre
            
        Returns:
            bool: True si s'ha inserit correctament
        """
        try:
            if not record_data or not self.current_table:
                return False
            
            # Filtrar valors None i buits
            filtered_data = {k: v for k, v in record_data.items() if v is not None}
            
            if not filtered_data:
                self.info_text.append("⚠️ No hi ha dades per inserir")
                return False
            
            # Construir query INSERT
            columns = list(filtered_data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(filtered_data.values())
            
            # Posar cometes als noms de columnes per evitar conflictes amb paraules reservades
            quoted_columns = [f'"{col}"' for col in columns]
            
            query = f"""
            INSERT INTO "{self.current_table}" ({', '.join(quoted_columns)})
            VALUES ({', '.join(placeholders)})
            """
            
            # Executar la inserció
            result = self.db_adapter.execute_query(query, tuple(values))
            
            if isinstance(result, int) and result > 0:
                self.info_text.append(f"✅ Nou registre inserit amb {len(filtered_data)} columnes")
                return True
            else:
                self.info_text.append(f"❌ Error en la inserció: resultat {result}")
                return False
                
        except Exception as e:
            self.info_text.append(f"❌ Error inserint registre: {str(e)}")
            logger.error(f"Error inserint registre: {e}")
            return False
    
    def _get_primary_key_for_row(self, row):
        """
        Detecta la clau primària per una fila específica
        
        Args:
            row: Número de fila
            
        Returns:
            tuple: (column_name, column_value) o (None, None) si no es troba
        """
        try:
            # Llista de possibles noms de clau primària en ordre de prioritat
            primary_key_candidates = ['id', 'ID', 'pk', 'primary_key', 'key']
            
            # Primer, provar amb columnes que continguin 'id' al nom
            for col in range(self.table_widget.columnCount()):
                header_item = self.table_widget.horizontalHeaderItem(col)
                if header_item:
                    column_name = header_item.text().lower()
                    
                    # Comprovar noms exactes de clau primària
                    if column_name in [pk.lower() for pk in primary_key_candidates]:
                        cell_item = self.table_widget.item(row, col)
                        if cell_item and cell_item.text():
                            return header_item.text(), cell_item.text()
            
            # Segon, provar amb columnes que continguin 'id' en el nom
            for col in range(self.table_widget.columnCount()):
                header_item = self.table_widget.horizontalHeaderItem(col)
                if header_item:
                    column_name = header_item.text().lower()
                    
                    if 'id' in column_name and column_name != 'acid':  # Evitar falsos positius
                        cell_item = self.table_widget.item(row, col)
                        if cell_item and cell_item.text():
                            return header_item.text(), cell_item.text()
            
            # Tercer, usar la primera columna com a clau primària per defecte
            if self.table_widget.columnCount() > 0:
                header_item = self.table_widget.horizontalHeaderItem(0)
                cell_item = self.table_widget.item(row, 0)
                if header_item and cell_item and cell_item.text():
                    return header_item.text(), cell_item.text()
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error detectant clau primària per fila {row}: {e}")
            return None, None
    
    def add_new_row(self):
        """Afegeix una nova fila buida"""
        if self.current_dataframe is None:
            QMessageBox.information(self, "No hi ha dades", "Primer carrega una taula per afegir files")
            return
        
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)
        
        # Afegir elements buits amb color distintiu per files noves
        for col in range(self.table_widget.columnCount()):
            item = QTableWidgetItem("")
            # Marcar visualmente com a fila nova (color verd clar)
            item.setBackground(Qt.green if hasattr(Qt, 'green') else Qt.lightGray)
            self.table_widget.setItem(row_count, col, item)
        
        self.modified_rows.add(row_count)
        self.save_btn.setEnabled(True)
        
        self.info_text.append(f"➕ Nova fila afegida a la posició {row_count + 1} (marcada en verd)")
        self.info_text.append(f"💡 Consell: Omple almenys una clau primària abans de guardar")
    
    def delete_selected_rows(self):
        """Elimina les files seleccionades de la base de dades"""
        selected_rows = set()
        for item in self.table_widget.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "Selecció", "Selecciona les files a eliminar")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminació",
            f"Vols eliminar {len(selected_rows)} files seleccionades DE LA BASE DE DADES?\n\n⚠️ AQUESTA ACCIÓ NO ES POT DESFER!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            
            # Eliminar cada fila de la base de dades
            for row in selected_rows:
                try:
                    # Detectar clau primària per aquesta fila
                    primary_key_column, primary_key_value = self._get_primary_key_for_row(row)
                    
                    if primary_key_column and primary_key_value:
                        if self.db_adapter.delete_record_by_key(self.current_table, primary_key_column, primary_key_value):
                            success_count += 1
                            self.info_text.append(f"🗑️ Fila {row + 1} eliminada ({primary_key_column}: {primary_key_value})")
                        else:
                            error_count += 1
                            self.info_text.append(f"❌ Error eliminant fila {row + 1} ({primary_key_column}: {primary_key_value})")
                    else:
                        error_count += 1
                        self.info_text.append(f"❌ No es pot identificar la clau primària per la fila {row + 1}")
                        
                except Exception as e:
                    error_count += 1
                    self.info_text.append(f"❌ Error eliminant fila {row + 1}: {str(e)}")
            
            # Resum de l'operació
            if success_count > 0:
                self.info_text.append(f"✅ {success_count} files eliminades correctament")
            
            if error_count > 0:
                self.info_text.append(f"⚠️ {error_count} files amb errors")
            
            # Refrescar dades després de l'eliminació
            if success_count > 0:
                self.refresh_current_table()
                QMessageBox.information(self, "Eliminació", f"Eliminació completada:\n✅ {success_count} èxits\n❌ {error_count} errors")
            elif error_count > 0:
                QMessageBox.warning(self, "Errors d'Eliminació", f"Hi ha hagut errors eliminant {error_count} files")
        
        else:
            self.info_text.append("🚫 Eliminació cancel·lada per l'usuari")
    
    def export_to_csv(self):
        """Exporta les dades actuals a CSV"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            QMessageBox.information(self, "Exportació", "No hi ha dades per exportar")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a CSV",
            f"{self.current_table}.csv",
            "CSV files (*.csv)"
        )
        
        if filename:
            try:
                self.current_dataframe.to_csv(filename, index=False)
                self.info_text.append(f"📤 Dades exportades a: {filename}")
                QMessageBox.information(self, "Exportació", f"Dades exportades correctament a:\n{filename}")
            except Exception as e:
                error_msg = f"Error exportant: {str(e)}"
                self.info_text.append(f"❌ {error_msg}")
                QMessageBox.critical(self, "Error d'Exportació", error_msg)
    
    def execute_custom_query(self):
        """Executa una query personalitzada"""
        query = self.query_edit.text().strip()
        if not query:
            return
        
        try:
            self.info_text.append(f"🔍 Executant query: {query}")
            
            if query.upper().startswith('SELECT'):
                # Query de selecció
                df = self.db_adapter.execute_query_to_dataframe(query)
                self.current_dataframe = df
                self.populate_table_widget(df)
                self.update_stats(df)
                self.info_text.append(f"✅ Query executada: {len(df)} files retornades")
            else:
                # Query de modificació
                result = self.db_adapter.execute_query(query)
                self.info_text.append(f"✅ Query executada: {result}")
                self.refresh_current_table()  # Refrescar dades
            
        except Exception as e:
            error_msg = f"Error executant query: {str(e)}"
            self.info_text.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Error de Query", error_msg)
    
    def on_show_all_changed(self, state):
        """Quan canvia el checkbox de mostrar totes les files"""
        if state == Qt.Checked:
            self.limit_spinbox.setEnabled(False)
        else:
            self.limit_spinbox.setEnabled(True)
        
        self.refresh_current_table()
    
    def closeEvent(self, event):
        """Quan es tanca la finestra"""
        if self.modified_rows:
            reply = QMessageBox.question(
                self,
                "Canvis No Guardats",
                "Hi ha canvis no guardats. Vols guardar-los abans de tancar?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_changes()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        # Tancar connexió BD
        if self.db_adapter:
            self.db_adapter.close()
