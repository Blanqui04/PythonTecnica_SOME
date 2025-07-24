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
            
            # Extreure LOT i DATA_HORA del nom del fitxer
            filename = os.path.basename(csv_file)
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
        
        # Pattern per extreure LOT_YYYY_MM_DD_HH_MM_SS
        pattern = r'^(.+?)_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
        match = re.match(pattern, name_without_ext)
        
        if match:
            lot = match.group(1)
            year = match.group(2)
            month = match.group(3)
            day = match.group(4)
            hour = match.group(5)
            minute = match.group(6)
            second = match.group(7)
            
            data_hora = f"{year}-{month}-{day} {hour}:{minute}:{second}"
            
            return {
                'lot': lot,
                'data_hora': data_hora
            }
        else:
            logger.warning(f"No s'ha pogut extreure LOT i DATA_HORA de {filename}")
            return {
                'lot': 'UNKNOWN',
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
