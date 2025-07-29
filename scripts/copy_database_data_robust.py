#!/usr/bin/env python3
"""
Script de còpia robusta amb capacitat de represa

Aquest script fa una còpia de la taula mesuresqualitat amb capacitat
de reprendre des d'on es va aturar en cas d'error.

Ús:
    python copy_database_data_robust.py
"""

import sys
import os
import logging
import json
import psycopg2
import time
from pathlib import Path

def setup_logging():
    """Configura el logging per al script"""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/database_copy_robust.log', encoding='utf-8')
        ]
    )

def load_db_configs():
    """Carrega les configuracions de BBDD"""
    try:
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        return {
            'source': full_config['secondary'],  # airflow_db
            'target': full_config['primary']     # documentacio_tecnica
        }
    except Exception as e:
        print(f"❌ Error carregant configuració: {e}")
        return None

def connect_to_db(config, retries=3):
    """Connecta a una base de dades amb reintentos"""
    for attempt in range(retries):
        try:
            connection = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                client_encoding='utf8',
                connect_timeout=30  # Timeout de connexió
            )
            connection.autocommit = True
            return connection
        except Exception as e:
            if attempt < retries - 1:
                print(f"⚠️  Intent {attempt + 1} fallit, reintentant en 5 segons...")
                time.sleep(5)
            else:
                print(f"❌ Error connectant després de {retries} intents: {e}")
                return None

def get_current_count(connection):
    """Obté el nombre actual de registres a la taula destí"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            return cursor.fetchone()[0]
    except:
        return 0

def ensure_target_table_exists(target_connection):
    """Assegura que la taula destí existeix"""
    logger = logging.getLogger(__name__)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS mesuresqualitat (
        id_referencia_some character varying(100) NOT NULL,
        id_element character varying(100) NOT NULL,
        valor numeric(15,6),
        ok boolean,
        id_referencia_client character varying(100),
        id_lot character varying(100),
        client character varying(100),
        data_hora timestamp without time zone,
        maquina character varying(50) DEFAULT 'gompc',
        element character varying(200),
        pieza character varying(200),
        datum character varying(200),
        property character varying(200),
        nominal numeric(15,6),
        actual numeric(15,6),
        tolerancia_negativa numeric(15,6),
        tolerancia_positiva numeric(15,6),
        desviacio numeric(15,6),
        check_value character varying(100),
        out_value character varying(100),
        alignment character varying(200),
        created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
        fase character varying(100),
        cavitat character varying(100),
        rivets_type character varying(100),
        CONSTRAINT mesuresqualitat_pkey PRIMARY KEY (id_referencia_some, id_element)
    );
    
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_client ON mesuresqualitat(client);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_lot ON mesuresqualitat(id_lot);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_data_hora ON mesuresqualitat(data_hora);
    """
    
    try:
        with target_connection.cursor() as cursor:
            cursor.execute(create_table_sql)
            logger.info("Taula mesuresqualitat verificada")
            return True
    except Exception as e:
        logger.error(f"Error creant taula: {e}")
        return False

