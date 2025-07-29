#!/usr/bin/env python3
"""
Test script per verificar la funcionalitat de còpia de dades

Aquest script executa proves per verificar que la còpia de dades
entre bases de dades funciona correctament.
"""

import sys
import os
from pathlib import Path

# Afegir el directori arrel al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.network_scanner import NetworkScanner
from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
import json

def test_database_connections():
    """Test de connexions a les bases de dades"""
    print("🧪 TESTEJANT CONNEXIONS A LES BASES DE DADES")
    print("-" * 50)
    
    try:
        # Carregar configuració
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        # Test connexió origen (airflow_db)
        print("📡 Testejant connexió a airflow_db...")
        source_adapter = QualityMeasurementDBAdapter(full_config['secondary'])
        if source_adapter.connect():
            print("✅ Connexió a airflow_db: CORRECTA")
            source_adapter.close()
        else:
            print("❌ Connexió a airflow_db: FALLIDA")
            return False
        
        # Test connexió destí (documentacio_tecnica)
        print("📡 Testejant connexió a documentacio_tecnica...")
        target_adapter = QualityMeasurementDBAdapter(full_config['primary'])
        if target_adapter.connect():
            print("✅ Connexió a documentacio_tecnica: CORRECTA")
            target_adapter.close()
        else:
            print("❌ Connexió a documentacio_tecnica: FALLIDA")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error durant el test de connexions: {e}")
        return False

def test_copy_method():
    """Test del mètode de còpia sense executar la còpia real"""
    print("\n🧪 TESTEJANT MÈTODE DE CÒPIA")
    print("-" * 50)
    
    try:
        scanner = NetworkScanner()
        
        # Verificar que el mètode existeix
        if hasattr(scanner, 'copy_data_between_databases'):
            print("✅ Mètode copy_data_between_databases: EXISTEIX")
        else:
            print("❌ Mètode copy_data_between_databases: NO EXISTEIX")
            return False
        
        # Nota: No executem la còpia real en el test
        print("✅ Mètode de còpia: PREPARAT")
        return True
        
    except Exception as e:
        print(f"❌ Error testejant mètode de còpia: {e}")
        return False

def test_configuration_files():
    """Test dels fitxers de configuració"""
    print("\n🧪 TESTEJANT FITXERS DE CONFIGURACIÓ")
    print("-" * 50)
    
    # Test configuració BBDD
    db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
    
    if os.path.exists(db_config_path):
        print("✅ Fitxer db_config.json: EXISTEIX")
        
        try:
            with open(db_config_path, 'r') as f:
                config = json.load(f)
            
            if 'primary' in config and 'secondary' in config:
                print("✅ Configuracions primary i secondary: PRESENTS")
                
                # Verificar camps obligatoris
                required_fields = ['host', 'port', 'database', 'user', 'password']
                
                for config_name, config_data in [('primary', config['primary']), ('secondary', config['secondary'])]:
                    missing_fields = [field for field in required_fields if field not in config_data]
                    
                    if not missing_fields:
                        print(f"✅ Configuració {config_name}: COMPLETA")
                    else:
                        print(f"❌ Configuració {config_name}: FALTEN CAMPS {missing_fields}")
                        return False
                
            else:
                print("❌ Configuracions primary/secondary: NO PRESENTS")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Error llegint JSON: {e}")
            return False
            
    else:
        print("❌ Fitxer db_config.json: NO EXISTEIX")
        return False
    
    return True

def main():
    """Executa tots els tests"""
    print("=" * 70)
    print("TESTS DE CÒPIA DE DADES ENTRE BASES DE DADES")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: Fitxers de configuració
    if not test_configuration_files():
        all_tests_passed = False
    
    # Test 2: Connexions BBDD
    if not test_database_connections():
        all_tests_passed = False
    
    # Test 3: Mètode de còpia
    if not test_copy_method():
        all_tests_passed = False
    
    # Resum final
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ TOTS ELS TESTS HAN PASSAT CORRECTAMENT")
        print("🚀 El sistema està preparat per copiar dades entre BBDD")
    else:
        print("❌ ALGUNS TESTS HAN FALLAT")
        print("🔧 Reviseu els errors abans d'executar la còpia")
    
    print("=" * 70)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
