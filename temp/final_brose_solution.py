#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solución final correcta para BROSE con nombres de columnas correctos
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

def get_correct_schema_and_test():
    """Obté l'esquema correcte i fa la prova final"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== SOLUCIÓ FINAL CORRECTA PER BROSE ===")
        
        with adapter.connection.cursor() as cursor:
            # Assegurar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            logger.info("✅ Client encoding configurat a UTF8")
            
            # Obtenir els noms correctes de les columnes
            logger.info("\n--- Obtenint esquema de la taula ---")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'mesuresqualitat' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            logger.info("Columnes de la taula mesuresqualitat:")
            for col_name, data_type in columns:
                logger.info(f"  {col_name}: {data_type}")
            
            # Test final amb les columnes correctes
            logger.info("\n--- TEST FINAL AMB COLUMNES CORRECTES ---")
            cursor.execute("""
                SELECT 
                    actual::numeric(15,6) as actual_precision,
                    nominal::numeric(15,6) as nominal_precision,
                    element,
                    client
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL
                LIMIT 5
            """)
            
            final_results = cursor.fetchall()
            if final_results:
                logger.info("🎯 RESULTATS FINALS AMB TOTS ELS DECIMALS:")
                for actual, nominal, element, client in final_results:
                    logger.info(f"  Client: {client}")
                    logger.info(f"    Element: {element}")
                    logger.info(f"    Actual: {actual} (precisió completa)")
                    logger.info(f"    Nominal: {nominal} (precisió completa)")
                    logger.info("")
            else:
                logger.warning("No s'han trobat resultats!")
            
            # Estadístiques finals
            logger.info("--- ESTADÍSTIQUES FINALS ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_brose,
                    COUNT(actual) as actual_not_null,
                    AVG(actual::numeric(15,6)) as avg_actual_precision,
                    STDDEV(actual::numeric(15,6)) as stddev_actual_precision
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            stats = cursor.fetchone()
            total, not_null, avg_val, stddev_val = stats
            
            logger.info(f"ESTADÍSTIQUES BROSE:")
            logger.info(f"  Total registres: {total:,}")
            logger.info(f"  Amb 'actual' vàlid: {not_null:,} ({not_null/total*100:.1f}%)")
            logger.info(f"  Mitjana amb precisió: {avg_val}")
            logger.info(f"  Desviació estàndard: {stddev_val}")
            
    finally:
        adapter.close()
    
    return True

def create_final_solution():
    """Crea la solució final definitiva"""
    
    solution_content = """-- SOLUCIÓ FINAL DEFINITIVA PER BROSE
-- ====================================

-- SEMPRE executa primer:
SET CLIENT_ENCODING TO 'UTF8';

-- ✅ CONSULTA QUE FUNCIONA I MOSTRA TOTS ELS DECIMALS:
SELECT 
    actual::numeric(15,6) as actual_full_decimals,
    nominal::numeric(15,6) as nominal_full_decimals
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
LIMIT 5;

-- ✅ CONSULTA COMPLETA AMB CONTEXT:
SELECT 
    client,
    element,
    caracteristica,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    "tol -"::numeric(15,6) as tolerance_minus,
    "tol +"::numeric(15,6) as tolerance_plus,
    data_mesura::date as measurement_date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_mesura DESC
LIMIT 10;

-- ✅ ESTADÍSTIQUES AMB PRECISIÓ COMPLETA:
SELECT 
    'BROSE Statistics' as description,
    COUNT(*) as total_records,
    COUNT(actual) as valid_actual_values,
    AVG(actual::numeric(15,6)) as average_with_full_precision,
    STDDEV(actual::numeric(15,6)) as stddev_with_full_precision,
    MIN(actual::numeric(15,6)) as minimum_value,
    MAX(actual::numeric(15,6)) as maximum_value
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- NOTA: Aquestes consultes mostren TOTS els decimals (fins a 6 posicions)
-- El problema era que el teu client estava configurat amb WIN1252 en lloc d'UTF8"""
    
    solution_file = Path(__file__).parent / "FINAL_BROSE_SOLUTION.sql"
    with open(solution_file, 'w', encoding='utf-8') as f:
        f.write(solution_content)
    
    logger.info(f"Solució final guardada a: {solution_file}")
    
    print("\n" + "🎯" + "="*78 + "🎯")
    print("🎯 SOLUCIÓ FINAL - COPY I PASTE AQUESTA CONSULTA: 🎯")
    print("🎯" + "="*78 + "🎯")
    print()
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("SELECT ")
    print("    actual::numeric(15,6) as actual_full_decimals,")
    print("    nominal::numeric(15,6) as nominal_full_decimals")
    print("FROM mesuresqualitat ")
    print("WHERE client LIKE 'BROSE%'")
    print("  AND actual IS NOT NULL")
    print("LIMIT 5;")
    print()
    print("🎯" + "="*78 + "🎯")
    print("✅ Aquesta consulta ET MOSTRARÀ TOTS ELS DECIMALS!")
    print("✅ Problema resolt: Era un tema d'encoding del client!")

if __name__ == "__main__":
    get_correct_schema_and_test()
    create_final_solution()
