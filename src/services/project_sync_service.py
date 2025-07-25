#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Project Sync Service
Servei de sincronització per Scanner Projectes del path \\gompc\kiosk

Versió 1.0: Sincronització automàtica de dades del Scanner Projectes
Basat en GompcSyncService però adaptat per \\gompc\kiosk

Autor: Sistema Automàtic
Data: Desembre 2024
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional

from .project_scanner import ProjectScanner

# Configurar logger
logger = logging.getLogger(__name__)

class ProjectSyncService:
    r"""
    Servei de sincronització per Scanner Projectes
    Gestiona la sincronització automàtica de dades del path \\gompc\kiosk
    """
    
    def __init__(self):
        """Inicialitzar el servei de sincronització"""
        self.project_scanner = ProjectScanner()
        logger.info("Project Sync Service inicialitzat")
    
    def sync_project_data(self) -> Dict:
        """
        Sincronitza les dades del Scanner Projectes
        
        Returns:
            dict: Resultat de la sincronització
        """
        try:
            logger.info("=== Iniciant sincronització de Scanner Projectes ===")
            start_time = datetime.now()
            
            # Verificar accés al path
            if not self._check_project_path_access():
                return {
                    'success': False,
                    'error': 'No es pot accedir al path del Scanner Projectes',
                    'timestamp': start_time
                }
            
            # Executar processament complet
            result = self.project_scanner.process_and_save_to_database()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Afegir informació temporal
            result.update({
                'sync_start': start_time,
                'sync_end': end_time,
                'duration_seconds': duration,
                'service_type': 'Scanner Projectes'
            })
            
            if result['success']:
                logger.info(f"=== Sincronització Scanner Projectes COMPLETADA en {duration:.1f}s ===")
                logger.info(f"CSV processats: {result.get('total_csv_processed', 0)}")
                logger.info(f"Registres inserits: {result.get('total_records_inserted', 0)}")
            else:
                logger.error(f"=== Sincronització Scanner Projectes FALLIDA: {result.get('error', 'Unknown')} ===")
            
            return result
            
        except Exception as e:
            error_msg = f"Error en sincronització Scanner Projectes: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now(),
                'service_type': 'Scanner Projectes'
            }
    
    def _check_project_path_access(self) -> bool:
        """
        Verifica l'accés al path del Scanner Projectes
        
        Returns:
            bool: True si el path és accessible, False altrament
        """
        try:
            project_path = self.project_scanner.project_path
            
            if not os.path.exists(project_path):
                logger.error(f"El path del Scanner Projectes no existeix: {project_path}")
                return False
            
            if not os.access(project_path, os.R_OK):
                logger.error(f"No hi ha permisos de lectura al path: {project_path}")
                return False
            
            logger.info(f"Accés al path del Scanner Projectes verificat: {project_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error verificant accés al path: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """
        Obté l'estat del servei de sincronització
        
        Returns:
            dict: Estat actual del servei
        """
        try:
            return {
                'service_name': 'Project Sync Service',
                'scanner_type': 'Scanner Projectes',
                'project_path': self.project_scanner.project_path,
                'maquina_value': self.project_scanner.MAQUINA_VALUE,
                'path_accessible': self._check_project_path_access(),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error obtenint estat del servei: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def test_connection(self) -> Dict:
        """
        Prova la connexió i funcionalitat bàsica
        
        Returns:
            dict: Resultat de la prova
        """
        try:
            logger.info("Provant connexió del Scanner Projectes...")
            
            # Verificar accés al path
            path_ok = self._check_project_path_access()
            
            # Escanejar projectes sense processar
            scan_result = self.project_scanner.scan_all_projects_and_references()
            
            # Verificar configuració de BBDD
            db_config = self.project_scanner.load_db_config()
            db_config_ok = db_config is not None
            
            result = {
                'success': path_ok and scan_result['success'] and db_config_ok,
                'path_accessible': path_ok,
                'scan_successful': scan_result['success'],
                'db_config_loaded': db_config_ok,
                'projects_found': scan_result.get('total_projects', 0) if scan_result['success'] else 0,
                'timestamp': datetime.now(),
                'service_type': 'Scanner Projectes'
            }
            
            if result['success']:
                logger.info("Prova de connexió Scanner Projectes: ÈXIT")
            else:
                logger.warning("Prova de connexió Scanner Projectes: PROBLEMES DETECTATS")
            
            return result
            
        except Exception as e:
            error_msg = f"Error en prova de connexió: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now(),
                'service_type': 'Scanner Projectes'
            }


def main():
    """Funció principal per testing"""
    try:
        # Crear instància del servei
        sync_service = ProjectSyncService()
        
        print("\n" + "="*60)
        print("PROJECT SYNC SERVICE - TEST")
        print("="*60)
        
        # Provar connexió
        print("\n1. Provant connexió...")
        test_result = sync_service.test_connection()
        
        if test_result['success']:
            print(f"✅ Connexió OK - {test_result['projects_found']} projectes trobats")
            
            # Executar sincronització
            print("\n2. Executant sincronització...")
            sync_result = sync_service.sync_project_data()
            
            if sync_result['success']:
                print(f"✅ Sincronització COMPLETADA!")
                print(f"📁 CSV processats: {sync_result.get('total_csv_processed', 0)}")
                print(f"💾 Registres inserits: {sync_result.get('total_records_inserted', 0)}")
                print(f"⏱️  Durada: {sync_result.get('duration_seconds', 0):.1f}s")
                print(f"🖥️  Màquina: {sync_result.get('maquina_value', 'N/A')}")
            else:
                print(f"❌ Error en sincronització: {sync_result.get('error', 'Unknown')}")
        else:
            print(f"❌ Error en connexió: {test_result.get('error', 'Unknown')}")
            print(f"   - Path accessible: {test_result.get('path_accessible', False)}")
            print(f"   - Scan OK: {test_result.get('scan_successful', False)}")
            print(f"   - DB Config OK: {test_result.get('db_config_loaded', False)}")
        
        # Mostrar estat
        print("\n3. Estat del servei:")
        status = sync_service.get_sync_status()
        print(f"   Service: {status.get('service_name', 'N/A')}")
        print(f"   Scanner: {status.get('scanner_type', 'N/A')}")
        print(f"   Path: {status.get('project_path', 'N/A')}")
        print(f"   Accessible: {status.get('path_accessible', False)}")
        
        print("="*60)
        
    except Exception as e:
        print(f"Error executant Project Sync Service: {e}")


if __name__ == "__main__":
    main()
