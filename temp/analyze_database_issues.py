#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per analitzar i detectar tots els problemes a la taula mesuresqualitat

Aquest script:
1. Analitza l'estructura completa de la taula
2. Detecta problemes d'encoding en totes les columnes
3. Identifica problemes de tipus de dades
4. Troba valors problemàtics (NaN, NULL, caràcters especials)
5. Proporciona estadístiques detallades

Autor: Sistema Automàtic
Data: Juliol 2025
"""

import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseAnalyzer:
    """Analitzador complet de problemes a la taula mesuresqualitat"""
    
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
    
    def analyze_table_structure(self):
        """Analitza l'estructura completa de la taula"""
        if not self.adapter:
            return None
            
        try:
            logger.info("=== ANÀLISI DE L'ESTRUCTURA DE LA TAULA ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Obtenir informació completa de les columnes
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'mesuresqualitat'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                
                logger.info(f"Taula mesuresqualitat té {len(columns)} columnes:")
                print("\n" + "="*100)
                print(f"{'Columna':<25} {'Tipus':<20} {'Longitud':<10} {'Precisió':<10} {'Escala':<8} {'Nullable':<8} {'Default':<15}")
                print("="*100)
                
                for col in columns:
                    col_name, data_type, max_len, precision, scale, nullable, default = col
                    print(f"{col_name:<25} {data_type:<20} {str(max_len or ''):<10} {str(precision or ''):<10} {str(scale or ''):<8} {nullable:<8} {str(default or '')[:15]:<15}")
                
                return columns
                
        except Exception as e:
            logger.error(f"Error analitzant estructura: {e}")
            return None
    
    def analyze_data_quality_issues(self):
        """Analitza problemes de qualitat de dades a totes les columnes"""
        if not self.adapter:
            return None
            
        try:
            logger.info("\n=== ANÀLISI DE PROBLEMES DE QUALITAT DE DADES ===")
            
            with self.adapter.connection.cursor() as cursor:
                # 1. Problemes generals
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                total_records = cursor.fetchone()[0]
                logger.info(f"Total de registres: {total_records:,}")
                
                # 2. Analitzar cada columna de text per problemes d'encoding
                text_columns = [
                    'client', 'element', 'pieza', 'datum', 'property', 
                    'check_value', 'out_value', 'alignment', 'fase', 
                    'rivets_type', 'cavitat', 'id_referencia_client', 
                    'id_lot', 'id_referencia_some', 'id_element'
                ]
                
                print("\n" + "="*80)
                print("PROBLEMES D'ENCODING I CARÀCTERS ESPECIALS:")
                print("="*80)
                
                for col in text_columns:
                    try:
                        # Comprovar si la columna existeix
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM information_schema.columns 
                            WHERE table_name = 'mesuresqualitat' AND column_name = '{col}'
                        """)
                        
                        if cursor.fetchone()[0] == 0:
                            continue  # Columna no existeix
                        
                        # Problemes d'encoding Unicode
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM mesuresqualitat 
                            WHERE {col} ~ '[\\u0080-\\uFFFF]'
                        """)
                        unicode_issues = cursor.fetchone()[0]
                        
                        # Valors NULL/buits
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM mesuresqualitat 
                            WHERE {col} IS NULL OR {col} = ''
                        """)
                        null_empty = cursor.fetchone()[0]
                        
                        # Valors amb patrons problemàtics
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM mesuresqualitat 
                            WHERE {col} LIKE '%¿¿¿%' OR {col} LIKE '%???%' OR {col} = 'nan' OR {col} = 'NaN'
                        """)
                        problematic_patterns = cursor.fetchone()[0]
                        
                        # Mostrar només columnes amb problemes
                        if unicode_issues > 0 or problematic_patterns > 0:
                            print(f"{col:<25} Unicode: {unicode_issues:>8,} | Patterns: {problematic_patterns:>8,} | NULL/Empty: {null_empty:>8,}")
                        
                    except Exception as e:
                        logger.error(f"Error analitzant columna {col}: {e}")
                
                # 3. Analitzar columnes numèriques
                numeric_columns = [
                    'valor', 'actual', 'nominal', 'tolerancia_negativa', 
                    'tolerancia_positiva', 'desviacio'
                ]
                
                print("\n" + "="*80)
                print("PROBLEMES EN COLUMNES NUMÈRIQUES:")
                print("="*80)
                print(f"{'Columna':<25} {'NULL':<10} {'NaN/Inf':<10} {'Zero':<10} {'Negatius':<10} {'Outliers':<10}")
                print("-"*80)
                
                for col in numeric_columns:
                    try:
                        # Comprovar si la columna existeix
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM information_schema.columns 
                            WHERE table_name = 'mesuresqualitat' AND column_name = '{col}'
                        """)
                        
                        if cursor.fetchone()[0] == 0:
                            continue
                        
                        # NULL values
                        cursor.execute(f"SELECT COUNT(*) FROM mesuresqualitat WHERE {col} IS NULL")
                        null_count = cursor.fetchone()[0]
                        
                        # NaN/Infinite values (stored as text)
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM mesuresqualitat 
                            WHERE {col}::text IN ('NaN', 'Infinity', '-Infinity', 'nan', 'inf', '-inf')
                        """)
                        nan_inf_count = cursor.fetchone()[0]
                        
                        # Zero values
                        cursor.execute(f"SELECT COUNT(*) FROM mesuresqualitat WHERE {col} = 0")
                        zero_count = cursor.fetchone()[0]
                        
                        # Negative values (pot ser problemàtic per toleràncies)
                        cursor.execute(f"SELECT COUNT(*) FROM mesuresqualitat WHERE {col} < 0")
                        negative_count = cursor.fetchone()[0]
                        
                        # Outliers (valors extrems)
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM mesuresqualitat 
                            WHERE ABS({col}) > 1000000 AND {col} IS NOT NULL
                        """)
                        outliers_count = cursor.fetchone()[0]
                        
                        print(f"{col:<25} {null_count:>9,} {nan_inf_count:>9,} {zero_count:>9,} {negative_count:>9,} {outliers_count:>9,}")
                        
                    except Exception as e:
                        logger.error(f"Error analitzant columna numèrica {col}: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error analitzant qualitat de dades: {e}")
            return False
    
    def analyze_client_specific_issues(self):
        """Analitza problemes específics per client"""
        if not self.adapter:
            return None
            
        try:
            logger.info("\n=== ANÀLISI PER CLIENT ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Estadístiques per client
                cursor.execute("""
                    SELECT 
                        client,
                        COUNT(*) as total,
                        COUNT(actual) as actual_not_null,
                        COUNT(CASE WHEN actual IS NOT NULL AND actual::text NOT IN ('NaN', 'nan', 'Infinity', '-Infinity') THEN 1 END) as actual_valid,
                        COUNT(nominal) as nominal_not_null,
                        COUNT(element) as element_not_null
                    FROM mesuresqualitat 
                    WHERE client IS NOT NULL
                    GROUP BY client
                    ORDER BY total DESC
                    LIMIT 10
                """)
                
                client_stats = cursor.fetchall()
                
                print("\n" + "="*90)
                print("ESTADÍSTIQUES PER CLIENT (TOP 10):")
                print("="*90)
                print(f"{'Client':<15} {'Total':<10} {'Actual!=NULL':<12} {'Actual Vàlid':<12} {'Nominal!=NULL':<13} {'Element!=NULL':<13}")
                print("-"*90)
                
                for stat in client_stats:
                    client, total, actual_nn, actual_valid, nominal_nn, element_nn = stat
                    print(f"{client:<15} {total:>9,} {actual_nn:>11,} {actual_valid:>11,} {nominal_nn:>12,} {element_nn:>12,}")
                
                return client_stats
                
        except Exception as e:
            logger.error(f"Error analitzant per client: {e}")
            return None
    
    def detect_specific_encoding_problems(self):
        """Detecta problemes específics d'encoding"""
        if not self.adapter:
            return None
            
        try:
            logger.info("\n=== DETECCIÓ DE PROBLEMES ESPECÍFICS D'ENCODING ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Buscar caràcters problemàtics específics
                problematic_chars = [
                    ('Δ', 'Delta grec'),
                    ('α', 'Alpha grec'),
                    ('β', 'Beta grec'),
                    ('γ', 'Gamma grec'),
                    ('μ', 'Mu grec'),
                    ('π', 'Pi grec'),
                    ('σ', 'Sigma grec'),
                    ('°', 'Símbol grau'),
                    ('±', 'Més/menys'),
                    ('–', 'Guió en dash'),
                    ('—', 'Guió em dash'),
                    ('"', 'Cometes curvades'),
                    ('"', 'Cometes curvades'),
                ]
                
                print("\nCaràcters Unicode problemàtics trobats:")
                print("-" * 50)
                
                for char, desc in problematic_chars:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM mesuresqualitat 
                        WHERE element LIKE '%{char}%' OR client LIKE '%{char}%' OR property LIKE '%{char}%'
                    """)
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        print(f"{char} ({desc}): {count:,} registres")
                        
                        # Mostrar exemples
                        cursor.execute(f"""
                            SELECT DISTINCT element 
                            FROM mesuresqualitat 
                            WHERE element LIKE '%{char}%'
                            LIMIT 3
                        """)
                        examples = cursor.fetchall()
                        for example in examples:
                            print(f"    Exemple: {example[0]}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error detectant problemes d'encoding: {e}")
            return False
    
    def generate_comprehensive_fix_script(self):
        """Genera script per corregir tots els problemes detectats"""
        try:
            logger.info("\n=== GENERANT SCRIPT DE CORRECCIÓ COMPLET ===")
            
            fix_script = """
-- SCRIPT DE CORRECCIÓ COMPLET PER LA TAULA mesuresqualitat
-- Executar pas a pas per evitar problemes

-- 1. CONFIGURAR ENCODING
SET CLIENT_ENCODING TO 'UTF8';
SET DateStyle TO 'ISO, DMY';

-- 2. CORREGIR CARÀCTERS UNICODE PROBLEMÀTICS
UPDATE mesuresqualitat SET element = REPLACE(element, 'Δ', 'Delta') WHERE element LIKE '%Δ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'α', 'alpha') WHERE element LIKE '%α%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'β', 'beta') WHERE element LIKE '%β%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'γ', 'gamma') WHERE element LIKE '%γ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'μ', 'mu') WHERE element LIKE '%μ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'π', 'pi') WHERE element LIKE '%π%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'σ', 'sigma') WHERE element LIKE '%σ%';
UPDATE mesuresqualitat SET element = REPLACE(element, '°', 'deg') WHERE element LIKE '%°%';
UPDATE mesuresqualitat SET element = REPLACE(element, '±', '+/-') WHERE element LIKE '%±%';

