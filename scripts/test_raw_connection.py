#!/usr/bin/env python3
"""
Test ultra simple sense dependències
"""

import json
import psycopg2
from pathlib import Path

def test_raw_connection():
    """Test de connexió raw sense mòduls"""
    
    print("=" * 70)
    print("TEST RAW DE CONNEXIÓ POSTGRESQL")
    print("=" * 70)
    
    # Llegir configuració directament
    config_path = Path(__file__).parent.parent / "config" / "database" / "db_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    secondary = config['secondary']
    
    print("📋 CONFIGURACIÓ LLEGIDA:")
    print(f"   Host: {secondary['host']}")
    print(f"   Port: {secondary['port']}")
    print(f"   Database: {secondary['database']}")
    print(f"   User: {secondary['user']}")
    print(f"   Password: {'*' * len(secondary['password'])}")
    
    # Crear connection string
    conn_string = f"host={secondary['host']} port={secondary['port']} dbname={secondary['database']} user={secondary['user']} password={secondary['password']}"
    
    print(f"\n📡 Intentant connexió directa...")
    print(f"   String de connexió: host={secondary['host']} port={secondary['port']} dbname={secondary['database']} user={secondary['user']} password=***")
    
    try:
        conn = psycopg2.connect(conn_string)
        print("✅ Connexió EXITOSA!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"📊 Versió PostgreSQL: {version}")
        
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
            print(f"📊 Registres a mesuresqualitat: {count:,}")
        else:
            print("⚠️  Taula mesuresqualitat no existeix")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error de connexió: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_raw_connection()
