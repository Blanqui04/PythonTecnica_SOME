"""
Processador específic per client PTCOVER amb estructura especial de 3 nivells

Estructura: CLIENT (PTCOVER) -> RIVETS (4 RIVETS, 5 RIVETS) -> CAVITATS -> FITXERS CSV
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from .value_cleaner import ValueCleaner

logger = logging.getLogger(__name__)

class PTCOVERProcessor:
    """Processador específic per client PTCOVER amb estructura de 3 nivells"""
    
    def __init__(self, network_path: str):
        self.network_path = network_path
        self.client_name = 'PTCOVER'
        self.valid_rivets = ['4 RIVETS', '5 RIVETS']
        self.ptcover_structure = {}
    
    def scan_ptcover_structure(self) -> Dict:
        """
        Escaneja l'estructura específica de PTCOVER
        
        Returns:
            dict: Estructura {rivet_type: {cavitat: [fitxers]}}
        """
        client_path = os.path.join(self.network_path, self.client_name)
        
        if not os.path.exists(client_path):
            logger.warning(f"Path del client PTCOVER no existeix: {client_path}")
            return {}
        
        structure = {}
        
        try:
            # Escanejar tipus de RIVETS dins del client PTCOVER
            for item in os.listdir(client_path):
                rivets_path = os.path.join(client_path, item)
                
                if os.path.isdir(rivets_path) and item in self.valid_rivets:
                    logger.info(f"Escanejant tipus de rivets: {item}")
                    structure[item] = self._scan_cavitats_in_rivets(rivets_path, item)
                elif os.path.isdir(rivets_path):
                    logger.warning(f"Tipus de rivets no reconegut: {item}")
                    
        except Exception as e:
            logger.error(f"Error escanejant client PTCOVER: {e}")
            
        return structure
    
    def _scan_cavitats_in_rivets(self, rivets_path: str, rivets_type: str) -> Dict:
        """Escaneja les cavitats dins d'un tipus de rivets"""
        cavitats = {}
        
        try:
            for item in os.listdir(rivets_path):
                cavitat_path = os.path.join(rivets_path, item)
                
                if os.path.isdir(cavitat_path):
                    csv_files = self._find_csv_files(cavitat_path)
                    if csv_files:
                        cavitats[item] = {
                            'path': cavitat_path,
                            'csv_files': csv_files,
                            'rivets_type': rivets_type
                        }
                        logger.info(f"Cavitat {item} trobada amb {len(csv_files)} fitxers CSV")
                        
        except Exception as e:
            logger.error(f"Error escanejant cavitats en {rivets_type}: {e}")
            
        return cavitats
    
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
    
    def process_ptcover_csvs(self) -> pd.DataFrame:
        """
        Processa tots els CSV del client PTCOVER
        
        Returns:
            DataFrame: Dades consolidades amb metadades específiques de PTCOVER
        """
        logger.info("Processant client especial: PTCOVER")
        
        # Escanejar estructura
        structure = self.scan_ptcover_structure()
        all_data = []
        
        for rivets_type, cavitats in structure.items():
            logger.info(f"Processant tipus de rivets: {rivets_type} amb {len(cavitats)} cavitats")
            
            for cavitat_name, cavitat_data in cavitats.items():
                csv_files = cavitat_data['csv_files']
                
                for csv_file in csv_files:
                    try:
                        # Processar CSV
                        df = self._process_ptcover_csv(
                            csv_file, 
                            rivets_type, 
                            cavitat_name
                        )
                        
                        if not df.empty:
                            all_data.append(df)
                            logger.info(f"CSV processat: {os.path.basename(csv_file)} ({len(df)} files)")
                            
                    except Exception as e:
                        logger.error(f"Error processant {csv_file}: {e}")
        
        # Consolidar totes les dades
        if all_data:
            consolidated_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Client PTCOVER processat: {len(consolidated_df)} files totals")
            return consolidated_df
        else:
            logger.warning("No s'han trobat dades per al client PTCOVER")
            return pd.DataFrame()
    
    def _process_ptcover_csv(self, csv_file: str, rivets_type: str, cavitat_name: str) -> pd.DataFrame:
        """Processa un CSV específic del client PTCOVER"""
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
                logger.info(f"Netejant valors problemàtics en PTCOVER {filename}: {detected_columns}")
                
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
                logger.info(f"Netejat completat per PTCOVER {filename}:")
                logger.info(f"  Patrons plantilla: {problems_before['template_patterns']} -> {problems_after['template_patterns']}")
                logger.info(f"  Patrons invàlids: {problems_before['invalid_patterns']} -> {problems_after['invalid_patterns']}")
                logger.info(f"  Problemes decimals: {problems_before['decimal_issues']} -> {problems_after['decimal_issues']}")
            
            # Extreure LOT i DATA_HORA del nom del fitxer
            lot_data_hora = self._extract_lot_and_datetime_from_filename(filename)
            
            # Afegir metadades específiques de PTCOVER
            df['CLIENT'] = self.client_name
            df['FASE'] = "Única"  # PTCOVER sempre té fase única
            df['RIVETS_TYPE'] = rivets_type  # Nova columna específica per PTCOVER
            df['CAVITAT'] = cavitat_name     # Nova columna específica per PTCOVER
            df['REFERENCIA'] = f"{rivets_type}_{cavitat_name}"  # Referència combinada
            df['LOT'] = lot_data_hora['lot']
            df['DATA_HORA'] = lot_data_hora['data_hora']
            df['FITXER_ORIGEN'] = filename
            
            return df
            
        except Exception as e:
            logger.error(f"Error llegint CSV {csv_file}: {e}")
            return pd.DataFrame()
    
    def _extract_lot_and_datetime_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Extreu LOT i DATA_HORA del nom del fitxer per PTCOVER
        Format esperat: LOT+CAVITATS+DATAHORA (flexible)
        Exemples: 
        - CAV1_LOT123_2024_01_01_12_30_45.csv
        - 1217853_CAV2_2024_02_22_23_25_10.csv
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
            
            logger.debug(f"PTCOVER extracció: {filename} -> LOT='{lot_part}', DATA={data_hora}")
            
            return {
                'lot': lot_part,
                'data_hora': data_hora
            }
        else:
            logger.warning(f"PTCOVER: No s'ha pogut extreure LOT i DATA_HORA de {filename}")
            logger.debug(f"PTCOVER: Nom processat: '{name_without_ext}'")
            return {
                'lot': name_without_ext,  # Usar tot el nom com LOT si no troba el patró
                'data_hora': '1900-01-01 00:00:00'
            }
    
    def get_ptcover_summary(self) -> Dict:
        """Obté un resum de l'estructura del client PTCOVER"""
        structure = self.scan_ptcover_structure()
        
        summary = {
            'client': self.client_name,
            'total_rivets_types': len(structure),
            'rivets_types': {},
            'total_cavitats': 0,
            'total_csv_files': 0
        }
        
        for rivets_type, cavitats in structure.items():
            cavitats_csv_count = sum(len(cavitat_data['csv_files']) for cavitat_data in cavitats.values())
            summary['rivets_types'][rivets_type] = {
                'cavitats': len(cavitats),
                'csv_files': cavitats_csv_count
            }
            summary['total_cavitats'] += len(cavitats)
            summary['total_csv_files'] += cavitats_csv_count
        
        return summary
