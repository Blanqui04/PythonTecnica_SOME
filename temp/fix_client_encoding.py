#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resolver el problema de encoding del cliente PostgreSQL

El error "character with byte sequence 0xce 0x94 in encoding UTF8 has no equivalent in encoding WIN1252"
se produce cuando el cliente PostgreSQL está configurado para usar WIN1252 pero los datos están en UTF8.

Esta script proporciona múltiples soluciones para este problema.
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

class ClientEncodingFixer:
    """Solucionador de problemes d'encoding del client"""
    
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
        """Connecta a la base de dades amb encoding forçat"""
        db_config = self.load_db_config()
        if not db_config:
            return False
            
        self.adapter = QualityMeasurementDBAdapter(db_config)
        return self.adapter.connect()
    
    def check_database_encodings(self):
        """Verifica els encodings de la base de dades"""
        if not self.adapter:
            return False
            
        try:
            logger.info("=== VERIFICANT ENCODINGS DE LA BASE DE DADES ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Encoding de la base de dades
                cursor.execute("SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = current_database()")
                db_encoding = cursor.fetchone()[0]
                logger.info(f"Encoding de la base de dades: {db_encoding}")
                
                # Encoding del client
                cursor.execute("SHOW client_encoding")
                client_encoding = cursor.fetchone()[0]
                logger.info(f"Encoding del client: {client_encoding}")
                
                # Encoding del servidor
                cursor.execute("SHOW server_encoding") 
                server_encoding = cursor.fetchone()[0]
                logger.info(f"Encoding del servidor: {server_encoding}")
                
                # Verificar si hi ha problemes
                if client_encoding != 'UTF8':
                    logger.warning(f"⚠️ PROBLEMA: Client encoding és {client_encoding}, hauria de ser UTF8")
                    return False
                else:
                    logger.info("✅ Client encoding és correcte (UTF8)")
                    return True
                    
        except Exception as e:
            logger.error(f"Error verificant encodings: {e}")
            return False
    
    def force_client_utf8(self):
        """Força l'encoding del client a UTF8"""
        if not self.adapter:
            return False
            
        try:
            logger.info("Forçant encoding del client a UTF8...")
            
            with self.adapter.connection.cursor() as cursor:
                # Forçar UTF8
                cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
                
                # Verificar
                cursor.execute("SHOW client_encoding")
                new_encoding = cursor.fetchone()[0]
                logger.info(f"Nou encoding del client: {new_encoding}")
                
                if new_encoding == 'UTF8':
                    logger.info("✅ Client encoding configurat a UTF8")
                    return True
                else:
                    logger.error(f"❌ No s'ha pogut configurar UTF8, encara és: {new_encoding}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error configurant client encoding: {e}")
            return False
    
    def test_brose_query_with_utf8(self):
        """Prova la consulta BROSE amb UTF8 forçat"""
        if not self.adapter:
            return False
            
        try:
            logger.info("=== TESTEJANT CONSULTA BROSE AMB UTF8 ===")
            
            with self.adapter.connection.cursor() as cursor:
                # Assegurar UTF8
                cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
                
                # Test 1: Consulta bàsica
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%'")
                count = cursor.fetchone()[0]
                logger.info(f"Total registres BROSE: {count:,}")
                
                # Test 2: Consulta amb dades
                cursor.execute("""
                    SELECT client, element, actual, nominal 
                    FROM mesuresqualitat 
                    WHERE client LIKE 'BROSE%' 
                      AND actual IS NOT NULL 
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                logger.info("Exemples de dades BROSE:")
                for i, row in enumerate(results, 1):
                    client, element, actual, nominal = row
                    logger.info(f"  {i}. Client: {client}, Element: {element}, Actual: {actual}, Nominal: {nominal}")
                
                # Test 3: Verificar que no hi ha caràcters problemàtics
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM mesuresqualitat 
                    WHERE client LIKE 'BROSE%' AND element ~ '[^[:ascii:]]'
                """)
                non_ascii = cursor.fetchone()[0]
                logger.info(f"Registres BROSE amb caràcters no-ASCII: {non_ascii}")
                
                if non_ascii == 0:
                    logger.info("✅ Tots els caràcters són ASCII, no hi hauria d'haver problemes d'encoding")
                else:
                    logger.warning(f"⚠️ Encara hi ha {non_ascii} registres amb caràcters no-ASCII")
                
                return True
                
        except Exception as e:
            logger.error(f"Error testejant consulta BROSE: {e}")
            return False
    
    def generate_client_config_solutions(self):
        """Genera solucions per configurar el client correctament"""
        try:
            logger.info("=== GENERANT SOLUCIONS DE CONFIGURACIÓ ===")
            
            solutions = {
                "psql_commands": [
                    "-- Solució 1: Configurar encoding a cada sessió",
                    "SET CLIENT_ENCODING TO 'UTF8';",
                    "\\encoding UTF8",
                    "",
                    "-- Després executa la teva consulta:",
                    "SELECT * FROM mesuresqualitat WHERE client LIKE 'BROSE%' LIMIT 10;",
                ],
                
                "psql_connection": [
                    "-- Solució 2: Connectar directament amb UTF8",
                    "psql -h tu_host -p tu_port -d documentacio_tecnica -U tu_user --client-encoding=UTF8",
                ],
                
                "environment_vars": [
                    "-- Solució 3: Variables d'entorn (Windows)",
                    "set PGCLIENTENCODING=UTF8",
                    "psql -h tu_host -p tu_port -d documentacio_tecnica -U tu_user",
                    "",
                    "-- Solució 3: Variables d'entorn (Linux/Mac)",
                    "export PGCLIENTENCODING=UTF8",
                    "psql -h tu_host -p tu_port -d documentacio_tecnica -U tu_user",
                ],
                
                "pgpass_config": [
                    "-- Solució 4: Configurar .psqlrc (fitxer de configuració automàtica)",
                    "-- Crear fitxer .psqlrc a la teva carpeta home amb:",
                    "\\set AUTOCOMMIT off",
                    "\\encoding UTF8",
                    "SET CLIENT_ENCODING TO 'UTF8';",
                ]
            }
            
            # Guardar solucions a fitxer
            solutions_file = Path(__file__).parent / "client_encoding_solutions.txt"
            with open(solutions_file, 'w', encoding='utf-8') as f:
                f.write("SOLUCIONS PER AL PROBLEMA D'ENCODING DEL CLIENT POSTGRESQL\n")
                f.write("=" * 70 + "\n\n")
                f.write("El error 'character with byte sequence 0xce 0x94 in encoding UTF8 has no equivalent in encoding WIN1252'\n")
                f.write("es produeix perquè el client PostgreSQL està configurat per usar WIN1252 en lloc d'UTF8.\n\n")
                
                for section, commands in solutions.items():
                    f.write(f"{section.upper().replace('_', ' ')}\n")
                    f.write("-" * 40 + "\n")
                    for command in commands:
                        f.write(f"{command}\n")
                    f.write("\n")
                
                f.write("CONSULTES DE TEST (executa després de configurar UTF8):\n")
                f.write("-" * 50 + "\n")
                f.write("SET CLIENT_ENCODING TO 'UTF8';\n")
                f.write("SELECT COUNT(*) FROM mesuresqualitat WHERE client LIKE 'BROSE%';\n")
                f.write("SELECT client, actual, nominal FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL LIMIT 5;\n")
            
            logger.info(f"Solucions guardades a: {solutions_file}")
            return solutions_file
            
        except Exception as e:
            logger.error(f"Error generant solucions: {e}")
            return None
    
    def create_safe_connection_script(self):
        """Crea script per connectar de forma segura"""
        try:
            db_config = self.load_db_config()
            if not db_config:
                return None
                
            config = db_config.get('primary', db_config)
            
            # Script per Windows
            windows_script = f'''@echo off
echo Connectant a PostgreSQL amb encoding UTF8...
set PGCLIENTENCODING=UTF8
psql -h {config['host']} -p {config['port']} -d {config['database']} -U {config['user']} --client-encoding=UTF8
'''
            
            # Script per Linux/Mac  
            unix_script = f'''#!/bin/bash
echo "Connectant a PostgreSQL amb encoding UTF8..."
export PGCLIENTENCODING=UTF8
psql -h {config['host']} -p {config['port']} -d {config['database']} -U {config['user']} --client-encoding=UTF8
'''
            
            # Guardar scripts
            windows_file = Path(__file__).parent / "connect_utf8.bat"
            unix_file = Path(__file__).parent / "connect_utf8.sh"
            
            with open(windows_file, 'w', encoding='utf-8') as f:
                f.write(windows_script)
                
            with open(unix_file, 'w', encoding='utf-8') as f:
                f.write(unix_script)
            
            # Fer executable l'script Unix
            try:
                os.chmod(unix_file, 0o755)
            except:
                pass
                
            logger.info(f"Scripts de connexió creats:")
            logger.info(f"  Windows: {windows_file}")
            logger.info(f"  Linux/Mac: {unix_file}")
            
            return windows_file, unix_file
            
        except Exception as e:
            logger.error(f"Error creant scripts de connexió: {e}")
            return None

def main():
    """Funció principal per resoldre problemes d'encoding del client"""
    logger.info("=== SOLUCIONADOR DE PROBLEMES D'ENCODING DEL CLIENT ===")
    
    fixer = ClientEncodingFixer()
    
    # Connectar
    if not fixer.connect_to_database():
        logger.error("No es pot connectar a la base de dades")
        return False
    
    try:
        # Verificar encodings
        encoding_ok = fixer.check_database_encodings()
        
        # Forçar UTF8 si cal
        if not encoding_ok:
            if fixer.force_client_utf8():
                logger.info("✅ UTF8 forçat correctament")
            else:
                logger.warning("⚠️ No s'ha pogut forçar UTF8")
        
        # Testejar consulta BROSE
        if fixer.test_brose_query_with_utf8():
            logger.info("✅ Consulta BROSE funciona amb UTF8")
        
        # Generar solucions
        solutions_file = fixer.generate_client_config_solutions()
        if solutions_file:
            logger.info(f"✅ Solucions generades: {solutions_file}")
        
        # Crear scripts de connexió
        scripts = fixer.create_safe_connection_script()
        if scripts:
            logger.info("✅ Scripts de connexió creats")
        
        logger.info("\n=== RESUM DE LA SOLUCIÓ ===")
        logger.info("El problema és que el teu client PostgreSQL està configurat amb WIN1252.")
        logger.info("Per solucionar-ho, executa SEMPRE abans de les consultes:")
        logger.info("  SET CLIENT_ENCODING TO 'UTF8';")
        logger.info("  \\encoding UTF8")
        logger.info("")
        logger.info("O utilitza un dels scripts de connexió creats per connectar directament amb UTF8.")
        
        return True
        
    finally:
        if fixer.adapter:
            fixer.adapter.close()

if __name__ == "__main__":
    main()
