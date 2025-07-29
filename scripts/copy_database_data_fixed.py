#!/usr/bin/env python3
"""
Script corregit per copiar dades de mesuresqualitat entre bases de dades

Aquest script copia totes les dades de la taula mesuresqualitat
des de la BBDD airflow_db (config_2) cap a documentacio_tecnica (config_1)
tenint en compte l'esquema real de les dades origen.

Ús:
    python copy_database_data_fixed.py
"""

import sys
import os
import logging
import json
import pandas as pd
from pathlib import Path

# Afegir el directori arrel al path per poder importar mòduls
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

def setup_logging():
    """Configura el logging per al script"""
    # Crear directori de logs si no existeix
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/database_copy_fixed.log', encoding='utf-8')
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

def adapt_source_data_to_expected_format(df):
    """
    Adapta les dades de la taula origen al format que espera el QualityMeasurementDBAdapter
    
    Args:
        df: DataFrame amb dades de la taula origen
        
    Returns:
        DataFrame adaptat al format esperat
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Adaptant dades origen al format esperat...")
    
    # Crear còpia del DataFrame
    adapted_df = df.copy()
    
    # Mapatge de columnes origen (minúscules) a format esperat (majúscules)
    column_mapping = {
        'client': 'CLIENT',
        'id_referencia_client': 'REFERENCIA', 
        'id_lot': 'LOT',
        'data_hora': 'DATA_HORA',
        'fase': 'FASE',
        'rivets_type': 'RIVETS_TYPE',
        'cavitat': 'CAVITAT',
        'element': 'Element',
        'pieza': 'Pieza',
        'datum': 'Datum',
        'property': 'Property',
        'nominal': 'Nominal',
        'actual': 'Actual',
        'tolerancia_negativa': 'Tol -',
        'tolerancia_positiva': 'Tol +',
        'desviacio': 'Dev',
        'check_value': 'Check',
        'out_value': 'Out',
        'alignment': 'Alignment'
    }
    
    # Aplicar mapatge només per columnes que existeixen
    existing_mapping = {}
    for source_col, target_col in column_mapping.items():
        if source_col in adapted_df.columns:
            existing_mapping[source_col] = target_col
            logger.debug(f"Mapejant: {source_col} -> {target_col}")
    
    # Aplicar renombrat
    adapted_df = adapted_df.rename(columns=existing_mapping)
    
    # Verificar que tenim les columnes essencials
    required_columns = ['CLIENT', 'REFERENCIA', 'LOT']
    missing_columns = [col for col in required_columns if col not in adapted_df.columns]
    
    if missing_columns:
        logger.error(f"Columnes essencials no trobades després de l'adaptació: {missing_columns}")
        return None
    
    logger.info(f"Dades adaptades correctament. Columnes disponibles: {list(adapted_df.columns)}")
    logger.info(f"Registres adaptats: {len(adapted_df)}")
    
    return adapted_df

def copy_data_between_databases_fixed():
    """
    Versió corregida que adapta les dades origen al format esperat
    
    Returns:
        dict: Resum de la còpia de dades
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== INICIANT CÒPIA CORREGIDA DE DADES ENTRE BBDD ===")
        
        # Carregar configuracions
        configs = load_db_configs()
        if not configs:
            return {
                'success': False,
                'error': 'No es pot carregar la configuració de les BBDD',
                'records_copied': 0
            }
        
        source_config = configs['source']
        target_config = configs['target']
        
        logger.info(f"Origen: {source_config['database']} en {source_config['host']}:{source_config['port']}")
        logger.info(f"Destí: {target_config['database']} en {target_config['host']}:{target_config['port']}")
        
        # Connectar a la BBDD origen
        source_adapter = QualityMeasurementDBAdapter(source_config)
        if not source_adapter.connect():
            return {
                'success': False,
                'error': 'No es pot connectar a la base de dades origen (airflow_db)',
                'records_copied': 0
            }
        
        logger.info("Connexió a BBDD origen establerta")
        
        # Connectar a la BBDD destí
        target_adapter = QualityMeasurementDBAdapter(target_config)
        if not target_adapter.connect():
            source_adapter.close()
            return {
                'success': False,
                'error': 'No es pot connectar a la base de dades destí (documentacio_tecnica)',
                'records_copied': 0
            }
        
        logger.info("Connexió a BBDD destí establerta")
        
        # Pas 1: Verificar/crear esquema a la BBDD destí
        logger.info("Verificant esquema de la taula destí...")
        schema_result = target_adapter.update_table_schema()
        if schema_result['success']:
            logger.info("Esquema de destí verificat/creat correctament")
        else:
            logger.warning(f"Advertència amb esquema destí: {schema_result.get('message', 'Unknown')}")
        
        # Pas 2: Llegir dades de la taula origen en batches per evitar problemes de memòria
        logger.info("Llegint dades de la taula mesuresqualitat origen...")
        
        try:
            with source_adapter.connection.cursor() as cursor:
                # Comptar registres totals
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                total_records = cursor.fetchone()[0]
                logger.info(f"Total registres a la BBDD origen: {total_records}")
                
                if total_records == 0:
                    source_adapter.close()
                    target_adapter.close()
                    return {
                        'success': True,
                        'message': 'No hi ha dades per copiar a la BBDD origen',
                        'records_copied': 0,
                        'records_total': 0
                    }
                
                # Llegir dades en chunks per evitar sobrecàrrega de memòria
                chunk_size = 50000  # Processar 50K registres alhora
                total_copied = 0
                chunk_num = 0
                
                while total_copied < total_records:
                    chunk_num += 1
                    logger.info(f"Processant chunk {chunk_num} (registres {total_copied} a {min(total_copied + chunk_size, total_records)})")
                    
                    # Llegir chunk
                    cursor.execute(f"""
                        SELECT * FROM mesuresqualitat 
                        ORDER BY created_at 
                        LIMIT {chunk_size} OFFSET {total_copied}
                    """)
                    
                    columns = [desc[0] for desc in cursor.description]
                    chunk_data = cursor.fetchall()
                    
                    if not chunk_data:
                        break
                    
                    # Convertir a DataFrame
                    chunk_df = pd.DataFrame(chunk_data, columns=columns)
                    logger.info(f"Chunk llegit: {len(chunk_df)} registres")
                    
                    # Adaptar format
                    adapted_df = adapt_source_data_to_expected_format(chunk_df)
                    if adapted_df is None:
                        source_adapter.close()
                        target_adapter.close()
                        return {
                            'success': False,
                            'error': 'Error adaptant format de les dades',
                            'records_copied': total_copied
                        }
                    
                    # Preparar per inserció
                    logger.info("Preparant chunk per inserció...")
                    prepared_data = target_adapter.prepare_dataset_for_insertion(adapted_df)
                    
                    if prepared_data is None or prepared_data.empty:
                        logger.warning(f"Chunk {chunk_num} no es pot preparar per inserció")
                        total_copied += len(chunk_df)
                        continue
                    
                    # Inserir chunk
                    logger.info(f"Inserint chunk {chunk_num} a la BBDD destí...")
                    insert_result = target_adapter.insert_dataset(prepared_data)
                    
                    if insert_result['success']:
                        logger.info(f"Chunk {chunk_num} inserit: {insert_result['records_inserted']} registres")
                        total_copied += len(chunk_df)
                    else:
                        logger.error(f"Error inserint chunk {chunk_num}: {insert_result.get('error')}")
                        # Continuar amb el següent chunk en cas d'error
                        total_copied += len(chunk_df)
                
                logger.info(f"Processament completat: {total_copied} registres processats")
                
        except Exception as e:
            source_adapter.close()
            target_adapter.close()
            return {
                'success': False,
                'error': f'Error durant el processament: {str(e)}',
                'records_copied': 0
            }
        
        # Tancar connexions
        source_adapter.close()
        target_adapter.close()
        
        # Verificar resultat final
        logger.info("Verificant resultat final...")
        
        # Reconnectar per verificar
        target_adapter_verify = QualityMeasurementDBAdapter(target_config)
        if target_adapter_verify.connect():
            with target_adapter_verify.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                final_count = cursor.fetchone()[0]
                logger.info(f"Registres finals a la BBDD destí: {final_count}")
            target_adapter_verify.close()
        else:
            final_count = -1
        
        return {
            'success': True,
            'message': 'Dades copiades correctament entre bases de dades',
            'records_copied': final_count if final_count > 0 else total_copied,
            'records_total': total_records,
            'source_database': source_config['database'],
            'target_database': target_config['database'],
            'chunks_processed': chunk_num
        }
            
    except Exception as e:
        logger.error(f"Error durant la còpia de dades: {e}")
        return {
            'success': False,
            'error': f'Error inesperat: {str(e)}',
            'records_copied': 0
        }