-- 3. CORREGIR VALORS NaN I PROBLEMÀTICS
UPDATE mesuresqualitat SET actual = NULL WHERE actual::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET nominal = NULL WHERE nominal::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET tolerancia_negativa = NULL WHERE tolerancia_negativa::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET tolerancia_positiva = NULL WHERE tolerancia_positiva::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET desviacio = NULL WHERE desviacio::text IN ('NaN', 'nan', 'Infinity', '-Infinity');

-- 4. NETEJAR PATRONS PROBLEMÀTICS
UPDATE mesuresqualitat SET element = REPLACE(element, '¿¿¿???', '') WHERE element LIKE '%¿¿¿???%';
UPDATE mesuresqualitat SET element = REPLACE(element, '???', '') WHERE element LIKE '%???%';
UPDATE mesuresqualitat SET element = TRIM(element) WHERE element IS NOT NULL;

-- 5. CONSULTA VERIFICACIÓ FINAL
SELECT 
    'Registres totals' as metric,
    COUNT(*)::text as value
FROM mesuresqualitat
UNION ALL
SELECT 
    'BROSE amb actual vàlid',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' AND actual IS NOT NULL AND actual::text NOT IN ('NaN', 'nan')
UNION ALL
SELECT 
    'Elements amb Unicode',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE element ~ '[^[:ascii:]]';
