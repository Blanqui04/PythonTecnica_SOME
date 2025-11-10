"""
Script de còpia automàtica de dades entre bases de dades
Copia les 4 taules de mesures de airflow_db a documentacio_tecnica

Ús:
    python scripts/sync_databases.py [--full-sync] [--verify-only]
    
    --full-sync: Fa una còpia completa (trunca i recopia tot)
    --verify-only: Només verifica l'estat, no copia res
"""
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch

# Afegir el directori arrel al path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuració de les taules a copiar
TABLES_TO_SYNC = [
    'mesures_gompcnou',
    'mesures_gompc_projectes',  # Nota: "projectes" amb c
    'mesureshoytom',
    'mesurestorsio'  # Nota: "torsio" no "toriso"
]

class DatabaseSync:
    """Gestiona la sincronització entre airflow_db i documentacio_tecnica"""
    
    def __init__(self, config_path: str = None):
        """Inicialitza el sincronitzador"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "database" / "db_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.source_config = config['secondary']  # airflow_db
        self.target_config = config['primary']    # documentacio_tecnica
        
        logger.info(f"Configuració carregada:")
        logger.info(f"  Origen: {self.source_config['database']} @ {self.source_config['host']}")
        logger.info(f"  Destí: {self.target_config['database']} @ {self.target_config['host']}")
    
    def connect_source(self):
        """Connecta a la base de dades origen (airflow_db)"""
        try:
            conn = psycopg2.connect(
                host=self.source_config['host'],
                port=self.source_config['port'],
                database=self.source_config['database'],
                user=self.source_config['user'],
                password=self.source_config['password']
            )
            logger.info(f"✅ Connectat a {self.source_config['database']}")
            return conn
        except Exception as e:
            logger.error(f"❌ Error connectant a origen: {e}")
            raise
    
    def connect_target(self):
        """Connecta a la base de dades destí (documentacio_tecnica)"""
        try:
            conn = psycopg2.connect(
                host=self.target_config['host'],
                port=self.target_config['port'],
                database=self.target_config['database'],
                user=self.target_config['user'],
                password=self.target_config['password']
            )
            logger.info(f"✅ Connectat a {self.target_config['database']}")
            return conn
        except Exception as e:
            logger.error(f"❌ Error connectant a destí: {e}")
            raise
    
    def get_table_count(self, conn, table_name: str, schema: str = 'public') -> int:
        """Obté el nombre de registres d'una taula"""
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.warning(f"⚠️  No es pot comptar {table_name}: {e}")
            return 0
    
    def table_exists(self, conn, table_name: str, schema: str = 'public') -> bool:
        """Verifica si una taula existeix"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    )
                """, (schema, table_name))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error verificant taula {table_name}: {e}")
            return False
    
    def verify_sync_status(self):
        """Verifica l'estat de sincronització de totes les taules"""
        logger.info("\n" + "="*60)
        logger.info("📊 ESTAT DE SINCRONITZACIÓ")
        logger.info("="*60)
        
        source_conn = self.connect_source()
        target_conn = self.connect_target()
        
        try:
            results = []
            for table in TABLES_TO_SYNC:
                source_exists = self.table_exists(source_conn, table, schema='qualitat')
                target_exists = self.table_exists(target_conn, table)
                
                source_count = 0
                target_count = 0
                
                if source_exists:
                    source_count = self.get_table_count(source_conn, table, schema='qualitat')
                
                if target_exists:
                    target_count = self.get_table_count(target_conn, table)
                
                diff = source_count - target_count
                status = "✅" if diff == 0 else ("⚠️" if diff < 1000 else "❌")
                
                results.append({
                    'table': table,
                    'source_count': source_count,
                    'target_count': target_count,
                    'diff': diff,
                    'status': status
                })
                
                logger.info(f"\n{status} {table}:")
                logger.info(f"   Origen: {source_count:,} registres")
                logger.info(f"   Destí:  {target_count:,} registres")
                logger.info(f"   Diferència: {diff:+,} registres")
            
            return results
            
        finally:
            source_conn.close()
            target_conn.close()
    
    def sync_table_incremental(self, table_name: str):
        """Sincronitza una taula de forma incremental (només nous registres)"""
        logger.info(f"\n🔄 Sincronitzant {table_name} (incremental)...")
        
        source_conn = self.connect_source()
        target_conn = self.connect_target()
        
        try:
            # Obtenir última data_hora al destí
            with target_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COALESCE(MAX(data_hora), '1900-01-01'::timestamp) 
                    FROM {table_name}
                """)
                last_sync = cursor.fetchone()[0]
            
            logger.info(f"   Última sincronització: {last_sync}")
            
            # Llegir nous registres de l'origen
            with source_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        client, data_hora, maquina, fase, id_referencia_client, id_lot,
                        cavitat, pieza, element, datum, property, actual, nominal,
                        tolerancia_negativa, tolerancia_positiva, desviacio,
                        check_value, created_at, updated_at
                    FROM qualitat.{table_name}
                    WHERE data_hora > %s
                    ORDER BY data_hora
                """, (last_sync,))
                
                rows = cursor.fetchall()
                logger.info(f"   Nous registres a copiar: {len(rows):,}")
            
            if len(rows) == 0:
                logger.info(f"   ✅ {table_name} ja està sincronitzada")
                return 0
            
            # Inserir al destí
            with target_conn.cursor() as cursor:
                insert_query = f"""
                    INSERT INTO {table_name} (
                        client, data_hora, maquina, fase, id_referencia_client, id_lot,
                        cavitat, pieza, element, datum, property, actual, nominal,
                        tolerancia_negativa, tolerancia_positiva, desviacio,
                        check_value, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT DO NOTHING
                """
                
                execute_batch(cursor, insert_query, rows, page_size=1000)
                target_conn.commit()
            
            logger.info(f"   ✅ {len(rows):,} registres copiats a {table_name}")
            return len(rows)
            
        except Exception as e:
            logger.error(f"   ❌ Error sincronitzant {table_name}: {e}")
            target_conn.rollback()
            return 0
            
        finally:
            source_conn.close()
            target_conn.close()
    
    def sync_table_full(self, table_name: str):
        """Sincronitza una taula completament (trunca i recopia tot)"""
        logger.info(f"\n🔄 Sincronitzant {table_name} (completa)...")
        
        source_conn = self.connect_source()
        target_conn = self.connect_target()
        
        try:
            # Comptar registres origen
            source_count = self.get_table_count(source_conn, table_name, schema='qualitat')
            logger.info(f"   Registres a l'origen: {source_count:,}")
            
            if source_count == 0:
                logger.warning(f"   ⚠️  Taula origen buida, saltant...")
                return 0
            
            # Truncar destí
            with target_conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
                target_conn.commit()
            
            logger.info(f"   Taula destí truncada")
            
            # Copiar en lots de 10,000
            batch_size = 10000
            offset = 0
            total_copied = 0
            
            while True:
                # Llegir lot de l'origen
                with source_conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 
                            client, data_hora, maquina, fase, id_referencia_client, id_lot,
                            cavitat, pieza, element, datum, property, actual, nominal,
                            tolerancia_negativa, tolerancia_positiva, desviacio,
                            check_value, created_at, updated_at
                        FROM qualitat.{table_name}
                        ORDER BY data_hora
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))
                    
                    rows = cursor.fetchall()
                
                if len(rows) == 0:
                    break
                
                # Inserir lot al destí
                with target_conn.cursor() as cursor:
                    insert_query = f"""
                        INSERT INTO {table_name} (
                            client, data_hora, maquina, fase, id_referencia_client, id_lot,
                            cavitat, pieza, element, datum, property, actual, nominal,
                            tolerancia_negativa, tolerancia_positiva, desviacio,
                            check_value, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
                    """
                    
                    execute_batch(cursor, insert_query, rows, page_size=1000)
                    target_conn.commit()
                
                total_copied += len(rows)
                offset += batch_size
                
                logger.info(f"   Progrés: {total_copied:,} / {source_count:,} ({total_copied*100//source_count}%)")
            
            logger.info(f"   ✅ {total_copied:,} registres copiats a {table_name}")
            return total_copied
            
        except Exception as e:
            logger.error(f"   ❌ Error sincronitzant {table_name}: {e}")
            target_conn.rollback()
            return 0
            
        finally:
            source_conn.close()
            target_conn.close()
    
    def sync_all_tables(self, full_sync: bool = False):
        """Sincronitza totes les taules"""
        logger.info("\n" + "="*60)
        logger.info(f"🚀 INICI SINCRONITZACIÓ {'COMPLETA' if full_sync else 'INCREMENTAL'}")
        logger.info("="*60)
        logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = datetime.now()
        results = {}
        
        for table in TABLES_TO_SYNC:
            if full_sync:
                copied = self.sync_table_full(table)
            else:
                copied = self.sync_table_incremental(table)
            
            results[table] = copied
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Resum
        logger.info("\n" + "="*60)
        logger.info("📋 RESUM DE LA SINCRONITZACIÓ")
        logger.info("="*60)
        
        total_copied = 0
        for table, count in results.items():
            logger.info(f"   {table}: {count:,} registres")
            total_copied += count
        
        logger.info(f"\n   Total registres copiats: {total_copied:,}")
        logger.info(f"   Temps total: {duration:.2f} segons")
        logger.info(f"   Velocitat: {total_copied/duration if duration > 0 else 0:.0f} reg/seg")
        
        logger.info("\n✅ SINCRONITZACIÓ COMPLETADA!")
        logger.info("="*60)
        
        return results

def main():
    """Funció principal"""
    parser = argparse.ArgumentParser(description='Sincronitza bases de dades')
    parser.add_argument('--full-sync', action='store_true', 
                       help='Fa una còpia completa (trunca i recopia tot)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Només verifica l\'estat, no copia res')
    
    args = parser.parse_args()
    
    try:
        sync = DatabaseSync()
        
        if args.verify_only:
            sync.verify_sync_status()
        else:
            sync.sync_all_tables(full_sync=args.full_sync)
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
