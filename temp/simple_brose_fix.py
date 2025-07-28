#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solución directa para consultar datos BROSE válidos
"""

import sys
import json
import logging
from pathlib import Path

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_db_config():
    """Carrega la configuració de la base de dades"""
    try:
        config_path = Path(__file__).parent / "config" / "database" / "db_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error carregant configuració BBDD: {e}")
        return None

def find_valid_brose_data():
    """Trova dades BROSE vàlides evitant errors de conversió"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== BUSCANT DADES BROSE VÀLIDES ===")
        
        with adapter.connection.cursor() as cursor:
            # Assegurar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            logger.info("✅ Client encoding configurat a UTF8")
            
            # Analitzar contingut del camp actual sense conversions
            logger.info("\n--- Analitzant contingut del camp 'actual' ---")
            cursor.execute("""
                SELECT 
                    actual as raw_value,
                    LENGTH(actual) as length,
                    ASCII(LEFT(actual, 1)) as first_char_ascii,
                    element,
                    projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                LIMIT 20
            """)
            
            raw_samples = cursor.fetchall()
            logger.info("Exemples de valors 'actual' en brut:")
            for actual, length, first_ascii, element, projecte in raw_samples:
                display_value = f"'{actual}'" if actual is not None else 'NULL'
                logger.info(f"  Valor: {display_value}, Longitud: {length}, ASCII: {first_ascii}, Element: {element}")
            
            # Buscar només registres amb valors que semblen numèrics
            logger.info("\n--- Buscant valors numèrics vàlids ---")
            cursor.execute("""
                SELECT 
                    actual,
                    nominal,
                    element,
                    projecte,
                    data_mesura
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL 
                  AND LENGTH(actual) > 0
                  AND actual NOT IN ('', 'NULL', 'nan', 'NaN')
                  AND actual NOT LIKE '%[^0-9.-]%'
                LIMIT 10
            """)
            
            numeric_candidates = cursor.fetchall()
            if numeric_candidates:
                logger.info("Candidats amb valors aparentment numèrics:")
                for actual, nominal, element, projecte, data in numeric_candidates:
                    logger.info(f"  Actual: '{actual}', Nominal: '{nominal}', Element: '{element}', Data: {data}")
                
                # Ara intentar la conversió segura
                logger.info("\n--- Convertint a numeric amb precisió ---")
                cursor.execute("""
                    SELECT 
                        actual,
                        CASE WHEN actual ~ '^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$' 
                             THEN actual::numeric(15,6) 
                             ELSE NULL END as actual_numeric,
                        nominal,
                        CASE WHEN nominal ~ '^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$' 
                             THEN nominal::numeric(15,6) 
                             ELSE NULL END as nominal_numeric,
                        element
                    FROM mesuresqualitat 
                    WHERE client LIKE 'BROSE%'
                      AND actual IS NOT NULL 
                      AND LENGTH(actual) > 0
                      AND actual NOT IN ('', 'NULL', 'nan', 'NaN')
                    LIMIT 5
                """)
                
                converted_results = cursor.fetchall()
                if converted_results:
                    logger.info("RESULTATS AMB PRECISIÓ COMPLETA:")
                    for actual_raw, actual_num, nominal_raw, nominal_num, element in converted_results:
                        logger.info(f"  Element: {element}")
                        logger.info(f"    Actual: '{actual_raw}' → {actual_num}")
                        logger.info(f"    Nominal: '{nominal_raw}' → {nominal_num}")
                        logger.info("")
            else:
                logger.warning("No s'han trobat candidats numèrics!")
            
            # Estadístiques de qualitat de dades
            logger.info("\n--- Estadístiques de qualitat ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_brose,
                    COUNT(CASE WHEN actual IS NULL THEN 1 END) as actual_null,
                    COUNT(CASE WHEN actual = '' THEN 1 END) as actual_empty,
                    COUNT(CASE WHEN LENGTH(actual) > 0 AND actual NOT IN ('', 'NULL', 'nan') THEN 1 END) as actual_non_empty
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            stats = cursor.fetchone()
            total, null_count, empty_count, non_empty = stats
            
            logger.info(f"Qualitat de dades BROSE:")
            logger.info(f"  Total registres: {total:,}")
            logger.info(f"  'actual' NULL: {null_count:,} ({null_count/total*100:.1f}%)")
            logger.info(f"  'actual' buit: {empty_count:,} ({empty_count/total*100:.1f}%)")
            logger.info(f"  'actual' no buit: {non_empty:,} ({non_empty/total*100:.1f}%)")
    
    finally:
        adapter.close()
    
    return True

def create_final_working_query():
    """Crea la consulta final que funcionarà"""
    
    query_content = """-- CONSULTA DEFINITIVA QUE FUNCIONA PER BROSE
-- ===============================================

-- IMPORTANT: Executa sempre primer aquests comandaments:
SET CLIENT_ENCODING TO 'UTF8';

-- Consulta segura que evita errors de conversió:
SELECT 
    client,
    element,
    actual as actual_raw,
    CASE WHEN actual ~ '^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$' 
         THEN actual::numeric(15,6) 
         ELSE NULL END as actual_numeric_precision,
    nominal as nominal_raw,
    CASE WHEN nominal ~ '^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$' 
         THEN nominal::numeric(15,6) 
         ELSE NULL END as nominal_numeric_precision,
    projecte,
    data_mesura::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND LENGTH(actual) > 0
  AND actual NOT IN ('', 'NULL', 'nan', 'NaN')
ORDER BY data_mesura DESC
LIMIT 10;

-- Consulta més simple si la anterior no funciona:
SELECT 
    client,
    element,
    actual,
    nominal,
    projecte
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND actual != ''
  AND LENGTH(actual) > 0
LIMIT 10;

-- Per veure només els valors numèrics convertibles:
SELECT 
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual ~ '^-?[0-9]*\.?[0-9]+$'
  AND nominal ~ '^-?[0-9]*\.?[0-9]+$'
LIMIT 5;"""
    
    query_file = Path(__file__).parent / "brose_final_query.sql"
    with open(query_file, 'w', encoding='utf-8') as f:
        f.write(query_content)
    
    logger.info(f"Consulta final guardada a: {query_file}")
    
    print("\n" + "="*80)
    print("CONSULTA FINAL QUE FUNCIONARÀ:")
    print("="*80)
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("")
    print("SELECT client, element, actual, nominal, projecte")
    print("FROM mesuresqualitat") 
    print("WHERE client LIKE 'BROSE%'")
    print("  AND actual IS NOT NULL")
    print("  AND actual != ''")
    print("  AND LENGTH(actual) > 0")
    print("LIMIT 10;")
    print("="*80)

if __name__ == "__main__":
    find_valid_brose_data()
    create_final_working_query()
