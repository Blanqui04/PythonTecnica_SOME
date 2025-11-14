#!/usr/bin/env python3
"""
Script per analitzar les columnes de les taules de mesures
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner


def analyze_table_columns():
    """Analitzar les columnes de totes les taules de mesures"""
    print("\n" + "="*80)
    print("ANÀLISI DE COLUMNES DE LES TAULES DE MESURES")
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
        
        # Obtenir totes les taules de mesures
        cursor.execute("""
            SELECT DISTINCT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('qualitat', 'public')
            AND table_name LIKE 'mesures%'
            ORDER BY table_schema, table_name
        """)
        
        tables = cursor.fetchall()
        
        print(f"\nTrobades {len(tables)} taules de mesures\n")
        
        # Columnes que busquem relacionades amb referències
        reference_patterns = [
            'referencia',
            'reference', 
            'ref',
            'id_referencia',
            'id_reference',
            'referencia_client',
            'referencia_some',
            'reference_client',
            'reference_some'
        ]
        
        for schema, table in tables:
            print(f"\n{'='*80}")
            print(f"📋 Taula: {schema}.{table}")
            print(f"{'='*80}")
            
            # Obtenir totes les columnes de la taula
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            
            columns = cursor.fetchall()
            
            print(f"\nTotal columnes: {len(columns)}")
            
            # Filtrar columnes relacionades amb referències
            print(f"\n🔍 Columnes relacionades amb REFERÈNCIES:")
            ref_columns = []
            for col_name, data_type, nullable in columns:
                col_lower = col_name.lower()
                if any(pattern in col_lower for pattern in reference_patterns):
                    ref_columns.append((col_name, data_type, nullable))
                    print(f"   ✅ {col_name} ({data_type}, nullable: {nullable})")
            
            if not ref_columns:
                print(f"   ⚠️  Cap columna de referència trobada")
            
            # Mostrar altres columnes importants
            print(f"\n📊 Altres columnes clau:")
            important_cols = ['client', 'id_lot', 'element', 'pieza', 'datum', 'property', 
                            'data_hora', 'actual', 'nominal', 'cavitat']
            for col_name, data_type, nullable in columns:
                if col_name.lower() in [c.lower() for c in important_cols]:
                    print(f"   • {col_name} ({data_type})")
            
            # Comprovar si hi ha dades amb referències
            if ref_columns:
                print(f"\n📈 Estadístiques de dades amb referències:")
                for col_name, _, _ in ref_columns:
                    try:
                        cursor.execute(f"""
                            SELECT 
                                COUNT(*) as total,
                                COUNT({col_name}) as with_value,
                                COUNT(DISTINCT {col_name}) as unique_values
                            FROM {schema}.{table}
                        """)
                        total, with_value, unique = cursor.fetchone()
                        
                        percentage = (with_value * 100 / total) if total > 0 else 0
                        print(f"   {col_name}:")
                        print(f"      Total registres: {total:,}")
                        print(f"      Amb valor: {with_value:,} ({percentage:.1f}%)")
                        print(f"      Valors únics: {unique:,}")
                        
                        # Mostrar exemples de valors
                        if with_value > 0:
                            cursor.execute(f"""
                                SELECT DISTINCT {col_name}
                                FROM {schema}.{table}
                                WHERE {col_name} IS NOT NULL
                                LIMIT 5
                            """)
                            examples = cursor.fetchall()
                            if examples:
                                examples_str = ", ".join([str(e[0]) for e in examples])
                                print(f"      Exemples: {examples_str}")
                    except Exception as e:
                        print(f"   ⚠️  Error llegint {col_name}: {e}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def search_autoliv_with_all_reference_columns():
    """Buscar AUTOLIV usant totes les possibles columnes de referència"""
    print("\n" + "="*80)
    print("CERCA D'AUTOLIV AMB TOTES LES COLUMNES DE REFERÈNCIA")
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
        
        # Referència a buscar
        search_ref = '663962200'
        
        print(f"\n🔍 Buscant referència: {search_ref}")
        
        # Llista de taules principals
        tables_to_check = [
            'qualitat.mesures_gompc_projectes',
            'qualitat.mesures_gompcnou',
            'qualitat.mesures_gompc_produccio'
        ]
        
        for table in tables_to_check:
            print(f"\n--- Taula: {table} ---")
            
            # Obtenir columnes de la taula
            schema, table_name = table.split('.')
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                AND (
                    LOWER(column_name) LIKE '%referencia%'
                    OR LOWER(column_name) LIKE '%reference%'
                    OR LOWER(column_name) LIKE '%ref%'
                )
            """, (schema, table_name))
            
            ref_columns = [row[0] for row in cursor.fetchall()]
            
            if ref_columns:
                print(f"Columnes de referència trobades: {', '.join(ref_columns)}")
                
                # Buscar en cada columna
                for col in ref_columns:
                    try:
                        cursor.execute(f"""
                            SELECT COUNT(*) as count,
                                   COUNT(DISTINCT {col}) as unique_refs
                            FROM {table}
                            WHERE client = 'AUTOLIV'
                            AND {col} LIKE %s
                        """, (f'%{search_ref}%',))
                        
                        count, unique = cursor.fetchone()
                        
                        if count > 0:
                            print(f"   ✅ {col}: {count} registres, {unique} referències úniques")
                            
                            # Mostrar exemples
                            cursor.execute(f"""
                                SELECT DISTINCT {col}, id_lot, element
                                FROM {table}
                                WHERE client = 'AUTOLIV'
                                AND {col} LIKE %s
                                LIMIT 3
                            """, (f'%{search_ref}%',))
                            
                            examples = cursor.fetchall()
                            for ref, lot, element in examples:
                                print(f"      📌 {ref} | LOT: {lot} | Element: {element}")
                        else:
                            print(f"   ⚠️  {col}: 0 resultats")
                    except Exception as e:
                        print(f"   ❌ Error amb {col}: {e}")
            else:
                print(f"   ⚠️  Cap columna de referència trobada")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar anàlisi"""
    analyze_table_columns()
    search_autoliv_with_all_reference_columns()


if __name__ == "__main__":
    main()
