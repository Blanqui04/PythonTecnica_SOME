# deployment/check_updates.py - Script per comprovar actualitzacions
import sys
import os
from pathlib import Path

# Afegir el directori de l'aplicació al path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from auto_updater import AutoUpdater
import logging

def main():
    """Comprova i aplica actualitzacions automàticament"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app_dir / "logs" / "updates.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Crear instància de l'actualitzador
        updater = AutoUpdater(
            current_version="1.0.0",
            update_server_url="http://your-company-server/updates"
        )
        
        # Comprovar actualitzacions
        logger.info("Checking for updates...")
        result = updater.auto_update_check()
        
        if result["updated"]:
            logger.info(f"Application updated to version {result['version']}")
            if result["restart_required"]:
                logger.info("Restart required to complete update")
        else:
            logger.info("No updates available")
            
    except Exception as e:
        logger.error(f"Error during update check: {e}")

if __name__ == "__main__":
    main()
