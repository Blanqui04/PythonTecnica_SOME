#!/usr/bin/env python3
"""
Servei de Backup Automàtic GOMPC

Aquest script executa només el servei de backup automàtic cada 24 hores
sense iniciar l'aplicació GUI principal.
"""

import sys
import os
import signal
import time
from pathlib import Path

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.services.gompc_backup_scheduler import GompcBackupScheduler

# Variable global pel scheduler
scheduler = None

def signal_handler(signum, frame):
    """Gestiona les senyals del sistema per aturar el servei de forma neta"""
    global scheduler
    print("\n🛑 Rebuda senyal d'aturada...")
    
    if scheduler:
        try:
            scheduler.stop_scheduler()
            print("✅ Backup scheduler aturat correctament.")
        except Exception as e:
            print(f"❌ Error aturant scheduler: {e}")
    
    print("👋 Servei de backup finalitzat.")
    sys.exit(0)

def start_backup_service():
    """Inicia el servei de backup automàtic"""
    global scheduler
    
    try:
        print("\n" + "=" * 60)
        print("SERVEI DE BACKUP AUTOMÀTIC GOMPC")
        print("=" * 60)
        print("🚀 Iniciant servei de backup cada 24 hores...")
        
        scheduler = GompcBackupScheduler()
        scheduler.start_scheduler()
        
        next_backup = scheduler.get_next_backup_time()
        if next_backup:
            print(f"✅ Servei de backup configurat i executant-se")
            print(f"   🕐 Propera execució: {next_backup}")
            print(f"   🔄 Freqüència: Cada 24 hores")
            print(f"   🛑 Per aturar: Ctrl+C")
        
        print("=" * 60)
        print("📊 SERVEI ACTIU - Executant en segon pla...")
        print("=" * 60)
        
        # Mantenir el servei executant-se
        try:
            while True:
                time.sleep(60)  # Revisar cada minut si el servei està actiu
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupció manual rebuda...")
            signal_handler(signal.SIGINT, None)
        
    except Exception as e:
        print(f"❌ Error iniciant servei de backup: {e}")
        return False
    
    return True

def main():
    """Punt d'entrada principal del servei"""
    # Configurar gestors de senyals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🔧 Servei de Backup Automàtic GOMPC v1.0")
    
    if not start_backup_service():
        print("❌ No s'ha pogut iniciar el servei.")
        sys.exit(1)

if __name__ == "__main__":
    main()
