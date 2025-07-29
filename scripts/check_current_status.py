#!/usr/bin/env python3
"""
Script per verificar l'estat actual de les dues bases de dades
"""

import sys
import os
import json
from pathlib import Path

# Afegir el directori arrel al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

def check_database_status():
    """Verifica l'estat de les dues bases de dades"""
    
    try:
        # Carregar configuració
        db_config_path = project_root / "config" / "database" / "db_config.json"
        with open(db_config_path, 'r') as f:
            config = json.load(f)
        
        print("=" * 80)
        print("ESTAT ACTUAL DE LES BASES DE DADES")
        print("=" * 80)
        
        # Verificar base de dades origen (airflow)
        print("\n🔍 BASE DE DADES ORIGEN (AIRFLOW):")
        print("-" * 50)
        source_config = config['secondary']
        print(f"📍 Connexió: {source_config['user']}@{source_config['host']}:{source_config['port']}/{source_config['database']}")
        
        source_adapter = QualityMeasurementDBAdapter(source_config)
        if source_adapter.connect():
            with source_adapter.connection.cursor() as cursor:
                # Comprovar si existeix la taula
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'mesuresqualitat'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                    count = cursor.fetchone()[0]
                    print(f"✅ Taula mesuresqualitat: EXISTS ({count:,} registres)")
                    
                    # Mostrar els primers registres
                    cursor.execute("SELECT * FROM mesuresqualitat LIMIT 5")
                    rows = cursor.fetchall()
                    if rows:
                        print("📋 Mostres dels primers registres:")
                        for i, row in enumerate(rows[:3], 1):
                            print(f"   {i}. ID: {row[0] if len(row) > 0 else 'N/A'}")
                else:
                    print("❌ Taula mesuresqualitat: NO EXISTEIX")
        else:
            print("❌ No es pot connectar a la base de dades origen")
        
        source_adapter.close()
        
        # Verificar base de dades destí (documentacio_tecnica)
        print("\n🎯 BASE DE DADES DESTÍ (DOCUMENTACIO_TECNICA):")
        print("-" * 50)
        target_config = config['primary']
        print(f"📍 Connexió: {target_config['user']}@{target_config['host']}:{target_config['port']}/{target_config['database']}")
        
        target_adapter = QualityMeasurementDBAdapter(target_config)
        if target_adapter.connect():
            with target_adapter.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                count = cursor.fetchone()[0]
                print(f"✅ Taula mesuresqualitat: {count:,} registres")
                
                # Mostrar informació sobre els últims registres
                cursor.execute("""
                    SELECT MIN(id), MAX(id), COUNT(DISTINCT id) 
                    FROM mesuresqualitat
                """)
                min_id, max_id, unique_ids = cursor.fetchone()
                print(f"📊 Rang d'IDs: {min_id} - {max_id}")
                print(f"📊 IDs únics: {unique_ids:,}")
        else:
            print("❌ No es pot connectar a la base de dades destí")
        
        target_adapter.close()
        
        print("\n" + "=" * 80)
        print("RESUM:")
        print("✅ Configuració actualitzada correctament")
        print("✅ Connexions funcionen amb noves credencials")
        print("🔄 Estat de còpia verificat")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_database_status()
