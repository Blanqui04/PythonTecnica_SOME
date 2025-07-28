#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per solucionar problemes d'encoding i precisió a la base de dades

Aquest script:
1. Actualitza l'esquema de la taula per suportar millor Unicode i precisió decimal
2. Proporciona funcions per netejar dades existents
3. Ofereix consultes SQL segures per evitar problemes d'encoding

Autor: Sistema Automàtic
Data: Juliol 2025
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
from src.services.value_cleaner import ValueCleaner
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseEncodingFixer:
    """Classe per solucionar problemes d'encoding a la base de dades"""
    
    def __init__(self):
        self.adapter = None
        
    def load_db_config(self):
        """Carrega la configuració de la base de dades"""
        try:
            config_path = Path(__file__).parent / "config" / "database" / "db_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error carregant configuració BBDD: {e}")
            return None
    
    def connect_to_database(self):
        """Connecta a la base de dades"""
        db_config = self.load_db_config()
        if not db_config:
            return False
            
        self.adapter = QualityMeasurementDBAdapter(db_config)
        return self.adapter.connect()
    
    def backup_existing_data(self):
        """Fa backup de les dades existents abans de les modificacions"""
        if not self.adapter:
            logger.error("No hi ha connexió a la base de dades")
            return False
            
        try:
            logger.info("Creant backup de dades existents...")
            backup_path = Path(__file__).parent / "data" / "backup"
            backup_path.mkdir(exist_ok=True, parents=True)
            
            backup_file = backup_path / f"mesuresqualitat_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with self.adapter.connection.cursor() as cursor:
                # Usar copy_to en lloc de COPY TO STDOUT
                with open(backup_file, 'w', encoding='utf-8', newline='') as f:
                    cursor.copy_to(
                        f, 
                        'mesuresqualitat', 
                        sep=',',
                        columns=('client', 'element', 'actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'data_hora', 'id_lot')
                    )
                
                logger.info(f"Backup creat: {backup_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error creant backup: {e}")
            # Intentar backup alternatiu amb SELECT
            try:
                logger.info("Intentant backup alternatiu...")
                with self.adapter.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT client, element, actual, nominal, tolerancia_negativa, tolerancia_positiva, data_hora, id_lot
                        FROM mesuresqualitat 
                        WHERE client LIKE 'BROSE%'
                        LIMIT 1000
                    """)
                    
                    rows = cursor.fetchall()
                    backup_file_alt = backup_path / f"mesuresqualitat_sample_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    
                    import csv
                    with open(backup_file_alt, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['client', 'element', 'actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'data_hora', 'id_lot'])
                        writer.writerows(rows)
                    
                    logger.info(f"Backup alternatiu creat (mostra): {backup_file_alt}")
                    return True
                    
            except Exception as e2:
                logger.warning(f"No s'ha pogut crear backup: {e2}")
                return False
    
    def update_database_schema(self):
        """Actualitza l'esquema de la base de dades"""
        if not self.adapter:
            logger.error("No hi ha connexió a la base de dades")
            return False
            
        try:
            logger.info("Actualitzant esquema de la base de dades...")
            result = self.adapter.update_table_schema()
            
            if result['success']:
                logger.info("Esquema actualitzat correctament")
                return True
            else:
                logger.error(f"Error actualitzant esquema: {result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Error actualitzant esquema: {e}")
            return False
    
    def clean_existing_unicode_data(self):
        """Neteja dades Unicode problemàtiques existents"""
        if not self.adapter:
            logger.error("No hi ha connexió a la base de dades")
            return False
            
        try:
            logger.info("Netejant dades Unicode problemàtiques...")
            
            with self.adapter.connection.cursor() as cursor:
                # Obtenir registres amb caràcters problemàtics
                cursor.execute("""
                    SELECT id_referencia_some, id_element, element, client
                    FROM mesuresqualitat 
                    WHERE element ~ '[\\u0080-\\uFFFF]' 
                       OR client ~ '[\\u0080-\\uFFFF]'
                    LIMIT 1000
                """)
                
                problematic_records = cursor.fetchall()
                logger.info(f"Trobats {len(problematic_records)} registres amb caràcters Unicode problemàtics")
                
                # Netejar cada registre
                cleaned_count = 0
                for record in problematic_records:
                    id_ref, id_elem, element, client = record
                    
                    # Netejar valors
                    clean_element = ValueCleaner.normalize_unicode_text(element or "")
                    clean_client = ValueCleaner.normalize_unicode_text(client or "")
                    
                    # Actualitzar registre
                    cursor.execute("""
                        UPDATE mesuresqualitat 
                        SET element = %s, client = %s
                        WHERE id_referencia_some = %s AND id_element = %s
                    """, (clean_element, clean_client, id_ref, id_elem))
                    
                    cleaned_count += 1
                
                logger.info(f"Netejats {cleaned_count} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error netejant dades Unicode: {e}")
            return False
    
    def fix_nan_values(self):
        """Corregeix valors NaN a les columnes numèriques"""
        if not self.adapter:
            logger.error("No hi ha connexió a la base de dades")
            return False
            
        try:
            logger.info("Corregint valors NaN a columnes numèriques...")
            
            with self.adapter.connection.cursor() as cursor:
                # Comptar registres amb valors NaN o NULL problemàtics
                cursor.execute("""
                    SELECT COUNT(*) FROM mesuresqualitat 
                    WHERE (actual IS NULL OR actual = 'NaN' OR actual = 'nan')
                       OR (nominal IS NULL OR nominal = 'NaN' OR nominal = 'nan')
                       OR (tolerancia_negativa IS NULL OR tolerancia_negativa = 'NaN')
                       OR (tolerancia_positiva IS NULL OR tolerancia_positiva = 'NaN')
                """)
                
                nan_count = cursor.fetchone()[0]
                logger.info(f"Trobats {nan_count} registres amb valors NaN/NULL problemàtics")
                
                if nan_count > 0:
                    # Actualitzar valors NaN a NULL explícit per columnes numèriques
                    numeric_updates = [
                        "UPDATE mesuresqualitat SET actual = NULL WHERE actual = 'NaN' OR actual = 'nan'",
                        "UPDATE mesuresqualitat SET nominal = NULL WHERE nominal = 'NaN' OR nominal = 'nan'", 
                        "UPDATE mesuresqualitat SET tolerancia_negativa = NULL WHERE tolerancia_negativa = 'NaN'",
                        "UPDATE mesuresqualitat SET tolerancia_positiva = NULL WHERE tolerancia_positiva = 'NaN'",
                        "UPDATE mesuresqualitat SET desviacio = NULL WHERE desviacio = 'NaN'"
                    ]
                    
                    total_fixed = 0
                    for update_sql in numeric_updates:
                        cursor.execute(update_sql)
                        total_fixed += cursor.rowcount
                        
                    logger.info(f"Corregits {total_fixed} valors NaN")
                    
                    # Verificar tipus de dades de les columnes
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'mesuresqualitat' 
                          AND column_name IN ('actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva')
                        ORDER BY column_name
                    """)
                    
                    column_types = cursor.fetchall()
                    logger.info("Tipus de dades actuals:")
                    for col_name, data_type in column_types:
                        logger.info(f"  {col_name}: {data_type}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error corregint valors NaN: {e}")
            return False
    
    def test_unicode_queries(self):
        """Testa consultes amb caràcters Unicode"""
        if not self.adapter:
            logger.error("No hi ha connexió a la base de dades")
            return False
            
        try:
            logger.info("Testejant consultes Unicode...")
            
            with self.adapter.connection.cursor() as cursor:
                # Test 1: Consulta bàsica BROSE
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%'")
                brose_count = cursor.fetchone()[0]
                logger.info(f"Registres BROSE trobats: {brose_count}")
                
                # Test 2: Consulta amb caràcters normalitzats
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat WHERE element LIKE '%Delta%'")
                delta_count = cursor.fetchone()[0]
                logger.info(f"Registres amb 'Delta' normalitzat: {delta_count}")
                
                # Test 3: Comptar registres amb valors vàlids vs NaN/NULL
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(actual) as actual_not_null,
                        COUNT(CASE WHEN actual IS NOT NULL AND actual != 'NaN' THEN 1 END) as actual_valid
                    FROM mesuresqualitat 
                    WHERE client LIKE 'BROSE%'
                """)
                
                counts = cursor.fetchone()
                logger.info(f"BROSE - Total: {counts[0]}, Actual no NULL: {counts[1]}, Actual vàlid: {counts[2]}")
                
                # Test 4: Mostra exemples amb valors vàlids
                cursor.execute("""
                    SELECT client, element, actual, nominal, tolerancia_negativa, tolerancia_positiva
                    FROM mesuresqualitat 
                    WHERE client LIKE 'BROSE%' 
                      AND actual IS NOT NULL 
                      AND actual != 'NaN'
                      AND nominal IS NOT NULL
                    LIMIT 5
                """)
                
                examples = cursor.fetchall()
                if examples:
                    logger.info("Exemples de dades VÀLIDES:")
                    for example in examples:
                        logger.info(f"  Client: {example[0]}, Element: {example[1]}, Actual: {example[2]}, Nominal: {example[3]}")
                else:
                    logger.warning("No s'han trobat registres BROSE amb valors vàlids")
                
                # Test 5: Verificar tipus de dades
                cursor.execute("""
                    SELECT column_name, data_type, numeric_precision, numeric_scale
                    FROM information_schema.columns 
                    WHERE table_name = 'mesuresqualitat' 
                      AND column_name IN ('actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva')
                    ORDER BY column_name
                """)
                
                schema_info = cursor.fetchall()
                logger.info("Informació de l'esquema:")
                for col_info in schema_info:
                    logger.info(f"  {col_info[0]}: {col_info[1]} (precisió: {col_info[2]}, escala: {col_info[3]})")
                
                return True
                
        except Exception as e:
            logger.error(f"Error testejant consultes: {e}")
            return False
    
    def generate_safe_queries(self):
        """Genera consultes SQL segures per evitar problemes d'encoding"""
        queries = {
            "consulta_brose_segura": """
                -- Consulta segura per dades BROSE
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT 
                    client,
                    element,
                    ROUND(actual::numeric, 6) as actual_precis,
                    ROUND(nominal::numeric, 6) as nominal_precis,
                    ROUND(tolerancia_negativa::numeric, 6) as tol_neg,
                    ROUND(tolerancia_positiva::numeric, 6) as tol_pos,
                    data_hora
                FROM mesuresqualitat 
                WHERE client ILIKE 'brose%'
                ORDER BY data_hora DESC
                LIMIT 100;
            """,
            
            "estadistiques_precisio": """
                -- Estadístiques de precisió per client
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT 
                    client,
                    COUNT(*) as total_mesures,
                    ROUND(AVG(actual::numeric), 6) as actual_mitjana,
                    ROUND(STDDEV(actual::numeric), 6) as actual_desviacio,
                    ROUND(MIN(actual::numeric), 6) as actual_min,
                    ROUND(MAX(actual::numeric), 6) as actual_max
                FROM mesuresqualitat 
                WHERE client IS NOT NULL AND actual IS NOT NULL
                GROUP BY client
                ORDER BY total_mesures DESC;
            """,
            
            "elements_amb_unicode": """
                -- Buscar elements que encara poden tenir caràcters especials
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT DISTINCT element, COUNT(*)
                FROM mesuresqualitat 
                WHERE element ~ '[^[:ascii:]]'
                GROUP BY element
                ORDER BY count DESC;
            """
        }
        
        # Guardar consultes a fitxer
        queries_file = Path(__file__).parent / "safe_queries.sql"
        with open(queries_file, 'w', encoding='utf-8') as f:
            f.write("-- Consultes SQL segures per evitar problemes d'encoding\n")
            f.write("-- Generat automàticament per fix_database_encoding.py\n\n")
            
            for name, query in queries.items():
                f.write(f"-- {name.upper()}\n")
                f.write(query)
                f.write("\n\n")
        
        logger.info(f"Consultes segures guardades a: {queries_file}")
        return queries_file


