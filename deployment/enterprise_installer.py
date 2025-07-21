# deployment/enterprise_installer.py - Instal·lador per a l'empresa
import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path
import json
import logging
from config_manager import ConfigManager
from auto_updater import AutoUpdater

class EnterpriseInstaller:
    def __init__(self):
        self.app_name = "PythonTecnica_SOME"
        self.company_name = "SOME"
        self.install_dir = Path(f"C:\\Program Files\\{self.company_name}\\{self.app_name}")
        self.start_menu_dir = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / self.company_name
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def install(self, source_dir):
        """Instal·la l'aplicació a l'empresa"""
        try:
            self.logger.info("Starting enterprise installation...")
            
            # Crear directoris d'instal·lació
            self._create_install_directories()
            
            # Copiar fitxers de l'aplicació
            self._copy_application_files(source_dir)
            
            # Configurar per a l'entorn empresarial
            self._setup_enterprise_environment()
            
            # Crear accesos directes
            self._create_shortcuts()
            
            # Registrar l'aplicació al sistema
            self._register_application()
            
            # Configurar actualitzacions automàtiques
            self._setup_auto_updates()
            
            self.logger.info("Enterprise installation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False
    
    def _create_install_directories(self):
        """Crea els directoris necessaris"""
        directories = [
            self.install_dir,
            self.install_dir / "logs",
            self.install_dir / "temp",
            self.install_dir / "data" / "processed" / "datasheets",
            self.install_dir / "data" / "processed" / "exports",
            self.start_menu_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {directory}")
    
    def _copy_application_files(self, source_dir):
        """Copia els fitxers de l'aplicació"""
        source_path = Path(source_dir)
        
        # Fitxers i directoris a copiar
        items_to_copy = [
            "main_app.py",
            "requirements.txt",
            "src/",
            "config/",
            "assets/",
            "i18n/",
            "deployment/"
        ]
        
        for item in items_to_copy:
            src = source_path / item
            dest = self.install_dir / item
            
            if src.exists():
                if src.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                
                self.logger.info(f"Copied: {src} -> {dest}")
    
    def _setup_enterprise_environment(self):
        """Configura l'entorn empresarial"""
        # Utilitzar ConfigManager per configurar automàticament
        config_manager = ConfigManager()
        config_manager.setup_enterprise_config()
        
        # Crear fitxer de configuració d'instal·lació
        install_info = {
            "installed_date": self._get_current_timestamp(),
            "version": "1.0.0",
            "install_path": str(self.install_dir),
            "company": self.company_name,
            "auto_update_enabled": True,
            "update_server": "http://your-company-server/updates"
        }
        
        with open(self.install_dir / "install_info.json", 'w', encoding='utf-8') as f:
            json.dump(install_info, f, indent=4)
    
    def _create_shortcuts(self):
        """Crea accesos directes"""
        try:
            # Script de PowerShell per crear accesos directes
            ps_script = f'''
            $WshShell = New-Object -comObject WScript.Shell
            
            # Accés directe al menú d'inici
            $Shortcut = $WshShell.CreateShortcut("{self.start_menu_dir}\\{self.app_name}.lnk")
            $Shortcut.TargetPath = "python.exe"
            $Shortcut.Arguments = '"{self.install_dir}\\main_app.py"'
            $Shortcut.WorkingDirectory = "{self.install_dir}"
            $Shortcut.IconLocation = "{self.install_dir}\\assets\\images\\gui\\logo_some.png"
            $Shortcut.Description = "Sistema de Gestió de Base de Dades Tècniques"
            $Shortcut.Save()
            
            # Accés directe a l'escriptori
            $Desktop = [Environment]::GetFolderPath("Desktop")
            $Shortcut = $WshShell.CreateShortcut("$Desktop\\{self.app_name}.lnk")
            $Shortcut.TargetPath = "python.exe"
            $Shortcut.Arguments = '"{self.install_dir}\\main_app.py"'
            $Shortcut.WorkingDirectory = "{self.install_dir}"
            $Shortcut.IconLocation = "{self.install_dir}\\assets\\images\\gui\\logo_some.png"
            $Shortcut.Description = "Sistema de Gestió de Base de Dades Tècniques"
            $Shortcut.Save()
            '''
            
            # Executar script de PowerShell
            subprocess.run(["powershell", "-Command", ps_script], check=True)
            self.logger.info("Shortcuts created successfully")
            
        except Exception as e:
            self.logger.warning(f"Could not create shortcuts: {e}")
    
    def _register_application(self):
        """Registra l'aplicació al registre de Windows"""
        try:
            # Registre per a desinstal·lació
            uninstall_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                0,
                winreg.KEY_ALL_ACCESS
            )
            
            app_key = winreg.CreateKey(uninstall_key, self.app_name)
            
            # Informació de l'aplicació
            winreg.SetValueEx(app_key, "DisplayName", 0, winreg.REG_SZ, 
                            f"{self.app_name} - Sistema de Gestió de BBDD")
            winreg.SetValueEx(app_key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(app_key, "Publisher", 0, winreg.REG_SZ, self.company_name)
            winreg.SetValueEx(app_key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
            winreg.SetValueEx(app_key, "UninstallString", 0, winreg.REG_SZ, 
                            f'python "{self.install_dir}\\deployment\\uninstaller.py"')
            
            winreg.CloseKey(app_key)
            winreg.CloseKey(uninstall_key)
            
            self.logger.info("Application registered in Windows registry")
            
        except Exception as e:
            self.logger.warning(f"Could not register application: {e}")
    
    def _setup_auto_updates(self):
        """Configura el sistema d'actualitzacions automàtiques"""
        try:
            # Crear tasca programada per comprovar actualitzacions
            task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
            <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
              <Triggers>
                <CalendarTrigger>
                  <StartBoundary>2025-01-01T09:00:00</StartBoundary>
                  <ScheduleByDay>
                    <DaysInterval>1</DaysInterval>
                  </ScheduleByDay>
                </CalendarTrigger>
              </Triggers>
              <Actions>
                <Exec>
                  <Command>python</Command>
                  <Arguments>"{self.install_dir}\\deployment\\check_updates.py"</Arguments>
                  <WorkingDirectory>{self.install_dir}</WorkingDirectory>
                </Exec>
              </Actions>
            </Task>'''
            
            # Crear fitxer de tasca
            task_file = self.install_dir / "update_task.xml"
            with open(task_file, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # Registrar tasca
            subprocess.run([
                "schtasks", "/create", "/tn", f"{self.app_name}_UpdateChecker",
                "/xml", str(task_file), "/f"
            ], check=True)
            
            self.logger.info("Auto-update task scheduled")
            
        except Exception as e:
            self.logger.warning(f"Could not setup auto-updates: {e}")
    
    def _get_current_timestamp(self):
        """Obté el timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()

# Script principal d'instal·lació
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enterprise_installer.py <source_directory>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    installer = EnterpriseInstaller()
    
    if installer.install(source_dir):
        print("Installation completed successfully!")
        print(f"Application installed to: {installer.install_dir}")
        print("You can now run the application from the Start Menu or Desktop shortcut.")
    else:
        print("Installation failed. Check the logs for details.")
        sys.exit(1)
