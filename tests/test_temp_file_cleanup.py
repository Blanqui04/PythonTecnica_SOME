#!/usr/bin/env python3
"""
Script de test per provar la funcionalitat de neteja automàtica
especialmente per projectes ZF.
"""

import sys
import os
import logging
from pathlib import Path

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

def test_zf_cleanup():
    """Prova la neteja específica per projectes ZF"""
    logger.info("=== Test de neteja ZF ===")
    
    try:
        # Test del TempFileCleaner directament
        cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
        
        # Projecte ZF d'exemple
        zf_project = "004938000151"
        
        result = cleaner.clean_for_zf_project(zf_project, aggressive=False)
        
        logger.info(f"Resultat neteja ZF: {result}")
        
        # Test a través del DatabaseUploader
        uploader = DatabaseUploader(
            client="ZF",
            ref_project=zf_project,
            db_key="primary"
        )
        
        uploader_result = uploader.cleanup_for_zf_project()
        logger.info(f"Resultat neteja via DatabaseUploader: {uploader_result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en test ZF: {e}")
        return False

def test_general_cleanup():
    """Prova la neteja general"""
    logger.info("=== Test de neteja general ===")
    
    try:
        cleaner = TempFileCleaner()
        
        # Neteja general
        cleaned_files = cleaner.clean_all_old_files()
        logger.info(f"Fitxers netejats en neteja general: {len(cleaned_files)}")
        
        # Crear alguns fitxers de test temporals per veure que funciona
        test_temp_dir = Path("data/temp/test_cleanup")
        test_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear fitxer de test
        test_file = test_temp_dir / "test_004938000151.csv"
        test_file.write_text("test,data\n1,2\n")
        logger.info(f"Creat fitxer de test: {test_file}")
        
        # Provar neteja per projecte
        project_cleaned = cleaner.clean_for_project("ZF", "004938000151", immediate=True)
        logger.info(f"Fitxers netejats per projecte: {len(project_cleaned)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en test general: {e}")
        return False

def test_config_loading():
    """Prova la càrrega de configuració"""
    logger.info("=== Test de configuració ===")
    
    try:
        cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
        
        if cleaner.config:
            logger.info("Configuració carregada correctament")
            logger.info(f"Configuració disponible: {list(cleaner.config.keys())}")
            
            # Mostrar polítiques de retenció
            retention_policies = cleaner.config.get('retention_policies', {})
            for policy_name, policy_config in retention_policies.items():
                logger.info(f"Política {policy_name}: {policy_config}")
        else:
            logger.warning("No s'ha pogut carregar la configuració")
            
        return True
        
    except Exception as e:
        logger.error(f"Error en test de configuració: {e}")
        return False

def main():
    """Executa tots els tests"""
    logger.info("Iniciant tests de neteja automàtica...")
    
    tests = [
        ("Configuració", test_config_loading),
        ("Neteja General", test_general_cleanup),
        ("Neteja ZF", test_zf_cleanup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Executant {test_name} ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSAT")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FALLIT")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info(f"\n=== RESUM ===")
    logger.info(f"Tests passats: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 Tots els tests han passat!")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} test(s) han fallat")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
