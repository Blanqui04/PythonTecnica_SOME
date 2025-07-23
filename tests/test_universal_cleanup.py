#!/usr/bin/env python3
"""
Script de test per provar la neteja universal amb diferents clients
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Afegir el directori root del projecte al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.temp_file_cleaner import TempFileCleaner
from src.database.database_uploader import DatabaseUploader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_files():
    """Crear fitxers de test per diferents clients"""
    test_clients = [
        ("ZF", "004938000151"),
        ("SEAT", "SE2023001234"),
        ("BMW", "BM2023005678"),
        ("AUDI", "AU2023009012"),
        ("MERCEDES", "MB2023003456")
    ]
    
    test_dirs = [
        Path("data/temp"),
        Path("data/processed/exports"),
        Path("data/processed/datasheets")
    ]
    
    created_files = []
    
    for client, project in test_clients:
        for test_dir in test_dirs:
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear fitxers de test
            test_files = [
                f"datasheet_{client}_{project}.csv",
                f"{project}_{client}_export.csv",
                f"temp_{client}_{project}.tmp",
                f"{client}_{project}_processed.csv"
            ]
            
            for filename in test_files:
                file_path = test_dir / filename
                file_path.write_text(f"test,data,client,project\n1,test,{client},{project}\n")
                created_files.append(file_path)
                logger.info(f"Creat fitxer de test: {file_path}")
    
    return created_files

def test_universal_cleanup():
    """Prova la neteja universal per diferents clients"""
    logger.info("=== Test de neteja universal per diferents clients ===")
    
    test_clients = [
        ("ZF", "004938000151"),
        ("SEAT", "SE2023001234"),
        ("BMW", "BM2023005678"),
        ("AUDI", "AU2023009012"),
        ("MERCEDES", "MB2023003456")
    ]
    
    cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
    
    results = {}
    
    for client, project in test_clients:
        logger.info(f"\n--- Testant neteja per {client} / {project} ---")
        
        try:
            # Test neteja universal
            result = cleaner.clean_for_project_universal(
                client=client,
                ref_project=project,
                aggressive=False
            )
            
            results[f"{client}_{project}"] = result
            
            logger.info(f"Resultat {client}: {result.get('summary', 'Error')}")
            if result.get('files_cleaned', 0) > 0:
                logger.info(f"  - Fitxers netejats: {result['files_cleaned']}")
                logger.info(f"  - Espai alliberat: {result.get('space_freed', 'N/A')}")
                logger.info(f"  - Política aplicada: {result.get('policy_applied', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error testant {client}/{project}: {e}")
            results[f"{client}_{project}"] = {"success": False, "error": str(e)}
    
    return results

def test_database_uploader_universal():
    """Prova la neteja a través del DatabaseUploader per diferents clients"""
    logger.info("=== Test de DatabaseUploader universal ===")
    
    test_cases = [
        ("ZF", "004938000151"),
        ("SEAT", "SE2023001234"),
        ("BMW", "BM2023005678")
    ]
    
    results = {}
    
    for client, project in test_cases:
        logger.info(f"\n--- Testant DatabaseUploader per {client} / {project} ---")
        
        try:
            # Crear uploader
            uploader = DatabaseUploader(
                client=client,
                ref_project=project,
                db_key="primary"
            )
            
            # Test neteja universal
            result = uploader.cleanup_for_any_project()
            results[f"{client}_{project}"] = result
            
            logger.info(f"Resultat DatabaseUploader {client}: {result.get('summary', 'Error')}")
            
        except Exception as e:
            logger.error(f"Error en DatabaseUploader {client}/{project}: {e}")
            results[f"{client}_{project}"] = {"success": False, "error": str(e)}
    
    return results

def test_aggressive_mode():
    """Prova el mode agressiu"""
    logger.info("=== Test de mode agressiu ===")
    
    cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
    
    # Test amb ZF en mode agressiu
    result_normal = cleaner.clean_for_project_universal("ZF", "004938000151", aggressive=False)
    result_aggressive = cleaner.clean_for_project_universal("ZF", "004938000151", aggressive=True)
    
    logger.info(f"Resultat normal: {result_normal.get('summary', 'Error')}")
    logger.info(f"Resultat agressiu: {result_aggressive.get('summary', 'Error')}")
    
    return {"normal": result_normal, "aggressive": result_aggressive}

def main():
    """Executa tots els tests"""
    logger.info(f"Iniciant tests de neteja universal - {datetime.now()}")
    
    # Crear fitxers de test
    logger.info("Creant fitxers de test...")
    test_files = create_test_files()
    logger.info(f"Creats {len(test_files)} fitxers de test")
    
    # Tests
    tests = [
        ("Neteja Universal", test_universal_cleanup),
        ("DatabaseUploader Universal", test_database_uploader_universal),
        ("Mode Agressiu", test_aggressive_mode)
    ]
    
    all_results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Executant: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            all_results[test_name] = result
            
            if isinstance(result, dict) and any(r.get('success', True) for r in result.values() if isinstance(r, dict)):
                logger.info(f"✅ {test_name}: PASSAT")
                passed += 1
            else:
                logger.warning(f"⚠️ {test_name}: PARCIAL")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            all_results[test_name] = {"error": str(e)}
    
    # Resum final
    logger.info(f"\n{'='*50}")
    logger.info(f"RESUM FINAL")
    logger.info(f"{'='*50}")
    logger.info(f"Tests completats: {passed}/{total}")
    
    # Mostrar estadístiques
    total_files_cleaned = 0
    for test_result in all_results.values():
        if isinstance(test_result, dict):
            for result in test_result.values():
                if isinstance(result, dict) and 'files_cleaned' in result:
                    total_files_cleaned += result.get('files_cleaned', 0)
    
    logger.info(f"Total fitxers netejats: {total_files_cleaned}")
    
    if passed == total:
        logger.info("🎉 Sistema de neteja universal funciona correctament!")
        return 0
    else:
        logger.warning(f"⚠️ Alguns tests necessiten atenció")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nTest completat amb codi de sortida: {exit_code}")
    sys.exit(exit_code)
