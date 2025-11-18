"""
Script per inspeccionar l'estructura de les taules
Determina les columnes disponibles a cada taula
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.database_connection import PostgresConn
import json
import os

def inspect_table_structure():
    """Inspecciona l'estructura de totes les taules"""
    
    print("\n" + "="*80)
    print("INSPECCIÓ D'ESTRUCTURA DE TAULES")
    print("="*80)
    
    # Carregar config
    config_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "config", "database", "db_config.json"
    )
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    db_config = list(config.values())[0]
    
    db = PostgresConn(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        port=db_config['port']
    )
    
    schema = '"1000_SQB_qualitat"'
    tables = [
        'mesures_gompc_projectes',
        'mesures_gompc_produccio',
        'mesureshoytom',
        'mesurestorsio',
        'mesureszwick'
    ]
    
    for table in tables:
        print(f"\n{'='*80}")
        print(f"TAULA: {table}")
        print('='*80)
        
        try:
            # Obtenir columnes
            query = f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = '1000_SQB_qualitat'
                AND table_name = %s
                ORDER BY ordinal_position
            """
            
            columns = db.fetchall(query, (table,))
            
            if columns:
                print(f"\nColumnes disponibles ({len(columns)}):")
                print("-" * 80)
                for col in columns:
                    col_name = col[0]
                    col_type = col[1]
                    col_length = col[2] if col[2] else ''
                    print(f"  {col_name:<35} {col_type:<20} {col_length}")
                
                # Intentar obtenir una fila d'exemple
                print(f"\nExemple de dada (primera fila):")
                print("-" * 80)
                try:
                    sample_query = f'SELECT * FROM {schema}.{table} LIMIT 1'
                    sample = db.fetchall(sample_query, ())
                    
                    if sample:
                        print(f"  ✅ Taula conté dades")
                        # Mostrar només primeres columnes per no saturar
                        col_names = [c[0] for c in columns[:10]]
                        print(f"  Primeres columnes: {', '.join(col_names)}")
                    else:
                        print(f"  ⚠️ Taula buida")
                except Exception as e:
                    print(f"  ❌ Error obtenint exemple: {e}")
                
                # Identificar columnes clau
                print(f"\nColumnes clau identificades:")
                print("-" * 80)
                col_names_lower = [c[0].lower() for c in columns]
                
                # Buscar referència
                ref_candidates = [c[0] for c in columns if 'referen' in c[0].lower()]
                if ref_candidates:
                    print(f"  Referència: {ref_candidates}")
                
                # Buscar LOT
                lot_candidates = [c[0] for c in columns if 'lot' in c[0].lower()]
                if lot_candidates:
                    print(f"  LOT: {lot_candidates}")
                
                # Buscar element
                element_candidates = [c[0] for c in columns if 'element' in c[0].lower()]
                if element_candidates:
                    print(f"  Element: {element_candidates}")
                
                # Buscar valor/actual
                value_candidates = [c[0] for c in columns if any(x in c[0].lower() for x in ['valor', 'actual', 'mesur'])]
                if value_candidates:
                    print(f"  Valor: {value_candidates}")
                
                # Buscar nominal
                nominal_candidates = [c[0] for c in columns if 'nominal' in c[0].lower()]
                if nominal_candidates:
                    print(f"  Nominal: {nominal_candidates}")
                
                # Buscar toleràncies
                tol_candidates = [c[0] for c in columns if 'toleran' in c[0].lower()]
                if tol_candidates:
                    print(f"  Toleràncies: {tol_candidates}")
                
            else:
                print(f"  ❌ No s'han trobat columnes (taula no existeix?)")
                
        except Exception as e:
            print(f"  ❌ Error inspeccionant taula: {e}")
    
    db.close()
    print("\n" + "="*80)
    print("INSPECCIÓ COMPLETADA")
    print("="*80)


if __name__ == "__main__":
    inspect_table_structure()
