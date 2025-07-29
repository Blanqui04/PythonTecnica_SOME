#!/usr/bin/env python3
"""
Script per copiar dades de mesuresqualitat entre bases de dades

Aquest script copia totes les dades de la taula mesuresqualitat
des de la BBDD airflow_db (config_2) cap a documentacio_tecnica (config_1).

Ús:
    python copy_database_data.py
"""

import sys
import os
import logging
from pathlib import Path

# Afegir el directori arrel al path per poder importar mòduls
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.network_scanner import NetworkScanner

def setup_logging():
    """Configura el logging per al script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/database_copy.log', encoding='utf-8')
        ]
    )

def main():
    """Funció principal del script"""
    print("="*70)
    print("CÒPIA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    print("Origen: airflow_db (config_2)")
    print("Destí: documentacio_tecnica (config_1)")
    print("Taula: mesuresqualitat")
    print("="*70)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Crear instància del NetworkScanner
        scanner = NetworkScanner()
        
        # Executar còpia de dades
        print("\n🔄 Iniciant còpia de dades...")
        result = scanner.copy_data_between_databases()
        
        if result['success']:
            print("\n✅ CÒPIA COMPLETADA CORRECTAMENT!")
            print(f"📊 Registres copiats: {result['records_copied']:,}")
            print(f"📊 Total registres: {result['records_total']:,}")
            print(f"📊 Registres saltats: {result.get('records_skipped', 0):,}")
            print(f"🗄️  Origen: {result['source_database']}")
            print(f"🗄️  Destí: {result['target_database']}")
            
            if result.get('errors'):
                print(f"\n⚠️  Errors durant la còpia:")
                for error in result['errors']:
                    print(f"   - {error}")
            
        else:
            print("\n❌ ERROR DURANT LA CÒPIA!")
            print(f"Error: {result['error']}")
            if result.get('records_copied', 0) > 0:
                print(f"Registres copiats abans de l'error: {result['records_copied']}")
            
            return 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operació cancel·lada per l'usuari")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        logger.error(f"Error inesperat durant la còpia: {e}")
        return 1
    
    print("\n🏁 Script finalitzat")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
