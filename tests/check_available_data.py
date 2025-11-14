#!/usr/bin/env python3
"""
Script per veure quines dades reals hi ha a la BD
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.database_connection import PostgresConn
from src.services.network_scanner import NetworkScanner
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_clients():
    """Veure quins clients hi ha"""
    print("\n" + "="*80)
    print("CLIENTS DISPONIBLES")
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
        
        # Comprovar taules disponibles
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('qualitat', 'public')
            AND table_name LIKE 'mesures%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\nTaules de mesures disponibles:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Veure clients disponibles en cada taula
        for table in tables:
            table_name = table[0]
            print(f"\n--- Clients a {table_name} ---")
            
            try:
                cursor.execute(f"""
                    SELECT DISTINCT client, COUNT(*) as count
                    FROM qualitat.{table_name}
                    WHERE client IS NOT NULL
                    GROUP BY client
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                clients = cursor.fetchall()
                for client, count in clients:
                    print(f"  {client}: {count} registres")
                    
            except Exception as e:
                print(f"  Error llegint {table_name}: {e}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def check_autoliv_references():
    """Veure quines referències d'AUTOLIV hi ha"""
    print("\n" + "="*80)
    print("REFERÈNCIES AUTOLIV DISPONIBLES")
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
        
        # Buscar referències que continguin AUTOLIV
        cursor.execute("""
            SELECT DISTINCT id_referencia_client, COUNT(*) as count,
                   MAX(data_hora) as last_measurement
            FROM qualitat.mesures_gompc_projectes
            WHERE UPPER(client) LIKE '%AUTOLIV%'
            GROUP BY id_referencia_client
            ORDER BY count DESC
            LIMIT 20
        """)
        
        refs = cursor.fetchall()
        
        if refs:
            print(f"\nTrobades {len(refs)} referències per AUTOLIV:")
            for ref, count, last in refs:
                print(f"  📊 {ref}: {count} mesures (última: {last})")
        else:
            print("⚠️  Cap referència trobada per AUTOLIV")
            
            # Buscar variants del client
            print("\nProvant variants del nom client...")
            cursor.execute("""
                SELECT DISTINCT client, COUNT(*) as count
                FROM qualitat.mesures_gompc_projectes
                WHERE UPPER(client) LIKE '%AUTO%'
                OR UPPER(client) LIKE '%LIV%'
                GROUP BY client
                ORDER BY count DESC
                LIMIT 10
            """)
            
            variants = cursor.fetchall()
            if variants:
                print("Clients similars trobats:")
                for client, count in variants:
                    print(f"  - {client}: {count} registres")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def check_specific_reference():
    """Buscar una referència específica amb diferents variants"""
    print("\n" + "="*80)
    print("CERCA DE REFERÈNCIA ESPECÍFICA: 663962200")
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
        
        # Buscar la referència amb LIKE
        search_patterns = ['663962200%', '%663962200%', '%663962200B%']
        
        for pattern in search_patterns:
            print(f"\n🔍 Buscant amb pattern: {pattern}")
            cursor.execute("""
                SELECT client, id_referencia_client, COUNT(*) as count,
                       MAX(data_hora) as last_measurement
                FROM qualitat.mesures_gompc_projectes
                WHERE id_referencia_client LIKE %s
                GROUP BY client, id_referencia_client
                ORDER BY count DESC
                LIMIT 5
            """, (pattern,))
            
            results = cursor.fetchall()
            if results:
                for client, ref, count, last in results:
                    print(f"  ✅ {client} - {ref}: {count} mesures (última: {last})")
            else:
                print(f"  ⚠️  Cap resultat")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


def main():
    """Executar totes les comprovacions"""
    check_clients()
    check_autoliv_references()
    check_specific_reference()


if __name__ == "__main__":
    main()
