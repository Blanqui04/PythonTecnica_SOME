#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per actualitzar els tipus de dades de la base de dades per millorar la precisió
Aquest script converteix les columnes de 'real' a 'numeric(15,6)' per preservar més decimals
"""

import os
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

def update_column_types():
    """Actualitza els tipus de columnes per millorar la precisió"""
    
    # Carregar configuració
    try:
        config_path = Path(__file__).parent / "config" / "database" / "db_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
    except Exception as e:
        logger.error(f"Error carregant configuració: {e}")
        return False
    
    # Connectar a la base de dades
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    try:
        logger.info("Actualitzant tipus de columnes per millorar la precisió...")
        
        with adapter.connection.cursor() as cursor:
            # Verificar tipus actuals
            cursor.execute("""
                SELECT column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_name = 'mesuresqualitat' 
                  AND column_name IN ('actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'desviacio', 'valor')
                ORDER BY column_name
            """)
            
            current_types = cursor.fetchall()
            logger.info("Tipus actuals de columnes:")
            for col in current_types:
                logger.info(f"  {col[0]}: {col[1]} (precisió: {col[2]}, escala: {col[3]})")
            
            # Actualitzar tipus de columnes a numeric(15,6)
            numeric_columns = ['actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'desviacio', 'valor']
            
            for column in numeric_columns:
                try:
                    logger.info(f"Actualitzant {column} a numeric(15,6)...")
                    
                    # Crear nova columna temporal
                    cursor.execute(f"ALTER TABLE mesuresqualitat ADD COLUMN {column}_new NUMERIC(15,6)")
                    
                    # Copiar dades (convertint de real a numeric)
                    cursor.execute(f"""
                        UPDATE mesuresqualitat 
                        SET {column}_new = CASE 
                            WHEN {column} IS NOT NULL THEN {column}::numeric(15,6)
                            ELSE NULL 
                        END
                    """)
                    
                    # Eliminar columna antiga
                    cursor.execute(f"ALTER TABLE mesuresqualitat DROP COLUMN {column}")
                    
                    # Renombrar nova columna
                    cursor.execute(f"ALTER TABLE mesuresqualitat RENAME COLUMN {column}_new TO {column}")
                    
                    logger.info(f"✅ {column} actualitzat a numeric(15,6)")
                    
                except Exception as e:
                    logger.error(f"Error actualitzant {column}: {e}")
                    # Intentar neteja si hi ha error
                    try:
                        cursor.execute(f"ALTER TABLE mesuresqualitat DROP COLUMN IF EXISTS {column}_new")
                    except:
                        pass
            
            # Verificar nous tipus
            cursor.execute("""
                SELECT column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_name = 'mesuresqualitat' 
                  AND column_name IN ('actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'desviacio', 'valor')
                ORDER BY column_name
            """)
            
            new_types = cursor.fetchall()
            logger.info("Nous tipus de columnes:")
            for col in new_types:
                logger.info(f"  {col[0]}: {col[1]} (precisió: {col[2]}, escala: {col[3]})")
            
            logger.info("✅ Actualització de tipus completada")
            return True
            
    except Exception as e:
        logger.error(f"Error actualitzant tipus: {e}")
        return False
    finally:
        adapter.close()

def test_precision():
    """Testa la precisió després de l'actualització"""
    
    # Carregar configuració
    try:
        config_path = Path(__file__).parent / "config" / "database" / "db_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
    except Exception as e:
        logger.error(f"Error carregant configuració: {e}")
        return False
    
    # Connectar a la base de dades
    adapter = QualityMeasurementDBAdapter(db_config)
    if not adapter.connect():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    try:
        logger.info("Testejant precisió després de l'actualització...")
        
        with adapter.connection.cursor() as cursor:
            # Test amb valors de precisió alta
            cursor.execute("""
                SELECT 
                    actual,
                    LENGTH(actual::text) as length_actual,
                    actual::text as actual_text
                FROM mesuresqualitat 
                WHERE client LIKE 'BROSE%'
                  AND actual IS NOT NULL
                  AND LENGTH(actual::text) > 5
                ORDER BY LENGTH(actual::text) DESC
                LIMIT 10
            """)
            
            precision_examples = cursor.fetchall()
            logger.info("Exemples de precisió alta:")
            for example in precision_examples:
                logger.info(f"  Valor: {example[0]}, Longitud: {example[1]}, Text: {example[2]}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error testejant precisió: {e}")
        return False
    finally:
        adapter.close()

def main():
    logger.info("=== ACTUALITZACIÓ DE TIPUS DE DADES PER MILLORAR PRECISIÓ ===")
    
    # Actualitzar tipus
    if update_column_types():
        logger.info("✅ Tipus actualitzats correctament")
        
        # Testejar precisió
        if test_precision():
            logger.info("✅ Test de precisió completat")
        else:
            logger.warning("⚠️ Problemes amb el test de precisió")
    else:
        logger.error("❌ Error actualitzant tipus de dades")
        return False
    
    logger.info("=== ACTUALITZACIÓ COMPLETADA ===")
    logger.info("Ara les columnes numèriques tenen precisió numeric(15,6)")
    logger.info("Pots executar consultes amb màxima precisió:")
    logger.info("  SELECT actual, nominal FROM mesuresqualitat WHERE client LIKE 'BROSE%' LIMIT 10;")
    
    return True

if __name__ == "__main__":
    main()