def main():
    """Funció principal per executar la correcció"""
    logger.info("=== INICIANT CORRECCIÓ D'ENCODING I PRECISIÓ ===")
    
    fixer = DatabaseEncodingFixer()
    
    # Pas 1: Connectar a la base de dades
    if not fixer.connect_to_database():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    logger.info("✅ Connexió establerta")
    
    # Pas 2: Crear backup
    if not fixer.backup_existing_data():
        logger.warning("⚠️ No s'ha pogut crear backup, continuant...")
    
    # Pas 3: Actualitzar esquema
    if fixer.update_database_schema():
        logger.info("✅ Esquema actualitzat")
    else:
        logger.error("❌ Error actualitzant esquema")
        return False
    
    # Pas 4: Netejar dades Unicode
    if fixer.clean_existing_unicode_data():
        logger.info("✅ Dades Unicode netejades")
    else:
        logger.warning("⚠️ Problemes netejant dades Unicode")
    
    # Pas 5: Corregir valors NaN
    if fixer.fix_nan_values():
        logger.info("✅ Valors NaN corregits")
    else:
        logger.warning("⚠️ Problemes corregint valors NaN")
    
    # Pas 6: Testejar consultes
    if fixer.test_unicode_queries():
        logger.info("✅ Consultes Unicode testejades")
    else:
        logger.warning("⚠️ Problemes amb consultes Unicode")
    
    # Pas 7: Generar consultes segures
    queries_file = fixer.generate_safe_queries()
    logger.info(f"✅ Consultes segures generades: {queries_file}")
    
    logger.info("=== CORRECCIÓ COMPLETADA ===")
    logger.info("Ara pots executar consultes com:")
    logger.info("  SET CLIENT_ENCODING TO 'UTF8';")
    logger.info("  SELECT * FROM mesuresqualitat WHERE client LIKE 'BROSE%';")
    
    return True


if __name__ == "__main__":
    main()