def copy_data_robust():
    """Còpia robusta amb capacitat de represa"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== INICIANT CÒPIA ROBUSTA DE DADES ===")
        
        configs = load_db_configs()
        if not configs:
            return {'success': False, 'error': 'No es pot carregar configuració'}
        
        chunk_size = 5000  # Chunks més petits per evitar timeouts
        max_retries = 3
        
        # Connectar inicialment
        logger.info("Establint connexions inicials...")
        source_conn = connect_to_db(configs['source'])
        if not source_conn:
            return {'success': False, 'error': 'No es pot connectar a BBDD origen'}
        
        target_conn = connect_to_db(configs['target'])
        if not target_conn:
            source_conn.close()
            return {'success': False, 'error': 'No es pot connectar a BBDD destí'}
        
        # Crear taula destí si cal
        if not ensure_target_table_exists(target_conn):
            source_conn.close()
            target_conn.close()
            return {'success': False, 'error': 'No es pot crear taula destí'}
        
        # Comptar registres origen
        with source_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            total_records = cursor.fetchone()[0]
            logger.info(f"Total registres origen: {total_records:,}")
        
        # Verificar si és continuació o nou inici
        current_count = get_current_count(target_conn)
        logger.info(f"Registres actuals al destí: {current_count:,}")
        
        if current_count > 0:
            response = input(f"Hi ha {current_count:,} registres al destí. Voleu continuar (C) o començar de nou (N)? ").strip().upper()
            if response == 'N':
                logger.info("Esborrant registres existents...")
                with target_conn.cursor() as cursor:
                    cursor.execute("DELETE FROM mesuresqualitat")
                current_count = 0
        
        # Iniciar/continuar còpia
        total_copied = current_count
        chunk_num = (current_count // chunk_size) + 1
        
        logger.info(f"Iniciant des del chunk {chunk_num} (offset: {total_copied:,})")
        
        # Tancar connexions inicials
        source_conn.close()
        target_conn.close()
        
        while total_copied < total_records:
            retry_count = 0
            chunk_success = False
            
            while retry_count < max_retries and not chunk_success:
                try:
                    # Reconnectar per cada chunk per evitar timeouts
                    source_conn = connect_to_db(configs['source'])
                    target_conn = connect_to_db(configs['target'])
                    
                    if not source_conn or not target_conn:
                        logger.error("No es pot reconnectar")
                        retry_count += 1
                        continue
                    
                    logger.info(f"Processant chunk {chunk_num} (registres {total_copied:,} a {min(total_copied + chunk_size, total_records):,})")
                    
                    # Llegir chunk
                    with source_conn.cursor() as source_cursor:
                        source_cursor.execute(f"""
                            SELECT id_referencia_some, id_element, valor, ok, id_referencia_client, 
                                   id_lot, client, data_hora, maquina, element, pieza, datum, 
                                   property, nominal, actual, tolerancia_negativa, tolerancia_positiva, 
                                   desviacio, check_value, out_value, alignment, created_at, 
                                   updated_at, fase, cavitat, rivets_type
                            FROM mesuresqualitat 
                            ORDER BY created_at 
                            LIMIT {chunk_size} OFFSET {total_copied}
                        """)
                        
                        chunk_data = source_cursor.fetchall()
                    
                    if not chunk_data:
                        chunk_success = True
                        break
                    
                    logger.info(f"Llegits {len(chunk_data)} registres")
                    
                    # Inserir chunk
                    insert_sql = """
                        INSERT INTO mesuresqualitat (
                            id_referencia_some, id_element, valor, ok, id_referencia_client, 
                            id_lot, client, data_hora, maquina, element, pieza, datum, 
                            property, nominal, actual, tolerancia_negativa, tolerancia_positiva, 
                            desviacio, check_value, out_value, alignment, created_at, 
                            updated_at, fase, cavitat, rivets_type
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (id_referencia_some, id_element) DO NOTHING
                    """
                    
                    with target_conn.cursor() as target_cursor:
                        target_cursor.executemany(insert_sql, chunk_data)
                    
                    logger.info(f"Chunk {chunk_num} inserit correctament")
                    total_copied += len(chunk_data)
                    chunk_num += 1
                    chunk_success = True
                    
                    # Tancar connexions
                    source_conn.close()
                    target_conn.close()
                    
                    # Pausa breu entre chunks
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error en chunk {chunk_num}, intent {retry_count + 1}: {e}")
                    retry_count += 1
                    
                    try:
                        if source_conn:
                            source_conn.close()
                        if target_conn:
                            target_conn.close()
                    except:
                        pass
                    
                    if retry_count < max_retries:
                        logger.info(f"Reintentant en 10 segons...")
                        time.sleep(10)
            
            if not chunk_success:
                logger.error(f"Chunk {chunk_num} fallit després de {max_retries} intents")
                break
        
        # Verificar resultat final
        final_conn = connect_to_db(configs['target'])
        if final_conn:
            final_count = get_current_count(final_conn)
            final_conn.close()
        else:
            final_count = total_copied
        
        return {
            'success': True,
            'message': 'Còpia robusta completada',
            'records_total': total_records,
            'records_copied': final_count,
            'chunks_processed': chunk_num - 1,
            'source_database': configs['source']['database'],
            'target_database': configs['target']['database']
        }
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        return {
            'success': False,
            'error': f'Error inesperat: {str(e)}',
            'records_copied': 0
        }

def main():
    """Funció principal"""
    print("="*70)
    print("CÒPIA ROBUSTA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    print("Origen: airflow_db (config_2)")
    print("Destí: documentacio_tecnica (config_1)")
    print("Taula: mesuresqualitat")
    print("Mètode: Còpia robusta amb represa (5K registres per chunk)")
    print("Funcionalitats:")
    print("  - Reconnexió automàtica")
    print("  - Capacitat de represa")
    print("  - Gestió d'errors")
    print("="*70)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        print("\n🔄 Iniciant còpia robusta...")
        result = copy_data_robust()
        
        if result['success']:
            print("\n✅ CÒPIA ROBUSTA COMPLETADA!")
            print(f"📊 Registres origen: {result['records_total']:,}")
            print(f"📊 Registres copiats: {result['records_copied']:,}")
            print(f"📊 Chunks processats: {result['chunks_processed']}")
            print(f"🗄️  Origen: {result['source_database']}")
            print(f"🗄️  Destí: {result['target_database']}")
        else:
            print(f"\n❌ ERROR: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Operació cancel·lada per l'usuari")
        print("💡 Podeu reprendre executant l'script de nou")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        return 1
    
    print("\n🏁 Script finalitzat")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
