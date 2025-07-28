#!/usr/bin/env python3
"""
Servei de sincronització automàtica de dades del GOMPC
Aquest servei s'executa a l'inici de l'aplicació per sincronitzar 
automàticament les dades dels CSV del GOMPC amb la base de dades.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

class GompcSyncService:
    """
    Servei per sincronitzar automàticament les dades del GOMPC amb la base de dades
    """
    
    def __init__(self):
        """Inicialitza el servei de sincronització"""
        self.logger = self._setup_logger()
        self.network_scanner = None
        self.sync_stats = {
            'start_time': None,
            'end_time': None,
            'csv_files_processed': 0,
            'records_inserted': 0,
            'errors': [],
            'success': False
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logger = logging.getLogger('GompcDataSync')
        logger.setLevel(logging.INFO)
        
        # Handler per consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format dels logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Evitar duplicats
        if not logger.handlers:
            logger.addHandler(console_handler)
        
        return logger
    
    def sync_data_on_startup(self) -> Dict[str, Any]:
        """
        Executa la sincronització completa de dades a l'inici de l'aplicació
        
        Returns:
            dict: Estadístiques de la sincronització
        """
        self.sync_stats['start_time'] = datetime.now()
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("INICIANT SINCRONITZACIÓ AUTOMÀTICA DE DADES GOMPC")
            self.logger.info("=" * 60)
            
            # Pas 1: Inicialitzar el scanner
            if not self._initialize_scanner():
                return self._finalize_sync(False, "Error inicialitzant scanner")
            
            # Pas 2: Verificar accés a la xarxa
            if not self._verify_network_access():
                return self._finalize_sync(False, "Error accedint a la xarxa GOMPC")
            
            # Pas 3: Processar fitxers CSV
            if not self._process_csv_files():
                return self._finalize_sync(False, "Error processant fitxers CSV")
            
            # Pas 4: Verificar connexió BBDD
            if not self._verify_database_connection():
                return self._finalize_sync(False, "Error connectant a la base de dades")
            
            # Pas 5: Inserir dades a la BBDD
            if not self._insert_data_to_database():
                return self._finalize_sync(False, "Error inserint dades a la BBDD")
            
            return self._finalize_sync(True, "Sincronització completada amb èxit")
            
        except Exception as e:
            error_msg = f"Error durant la sincronització: {e}"
            self.logger.error(error_msg)
            return self._finalize_sync(False, error_msg)
    
    def _initialize_scanner(self) -> bool:
        """Inicialitza el scanner de xarxa"""
        try:
            from src.services.network_scanner import NetworkScanner
            self.network_scanner = NetworkScanner()
            self.logger.info("✅ Scanner de xarxa inicialitzat")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error inicialitzant scanner: {e}")
            self.sync_stats['errors'].append(str(e))
            return False
    
    def _verify_network_access(self) -> bool:
        """Verifica l'accés al directori de xarxa GOMPC"""
        try:
            network_path = r"\\gompcnou\KIOSK\results"
            if os.path.exists(network_path):
                clients = os.listdir(network_path)
                filtered_clients = [c for c in clients if not c.endswith('.ginspect')]
                self.logger.info(f"✅ Accés a xarxa verificat: {len(filtered_clients)} clients trobats")
                return True
            else:
                self.logger.error("❌ No es pot accedir al directori GOMPC")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error verificant accés de xarxa: {e}")
            self.sync_stats['errors'].append(str(e))
            return False
    
    def _process_csv_files(self) -> bool:
        """Processa tots els fitxers CSV del GOMPC"""
        try:
            self.logger.info("📋 Processant fitxers CSV...")
            
            # Processar tots els CSV
            self.network_scanner.process_all_csv_files()
            
            if self.network_scanner.global_dataset is not None and not self.network_scanner.global_dataset.empty:
                total_records = len(self.network_scanner.global_dataset)
                self.sync_stats['csv_files_processed'] = total_records
                self.logger.info(f"✅ Processament CSV completat: {total_records} registres")
                return True
            else:
                self.logger.error("❌ Dataset global buit després del processament")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error processant CSV: {e}")
            self.sync_stats['errors'].append(str(e))
            return False
    
    def _verify_database_connection(self) -> bool:
        """Verifica la connexió a la base de dades amb suport Unicode millorat"""
        try:
            # Carregar configuració BBDD
            db_config = self.network_scanner.load_db_config()
            if not db_config:
                self.logger.error("❌ No es pot carregar configuració BBDD")
                return False
            
            # Test de connexió amb encoding UTF-8
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            adapter = QualityMeasurementDBAdapter(db_config)
            
            if adapter.connect():
                # Verificar que l'encoding és correcte
                with adapter.connection.cursor() as cursor:
                    cursor.execute("SHOW client_encoding")
                    encoding = cursor.fetchone()[0]
                    self.logger.info(f"✅ Connexió BBDD establerta amb encoding: {encoding}")
                    
                    # Verificar l'esquema de la taula
                    cursor.execute("""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'mesuresqualitat' AND column_name = 'actual'
                    """)
                    result = cursor.fetchone()
                    if result:
                        actual_type = result[0]
                        self.logger.info(f"✅ Tipus de dada 'actual': {actual_type}")
                    
                adapter.close()
                return True
            else:
                self.logger.error("❌ No es pot connectar a la base de dades")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verificant connexió BBDD: {e}")
            self.sync_stats['errors'].append(str(e))
            return False
    
    def _insert_data_to_database(self) -> bool:
        """Insereix les dades processades a la base de dades"""
        try:
            self.logger.info("💾 Inserint dades a la base de dades...")
            
            result = self.network_scanner.insert_dataset_to_database()
            
            if result['success']:
                self.sync_stats['records_inserted'] = result.get('records_inserted', 0)
                self.logger.info(f"✅ Inserció completada: {self.sync_stats['records_inserted']} registres")
                return True
            else:
                error_msg = result.get('error', 'Error desconegut')
                self.logger.error(f"❌ Error durant la inserció: {error_msg}")
                self.sync_stats['errors'].append(error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error inserint dades: {e}")
            self.sync_stats['errors'].append(str(e))
            return False
    
    def _finalize_sync(self, success: bool, message: str) -> Dict[str, Any]:
        """Finalitza la sincronització i retorna les estadístiques"""
        self.sync_stats['end_time'] = datetime.now()
        self.sync_stats['success'] = success
        
        duration = (self.sync_stats['end_time'] - self.sync_stats['start_time']).total_seconds()
        
        self.logger.info("=" * 60)
        if success:
            self.logger.info("🎉 SINCRONITZACIÓ COMPLETADA AMB ÈXIT")
        else:
            self.logger.info("❌ SINCRONITZACIÓ FALLIDA")
        
        self.logger.info(f"📊 Temps total: {duration:.2f} segons")
        self.logger.info(f"📋 Fitxers processats: {self.sync_stats['csv_files_processed']}")
        self.logger.info(f"💾 Registres inserits: {self.sync_stats['records_inserted']}")
        
        if self.sync_stats['errors']:
            self.logger.info(f"⚠️ Errors: {len(self.sync_stats['errors'])}")
        
        self.logger.info("=" * 60)
        
        return {
            'success': success,
            'message': message,
            'duration_seconds': duration,
            'csv_files_processed': self.sync_stats['csv_files_processed'],
            'records_inserted': self.sync_stats['records_inserted'],
            'errors': self.sync_stats['errors'],
            'start_time': self.sync_stats['start_time'],
            'end_time': self.sync_stats['end_time']
        }
    
    def quick_verification(self) -> Dict[str, Any]:
        """
        Verificació ràpida per comprovar l'estat de les dades a la BBDD
        
        Returns:
            dict: Informació sobre l'estat actual de la BBDD
        """
        try:
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
            
            # Carregar configuració
            from src.services.network_scanner import NetworkScanner
            scanner = NetworkScanner()
            db_config = scanner.load_db_config()
            
            if not db_config:
                return {'success': False, 'error': 'No es pot carregar configuració BBDD'}
            
            # Connectar i verificar
            adapter = QualityMeasurementDBAdapter(db_config)
            
            if adapter.connect():
                with adapter.connection.cursor() as cursor:
                    # Comptar registres
                    cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                    total_records = cursor.fetchone()[0]
                    
                    # Obtenir últim registre
                    cursor.execute("""
                        SELECT created_at 
                        FROM mesuresqualitat 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)
                    last_record = cursor.fetchone()
                    last_insert = last_record[0] if last_record else None
                    
                adapter.close()
                
                return {
                    'success': True,
                    'total_records': total_records,
                    'last_insert': last_insert,
                    'database_active': True
                }
            else:
                return {'success': False, 'error': 'No es pot connectar a la BBDD'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
