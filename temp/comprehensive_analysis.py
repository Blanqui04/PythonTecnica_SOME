#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis completo del problema de encoding y estructura de datos
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

def comprehensive_data_analysis():
    """Analisi completa dels problemes de dades i encoding"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== ANÀLISI COMPLETA DE PROBLEMES ===")
        
        with adapter.connection.cursor() as cursor:
            # Forçar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            logger.info("✅ Client encoding configurat a UTF8")
            
            # Anàlisi 1: Problemes d'encoding
            logger.info("\n--- ANÀLISI 1: Problemes d'encoding ---")
            cursor.execute("""
                SELECT 
                    element,
                    property,
                    COUNT(*) as count
                FROM mesuresqualitat 
                WHERE element LIKE '%├%' OR property LIKE '%├%'
                   OR element LIKE '%ÿ%' OR property LIKE '%ÿ%'
                GROUP BY element, property
                ORDER BY count DESC
                LIMIT 10
            """)
            
            encoding_issues = cursor.fetchall()
            if encoding_issues:
                logger.info("Elements amb problemes d'encoding:")
                for element, prop, count in encoding_issues:
                    logger.info(f"  Element: '{element}', Property: '{prop}', Count: {count}")
            else:
                logger.info("No s'han trobat problemes d'encoding obvius")
            
            # Anàlisi 2: Distribució de dades en camps numèrics
            logger.info("\n--- ANÀLISI 2: Camps numèrics ---")
            cursor.execute("""
                SELECT 
                    'actual' as field_name,
                    COUNT(*) as total,
                    COUNT(actual) as not_null,
                    COUNT(CASE WHEN actual IS NOT NULL AND actual != 0 THEN 1 END) as non_zero
                FROM mesuresqualitat
                UNION ALL
                SELECT 
                    'nominal' as field_name,
                    COUNT(*) as total,
                    COUNT(nominal) as not_null,
                    COUNT(CASE WHEN nominal IS NOT NULL AND nominal != 0 THEN 1 END) as non_zero
                FROM mesuresqualitat
            """)
            
            numeric_stats = cursor.fetchall()
            logger.info("Estadístiques camps numèrics:")
            for field, total, not_null, non_zero in numeric_stats:
                percentage_not_null = (not_null/total*100) if total > 0 else 0
                percentage_non_zero = (non_zero/total*100) if total > 0 else 0
                logger.info(f"  {field}: {not_null:,}/{total:,} not null ({percentage_not_null:.1f}%), {non_zero:,} non-zero ({percentage_non_zero:.1f}%)")
            
            # Anàlisi 3: Dades en check_value que semblen numèriques
            logger.info("\n--- ANÀLISI 3: Valors numèrics en check_value ---")
            cursor.execute("""
                SELECT 
                    check_value,
                    COUNT(*) as count,
                    client
                FROM mesuresqualitat 
                WHERE check_value ~ '^-?[0-9]+\.?[0-9]*$'
                  AND LENGTH(check_value) > 0
                GROUP BY check_value, client
                ORDER BY count DESC
                LIMIT 15
            """)
            
            numeric_in_check = cursor.fetchall()
            if numeric_in_check:
                logger.info("Valors numèrics trobats en check_value:")
                for value, count, client in numeric_in_check:
                    logger.info(f"  Valor: '{value}', Count: {count}, Client: {client}")
            
            # Anàlisi 4: Registres BROSE específics
            logger.info("\n--- ANÀLISI 4: Registres BROSE ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_brose,
                    COUNT(actual) as actual_not_null,
                    COUNT(CASE WHEN check_value ~ '^-?[0-9]+\.?[0-9]*$' THEN 1 END) as numeric_check_values,
                    COUNT(CASE WHEN LENGTH(TRIM(COALESCE(check_value, ''))) > 0 THEN 1 END) as non_empty_check
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            brose_stats = cursor.fetchone()
            total_brose, actual_nn, numeric_check, non_empty_check = brose_stats
            
            logger.info(f"Estadístiques BROSE:")
            logger.info(f"  Total registres BROSE: {total_brose:,}")
            logger.info(f"  Amb 'actual' not null: {actual_nn:,} ({actual_nn/total_brose*100:.1f}%)")
            logger.info(f"  Amb check_value numèric: {numeric_check:,} ({numeric_check/total_brose*100:.1f}%)")
            logger.info(f"  Amb check_value no buit: {non_empty_check:,} ({non_empty_check/total_brose*100:.1f}%)")
            
            # Anàlisi 5: Exemples BROSE amb dades
            logger.info("\n--- ANÀLISI 5: Exemples BROSE amb dades ---")
            cursor.execute("""
                SELECT 
                    element,
                    property,
                    check_value,
                    actual,
                    nominal,
                    data_hora::date
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND (actual IS NOT NULL OR LENGTH(TRIM(COALESCE(check_value, ''))) > 0)
                ORDER BY data_hora DESC
                LIMIT 10
            """)
            
            brose_examples = cursor.fetchall()
            if brose_examples:
                logger.info("Exemples BROSE amb dades:")
                for element, prop, check_val, actual, nominal, data in brose_examples:
                    logger.info(f"  Data: {data}")
                    logger.info(f"    Element: '{element}', Property: '{prop}'")
                    logger.info(f"    Check_value: '{check_val}', Actual: {actual}, Nominal: {nominal}")
                    logger.info("")
            
    finally:
        adapter.close()
    
    return True

def create_multi_strategy_solution():
    """Crea solucions per múltiples escenaris"""
    
    solution_content = """-- SOLUCIONS MÚLTIPLES PER PROBLEMES IDENTIFICATS
