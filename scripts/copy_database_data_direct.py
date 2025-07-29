#!/usr/bin/env python3
"""
Script de còpia directa de dades entre bases de dades

Aquest script fa una còpia directa de la taula mesuresqualitat
des de airflow_db cap a documentacio_tecnica sense transformacions complexes.

Ús:
    python copy_database_data_direct.py
"""

import sys
import os
import logging
import json
import pandas as pd
import psycopg2
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
            logging.FileHandler('logs/database_copy_direct.log', encoding='utf-8')
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

def connect_to_db(config):
    """Connecta a una base de dades"""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            client_encoding='utf8'
        )
        connection.autocommit = True
        return connection
    except Exception as e:
        print(f"❌ Error connectant a {config['database']}: {e}")
        return None

def ensure_target_table_exists(target_connection):
    """Assegura que la taula destí existeix amb l'esquema correcte"""
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
    
    -- Crear índexs
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_client ON mesuresqualitat(client);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_lot ON mesuresqualitat(id_lot);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_data_hora ON mesuresqualitat(data_hora);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_maquina ON mesuresqualitat(maquina);
    CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_referencia_client ON mesuresqualitat(id_referencia_client);
    """
    
    try:
        with target_connection.cursor() as cursor:
            cursor.execute(create_table_sql)
            logger.info("Taula mesuresqualitat creada/verificada correctament")
            return True
    except Exception as e:
        logger.error(f"Error creant taula: {e}")
        return False

def copy_data_direct():
    """Còpia directa de dades entre bases de dades"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== INICIANT CÒPIA DIRECTA DE DADES ===")
        
        # Carregar configuracions
        configs = load_db_configs()
        if not configs:
            return {'success': False, 'error': 'No es pot carregar configuració'}
        
        # Connectar a origen
        logger.info("Connectant a BBDD origen...")
        source_conn = connect_to_db(configs['source'])
        if not source_conn:
            return {'success': False, 'error': 'No es pot connectar a BBDD origen'}
        
        # Connectar a destí
        logger.info("Connectant a BBDD destí...")
        target_conn = connect_to_db(configs['target'])
        if not target_conn:
            source_conn.close()
            return {'success': False, 'error': 'No es pot connectar a BBDD destí'}
        
        # Crear taula destí si cal
        logger.info("Verificant taula destí...")
        if not ensure_target_table_exists(target_conn):
            source_conn.close()
            target_conn.close()
            return {'success': False, 'error': 'No es pot crear taula destí'}
        
        # Comptar registres origen
        with source_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            total_records = cursor.fetchone()[0]
            logger.info(f"Total registres origen: {total_records:,}")
        
        # Esborrar registres destí existents
        logger.info("Esborrant registres existents al destí...")
        with target_conn.cursor() as cursor:
            cursor.execute("DELETE FROM mesuresqualitat")
            logger.info("Registres existents esborrats")
        
        # Còpia en chunks
        chunk_size = 10000
        total_copied = 0
        chunk_num = 0
        
        logger.info(f"Iniciant còpia en chunks de {chunk_size:,} registres...")
        
        while total_copied < total_records:
            chunk_num += 1
            logger.info(f"Processant chunk {chunk_num} (registres {total_copied:,} a {min(total_copied + chunk_size, total_records):,})")
            
            # Llegir chunk d'origen
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
                    break
                
                logger.info(f"Llegits {len(chunk_data)} registres del chunk {chunk_num}")
            
            # Inserir chunk al destí
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
                ON CONFLICT (id_referencia_some, id_element) 
                DO UPDATE SET
                    valor = EXCLUDED.valor,
                    ok = EXCLUDED.ok,
                    id_referencia_client = EXCLUDED.id_referencia_client,
                    id_lot = EXCLUDED.id_lot,
                    client = EXCLUDED.client,
                    data_hora = EXCLUDED.data_hora,
                    maquina = EXCLUDED.maquina,
                    element = EXCLUDED.element,
                    pieza = EXCLUDED.pieza,
                    datum = EXCLUDED.datum,
                    property = EXCLUDED.property,
                    nominal = EXCLUDED.nominal,
                    actual = EXCLUDED.actual,
                    tolerancia_negativa = EXCLUDED.tolerancia_negativa,
                    tolerancia_positiva = EXCLUDED.tolerancia_positiva,
                    desviacio = EXCLUDED.desviacio,
                    check_value = EXCLUDED.check_value,
                    out_value = EXCLUDED.out_value,
                    alignment = EXCLUDED.alignment,
                    updated_at = CURRENT_TIMESTAMP,
                    fase = EXCLUDED.fase,
                    cavitat = EXCLUDED.cavitat,
                    rivets_type = EXCLUDED.rivets_type
            """
            
            try:
                with target_conn.cursor() as target_cursor:
                    target_cursor.executemany(insert_sql, chunk_data)
                    logger.info(f"Chunk {chunk_num} inserit correctament")
                    total_copied += len(chunk_data)
                    
            except Exception as e:
                logger.error(f"Error inserint chunk {chunk_num}: {e}")
                # Continuar amb el següent chunk
                total_copied += len(chunk_data)
        
        # Verificar resultat final
        with target_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            final_count = cursor.fetchone()[0]
            logger.info(f"Registres finals al destí: {final_count:,}")
        
        # Tancar connexions
        source_conn.close()
        target_conn.close()
        
        return {
            'success': True,
            'message': 'Còpia directa completada correctament',
            'records_total': total_records,
            'records_copied': final_count,
            'chunks_processed': chunk_num,
            'source_database': configs['source']['database'],
            'target_database': configs['target']['database']
        }
        
    except Exception as e:
        logger.error(f"Error durant la còpia directa: {e}")
        return {
            'success': False,
            'error': f'Error inesperat: {str(e)}',
            'records_copied': 0
        }

def main():
    """Funció principal"""
    print("="*70)
    print("CÒPIA DIRECTA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    print("Origen: airflow_db (config_2)")
    print("Destí: documentacio_tecnica (config_1)")
    print("Taula: mesuresqualitat")
    print("Mètode: Còpia directa SQL (10K registres per chunk)")
    print("="*70)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Confirmació
    response = input(f"\n❓ Voleu continuar? Això esborrarà les dades existents al destí! (S/N): ").strip().upper()
    if response not in ['S', 'SI', 'SÍ', 'Y', 'YES']:
        print("❌ Operació cancel·lada per l'usuari.")
        return 0
    
    try:
        print("\n🔄 Iniciant còpia directa...")
        result = copy_data_direct()
        
        if result['success']:
            print("\n✅ CÒPIA DIRECTA COMPLETADA!")
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
        return 1
        
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        return 1
    
    print("\n🏁 Script finalitzat")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
