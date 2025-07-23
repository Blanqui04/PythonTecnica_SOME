#!/usr/bin/env python3
"""
Script d'automatització per la neteja periòdica de fitxers temporals.
Pot ser executat manualment o programat amb Task Scheduler de Windows.
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# Afegir el directori root del projecte al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.temp_file_cleaner import TempFileCleaner

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Neteja automàtica de fitxers temporals')
    parser.add_argument('--project-id', help='ID del projecte específic a netejar')
    parser.add_argument('--client', help='Nom del client específic')
    parser.add_argument('--aggressive', action='store_true', help='Neteja més agressiva')
    parser.add_argument('--dry-run', action='store_true', help='Simula la neteja sense eliminar fitxers')
    parser.add_argument('--universal', action='store_true', help='Neteja universal per tots els clients')
    
    args = parser.parse_args()
    
    logger.info(f"Iniciant neteja automàtica - {datetime.now()}")
    
    try:
        cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
        
        if args.universal and args.client and args.project_id:
            # Neteja universal per client/projecte específic
            logger.info(f"Mode universal per {args.client}/{args.project_id}")
            result = cleaner.clean_for_project_universal(
                client=args.client,
                ref_project=args.project_id,
                aggressive=args.aggressive
            )
            
        elif args.project_id and args.client:
            # Neteja per client i projecte específics
            logger.info(f"Neteja específica per {args.client}/{args.project_id}")
            result = cleaner.clean_for_project_universal(
                client=args.client,
                ref_project=args.project_id,
                aggressive=args.aggressive
            )
            
        else:
            # Neteja general de tots els fitxers antics
            logger.info("Neteja general de fitxers antics")
            
            # Configurar paràmetres segons el mode
            if args.aggressive:
                age_minutes_temp = 10
                age_hours_processed = 0.5
                age_hours_exports = 2
                logger.info("Mode agressiu activat")
            else:
                age_minutes_temp = 60  # 1 hora per temps
                age_hours_processed = 6  # 6 hores per processats
                age_hours_exports = 24  # 24 hores per exports
                logger.info("Mode normal activat")
            
            # Executar neteja general
            cleaned_files = cleaner.clean_all_old_files()
            result = {
                'files_cleaned': len(cleaned_files),
                'summary': f'Neteja general: {len(cleaned_files)} fitxers eliminats'
            }
        
        # Mostrar resultats
        logger.info(f"Neteja completada: {result.get('summary', 'OK')}")
        if result.get('files_cleaned', 0) > 0:
            logger.info(f"Fitxers eliminats: {result['files_cleaned']}")
            logger.info(f"Espai alliberat: {result.get('space_freed', 'N/A')}")
        
        # Neteja específica de directoris temp del sistema
        if not args.dry_run:
            cleaner.clean_system_temp_files(pattern_prefix='pythontecnica_')
            logger.info("Neteja de fitxers temporals del sistema completada")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error durant la neteja automàtica: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
