#!/usr/bin/env python3
"""
Script de test simple que llegeix directament el fitxer de configuració
"""

import sys
import os
import json
from pathlib import Path

# Afegir el directori arrel al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

def test_direct_config():
    """Test que llegeix directament el fitxer de configuració"""
    
    print("=" * 70)
    print("TEST DIRECTE DE CONFIGURACIÓ")
    print("=" * 70)
    
    # Llegir directament el fitxer
    config_path = project_root / "config" / "database" / "db_config.json"
    print(f"📁 Llegint configuració de: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📋 CONFIGURACIÓ CARREGADA:")
    print("-" * 50)
    
    secondary_config = config['secondary']
    print(f"🔍 SECONDARY CONFIG:")
    print(f"   Host: {secondary_config['host']}")
    print(f"   Port: {secondary_config['port']}")
    print(f"   Database: {secondary_config['database']}")
    print(f"   User: {secondary_config['user']}")
    print(f"   Password: {'*' * len(secondary_config['password'])}")
    
    # Test de connexió
    print(f"\n📡 Testejant connexió a {secondary_config['database']}...")
    print(f"   Connexió: {secondary_config['user']}@{secondary_config['host']}:{secondary_config['port']}")
    
    try:
        adapter = QualityMeasurementDBAdapter(secondary_config)
        if adapter.connect():
            print("✅ Connexió: EXITOSA")
            
            # Comprovar la taula
            with adapter.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                count = cursor.fetchone()[0]
                print(f"📊 Registres a mesuresqualitat: {count:,}")
            
            adapter.close()
        else:
            print("❌ Connexió: FALLIDA")
            
    except Exception as e:
        print(f"❌ Error de connexió: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_direct_config()
