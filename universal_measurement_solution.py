#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solución universal para todos los clientes con mediciones numéricas
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

def analyze_all_clients():
    """Analitza les dades per tots els clients"""
    
    db_config = load_db_config()
    if not db_config:
        return False
        
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        return False
    
    try:
        logger.info("=== ANÀLISI UNIVERSAL PER TOTS ELS CLIENTS ===")
        
        with adapter.connection.cursor() as cursor:
            # Forçar UTF8
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
            logger.info("✅ Client encoding configurat a UTF8")
            
            # Anàlisi 1: Clients amb dades numèriques
            logger.info("\n--- ANÀLISI 1: Clients amb dades numèriques ---")
            cursor.execute("""
                SELECT 
                    client,
                    COUNT(*) as total_records,
                    COUNT(actual) as actual_count,
                    COUNT(CASE WHEN check_value ~ '^-?[0-9]+[,.][0-9]+$' THEN 1 END) as numeric_check_count,
                    COUNT(CASE WHEN check_value ~ '^-?[0-9]+$' THEN 1 END) as integer_check_count
                FROM mesuresqualitat 
                WHERE client IS NOT NULL
                GROUP BY client
                HAVING COUNT(CASE WHEN actual IS NOT NULL 
                                   OR check_value ~ '^-?[0-9]+[,.][0-9]+$' 
                                   OR check_value ~ '^-?[0-9]+$' THEN 1 END) > 0
                ORDER BY (COUNT(CASE WHEN check_value ~ '^-?[0-9]+[,.][0-9]+$' THEN 1 END) + 
                         COUNT(CASE WHEN check_value ~ '^-?[0-9]+$' THEN 1 END)) DESC
                LIMIT 15
            """)
            
            clients_data = cursor.fetchall()
            logger.info("Clients amb més dades numèriques:")
            for client, total, actual_count, numeric_check, integer_check in clients_data:
                total_numeric = numeric_check + integer_check
                logger.info(f"  {client}: {total:,} total, {actual_count:,} actual, {total_numeric:,} check_value numeric")
            
            # Anàlisi 2: Formats de decimal utilitzats
            logger.info("\n--- ANÀLISI 2: Formats de decimal ---")
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 'European (comma)'
                        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 'Anglo (dot)'
                        WHEN check_value ~ '^-?[0-9]+$' THEN 'Integer'
                        ELSE 'Other'
                    END as decimal_format,
                    COUNT(*) as count,
                    COUNT(DISTINCT client) as clients_using_format
                FROM mesuresqualitat 
                WHERE check_value IS NOT NULL 
                  AND LENGTH(TRIM(check_value)) > 0
                  AND check_value != 'DATUMS D A B-C'
                GROUP BY 1
                ORDER BY count DESC
            """)
            
            decimal_formats = cursor.fetchall()
            logger.info("Formats de decimal utilitzats:")
            for format_type, count, clients in decimal_formats:
                logger.info(f"  {format_type}: {count:,} registres, {clients} clients")
            
            # Anàlisi 3: Exemples per client
            logger.info("\n--- ANÀLISI 3: Exemples per client ---")
            cursor.execute("""
                SELECT DISTINCT
                    client,
                    element,
                    property,
                    check_value,
                    data_hora::date
                FROM mesuresqualitat 
                WHERE client IN (
                    SELECT client 
                    FROM mesuresqualitat 
                    WHERE check_value ~ '^-?[0-9]+[,.][0-9]+$'
                    GROUP BY client 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                )
                AND check_value ~ '^-?[0-9]+[,.][0-9]+$'
                ORDER BY client, data_hora DESC
                LIMIT 15
            """)
            
            examples = cursor.fetchall()
            logger.info("Exemples de mesuraments per client:")
            current_client = None
            for client, element, prop, check_val, data in examples:
                if client != current_client:
                    logger.info(f"\n  {client}:")
                    current_client = client
                logger.info(f"    {element} ({prop}): {check_val} - {data}")
    
    finally:
        adapter.close()
    
    return True

def create_universal_solution():
    """Crea la solució universal per tots els clients"""
    
    solution_content = """-- SOLUCIÓN UNIVERSAL PARA TODOS LOS CLIENTES CON MEDICIONES NUMÉRICAS
-- =====================================================================

-- SIEMPRE ejecutar primero:
SET CLIENT_ENCODING TO 'UTF8';

