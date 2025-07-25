"""
Processador especial per clients amb estructura de carpetes amb FASE
(RPLL, SAMS, TAKATA)

Estructura: CLIENT -> FASE -> REF_CLIENT -> FITXERS CSV
FASE pot ser: MATRIU, PLA, REMATXAT, MATRIU + REMATXAT
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from .value_cleaner import ValueCleaner

logger = logging.getLogger(__name__)

class SpecialClientsProcessor:
    """Processador per clients amb estructura especial (RPLL, SAMS, TAKATA)"""
    
    def __init__(self, network_path: str):
        self.network_path = network_path
        self.special_clients = ['RPLL', 'SAMS', 'TAKATA']
        self.valid_phases = ['MATRIU', 'PLA', 'REMATXAT', 'MATRIU + REMATXAT']
        self.special_client_structure = {}
    
    def scan_special_client_structure(self, client_name: str) -> Dict:
        """
        Escaneja l'estructura especial d'un client amb fases
        
        Returns:
            dict: Estructura {fase: {referencia: [fitxers]}}
        """
        if client_name not in self.special_clients:
            return {}
            
        client_path = os.path.join(self.network_path, client_name)
        
        if not os.path.exists(client_path):
            logger.warning(f"Path del client especial {client_name} no existeix: {client_path}")
            return {}
        
        structure = {}
        
        try:
            # Escanejar fases dins del client
            for item in os.listdir(client_path):
                fase_path = os.path.join(client_path, item)
                
                if os.path.isdir(fase_path) and item in self.valid_phases:
                    logger.info(f"Escanejant fase {item} del client {client_name}")
                    structure[item] = self._scan_references_in_phase(fase_path, client_name, item)
                    
        except Exception as e:
            logger.error(f"Error escanejant client especial {client_name}: {e}")
            
        return structure
    
    def _scan_references_in_phase(self, fase_path: str, client_name: str, fase_name: str) -> Dict:
        """Escaneja les referències dins d'una fase"""
        references = {}
        
        try:
            for item in os.listdir(fase_path):
                ref_path = os.path.join(fase_path, item)
                
                if os.path.isdir(ref_path):
                    csv_files = self._find_csv_files(ref_path)
                    if csv_files:
                        references[item] = {
                            'path': ref_path,
                            'csv_files': csv_files,
                            'fase': fase_name
                        }
                        logger.info(f"Referència {item} trobada amb {len(csv_files)} fitxers CSV")
                        
        except Exception as e:
            logger.error(f"Error escanejant fase {fase_name} del client {client_name}: {e}")
            
        return references
    
    def _find_csv_files(self, directory: str) -> List[str]:
        """Troba fitxers CSV en un directori"""
        csv_files = []
        
        try:
            for item in os.listdir(directory):
                if item.lower().endswith('.csv'):
                    csv_files.append(os.path.join(directory, item))
                    
        except Exception as e:
            logger.error(f"Error cercant CSV a {directory}: {e}")
            
        return csv_files
    
    def process_special_client_csvs(self, client_name: str) -> pd.DataFrame:
        """
        Processa tots els CSV d'un client especial
        
        Returns:
            DataFrame: Dades consolidades amb metadades especials
        """
        if client_name not in self.special_clients:
            return pd.DataFrame()
            
        logger.info(f"Processant client especial: {client_name}")
        
        # Escanejar estructura
        structure = self.scan_special_client_structure(client_name)
        all_data = []
        
        for fase_name, references in structure.items():
            logger.info(f"Processant fase {fase_name} amb {len(references)} referències")
            
            for ref_name, ref_data in references.items():
                csv_files = ref_data['csv_files']
                
                for csv_file in csv_files:
                    try:
                        # Processar CSV
                        df = self._process_special_csv(csv_file, client_name, fase_name, ref_name)
                        if not df.empty:
                            all_data.append(df)
                            logger.info(f"CSV processat: {os.path.basename(csv_file)} ({len(df)} files)")
                            
                    except Exception as e:
                        logger.error(f"Error processant {csv_file}: {e}")
        
        # Consolidar totes les dades
        if all_data:
            consolidated_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Client especial {client_name} processat: {len(consolidated_df)} files totals")
            return consolidated_df
        else:
            logger.warning(f"No s'han trobat dades per al client especial {client_name}")
            return pd.DataFrame()
    
    def _process_special_csv(self, csv_file: str, client_name: str, fase_name: str, ref_name: str) -> pd.DataFrame:
        """Processa un CSV específic d'un client especial"""
        try:
            # Intentar llegir CSV amb diferents encodings
            df = None
            encodings = ['utf-8', 'windows-1252', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file, sep=';', encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                logger.error(f"Error llegint CSV {csv_file}: No s'ha pogut determinar l'encoding")
                return pd.DataFrame()
            
            if df.empty:
                return pd.DataFrame()
            
            # Extreure nom del fitxer primer
            filename = os.path.basename(csv_file)
            
            # NETEJAT DE VALORS PROBLEMÀTICS
            # Detectar columnes que poden contenir valors problemàtics
            possible_columns = {
                'element': ['Element', 'element', 'ELEMENT', 'Feature', 'feature', 'FEATURE', 'Mesura', 'mesura'],
                'actual': ['Actual', 'actual', 'ACTUAL', 'Value', 'value', 'VALUE', 'Valor', 'valor'],
                'nominal': ['Nominal', 'nominal', 'NOMINAL', 'Target', 'target', 'TARGET'],
                'tolerance': ['Tolerance', 'tolerance', 'TOLERANCE', 'Tol', 'tol', 'TOL']
            }
            
            # Trobar les columnes corresponents
            detected_columns = {}
            for col_type, possible_names in possible_columns.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        detected_columns[col_type] = possible_name
                        break
            
            # Aplicar netejat si trobem columnes
            if detected_columns:
                logger.info(f"Netejant valors problemàtics en {filename}: {detected_columns}")
                
                # Detectar problemes abans
                problems_before = ValueCleaner.detect_problematic_values(df)
                
                # Netejar DataFrame
                df = ValueCleaner.clean_dataframe_columns(
                    df,
                    element_col=detected_columns.get('element'),
                    actual_col=detected_columns.get('actual'),
                    nominal_col=detected_columns.get('nominal'),
                    tolerance_col=detected_columns.get('tolerance')
                )
                
                # Detectar problemes després
                problems_after = ValueCleaner.detect_problematic_values(df)
                
                # Log del resultat
                logger.info(f"Netejat completat per {filename}:")
                logger.info(f"  Patrons plantilla: {problems_before['template_patterns']} -> {problems_after['template_patterns']}")
                logger.info(f"  Patrons invàlids: {problems_before['invalid_patterns']} -> {problems_after['invalid_patterns']}")
                logger.info(f"  Problemes decimals: {problems_before['decimal_issues']} -> {problems_after['decimal_issues']}")
            
            # Extreure LOT i DATA_HORA del nom del fitxer
            lot_data_hora = self._extract_lot_and_datetime_from_filename(filename)
            
            # Afegir metadades especials
            df['CLIENT'] = client_name
            df['FASE'] = fase_name if fase_name is not None else "Única"  # Nova columna per la fase, "Única" si és None
            df['REFERENCIA'] = ref_name
            df['LOT'] = lot_data_hora['lot']
            df['DATA_HORA'] = lot_data_hora['data_hora']
            df['FITXER_ORIGEN'] = filename
            
            return df
            
        except Exception as e:
            logger.error(f"Error llegint CSV {csv_file}: {e}")
            return pd.DataFrame()
    
    def _extract_lot_and_datetime_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Extreu LOT i DATA_HORA del nom del fitxer
        Format esperat: LOT_Any_Mes_Dia_Hora_Minut_Segon.csv
        """
        import re
        
        # Eliminar extensió
        name_without_ext = filename.replace('.csv', '')
        
        # Pattern flexible per trobar data i hora al final
        # Buscar YYYY_MM_DD_HH_MM_SS al final del nom
        date_pattern = r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
        date_match = re.search(date_pattern, name_without_ext)
        
        if date_match:
            # Extreure data i hora
            year = date_match.group(1)
            month = date_match.group(2)
            day = date_match.group(3)
            hour = date_match.group(4)
            minute = date_match.group(5)
            second = date_match.group(6)
            
            data_hora = f"{year}-{month}-{day} {hour}:{minute}:{second}"
            
            # Extreure LOT com tot el que va abans de la data
            lot_part = name_without_ext[:date_match.start()].rstrip('_')
            if not lot_part:
                lot_part = "UNKNOWN"
            
            logger.debug(f"SpecialClient extracció: {filename} -> LOT='{lot_part}', DATA={data_hora}")
            
            return {
                'lot': lot_part,
                'data_hora': data_hora
            }
        else:
            logger.warning(f"SpecialClient: No s'ha pogut extreure LOT i DATA_HORA de {filename}")
            logger.debug(f"SpecialClient: Nom processat: '{name_without_ext}'")
            return {
                'lot': name_without_ext,  # Usar tot el nom com LOT si no troba el patró
                'data_hora': '1900-01-01 00:00:00'
            }
    
    def get_special_client_summary(self, client_name: str) -> Dict:
        """Obté un resum de l'estructura d'un client especial"""
        structure = self.scan_special_client_structure(client_name)
        
        summary = {
            'client': client_name,
            'total_phases': len(structure),
            'phases': {},
            'total_references': 0,
            'total_csv_files': 0
        }
        
        for fase_name, references in structure.items():
            fase_csv_count = sum(len(ref_data['csv_files']) for ref_data in references.values())
            summary['phases'][fase_name] = {
                'references': len(references),
                'csv_files': fase_csv_count
            }
            summary['total_references'] += len(references)
            summary['total_csv_files'] += fase_csv_count
        
        return summary
