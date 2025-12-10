"""
SISTEMA PROFESSIONAL D'ACTUALITZACIONS AUTOMÀTIQUES
====================================================
Gestor complet i robust d'actualitzacions via GitHub Releases

Característiques:
- ✅ Detecció automàtica de noves versions
- ✅ Descàrrega i instal·lació automàtiques
- ✅ Script trampolí per evitar conflictes de fitxers
- ✅ Logging complet de totes les operacions
- ✅ Rollback en cas d'error
- ✅ Notificacions visuals a l'usuari
- ✅ Validació de integritat del ZIP
"""

import requests
import os
import sys
import zipfile
import shutil
import subprocess
import time
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    from src.utils.version import APP_VERSION
except ImportError:
    APP_VERSION = "1.0.0"

# Configurar logging professional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('update_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class AutoUpdater:
    """Gestor professional d'actualitzacions des de GitHub Releases"""

    def __init__(self, github_owner: str = "Blanqui04", github_repo: str = "PythonTecnica_SOME"):
        """
        Inicialitza el gestor d'actualitzacions professional
        
        Args:
            github_owner: Propietari del repositori a GitHub
            github_repo: Nom del repositori a GitHub
        """
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.current_version = APP_VERSION
        self.temp_dir = Path("temp_update")
        self.backup_dir = Path("backup_update")
        self.log = logging.getLogger(__name__)
        self.update_history_file = Path("update_history.json")
        
        self.log.info(f"=== AutoUpdater Professional Inicialitzat ===")
        self.log.info(f"Versió local: {self.current_version}")
        self.log.info(f"Repositori: {github_owner}/{github_repo}")

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compara dues versions de forma professional
        
        Args:
            version1: Primera versió (ex: "1.0.5")
            version2: Segona versió (ex: "1.0.6")
            
        Returns:
            -1 si version1 < version2
             0 si version1 == version2
             1 si version1 > version2
        """
        try:
            v1_parts = [int(x) for x in version1.strip().lstrip('v').split('.')]
            v2_parts = [int(x) for x in version2.strip().lstrip('v').split('.')]
            
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            if v1_parts < v2_parts:
                return -1
            elif v1_parts > v2_parts:
                return 1
            else:
                return 0
        except Exception as e:
            self.log.warning(f"Error comparant versions: {e}")
            return 0

    def check_for_updates(self, force_check: bool = False) -> dict:
        """
        Comprova si hi ha actualitzacions disponibles
        
        Args:
            force_check: Si True, ignora la caché i força la comprovació
            
        Returns:
            dict: Informació sobre actualitzacions disponibles
        """
        try:
            self.log.info(">>> Comprovant actualitzacions a GitHub...")
            print("🔍 Buscando actualizaciones...")
            
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data["tag_name"].lstrip("v")
            
            self.log.info(f"Versió local:  {self.current_version}")
            self.log.info(f"Versió remota: {latest_version}")
            
            # Comparació professional
            version_cmp = self.compare_versions(self.current_version, latest_version)
            
            if version_cmp < 0:
                info = {
                    "update_available": True,
                    "version": latest_version,
                    "download_url": data["zipball_url"],
                    "body": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                    "release_notes": data.get("body", "Sin descripción"),
                    "author": data.get("author", {}).get("login", "Unknown")
                }
                self.log.info(f"✅ ACTUALITZACIÓ DISPONIBLE: {latest_version}")
                return info
                
            elif version_cmp == 0:
                self.log.info(f"✓ Versió actual és la darrera")
                return {"update_available": False, "version": self.current_version}
            else:
                self.log.warning(f"⚠ Versió local és més nova que remota")
                return {"update_available": False, "version": self.current_version}
            
        except requests.exceptions.Timeout:
            self.log.error("❌ Timeout connectant a GitHub")
            return {"update_available": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            self.log.error("❌ Error de connexió a GitHub")
            return {"update_available": False, "error": "Connection Error"}
        except Exception as e:
            self.log.error(f"❌ Error comprovant actualitzacions: {e}")
            return {"update_available": False, "error": str(e)}

    def validate_zip_integrity(self, zip_path: Path) -> bool:
        """Valida que el ZIP és correcte i completa"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                result = zip_ref.testzip()
                if result is None:
                    self.log.info(f"✅ ZIP validat correctament")
                    return True
                else:
                    self.log.error(f"❌ ZIP corrupte: {result}")
                    return False
        except Exception as e:
            self.log.error(f"❌ Error validant ZIP: {e}")
            return False

    def create_backup(self, source_dir: Path) -> bool:
        """Crea una cópia de seguretat dels fitxers actuals"""
        try:
            self.log.info(">>> Creant backup de seguretat...")
            print("💾 Creando copia de seguridad...")
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            for item in source_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, self.backup_dir / item.name, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'backup_update', 'temp_update'))
                else:
                    shutil.copy2(item, self.backup_dir / item.name)
            
            self.log.info(f"✅ Backup creat correctament")
            print("✅ Copia de seguridad realizada")
            return True
        except Exception as e:
            self.log.error(f"❌ Error creant backup: {e}")
            return False

    def restore_backup(self, target_dir: Path) -> bool:
        """Restaura les copies de seguretat en cas d'error"""
        try:
            if not self.backup_dir.exists():
                self.log.warning("❌ No hi ha backup disponible")
                return False
            
            self.log.warning(">>> Restaurant backup anterior...")
            print("⚠️  Restaurando versión anterior...")
            
            for item in target_dir.iterdir():
                if item.is_dir() and item.name not in ['__pycache__', 'backup_update', 'temp_update']:
                    shutil.rmtree(item)
                elif item.is_file():
                    item.unlink()
            
            for item in self.backup_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, target_dir / item.name)
                else:
                    shutil.copy2(item, target_dir / item.name)
            
            self.log.info("✅ Backup restaurat")
            print("✅ Versión anterior restaurada")
            return True
        except Exception as e:
            self.log.error(f"❌ Error restaurant backup: {e}")
            return False

    def log_update_history(self, version: str, success: bool, details: str = ""):
        """Registra l'historial d'actualitzacions"""
        try:
            history = []
            if self.update_history_file.exists():
                with open(self.update_history_file, 'r') as f:
                    history = json.load(f)
            
            history.append({
                "timestamp": datetime.now().isoformat(),
                "from_version": self.current_version,
                "to_version": version,
                "success": success,
                "details": details
            })
            
            with open(self.update_history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            self.log.info(f"Historial registrat: {version} - {'✅' if success else '❌'}")
        except Exception as e:
            self.log.error(f"Error registrant historial: {e}")

    def download_and_install(self, download_url: str, new_version: str) -> bool:
        """Descarrega l'actualització i prepara la instal·lació professional"""
        try:
            print("\n" + "=" * 80)
            print("SISTEMA D'ACTUALITZACIÓ AUTOMÀTICA PROFESSIONAL")
            print("=" * 80)
            
            self.log.info(">>> Iniciant descarregament...")
            print(f"\n📥 Descargando versión {new_version}...")
            
            # 1. Descargar ZIP
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            zip_path = Path("update.zip")
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"   Progreso: {percent:.1f}%", end='\r')
            
            print(f"\n✅ Descarga completada ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
            self.log.info(f"ZIP descargat: {zip_path.stat().st_size} bytes")
            
            # 2. Validar ZIP
            print("🔍 Validando integridad...")
            if not self.validate_zip_integrity(zip_path):
                print("❌ Archivo corrupto. Abortando...")
                self.log_update_history(new_version, False, "ZIP corrupto")
                return False
            
            # 3. Extraer ZIP
            print("📦 Extrayendo archivos...")
            self.log.info("Extrayendo ZIP...")
            
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            extracted_items = list(self.temp_dir.glob("*"))
            if not extracted_items:
                raise Exception("ZIP vacío")
            
            extracted_root = extracted_items[0]
            self.log.info(f"ZIP extraído en: {extracted_root}")
            
            # 4. Crear backup
            app_dir = Path(__file__).parent.parent.parent
            if not self.create_backup(app_dir):
                print("❌ No se pudo crear backup. Abortando...")
                self.log_update_history(new_version, False, "Backup fallido")
                return False
            
            # 5. Crear script BAT professional
            print("⚙️  Preparando instalación...")
            self.log.info("Creando script de instalación...")
            
            app_exe = sys.executable
            script_path = Path(sys.argv[0]).resolve()
            app_dir = script_path.parent.resolve()
            
            pythonTecnica_folder = extracted_root / "PythonTecnica_SOME"
            source_folder = pythonTecnica_folder if pythonTecnica_folder.exists() else extracted_root
            
            # Script BAT professional con logs
            bat_content = f"""@echo off
setlocal enabledelayedexpansion
set BACKUP_DIR={self.backup_dir}
set SOURCE_DIR={source_folder}
set TARGET_DIR={app_dir}
set TEMP_DIR={self.temp_dir}
set LOG_FILE=%TARGET_DIR%\\update_install.log

echo [%date% %time%] === ACTUALIZACIÓN INICIADA === >> %LOG_FILE%
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         SISTEMA DE ACTUALIZACIÓN AUTOMÁTICA                   ║
echo ║              PythonTecnica_SOME v{new_version}                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo  Estado: Aguardando cierre de la aplicación...
echo.

timeout /t 3 /nobreak > NUL

echo  Estado: Aplicando actualización...
echo  [%date% %time%] Copiando archivos nuevos... >> %LOG_FILE%

xcopy "!SOURCE_DIR!\\*" "!TARGET_DIR!\\" /E /H /C /I /Y >>%LOG_FILE% 2>&1

if errorlevel 1 (
    echo  [%date% %time%] ERROR en actualización >> %LOG_FILE%
    echo.
    echo  ❌ ERROR: No se pudo completar la actualización
    echo  Estado: Restaurando versión anterior...
    xcopy "!BACKUP_DIR!\\*" "!TARGET_DIR!\\" /E /H /C /I /Y >>%LOG_FILE% 2>&1
    echo  ✅ Versión anterior restaurada
    timeout /t 3 /nobreak > NUL
    goto cleanup
)

echo  [%date% %time%] Archivos copiados correctamente >> %LOG_FILE%

:cleanup
echo  Estado: Limpiando archivos temporales...
echo  [%date% %time%] Limpiando temporales >> %LOG_FILE%
if exist "!TEMP_DIR!" rmdir /s /q "!TEMP_DIR!" >>%LOG_FILE% 2>&1
if exist "update.zip" del "update.zip" >>%LOG_FILE% 2>&1
if exist "%~f0" del "%~f0" >>%LOG_FILE% 2>&1

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║  ✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE                     ║
echo ║                                                                ║
echo ║  La aplicación se reiniciará en 2 segundos...                 ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo  [%date% %time%] Reiniciando aplicación >> %LOG_FILE%
timeout /t 2 /nobreak > NUL

start "" "{app_exe}" "{script_path}"
echo  [%date% %time%] === ACTUALIZACIÓN COMPLETADA === >> %LOG_FILE%
exit /b 0
"""
            
            bat_file = Path("update_installer.bat").resolve()
            with open(bat_file, "w", encoding='utf-8') as f:
                f.write(bat_content)
            
            print("\n✅ Preparado para actualizar")
            print("\nLa aplicación se cerrará y se actualizará automáticamente...")
            print("Este proceso puede tomar 1-2 minutos")
            print("=" * 80 + "\n")
            
            self.log.info(f"Script creado: {bat_file}")
            self.log.info("Iniciando actualización...")
            
            # Ejecutar el script
            subprocess.Popen([str(bat_file)], shell=True)
            time.sleep(0.5)
            
            self.log_update_history(new_version, True, "Descarga y preparación completada")
            sys.exit(0)
            
        except requests.exceptions.Timeout:
            self.log.error("Timeout descargando")
            print("❌ Timeout descargando actualización")
            self.log_update_history(new_version, False, "Timeout")
            return False
        except Exception as e:
            self.log.error(f"Error en actualización: {e}")
            print(f"❌ Error: {e}")
            self.log_update_history(new_version, False, str(e))
            self.restore_backup(Path(__file__).parent.parent.parent)
            return False

    def print_update_info(self, update_info: dict):
        """Mostra informació formatada sobre l'actualització disponible"""
        if update_info.get("update_available"):
            print("\n" + "=" * 80)
            print("  📦 ACTUALITZACIÓ DISPONIBLE")
            print("=" * 80)
            print(f"  Versió actual:     {self.current_version}")
            print(f"  Versió nueva:      {update_info.get('version')}")
            print(f"  Autor:             {update_info.get('author', 'Unknown')}")
            print(f"  Publicado:         {update_info.get('published_at', 'Unknown')}")
            if update_info.get('release_notes'):
                print(f"\n  📝 Notas de la versión:")
                for line in update_info.get('release_notes', '').split('\n')[:5]:
                    if line.strip():
                        print(f"     {line}")
            print("=" * 80 + "\n")

    def get_update_history(self) -> list:
        """Obtenir l'historial d'actualitzacions"""
        try:
            if self.update_history_file.exists():
                with open(self.update_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.log.error(f"Error llegint historial: {e}")
            return []
