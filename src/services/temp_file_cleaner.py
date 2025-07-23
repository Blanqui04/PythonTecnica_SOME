"""
Temporary File Cleaner Service

Aquest servei s'encarrega de netejar fitxers temporals (CSV, JSON, etc.) 
que es generen durant el processament de dades i que ja no són necessaris
un cop s'han carregat a la base de dades.

Versió 2.0: Amb suport per configuració externa i polítiques específiques per projecte.
"""

import os
import time
import glob
import json
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TempFileCleaner:
    """Gestiona la neteja automàtica de fitxers temporals amb configuració avançada"""
    
    def __init__(self, 
                 temp_retention_hours: int = 24,
                 processed_retention_hours: int = 72,
                 exports_retention_hours: int = 48,
                 config_path: str = None):
        """
        Inicialitza el netejador de fitxers temporals
        
        Args:
            temp_retention_hours: Hores que es mantenen els fitxers a data/temp
            processed_retention_hours: Hores que es mantenen els fitxers processats
            exports_retention_hours: Hores que es mantenen els fitxers d'exportació
            config_path: Ruta al fitxer de configuració (opcional)
        """
        self.temp_retention_hours = temp_retention_hours
        self.processed_retention_hours = processed_retention_hours
        self.exports_retention_hours = exports_retention_hours
        
        # Carregar configuració externa si està disponible
        self.config = self._load_config(config_path) if config_path else {}
        
        # Definir directoris a netejar
        self.base_path = Path(__file__).parent.parent.parent
        self.temp_directories = self._get_temp_directories()
    
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuració externa"""
        try:
            full_path = self.base_path / config_path if not os.path.isabs(config_path) else Path(config_path)
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return config_data.get('auto_cleanup_config', {})
            else:
                logger.warning(f"Configuració no trobada: {full_path}")
                return {}
        except Exception as e:
            logger.error(f"Error carregant configuració: {e}")
            return {}
    
    def _get_temp_directories(self) -> Dict:
        """Defineix els directoris a netejar segons configuració"""
        base_config = {
            'temp_processing': {
                'path': self.base_path / 'data' / 'temp' / 'excel_processing',
                'retention_hours': self.temp_retention_hours,
                'description': 'Fitxers temporals de processament Excel'
            },
            'temp_general': {
                'path': self.base_path / 'data' / 'temp',
                'retention_hours': self.temp_retention_hours,
                'description': 'Fitxers temporals generals'
            },
            'processed_exports': {
                'path': self.base_path / 'data' / 'processed' / 'exports',
                'retention_hours': self.exports_retention_hours,
                'description': 'Fitxers d\'exportació processats'
            },
            'processed_datasheets': {
                'path': self.base_path / 'data' / 'processed' / 'datasheets',
                'retention_hours': self.processed_retention_hours,
                'description': 'Fulls de dades processats (conservats més temps)',
                'file_types': ['.csv']  # Només CSV, mantenir JSON més temps
            }
        }
        
        # Aplicar configuració externa si està disponible
        if self.config.get('directories'):
            self._update_directories_from_config()
            
        return base_config
    
    def _update_directories_from_config(self):
        """Actualitza directoris segons configuració externa"""
        try:
            config_dirs = self.config.get('directories', {})
            retention_policies = self.config.get('retention_policies', {})
            
            # Actualitzar rutes des de configuració
            for key, config_path in config_dirs.items():
                if key in ['data_temp', 'data_processed', 'data_exports']:
                    # Actualitzar rutes segons configuració
                    pass
                    
        except Exception as e:
            logger.warning(f"Error aplicant configuració externa: {e}")
    
    def clean_for_project(self, client: str, ref_project: str, immediate: bool = False):
        """
        Neteja fitxers temporals per a un projecte específic
        
        Args:
            client: Nom del client
            ref_project: Referència del projecte
            immediate: Si True, elimina immediatament sense comprovar edat
        """
        cleaned_files = []
        
        try:
            logger.info(f"Netejant fitxers temporals per client '{client}' i projecte '{ref_project}'")
            
            for dir_name, dir_config in self.temp_directories.items():
                dir_path = dir_config['path']
                
                if not dir_path.exists():
                    continue
                
                # Patrons de cerca per aquest client i projecte
                patterns = [
                    f"*{client}*{ref_project}*",
                    f"*{ref_project}*{client}*",
                    f"{ref_project}_*",
                    f"*_{ref_project}.*",
                    f"datasheet_{client}_{ref_project}*"
                ]
                
                for pattern in patterns:
                    files = list(dir_path.glob(pattern))
                    
                    for file_path in files:
                        if self._should_clean_file(file_path, dir_config, immediate):
                            try:
                                # Verificar que és realment un fitxer temporal
                                if self._is_safe_to_delete(file_path, client, ref_project):
                                    file_path.unlink()
                                    cleaned_files.append(str(file_path))
                                    logger.debug(f"Eliminat: {file_path}")
                                else:
                                    logger.debug(f"Saltat per seguretat: {file_path}")
                            except Exception as e:
                                logger.warning(f"No s'ha pogut eliminar {file_path}: {e}")
            
            if cleaned_files:
                logger.info(f"Neteja completada: {len(cleaned_files)} fitxers eliminats")
                for file in cleaned_files:
                    logger.debug(f"  🧹 {file}")
            else:
                logger.debug(f"No s'han trobat fitxers temporals per netejar per {client}/{ref_project}")
                
        except Exception as e:
            logger.error(f"Error durant la neteja per {client}/{ref_project}: {e}")
        
        return cleaned_files
    
    def clean_all_old_files(self):
        """Neteja tots els fitxers antics basant-se en els temps de retenció"""
        cleaned_files = []
        
        try:
            logger.info("Iniciant neteja general de fitxers antics...")
            
            for dir_name, dir_config in self.temp_directories.items():
                dir_path = dir_config['path']
                
                if not dir_path.exists():
                    logger.debug(f"Directori no existeix: {dir_path}")
                    continue
                
                logger.debug(f"Netejant {dir_config['description']}: {dir_path}")
                
                # Obtenir tots els fitxers del directori
                for file_path in dir_path.iterdir():
                    if file_path.is_file():
                        if self._should_clean_file(file_path, dir_config, False):
                            try:
                                file_path.unlink()
                                cleaned_files.append(str(file_path))
                                logger.debug(f"Eliminat fitxer antic: {file_path}")
                            except Exception as e:
                                logger.warning(f"No s'ha pogut eliminar {file_path}: {e}")
            
            if cleaned_files:
                logger.info(f"Neteja general completada: {len(cleaned_files)} fitxers antics eliminats")
            else:
                logger.debug("No s'han trobat fitxers antics per eliminar")
                
        except Exception as e:
            logger.error(f"Error durant la neteja general: {e}")
        
        return cleaned_files
    
    def clean_for_project_universal(self, client: str, ref_project: str, aggressive: bool = False) -> Dict:
        """
        Neteja universal per qualsevol client i projecte amb polítiques intel·ligents
        
        Args:
            client: Nom del client (ex: 'ZF', 'SEAT', 'BMW', etc.)
            ref_project: Referència del projecte
            aggressive: Si True, aplica neteja més agressiva
            
        Returns:
            Dict amb informació sobre la neteja realitzada
        """
        try:
            logger.info(f"Iniciant neteja universal per client '{client}' i projecte '{ref_project}'")
            
            # Detectar tipus de client i aplicar polítiques corresponents
            client_upper = client.upper()
            
            # Configuració segons tipus de client
            if client_upper in ['ZF']:
                # Polítiques per ZF (més agressives)
                policy_config = self.config.get('retention_policies', {}).get('zf_projects', {})
                base_retention = {
                    'temp': policy_config.get('age_minutes_temp', 30) / 60,
                    'processed': policy_config.get('age_hours_processed', 2),
                    'exports': policy_config.get('age_hours_exports', 4)
                }
                logger.info(f"Aplicant polítiques ZF per {client}")
                
            elif client_upper in ['SEAT', 'AUDI', 'VW', 'VOLKSWAGEN']:
                # Polítiques per grup VAG (intermèdies)
                base_retention = {
                    'temp': 45 / 60,     # 45 minuts
                    'processed': 4,      # 4 hores
                    'exports': 8         # 8 hores
                }
                logger.info(f"Aplicant polítiques VAG per {client}")
                
            elif client_upper in ['BMW', 'MINI']:
                # Polítiques per BMW Group (conservadores)
                base_retention = {
                    'temp': 90 / 60,     # 1.5 hores
                    'processed': 8,      # 8 hores
                    'exports': 16        # 16 hores
                }
                logger.info(f"Aplicant polítiques BMW per {client}")
                
            else:
                # Polítiques estàndard per altres clients
                policy_config = self.config.get('retention_policies', {}).get('standard_projects', {})
                base_retention = {
                    'temp': policy_config.get('age_minutes_temp', 120) / 60,
                    'processed': policy_config.get('age_hours_processed', 12),
                    'exports': policy_config.get('age_hours_exports', 48)
                }
                logger.info(f"Aplicant polítiques estàndard per {client}")
            
            # Ajustar per mode agressiu
            if aggressive:
                retention_config = {
                    'temp': base_retention['temp'] / 3,      # Dividir per 3
                    'processed': base_retention['processed'] / 2,  # Dividir per 2
                    'exports': base_retention['exports'] / 2       # Dividir per 2
                }
                logger.info(f"Mode agressiu activat per {client}")
            else:
                retention_config = base_retention
            
            cleaned_files = []
            total_size_freed = 0
            
            # Definir directoris universals
            universal_directories = {
                'temp': self.base_path / 'data' / 'temp',
                'exports': self.base_path / 'data' / 'processed' / 'exports',
                'datasheets': self.base_path / 'data' / 'processed' / 'datasheets',
                'imports': self.base_path / 'data' / 'processed' / 'imports'
            }
            
            # Patrons universals per buscar fitxers
            universal_patterns = [
                f"*{client}*{ref_project}*",
                f"*{ref_project}*{client}*",
                f"{ref_project}_*",
                f"*_{ref_project}_*",
                f"*_{ref_project}.*",
                f"datasheet_{client}_{ref_project}*",
                f"{client}_{ref_project}*",
                f"export_{client}_{ref_project}*"
            ]
            
            # Netejar cada directori
            for dir_type, dir_path in universal_directories.items():
                if not dir_path.exists():
                    continue
                    
                retention_hours = retention_config.get(dir_type, retention_config.get('temp', 1))
                
                for pattern in universal_patterns:
                    for file_path in dir_path.glob(pattern):
                        if file_path.is_file():
                            try:
                                # Verificar edat del fitxer
                                file_age_hours = self._get_file_age_hours(file_path)
                                file_size = file_path.stat().st_size
                                
                                # Verificar si cal eliminar
                                if file_age_hours > retention_hours and self._is_safe_to_delete_universal(file_path, client, ref_project):
                                    file_path.unlink()
                                    cleaned_files.append(str(file_path))
                                    total_size_freed += file_size
                                    logger.debug(f"Universal: Eliminat {file_path} (edat: {file_age_hours:.1f}h)")
                                    
                            except Exception as e:
                                logger.warning(f"Error eliminant fitxer universal {file_path}: {e}")
            
            # També netejar fitxers del sistema temporal
            self._clean_system_temp_universal(client, ref_project, cleaned_files)
            
            result = {
                'success': True,
                'client': client,
                'project': ref_project,
                'files_cleaned': len(cleaned_files),
                'space_freed': self._format_file_size(total_size_freed),
                'aggressive_mode': aggressive,
                'policy_applied': client_upper if client_upper in ['ZF'] else 'standard',
                'summary': f"Universal: {len(cleaned_files)} fitxers netejats per {client}/{ref_project}"
            }
            
            logger.info(f"Neteja universal completada: {result['summary']}")
            return result
            
        except Exception as e:
            logger.error(f"Error en neteja universal: {e}")
            return {
                'success': False,
                'error': str(e),
                'client': client,
                'project': ref_project
            }
    
    def _is_safe_to_delete_universal(self, file_path: Path, client: str, ref_project: str) -> bool:
        """Verificacions de seguretat universals abans d'eliminar fitxers"""
        try:
            filename = file_path.name.lower()
            
            # Patrons que mai s'han d'eliminar
            protected_patterns = [
                'backup', 'important', 'config', 'master', 'template'
            ]
            
            for pattern in protected_patterns:
                if pattern in filename:
                    logger.debug(f"Fitxer protegit, no s'elimina: {file_path}")
                    return False
            
            # Verificar que conté referències al client/projecte
            if client.lower() in filename or ref_project.lower() in filename:
                return True
            
            # Fitxers temporals genèrics
            if filename.endswith(('.tmp', '.temp', '_temp.csv')):
                return True
                
            logger.debug(f"Fitxer no coincideix amb patrons segurs: {file_path}")
            return False
            
        except Exception as e:
            logger.warning(f"Error verificant seguretat per {file_path}: {e}")
            return False
    
    def _clean_system_temp_universal(self, client: str, ref_project: str, cleaned_files: List[str]):
        """Neteja fitxers del directori temporal del sistema per qualsevol client"""
        try:
            system_temp = Path(os.environ.get('TEMP', tempfile.gettempdir()))
            
            # Patrons per diferents clients
            temp_patterns = [
                f"pythontecnica_*{client}*{ref_project}*",
                f"pythontecnica_*{ref_project}*",
                f"{client.lower()}_*{ref_project}*",
                f"*{ref_project}*.tmp",
                f"datasheet_*{client}*{ref_project}*"
            ]
            
            for pattern in temp_patterns:
                for temp_file in system_temp.glob(pattern):
                    if temp_file.is_file():
                        try:
                            # Verificar edat mínima (5 minuts)
                            file_age_hours = self._get_file_age_hours(temp_file)
                            if file_age_hours > (5/60):  # 5 minuts en hores
                                temp_file.unlink()
                                cleaned_files.append(str(temp_file))
                                logger.debug(f"Universal: Eliminat fitxer temporal del sistema: {temp_file}")
                        except Exception as e:
                            logger.warning(f"No s'ha pogut eliminar {temp_file}: {e}")
                            
        except Exception as e:
            logger.warning(f"Error netejant temporals del sistema per {client}/{ref_project}: {e}")

    def clean_for_zf_project(self, ref_project: str, aggressive: bool = False) -> Dict:
        """
        Neteja específica per projectes ZF amb polítiques personalitzades
        
        Args:
            ref_project: Referència del projecte ZF (ex: '004938000151')
            aggressive: Si True, aplica neteja més agressiva
            
        Returns:
            Dict amb informació sobre la neteja realitzada
        """
        try:
            logger.info(f"Iniciant neteja específica ZF per projecte: {ref_project}")
            
            # Configuració específica per ZF
            zf_config = self.config.get('retention_policies', {}).get('zf_projects', {})
            
            if aggressive:
                retention_config = {
                    'temp': 10,      # 10 minuts
                    'processed': 1,  # 1 hora
                    'exports': 2     # 2 hores
                }
                logger.info("Mode agressiu activat per ZF")
            else:
                retention_config = {
                    'temp': zf_config.get('age_minutes_temp', 30) / 60,  # Convertir a hores
                    'processed': zf_config.get('age_hours_processed', 2),
                    'exports': zf_config.get('age_hours_exports', 4)
                }
            
            cleaned_files = []
            total_size_freed = 0
            
            # Definir directoris específics per ZF
            zf_directories = {
                'temp': self.base_path / 'data' / 'temp',
                'exports': self.base_path / 'data' / 'processed' / 'exports',
                'datasheets': self.base_path / 'data' / 'processed' / 'datasheets'
            }
            
            # Patrons específics per ZF
            zf_patterns = [
                f"*{ref_project}*",
                f"*ZF*{ref_project}*",
                f"datasheet_ZF_{ref_project}*",
                f"{ref_project}_*.csv",
                f"*_{ref_project}_*.csv"
            ]
            
            for dir_type, dir_path in zf_directories.items():
                if not dir_path.exists():
                    continue
                    
                retention_hours = retention_config.get(dir_type, 24)
                
                for pattern in zf_patterns:
                    for file_path in dir_path.glob(pattern):
                        if file_path.is_file():
                            try:
                                # Verificar edat del fitxer
                                file_age_hours = self._get_file_age_hours(file_path)
                                file_size = file_path.stat().st_size
                                
                                if file_age_hours > retention_hours:
                                    file_path.unlink()
                                    cleaned_files.append(str(file_path))
                                    total_size_freed += file_size
                                    logger.debug(f"ZF: Eliminat {file_path} (edat: {file_age_hours:.1f}h)")
                                    
                            except Exception as e:
                                logger.warning(f"Error eliminant fitxer ZF {file_path}: {e}")
            
            # També netejar fitxers del sistema temporal
            self._clean_system_temp_for_zf(ref_project, cleaned_files)
            
            result = {
                'success': True,
                'project': ref_project,
                'files_cleaned': len(cleaned_files),
                'space_freed': self._format_file_size(total_size_freed),
                'aggressive_mode': aggressive,
                'summary': f"ZF: {len(cleaned_files)} fitxers netejats per {ref_project}"
            }
            
            logger.info(f"Neteja ZF completada: {result['summary']}")
            return result
            
        except Exception as e:
            logger.error(f"Error en neteja específica ZF: {e}")
            return {
                'success': False,
                'error': str(e),
                'project': ref_project
            }
    
    def _clean_system_temp_for_zf(self, ref_project: str, cleaned_files: List[str]):
        """Neteja fitxers ZF del directori temporal del sistema"""
        try:
            system_temp = Path(os.environ.get('TEMP', tempfile.gettempdir()))
            zf_temp_patterns = [
                f"pythontecnica_*{ref_project}*",
                f"zf_*{ref_project}*",
                f"*{ref_project}*.tmp"
            ]
            
            for pattern in zf_temp_patterns:
                for temp_file in system_temp.glob(pattern):
                    if temp_file.is_file():
                        try:
                            temp_file.unlink()
                            cleaned_files.append(str(temp_file))
                            logger.debug(f"ZF: Eliminat fitxer temporal del sistema: {temp_file}")
                        except Exception as e:
                            logger.warning(f"No s'ha pogut eliminar {temp_file}: {e}")
                            
        except Exception as e:
            logger.warning(f"Error netejant temporals del sistema per ZF: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formata la mida del fitxer en unitats llegibles"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _should_clean_file(self, file_path: Path, dir_config: dict, immediate: bool) -> bool:
        """Determina si un fitxer s'ha d'eliminar"""
        try:
            # Si és eliminació immediata, comprova només tipus de fitxer
            if immediate:
                return self._is_cleanable_file_type(file_path, dir_config)
            
            # Comprova l'edat del fitxer
            file_age_hours = self._get_file_age_hours(file_path)
            retention_hours = dir_config['retention_hours']
            
            # Comprova tipus de fitxer si està especificat
            if not self._is_cleanable_file_type(file_path, dir_config):
                return False
            
            return file_age_hours > retention_hours
            
        except Exception as e:
            logger.warning(f"Error avaluant si eliminar {file_path}: {e}")
            return False
    
    def _is_cleanable_file_type(self, file_path: Path, dir_config: dict) -> bool:
        """Comprova si el tipus de fitxer es pot netejar"""
        # Si està especificat tipus de fitxers, només neteja aquests
        if 'file_types' in dir_config:
            return file_path.suffix.lower() in [ft.lower() for ft in dir_config['file_types']]
        
        # Tipus de fitxers temporals que és segur eliminar
        cleanable_extensions = {'.csv', '.json', '.xlsx', '.xls', '.tmp', '.temp', '.log'}
        return file_path.suffix.lower() in cleanable_extensions
    
    def _get_file_age_hours(self, file_path: Path) -> float:
        """Calcula l'edat del fitxer en hores"""
        try:
            file_mtime = file_path.stat().st_mtime
            current_time = time.time()
            age_seconds = current_time - file_mtime
            return age_seconds / 3600  # Convertir a hores
        except Exception:
            return 0  # Si no es pot calcular, assumeix que és nou
    
    def _is_safe_to_delete(self, file_path: Path, client: str, ref_project: str) -> bool:
        """Verificacions de seguretat abans d'eliminar un fitxer"""
        try:
            # No eliminar si està en ús
            if self._is_file_in_use(file_path):
                return False
            
            # Verificar que el nom del fitxer conté realment els identificadors del projecte
            file_name = file_path.name.lower()
            client_lower = client.lower()
            ref_project_lower = ref_project.lower()
            
            # Ha de contenir almenys un dels identificadors
            contains_identifier = (
                client_lower in file_name or 
                ref_project_lower in file_name or
                any(part in file_name for part in ref_project_lower.split('_'))
            )
            
            return contains_identifier
            
        except Exception:
            return False  # Si hi ha dubtes, no eliminar
    
    def _is_file_in_use(self, file_path: Path) -> bool:
        """Comprova si un fitxer està en ús"""
        try:
            # Intentar obrir en mode exclusiu
            with open(file_path, 'r+b'):
                pass
            return False
        except (IOError, OSError):
            return True  # Probablement en ús
    
    def get_cleanup_summary(self) -> Dict:
        """Obté un resum de l'estat dels directoris temporals"""
        summary = {}
        
        for dir_name, dir_config in self.temp_directories.items():
            dir_path = dir_config['path']
            
            if not dir_path.exists():
                summary[dir_name] = {
                    'exists': False,
                    'file_count': 0,
                    'total_size_mb': 0
                }
                continue
            
            files = list(dir_path.iterdir())
            file_count = len([f for f in files if f.is_file()])
            
            total_size = 0
            for file in files:
                if file.is_file():
                    try:
                        total_size += file.stat().st_size
                    except:
                        pass
            
            summary[dir_name] = {
                'exists': True,
                'path': str(dir_path),
                'description': dir_config['description'],
                'file_count': file_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'retention_hours': dir_config['retention_hours']
            }
        
        return summary