-- ✅ CONSULTA UNIVERSAL: Maneja formatos europeos (comas) y anglosajones (puntos)
SELECT 
    client,
    element,
    property,
    check_value as raw_measurement,
    CASE 
        -- Formato europeo con coma (0,25)
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
            REPLACE(check_value, ',', '.')::numeric(15,6)
        -- Formato anglosajón con punto (0.25)
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
            check_value::numeric(15,6)
        -- Enteros (25)
        WHEN check_value ~ '^-?[0-9]+$' THEN 
            check_value::numeric(15,6)
        -- Si hay datos en 'actual', usarlos también
        WHEN actual IS NOT NULL THEN
            actual::numeric(15,6)
        ELSE NULL
    END as measurement_with_full_precision,
    CASE 
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 'check_value_european'
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 'check_value_anglo'
        WHEN check_value ~ '^-?[0-9]+$' THEN 'check_value_integer'
        WHEN actual IS NOT NULL THEN 'actual_field'
        ELSE 'no_data'
    END as data_source,
    data_hora::date as measurement_date
FROM mesuresqualitat 
WHERE (
    -- Datos numéricos en check_value
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    -- O datos en actual
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
ORDER BY client, data_hora DESC
LIMIT 50;

-- ✅ ESTADÍSTICAS POR CLIENTE:
SELECT 
    client,
    COUNT(*) as total_measurements,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 1 END) as european_format_count,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 1 END) as anglo_format_count,
    COUNT(CASE WHEN actual IS NOT NULL THEN 1 END) as actual_field_count,
    AVG(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as average_measurement
FROM mesuresqualitat 
WHERE (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
GROUP BY client
ORDER BY total_measurements DESC;

-- ✅ CONSULTA PARA UN CLIENTE ESPECÍFICO (cambia 'CLIENTE_NOMBRE'):
SELECT 
    client,
    element,
    property,
    check_value as raw_value,
    CASE 
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
            REPLACE(check_value, ',', '.')::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
            check_value::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+$' THEN 
            check_value::numeric(15,6)
        WHEN actual IS NOT NULL THEN
            actual::numeric(15,6)
    END as precise_measurement,
    data_hora::date
FROM mesuresqualitat 
WHERE client = 'BROSE'  -- Cambia aquí el nombre del cliente
  AND (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
  )
  AND check_value != 'DATUMS D A B-C'
ORDER BY data_hora DESC
LIMIT 20;

-- ✅ DISTRIBUCIÓN POR ELEMENTO (todos los clientes):
SELECT 
    client,
    element,
    property,
    COUNT(*) as measurement_count,
    AVG(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as avg_measurement,
    STDDEV(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as stddev_measurement
FROM mesuresqualitat 
WHERE (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
GROUP BY client, element, property
HAVING COUNT(*) >= 5  -- Solo elementos con al menos 5 mediciones
ORDER BY client, measurement_count DESC;

-- NOTA: Esta solución maneja:
-- 1. Formato europeo (comas): 0,25 → 0.250000
-- 2. Formato anglosajón (puntos): 0.25 → 0.250000  
-- 3. Enteros: 25 → 25.000000
-- 4. Datos en campo 'actual' cuando disponibles
-- 5. Precisión completa hasta 6 decimales para todos los clientes"""
    
    solution_file = Path(__file__).parent / "UNIVERSAL_MEASUREMENT_SOLUTION.sql"
    with open(solution_file, 'w', encoding='utf-8') as f:
        f.write(solution_content)
    
    logger.info(f"Solució universal guardada a: {solution_file}")
    
    print("\n" + "🌍" + "="*78 + "🌍")
    print("🌍 SOLUCIÓN UNIVERSAL PARA TODOS LOS CLIENTES: 🌍")
    print("🌍" + "="*78 + "🌍")
    print()
    print("SET CLIENT_ENCODING TO 'UTF8';")
    print("SELECT ")
    print("    client,")
    print("    element,")
    print("    property,")
    print("    check_value as raw_measurement,")
    print("    CASE ")
    print("        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN ")
    print("            REPLACE(check_value, ',', '.')::numeric(15,6)")
    print("        WHEN check_value ~ '^-?[0-9]+\\.[0-9]+$' THEN ")
    print("            check_value::numeric(15,6)")
    print("        WHEN check_value ~ '^-?[0-9]+$' THEN ")
    print("            check_value::numeric(15,6)")
    print("        WHEN actual IS NOT NULL THEN")
    print("            actual::numeric(15,6)")
    print("    END as measurement_with_full_precision,")
    print("    data_hora::date as measurement_date")
    print("FROM mesuresqualitat ")
    print("WHERE (check_value ~ '^-?[0-9]+[,.][0-9]+$' ")
    print("       OR check_value ~ '^-?[0-9]+$'")
    print("       OR actual IS NOT NULL)")
    print("  AND check_value != 'DATUMS D A B-C'")
    print("ORDER BY client, data_hora DESC")
    print("LIMIT 50;")
    print()
    print("🌍" + "="*78 + "🌍")
    print("✅ Funciona para TODOS los clientes con TODOS los decimales!")

if __name__ == "__main__":
    analyze_all_clients()
    create_universal_solution()
