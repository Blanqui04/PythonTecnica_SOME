import sys
import os  # noqa: F401
from pathlib import Path
from src.gui.main_window import run_app
# Afegir el directori de deployment al path si existeix
deployment_dir = Path(__file__).parent / "deployment"
if deployment_dir.exists():
    sys.path.insert(0, str(deployment_dir))

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


#from src.services.gompc_sync_service import GompcSyncService
#from src.services.gompc_backup_scheduler import GompcBackupScheduler
#from src.services.project_backup_scheduler import ProjectBackupScheduler
"""
def start_project_backup_scheduler():
    try:
        print("\n" + "=" * 60)
        print("CONFIGURANT BACKUP AUTOMÀTIC SCANNER PROJECTES CADA 24 HORES")
        print("=" * 60)
        
        scheduler = ProjectBackupScheduler()
        scheduler.start_scheduler()
        
        next_backup = scheduler.get_next_backup_time()
        if next_backup:
            print(f"✅ Backup Scanner Projectes configurat")
            print(f"🕐 Propera execució: {next_backup}")
            print(f"🔄 Freqüència: Cada 24 hores")
        
        return scheduler
        
    except Exception as e:
        print(f"❌ Error configurant backup Scanner Projectes: {e}")
        return None

def sync_gompc_data():
    Sincronitza automàticament les dades del GOMPC a l'inici
    print("\n" + "=" * 60)
    print("SINCRONITZACIÓ AUTOMÀTICA DE DADES GOMPC")
    print("=" * 60)
    
    try:
        #sync_service = GompcSyncService()
        result = sync_service.sync_data_on_startup()
        
        if result['success']:
            print(f"✅ Sincronització completada:")
            print(f"   📋 Fitxers processats: {result['csv_files_processed']}")
            print(f"   💾 Registres inserits: {result['records_inserted']}")
            print(f"   ⏱️ Temps: {result['duration_seconds']:.2f}s")
        else:
            print(f"❌ Error en la sincronització: {result['message']}")
            if result['errors']:
                for error in result['errors'][:3]:
                    print(f"   - {error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error crític durant la sincronització: {e}")
        return {'success': False, 'error': str(e)}

def start_backup_scheduler():
    try:
        print("\n" + "=" * 60)
        print("CONFIGURANT BACKUP AUTOMÀTIC CADA 24 HORES")
        print("=" * 60)
        
        scheduler = GompcBackupScheduler()
        scheduler.start_scheduler()
        
        next_backup = scheduler.get_next_backup_time()
        if next_backup:
            print(f"✅ Backup automàtic configurat")
            print(f"   🕐 Propera execució: {next_backup}")
            print(f"   🔄 Freqüència: Cada 24 hores")
        
        return scheduler
        
    except Exception as e:
        print(f"❌ Error configurant backup automàtic: {e}")
        return None
"""
def main():
    """Punt d'entrada principal de l'aplicació"""
    
    try:
        # Comprovar actualitzacions automàtiques des de GitHub
        try:
            from src.updater.auto_updater import AutoUpdater
            
            print("\n" + "=" * 60)
            print("COMPROVANT ACTUALITZACIONS")
            print("=" * 60)
            
            updater = AutoUpdater(github_owner="Blanqui04", github_repo="PythonTecnica_SOME")
            update_info = updater.check_for_updates()
            
            if update_info.get("update_available"):
                print(f"\n✨ NOVA VERSIÓ DISPONIBLE: {update_info['version']}")
                print("⬇️  Descargando e instalando...")
                
                # Descargar e instalar, esto cerrará la app
                updater.download_and_install(update_info['download_url'])
                # Si llegamos aquí, algo salió mal
                print("⚠️ No se pudo aplicar la actualización. Continuando con la versión actual...")
            else:
                print(f"✅ L'aplicació està actualitzada (versió {update_info.get('version', 'desconeguda')})")
        
        except ImportError:
            print("⚠️ Mòdul AutoUpdater no trobat. Verificar que 'requests' estigui instal·lat.")
            print("   pip install requests")
        except Exception as e:
            print(f"⚠️ No s'ha pogut comprovar actualitzacions: {e}")
        
        # Configurar entorn empresarial si estem en mode deployment
        if deployment_dir.exists():
            try:
                from config_manager import ConfigManager

                # Configurar automàticament per a l'empresa
                config_manager = ConfigManager()
                if not config_manager.verify_config():
                    print("Setting up enterprise configuration...")
                    config_manager.setup_enterprise_config()
            except Exception as e:
                print(f"⚠️ Error configurant entorn empresarial: {e}")
        
        # Executar aplicació principal directament
        print("\n" + "=" * 60)
        print("INICIANT APLICACIÓ PRINCIPAL")
        print("=" * 60)
        print("📅 Backup GOMPC automàtic configurat per executar-se cada 24 hores")
        print("📅 Backup Scanner Projectes configurat per executar-se cada 24 hores")
        print("🚀 Aplicació iniciada immediatament - backups en segon pla")
        print("=" * 60 + "\n")
        run_app()

    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
        

if __name__ == "__main__":
    main()
