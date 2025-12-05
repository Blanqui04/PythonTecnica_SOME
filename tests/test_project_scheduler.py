"""
Test del ProjectBackupScheduler
Execució ràpida per verificar funcionament
"""

import sys
import os
import time
from pathlib import Path

# Afegir src al path
current_dir = Path(__file__).parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))

try:
    from src.services.project_backup_scheduler import ProjectBackupScheduler
except ImportError:
    ProjectBackupScheduler = None

def test_project_scheduler():
    """Test del programador amb interval curt"""
    import pytest
    
    if ProjectBackupScheduler is None:
        pytest.skip("ProjectBackupScheduler no disponible")
    
    print("=" * 60)
    print("🧪 TEST PROJECTBACKUPSCHEDULER")
    print("=" * 60)
    
    try:
        # Crear scheduler amb interval de 2 minuts per testing
        scheduler = ProjectBackupScheduler(interval_hours=0.033)  # ~2 minuts
        
        print("📅 Iniciant scheduler amb interval de 2 minuts...")
        
        if scheduler.start_scheduler():
            print("✅ Scheduler iniciat correctament")
            
            # Mostrar estat cada 30 segons durant 5 minuts
            for i in range(10):
                status = scheduler.get_status()
                print(f"\n📊 Estat [{i+1}/10]:")
                print(f"   🔄 Running: {status['running']}")
                print(f"   🕐 Propera execució: {status['next_execution']}")
                print(f"   🧵 Thread viu: {status['thread_alive']}")
                
                if status['last_execution']:
                    print(f"   ✅ Última execució: {status['last_execution']}")
                
                time.sleep(30)
            
            print("\n🛑 Aturant scheduler...")
            scheduler.stop_scheduler()
            print("✅ Test completat")
            
        else:
            print("❌ Error iniciant scheduler")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")

def test_force_backup():
    """Test de backup forçat"""
    print("\n" + "=" * 60)
    print("🚀 TEST BACKUP FORÇAT")
    print("=" * 60)
    
    try:
        scheduler = ProjectBackupScheduler()
        
        if scheduler.start_scheduler():
            print("✅ Scheduler iniciat")
            
            print("🚀 Forçant backup immediat...")
            result = scheduler.force_backup_now()
            
            if result['success']:
                print(f"✅ Backup forçat: {result['message']}")
                
                # Esperar una mica per veure els logs
                print("⏱️ Esperant 30 segons per veure logs...")
                time.sleep(30)
                
            else:
                print(f"❌ Error forçant backup: {result['error']}")
            
            scheduler.stop_scheduler()
            print("✅ Test backup forçat completat")
            
        else:
            print("❌ Error iniciant scheduler per test")
            
    except Exception as e:
        print(f"❌ Error en test backup forçat: {e}")

def main():
    """Menú de tests"""
    print("🧪 TESTS PROJECTBACKUPSCHEDULER")
    print("1. Test scheduler amb interval curt")
    print("2. Test backup forçat")
    print("3. Ambdós tests")
    
    choice = input("\nTriar opció (1-3): ").strip()
    
    if choice == "1":
        test_project_scheduler()
    elif choice == "2":
        test_force_backup()
    elif choice == "3":
        test_project_scheduler()
        test_force_backup()
    else:
        print("❌ Opció no vàlida")

if __name__ == "__main__":
    main()
