#!/usr/bin/env python3
"""
Buscar específicament la referència 663962200 en totes les columnes
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner


def search_reference_663962200():
    """Buscar la referència 663962200 en totes les taules i columnes"""
    print("\n" + "="*80)
    print("CERCA DE REFERÈNCIA: 663962200")
    print("="*80)
    
    scanner = NetworkScanner()
    db_config = scanner.load_db_config()
    
    if not db_config:
        print("❌ No s'ha pogut carregar configuració BD")
        return
    
    db_conn = PostgresConn(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password']
    )
    
    try:
        conn = db_conn.connect()
        cursor = conn.cursor()
        
        search_ref = '663962200'
        
        # Taules principals on buscar
        tables_config = [
            ('public', 'mesuresqualitat', ['id_referencia_some', 'id_referencia_client']),
            ('qualitat', 'mesures_gompc_projectes', ['id_referencia_some', 'id_referencia_client']),
            ('public', 'mesures_gompc_projectes', ['id_referencia_some', 'id_referencia_client']),
            ('public', 'mesureshoytom', ['ref_some', 'ref_client', 'ref_cliente']),
            ('public', 'mesures_gompcnou', ['id_referencia_client']),
        ]
        
        total_found = 0
        
        for schema, table, ref_columns in tables_config:
            print(f"\n{'='*80}")
            print(f"📋 {schema}.{table}")
            print(f"{'='*80}")
            
            table_found = False
            
            for col in ref_columns:
                try:
                    # Comprovar si la columna existeix
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        AND table_name = %s
                        AND column_name = %s
                    """, (schema, table, col))
                    
                    if not cursor.fetchone():
                        continue
                    
                    # Buscar amb LIKE
                    cursor.execute(f"""
                        SELECT COUNT(*) as count
                        FROM {schema}.{table}
                        WHERE {col} LIKE %s
                    """, (f'%{search_ref}%',))
                    
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        print(f"\n✅ Columna: {col}")
                        print(f"   Registres trobats: {count:,}")
                        table_found = True
                        total_found += count
                        
                        # Obtenir exemples
                        cursor.execute(f"""
                            SELECT {col}, client, id_lot, element
                            FROM {schema}.{table}
                            WHERE {col} LIKE %s
                            LIMIT 5
                        """, (f'%{search_ref}%',))
                        
                        examples = cursor.fetchall()
                        print(f"   Exemples:")
                        for ref, client, lot, element in examples:
                            print(f"      📌 {ref} | Client: {client} | LOT: {lot} | Element: {element}")
                    else:
                        print(f"   ⚠️  Columna {col}: 0 resultats")
                        
                except Exception as e:
                    print(f"   ❌ Error amb {col}: {e}")
            
            if not table_found:
                print(f"   ℹ️  Cap registre trobat en aquesta taula")
        
        print(f"\n{'='*80}")
        print(f"📊 TOTAL REGISTRES TROBATS: {total_found:,}")
        print(f"{'='*80}")
        
        # Buscar també per AUTOLIV sense referència específica
        print(f"\n{'='*80}")
        print("AUTOLIV: REFERÈNCIES DISPONIBLES")
        print(f"{'='*80}")
        
        cursor.execute("""
            SELECT DISTINCT id_referencia_client, COUNT(*) as count
            FROM public.mesuresqualitat
            WHERE client = 'AUTOLIV'
            AND id_referencia_client IS NOT NULL
            AND id_referencia_client != '.'
            AND id_referencia_client != '0'
            GROUP BY id_referencia_client
            ORDER BY count DESC
            LIMIT 20
        """)
        
        autoliv_refs = cursor.fetchall()
        
        if autoliv_refs:
            print(f"\nReferències AUTOLIV trobades ({len(autoliv_refs)}):")
            for ref, count in autoliv_refs:
                print(f"   📊 {ref}: {count:,} registres")
                if search_ref in str(ref):
                    print(f"      ⭐ AQUESTA CONTÉ {search_ref}!")
        else:
            print("   ⚠️  Cap referència client trobada per AUTOLIV")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar cerca"""
    search_reference_663962200()


if __name__ == "__main__":
    main()
