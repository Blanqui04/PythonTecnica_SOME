#!/usr/bin/env python3
"""
Script per inspeccionar l'estructura de la taula mesuresqualitat a la BBDD origen

Aquest script examina l'esquema i contingut de la taula mesuresqualitat
a la base de dades airflow_db per entendre la seva estructura.
"""

import sys
import os
import json
from pathlib import Path

# Afegir el directori arrel al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

def inspect_source_table():
    """Inspecciona l'estructura de la taula origen"""
    
    try:
        # Carregar configuració
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        source_config = full_config['secondary']  # airflow_db
        
        print("=" * 70)
        print("INSPECCIÓ DE LA TAULA MESURESQUALITAT - AIRFLOW_DB")
        print("=" * 70)
        print(f"Host: {source_config['host']}:{source_config['port']}")
        print(f"Database: {source_config['database']}")
        print(f"User: {source_config['user']}")
        
        # Connectar
        adapter = QualityMeasurementDBAdapter(source_config)
        if not adapter.connect():
            print("❌ No es pot connectar a la base de dades")
            return
        
        with adapter.connection.cursor() as cursor:
            # 1. Obtenir estructura de la taula
            print("\n📋 ESTRUCTURA DE LA TAULA:")
            print("-" * 50)
            
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'mesuresqualitat' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            for i, (col_name, data_type, is_nullable, default_val) in enumerate(columns, 1):
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default = f" DEFAULT {default_val}" if default_val else ""
                print(f"{i:2d}. {col_name:<25} {data_type:<20} {nullable}{default}")
            
            # 2. Comptar registres
            print(f"\n📊 ESTADÍSTIQUES:")
            print("-" * 50)
            
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            total_records = cursor.fetchone()[0]
            print(f"Total registres: {total_records:,}")
            
            # 3. Mostrar algunes files d'exemple
            print(f"\n📄 PRIMER REGISTRE D'EXEMPLE:")
            print("-" * 50)
            
            cursor.execute("SELECT * FROM mesuresqualitat LIMIT 1")
            sample_data = cursor.fetchone()
            column_names = [desc[0] for desc in cursor.description]
            
            if sample_data:
                for col_name, value in zip(column_names, sample_data):
                    # Truncar valors llargs
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    print(f"{col_name:<25}: {str_value}")
            
            # 4. Verificar si existeixen columnes clau
            print(f"\n🔍 VERIFICACIÓ DE COLUMNES CLAU:")
            print("-" * 50)
            
            expected_columns = ['client', 'id_referencia_client', 'id_lot', 'data_hora', 'element']
            existing_columns = [col[0] for col in columns]
            
            for col in expected_columns:
                if col in existing_columns:
                    print(f"✅ {col}: PRESENT")
                else:
                    print(f"❌ {col}: NO PRESENT")
            
            # 5. Mostrar columnes úniques disponibles
            print(f"\n📂 TOTES LES COLUMNES DISPONIBLES:")
            print("-" * 50)
            
            for i, col_name in enumerate(existing_columns, 1):
                print(f"{i:2d}. {col_name}")
        
        adapter.close()
        
    except Exception as e:
        print(f"❌ Error durant la inspecció: {e}")

if __name__ == "__main__":
    inspect_source_table()
