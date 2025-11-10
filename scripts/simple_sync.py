"""
Script simple per copiar dades de airflow_db.qualitat a documentacio_tecnica.qualitat
"""
import psycopg2
import json
from pathlib import Path
from datetime import datetime

def simple_sync():
    """Copia totes les dades d'una BD a l'altra utilitzant INSERT...SELECT"""
    
    # Carregar configuració
    config_path = Path(__file__).parent.parent / "config" / "database" / "db_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    source_config = config['secondary']  # airflow_db
    target_config = config['primary']    # documentacio_tecnica
    target_config['user'] = 'administrador'
    target_config['password'] = 'Xan1212$%'
    
    tables = [
        'mesures_gompcnou',
        'mesures_gompc_projectes',
        'mesureshoytom',
        'mesurestorsio'
    ]
    
    print("\n" + "="*70)
    print("SINCRONITZACIO SIMPLE: airflow_db → documentacio_tecnica")
    print("="*70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_copied = 0
    
    for table in tables:
        print(f"\n[INFO] Processant {table}...")
        
        try:
            # Connexió a origen
            source_conn = psycopg2.connect(
                host=source_config['host'],
                port=source_config['port'],
                database=source_config['database'],
                user=source_config['user'],
                password=source_config['password']
            )
            
            # Connexió a destí  
            target_conn = psycopg2.connect(
                host=target_config['host'],
                port=target_config['port'],
                database=target_config['database'],
                user=target_config['user'],
                password=target_config['password']
            )
            target_conn.autocommit = True
            
            # Comptar registres origen
            with source_conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table}")
                count_source = cursor.fetchone()[0]
            
            print(f"   Registres a l'origen: {count_source:,}")
            
            if count_source == 0:
                print(f"   [INFO] Taula buida, saltant...")
                source_conn.close()
                target_conn.close()
                continue
            
            # Truncar taula destí
            with target_conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE qualitat.{table}")
                print(f"   [OK] Taula destí truncada")
            
            # Copiar dades amb cursors regulars
            with source_conn.cursor() as source_cursor:
                source_cursor.execute(f"SELECT * FROM qualitat.{table}")
                
                # Obtenir noms de columnes
                columns = [desc[0] for desc in source_cursor.description]
                columns_str = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                with target_conn.cursor() as target_cursor:
                    batch_size = 5000
                    copied = 0
                    
                    while True:
                        rows = source_cursor.fetchmany(batch_size)
                        if not rows:
                            break
                        
                        # Inserir batch
                        query = f"INSERT INTO qualitat.{table} ({columns_str}) VALUES ({placeholders})"
                        target_cursor.executemany(query, rows)
                        copied += len(rows)
                        print(f"   [INFO] Copiats {copied:,} / {count_source:,} registres...", end='\r')
                    
                    print(f"   [OK] Total copiats: {copied:,} registres" + " " * 20)
                    total_copied += copied
            
            source_conn.close()
            target_conn.close()
            
        except Exception as e:
            print(f"   [ERROR] Error: {e}")
            continue
    
    print("\n" + "="*70)
    print(f"RESUM: {total_copied:,} registres copiats en total")
    print("="*70 + "\n")

if __name__ == "__main__":
    simple_sync()
