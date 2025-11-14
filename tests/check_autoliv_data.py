#!/usr/bin/env python3
"""
Script per veure l'estructura de dades d'AUTOLIV
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner


def check_autoliv_structure():
    """Veure l'estructura de dades d'AUTOLIV"""
    print("\n" + "="*80)
    print("ESTRUCTURA DE DADES AUTOLIV")
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
        
        # Veure mostra de registres AUTOLIV
        cursor.execute("""
            SELECT 
                client,
                id_referencia_client,
                id_lot,
                element,
                pieza,
                datum,
                property,
                data_hora
            FROM qualitat.mesures_gompc_projectes
            WHERE UPPER(client) LIKE '%AUTOLIV%'
            ORDER BY data_hora DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"\nMostra de {len(rows)} registres AUTOLIV:")
            print("-" * 120)
            for row in rows:
                client, ref, lot, element, pieza, datum, prop, data = row
                print(f"Client: {client}")
                print(f"  Ref: {ref} | LOT: {lot} | Element: {element} | Pieza: {pieza} | Datum: {datum} | Property: {prop}")
                print(f"  Data: {data}")
                print("-" * 120)
        else:
            print("⚠️  Cap registre AUTOLIV trobat")
        
        # Comprovar quins camps tenen valors
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(id_referencia_client) as with_ref,
                COUNT(id_lot) as with_lot,
                COUNT(element) as with_element,
                COUNT(pieza) as with_pieza
            FROM qualitat.mesures_gompc_projectes
            WHERE UPPER(client) LIKE '%AUTOLIV%'
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, with_ref, with_lot, with_element, with_pieza = stats
            print(f"\nEstadístiques AUTOLIV:")
            print(f"  Total registres: {total}")
            print(f"  Amb id_referencia_client: {with_ref} ({with_ref*100/total if total > 0 else 0:.1f}%)")
            print(f"  Amb id_lot: {with_lot} ({with_lot*100/total if total > 0 else 0:.1f}%)")
            print(f"  Amb element: {with_element} ({with_element*100/total if total > 0 else 0:.1f}%)")
            print(f"  Amb pieza: {with_pieza} ({with_pieza*100/total if total > 0 else 0:.1f}%)")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def check_all_clients_with_references():
    """Veure quins clients tenen referències"""
    print("\n" + "="*80)
    print("CLIENTS AMB REFERÈNCIES DISPONIBLES")
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
        
        cursor.execute("""
            SELECT 
                client,
                COUNT(DISTINCT id_referencia_client) as num_refs,
                COUNT(*) as total_records,
                MAX(data_hora) as last_measurement
            FROM qualitat.mesures_gompc_projectes
            WHERE id_referencia_client IS NOT NULL
            GROUP BY client
            ORDER BY total_records DESC
            LIMIT 15
        """)
        
        clients = cursor.fetchall()
        
        if clients:
            print(f"\nClients amb referències ({len(clients)}):")
            for client, num_refs, total, last in clients:
                print(f"  📊 {client}: {num_refs} referències diferents, {total} registres (última: {last})")
                
                # Mostrar algunes referències d'exemple
                cursor.execute("""
                    SELECT DISTINCT id_referencia_client
                    FROM qualitat.mesures_gompc_projectes
                    WHERE client = %s
                    AND id_referencia_client IS NOT NULL
                    ORDER BY id_referencia_client
                    LIMIT 3
                """, (client,))
                
                refs = cursor.fetchall()
                if refs:
                    refs_str = ", ".join([r[0] for r in refs])
                    print(f"     Exemples: {refs_str}")
        else:
            print("⚠️  Cap client amb referències trobat")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar comprovacions"""
    check_autoliv_structure()
    check_all_clients_with_references()


if __name__ == "__main__":
    main()
