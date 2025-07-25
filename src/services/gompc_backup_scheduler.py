#!/usr/bin/env python3
"""
Servei de backup automàtic per sincronitzar dades GOMPC cada 24 hores
"""

import os
import sys
import time
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Afegir src al path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from services.gompc_sync_service import GompcSyncService
import logging

class GompcBackupScheduler:
    """Programador de backup automàtic per dades GOMPC"""
    
    def __init__(self):
        self.sync_service = GompcSyncService()
        self.is_running = False
        self.backup_thread = None
        
        # Configurar logging específic per backups
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configura el logger per als backups"""
        logger = logging.getLogger('gompc_backup')
        logger.setLevel(logging.INFO)
        
        # Crear handler per fitxer de log
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "gompc_backup.log")
        file_handler.setLevel(logging.INFO)
        
        # Crear handler per consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Afegir handlers al logger
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def perform_backup(self):
        """Executa el backup de dades GOMPC"""
        self.logger.info("=" * 60)
        self.logger.info("INICIANT BACKUP AUTOMÀTIC DADES GOMPC")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Executar sincronització
            result = self.sync_service.sync_data_on_startup()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result['success']:
                self.logger.info(f"✅ Backup completat exitosament!")
                self.logger.info(f"   📋 Fitxers processats: {result.get('csv_files_processed', 0)}")
                self.logger.info(f"   💾 Registres inserits: {result.get('records_inserted', 0)}")
                self.logger.info(f"   ⏱️ Durada: {duration:.2f}s")
                self.logger.info(f"   🕐 Propera execució: {datetime.now() + timedelta(hours=24)}")
            else:
                self.logger.error(f"❌ Error en el backup: {result.get('message', 'Error desconegut')}")
                if result.get('errors'):
                    for error in result['errors'][:5]:
                        self.logger.error(f"   - {error}")
        
        except Exception as e:
            self.logger.error(f"❌ Error crític durant el backup: {e}")
            
        self.logger.info("=" * 60)
    
    def start_scheduler(self):
        """Inicia el programador de backups"""
        if self.is_running:
            self.logger.warning("El programador ja està en funcionament")
            return
        
        self.logger.info("Iniciant programador de backup GOMPC...")
        
        # Programar backup cada 24 hores
        schedule.every(24).hours.do(self.perform_backup)
        
        # Executar primer backup immediatament (opcional)
        # self.perform_backup()
        
        self.is_running = True
        
        # Crear thread per executar el programador
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Comprovar cada minut
        
        self.backup_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.backup_thread.start()
        
        self.logger.info(f"✅ Programador iniciat. Primer backup programat per: {datetime.now() + timedelta(hours=24)}")
    
    def stop_scheduler(self):
        """Atura el programador de backups"""
        if not self.is_running:
            return
            
        self.logger.info("Aturant programador de backup GOMPC...")
        self.is_running = False
        schedule.clear()
        
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=5)
        
        self.logger.info("✅ Programador aturat")
    
    def get_next_backup_time(self):
        """Retorna la data/hora del proper backup programat"""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def force_backup_now(self):
        """Força un backup immediat"""
        self.logger.info("🔥 BACKUP FORÇAT - Executant ara...")
        self.perform_backup()


if __name__ == "__main__":
    """Executar com a servei independent"""
    print("Iniciant servei de backup GOMPC...")
    
    scheduler = GompcBackupScheduler()
    
    try:
        # Iniciar programador
        scheduler.start_scheduler()
        
        # Mantenir el servei en funcionament
        print("Servei de backup en funcionament. Pressiona Ctrl+C per aturar.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nAturant servei de backup...")
        scheduler.stop_scheduler()
        print("Servei aturat.")
    except Exception as e:
        print(f"Error en el servei: {e}")
        scheduler.stop_scheduler()
