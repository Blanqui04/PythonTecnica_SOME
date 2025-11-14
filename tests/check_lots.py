#!/usr/bin/env python3
"""
Script per veure com es guarden els LOTs realment
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner


def check_lot_structure():
    """Veure estructura dels LOTs"""
    print("\n" + "="*80)
    print("ESTRUCTURA DELS LOTS")
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
        
        # Veure exemples de LOTs per AUTOLIV
        cursor.execute("""
            SELECT DISTINCT id_lot, COUNT(*) as count
            FROM qualitat.mesures_gompc_projectes
            WHERE client = 'AUTOLIV'
            AND id_lot IS NOT NULL
            GROUP BY id_lot
            ORDER BY count DESC
            LIMIT 20
        """)
        
        lots = cursor.fetchall()
        
        if lots:
            print(f"\nLOTs disponibles per AUTOLIV ({len(lots)}):")
            for lot, count in lots:
                print(f"  📦 {lot}: {count} mesures")
                
                # Veure si el LOT conté la referència
                if '663962200' in str(lot):
                    print(f"     ⭐ Aquest LOT conté 663962200!")
        else:
            print("⚠️  Cap LOT trobat per AUTOLIV")
        
        # Buscar LOTs que continguin 663962200
        print("\n" + "="*80)
        print("CERCA DE LOTS AMB 663962200")
        print("="*80)
        
        cursor.execute("""
            SELECT id_lot, COUNT(*) as count,
                   MIN(element) as sample_element
            FROM qualitat.mesures_gompc_projectes
            WHERE client = 'AUTOLIV'
            AND id_lot LIKE '%663962200%'
            GROUP BY id_lot
            ORDER BY count DESC
        """)
        
        matching_lots = cursor.fetchall()
        
        if matching_lots:
            print(f"\nLOTs que contenen '663962200': {len(matching_lots)}")
            for lot, count, element in matching_lots:
                print(f"  ✅ {lot}: {count} mesures, element exemple: {element}")
        else:
            print("⚠️  Cap LOT conté '663962200'")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar comprovació"""
    check_lot_structure()


if __name__ == "__main__":
    main()
