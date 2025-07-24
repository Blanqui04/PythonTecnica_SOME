import sys
import os  # noqa: F401
from pathlib import Path
from src.gui.main_window import run_app

# Afegir el directori de deployment al path si existeix
deployment_dir = Path(__file__).parent / "deployment"
if deployment_dir.exists():
    sys.path.insert(0, str(deployment_dir))


def main():
    """Punt d'entrada principal de l'aplicació"""
    try:
        # Configurar entorn empresarial si estem en mode deployment
        if deployment_dir.exists():
            from config_manager import ConfigManager
            from auto_updater import AutoUpdater

            # Configurar automàticament per a l'empresa
            config_manager = ConfigManager()
            if not config_manager.verify_config():
                print("Setting up enterprise configuration...")
                config_manager.setup_enterprise_config()

            # Comprovar actualitzacions en segon pla (només en mode empresarial)
            try:
                updater = AutoUpdater()
                update_info = updater.check_for_updates()
                if update_info.get("update_available"):
                    print(f"Update available: {update_info['version']}")
            except Exception as e:
                print(f"Could not check for updates: {e}")

        # Executar aplicació principal
        run_app()

    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
