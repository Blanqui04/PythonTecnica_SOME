#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test directo para demostrar la diferencia entre WIN1252 y UTF8 en el cliente
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

def test_encoding_differences():
    """Testa la diferència entre encodings"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== TEST D'ENCODING DEL CLIENT ===")
        
        with adapter.connection.cursor() as cursor:
            # Test 1: Sense forçar UTF8 (simulant el teu problema)
            logger.info("\n--- TEST 1: Encoding actual del client ---")
            cursor.execute("SHOW client_encoding")
            current_encoding = cursor.fetchone()[0]
            logger.info(f"Encoding actual: {current_encoding}")
            
            # Test 2: Comptar registres BROSE
            cursor.execute("SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%'")
            total_brose = cursor.fetchone()[0]
            logger.info(f"Total registres BROSE: {total_brose:,}")
            
            # Test 3: Forçar UTF8
            logger.info("\n--- TEST 2: Forçant UTF8 ---")
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            cursor.execute("SHOW client_encoding")
            new_encoding = cursor.fetchone()[0]
            logger.info(f"Nou encoding: {new_encoding}")
            
            # Test 4: Consulta amb UTF8 forçat
            logger.info("\n--- TEST 3: Consulta amb UTF8 ---")
            cursor.execute("""
                SELECT 
                    actual::numeric(15,6) as actual_precision,
                    nominal::numeric(15,6) as nominal_precision,
                    element,
                    client
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%' 
                  AND actual IS NOT NULL 
                  AND actual != ''
                  AND actual != 'NULL'
                  AND LENGTH(TRIM(actual)) > 0
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            if results:
                logger.info("Resultats amb UTF8:")
                for i, (actual, nominal, element, client) in enumerate(results, 1):
                    logger.info(f"  {i}. Actual: {actual}, Nominal: {nominal}, Element: {element}")
            else:
                logger.warning("Cap resultat trobat amb UTF8")
            
            # Test 5: Verificar dades nul·les
            logger.info("\n--- TEST 4: Anàlisi de dades nul·les ---")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN actual IS NULL THEN 1 END) as null_actual,
                    COUNT(CASE WHEN actual = '' THEN 1 END) as empty_actual,
                    COUNT(CASE WHEN actual = 'NULL' THEN 1 END) as string_null_actual,
                    COUNT(CASE WHEN LENGTH(TRIM(actual)) = 0 THEN 1 END) as whitespace_actual,
                    COUNT(CASE WHEN actual IS NOT NULL AND actual != '' AND actual != 'NULL' AND LENGTH(TRIM(actual)) > 0 THEN 1 END) as valid_actual
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
            """)
            
            stats = cursor.fetchone()
            total, null_actual, empty_actual, string_null, whitespace, valid_actual = stats
            
            logger.info(f"Estadístiques BROSE:")
            logger.info(f"  Total registres: {total:,}")
            logger.info(f"  Actual NULL: {null_actual:,}")
            logger.info(f"  Actual buit (''): {empty_actual:,}")
            logger.info(f"  Actual 'NULL' (string): {string_null:,}")
            logger.info(f"  Actual whitespace: {whitespace:,}")
            logger.info(f"  Actual vàlid: {valid_actual:,}")
            
            # Test 6: Mostrar exemples de valors actual
            logger.info("\n--- TEST 5: Exemples de valors 'actual' ---")
            cursor.execute("""
                SELECT DISTINCT 
                    actual,
                    LENGTH(actual) as length,
                    COUNT(*) as occurrences
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                GROUP BY actual, LENGTH(actual)
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            
            examples = cursor.fetchall()
            logger.info("Top 10 valors més freqüents per 'actual':")
            for actual, length, count in examples:
                display_value = repr(actual) if actual is not None else 'NULL'
                logger.info(f"  Valor: {display_value}, Longitud: {length}, Freqüència: {count:,}")
    
    finally:
        adapter.close()
    
    return True

def generate_step_by_step_solution():
    """Genera solució pas a pas"""
    
    solution = """
SOLUCIÓ PAS A PAS PER AL PROBLEMA D'ENCODING
============================================

El teu problema és que el client PostgreSQL està usant WIN1252 quan la base de dades és UTF8.

EXECUTA AQUESTS COMANDAMENTS EN AQUEST ORDRE:

1. Primer, configura l'encoding:
   SET CLIENT_ENCODING TO 'UTF8';

2. També pots usar aquesta alternativa:
   \\encoding UTF8

3. Després executa la teva consulta:
   SELECT actual::numeric(15,6), nominal::numeric(15,6) 
   FROM mesuresqualitat 
   WHERE client LIKE 'BROSE%' 
     AND actual IS NOT NULL 
     AND actual != '' 
   LIMIT 5;

COMANDAMENTS COMPLETS A COPY-PASTE:
===================================

SET CLIENT_ENCODING TO 'UTF8';
SELECT actual::numeric(15,6), nominal::numeric(15,6) FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL AND actual != '' LIMIT 5;

ALTERNATIVA COMPLETA:
====================

SET CLIENT_ENCODING TO 'UTF8';
SELECT 
    client,
    element,
    actual::numeric(15,6) as actual_full_precision,
    nominal::numeric(15,6) as nominal_full_precision
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND actual IS NOT NULL 
  AND actual != ''
  AND LENGTH(TRIM(actual)) > 0
LIMIT 10;

NOTA IMPORTANT:
===============
Si continues veient resultats buits, pot ser que els valors 'actual' siguin strings buides o NULL.
En aquest cas, executa primer l'anàlisi per veure què contenen realment els camps.
"""
    
    solution_file = Path(__file__).parent / "step_by_step_solution.txt"
    with open(solution_file, 'w', encoding='utf-8') as f:
        f.write(solution)
    
    logger.info(f"Solució pas a pas guardada a: {solution_file}")
    print("\n" + "="*60)
    print("SOLUCIÓ IMMEDIATA:")
    print("="*60)
    print("1. Executa: SET CLIENT_ENCODING TO 'UTF8';")
    print("2. Després executa la teva consulta")
    print("="*60)

if __name__ == "__main__":
    test_encoding_differences()
    generate_step_by_step_solution()
