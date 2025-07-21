# deployment/config_manager.py - Gestió automàtica de configuració
import json
import os
import configparser
from pathlib import Path
import logging

class ConfigManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.config_dir = self.app_dir / "config"
        self.logger = logging.getLogger(__name__)
    
    def setup_enterprise_config(self):
        """Configura automàticament per a l'entorn empresarial"""
        try:
            # Configuració de base de dades per defecte
            self._setup_database_config()
            
            # Configuració general
            self._setup_general_config()
            
            # Variables d'entorn
            self._setup_environment_variables()
            
            self.logger.info("Enterprise configuration setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up enterprise config: {e}")
            return False
    
    def _setup_database_config(self):
        """Configura connexió automàtica a la BBDD"""
        db_config_path = self.config_dir / "database" / "db_config.json"
        
        # Configuració per defecte de l'empresa
        enterprise_db_config = {
            "primary": {
                "host": os.getenv("DB_HOST", "172.26.5.159"),
                "port": os.getenv("DB_PORT", "5433"),
                "database": os.getenv("DB_NAME", "documentacio_tecnica"),
                "user": os.getenv("DB_USER", "administrador"),
                "password": os.getenv("DB_PASSWORD", "Some2025.!$%"),
                "auto_connect": True,
                "connection_timeout": 30,
                "retry_attempts": 3
            },
            "secondary": {
                "host": os.getenv("DB_HOST_SECONDARY", "172.26.5.159"),
                "port": os.getenv("DB_PORT_SECONDARY", "5434"),
                "database": os.getenv("DB_NAME_SECONDARY", "airflow_db"),
                "user": os.getenv("DB_USER_SECONDARY", "airflow_user"),
                "password": os.getenv("DB_PASSWORD_SECONDARY", "airflow123"),
                "auto_connect": False
            }
        }
        
        # Crear directori si no existeix
        db_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escriure configuració
        with open(db_config_path, 'w', encoding='utf-8') as f:
            json.dump(enterprise_db_config, f, indent=4)
    
    def _setup_general_config(self):
        """Configura paràmetres generals"""
        config_path = self.config_dir / "config.ini"
        
        config = configparser.ConfigParser()
        
        # Configuració per defecte de l'empresa
        config['DEFAULT'] = {
            'debug': 'false',  # Desactivar debug en producció
            'log_level': 'INFO',
            'language': 'ca',
            'auto_update': 'true',
            'update_check_interval': '3600'  # Comprovar actualitzacions cada hora
        }
        
        config['PATHS'] = {
            'base_dir': str(self.app_dir),
            'datasheets_dir': 'data\\processed\\datasheets',
            'db_export_dir': 'data\\processed\\exports',
            'log_dir': 'logs',
            'temp_dir': 'temp'
        }
        
        config['DATABASE'] = {
            'auto_connect_on_startup': 'true',
            'connection_pool_size': '5',
            'max_retries': '3',
            'retry_delay': '5'
        }
        
        config['ENTERPRISE'] = {
            'company_name': 'SOME',
            'department': 'Technical Documentation',
            'admin_contact': 'it@some.com',
            'support_url': 'http://intranet.some.com/support'
        }
        
        # Crear directori si no existeix
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escriure configuració
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def _setup_environment_variables(self):
        """Configura variables d'entorn necessàries"""
        env_vars = {
            'PYTHONPATH': str(self.app_dir),
            'APP_ENV': 'production',
            'APP_NAME': 'PythonTecnica_SOME',
            'APP_VERSION': '1.0.0'
        }
        
        for key, value in env_vars.items():
            if not os.getenv(key):
                os.environ[key] = value
    
    def verify_config(self):
        """Verifica que la configuració sigui correcta"""
        try:
            # Verificar fitxers de configuració
            required_files = [
                self.config_dir / "config.ini",
                self.config_dir / "database" / "db_config.json"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    self.logger.error(f"Missing config file: {file_path}")
                    return False
            
            # Verificar contingut de la configuració de BBDD
            db_config_path = self.config_dir / "database" / "db_config.json"
            with open(db_config_path, 'r', encoding='utf-8') as f:
                db_config = json.load(f)
                
                if 'primary' not in db_config:
                    self.logger.error("Missing primary database configuration")
                    return False
            
            self.logger.info("Configuration verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration verification failed: {e}")
            return False