"""
            
            script_path = Path(__file__).parent / "comprehensive_database_fix.sql"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(fix_script)
            
            logger.info(f"Script de correcció guardat: {script_path}")
            return script_path
            
        except Exception as e:
            logger.error(f"Error generant script: {e}")
            return None

def main():
    """Funció principal d'anàlisi"""
    logger.info("=== ANÀLISI COMPLET DE LA TAULA mesuresqualitat ===")
    
    analyzer = DatabaseAnalyzer()
    
    # Connectar
    if not analyzer.connect_to_database():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    try:
        # Analitzar estructura
        analyzer.analyze_table_structure()
        
        # Analitzar problemes de qualitat
        analyzer.analyze_data_quality_issues()
        
        # Analitzar per client
        analyzer.analyze_client_specific_issues()
        
        # Detectar problemes d'encoding específics
        analyzer.detect_specific_encoding_problems()
        
        # Generar script de correcció
        script_path = analyzer.generate_comprehensive_fix_script()
        
        logger.info("\n=== ANÀLISI COMPLETAT ===")
        logger.info("Per solucionar tots els problemes, executa:")
        logger.info(f"  psql -f {script_path}")
        logger.info("O utilitza el script comprehensive_database_fix.sql")
        
        return True
        
    finally:
        if analyzer.adapter:
            analyzer.adapter.close()

if __name__ == "__main__":
    main()
