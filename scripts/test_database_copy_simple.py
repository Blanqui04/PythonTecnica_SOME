#!/usr/bin/env python3
"""
Test simplificat per verificar la funcionalitat de còpia de dades

Aquest script executa proves bàsiques per verificar que la còpia de dades
entre bases de dades pot funcionar.
"""

import sys
import os
from pathlib import Path
import json

# Afegir el directori arrel al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_configuration_files():
    """Test dels fitxers de configuració"""
    print("🧪 TESTEJANT FITXERS DE CONFIGURACIÓ")
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
                        print(f"   - Host: {config_data['host']}")
                        print(f"   - Port: {config_data['port']}")
                        print(f"   - Database: {config_data['database']}")
                        print(f"   - User: {config_data['user']}")
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

def test_database_imports():
    """Test d'importació de mòduls de BBDD"""
    print("\n🧪 TESTEJANT IMPORTACIONS DE MÒDULS")
    print("-" * 50)
    
    try:
        # Intentar importar l'adapter de BBDD
        from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
        print("✅ QualityMeasurementDBAdapter: IMPORTAT CORRECTAMENT")
        
        # Verificar que té els mètodes necessaris
        required_methods = ['connect', 'close', 'prepare_dataset_for_insertion', 'insert_dataset']
        
        for method in required_methods:
            if hasattr(QualityMeasurementDBAdapter, method):
                print(f"✅ Mètode {method}: PRESENT")
            else:
                print(f"❌ Mètode {method}: NO PRESENT")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error important QualityMeasurementDBAdapter: {e}")
        return False

def test_database_connections():
    """Test de connexions a les bases de dades"""
    print("\n🧪 TESTEJANT CONNEXIONS A LES BASES DE DADES")
    print("-" * 50)
    
    try:
        from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
        
        # Carregar configuració
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        # Test connexió origen (airflow_db)
        print("📡 Testejant connexió a airflow_db...")
        source_adapter = QualityMeasurementDBAdapter(full_config['secondary'])
        if source_adapter.connect():
            print("✅ Connexió a airflow_db: CORRECTA")
            
            # Intentar comptar registres
            try:
                with source_adapter.connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                    count = cursor.fetchone()[0]
                    print(f"📊 Registres a airflow_db: {count:,}")
            except Exception as e:
                print(f"⚠️  Taula mesuresqualitat a airflow_db: {e}")
            
            source_adapter.close()
        else:
            print("❌ Connexió a airflow_db: FALLIDA")
            return False
        
        # Test connexió destí (documentacio_tecnica)
        print("📡 Testejant connexió a documentacio_tecnica...")
        target_adapter = QualityMeasurementDBAdapter(full_config['primary'])
        if target_adapter.connect():
            print("✅ Connexió a documentacio_tecnica: CORRECTA")
            
            # Intentar comptar registres
            try:
                with target_adapter.connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                    count = cursor.fetchone()[0]
                    print(f"📊 Registres a documentacio_tecnica: {count:,}")
            except Exception as e:
                print(f"⚠️  Taula mesuresqualitat a documentacio_tecnica: {e}")
            
            target_adapter.close()
        else:
            print("❌ Connexió a documentacio_tecnica: FALLIDA")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error durant el test de connexions: {e}")
        return False

def main():
    """Executa tots els tests"""
    print("=" * 70)
    print("TESTS SIMPLIFICATS DE CÒPIA DE DADES ENTRE BASES DE DADES")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: Fitxers de configuració
    if not test_configuration_files():
        all_tests_passed = False
    
    # Test 2: Importacions
    if not test_database_imports():
        all_tests_passed = False
    
    # Test 3: Connexions BBDD (només si les importacions funcionen)
    if all_tests_passed:
        if not test_database_connections():
            all_tests_passed = False
    
    # Resum final
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ TOTS ELS TESTS HAN PASSAT CORRECTAMENT")
        print("🚀 El sistema està preparat per copiar dades entre BBDD")
        print("\n📋 SEGÜENTS PASSOS:")
        print("   1. Executar: python scripts/copy_database_data_simple.py")
        print("   2. O utilitzar l'script avançat per més opcions")
    else:
        print("❌ ALGUNS TESTS HAN FALLAT")
        print("🔧 Reviseu els errors abans d'executar la còpia")
    
    print("=" * 70)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
