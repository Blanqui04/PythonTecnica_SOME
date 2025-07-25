"""
Programador de backup automàtic per Scanner Projectes
Executa sincronització cada 24 hores en segon pla
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from src.services.project_sync_service import ProjectSyncService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectBackupScheduler:
    """
    Programador de backup automàtic per Scanner Projectes
    Executa sincronització cada 24 hores sense bloquejar l'aplicació
    """
    
    def __init__(self, interval_hours: int = 24):
        """
        Inicialitza el programador
        
        Args:
            interval_hours: Interval en hores entre sincronitzacions (default: 24h)
        """
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 3600
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.sync_service = ProjectSyncService()
        self.last_execution: Optional[datetime] = None
        self.next_execution: Optional[datetime] = None
        
        logger.info(f"ProjectBackupScheduler inicialitzat: interval {interval_hours}h")
    
    def start_scheduler(self) -> bool:
        """
        Inicia el programador en un thread separat
        
        Returns:
            bool: True si s'ha iniciat correctament
        """
        if self.running:
            logger.warning("El programador ja està en execució")
            return False
        
        try:
            self.running = True
            self.next_execution = datetime.now() + timedelta(hours=self.interval_hours)
            
            # Crear i iniciar thread
            self.thread = threading.Thread(
                target=self._scheduler_loop,
                name="ProjectBackupScheduler",
                daemon=True  # Thread daemon per no bloquejar l'aplicació
            )
            self.thread.start()
            
            logger.info(f"Programador Scanner Projectes iniciat. Propera execució: {self.next_execution}")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciant programador Scanner Projectes: {e}")
            self.running = False
            return False
    
    def stop_scheduler(self) -> bool:
        """
        Atura el programador
        
        Returns:
            bool: True si s'ha aturat correctament
        """
        if not self.running:
            logger.info("El programador ja està aturat")
            return True
        
        try:
            self.running = False
            
            # Esperar que el thread acabi (màxim 5 segons)
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)
            
            logger.info("Programador Scanner Projectes aturat")
            return True
            
        except Exception as e:
            logger.error(f"Error aturant programador Scanner Projectes: {e}")
            return False
    
    def _scheduler_loop(self):
        """
        Bucle principal del programador (executa en thread separat)
        """
        logger.info("Bucle programador Scanner Projectes iniciat")
        
        while self.running:
            try:
                # Esperar fins la propera execució (en intervals de 60 segons per poder aturar)
                while self.running and datetime.now() < self.next_execution:
                    time.sleep(60)  # Revisar cada minut
                
                if not self.running:
                    break
                
                # Executar sincronització
                logger.info("=== INICIANT BACKUP AUTOMÀTIC SCANNER PROJECTES ===")
                self._execute_backup()
                
                # Programar propera execució
                self.next_execution = datetime.now() + timedelta(hours=self.interval_hours)
                logger.info(f"Propera execució programada per: {self.next_execution}")
                
            except Exception as e:
                logger.error(f"Error en bucle programador Scanner Projectes: {e}")
                # En cas d'error, esperar 1 hora abans de tornar a intentar
                time.sleep(3600)
        
        logger.info("Bucle programador Scanner Projectes finalitzat")
    
    def _execute_backup(self):
        """
        Executa la sincronització de backup
        """
        try:
            self.last_execution = datetime.now()
            start_time = time.time()
            
            logger.info("Iniciant sincronització Scanner Projectes...")
            
            # Executar sincronització
            result = self.sync_service.sync_project_data()
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result['success']:
                logger.info("=== BACKUP SCANNER PROJECTES COMPLETAT AMB ÈXIT ===")
                logger.info(f"📋 CSV processats: {result.get('total_csv_processed', 0)}")
                logger.info(f"💾 Registres inserits: {result.get('total_records_inserted', 0)}")
                logger.info(f"⏱️ Temps: {duration:.2f}s")
                logger.info(f"🖥️ Màquina: {result.get('maquina_value', 'N/A')}")
            else:
                logger.error(f"=== BACKUP SCANNER PROJECTES FALLIT ===")
                logger.error(f"Error: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error executant backup Scanner Projectes: {e}")
    
    def get_status(self) -> dict:
        """
        Retorna l'estat actual del programador
        
        Returns:
            dict: Informació d'estat
        """
        return {
            'running': self.running,
            'interval_hours': self.interval_hours,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'thread_alive': self.thread.is_alive() if self.thread else False
        }
    
    def get_next_backup_time(self) -> Optional[str]:
        """
        Retorna la propera hora de backup formatada
        
        Returns:
            str: Hora formatada o None
        """
        if self.next_execution:
            return self.next_execution.strftime("%d/%m/%Y %H:%M:%S")
        return None
    
    def force_backup_now(self) -> dict:
        """
        Força una execució immediata del backup (en thread separat)
        
        Returns:
            dict: Resultat de l'execució
        """
        if not self.running:
            return {
                'success': False,
                'error': 'El programador no està en execució'
            }
        
        try:
            logger.info("=== FORÇANT BACKUP IMMEDIAT SCANNER PROJECTES ===")
            
            # Executar en thread separat per no bloquejar
            backup_thread = threading.Thread(
                target=self._execute_backup,
                name="ForceProjectBackup",
                daemon=True
            )
            backup_thread.start()
            
            return {
                'success': True,
                'message': 'Backup forçat iniciat en segon pla'
            }
            
        except Exception as e:
            logger.error(f"Error forçant backup Scanner Projectes: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Funció de test per al programador"""
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print('\nAturant programador...')
        if scheduler:
            scheduler.stop_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Crear i iniciar programador amb interval curt per testing (1 minut)
    scheduler = ProjectBackupScheduler(interval_hours=0.02)  # ~1 minut per testing
    
    if scheduler.start_scheduler():
        print("Programador Scanner Projectes iniciat. Ctrl+C per aturar.")
        
        try:
            while True:
                status = scheduler.get_status()
                print(f"Estat: {status}")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nAturant...")
            scheduler.stop_scheduler()
    else:
        print("Error iniciant programador Scanner Projectes")


if __name__ == "__main__":
    main()
