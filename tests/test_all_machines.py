#!/usr/bin/env python3
"""
Test complet per totes les màquines: gompc_projectes, gompc_produccio, hoytom, torsio
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner


def analyze_all_machines():
    """Analitzar dades disponibles per cada màquina"""
    print("\n" + "="*80)
    print("ANÀLISI DE DADES PER MÀQUINA")
    print("="*80)
    
    scanner = NetworkScanner()
    db_config = scanner.load_db_config()
    
    if not db_config:
        print("[ERROR] No s'ha pogut carregar configuració BD")
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
        
        # Mapeig de taules per màquina/tipus
        machines = {
            'GOMPC Projectes': {
                'table': 'qualitat.mesures_gompc_projectes',
                'description': 'Mesures de projectes (GOMPC)'
            },
            'GOMPC Projectes (Public)': {
                'table': 'public.mesures_gompc_projectes',
                'description': 'Mesures de projectes (GOMPC) - Legacy'
            },
            'GOMPC Nou': {
                'table': 'public.mesures_gompcnou',
                'description': 'Mesures noves (GOMPCNOU)'
            },
            'Hoytom': {
                'table': 'public.mesureshoytom',
                'description': 'Assaigs de tracció (Hoytom)'
            },
            'Torsió': {
                'table': 'public.mesurestorsio',
                'description': 'Assaigs de torsió'
            },
            'MesuresQualitat': {
                'table': 'public.mesuresqualitat',
                'description': 'Taula consolidada de qualitat'
            }
        }
        
        results = {}
        
        for machine_name, config in machines.items():
            table = config['table']
            print(f"\n{'='*80}")
            print(f"MÀQUINA: {machine_name}")
            print(f"Descripció: {config['description']}")
            print(f"Taula: {table}")
            print(f"{'='*80}")
            
            try:
                # Comprovar si la taula té dades
                cursor.execute(f"""
                    SELECT COUNT(*) as total
                    FROM {table}
                """)
                total = cursor.fetchone()[0]
                
                if total == 0:
                    print(f"[WARN] Taula buida - 0 registres")
                    results[machine_name] = {'total': 0, 'has_data': False}
                    continue
                
                print(f"\n[OK] Total registres: {total:,}")
                results[machine_name] = {'total': total, 'has_data': True}
                
                # Clients disponibles
                cursor.execute(f"""
                    SELECT DISTINCT client, COUNT(*) as count
                    FROM {table}
                    WHERE client IS NOT NULL
                    GROUP BY client
                    ORDER BY count DESC
                    LIMIT 10
                """)
                clients = cursor.fetchall()
                
                if clients:
                    print(f"\nClients disponibles ({len(clients)} diferents):")
                    for client, count in clients[:5]:
                        print(f"   - {client}: {count:,} registres")
                    results[machine_name]['clients'] = [c[0] for c in clients]
                
                # Referències disponibles (buscar a totes les columnes possibles)
                ref_columns = ['id_referencia_some', 'id_referencia_client', 'ref_some', 'ref_client', 'reference']
                
                print(f"\nReferències disponibles:")
                for ref_col in ref_columns:
                    try:
                        # Comprovar si la columna existeix
                        cursor.execute(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            AND column_name = %s
                        """, (table.split('.')[1], ref_col))
                        
                        if cursor.fetchone():
                            cursor.execute(f"""
                                SELECT COUNT(DISTINCT CAST({ref_col} AS TEXT)) as unique_refs,
                                       COUNT({ref_col}) as with_value
                                FROM {table}
                                WHERE {ref_col} IS NOT NULL
                            """)
                            unique, with_value = cursor.fetchone()
                            
                            if with_value > 0:
                                percentage = (with_value * 100 / total) if total > 0 else 0
                                print(f"   {ref_col}: {unique:,} referències úniques ({percentage:.1f}% omplert)")
                                
                                # Mostrar exemples
                                cursor.execute(f"""
                                    SELECT DISTINCT CAST({ref_col} AS TEXT)
                                    FROM {table}
                                    WHERE {ref_col} IS NOT NULL
                                    LIMIT 3
                                """)
                                examples = [r[0] for r in cursor.fetchall()]
                                print(f"      Exemples: {', '.join(examples[:3])}")
                    except Exception as e:
                        pass  # Columna no existeix
                
                # LOTs disponibles
                try:
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT id_lot) as unique_lots,
                               COUNT(id_lot) as with_lot
                        FROM {table}
                        WHERE id_lot IS NOT NULL
                    """)
                    unique_lots, with_lot = cursor.fetchone()
                    
                    if with_lot > 0:
                        percentage = (with_lot * 100 / total) if total > 0 else 0
                        print(f"\nLOTs: {unique_lots:,} lots únics ({percentage:.1f}% omplert)")
                        
                        # Exemples de lots
                        cursor.execute(f"""
                            SELECT DISTINCT id_lot, COUNT(*) as count
                            FROM {table}
                            WHERE id_lot IS NOT NULL
                            GROUP BY id_lot
                            ORDER BY count DESC
                            LIMIT 5
                        """)
                        lot_examples = cursor.fetchall()
                        print(f"   Exemples:")
                        for lot, count in lot_examples:
                            print(f"      - {lot}: {count:,} mesures")
                except Exception as e:
                    print(f"   [WARN] No hi ha columna id_lot")
                
                # Elements disponibles (si existeix)
                try:
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT element) as unique_elements
                        FROM {table}
                        WHERE element IS NOT NULL
                    """)
                    unique_elements = cursor.fetchone()[0]
                    print(f"\nElements: {unique_elements:,} elements únics")
                except Exception as e:
                    pass
                
            except Exception as e:
                print(f"[ERROR] Error processant {machine_name}: {e}")
                results[machine_name] = {'total': 0, 'has_data': False, 'error': str(e)}
                # Rollback per continuar amb la següent taula
                try:
                    conn.rollback()
                except:
                    pass
        
        # Resum final
        print(f"\n{'='*80}")
        print("RESUM FINAL")
        print(f"{'='*80}")
        
        for machine, data in results.items():
            if data.get('has_data'):
                print(f"[OK] {machine}: {data['total']:,} registres")
            else:
                print(f"[WARN] {machine}: Sense dades")
        
        cursor.close()
        
    except Exception as e:
        print(f"[ERROR] Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def test_search_by_machine():
    """Provar cerca per màquina específica"""
    print("\n" + "="*80)
    print("PROVES DE CERCA PER MÀQUINA")
    print("="*80)
    
    scanner = NetworkScanner()
    db_config = scanner.load_db_config()
    
    if not db_config:
        print("[ERROR] No s'ha pogut carregar configuració BD")
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
        
        # Test 1: Buscar AUTOLIV 663962200 a GOMPC Projectes
        print(f"\n--- Test 1: AUTOLIV 663962200 a GOMPC Projectes ---")
        cursor.execute("""
            SELECT COUNT(*) as count,
                   COUNT(DISTINCT element) as unique_elements,
                   COUNT(DISTINCT id_lot) as unique_lots
            FROM qualitat.mesures_gompc_projectes
            WHERE UPPER(client) = UPPER('AUTOLIV')
            AND UPPER(CAST(id_referencia_some AS TEXT)) LIKE UPPER('%663962200%')
        """)
        count, elements, lots = cursor.fetchone()
        print(f"   Registres: {count:,}")
        print(f"   Elements únics: {elements:,}")
        print(f"   LOTs únics: {lots:,}")
        
        if count > 0:
            # Mostrar alguns elements
            cursor.execute("""
                SELECT DISTINCT element, property, COUNT(*) as count
                FROM qualitat.mesures_gompc_projectes
                WHERE UPPER(client) = UPPER('AUTOLIV')
                AND UPPER(CAST(id_referencia_some AS TEXT)) LIKE UPPER('%663962200%')
                GROUP BY element, property
                ORDER BY count DESC
                LIMIT 5
            """)
            print(f"   Elements exemple:")
            for element, prop, cnt in cursor.fetchall():
                print(f"      - {element} | {prop}: {cnt} mesures")
        
        cursor.close()
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar tots els tests"""
    analyze_all_machines()
    test_search_by_machine()


if __name__ == "__main__":
    main()
