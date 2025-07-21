# deployment/auto_updater.py - Sistema d'actualitzacions automàtiques
import requests
import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
import hashlib
import zipfile

class AutoUpdater:
    def __init__(self, current_version="1.0.0", update_server_url="http://your-company-server/updates"):
        self.current_version = current_version
        self.update_server_url = update_server_url
        self.app_dir = Path(__file__).parent.parent
        self.temp_dir = self.app_dir / "temp_update"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def check_for_updates(self):
        """Comprova si hi ha actualitzacions disponibles"""
        try:
            response = requests.get(f"{self.update_server_url}/version.json", timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                latest_version = version_info.get("version")
                
                if self._is_newer_version(latest_version, self.current_version):
                    return {
                        "update_available": True,
                        "version": latest_version,
                        "download_url": version_info.get("download_url"),
                        "release_notes": version_info.get("release_notes", "")
                    }
            return {"update_available": False}
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return {"update_available": False}
    
    def download_update(self, download_url):
        """Descarrega l'actualització"""
        try:
            self.temp_dir.mkdir(exist_ok=True)
            
            response = requests.get(download_url, stream=True, timeout=30)
            update_file = self.temp_dir / "update.zip"
            
            with open(update_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return update_file
        except Exception as e:
            self.logger.error(f"Error downloading update: {e}")
            return None
    
    def apply_update(self, update_file):
        """Aplica l'actualització"""
        try:
            # Extreure l'actualització
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Crear backup de la versió actual
            backup_dir = self.app_dir / "backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            # Fer backup dels fitxers principals
            for item in ["src", "config", "assets", "i18n"]:
                src_path = self.app_dir / item
                if src_path.exists():
                    shutil.copytree(src_path, backup_dir / item)
            
            # Aplicar nova versió
            update_src = self.temp_dir / "update"
            for item in update_src.iterdir():
                dest = self.app_dir / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            
            # Neteja
            shutil.rmtree(self.temp_dir)
            
            self.logger.info("Update applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying update: {e}")
            return False
    
    def _is_newer_version(self, latest, current):
        """Compara versions"""
        latest_parts = [int(x) for x in latest.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        return latest_parts > current_parts
    
    def auto_update_check(self):
        """Procés complet d'actualització automàtica"""
        update_info = self.check_for_updates()
        
        if update_info["update_available"]:
            self.logger.info(f"Update available: {update_info['version']}")
            
            # Descarregar actualització
            update_file = self.download_update(update_info["download_url"])
            if update_file:
                # Aplicar actualització
                if self.apply_update(update_file):
                    return {
                        "updated": True,
                        "version": update_info["version"],
                        "restart_required": True
                    }
        
        return {"updated": False}
