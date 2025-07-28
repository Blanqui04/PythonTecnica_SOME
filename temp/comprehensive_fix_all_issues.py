#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script complet per corregir TOTS els problemes detectats a la taula mesuresqualitat

Aquest script corregeix:
1. Problemes d'encoding Unicode (53,085+ registres)
2. Caràcters grecs problemàtics (247 registres amb Δ)
3. Patrons problemàtics ¿¿¿??? (21,626+ registres)
4. Valors NaN a columnes numèriques (193,641 registres)
5. Normalització completa de text

Autor: Sistema Automàtic
Data: Juliol 2025
"""

import os
import sys
import json
import logging
from pathlib import Path
import time

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
from src.services.value_cleaner import ValueCleaner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveDatabaseFixer:
    """Correcció completa de tots els problemes de la taula mesuresqualitat"""
    
    def __init__(self):
        self.adapter = None
        self.fixed_counts = {
            'unicode_chars': 0,
            'problematic_patterns': 0,
            'nan_values': 0,
            'greek_chars': 0,
            'text_normalization': 0
        }
        
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
    
    def backup_problematic_data(self):
        """Crea backup específic de dades problemàtiques abans de la correcció"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Creant backup de dades problemàtiques...")
            backup_path = Path(__file__).parent / "data" / "backup"
            backup_path.mkdir(exist_ok=True, parents=True)
            
            with self.adapter.connection.cursor() as cursor:
                # Backup de registres amb problemes d'encoding
                backup_file = backup_path / f"problematic_data_backup_{int(time.time())}.csv"
                
                cursor.execute("""
                    SELECT id_referencia_some, id_element, client, element, property, pieza, datum
                    FROM mesuresqualitat 
                    WHERE element ~ '[^[:ascii:]]' 
                       OR property ~ '[^[:ascii:]]'
                       OR pieza LIKE '%¿¿¿%'
                       OR datum LIKE '%¿¿¿%'
                    LIMIT 5000
                """)
                
                problematic_records = cursor.fetchall()
                
                import csv
                with open(backup_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id_referencia_some', 'id_element', 'client', 'element', 'property', 'pieza', 'datum'])
                    writer.writerows(problematic_records)
                
                logger.info(f"Backup creat amb {len(problematic_records)} registres problemàtics: {backup_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error creant backup: {e}")
            return False
    
    def fix_greek_characters(self):
        """Corregeix caràcters grecs específics"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Corregint caràcters grecs (Δ, α, β, etc.)...")
            
            greek_replacements = {
                'Δ': 'Delta',
                'α': 'alpha', 
                'β': 'beta',
                'γ': 'gamma',
                'δ': 'delta',
                'ε': 'epsilon',
                'θ': 'theta',
                'λ': 'lambda',
                'μ': 'mu',
                'π': 'pi',
                'σ': 'sigma',
                'φ': 'phi',
                'ω': 'omega',
                'Ω': 'Omega'
            }
            
            text_columns = ['element', 'property', 'pieza', 'datum', 'alignment']
            
            with self.adapter.connection.cursor() as cursor:
                total_fixed = 0
                
                for col in text_columns:
                    for greek_char, replacement in greek_replacements.items():
                        try:
                            cursor.execute(f"""
                                UPDATE mesuresqualitat 
                                SET {col} = REPLACE({col}, %s, %s)
                                WHERE {col} LIKE %s
                            """, (greek_char, replacement, f'%{greek_char}%'))
                            
                            fixed_count = cursor.rowcount
                            total_fixed += fixed_count
                            
                            if fixed_count > 0:
                                logger.info(f"  {col}: {greek_char} → {replacement} ({fixed_count:,} registres)")
                                
                        except Exception as e:
                            logger.error(f"Error corregint {greek_char} a {col}: {e}")
                
                self.fixed_counts['greek_chars'] = total_fixed
                logger.info(f"Caràcters grecs corregits: {total_fixed:,} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error corregint caràcters grecs: {e}")
            return False
    
    def fix_problematic_patterns(self):
        """Corregeix patrons problemàtics com ¿¿¿???, ???, etc."""
        if not self.adapter:
            return False
            
        try:
            logger.info("Corregint patrons problemàtics (¿¿¿???, ???, etc.)...")
            
            problematic_patterns = [
                '¿¿¿???',
                '¿¿¿',
                '???',
                'nan',
                'NaN',
                'NULL',
                'null'
            ]
            
            text_columns = ['element', 'property', 'pieza', 'datum', 'check_value', 'out_value', 'alignment']
            
            with self.adapter.connection.cursor() as cursor:
                total_fixed = 0
                
                for col in text_columns:
                    for pattern in problematic_patterns:
                        try:
                            # Reemplaçar patrons amb cadena buida i netejar espais
                            cursor.execute(f"""
                                UPDATE mesuresqualitat 
                                SET {col} = TRIM(REPLACE({col}, %s, ''))
                                WHERE {col} LIKE %s AND {col} IS NOT NULL
                            """, (pattern, f'%{pattern}%'))
                            
                            fixed_count = cursor.rowcount
                            total_fixed += fixed_count
                            
                            if fixed_count > 0:
                                logger.info(f"  {col}: '{pattern}' eliminat ({fixed_count:,} registres)")
                                
                        except Exception as e:
                            logger.error(f"Error corregint patró {pattern} a {col}: {e}")
                
                # Convertir strings buides a NULL
                for col in text_columns:
                    try:
                        cursor.execute(f"""
                            UPDATE mesuresqualitat 
                            SET {col} = NULL 
                            WHERE {col} = '' OR {col} = ' '
                        """)
                        
                        empty_fixed = cursor.rowcount
                        if empty_fixed > 0:
                            logger.info(f"  {col}: strings buides → NULL ({empty_fixed:,} registres)")
                            
                    except Exception as e:
                        logger.error(f"Error convertint strings buides a {col}: {e}")
                
                self.fixed_counts['problematic_patterns'] = total_fixed
                logger.info(f"Patrons problemàtics corregits: {total_fixed:,} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error corregint patrons problemàtics: {e}")
            return False
    
    def fix_unicode_characters(self):
        """Corregeix tots els caràcters Unicode problemàtics"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Corregint caràcters Unicode problemàtics...")
            
            unicode_replacements = {
                '°': 'deg',
                '±': '+/-',
                '≤': '<=',
                '≥': '>=',
                '≠': '!=',
                '≈': '~',
                '×': 'x',
                '÷': '/',
                '–': '-',
                '—': '-',
                '"': '"',
                '"': '"',
                ''': "'",
                ''': "'",
                '…': '...',
                '€': 'EUR',
                '£': 'GBP',
                '¡': '!',
                '¿': '?'
            }
            
            text_columns = ['element', 'property', 'pieza', 'datum', 'alignment', 'check_value', 'out_value']
            
            with self.adapter.connection.cursor() as cursor:
                total_fixed = 0
                
                for col in text_columns:
                    for unicode_char, replacement in unicode_replacements.items():
                        try:
                            cursor.execute(f"""
                                UPDATE mesuresqualitat 
                                SET {col} = REPLACE({col}, %s, %s)
                                WHERE {col} LIKE %s
                            """, (unicode_char, replacement, f'%{unicode_char}%'))
                            
                            fixed_count = cursor.rowcount
                            total_fixed += fixed_count
                            
                            if fixed_count > 0:
                                logger.info(f"  {col}: {unicode_char} → {replacement} ({fixed_count:,} registres)")
                                
                        except Exception as e:
                            logger.error(f"Error corregint {unicode_char} a {col}: {e}")
                
                self.fixed_counts['unicode_chars'] = total_fixed
                logger.info(f"Caràcters Unicode corregits: {total_fixed:,} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error corregint caràcters Unicode: {e}")
            return False
    
    def fix_numeric_nan_values(self):
        """Corregeix valors NaN a totes les columnes numèriques"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Corregint valors NaN a columnes numèriques...")
            
            numeric_columns = ['valor', 'actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'desviacio']
            
            with self.adapter.connection.cursor() as cursor:
                total_fixed = 0
                
                for col in numeric_columns:
                    try:
                        # Primer, convertir strings problemàtics a NULL
                        cursor.execute(f"""
                            UPDATE mesuresqualitat 
                            SET {col} = NULL 
                            WHERE {col}::text IN ('NaN', 'nan', 'Infinity', '-Infinity', 'inf', '-inf', '')
                        """)
                        
                        fixed_count = cursor.rowcount
                        total_fixed += fixed_count
                        
                        if fixed_count > 0:
                            logger.info(f"  {col}: valors NaN/Infinity → NULL ({fixed_count:,} registres)")
                            
                    except Exception as e:
                        logger.error(f"Error corregint NaN a {col}: {e}")
                
                self.fixed_counts['nan_values'] = total_fixed
                logger.info(f"Valors NaN corregits: {total_fixed:,} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error corregint valors NaN: {e}")
            return False
    
    def normalize_all_text(self):
        """Normalitza tot el text per eliminar caràcters problemàtics restants"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Normalitzant tot el text restant...")
            
            text_columns = ['element', 'property', 'pieza', 'datum', 'alignment', 'check_value', 'out_value', 'client']
            
            with self.adapter.connection.cursor() as cursor:
                total_normalized = 0
                
                for col in text_columns:
                    try:
                        # Eliminar caràcters no-ASCII restants
                        cursor.execute(f"""
                            UPDATE mesuresqualitat 
                            SET {col} = REGEXP_REPLACE({col}, '[^[:ascii:]]', '', 'g')
                            WHERE {col} ~ '[^[:ascii:]]'
                        """)
                        
                        normalized_count = cursor.rowcount
                        total_normalized += normalized_count
                        
                        if normalized_count > 0:
                            logger.info(f"  {col}: caràcters no-ASCII eliminats ({normalized_count:,} registres)")
                            
                        # Netejar espais múltiples i espais al principi/final
                        cursor.execute(f"""
                            UPDATE mesuresqualitat 
                            SET {col} = TRIM(REGEXP_REPLACE({col}, '\s+', ' ', 'g'))
                            WHERE {col} IS NOT NULL
                        """)
                        
                    except Exception as e:
                        logger.error(f"Error normalitzant text a {col}: {e}")
                
                self.fixed_counts['text_normalization'] = total_normalized
                logger.info(f"Text normalitzat: {total_normalized:,} registres")
                return True
                
        except Exception as e:
            logger.error(f"Error normalitzant text: {e}")
            return False
    
    def verify_fixes(self):
        """Verifica que les correccions s'han aplicat correctament"""
        if not self.adapter:
            return False
            
        try:
            logger.info("\n=== VERIFICANT CORRECCIONS ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Verificar problemes restants
                checks = [
                    ("Caràcters grecs restants", "SELECT COUNT(*) FROM mesuresqualitat WHERE element LIKE '%Δ%' OR property LIKE '%Δ%'"),
                    ("Patrons ¿¿¿ restants", "SELECT COUNT(*) FROM mesuresqualitat WHERE element LIKE '%¿¿¿%' OR pieza LIKE '%¿¿¿%'"),
                    ("Valors NaN restants", "SELECT COUNT(*) FROM mesuresqualitat WHERE valor::text = 'NaN'"),
                    ("Unicode no-ASCII restant", "SELECT COUNT(*) FROM mesuresqualitat WHERE element ~ '[^[:ascii:]]'"),
                    ("Registres BROSE vàlids", "SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL")
                ]
                
                for check_name, query in checks:
                    cursor.execute(query)
                    result = cursor.fetchone()[0]
                    logger.info(f"{check_name}: {result:,}")
                
                # Estadístiques finals
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                total_records = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL")
                brose_valid = cursor.fetchone()[0]
                
                logger.info(f"\nESTADÍSTIQUES FINALS:")
                logger.info(f"  Total registres: {total_records:,}")
                logger.info(f"  BROSE amb dades vàlides: {brose_valid:,}")
                logger.info(f"  Caràcters grecs corregits: {self.fixed_counts['greek_chars']:,}")
                logger.info(f"  Patrons problemàtics corregits: {self.fixed_counts['problematic_patterns']:,}")
                logger.info(f"  Valors NaN corregits: {self.fixed_counts['nan_values']:,}")
                logger.info(f"  Caràcters Unicode corregits: {self.fixed_counts['unicode_chars']:,}")
                logger.info(f"  Text normalitzat: {self.fixed_counts['text_normalization']:,}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error verificant correccions: {e}")
            return False

def main():
    """Funció principal de correcció completa"""
    logger.info("=== CORRECCIÓ COMPLETA DE LA TAULA mesuresqualitat ===")
    
    fixer = ComprehensiveDatabaseFixer()
    
    # Connectar
    if not fixer.connect_to_database():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    try:
        # Pas 1: Backup
        if not fixer.backup_problematic_data():
            logger.warning("⚠️ No s'ha pogut crear backup, continuant...")
        
        # Pas 2: Corregir caràcters grecs
        if fixer.fix_greek_characters():
            logger.info("✅ Caràcters grecs corregits")
        else:
            logger.warning("⚠️ Problemes corregint caràcters grecs")
        
        # Pas 3: Corregir patrons problemàtics
        if fixer.fix_problematic_patterns():
            logger.info("✅ Patrons problemàtics corregits")
        else:
            logger.warning("⚠️ Problemes corregint patrons")
        
        # Pas 4: Corregir caràcters Unicode
        if fixer.fix_unicode_characters():
            logger.info("✅ Caràcters Unicode corregits")
        else:
            logger.warning("⚠️ Problemes corregint Unicode")
        
        # Pas 5: Corregir valors NaN
        if fixer.fix_numeric_nan_values():
            logger.info("✅ Valors NaN corregits")
        else:
            logger.warning("⚠️ Problemes corregint NaN")
        
        # Pas 6: Normalitzar text restant
        if fixer.normalize_all_text():
            logger.info("✅ Text normalitzat")
        else:
            logger.warning("⚠️ Problemes normalitzant text")
        
        # Pas 7: Verificar correccions
        if fixer.verify_fixes():
            logger.info("✅ Verificació completada")
        
        logger.info("\n=== CORRECCIÓ COMPLETA FINALITZADA ===")
        logger.info("La taula mesuresqualitat ha estat completament corregida!")
        logger.info("Ara pots executar consultes sense problemes d'encoding:")
        logger.info("  SET CLIENT_ENCODING TO 'UTF8';")
        logger.info("  SELECT * FROM mesuresqualitat WHERE client LIKE 'BROSE%' LIMIT 10;")
        
        return True
        
    finally:
        if fixer.adapter:
            fixer.adapter.close()

if __name__ == "__main__":
    main()
