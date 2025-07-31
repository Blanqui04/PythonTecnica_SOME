#!/usr/bin/env python3
"""
Script per completar la còpia de dades

Continua la còpia des d'on es va aturar automàticament.
"""

import sys
import os
import logging
import json
import psycopg2
import time
from pathlib import Path

def setup_logging():
    """Configura el logging"""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/complete_copy.log', encoding='utf-8')
        ]
    )

def connect_to_db(config):
    """Connecta a una base de dades"""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            client_encoding='utf8',
            connect_timeout=30
        )
        connection.autocommit = True
        return connection
    except Exception as e:
        logging.error(f"Error connectant: {e}")
        return None

def main():
    """Completa la còpia de dades"""
    print("=" * 60)
    print("COMPLETANT CÒPIA DE DADES")
    print("=" * 60)
    
    setup_logging()
    
    # Carregar configuració
    try:
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        source_config = full_config['secondary']  # airflow_db
        target_config = full_config['primary']    # documentacio_tecnica
        
    except Exception as e:
        print(f"❌ Error carregant configuració: {e}")
        return 1
    
    # Connectar
    print("🔗 Connectant a les bases de dades...")
    source_conn = connect_to_db(source_config)
    target_conn = connect_to_db(target_config)
    
    if not source_conn or not target_conn:
        print("❌ Error de connexió")
        return 1
    
    try:
        # Comptar registres
        with source_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            total_origen = cursor.fetchone()[0]
        
        with target_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            total_desti = cursor.fetchone()[0]
        
        print(f"📊 Registres origen: {total_origen:,}")
        print(f"📊 Registres destí: {total_desti:,}")
        print(f"📊 Pendents: {total_origen - total_desti:,}")
        
        if total_desti >= total_origen:
            print("✅ La còpia ja està completa!")
            return 0
        
        # Continuar còpia
        chunk_size = 2000  # Chunks més petits
        current_offset = total_desti
        
        print(f"\n🔄 Continuant des del registre {current_offset:,}")
        
        chunk_num = (current_offset // chunk_size) + 1
        
        while current_offset < total_origen:
            try:
                print(f"📦 Chunk {chunk_num}: registres {current_offset:,} a {min(current_offset + chunk_size, total_origen):,}")
                
                # Llegir chunk
                with source_conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id_referencia_some, id_element, valor, ok, id_referencia_client, 
                               id_lot, client, data_hora, maquina, element, pieza, datum, 
                               property, nominal, actual, tolerancia_negativa, tolerancia_positiva, 
                               desviacio, check_value, out_value, alignment, created_at, 
                               updated_at, fase, cavitat, rivets_type
                        FROM mesuresqualitat 
                        ORDER BY created_at 
                        LIMIT {chunk_size} OFFSET {current_offset}
                    """)
                    
                    chunk_data = cursor.fetchall()
                
                if not chunk_data:
                    break
                
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
                
                with target_conn.cursor() as cursor:
                    cursor.executemany(insert_sql, chunk_data)
                
                current_offset += len(chunk_data)
                chunk_num += 1
                
                print(f"✅ Chunk completat. Total processat: {current_offset:,}")
                
                # Pausa breu
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error en chunk {chunk_num}: {e}")
                print("⏳ Reintentant en 5 segons...")
                time.sleep(5)
                
                # Reconnectar si cal
                try:
                    source_conn.close()
                    target_conn.close()
                except:
                    pass
                
                source_conn = connect_to_db(source_config)
                target_conn = connect_to_db(target_config)
                
                if not source_conn or not target_conn:
                    print("❌ No es pot reconnectar")
                    return 1
        
        # Verificar resultat final
        with target_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            final_count = cursor.fetchone()[0]
        
        print(f"\n🎉 CÒPIA COMPLETADA!")
        print(f"📊 Registres finals: {final_count:,}")
        print(f"📊 Percentatge completat: {(final_count / total_origen) * 100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return 1
    
    finally:
        try:
            source_conn.close()
            target_conn.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
