#!/usr/bin/env python3
"""
Script simplificat per copiar dades de mesuresqualitat entre bases de dades

Aquest script copia totes les dades de la taula mesuresqualitat
des de la BBDD airflow_db (config_2) cap a documentacio_tecnica (config_1)
sense dependre del NetworkScanner.

Ús:
    python copy_database_data_simple.py
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
            logging.FileHandler('logs/database_copy_simple.log', encoding='utf-8')
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

def copy_data_between_databases():
    """
    Copia les dades de la taula mesuresqualitat de la BBDD origen (airflow_db/config_2) 
    cap a la BBDD destí (documentacio_tecnica/config_1)
    
    Returns:
        dict: Resum de la còpia de dades
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== INICIANT CÒPIA SIMPLIFICADA DE DADES ENTRE BBDD ===")
        
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
        
        # Pas 2: Llegir totes les dades de la taula origen
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
                
                # Llegir totes les dades
                cursor.execute("SELECT * FROM mesuresqualitat ORDER BY created_at")
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                logger.info(f"Dades llegides: {len(data)} registres amb {len(columns)} columnes")
                
        except Exception as e:
            source_adapter.close()
            target_adapter.close()
            return {
                'success': False,
                'error': f'Error llegint dades de la BBDD origen: {str(e)}',
                'records_copied': 0
            }
        
        # Pas 3: Convertir a DataFrame per facilitar la inserció
        source_df = pd.DataFrame(data, columns=columns)
        logger.info(f"DataFrame creat amb {len(source_df)} registres")
        
        # Pas 4: Preparar dades per inserció al destí
        logger.info("Preparant dades per inserció...")
        prepared_data = target_adapter.prepare_dataset_for_insertion(source_df)
        
        if prepared_data is None or prepared_data.empty:
            source_adapter.close()
            target_adapter.close()
            return {
                'success': False,
                'error': 'Error preparant les dades per inserció',
                'records_copied': 0
            }
        
        # Pas 5: Inserir a la BBDD destí
        logger.info("Inserint dades a la BBDD destí...")
        insert_result = target_adapter.insert_dataset(prepared_data)
        
        # Tancar connexions
        source_adapter.close()
        target_adapter.close()
        
        if insert_result['success']:
            logger.info(f"Còpia completada: {insert_result['records_inserted']} registres")
            return {
                'success': True,
                'message': 'Dades copiades correctament entre bases de dades',
                'records_copied': insert_result['records_inserted'],
                'records_total': total_records,
                'records_skipped': insert_result.get('skipped_records', 0),
                'source_database': source_config['database'],
                'target_database': target_config['database'],
                'errors': insert_result.get('errors', [])
            }
        else:
            return {
                'success': False,
                'error': insert_result.get('error', 'Error desconegut durant la inserció'),
                'records_copied': insert_result.get('records_inserted', 0),
                'source_database': source_config['database'],
                'target_database': target_config['database']
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
    print("CÒPIA SIMPLIFICADA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    print("Origen: airflow_db (config_2)")
    print("Destí: documentacio_tecnica (config_1)")
    print("Taula: mesuresqualitat")
    print("="*70)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Executar còpia de dades
        print("\n🔄 Iniciant còpia de dades...")
        result = copy_data_between_databases()
        
        if result['success']:
            print("\n✅ CÒPIA COMPLETADA CORRECTAMENT!")
            print(f"📊 Registres copiats: {result['records_copied']:,}")
            print(f"📊 Total registres: {result['records_total']:,}")
            print(f"📊 Registres saltats: {result.get('records_skipped', 0):,}")
            print(f"🗄️  Origen: {result['source_database']}")
            print(f"🗄️  Destí: {result['target_database']}")
            
            if result.get('errors'):
                print(f"\n⚠️  Errors durant la còpia:")
                for error in result['errors']:
                    print(f"   - {error}")
            
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
