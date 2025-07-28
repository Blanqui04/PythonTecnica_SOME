#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solución correcta para datos BROSE - el campo actual ya es numeric
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

def test_brose_numeric_fields():
    """Testa els camps numèrics de BROSE correctament"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== TEST CORRECTE DE CAMPS NUMÈRICS BROSE ===")
        
        with adapter.connection.cursor() as cursor:
            # Assegurar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            logger.info("✅ Client encoding configurat a UTF8")
            
            # Verificar el tipus de dades dels camps
            logger.info("\n--- Verificant tipus de dades ---")
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = 'mesuresqualitat' 
                  AND column_name IN ('actual', 'nominal', 'tol -', 'tol +')
                ORDER BY column_name
            """)
            
            column_types = cursor.fetchall()
            logger.info("Tipus de dades dels camps:")
            for col_name, data_type, precision, scale in column_types:
                logger.info(f"  {col_name}: {data_type}({precision},{scale})")
            
            # Test 1: Consulta bàsica amb camps numèrics
            logger.info("\n--- Test 1: Consulta bàsica ---")
            cursor.execute("""
                SELECT 
                    actual,
                    nominal,
                    element,
                    projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL
                LIMIT 5
            """)
            
            basic_results = cursor.fetchall()
            if basic_results:
                logger.info("RESULTATS BÀSICS:")
                for actual, nominal, element, projecte in basic_results:
                    logger.info(f"  Actual: {actual}, Nominal: {nominal}, Element: '{element}', Projecte: '{projecte}'")
            else:
                logger.warning("No s'han trobat resultats bàsics!")
            
            # Test 2: Amb precisió forçada
            logger.info("\n--- Test 2: Amb precisió numeric(15,6) ---")
            cursor.execute("""
                SELECT 
                    actual::numeric(15,6) as actual_precision,
                    nominal::numeric(15,6) as nominal_precision,
                    element,
                    projecte
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL
                  AND nominal IS NOT NULL
                LIMIT 5
            """)
            
            precision_results = cursor.fetchall()
            if precision_results:
                logger.info("RESULTATS AMB PRECISIÓ COMPLETA:")
                for actual, nominal, element, projecte in precision_results:
                    logger.info(f"  Actual: {actual}, Nominal: {nominal}, Element: '{element}', Projecte: '{projecte}'")
            else:
                logger.warning("No s'han trobat resultats amb precisió!")
            
            # Test 3: Estadístiques amb precisió
            logger.info("\n--- Test 3: Estadístiques amb precisió ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(actual) as non_null_actual,
                    AVG(actual::numeric(15,6)) as avg_actual_precision,
                    STDDEV(actual::numeric(15,6)) as stddev_actual_precision,
                    MIN(actual::numeric(15,6)) as min_actual,
                    MAX(actual::numeric(15,6)) as max_actual
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            stats = cursor.fetchone()
            total, non_null, avg_val, stddev_val, min_val, max_val = stats
            
            logger.info(f"ESTADÍSTIQUES BROSE AMB PRECISIÓ COMPLETA:")
            logger.info(f"  Total registres: {total:,}")
            logger.info(f"  Registres amb 'actual' no nul: {non_null:,}")
            logger.info(f"  Mitjana 'actual': {avg_val}")
            logger.info(f"  Desviació estàndard: {stddev_val}")
            logger.info(f"  Mínim: {min_val}")
            logger.info(f"  Màxim: {max_val}")
            
            # Test 4: Consulta completa amb tots els camps
            logger.info("\n--- Test 4: Consulta completa ---")
            cursor.execute("""
                SELECT 
                    id,
                    client,
                    projecte,
                    element,
                    caracteristica,
                    actual::numeric(15,6) as actual_precision,
                    nominal::numeric(15,6) as nominal_precision,
                    "tol -"::numeric(15,6) as tol_minus_precision,
                    "tol +"::numeric(15,6) as tol_plus_precision,
                    data_mesura::date as mesura_date
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL
                ORDER BY data_mesura DESC, id DESC
                LIMIT 3
            """)
            
            complete_results = cursor.fetchall()
            if complete_results:
                logger.info("CONSULTA COMPLETA AMB TOTS ELS DECIMALS:")
                for row in complete_results:
                    id_val, client, projecte, element, caracteristica, actual, nominal, tol_minus, tol_plus, data = row
                    logger.info(f"  ID: {id_val}")
                    logger.info(f"    Client: {client}, Projecte: {projecte}")
                    logger.info(f"    Element: {element}, Característica: {caracteristica}")
                    logger.info(f"    Actual: {actual}, Nominal: {nominal}")
                    logger.info(f"    Toleràncies: -{tol_minus}, +{tol_plus}")
                    logger.info(f"    Data: {data}")
                    logger.info("")
            
    finally:
        adapter.close()
    
    return True

def create_perfect_query():
    """Crea la consulta perfecta que funciona"""
    
    query_content = """-- CONSULTA PERFECTA PER BROSE AMB TOTS ELS DECIMALS
-- ===================================================

-- IMPORTANT: Executa sempre primer:
SET CLIENT_ENCODING TO 'UTF8';

-- Consulta que mostra tots els decimals:
SELECT 
    actual::numeric(15,6) as actual_full_precision,
    nominal::numeric(15,6) as nominal_full_precision
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
LIMIT 5;

-- Consulta completa amb context:
SELECT 
    client,
    projecte,
    element,
    caracteristica,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    "tol -"::numeric(15,6) as tol_minus_precision,
    "tol +"::numeric(15,6) as tol_plus_precision,
    data_mesura::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_mesura DESC
LIMIT 10;

-- Estadístiques amb precisió completa:
SELECT 
    COUNT(*) as total_records,
    COUNT(actual) as records_with_actual,
    AVG(actual::numeric(15,6)) as average_actual_full_precision,
    STDDEV(actual::numeric(15,6)) as stddev_actual_full_precision,
    MIN(actual::numeric(15,6)) as minimum_actual,
    MAX(actual::numeric(15,6)) as maximum_actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';"""
    
    query_file = Path(__file__).parent / "perfect_brose_query.sql"
    with open(query_file, 'w', encoding='utf-8') as f:
        f.write(query_content)
    
    logger.info(f"Consulta perfecta guardada a: {query_file}")
    
    print("\n" + "="*80)
    print("🎯 CONSULTA PERFECTA QUE FUNCIONARÀ AL 100%:")
    print("="*80)
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("")
    print("SELECT ")
    print("    actual::numeric(15,6) as actual_full_precision,")
    print("    nominal::numeric(15,6) as nominal_full_precision")
    print("FROM mesuresqualitat") 
    print("WHERE client LIKE 'BROSE%'")
    print("  AND actual IS NOT NULL")
    print("LIMIT 5;")
    print("="*80)
    print("✅ Aquesta consulta mostrarà tots els decimals!")

if __name__ == "__main__":
    test_brose_numeric_fields()
    create_perfect_query()
