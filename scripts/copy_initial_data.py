"""
Script per copiar taules de airflow_db.qualitat a documentacio_tecnica.public
Executa aquesta còpia INICIAL una sola vegada
"""
import sys
import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TABLES_TO_COPY = [
    'mesures_gompcnou',
    'mesures_gompc_projectes',
    'mesureshoytom',
    'mesurestorsio'
]

def copy_table_structure_and_data(source_conn, target_conn, table_name):
    """Copia l'estructura i dades d'una taula"""
    logger.info(f"\n{'='*60}")
    logger.info(f"📋 Copiant taula: {table_name}")
    logger.info(f"{'='*60}")
    
    try:
        # 1. Obtenir estructura de la taula
        with source_conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'qualitat' AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
        
        logger.info(f"   Columnes trobades: {len(columns)}")
        
        # 2. Crear taula al destí (DROP si existeix)
        logger.info(f"   Creant taula a documentacio_tecnica...")
        with target_conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            # Crear taula amb estructura simplificada
            create_sql = f"""
            CREATE TABLE {table_name} (
                id_referencia_some SERIAL,
                id_element BIGSERIAL,
                client VARCHAR(100),
                data_hora TIMESTAMP,
                maquina VARCHAR(50),
                fase VARCHAR(100),
                id_referencia_client VARCHAR(100),
                id_lot VARCHAR(100),
                cavitat VARCHAR(50),
                pieza VARCHAR(200),
                element VARCHAR(200),
                datum VARCHAR(200),
                property VARCHAR(200),
                actual DOUBLE PRECISION,
                nominal DOUBLE PRECISION,
                tolerancia_negativa DOUBLE PRECISION,
                tolerancia_positiva DOUBLE PRECISION,
                desviacio DOUBLE PRECISION,
                check_value VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT {table_name}_pkey PRIMARY KEY (id_referencia_some, id_element)
            )
            """
            cursor.execute(create_sql)
            target_conn.commit()
        
        logger.info(f"   ✅ Taula creada")
        
        # 3. Comptar registres origen
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table_name}")
            total_count = cursor.fetchone()[0]
        
        logger.info(f"   Registres a copiar: {total_count:,}")
        
        if total_count == 0:
            logger.warning(f"   ⚠️  Taula buida, saltant còpia de dades")
            return 0
        
        # 4. Copiar dades en lots
        batch_size = 10000
        offset = 0
        total_copied = 0
        
        while True:
            # Llegir lot
            with source_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        client, data_hora, maquina, fase, id_referencia_client, id_lot,
                        cavitat, pieza, element, datum, property, actual, nominal,
                        tolerancia_negativa, tolerancia_positiva, desviacio,
                        check_value, created_at, updated_at
                    FROM qualitat.{table_name}
                    ORDER BY data_hora
                    LIMIT {batch_size} OFFSET {offset}
                """)
                rows = cursor.fetchall()
            
            if len(rows) == 0:
                break
            
            # Inserir lot
            with target_conn.cursor() as cursor:
                insert_sql = f"""
                    INSERT INTO {table_name} (
                        client, data_hora, maquina, fase, id_referencia_client, id_lot,
                        cavitat, pieza, element, datum, property, actual, nominal,
                        tolerancia_negativa, tolerancia_positiva, desviacio,
                        check_value, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_batch(cursor, insert_sql, rows, page_size=1000)
                target_conn.commit()
            
            total_copied += len(rows)
            offset += batch_size
            
            progress = (total_copied * 100) // total_count if total_count > 0 else 0
            logger.info(f"   Progrés: {total_copied:,} / {total_count:,} ({progress}%)")
        
        # 5. Crear índexs
        logger.info(f"   Creant índexs...")
        with target_conn.cursor() as cursor:
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_client ON {table_name}(client)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_lot ON {table_name}(id_lot)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_data_hora ON {table_name}(data_hora)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_ref_client ON {table_name}(id_referencia_client)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_element ON {table_name}(element)"
            ]
            for idx_sql in indexes:
                cursor.execute(idx_sql)
            target_conn.commit()
        
        logger.info(f"   ✅ {total_copied:,} registres copiats amb èxit!")
        return total_copied
        
    except Exception as e:
        logger.error(f"   ❌ Error copiant {table_name}: {e}")
        target_conn.rollback()
        raise

def main():
    """Funció principal"""
    logger.info("\n" + "="*60)
    logger.info("🚀 CÒPIA INICIAL DE TAULES")
    logger.info("="*60)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Origen: airflow_db.qualitat")
    logger.info(f"Destí: documentacio_tecnica.public")
    
    # Carregar configuració
    config_path = Path(__file__).parent.parent / "config" / "database" / "db_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    source_config = config['secondary']  # airflow_db
    target_config = config['primary']    # documentacio_tecnica
    
    # Connectar
    logger.info(f"\nConnectant a bases de dades...")
    source_conn = psycopg2.connect(
        host=source_config['host'],
        port=source_config['port'],
        database=source_config['database'],
        user=source_config['user'],
        password=source_config['password']
    )
    logger.info(f"✅ Connectat a {source_config['database']}")
    
    target_conn = psycopg2.connect(
        host=target_config['host'],
        port=target_config['port'],
        database=target_config['database'],
        user=target_config['user'],
        password=target_config['password']
    )
    logger.info(f"✅ Connectat a {target_config['database']}")
    
    start_time = datetime.now()
    results = {}
    
    try:
        # Copiar cada taula
        for table in TABLES_TO_COPY:
            copied = copy_table_structure_and_data(source_conn, target_conn, table)
            results[table] = copied
        
        # Resum
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("📊 RESUM DE LA CÒPIA")
        logger.info("="*60)
        
        total_copied = 0
        for table, count in results.items():
            logger.info(f"   {table}: {count:,} registres")
            total_copied += count
        
        logger.info(f"\n   Total registres copiats: {total_copied:,}")
        logger.info(f"   Temps total: {duration:.2f} segons")
        logger.info(f"   Velocitat: {total_copied/duration if duration > 0 else 0:.0f} reg/seg")
        
        logger.info("\n✅ CÒPIA INICIAL COMPLETADA AMB ÈXIT!")
        logger.info("="*60)
        
        logger.info("\n📝 Pròxims passos:")
        logger.info("   1. Configurar Airflow DAG per sincronització diària")
        logger.info("   2. Testejar l'aplicació: python main_app.py")
        logger.info("   3. Verificar capacity studies, search, dimensional study")
        
    except Exception as e:
        logger.error(f"\n❌ Error fatal durant la còpia: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        source_conn.close()
        target_conn.close()
        logger.info("\nConnexions tancades")

if __name__ == "__main__":
    print("\n⚠️  ADVERTÈNCIA: Aquest script farà DROP de les taules existents!")
    print("Taules que es copiaran:")
    for table in TABLES_TO_COPY:
        print(f"  • {table}")
    print("\nVols continuar? (escriu 'SI' per confirmar)")
    
    response = input("> ").strip().upper()
    if response == "SI":
        main()
    else:
        print("\n❌ Còpia cancel·lada per l'usuari")
        sys.exit(0)