def main():
    """Funció principal del script"""
    print("="*70)
    print("CÒPIA CORREGIDA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    print("Origen: airflow_db (config_2)")
    print("Destí: documentacio_tecnica (config_1)")
    print("Taula: mesuresqualitat")
    print("Mètode: Processament per chunks (50K registres)")
    print("="*70)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Confirmació abans de procedir
    response = input(f"\n❓ Voleu continuar amb la còpia? Això pot trigar una estona... (S/N): ").strip().upper()
    if response not in ['S', 'SI', 'SÍ', 'Y', 'YES']:
        print("❌ Operació cancel·lada per l'usuari.")
        return 0
    
    try:
        # Executar còpia de dades
        print("\n🔄 Iniciant còpia de dades...")
        result = copy_data_between_databases_fixed()
        
        if result['success']:
            print("\n✅ CÒPIA COMPLETADA CORRECTAMENT!")
            print(f"📊 Registres copiats: {result['records_copied']:,}")
            print(f"📊 Total registres origen: {result['records_total']:,}")
            print(f"📊 Chunks processats: {result.get('chunks_processed', 0)}")
            print(f"🗄️  Origen: {result['source_database']}")
            print(f"🗄️  Destí: {result['target_database']}")
            
        else:
            print("\n❌ ERROR DURANT LA CÒPIA!")
            print(f"Error: {result['error']}")
            if result.get('records_copied', 0) > 0:
                print(f"Registres copiats abans de l'error: {result['records_copied']}")
            
            return 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operació cancel·lada per l'usuari")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        logger.error(f"Error inesperat durant la còpia: {e}")
        return 1
    
    print("\n🏁 Script finalitzat")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