-- =================================================

-- SEMPRE EXECUTA PRIMER:
SET CLIENT_ENCODING TO 'UTF8';

-- ESTRATÈGIA 1: Si les dades estan en els camps 'actual'/'nominal'
-- ----------------------------------------------------------------
SELECT 
    client,
    element,
    property,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_hora DESC
LIMIT 10;

-- ESTRATÈGIA 2: Si les dades estan en 'check_value' (probable!)
-- -------------------------------------------------------------
SELECT 
    client,
    element,
    property,
    check_value as measured_value,
    CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' 
         THEN check_value::numeric(15,6) 
         ELSE NULL END as numeric_value,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND LENGTH(TRIM(COALESCE(check_value, ''))) > 0
  AND check_value != 'DATUMS D A B-C'
ORDER BY data_hora DESC
LIMIT 10;

-- ESTRATÈGIA 3: Combinada - buscar dades en tots els camps
-- --------------------------------------------------------
SELECT 
    client,
    element,
    property,
    COALESCE(
        CASE WHEN actual IS NOT NULL THEN actual::text END,
        CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN check_value END,
        'No numeric data'
    ) as value_found,
    CASE 
        WHEN actual IS NOT NULL THEN 'actual_field'
        WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN 'check_value_field'
        ELSE 'no_data'
    END as data_source,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
ORDER BY data_hora DESC
LIMIT 15;

-- ESTRATÈGIA 4: Estadístiques per identificar millor font de dades
-- ----------------------------------------------------------------
SELECT 
    'Data source analysis' as analysis,
    COUNT(CASE WHEN actual IS NOT NULL THEN 1 END) as actual_count,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN 1 END) as numeric_check_count,
    COUNT(CASE WHEN LENGTH(TRIM(COALESCE(check_value, ''))) > 0 
               AND check_value !~ '^-?[0-9]*\.?[0-9]+$' THEN 1 END) as text_check_count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- ESTRATÈGIA 5: Corregir problemes d'encoding en elements
-- -------------------------------------------------------
SELECT 
    client,
    element,
    REPLACE(REPLACE(element, '├│n', 'ón'), '├ÿ', '') as element_fixed,
    property,
    REPLACE(REPLACE(property, '├│n', 'ón'), '├ÿ', '') as property_fixed,
    check_value,
    actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND (element LIKE '%├%' OR property LIKE '%├%')
LIMIT 10;

-- NOTA IMPORTANT:
-- Segons l'anàlisi, sembla que les dades numèriques estan principalment
-- en el camp 'check_value' i no en 'actual'/'nominal'.
-- Prova primer l'ESTRATÈGIA 2 per veure els valors mesurats reals."""
    
    solution_file = Path(__file__).parent / "multi_strategy_brose_solution.sql"
    with open(solution_file, 'w', encoding='utf-8') as f:
        f.write(solution_content)
    
    logger.info(f"Solucions múltiples guardades a: {solution_file}")
    
    print("\n" + "🔍" + "="*78 + "🔍")
    print("🔍 PROVA AQUESTA CONSULTA PRIMER (dades probablement a check_value): 🔍")
    print("🔍" + "="*78 + "🔍")
    print()
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("SELECT ")
    print("    client,")
    print("    element,")
    print("    property,")
    print("    check_value as measured_value,")
    print("    data_hora::date")
    print("FROM mesuresqualitat ")
    print("WHERE client LIKE 'BROSE%'")
    print("  AND LENGTH(TRIM(COALESCE(check_value, ''))) > 0")
    print("  AND check_value != 'DATUMS D A B-C'")
    print("ORDER BY data_hora DESC")
    print("LIMIT 10;")
    print()
    print("🔍" + "="*78 + "🔍")

if __name__ == "__main__":
    comprehensive_data_analysis()
    create_multi_strategy_solution()
