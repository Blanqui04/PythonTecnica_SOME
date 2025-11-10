"""
Script CORREGIT per copiar taules de airflow_db.qualitat a documentacio_tecnica.public
Mapeja columnes segons el tipus de taula i afegeix el camp 'maquina' manualment
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

# Configuració de les taules amb els seus tipus de màquina
TABLES_CONFIG = {
    'mesures_gompcnou': {
        'machine': 'gompcnou',
        'type': 'dimensional'
    },
    'mesures_gompc_projectes': {
        'machine': 'gompc_projectes',
        'type': 'dimensional'
    },
    'mesureshoytom': {
        'machine': 'hoytom',
        'type': 'hoytom'
    },
    'mesurestorsio': {
        'machine': 'torsio',
        'type': 'torsio'
    }
}

def copy_dimensional_table(source_conn, target_conn, table_name, machine_name):
    """
    Copia taules dimensionals (gompcnou i gompc_projectes).
    Aquestes tenen 28 columnes similars.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"📋 COPIANT TAULA DIMENSIONAL: {table_name}")
    logger.info(f"   Màquina: {machine_name}")
    logger.info(f"{'='*70}")
    
    try:
        # 1. DROP i CREATE taula destí
        with target_conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            create_sql = f"""
            CREATE TABLE {table_name} (
                client VARCHAR(255),
                data_hora TIMESTAMP,
                maquina VARCHAR(50),
                fase VARCHAR(255),
                id_referencia_client VARCHAR(255),
                id_lot VARCHAR(255),
                cavitat VARCHAR(255),
                pieza VARCHAR(255),
                element VARCHAR(255),
                datum VARCHAR(255),
                property VARCHAR(255),
                actual NUMERIC,
                nominal NUMERIC,
                tolerancia_negativa NUMERIC,
                tolerancia_positiva NUMERIC,
                desviacio NUMERIC,
                check_value VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_sql)
            target_conn.commit()
        
        logger.info("   ✅ Taula creada")
        
        # 2. Comptar registres origen
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table_name}")
            total_count = cursor.fetchone()[0]
        
        logger.info(f"   📊 Total registres: {total_count:,}")
        
        if total_count == 0:
            logger.warning("   ⚠️  Taula buida")
            return 0
        
        # 3. Copiar dades en lots
        batch_size = 10000
        offset = 0
        total_copied = 0
        
        logger.info("   📥 Copiant dades...")
        
        while True:
            # Llegir lot - IMPORTANT: afegim 'maquina' com a literal
            with source_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        client,
                        data_hora,
                        '{machine_name}' as maquina,
                        fase,
                        id_referencia_client,
                        id_lot,
                        cavitat,
                        pieza,
                        element,
                        datum,
                        property,
                        actual,
                        nominal,
                        tolerancia_negativa,
                        tolerancia_positiva,
                        desviacio,
                        check_value,
                        created_at,
                        updated_at
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
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                execute_batch(cursor, insert_sql, rows, page_size=1000)
                target_conn.commit()
            
            total_copied += len(rows)
            offset += batch_size
            
            progress = (total_copied * 100) // total_count if total_count > 0 else 0
            logger.info(f"      ⏳ {total_copied:,} / {total_count:,} ({progress}%)")
        
        # 4. Crear índexs
        logger.info("   🔍 Creant índexs...")
        with target_conn.cursor() as cursor:
            indexes = [
                f"CREATE INDEX idx_{table_name}_client ON {table_name}(client)",
                f"CREATE INDEX idx_{table_name}_data_hora ON {table_name}(data_hora)",
                f"CREATE INDEX idx_{table_name}_maquina ON {table_name}(maquina)",
                f"CREATE INDEX idx_{table_name}_ref_client ON {table_name}(id_referencia_client)",
                f"CREATE INDEX idx_{table_name}_lot ON {table_name}(id_lot)",
                f"CREATE INDEX idx_{table_name}_element ON {table_name}(element)"
            ]
            for idx_sql in indexes:
                cursor.execute(idx_sql)
            target_conn.commit()
        
        logger.info(f"   ✅ COMPLETAT: {total_copied:,} registres copiats")
        return total_copied
        
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        target_conn.rollback()
        raise

def copy_hoytom_table(source_conn, target_conn, table_name, machine_name):
    """
    Copia taula hoytom (testing de tracció) amb 46 columnes específiques.
    Mapeja les columnes hoytom a l'estructura estàndard.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"📋 COPIANT TAULA HOYTOM: {table_name}")
    logger.info(f"   Màquina: {machine_name}")
    logger.info(f"{'='*70}")
    
    try:
        # 1. DROP i CREATE
        with target_conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            create_sql = f"""
            CREATE TABLE {table_name} (
                client VARCHAR(255),
                data_hora TIMESTAMP,
                maquina VARCHAR(50),
                fase VARCHAR(255),
                id_referencia_client VARCHAR(255),
                id_lot VARCHAR(255),
                cavitat VARCHAR(255),
                pieza VARCHAR(255),
                element VARCHAR(255),
                datum VARCHAR(255),
                property VARCHAR(255),
                actual NUMERIC,
                nominal NUMERIC,
                tolerancia_negativa NUMERIC,
                tolerancia_positiva NUMERIC,
                desviacio NUMERIC,
                check_value VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_sql)
            target_conn.commit()
        
        logger.info("   ✅ Taula creada")
        
        # 2. Comptar registres
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table_name}")
            total_count = cursor.fetchone()[0]
        
        logger.info(f"   📊 Total registres: {total_count:,}")
        
        if total_count == 0:
            logger.warning("   ⚠️  Taula buida")
            return 0
        
        # 3. Copiar dades mapeant columnes hoytom
        batch_size = 1000  # Més petit per hoytom
        offset = 0
        total_copied = 0
        
        logger.info("   📥 Copiant dades...")
        
        while True:
            # Mapegem columnes específiques de hoytom
            with source_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        COALESCE(proveedor, 'Unknown') as client,
                        fecha_ensayo as data_hora,
                        '{machine_name}' as maquina,
                        operacion as fase,
                        ref_client as id_referencia_client,
                        operacion_lot_fabric_n as id_lot,
                        NULL as cavitat,
                        denom_probeta as pieza,
                        tipo_ensayo as element,
                        NULL as datum,
                        'Força Màxima' as property,
                        fuerza_maxima_fm as actual,
                        f1 as nominal,
                        NULL as tolerancia_negativa,
                        NULL as tolerancia_positiva,
                        NULL as desviacio,
                        modo_rotura as check_value,
                        COALESCE(created_at, NOW()) as created_at,
                        COALESCE(updated_at, NOW()) as updated_at
                    FROM qualitat.{table_name}
                    ORDER BY fecha_ensayo
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
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                execute_batch(cursor, insert_sql, rows, page_size=500)
                target_conn.commit()
            
            total_copied += len(rows)
            offset += batch_size
            
            progress = (total_copied * 100) // total_count if total_count > 0 else 0
            logger.info(f"      ⏳ {total_copied:,} / {total_count:,} ({progress}%)")
        
        # 4. Índexs
        logger.info("   🔍 Creant índexs...")
        with target_conn.cursor() as cursor:
            cursor.execute(f"CREATE INDEX idx_{table_name}_maquina ON {table_name}(maquina)")
            cursor.execute(f"CREATE INDEX idx_{table_name}_data_hora ON {table_name}(data_hora)")
            target_conn.commit()
        
        logger.info(f"   ✅ COMPLETAT: {total_copied:,} registres copiats")
        return total_copied
        
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        target_conn.rollback()
        raise

def copy_torsio_table(source_conn, target_conn, table_name, machine_name):
    """
    Copia taula torsio (testing de parell) amb 38 columnes específiques.
    Mapeja les columnes torsio a l'estructura estàndard.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"📋 COPIANT TAULA TORSIO: {table_name}")
    logger.info(f"   Màquina: {machine_name}")
    logger.info(f"{'='*70}")
    
    try:
        # 1. DROP i CREATE
        with target_conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            create_sql = f"""
            CREATE TABLE {table_name} (
                client VARCHAR(255),
                data_hora TIMESTAMP,
                maquina VARCHAR(50),
                fase VARCHAR(255),
                id_referencia_client VARCHAR(255),
                id_lot VARCHAR(255),
                cavitat VARCHAR(255),
                pieza VARCHAR(255),
                element VARCHAR(255),
                datum VARCHAR(255),
                property VARCHAR(255),
                actual NUMERIC,
                nominal NUMERIC,
                tolerancia_negativa NUMERIC,
                tolerancia_positiva NUMERIC,
                desviacio NUMERIC,
                check_value VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_sql)
            target_conn.commit()
        
        logger.info("   ✅ Taula creada")
        
        # 2. Comptar registres
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table_name}")
            total_count = cursor.fetchone()[0]
        
        logger.info(f"   📊 Total registres: {total_count:,}")
        
        if total_count == 0:
            logger.warning("   ⚠️  Taula buida")
            return 0
        
        # 3. Copiar dades mapeant columnes torsio
        batch_size = 500
        offset = 0
        total_copied = 0
        
        logger.info("   📥 Copiant dades...")
        
        while True:
            # Mapegem columnes específiques de torsio
            with source_conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        COALESCE(familia, 'Unknown') as client,
                        DataHoraCorrect as data_hora,
                        '{machine_name}' as maquina,
                        operacio as fase,
                        ref_some as id_referencia_client,
                        lot as id_lot,
                        NULL as cavitat,
                        item as pieza,
                        tipassaig as element,
                        NULL as datum,
                        'Torque' as property,
                        torque as actual,
                        NULL as nominal,
                        NULL as tolerancia_negativa,
                        NULL as tolerancia_positiva,
                        NULL as desviacio,
                        status as check_value,
                        NOW() as created_at,
                        NOW() as updated_at
                    FROM qualitat.{table_name}
                    ORDER BY id
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
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                execute_batch(cursor, insert_sql, rows, page_size=100)
                target_conn.commit()
            
            total_copied += len(rows)
            offset += batch_size
            
            progress = (total_copied * 100) // total_count if total_count > 0 else 0
            logger.info(f"      ⏳ {total_copied:,} / {total_count:,} ({progress}%)")
        
        # 4. Índexs
        logger.info("   🔍 Creant índexs...")
        with target_conn.cursor() as cursor:
            cursor.execute(f"CREATE INDEX idx_{table_name}_maquina ON {table_name}(maquina)")
            cursor.execute(f"CREATE INDEX idx_{table_name}_data_hora ON {table_name}(data_hora)")
            target_conn.commit()
        
        logger.info(f"   ✅ COMPLETAT: {total_copied:,} registres copiats")
        return total_copied
        
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        target_conn.rollback()
        raise

def main():
    """Funció principal"""
    logger.info("\n" + "="*70)
    logger.info("🚀 CÒPIA INICIAL DE TAULES (VERSIÓ CORREGIDA)")
    logger.info("="*70)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Origen: airflow_db.qualitat (172.26.11.201)")
    logger.info(f"Destí: documentacio_tecnica.public (172.26.11.201)")
    
    # Carregar configuració
    config_path = Path(__file__).parent.parent / "config" / "database" / "db_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    source_config = config['secondary']  # airflow_db
    target_config = config['primary']    # documentacio_tecnica
    
    # Connectar a bases de dades
    logger.info(f"\n🔌 Connectant a bases de dades...")
    
    source_conn = psycopg2.connect(
        host=source_config['host'],
        port=source_config['port'],
        database=source_config['database'],
        user=source_config['user'],
        password=source_config['password']
    )
    logger.info(f"   ✅ Connectat a {source_config['database']}")
    
    target_conn = psycopg2.connect(
        host=target_config['host'],
        port=target_config['port'],
        database=target_config['database'],
        user=target_config['user'],
        password=target_config['password']
    )
    logger.info(f"   ✅ Connectat a {target_config['database']}")
    
    start_time = datetime.now()
    results = {}
    
    try:
        # Processar cada taula segons el seu tipus
        for table_name, table_config in TABLES_CONFIG.items():
            table_type = table_config['type']
            machine_name = table_config['machine']
            
            if table_type == 'dimensional':
                copied = copy_dimensional_table(source_conn, target_conn, table_name, machine_name)
            elif table_type == 'hoytom':
                copied = copy_hoytom_table(source_conn, target_conn, table_name, machine_name)
            elif table_type == 'torsio':
                copied = copy_torsio_table(source_conn, target_conn, table_name, machine_name)
            
            results[table_name] = copied
        
        # Resum final
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "="*70)
        logger.info("📊 RESUM FINAL")
        logger.info("="*70)
        
        total_records = 0
        for table_name, count in results.items():
            logger.info(f"   {table_name}: {count:,} registres")
            total_records += count
        
        logger.info(f"\n   🎉 TOTAL: {total_records:,} registres copiats")
        logger.info(f"   ⏱️  Temps: {duration}")
        logger.info("\n✅ MIGRACIÓ COMPLETADA AMB ÈXIT!")
        
    except Exception as e:
        logger.error(f"\n❌ ERROR DURANT LA MIGRACIÓ: {e}")
        raise
    finally:
        source_conn.close()
        target_conn.close()
        logger.info("\n🔌 Connexions tancades")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
