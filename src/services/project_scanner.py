#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Project Scanner Service
Escaneig de fitxers CSV al path \\gompc\kiosk per Scanner Projectes

Versió 1.0: Escaneig bàsic + processament de fitxers CSV + inserció a BBDD
Basat en NetworkScanner però adaptat per \\gompc\kiosk

Autor: Sistema Automàtic
Data: Desembre 2024
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .special_clients_processor import SpecialClientsProcessor
from .ptcover_processor import PTCOVERProcessor

# Configurar logger
logger = logging.getLogger(__name__)

class ProjectScanner:
    r"""
    Escaner per processar fitxers CSV del path \\gompc\kiosk
    Replica la funcionalitat del NetworkScanner però per Scanner Projectes
    """
    
    # Path base per Scanner Projectes
    DEFAULT_PROJECT_PATH = r"\\gompc\kiosk\PROJECTES"
    
    # Clients que requieren processament especial
    EXCLUDED_CLIENTS = ['EXAMPLE_EXCLUDED']  # Adaptar segons necessitats
    SPECIAL_PHASE_CLIENTS = ['VW', 'BMW', 'AUDI', 'MERCEDES', 'SEAT']
    PTCOVER_CLIENT = 'PTCOVER'
    
    # Valor de maquina per Scanner Projectes
    MAQUINA_VALUE = "Scanner Projectes"
    
    def __init__(self, project_path: str = None):
        r"""
        Inicialitzar Project Scanner
        
        Args:
            project_path (str): Path personalitzat per escanejar. Per defecte \\gompc\kiosk
        """
        self.project_path = project_path or self.DEFAULT_PROJECT_PATH
        self.global_dataset = pd.DataFrame()
        
        # Inicialitzar processadors especials
        self.special_processor = SpecialClientsProcessor(self.project_path)
        self.ptcover_processor = PTCOVERProcessor(self.project_path)
        
        logger.info(f"Project Scanner inicialitzat per path: {self.project_path}")
        logger.info(f"Valor maquina: {self.MAQUINA_VALUE}")
    
    def scan_all_projects_and_references(self) -> Dict:
        """
        Escaneja tots els projectes i referències disponibles al path base
        Similar a scan_all_clients_and_references però per projectes
        
        Returns:
            dict: Estructura amb tots els projectes trobats
        """
        try:
            logger.info(f"Iniciant escaneig de projectes a: {self.project_path}")
            
            if not os.path.exists(self.project_path):
                error_msg = f"El path {self.project_path} no existeix o no és accessible"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'projects': {}
                }
            
            projects = {}
            
            # Llistar tots els directoris (projectes)
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                
                if os.path.isdir(item_path):
                    project_name = item
                    logger.info(f"Trobat projecte: {project_name}")
                    
                    # Buscar referències dins del projecte
                    references = self._scan_project_references(item_path, project_name)
                    
                    if references:
                        projects[project_name] = {
                            'path': item_path,
                            'references': references
                        }
                        logger.info(f"  Projecte {project_name}: {len(references)} referències trobades")
                    else:
                        logger.info(f"  Projecte {project_name}: cap referència trobada")
            
            logger.info(f"Escaneig completat: {len(projects)} projectes trobats")
            
            return {
                'success': True,
                'projects': projects,
                'total_projects': len(projects)
            }
            
        except Exception as e:
            error_msg = f"Error escaneiant projectes: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'projects': {}
            }
    
    def _scan_project_references(self, project_path: str, project_name: str) -> List[Dict]:
        """
        Escaneja les referències dins d'un projecte
        
        Args:
            project_path (str): Path del projecte
            project_name (str): Nom del projecte
            
        Returns:
            List[Dict]: Llista de referències trobades
        """
        references = []
        
        try:
            # Escaneig recursiu per trobar fitxers CSV
            for root, dirs, files in os.walk(project_path):
                # Comprovar si hi ha fitxers CSV en aquest directori
                csv_files = [f for f in files if f.lower().endswith('.csv')]
                
                if csv_files:
                    # Determinar el nom de la referència basat en el path relatiu
                    relative_path = os.path.relpath(root, project_path)
                    
                    if relative_path == '.':
                        reference_name = project_name
                    else:
                        reference_name = f"{project_name}_{relative_path.replace(os.sep, '_')}"
                    
                    references.append({
                        'referencia_client': reference_name,
                        'path': root,
                        'csv_files_count': len(csv_files)
                    })
                    
                    logger.debug(f"    Referència: {reference_name} ({len(csv_files)} CSV)")
        
        except Exception as e:
            logger.error(f"Error escaneiant referències del projecte {project_name}: {e}")
        
        return references
    
    def extract_lot_and_datetime_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[datetime]]:
        r"""
        Extreu LOT i DATA_HORA del nom del fitxer CSV
        Suporta múltiples formats de Scanner Projectes:
        - LOT_info_extra_2024_01_01_12_30_45.csv
        - CAV 1.1_2021_11_05_09_47_26.csv  
        - PRJ1234_blabla_2024_01_01_12_30_45.csv
        - 00000_2020_05_12_18_15_01.csv
        
        Args:
            filename (str): Nom del fitxer CSV
            
        Returns:
            Tuple[Optional[str], Optional[datetime]]: LOT i DATA_HORA extrets
        """
        try:
            # Eliminar extensió .csv
            base_name = filename.replace('.csv', '')
            
            # Buscar patró de data/hora al final: YYYY_MM_DD_HH_MM_SS
            date_pattern = r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
            date_match = re.search(date_pattern, base_name)
            
            if date_match:
                # Extraure data/hora
                year, month, day, hour, minute, second = date_match.groups()
                
                try:
                    data_hora = datetime(
                        year=int(year),
                        month=int(month), 
                        day=int(day),
                        hour=int(hour),
                        minute=int(minute),
                        second=int(second)
                    )
                    
                    # Extraure LOT: tot el que està abans de la data/hora
                    lot_part = base_name[:date_match.start()].rstrip('_')
                    
                    # Si LOT està buit, usar nom complet sense data
                    if not lot_part:
                        lot_part = base_name.split('_')[0] if '_' in base_name else base_name
                    
                    # Netejar LOT: eliminar espais múltiples i guions baixos finals
                    lot = lot_part.strip().replace('  ', ' ').rstrip('_')
                    
                    # Si LOT segueix sent buit o massa curt, usar part del nom del fitxer
                    if not lot or len(lot) < 2:
                        # Usar primera part més significativa del nom
                        parts = base_name.split('_')
                        lot = parts[0] if parts else base_name[:10]
                    
                    logger.debug(f"Extret de {filename}: LOT='{lot}', DATA_HORA={data_hora}")
                    return lot, data_hora
                    
                except ValueError as e:
                    logger.debug(f"Error convertint data de {filename}: {e}")
            
            # Si no trobem patró de data vàlid, intentar patrons alternatives
            alternative_patterns = [
                # Format curt: MM_DD_HH_MM_SS (any implícit)
                r'_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$',
                # Format amb any de 2 dígits: YY_MM_DD_HH_MM_SS
                r'_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
            ]
            
            for pattern in alternative_patterns:
                match = re.search(pattern, base_name)
                if match:
                    try:
                        if len(match.groups()) == 5:  # MM_DD_HH_MM_SS
                            month, day, hour, minute, second = match.groups()
                            year = datetime.now().year  # Any actual
                        else:  # YY_MM_DD_HH_MM_SS
                            yy, month, day, hour, minute, second = match.groups()
                            year = 2000 + int(yy) if int(yy) < 50 else 1900 + int(yy)
                        
                        data_hora = datetime(year, int(month), int(day), int(hour), int(minute), int(second))
                        lot_part = base_name[:match.start()].rstrip('_')
                        lot = lot_part if lot_part else base_name.split('_')[0]
                        
                        logger.debug(f"Extret (patró alternatiu) de {filename}: LOT='{lot}', DATA_HORA={data_hora}")
                        return lot, data_hora
                        
                    except (ValueError, IndexError):
                        continue
            
            # Si cap patró funciona, usar valors per defecte basats en nom de fitxer
            logger.debug(f"No es pot extreure data de {filename}, utilitzant valors per defecte")
            
            # Intentar usar primera part del nom com LOT
            parts = base_name.split('_')
            lot = parts[0] if parts else base_name
            
            # Si LOT té només números, afegir prefix
            if lot.isdigit():
                lot = f"LOT_{lot}"
            
            # Usar data actual com fallback
            return lot, datetime.now()
            
        except Exception as e:
            logger.error(f"Error extraient LOT/DATA_HORA de {filename}: {e}")
            return None, None
    
    def read_csv_file(self, file_path: str, project_name: str, referencia_name: str, 
                     lot: str, data_hora: datetime) -> Optional[pd.DataFrame]:
        r"""
        Llegeix i processa un fitxer CSV individual
        Adaptat per Scanner Projectes amb maquina = "Scanner Projectes"
        Format específic: Element;Description;Property;Nominal;Actual;Tol -;Tol +;Dev;Check;Out;Alignment
        
        Args:
            file_path (str): Path complet del fitxer CSV
            project_name (str): Nom del projecte
            referencia_name (str): Nom de la referència
            lot (str): LOT extret del nom del fitxer
            data_hora (datetime): Data i hora extretes del nom del fitxer
            
        Returns:
            Optional[pd.DataFrame]: DataFrame processat o None si error
        """
        try:
            # Llegir CSV amb separador ';' específic per Scanner Projectes
            df = None
            
            try:
                df = pd.read_csv(file_path, encoding='utf-8', sep=';')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1', sep=';')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='cp1252', sep=';')
            
            if df is None or df.empty:
                logger.warning(f"No es pot llegir el fitxer {file_path}")
                return None
            
            # Neteja de noms de columnes (eliminar espais)
            df.columns = df.columns.str.strip()
            
            # Identificar columnes específiques del format Scanner Projectes
            element_col = None
            actual_col = None
            property_col = None
            nominal_col = None
            
            # Buscar columnes per nom exacte
            for col in df.columns:
                col_lower = col.lower()
                if col_lower == 'element':
                    element_col = col
                elif col_lower == 'actual':
                    actual_col = col
                elif col_lower == 'property':
                    property_col = col
                elif col_lower == 'nominal':
                    nominal_col = col
            
            # Si no trobem les columnes exactes, fer fallback
            if element_col is None:
                for col in df.columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['element', 'caracteristic', 'feature', 'param']):
                        element_col = col
                        break
            
            if actual_col is None:
                for col in df.columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['actual', 'valor', 'value', 'mesura', 'measure', 'result']):
                        actual_col = col
                        break
            
            # Si seguim sense trobar columnes, usar les primeres disponibles
            if element_col is None and len(df.columns) >= 1:
                element_col = df.columns[0]
            if actual_col is None and len(df.columns) >= 2:
                actual_col = df.columns[1]
            
            if element_col is None or actual_col is None:
                logger.warning(f"No es poden identificar columnes necessàries a {file_path}")
                logger.debug(f"Columnes disponibles: {list(df.columns)}")
                return None
            
            # Crear dataset estructurat
            processed_rows = []
            
            for _, row in df.iterrows():
                try:
                    element = str(row[element_col]).strip()
                    actual_str = str(row[actual_col]).strip()
                    
                    # Obtenir property si està disponible
                    property_val = ""
                    if property_col and property_col in row:
                        property_val = str(row[property_col]).strip()
                    
                    # Crear element complet (Element + Property si està disponible)
                    if property_val and property_val.lower() != 'nan' and property_val != '':
                        element_full = f"{element}_{property_val}"
                    else:
                        element_full = element
                    
                    # Netejar element (eliminar espais extres)
                    element_full = ' '.join(element_full.split())
                    
                    # PROCESSAR ELEMENT: convertir valors problemàtics a "NULL"
                    element_invalid_patterns = ['nan', 'none', '', 'null', '#N/A', '#ERROR']
                    
                    if not element or element.lower() in element_invalid_patterns:
                        element_full = "NULL"
                    elif any(pattern in element.lower() for pattern in ['¿¿¿', '???', 'unknown', 'error']):
                        # Netejar element de patrons problemàtics però mantenir-lo
                        element_full = element.replace('¿¿¿???', '').replace('¿¿¿', '').replace('???', '').strip()
                        if not element_full:
                            element_full = "NULL"
                    
                    # PROCESSAR VALOR ACTUAL: convertir valors problemàtics a 0.000
                    valor = 0.000  # Valor per defecte
                    
                    # Verificar si el valor és vàlid
                    actual_invalid_patterns = ['nan', 'none', '', 'null', '#N/A', '#ERROR']
                    
                    if not actual_str or actual_str.lower() in actual_invalid_patterns:
                        # Usar valor per defecte
                        valor = 0.000
                    elif any(pattern in actual_str for pattern in ['¿¿¿???', '¿¿¿', '???']):
                        # Valor de plantilla -> 0.000
                        valor = 0.000
                    else:
                        # Intentar convertir valor real
                        try:
                            # Eliminar espais en blanc
                            actual_str = actual_str.replace(' ', '')
                            
                            # Gestió de format numèric europeu
                            if ',' in actual_str and '.' not in actual_str:
                                # Format: "123,45" -> "123.45"
                                actual_str = actual_str.replace(',', '.')
                            elif ',' in actual_str and '.' in actual_str:
                                # Format: "1.234,56" -> "1234.56"
                                parts = actual_str.split(',')
                                if len(parts) == 2 and len(parts[1]) <= 3:  # Decimal part <= 3 digits
                                    integer_part = parts[0].replace('.', '')
                                    decimal_part = parts[1]
                                    actual_str = f"{integer_part}.{decimal_part}"
                                else:
                                    # Si no és format estàndard, intentar només eliminar comes
                                    actual_str = actual_str.replace(',', '')
                            
                            valor = float(actual_str)
                            
                            # Verificar que el valor és raonable (no infinit o NaN)
                            if not (float('-inf') < valor < float('inf')):
                                valor = 0.000
                                
                        except (ValueError, OverflowError):
                            # Si no es pot convertir, usar 0.000
                            valor = 0.000
                            logger.debug(f"Valor '{actual_str}' convertit a 0.000 per element '{element_full}' a {file_path}")
                    
                    # Crear registre sempre (fins i tot amb valors per defecte)
                    processed_rows.append({
                        'client': project_name,
                        'referencia_client': referencia_name,
                        'lot': lot,
                        'data_hora': data_hora,
                        'element': element_full,
                        'valor': valor,
                        'maquina': self.MAQUINA_VALUE,
                        'nom_fitxer': os.path.basename(file_path)
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processant fila: {e}")
                    continue
            
            if not processed_rows:
                logger.warning(f"Cap fila processable trobada a {file_path}")
                logger.debug(f"Columnes utilitzades: element='{element_col}', actual='{actual_col}'")
                logger.debug(f"Primera fila d'exemple: {df.iloc[0].to_dict() if len(df) > 0 else 'N/A'}")
                return None
            
            result_df = pd.DataFrame(processed_rows)
            
            # Comptar quants valors eren originals vs convertits
            original_values = sum(1 for row in processed_rows if row['valor'] != 0.000)
            converted_values = len(processed_rows) - original_values
            
            log_msg = f"Fitxer processat: {os.path.basename(file_path)} -> {len(result_df)} files"
            if converted_values > 0:
                log_msg += f" ({original_values} valors originals, {converted_values} convertits a 0.000)"
                
            logger.info(log_msg)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error llegint fitxer CSV {file_path}: {e}")
            return None
    
    def process_all_csv_files(self) -> Dict:
        """
        Processa tots els fitxers CSV de tots els projectes
        Adaptat per Scanner Projectes
        
        Returns:
            dict: Resum del processament amb estadístiques
        """
        try:
            logger.info("Iniciant processament de tots els fitxers CSV de projectes")
            
            # Reinicialitzar dataset global
            self.global_dataset = pd.DataFrame()
            
            # Obtenir estructura de projectes i referències
            scan_result = self.scan_all_projects_and_references()
            
            if not scan_result['success']:
                return {
                    'success': False,
                    'error': scan_result['error']
                }
            
            # Estadístiques del processament
            stats = {
                'projects_processed': 0,
                'references_processed': 0,
                'csv_files_found': 0,
                'csv_files_processed': 0,
                'csv_files_failed': 0,
                'total_rows': 0,
                'projects_skipped': [],
                'processing_errors': []
            }
            
            # Processar cada projecte
            for project_name, project_data in scan_result['projects'].items():
                
                # Saltar projectes exclosos
                if project_name in self.EXCLUDED_CLIENTS:
                    stats['projects_skipped'].append(project_name)
                    logger.info(f"Saltant projecte exclòs: {project_name}")
                    continue
                
                stats['projects_processed'] += 1
                logger.info(f"Processant projecte: {project_name}")
                
                # Processament normal per projectes regulars
                # Processar cada referència del projecte
                for reference in project_data['references']:
                    referencia_name = reference['referencia_client']
                    reference_path = reference['path']
                    
                    stats['references_processed'] += 1
                    logger.info(f"  Processant referència: {referencia_name}")
                    
                    try:
                        # Llistar fitxers CSV en aquesta referència
                        csv_files = []
                        for item in os.listdir(reference_path):
                            if item.lower().endswith('.csv'):
                                csv_files.append(item)
                        
                        stats['csv_files_found'] += len(csv_files)
                        logger.info(f"    Trobats {len(csv_files)} fitxers CSV")
                        
                        # Processar cada fitxer CSV
                        for csv_file in csv_files:
                            csv_path = os.path.join(reference_path, csv_file)
                            
                            # Extreure LOT i DATA_HORA del nom del fitxer
                            lot, data_hora = self.extract_lot_and_datetime_from_filename(csv_file)
                            
                            if lot is None or data_hora is None:
                                stats['csv_files_failed'] += 1
                                error_msg = f"No es pot extreure LOT/DATA_HORA de: {csv_file}"
                                stats['processing_errors'].append(error_msg)
                                logger.warning(error_msg)
                                continue
                            
                            # Llegir i processar el CSV
                            df = self.read_csv_file(csv_path, project_name, referencia_name, lot, data_hora)
                            
                            if df is not None:
                                # Afegir al dataset global
                                if self.global_dataset.empty:
                                    self.global_dataset = df.copy()
                                else:
                                    self.global_dataset = pd.concat([self.global_dataset, df], ignore_index=True)
                                
                                stats['csv_files_processed'] += 1
                                stats['total_rows'] += len(df)
                                logger.info(f"    Processat: {csv_file} ({len(df)} files)")
                            else:
                                stats['csv_files_failed'] += 1
                                error_msg = f"Error llegint: {csv_file}"
                                stats['processing_errors'].append(error_msg)
                    
                    except Exception as e:
                        error_msg = f"Error processant referència {referencia_name}: {str(e)}"
                        stats['processing_errors'].append(error_msg)
                        logger.error(error_msg)
            
            # Resultat final amb normalització de columnes
            if not self.global_dataset.empty:
                self.global_dataset = self._normalize_column_names(self.global_dataset)
            
            result = {
                'success': True,
                'message': f'Processament completat: {stats["csv_files_processed"]} CSV processats',
                'stats': stats,
                'global_dataset_size': len(self.global_dataset) if not self.global_dataset.empty else 0
            }
            
            logger.info(f"Processament completat: {stats['csv_files_processed']} fitxers CSV processats, {stats['total_rows']} files totals")
            
            return result
            
        except Exception as e:
            error_msg = f"Error en processament global: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': {}
            }
    
    def load_db_config(self) -> Optional[Dict]:
        """
        Carrega la configuració de la base de dades
        Utilitza la mateixa configuració que NetworkScanner
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'database', 'db_config.json')
            config_path = os.path.abspath(config_path)
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.error(f"Fitxer de configuració BBDD no trobat: {config_path}")
                return None
        except Exception as e:
            logger.error(f"Error carregant configuració BBDD: {e}")
            return None
    
    def insert_dataset_to_database(self) -> Dict:
        """
        Insereix el dataset global a la base de dades a la taula 'mesuresqualitat'
        Idèntic a NetworkScanner
        
        Returns:
            dict: Resum de la inserció
        """
        if self.global_dataset is None or self.global_dataset.empty:
            logger.error("No hi ha dataset global per inserir a la BBDD")
            return {
                'success': False,
                'error': 'Dataset global buit o no processat',
                'records_inserted': 0
            }
        
        try:
            # Carregar configuració BBDD
            db_config = self.load_db_config()
            if not db_config:
                return {
                    'success': False,
                    'error': 'No es pot carregar la configuració de la BBDD',
                    'records_inserted': 0
                }
            
            # Importar i utilitzar l'adapter de BBDD
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            
            # Crear adapter amb configuració
            adapter = QualityMeasurementDBAdapter(db_config)
            
            # Connectar a la BBDD
            if not adapter.connect():
                return {
                    'success': False,
                    'error': 'No es pot connectar a la base de dades',
                    'records_inserted': 0
                }
            
            logger.info("Connexió a BBDD establerta correctament")
            
            # Actualitzar esquema de la taula si cal
            logger.info("Actualitzant esquema de la taula mesuresqualitat...")
            schema_result = adapter.update_table_schema()
            
            if schema_result['success']:
                logger.info("Esquema actualitzat correctament")
            else:
                logger.warning(f"Advertència actualitzant esquema: {schema_result.get('message', 'Unknown')}")
            
            # Preparar dataset per inserció
            logger.info("Preparant dataset per inserció...")
            prepared_data = adapter.prepare_dataset_for_insertion(self.global_dataset)
            
            if prepared_data is None or prepared_data.empty:
                return {
                    'success': False,
                    'error': 'Error preparant les dades per inserció',
                    'records_inserted': 0
                }
            
            logger.info(f"Dataset preparat: {len(prepared_data)} registres")
            
            # Inserir a la BBDD
            logger.info("Iniciant inserció a la taula mesuresqualitat...")
            insert_result = adapter.insert_dataset(prepared_data)
            
            # Tancar connexió
            adapter.close()
            
            if insert_result['success']:
                logger.info(f"Inserció completada: {insert_result['records_inserted']} registres")
                return {
                    'success': True,
                    'message': 'Dades inserides correctament a mesuresqualitat',
                    'records_inserted': insert_result['records_inserted'],
                    'maquina_value': self.MAQUINA_VALUE
                }
            else:
                return {
                    'success': False,
                    'error': f"Error en inserció: {insert_result.get('error', 'Unknown')}",
                    'records_inserted': 0
                }
                
        except Exception as e:
            error_msg = f"Error inserint dataset a BBDD: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'records_inserted': 0
            }
    
    def process_and_save_to_database(self) -> Dict:
        """
        Processament complet: escaneja, processa CSV i guarda a BBDD
        Mètode principal per ús extern
        
        Returns:
            dict: Resum complet del processament i inserció
        """
        try:
            logger.info("=== Iniciant processament complet de Scanner Projectes ===")
            
            # Pas 1: Processar tots els CSV
            process_result = self.process_all_csv_files()
            
            if not process_result['success']:
                return {
                    'success': False,
                    'error': f"Error en processament: {process_result['error']}",
                    'process_result': process_result,
                    'db_result': None
                }
            
            logger.info(f"Processament CSV completat: {process_result['stats']['csv_files_processed']} fitxers")
            
            # Pas 2: Inserir a la base de dades
            db_result = self.insert_dataset_to_database()
            
            # Resultat combinat
            final_result = {
                'success': db_result['success'],
                'message': f"Scanner Projectes: {process_result['stats']['csv_files_processed']} CSV processats, {db_result.get('records_inserted', 0)} registres inserits",
                'process_result': process_result,
                'db_result': db_result,
                'maquina_value': self.MAQUINA_VALUE,
                'total_csv_processed': process_result['stats']['csv_files_processed'],
                'total_records_inserted': db_result.get('records_inserted', 0)
            }
            
            if final_result['success']:
                logger.info("=== Processament complet de Scanner Projectes COMPLETAT amb èxit ===")
            else:
                logger.error(f"=== Processament complet FALLIT: {db_result.get('error', 'Unknown')} ===")
            
            return final_result
            
        except Exception as e:
            error_msg = f"Error en processament complet: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'process_result': None,
                'db_result': None
            }
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalitza els noms de les columnes per fer-los compatibles amb la base de dades.
        Converteix columnes de ProjectScanner al format esperat per la BBDD.
        """
        try:
            # Crear còpia per no modificar l'original
            normalized_df = df.copy()
            
            # Mapejat de columnes del ProjectScanner al format BBDD
            column_mapping = {
                'client': 'CLIENT',
                'referencia_client': 'REFERENCIA', 
                'lot': 'LOT',
                'data_hora': 'DATA_HORA',
                'element': 'Element',
                'valor': 'Actual',
                'maquina': 'MAQUINA',
                'nom_fitxer': 'NOM_FITXER'
            }
            
            # Aplicar el mapejat
            for old_name, new_name in column_mapping.items():
                if old_name in normalized_df.columns:
                    normalized_df = normalized_df.rename(columns={old_name: new_name})
            
            logger.info(f"Columnes normalitzades: {list(normalized_df.columns)}")
            return normalized_df
            
        except Exception as e:
            logger.error(f"Error normalitzant noms de columnes: {e}")
            return df


def main():
    """Funció principal per testing"""
    try:
        # Crear instància del scanner
        scanner = ProjectScanner()
        
        # Executar processament complet
        result = scanner.process_and_save_to_database()
        
        # Mostrar resultats
        print("\n" + "="*60)
        print("RESULTATS SCANNER PROJECTES")
        print("="*60)
        
        if result['success']:
            print(f"✅ ÈXIT: {result['message']}")
            print(f"📁 CSV processats: {result['total_csv_processed']}")
            print(f"💾 Registres inserits: {result['total_records_inserted']}")
            print(f"🖥️  Màquina: {result['maquina_value']}")
        else:
            print(f"❌ ERROR: {result['error']}")
        
        print("="*60)
        
    except Exception as e:
        print(f"Error executant Scanner Projectes: {e}")


if __name__ == "__main__":
    main()
