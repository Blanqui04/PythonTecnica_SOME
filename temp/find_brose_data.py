#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test correcto para encontrar datos BROSE válidos
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

def analyze_brose_data():
    """Analitza les dades BROSE per trobar el problema real"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== ANÀLISI DETALLADA DE DADES BROSE ===")
        
        with adapter.connection.cursor() as cursor:
            # Assegurar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            
            # Anàlisi 1: Tipus de valors en el camp 'actual'
            logger.info("\n--- ANÀLISI 1: Contingut del camp 'actual' ---")
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN actual IS NULL THEN 'NULL'
                        WHEN actual = '' THEN 'EMPTY_STRING'
                        WHEN actual ~ '^-?[0-9]+\.?[0-9]*$' THEN 'VALID_NUMBER'
                        WHEN actual ~ '^-?[0-9]+$' THEN 'INTEGER'
                        ELSE 'OTHER'
                    END as value_type,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                GROUP BY 1
                ORDER BY count DESC
            """)
            
            value_types = cursor.fetchall()
            logger.info("Tipus de valors en 'actual':")
            for value_type, count, percentage in value_types:
                logger.info(f"  {value_type}: {count:,} ({percentage}%)")
            
            # Anàlisi 2: Exemples de cada tipus
            logger.info("\n--- ANÀLISI 2: Exemples de valors ---")
            
            # Valors vàlids
            cursor.execute("""
                SELECT actual, nominal, element, projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL 
                  AND actual != ''
                  AND actual ~ '^-?[0-9]+\.?[0-9]*$'
                LIMIT 5
            """)
            
            valid_examples = cursor.fetchall()
            if valid_examples:
                logger.info("Exemples de valors VÀLIDS:")
                for actual, nominal, element, projecte in valid_examples:
                    logger.info(f"  Actual: '{actual}', Nominal: '{nominal}', Element: '{element}', Projecte: '{projecte}'")
            else:
                logger.warning("No s'han trobat valors vàlids!")
            
            # Valors problemàtics
            cursor.execute("""
                SELECT actual, nominal, element, projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL 
                  AND actual != ''
                  AND actual !~ '^-?[0-9]+\.?[0-9]*$'
                LIMIT 5
            """)
            
            invalid_examples = cursor.fetchall()
            if invalid_examples:
                logger.info("Exemples de valors PROBLEMÀTICS:")
                for actual, nominal, element, projecte in invalid_examples:
                    logger.info(f"  Actual: '{actual}', Nominal: '{nominal}', Element: '{element}', Projecte: '{projecte}'")
            
            # Anàlisi 3: Consulta que funcionarà
            logger.info("\n--- ANÀLISI 3: Consulta correcta ---")
            cursor.execute("""
                SELECT 
                    actual::numeric(15,6) as actual_precision,
                    nominal::numeric(15,6) as nominal_precision,
                    element,
                    projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL 
                  AND actual != ''
                  AND actual ~ '^-?[0-9]+\.?[0-9]*$'
                  AND nominal IS NOT NULL 
                  AND nominal != ''
                  AND nominal ~ '^-?[0-9]+\.?[0-9]*$'
                LIMIT 5
            """)
            
            correct_results = cursor.fetchall()
            if correct_results:
                logger.info("RESULTATS CORRECTES amb tots els decimals:")
                for actual, nominal, element, projecte in correct_results:
                    logger.info(f"  Actual: {actual}, Nominal: {nominal}, Element: '{element}', Projecte: '{projecte}'")
            else:
                logger.warning("No s'han trobat resultats amb la consulta correcta!")
            
            # Anàlisi 4: Estadístiques finals
            logger.info("\n--- ANÀLISI 4: Estadístiques ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_brose,
                    COUNT(CASE WHEN actual IS NOT NULL AND actual != '' AND actual ~ '^-?[0-9]+\.?[0-9]*$' THEN 1 END) as valid_actual,
                    COUNT(CASE WHEN nominal IS NOT NULL AND nominal != '' AND nominal ~ '^-?[0-9]+\.?[0-9]*$' THEN 1 END) as valid_nominal,
                    COUNT(CASE WHEN actual IS NOT NULL AND actual != '' AND actual ~ '^-?[0-9]+\.?[0-9]*$' 
                               AND nominal IS NOT NULL AND nominal != '' AND nominal ~ '^-?[0-9]+\.?[0-9]*$' THEN 1 END) as both_valid
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            stats = cursor.fetchone()
            total, valid_actual, valid_nominal, both_valid = stats
            
            logger.info(f"Estadístiques BROSE:")
            logger.info(f"  Total registres: {total:,}")
            logger.info(f"  'actual' vàlid: {valid_actual:,} ({valid_actual/total*100:.1f}%)")
            logger.info(f"  'nominal' vàlid: {valid_nominal:,} ({valid_nominal/total*100:.1f}%)")
            logger.info(f"  Ambdós vàlids: {both_valid:,} ({both_valid/total*100:.1f}%)")
    
    finally:
        adapter.close()
    
    return True

def generate_working_queries():
    """Genera consultes que funcionen"""
    
    queries = """
CONSULTES QUE FUNCIONEN PER BROSE
=================================

IMPORTANT: Executa sempre primer:
SET CLIENT_ENCODING TO 'UTF8';

1. CONSULTA BÀSICA (només valors numèrics vàlids):
--------------------------------------------------
SELECT 
    actual::numeric(15,6) as actual_full_precision,
    nominal::numeric(15,6) as nominal_full_precision
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND actual != ''
  AND actual ~ '^-?[0-9]+\.?[0-9]*$'
  AND nominal IS NOT NULL 
  AND nominal != ''
  AND nominal ~ '^-?[0-9]+\.?[0-9]*$'
LIMIT 5;

2. CONSULTA AMB CONTEXT (element i projecte):
--------------------------------------------
SELECT 
    client,
    projecte,
    element,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    "tol -"::numeric(15,6) as tol_minus,
    "tol +"::numeric(15,6) as tol_plus
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND actual != ''
  AND actual ~ '^-?[0-9]+\.?[0-9]*$'
LIMIT 10;

3. ESTADÍSTIQUES AMB PRECISIÓ COMPLETA:
---------------------------------------
SELECT 
    COUNT(*) as total_valid_records,
    AVG(actual::numeric(15,6)) as avg_actual_full_precision,
    STDDEV(actual::numeric(15,6)) as stddev_actual_full_precision,
    MIN(actual::numeric(15,6)) as min_actual,
    MAX(actual::numeric(15,6)) as max_actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND actual != ''
  AND actual ~ '^-?[0-9]+\.?[0-9]*$';

4. TOP ELEMENTS AMB MÉS DADES:
------------------------------
SELECT 
    element,
    COUNT(*) as record_count,
    AVG(actual::numeric(15,6)) as avg_actual,
    STDDEV(actual::numeric(15,6)) as stddev_actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL 
  AND actual != ''
  AND actual ~ '^-?[0-9]+\.?[0-9]*$'
GROUP BY element
ORDER BY record_count DESC
LIMIT 10;

NOTA SOBRE EL PROBLEMA:
=======================
El teu problema era que intentaves convertir strings buits ('') a numeric.
La solució és filtrar només els valors que són realment números vàlids
usant la expressió regular: actual ~ '^-?[0-9]+\.?[0-9]*$'

Això assegura que només processem valors numèrics vàlids.
"""
    
    queries_file = Path(__file__).parent / "working_brose_queries.sql"
    with open(queries_file, 'w', encoding='utf-8') as f:
        f.write(queries)
    
    logger.info(f"Consultes que funcionen guardades a: {queries_file}")
    
    print("\n" + "="*70)
    print("CONSULTA IMMEDIATA QUE FUNCIONARÀ:")
    print("="*70)
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("SELECT actual::numeric(15,6), nominal::numeric(15,6)")
    print("FROM mesuresqualitat") 
    print("WHERE client LIKE 'BROSE%'")
    print("  AND actual ~ '^-?[0-9]+\.?[0-9]*$'")
    print("  AND nominal ~ '^-?[0-9]+\.?[0-9]*$'")
    print("LIMIT 5;")
    print("="*70)

if __name__ == "__main__":
    analyze_brose_data()
    generate_working_queries()
