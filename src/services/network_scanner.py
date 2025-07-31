"""
Network Scanner Service

Aquest servei s'encarrega d'escanejar directoris de xarxa per trobar
carpetes de clients i projectes disponibles.

Versió 2.1: Escaneig bàsic + processament de fitxers CSV + inserció a BBDD
"""
import os
import logging
import pandas as pd
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .special_clients_processor import SpecialClientsProcessor
from .ptcover_processor import PTCOVERProcessor
from .value_cleaner import ValueCleaner

logger = logging.getLogger(__name__)

class NetworkScanner:
    """Gestiona l'escaneig de directoris de xarxa per trobar projectes"""
    
    # Configuració del servidor
    DEFAULT_NETWORK_PATH = r"\\gompcnou\KIOSK\results"
    
    # Clients a obviar de moment (ara buit perquè PTCOVER té processador específic)
    EXCLUDED_CLIENTS = []
    
    # Clients amb estructura especial de carpetes (tenen capa FASE)
    SPECIAL_PHASE_CLIENTS = ['RPLL', 'SAMS', 'TAKATA']
    
    # Client amb estructura ultra-especial de 3 nivells
    PTCOVER_CLIENT = 'PTCOVER'
    
    def __init__(self, network_path: str = None):
        """
        Inicialitza el scanner de xarxa
        
        Args:
            network_path: Ruta de xarxa personalitzada (opcional)
        """
        self.network_path = network_path or self.DEFAULT_NETWORK_PATH
        self.last_scan_results = {}
        self.global_dataset = pd.DataFrame()  # Dataset global per tots els CSV
        
        # Inicialitzar processador especial per clients amb fases
        self.special_processor = SpecialClientsProcessor(self.network_path)
        
        # Inicialitzar processador específic per PTCOVER
        self.ptcover_processor = PTCOVERProcessor(self.network_path)
        
    def scan_main_directory(self) -> Dict:
        """
        Escaneja el directori principal i retorna informació sobre les carpetes trobades
        
        Returns:
            dict: Informació sobre l'escaneig amb carpetes trobades
        """
        try:
            logger.info(f"Iniciant escaneig del directori: {self.network_path}")
            
            if not self._validate_network_connection():
                return {
                    'success': False,
                    'error': f"No es pot accedir al directori de xarxa: {self.network_path}",
                    'accessible': False
                }
            
            # Llegir contingut del directori
            folders = []
            files = []
            
            for item in os.listdir(self.network_path):
                item_path = os.path.join(self.network_path, item)
                
                if os.path.isdir(item_path):
                    folder_info = self._get_folder_info(item_path, item)
                    folders.append(folder_info)
                else:
                    file_info = self._get_file_info(item_path, item)
                    files.append(file_info)
            
            # Ordenar carpetes per nom
            folders.sort(key=lambda x: x['name'])
            
            result = {
                'success': True,
                'network_path': self.network_path,
                'scan_timestamp': datetime.now().isoformat(),
                'accessible': True,
                'folders': folders,
                'files': files,
                'summary': {
                    'total_folders': len(folders),
                    'total_files': len(files),
                    'client_folders': [f for f in folders if self._is_client_folder(f['name'])]
                }
            }
            
            self.last_scan_results = result
            logger.info(f"Escaneig completat: {len(folders)} carpetes trobades")
            
            return result
            
        except PermissionError as e:
            logger.error(f"Error de permisos accedint a {self.network_path}: {e}")
            return {
                'success': False,
                'error': f"Error de permisos: {str(e)}",
                'accessible': False
            }
        except Exception as e:
            logger.error(f"Error durant l'escaneig: {e}")
            return {
                'success': False,
                'error': str(e),
                'accessible': False
            }
    
    def scan_client_folder(self, client_name: str) -> Dict:
        """
        Escaneja una carpeta específica de client
        
        Args:
            client_name: Nom de la carpeta del client
            
        Returns:
            dict: Informació detallada sobre la carpeta del client
        """
        try:
            client_path = os.path.join(self.network_path, client_name)
            
            if not os.path.exists(client_path):
                return {
                    'success': False,
                    'error': f"Carpeta del client no trobada: {client_name}",
                    'client_name': client_name
                }
            
            if not os.path.isdir(client_path):
                return {
                    'success': False,
                    'error': f"{client_name} no és una carpeta",
                    'client_name': client_name
                }
            
            logger.info(f"Escanejant carpeta del client: {client_name}")
            
            # Escanejar contingut de la carpeta del client
            subfolders = []
            files = []
            
            for item in os.listdir(client_path):
                item_path = os.path.join(client_path, item)
                
                if os.path.isdir(item_path):
                    subfolder_info = self._get_folder_info(item_path, item)
                    subfolders.append(subfolder_info)
                else:
                    file_info = self._get_file_info(item_path, item)
                    files.append(file_info)
            
            # Ordenar per nom
            subfolders.sort(key=lambda x: x['name'])
            
            result = {
                'success': True,
                'client_name': client_name,
                'client_path': client_path,
                'scan_timestamp': datetime.now().isoformat(),
                'subfolders': subfolders,
                'files': files,
                'summary': {
                    'total_subfolders': len(subfolders),
                    'total_files': len(files),
                    'project_folders': [f for f in subfolders if self._is_project_folder(f['name'])]
                }
            }
            
            logger.info(f"Escaneig de {client_name} completat: {len(subfolders)} subcarpetes trobades")
            return result
            
        except Exception as e:
            logger.error(f"Error escanejant carpeta del client {client_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'client_name': client_name
            }
    
    def get_all_clients(self) -> List[str]:
        """
        Retorna una llista de tots els clients disponibles
        
        Returns:
            list: Noms de les carpetes de clients
        """
        scan_result = self.scan_main_directory()
        
        if not scan_result['success']:
            return []
        
        return [folder['name'] for folder in scan_result['folders'] 
                if self._is_client_folder(folder['name'])]
    
    def find_projects_for_client(self, client_name: str) -> List[str]:
        """
        Troba tots els projectes per un client específic
        
        Args:
            client_name: Nom del client
            
        Returns:
            list: Noms dels projectes trobats
        """
        client_scan = self.scan_client_folder(client_name)
        
        if not client_scan['success']:
            return []
        
        return [folder['name'] for folder in client_scan['subfolders']
                if self._is_project_folder(folder['name'])]
    
    def scan_all_clients_and_references(self) -> Dict:
        """
        Escaneja tots els clients i les seves referències
        
        Returns:
            dict: Estructura completa amb clients i referències_client
        """
        try:
            logger.info("Iniciant escaneig complet de clients i referències")
            
            # Primer escaneig del directori principal
            main_scan = self.scan_main_directory()
            
            if not main_scan['success']:
                return {
                    'success': False,
                    'error': main_scan['error'],
                    'accessible': False
                }
            
            # Estructura per guardar els resultats
            clients_structure = {}
            scan_errors = []
            total_references = 0
            
            # Obtenir només les carpetes de clients
            client_folders = [f for f in main_scan['folders'] 
                            if self._is_client_folder(f['name'])]
            
            logger.info(f"Processant {len(client_folders)} clients")
            
            # Per cada client, escanejar les seves referències
            for client_folder in client_folders:
                client_name = client_folder['name']
                logger.info(f"Escanejant client: {client_name}")
                
                try:
                    # Escanejar carpeta del client
                    client_scan = self.scan_client_folder(client_name)
                    
                    if client_scan['success']:
                        # Obtenir les subcarpetes (referències_client)
                        references = []
                        for subfolder in client_scan['subfolders']:
                            reference_name = subfolder['name']
                            references.append({
                                'referencia_client': reference_name,
                                'path': subfolder['path'],
                                'accessible': subfolder.get('accessible', True),
                                'modified_time': subfolder.get('modified_time', ''),
                                'size': subfolder.get('size', 0)
                            })
                        
                        clients_structure[client_name] = {
                            'client': client_name,
                            'client_path': client_scan['client_path'],
                            'total_references': len(references),
                            'references': references,
                            'scan_timestamp': client_scan['scan_timestamp']
                        }
                        
                        total_references += len(references)
                        logger.info(f"Client {client_name}: {len(references)} referències trobades")
                        
                    else:
                        scan_errors.append({
                            'client': client_name,
                            'error': client_scan['error']
                        })
                        logger.warning(f"Error escanejant client {client_name}: {client_scan['error']}")
                        
                except Exception as e:
                    error_msg = f"Error processant client {client_name}: {str(e)}"
                    scan_errors.append({
                        'client': client_name,
                        'error': error_msg
                    })
                    logger.error(error_msg)
            
            # Resultat final
            result = {
                'success': True,
                'network_path': self.network_path,
                'scan_timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_clients': len(clients_structure),
                    'total_references': total_references,
                    'clients_with_errors': len(scan_errors),
                    'scan_errors': scan_errors
                },
                'clients': clients_structure
            }
            
            logger.info(f"Escaneig complet finalitzat: {len(clients_structure)} clients, {total_references} referències")
            return result
            
        except Exception as e:
            logger.error(f"Error durant l'escaneig complet: {e}")
            return {
                'success': False,
                'error': str(e),
                'accessible': False
            }
    
    def get_client_references_list(self, client_name: str = None) -> List[Dict]:
        """
        Obté una llista de totes les referències per client(s)
        
        Args:
            client_name: Nom específic del client (opcional, si None retorna tots)
            
        Returns:
            list: Llista de diccionaris amb client i referència_client
        """
        scan_result = self.scan_all_clients_and_references()
        
        if not scan_result['success']:
            return []
        
        references_list = []
        
        for client, client_data in scan_result['clients'].items():
            # Si s'especifica un client, filtrar
            if client_name and client.lower() != client_name.lower():
                continue
                
            for reference in client_data['references']:
                references_list.append({
                    'client': client,
                    'referencia_client': reference['referencia_client'],
                    'client_path': client_data['client_path'],
                    'reference_path': reference['path'],
                    'accessible': reference['accessible'],
                    'modified_time': reference['modified_time']
                })
        
        return references_list
    
    def _validate_network_connection(self) -> bool:
        """
        Valida que es pugui accedir al directori de xarxa
        
        Returns:
            bool: True si es pot accedir, False altrament
        """
        try:
            return os.path.exists(self.network_path) and os.path.isdir(self.network_path)
        except Exception:
            return False
    
    def _get_folder_info(self, folder_path: str, folder_name: str) -> Dict:
        """
        Obté informació detallada d'una carpeta
        
        Args:
            folder_path: Ruta completa de la carpeta
            folder_name: Nom de la carpeta
            
        Returns:
            dict: Informació de la carpeta
        """
        try:
            stats = os.stat(folder_path)
            return {
                'name': folder_name,
                'path': folder_path,
                'type': 'folder',
                'size': self._get_folder_size(folder_path),
                'modified_time': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'accessible': True
            }
        except Exception as e:
            return {
                'name': folder_name,
                'path': folder_path,
                'type': 'folder',
                'error': str(e),
                'accessible': False
            }
    
    def _get_file_info(self, file_path: str, file_name: str) -> Dict:
        """
        Obté informació detallada d'un fitxer
        
        Args:
            file_path: Ruta completa del fitxer
            file_name: Nom del fitxer
            
        Returns:
            dict: Informació del fitxer
        """
        try:
            stats = os.stat(file_path)
            return {
                'name': file_name,
                'path': file_path,
                'type': 'file',
                'size': stats.st_size,
                'size_mb': round(stats.st_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'extension': os.path.splitext(file_name)[1].lower()
            }
        except Exception as e:
            return {
                'name': file_name,
                'path': file_path,
                'type': 'file',
                'error': str(e)
            }
    
    def _get_folder_size(self, folder_path: str) -> int:
        """
        Calcula la mida total d'una carpeta (només primer nivell per rendiment)
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            int: Mida en bytes
        """
        try:
            total_size = 0
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    total_size += os.path.getsize(item_path)
            return total_size
        except Exception:
            return 0
    
    def _is_client_folder(self, folder_name: str) -> bool:
        """
        Determina si una carpeta és una carpeta de client
        
        Args:
            folder_name: Nom de la carpeta
            
        Returns:
            bool: True si sembla una carpeta de client
        """
        # Carpetes que no són clients
        exclude_patterns = [
            'calibration', 'measured', 'projectes', 'destructor'
        ]
        
        folder_lower = folder_name.lower()
        
        # Si conté patrons d'exclusió, no és un client
        for pattern in exclude_patterns:
            if pattern in folder_lower:
                return False
        
        # Si està en la llista d'exclosos específics, no és un client per ara
        if folder_name in self.EXCLUDED_CLIENTS:
            return False
        
        # Si té més de 3 caràcters i no conté només números, probablement és un client
        return len(folder_name) > 3
    
    def _is_project_folder(self, folder_name: str) -> bool:
        """
        Determina si una carpeta és una carpeta de projecte
        
        Args:
            folder_name: Nom de la carpeta
            
        Returns:
            bool: True si sembla una carpeta de projecte
        """
        # Els projectes solen tenir números o codis específics
        return any(c.isdigit() for c in folder_name) or len(folder_name) > 5
    
    def print_scan_summary(self) -> None:
        """Imprimeix un resum de l'últim escaneig"""
        if not self.last_scan_results:
            print("No hi ha resultats d'escaneig disponibles")
            return
        
        results = self.last_scan_results
        
        if not results['success']:
            print(f"❌ Error durant l'escaneig: {results['error']}")
            return
        
        print(f"\n📁 Resum de l'escaneig de {results['network_path']}")
        print(f"🕒 Data: {results['scan_timestamp']}")
        print(f"📂 Carpetes trobades: {results['summary']['total_folders']}")
        print(f"📄 Fitxers trobats: {results['summary']['total_files']}")
        
        print(f"\n🏢 Clients identificats:")
        client_folders = results['summary']['client_folders']
        for client in client_folders:
            print(f"  - {client['name']}")
        
        print(f"\n📋 Altres carpetes:")
        other_folders = [f for f in results['folders'] 
                        if not self._is_client_folder(f['name'])]
        for folder in other_folders:
            print(f"  - {folder['name']}")
    
    def print_clients_and_references_summary(self) -> None:
        """Imprimeix un resum detallat de clients i referències"""
        scan_result = self.scan_all_clients_and_references()
        
        if not scan_result['success']:
            print(f"❌ Error durant l'escaneig: {scan_result['error']}")
            return
        
        print(f"\n🏢 RESUM COMPLET DE CLIENTS I REFERÈNCIES")
        print(f"{'='*60}")
        print(f"📁 Directori escanejat: {scan_result['network_path']}")
        print(f"🕒 Data escaneig: {scan_result['scan_timestamp']}")
        print(f"🏢 Total clients: {scan_result['summary']['total_clients']}")
        print(f"📋 Total referències: {scan_result['summary']['total_references']}")
        
        if scan_result['summary']['clients_with_errors'] > 0:
            print(f"⚠️  Clients amb errors: {scan_result['summary']['clients_with_errors']}")
        
        print(f"\n{'='*60}")
        
        # Mostrar cada client i les seves referències
        for client_name, client_data in scan_result['clients'].items():
            print(f"\n🏢 CLIENT: {client_name}")
            print(f"   📁 Ruta: {client_data['client_path']}")
            print(f"   📋 Total referències: {client_data['total_references']}")
            
            if client_data['references']:
                print(f"   🔗 Referències:")
                for i, ref in enumerate(client_data['references'], 1):
                    status = "✅" if ref['accessible'] else "❌"
                    print(f"      {i:2d}. {status} {ref['referencia_client']}")
            else:
                print(f"   ⚠️  No s'han trobat referències")
        
        # Mostrar errors si n'hi ha
        if scan_result['summary']['scan_errors']:
            print(f"\n⚠️  ERRORS DURANT L'ESCANEIG:")
            print(f"{'='*40}")
            for error in scan_result['summary']['scan_errors']:
                print(f"❌ {error['client']}: {error['error']}")
    
    def export_clients_and_references_to_dict(self) -> Dict:
        """
        Exporta la informació de clients i referències en un format simple
        
        Returns:
            dict: Estructura simplificada amb clients i referències
        """
        scan_result = self.scan_all_clients_and_references()
        
        if not scan_result['success']:
            return {'error': scan_result['error']}
        
        simplified_structure = {
            'scan_info': {
                'network_path': scan_result['network_path'],
                'scan_timestamp': scan_result['scan_timestamp'],
                'total_clients': scan_result['summary']['total_clients'],
                'total_references': scan_result['summary']['total_references']
            },
            'clients_data': {}
        }
        
        for client_name, client_data in scan_result['clients'].items():
            simplified_structure['clients_data'][client_name] = {
                'client': client_name,
                'references': [ref['referencia_client'] for ref in client_data['references']]
            }
        
        return simplified_structure
    
    def extract_lot_and_datetime_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extreu el LOT i DATA_HORA del nom del fitxer
        Format esperat: LOT_ANY_MES_DIA_HORA_MINUT_SEGON.csv
        
        Args:
            filename: Nom del fitxer (ex: "1200135A_2023_01_31_22_01_56.csv")
            
        Returns:
            tuple: (LOT, DATA_HORA) o (None, None) si no es pot extreure
        """
        try:
            # Eliminar l'extensió
            name_without_ext = os.path.splitext(filename)[0]
            
            # Patró regex per extreure LOT i components de data/hora
            # Busca: LOT_ANY_MES_DIA_HORA_MINUT_SEGON
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
                
                # Construir DATA_HORA en format ISO
                data_hora = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                
                return lot, data_hora
            else:
                logger.warning(f"No es pot extreure LOT i DATA_HORA de: {filename}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error processant nom de fitxer {filename}: {e}")
            return None, None
    
    def read_csv_file(self, file_path: str, client: str, referencia: str, lot: str, data_hora: str) -> Optional[pd.DataFrame]:
        """
        Llegeix un fitxer CSV i afegeix les columnes CLIENT, REFERENCIA, LOT, DATA_HORA
        
        Args:
            file_path: Ruta completa del fitxer CSV
            client: Nom del client
            referencia: Referència del client
            lot: Número de lot extret del nom del fitxer
            data_hora: Data i hora extreta del nom del fitxer
            
        Returns:
            DataFrame amb les dades del CSV + columnes addicionals, o None si error
        """
        try:
            # Llegir CSV - provar diferents separadors i encodings per evitar problemes Unicode
            separators = [';', ',', '\t']
            encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding=encoding)
                        if len(df.columns) > 1:  # Si té més d'una columna, probablement és correcte
                            logger.debug(f"CSV llegit amb encoding {encoding} i separador '{sep}': {file_path}")
                            break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error llegint amb {encoding}/{sep}: {e}")
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            
            if df is None or df.empty:
                logger.warning(f"No es pot llegir o el fitxer està buit: {file_path}")
                return None
            
            # Netejar columnes problemàtiques
            # Si hi ha columna "Out,Alignment", dividir-la
            if 'Out,Alignment' in df.columns:
                # Intentar dividir la columna combinada
                out_alignment = df['Out,Alignment'].astype(str)
                df['Out'] = out_alignment
                df['Alignment'] = out_alignment
                df = df.drop(columns=['Out,Alignment'])
            
            # Eliminar columnes duplicades si existeixen
            df = df.loc[:, ~df.columns.duplicated()]
            
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
                logger.info(f"Netejant valors problemàtics en: {detected_columns}")
                
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
                logger.info(f"Netejat completat per {os.path.basename(file_path)}:")
                logger.info(f"  Patrons plantilla: {problems_before['template_patterns']} -> {problems_after['template_patterns']}")
                logger.info(f"  Patrons invàlids: {problems_before['invalid_patterns']} -> {problems_after['invalid_patterns']}")
                logger.info(f"  Problemes decimals: {problems_before['decimal_issues']} -> {problems_after['decimal_issues']}")
            
            # Afegir les columnes identificadores
            df['CLIENT'] = client
            df['FASE'] = "Única"  # Per clients normals sempre és "Única"
            df['REFERENCIA'] = referencia
            df['LOT'] = lot
            df['DATA_HORA'] = data_hora
            
            logger.info(f"CSV llegit: {os.path.basename(file_path)} - {len(df)} files")
            return df
            
        except Exception as e:
            logger.error(f"Error llegint fitxer CSV {file_path}: {e}")
            return None
    
    def process_all_csv_files(self) -> Dict:
        """
        Processa tots els fitxers CSV de tots els clients (excepte EXCLUDED_CLIENTS)
        i crea un dataset global
        
        Returns:
            dict: Resum del processament amb estadístiques
        """
        try:
            logger.info("Iniciant processament de tots els fitxers CSV")
            
            # Reinicialitzar dataset global
            self.global_dataset = pd.DataFrame()
            
            # Obtenir estructura de clients i referències
            scan_result = self.scan_all_clients_and_references()
            
            if not scan_result['success']:
                return {
                    'success': False,
                    'error': scan_result['error']
                }
            
            # Estadístiques del processament
            stats = {
                'clients_processed': 0,
                'references_processed': 0,
                'csv_files_found': 0,
                'csv_files_processed': 0,
                'csv_files_failed': 0,
                'total_rows': 0,
                'clients_skipped': [],
                'processing_errors': []
            }
            
            # Processar cada client
            for client_name, client_data in scan_result['clients'].items():
                
                # Saltar clients exclosos
                if client_name in self.EXCLUDED_CLIENTS:
                    stats['clients_skipped'].append(client_name)
                    logger.info(f"Saltant client exclòs: {client_name}")
                    continue
                
                stats['clients_processed'] += 1
                logger.info(f"Processant client: {client_name}")
                
                # Verificar si és un client especial amb estructura de fases
                if client_name in self.SPECIAL_PHASE_CLIENTS:
                    try:
                        logger.info(f"Processant client especial amb fases: {client_name}")
                        special_df = self.special_processor.process_special_client_csvs(client_name)
                        
                        if not special_df.empty:
                            # Afegir al dataset global
                            if self.global_dataset.empty:
                                self.global_dataset = special_df
                            else:
                                self.global_dataset = pd.concat([self.global_dataset, special_df], ignore_index=True)
                            
                            stats['csv_files_processed'] += len(special_df)
                            stats['total_rows'] += len(special_df)
                            logger.info(f"Client especial {client_name} processat: {len(special_df)} files")
                        
                    except Exception as e:
                        error_msg = f"Error processant client especial {client_name}: {e}"
                        logger.error(error_msg)
                        stats['processing_errors'].append(error_msg)
                        stats['csv_files_failed'] += 1
                    
                    continue  # Saltar processament normal per clients especials
                
                # Verificar si és el client PTCOVER amb estructura ultra-especial
                if client_name == self.PTCOVER_CLIENT:
                    try:
                        logger.info(f"Processant client PTCOVER amb estructura de 3 nivells: {client_name}")
                        ptcover_df = self.ptcover_processor.process_ptcover_csvs()
                        
                        if not ptcover_df.empty:
                            # Afegir al dataset global
                            if self.global_dataset.empty:
                                self.global_dataset = ptcover_df
                            else:
                                self.global_dataset = pd.concat([self.global_dataset, ptcover_df], ignore_index=True)
                            
                            stats['csv_files_processed'] += len(ptcover_df)
                            stats['total_rows'] += len(ptcover_df)
                            logger.info(f"Client PTCOVER processat: {len(ptcover_df)} files")
                        
                    except Exception as e:
                        error_msg = f"Error processant client PTCOVER: {e}"
                        logger.error(error_msg)
                        stats['processing_errors'].append(error_msg)
                        stats['csv_files_failed'] += 1
                    
                    continue  # Saltar processament normal per PTCOVER
                
                # Processament normal per clients regulars
                # Processar cada referència del client
                for reference in client_data['references']:
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
                            df = self.read_csv_file(csv_path, client_name, referencia_name, lot, data_hora)
                            
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
            
            # Resultat final
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'csv_files_processed': stats['csv_files_processed'],
                'total_records': len(self.global_dataset),
                'errors': stats['processing_errors'],
                'statistics': stats,
                'dataset_info': {
                    'total_rows': len(self.global_dataset),
                    'total_columns': len(self.global_dataset.columns) if not self.global_dataset.empty else 0,
                    'columns': list(self.global_dataset.columns) if not self.global_dataset.empty else []
                }
            }
            
            logger.info(f"Processament completat: {stats['csv_files_processed']} fitxers, {len(self.global_dataset)} files totals")
            return result
            
        except Exception as e:
            logger.error(f"Error durant el processament de CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_global_dataset(self) -> pd.DataFrame:
        """
        Retorna el dataset global amb tots els CSV processats
        
        Returns:
            DataFrame: Dataset global amb totes les dades
        """
        return self.global_dataset.copy() if not self.global_dataset.empty else pd.DataFrame()
    
    def save_global_dataset(self, output_path: str, format: str = 'csv') -> bool:
        """
        Guarda el dataset global en un fitxer
        
        Args:
            output_path: Ruta on guardar el fitxer
            format: Format del fitxer ('csv', 'excel', 'parquet')
            
        Returns:
            bool: True si s'ha guardat correctament
        """
        try:
            if self.global_dataset.empty:
                logger.warning("El dataset global està buit, no es pot guardar")
                return False
            
            if format.lower() == 'csv':
                self.global_dataset.to_csv(output_path, index=False, encoding='utf-8')
            elif format.lower() == 'excel':
                self.global_dataset.to_excel(output_path, index=False)
            elif format.lower() == 'parquet':
                self.global_dataset.to_parquet(output_path, index=False)
            else:
                raise ValueError(f"Format no suportat: {format}")
            
            logger.info(f"Dataset global guardat a: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardant dataset global: {e}")
            return False
    
    def print_dataset_summary(self) -> None:
        """Imprimeix un resum del dataset global"""
        if self.global_dataset.empty:
            print("❌ El dataset global està buit")
            return
        
        print(f"\n📊 RESUM DEL DATASET GLOBAL")
        print(f"{'='*50}")
        print(f"📋 Total files: {len(self.global_dataset):,}")
        print(f"📂 Total columnes: {len(self.global_dataset.columns)}")
        
        # Resum per client
        if 'CLIENT' in self.global_dataset.columns:
            print(f"\n🏢 DISTRIBUCIÓ PER CLIENT:")
            client_counts = self.global_dataset['CLIENT'].value_counts()
            for client, count in client_counts.items():
                print(f"   {client}: {count:,} files")
        
        # Resum per LOT
        if 'LOT' in self.global_dataset.columns:
            print(f"\n📦 TOTAL LOTS ÚNICS: {self.global_dataset['LOT'].nunique()}")
            
        # Resum per referència
        if 'REFERENCIA' in self.global_dataset.columns:
            print(f"\n🔗 TOTAL REFERÈNCIES ÚNIQUES: {self.global_dataset['REFERENCIA'].nunique()}")
        
        # Columnes disponibles
        print(f"\n📋 COLUMNES DISPONIBLES:")
        for i, col in enumerate(self.global_dataset.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Informació de dates
        if 'DATA_HORA' in self.global_dataset.columns:
            try:
                # Convertir a datetime si és possible
                dates = pd.to_datetime(self.global_dataset['DATA_HORA'])
                print(f"\n📅 RANG DE DATES:")
                print(f"   Des de: {dates.min()}")
                print(f"   Fins a: {dates.max()}")
            except:
                print(f"\n📅 Columna DATA_HORA disponible però no es pot processar com a dates")

    def load_db_config(self) -> Dict:
        """Carrega la configuració de la base de dades"""
        try:
            db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
            with open(db_config_path, 'r') as f:
                config = json.load(f)
            
            # Retornar la configuració 'primary' directament
            if 'primary' in config:
                logger.info("Configuració de BBDD 'primary' carregada correctament")
                return config['primary']
            else:
                logger.error("No es troba la configuració 'primary' a db_config.json")
                return None
        except Exception as e:
            logger.error(f"Error carregant configuració BBDD: {e}")
            return None
    
    def insert_dataset_to_database(self) -> Dict:
        """
        Insereix el dataset global a la base de dades a la taula 'mesuresqualitat'
        
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
                    'records_total': len(self.global_dataset),
                    'skipped_records': insert_result.get('skipped_records', 0),
                    'errors': insert_result.get('errors', [])
                }
            else:
                return {
                    'success': False,
                    'error': insert_result.get('error', 'Error desconegut durant la inserció'),
                    'records_inserted': insert_result.get('records_inserted', 0)
                }
                
        except Exception as e:
            logger.error(f"Error durant la inserció a BBDD: {e}")
            return {
                'success': False,
                'error': f'Error inesperat: {str(e)}',
                'records_inserted': 0
            }
    
    def process_and_store_data(self) -> Dict:
        """
        Processa tots els CSV i els guarda a la base de dades
        Pipeline complet: scan → process → store
        
        Returns:
            dict: Resum del procés complet
        """
        logger.info("=== INICIANT PIPELINE COMPLET ===")
        
        try:
            # Pas 1: Escanejar tots els clients i referències
            logger.info("Pas 1: Escanejant clients i referències...")
            scan_result = self.scan_all_clients_and_references()
            
            if not scan_result['success']:
                return {
                    'success': False,
                    'error': f"Error durant l'escaneig: {scan_result.get('error', 'Unknown')}",
                    'step_failed': 'scan'
                }
            
            logger.info(f"Escaneig completat: {scan_result['total_clients']} clients trobats")
            
            # Pas 2: Processar tots els CSV
            logger.info("Pas 2: Processant fitxers CSV...")
            process_result = self.process_all_csv_files()
            
            if not process_result['success']:
                return {
                    'success': False,
                    'error': f"Error durant el processament: {process_result.get('error', 'Unknown')}",
                    'step_failed': 'process'
                }
            
            logger.info(f"Processament completat: {process_result['total_records']} registres")
            
            # Pas 3: Inserir a la base de dades
            logger.info("Pas 3: Inserint a la base de dades...")
            db_result = self.insert_dataset_to_database()
            
            if not db_result['success']:
                return {
                    'success': False,
                    'error': f"Error durant la inserció a BBDD: {db_result.get('error', 'Unknown')}",
                    'step_failed': 'database',
                    'scan_data': scan_result,
                    'process_data': process_result
                }
            
            logger.info("=== PIPELINE COMPLET FINALITZAT ===")
            
            # Resum final
            return {
                'success': True,
                'message': 'Pipeline complet executat correctament',
                'scan_summary': {
                    'clients_found': scan_result['summary']['total_clients'],
                    'references_found': scan_result['summary']['total_references']
                },
                'process_summary': {
                    'csv_files_processed': process_result['csv_files_processed'],
                    'total_records': process_result['total_records'],
                    'errors': process_result['errors']
                },
                'database_summary': {
                    'records_inserted': db_result['records_inserted'],
                    'skipped_records': db_result.get('skipped_records', 0),
                    'db_errors': db_result.get('errors', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error crític durant el pipeline: {e}")
            return {
                'success': False,
                'error': f'Error crític: {str(e)}',
                'step_failed': 'pipeline'
            }
    
    def copy_data_between_databases(self) -> Dict:
        """
        Copia les dades de la taula mesuresqualitat de la BBDD origen (airflow_db/config_2) 
        cap a la BBDD destí (documentacio_tecnica/config_1)
        
        Returns:
            dict: Resum de la còpia de dades
        """
        try:
            logger.info("=== INICIANT CÒPIA DE DADES ENTRE BBDD ===")
            
            # Carregar configuració completa
            db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
            with open(db_config_path, 'r') as f:
                full_config = json.load(f)
            
            # Configuracions origen i destí
            source_config = full_config['secondary']  # airflow_db (config_2)
            target_config = full_config['primary']    # documentacio_tecnica (config_1)
            
            logger.info(f"Origen: {source_config['database']} en {source_config['host']}:{source_config['port']}")
            logger.info(f"Destí: {target_config['database']} en {target_config['host']}:{target_config['port']}")
            
            # Importar i crear adapters
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            
            # Connectar a la BBDD origen
            source_adapter = QualityMeasurementDBAdapter(source_config)
            if not source_adapter.connect():
                return {
                    'success': False,
                    'error': 'No es pot connectar a la base de dades origen (airflow_db)',
                    'records_copied': 0
                }
            
            logger.info("Connexió a BBDD origen establerta")
            
            # Connectar a la BBDD destí
            target_adapter = QualityMeasurementDBAdapter(target_config)
            if not target_adapter.connect():
                source_adapter.close()
                return {
                    'success': False,
                    'error': 'No es pot connectar a la base de dades destí (documentacio_tecnica)',
                    'records_copied': 0
                }
            
            logger.info("Connexió a BBDD destí establerta")
            
            # Pas 1: Verificar/crear esquema a la BBDD destí
            logger.info("Verificant esquema de la taula destí...")
            schema_result = target_adapter.update_table_schema()
            if schema_result['success']:
                logger.info("Esquema de destí verificat/creat correctament")
            else:
                logger.warning(f"Advertència amb esquema destí: {schema_result.get('message', 'Unknown')}")
            
            # Pas 2: Llegir totes les dades de la taula origen
            logger.info("Llegint dades de la taula mesuresqualitat origen...")
            
            try:
                with source_adapter.connection.cursor() as cursor:
                    # Comptar registres totals
                    cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                    total_records = cursor.fetchone()[0]
                    logger.info(f"Total registres a la BBDD origen: {total_records}")
                    
                    if total_records == 0:
                        source_adapter.close()
                        target_adapter.close()
                        return {
                            'success': True,
                            'message': 'No hi ha dades per copiar a la BBDD origen',
                            'records_copied': 0,
                            'records_total': 0
                        }
                    
                    # Llegir totes les dades
                    cursor.execute("SELECT * FROM mesuresqualitat ORDER BY created_at")
                    columns = [desc[0] for desc in cursor.description]
                    data = cursor.fetchall()
                    
                    logger.info(f"Dades llegides: {len(data)} registres amb {len(columns)} columnes")
                    
            except Exception as e:
                source_adapter.close()
                target_adapter.close()
                return {
                    'success': False,
                    'error': f'Error llegint dades de la BBDD origen: {str(e)}',
                    'records_copied': 0
                }
            
            # Pas 3: Convertir a DataFrame per facilitar la inserció
            import pandas as pd
            source_df = pd.DataFrame(data, columns=columns)
            logger.info(f"DataFrame creat amb {len(source_df)} registres")
            
            # Pas 4: Preparar dades per inserció al destí
            logger.info("Preparant dades per inserció...")
            prepared_data = target_adapter.prepare_dataset_for_insertion(source_df)
            
            if prepared_data is None or prepared_data.empty:
                source_adapter.close()
                target_adapter.close()
                return {
                    'success': False,
                    'error': 'Error preparant les dades per inserció',
                    'records_copied': 0
                }
            
            # Pas 5: Inserir a la BBDD destí
            logger.info("Inserint dades a la BBDD destí...")
            insert_result = target_adapter.insert_dataset(prepared_data)
            
            # Tancar connexions
            source_adapter.close()
            target_adapter.close()
            
            if insert_result['success']:
                logger.info(f"Còpia completada: {insert_result['records_inserted']} registres")
                return {
                    'success': True,
                    'message': 'Dades copiades correctament entre bases de dades',
                    'records_copied': insert_result['records_inserted'],
                    'records_total': total_records,
                    'records_skipped': insert_result.get('skipped_records', 0),
                    'source_database': source_config['database'],
                    'target_database': target_config['database'],
                    'errors': insert_result.get('errors', [])
                }
            else:
                return {
                    'success': False,
                    'error': insert_result.get('error', 'Error desconegut durant la inserció'),
                    'records_copied': insert_result.get('records_inserted', 0),
                    'source_database': source_config['database'],
                    'target_database': target_config['database']
                }
                
        except Exception as e:
            logger.error(f"Error durant la còpia de dades: {e}")
            return {
                'success': False,
                'error': f'Error inesperat: {str(e)}',
                'records_copied': 0
            }
