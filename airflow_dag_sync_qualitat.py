"""
DAG Airflow per sincronitzar dades de qualitat cada nit
airflow_db.qualitat → documentacio_tecnica.qualitat

Aquest DAG copia les 4 taules de mesures cada nit a les 00:00
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

# Configuració
DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

TABLES = [
    'mesures_gompcnou',
    'mesures_gompc_projectes',
    'mesureshoytom',
    'mesurestorsio'
]

def sync_table(table_name, **context):
    """Sincronitza una taula de airflow_db a documentacio_tecnica"""
    
    # Hooks per les dues bases de dades
    # Nota: Configurar aquestes connexions a Airflow UI → Admin → Connections
    source_hook = PostgresHook(postgres_conn_id='airflow_db')
    target_hook = PostgresHook(postgres_conn_id='documentacio_tecnica')
    
    source_conn = source_hook.get_conn()
    target_conn = target_hook.get_conn()
    
    try:
        # Comptar registres origen
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table_name}")
            count = cursor.fetchone()[0]
        
        print(f"[INFO] {table_name}: {count:,} registres a l'origen")
        
        if count == 0:
            print(f"[INFO] {table_name}: Taula buida, saltant")
            return
        
        # Truncar taula destí
        with target_conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE qualitat.{table_name}")
            target_conn.commit()
        
        print(f"[INFO] {table_name}: Taula destí truncada")
        
        # Copiar dades
        with source_conn.cursor() as source_cursor:
            source_cursor.execute(f"SELECT * FROM qualitat.{table_name}")
            
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
                    
                    query = f"INSERT INTO qualitat.{table_name} ({columns_str}) VALUES ({placeholders})"
                    target_cursor.executemany(query, rows)
                    target_conn.commit()
                    copied += len(rows)
                    
                    print(f"[INFO] {table_name}: {copied:,} / {count:,} registres copiats")
        
        print(f"[OK] {table_name}: Sincronització completada ({copied:,} registres)")
        
    except Exception as e:
        print(f"[ERROR] {table_name}: {e}")
        raise
    finally:
        source_conn.close()
        target_conn.close()

# Crear DAG
with DAG(
    'sync_qualitat_db_nightly',
    default_args=DEFAULT_ARGS,
    description='Sincronització nocturna de dades de qualitat',
    schedule_interval='0 0 * * *',  # Cada dia a les 00:00
    catchup=False,
    tags=['database', 'sync', 'qualitat'],
) as dag:
    
    # Crear una tasca per cada taula
    sync_tasks = []
    for table in TABLES:
        task = PythonOperator(
            task_id=f'sync_{table}',
            python_callable=sync_table,
            op_kwargs={'table_name': table},
        )
        sync_tasks.append(task)
    
    # Les taules es poden sincronitzar en paral·lel
    # (no hi ha dependències entre elles)
