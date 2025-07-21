# deployment/build_and_deploy.py - Script per construir i fer deployment
import subprocess
import sys
import os
import shutil
import zipfile
from pathlib import Path
import json
from datetime import datetime

class BuildAndDeploy:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.deploy_dir = self.project_dir / "deployment_package"
        
    def clean_build(self):
        """Neteja directoris de build anteriors"""
        dirs_to_clean = [self.build_dir, self.dist_dir, self.deploy_dir]
        
        for directory in dirs_to_clean:
            if directory.exists():
                shutil.rmtree(directory)
                print(f"Cleaned: {directory}")
    
    def install_build_dependencies(self):
        """Instal·la dependències per al build"""
        print("Installing build dependencies...")
        
        build_deps = [
            "cx-Freeze==6.14.9",
            "pyinstaller==5.8.0"
        ]
        
        for dep in build_deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
    
    def build_executable(self):
        """Construeix l'executable amb PyInstaller (més fiable que cx_Freeze)"""
        print("Building executable with PyInstaller...")
        
        # Crear spec file per PyInstaller
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_app.py'],
    pathex=['{self.project_dir}'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('assets', 'assets'),
        ('i18n', 'i18n'),
        ('src', 'src'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'psycopg2',
        'pandas',
        'numpy',
        'matplotlib',
        'plotly',
        'openpyxl'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PythonTecnica_SOME',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/gui/logo_some.png'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PythonTecnica_SOME'
)'''
        
        # Escriure spec file
        spec_file = self.project_dir / "PythonTecnica_SOME.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        # Executar PyInstaller
        os.chdir(self.project_dir)
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            str(spec_file)
        ], check=True)
        
        print("Executable built successfully!")
    
    def create_deployment_package(self):
        """Crea el paquet de deployment"""
        print("Creating deployment package...")
        
        self.deploy_dir.mkdir(exist_ok=True)
        
        # Copiar executable i dependències
        exe_source = self.dist_dir / "PythonTecnica_SOME"
        exe_dest = self.deploy_dir / "app"
        
        if exe_source.exists():
            shutil.copytree(exe_source, exe_dest)
        
        # Copiar scripts de deployment
        deployment_scripts = [
            "enterprise_installer.py",
            "config_manager.py", 
            "auto_updater.py",
            "check_updates.py"
        ]
        
        scripts_dir = self.deploy_dir / "deployment"
        scripts_dir.mkdir(exist_ok=True)
        
        for script in deployment_scripts:
            src = self.project_dir / "deployment" / script
            if src.exists():
                shutil.copy2(src, scripts_dir)
        
        # Crear script d'instal·lació fàcil
        self._create_easy_installer()
        
        # Crear documentació
        self._create_deployment_docs()
        
        print(f"Deployment package created at: {self.deploy_dir}")
    
    def _create_easy_installer(self):
        """Crea script d'instal·lació fàcil"""
        installer_content = '''@echo off
echo Installing PythonTecnica_SOME...
echo.

REM Comprovar si Python està instal·lat
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no està instal·lat. Si us plau, instal·la Python primer.
    echo Pots descarregar Python des de: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Instal·lar dependències
echo Installing Python dependencies...
pip install -r requirements.txt

REM Executar instal·lador empresarial
echo Running enterprise installer...
python deployment\\enterprise_installer.py app

echo.
echo Installation completed!
echo You can now run PythonTecnica_SOME from the Start Menu or Desktop.
pause
'''
        
        installer_path = self.deploy_dir / "install.bat"
        with open(installer_path, 'w', encoding='utf-8') as f:
            f.write(installer_content)
        
        # Copiar requirements.txt
        req_src = self.project_dir / "requirements.txt"
        req_dest = self.deploy_dir / "requirements.txt"
        if req_src.exists():
            shutil.copy2(req_src, req_dest)
    
    def _create_deployment_docs(self):
        """Crea documentació de deployment"""
        docs_content = f'''# Guia d'Instal·lació - PythonTecnica_SOME

## Requisits del Sistema
- Windows 10 o superior
- Python 3.8 o superior
- Connexió a la xarxa de l'empresa (per accés a la BBDD)
- Permisos d'administrador (per a la instal·lació)

## Instal·lació Ràpida
1. Descarrega i descomprimeix aquest paquet
2. Executa `install.bat` com a administrador
3. Segueix les instruccions en pantalla

## Instal·lació Manual
1. Assegura't que Python està instal·lat
2. Instal·la dependències: `pip install -r requirements.txt`
3. Executa: `python deployment\\enterprise_installer.py app`

## Configuració Automàtica
L'aplicació es configura automàticament per:
- Connexió a la BBDD de l'empresa (172.26.5.159:5433)
- Actualitzacions automàtiques
- Integració amb el sistema Windows

## Característiques del Deployment
- **Connexió Automàtica**: L'aplicació es connecta automàticament a la BBDD
- **Actualitzacions**: Comprova actualitzacions diàriament
- **Instalació Centralitzada**: Es guarda a `C:\\Program Files\\SOME\\PythonTecnica_SOME`
- **Accesos Directes**: Crea accesos al menú d'inici i escriptori

## Suport
Per problemes o qüestions, contacta amb l'equip IT.

Data de creació: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Versió: 1.0.0
'''
        
        docs_path = self.deploy_dir / "README_INSTALACIO.md"
        with open(docs_path, 'w', encoding='utf-8') as f:
            f.write(docs_content)
    
    def create_update_package(self, version):
        """Crea paquet d'actualització"""
        print(f"Creating update package for version {version}...")
        
        update_dir = self.project_dir / f"update_v{version}"
        update_dir.mkdir(exist_ok=True)
        
        # Fitxers a incloure en l'actualització
        update_items = ["src", "config", "assets", "i18n", "main_app.py"]
        
        for item in update_items:
            src = self.project_dir / item
            dest = update_dir / item
            
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
        
        # Crear ZIP d'actualització
        update_zip = self.project_dir / f"update_v{version}.zip"
        with zipfile.ZipFile(update_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in update_dir.rglob('*'):
                if item.is_file():
                    arcname = item.relative_to(update_dir)
                    zf.write(item, f"update/{arcname}")
        
        # Crear fitxer de versió
        version_info = {
            "version": version,
            "release_date": datetime.now().isoformat(),
            "download_url": f"http://your-company-server/updates/update_v{version}.zip",
            "release_notes": f"Actualització a la versió {version}"
        }
        
        version_file = self.project_dir / "version.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=4)
        
        # Neteja
        shutil.rmtree(update_dir)
        
        print(f"Update package created: {update_zip}")
        print(f"Version file created: {version_file}")
    
    def full_build(self, create_update=False, version="1.0.0"):
        """Procés complet de build i deployment"""
        print("Starting full build and deployment process...")
        
        try:
            # Neteja
            self.clean_build()
            
            # Instal·lar dependències de build
            self.install_build_dependencies()
            
            # Construir executable
            self.build_executable()
            
            # Crear paquet de deployment
            self.create_deployment_package()
            
            # Crear paquet d'actualització si es demana
            if create_update:
                self.create_update_package(version)
            
            print("\\n" + "="*50)
            print("BUILD AND DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*50)
            print(f"Deployment package: {self.deploy_dir}")
            print("To install on enterprise computers, copy this package and run install.bat")
            
        except Exception as e:
            print(f"Build failed: {e}")
            return False
        
        return True

if __name__ == "__main__":
    builder = BuildAndDeploy()
    
    # Paràmetres de la línia de comandes
    create_update = "--update" in sys.argv
    version = "1.0.0"
    
    # Buscar versió en arguments
    for arg in sys.argv:
        if arg.startswith("--version="):
            version = arg.split("=")[1]
    
    builder.full_build(create_update=create_update, version=version)
