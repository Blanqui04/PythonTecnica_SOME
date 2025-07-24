"""
Processador específic per client PTCOVER amb estructura especial de 3 nivells

Estructura: CLIENT (PTCOVER) -> RIVETS (4 RIVETS, 5 RIVETS) -> CAVITATS -> FITXERS CSV
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional

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
            
            # Extreure LOT i DATA_HORA del nom del fitxer
            filename = os.path.basename(csv_file)
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
