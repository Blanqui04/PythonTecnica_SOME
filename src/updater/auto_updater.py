"""
Sistema automàtic d'actualitzacions mitjançant GitHub Releases
Descarrega la versió nova, crea un script temporalitzador .bat i es reinicia
"""

import requests
import os
import sys
import zipfile
import shutil
import subprocess
import time
from pathlib import Path

try:
    from src.utils.version import APP_VERSION
except ImportError:
    # Fallback si no es pot importar
    APP_VERSION = "1.0.0"


class AutoUpdater:
    """Gestor automàtic d'actualitzacions des de GitHub Releases"""

    def __init__(self, github_owner: str = "Blanqui04", github_repo: str = "PythonTecnica_SOME"):
        """
        Inicialitza el gestor d'actualitzacions
        
        Args:
            github_owner: Propietari del repositori a GitHub
            github_repo: Nom del repositori a GitHub
        """
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.current_version = APP_VERSION
        self.temp_dir = Path("temp_update")

    def check_for_updates(self) -> dict:
        """
        Compara la versió local amb la última release a GitHub
        
        Returns:
            dict: Informació sobre si hi ha actualitzacions disponibles
        """
        try:
            print("🔍 Comprovant actualitzacions a GitHub...")
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            
            # Obtenir la versió del tag (ex: v1.0.1 -> 1.0.1)
            latest_version = data["tag_name"].lstrip("v")
            
            print(f"   Versió local: {self.current_version}")
            print(f"   Versió remota: {latest_version}")
            
            # Comparació simple de versions
            if latest_version != self.current_version:
                return {
                    "update_available": True,
                    "version": latest_version,
                    "download_url": data["zipball_url"],
                    "body": data.get("body", ""),
                    "published_at": data.get("published_at", "")
                }
            
            return {"update_available": False, "version": self.current_version}
            
        except requests.exceptions.Timeout:
            print("   ⚠️ Timeout en la connexió a GitHub")
            return {"update_available": False}
        except requests.exceptions.ConnectionError:
            print("   ⚠️ Error de connexió a GitHub")
            return {"update_available": False}
        except Exception as e:
            print(f"   ⚠️ Error comprovant actualitzacions: {e}")
            return {"update_available": False}

    def download_and_install(self, download_url: str) -> bool:
        """
        Descarrega l'actualització i prepara el script d'instal·lació
        
        Args:
            download_url: URL del ZIP a descarregar
            
        Returns:
            bool: True si l'actualització s'ha preparat correctament
        """
        try:
            print("⬇️  Descargando actualización...")
            
            # 1. Descargar ZIP
            response = requests.get(download_url, stream=True, timeout=30)
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
            
            print("\n📦 Extrayendo archivos...")
            
            # 2. Extraer ZIP
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # GitHub envuelve el contenido en una carpeta, encontrarla
            extracted_items = list(self.temp_dir.glob("*"))
            if not extracted_items:
                raise Exception("ZIP vacío o corrupto")
            
            extracted_root = extracted_items[0]
            
            # 3. Crear script BAT para reemplazar archivos
            print("⚙️  Preparando actualización...")
            
            app_exe = sys.executable
            script_path = Path(sys.argv[0]).resolve()
            app_dir = script_path.parent.resolve()
            
            # Buscar la carpeta PythonTecnica_SOME dentro del ZIP extraído
            pythonTecnica_folder = extracted_root / "PythonTecnica_SOME"
            
            if not pythonTecnica_folder.exists():
                # Si no existe, usar la raíz extraída
                source_folder = extracted_root
            else:
                source_folder = pythonTecnica_folder
            
            # Script BAT que se ejecutará después de cerrar la app
            bat_content = f"""@echo off
REM Script de actualización automática de PythonTecnica_SOME
echo.
echo ========================================
echo Aplicando actualización...
echo ========================================
echo.

REM Esperar a que se cierre la aplicación
timeout /t 2 /nobreak > NUL

REM Copiar archivos nuevos
echo Copiando archivos...
xcopy "{source_folder}\\*" "{app_dir}\\" /E /H /C /I /Y

REM Limpiar temporales
echo Limpiando archivos temporales...
if exist "{self.temp_dir}" rmdir /s /q "{self.temp_dir}"
if exist "update.zip" del "update.zip"

REM Auto-eliminar este script
if exist "%~f0" del "%~f0"

REM Reiniciar la aplicación
echo.
echo Reiniciando aplicación...
timeout /t 1 /nobreak > NUL
start "" "{app_exe}" "{script_path}"
"""
            
            bat_file = Path("update_installer.bat").resolve()
            with open(bat_file, "w", encoding='utf-8') as f:
                f.write(bat_content)
            
            print("🚀 Reiniciando aplicación para aplicar cambios...")
            print("   La aplicación se cerrará y se actualizará automáticamente.")
            
            # Ejecutar el script BAT en segundo plano
            subprocess.Popen([str(bat_file)], shell=True)
            
            # Cerrar la aplicación actual
            time.sleep(0.5)
            sys.exit(0)
            
        except requests.exceptions.Timeout:
            print("❌ Timeout descargando actualización")
            return False
        except Exception as e:
            print(f"❌ Error preparando actualización: {e}")
            return False

    def update_version_file(self, new_version: str) -> bool:
        """
        Actualiza el archivo de versión (útil después de instalar)
        
        Args:
            new_version: Nueva versión a registrar
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            version_file = Path(__file__).parent.parent / "utils" / "version.py"
            with open(version_file, "w", encoding='utf-8') as f:
                f.write(f"# Versió actual de l'aplicació\n")
                f.write(f"# Actualitzat automàticament\n")
                f.write(f'APP_VERSION = "{new_version}"\n')
            return True
        except Exception as e:
            print(f"⚠️ No se pudo actualizar archivo de versión: {e}")
            return False
