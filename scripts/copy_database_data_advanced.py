#!/usr/bin/env python3
"""
Script avançat per gestionar còpia de dades entre bases de dades

Aquest script ofereix opcions per:
- Verificar connexions a les BBDD
- Comptar registres abans de copiar
- Copiar dades amb confirmació
- Verificar integritat després de la còpia

Ús:
    python copy_database_data_advanced.py [opcions]
    
Opcions:
    --check-only    : Només verificar connexions i comptar registres
    --force         : Copiar sense confirmació
    --verify        : Verificar integritat després de la còpia
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Afegir el directori arrel al path per poder importar mòduls
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.network_scanner import NetworkScanner
from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
import json

def setup_logging():
    """Configura el logging per al script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/database_copy_advanced.log', encoding='utf-8')
        ]
    )

def load_db_configs():
    """Carrega les configuracions de BBDD"""
    try:
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        return {
            'source': full_config['secondary'],  # airflow_db
            'target': full_config['primary']     # documentacio_tecnica
        }
    except Exception as e:
        print(f"❌ Error carregant configuració: {e}")
        return None

def check_database_connections(configs):
    """Verifica les connexions a ambdues BBDD"""
    print("\n🔍 VERIFICANT CONNEXIONS...")
    
    results = {}
    
    # Verificar connexió origen
    print(f"📡 Provant connexió a BBDD origen ({configs['source']['database']})...")
    source_adapter = QualityMeasurementDBAdapter(configs['source'])
    if source_adapter.connect():
        print("✅ Connexió origen correcta")
        results['source_connected'] = True
        
        # Comptar registres origen
        try:
            with source_adapter.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                source_count = cursor.fetchone()[0]
                results['source_count'] = source_count
                print(f"📊 Registres a l'origen: {source_count:,}")
        except Exception as e:
            print(f"⚠️  Error comptant registres origen: {e}")
            results['source_count'] = -1
        
        source_adapter.close()
    else:
        print("❌ Error connectant a la BBDD origen")
        results['source_connected'] = False
        results['source_count'] = -1
    
    # Verificar connexió destí
    print(f"📡 Provant connexió a BBDD destí ({configs['target']['database']})...")
    target_adapter = QualityMeasurementDBAdapter(configs['target'])
    if target_adapter.connect():
        print("✅ Connexió destí correcta")
        results['target_connected'] = True
        
        # Comptar registres destí
        try:
            with target_adapter.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                target_count = cursor.fetchone()[0]
                results['target_count'] = target_count
                print(f"📊 Registres al destí: {target_count:,}")
        except Exception as e:
            print(f"⚠️  Error comptant registres destí (taula pot no existir): {e}")
            results['target_count'] = 0
        
        target_adapter.close()
    else:
        print("❌ Error connectant a la BBDD destí")
        results['target_connected'] = False
        results['target_count'] = -1
    
    return results

def verify_data_integrity(configs):
    """Verifica la integritat de les dades després de la còpia"""
    print("\n🔍 VERIFICANT INTEGRITAT DE DADES...")
    
    try:
        # Connectar a ambdues BBDD
        source_adapter = QualityMeasurementDBAdapter(configs['source'])
        target_adapter = QualityMeasurementDBAdapter(configs['target'])
        
        if not source_adapter.connect() or not target_adapter.connect():
            print("❌ Error connectant per verificar integritat")
            return False
        
        with source_adapter.connection.cursor() as source_cursor, \
             target_adapter.connection.cursor() as target_cursor:
            
            # Comptar registres totals
            source_cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            source_total = source_cursor.fetchone()[0]
            
            target_cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
            target_total = target_cursor.fetchone()[0]
            
            print(f"📊 Registres origen: {source_total:,}")
            print(f"📊 Registres destí: {target_total:,}")
            
            if source_total != target_total:
                print("⚠️  ADVERTÈNCIA: El nombre de registres no coincideix!")
            else:
                print("✅ Nombre de registres coincideix")
            
            # Verificar alguns camps clau
            source_cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM mesuresqualitat")
            source_dates = source_cursor.fetchone()
            
            target_cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM mesuresqualitat")
            target_dates = target_cursor.fetchone()
            
            print(f"📅 Rang dates origen: {source_dates[0]} - {source_dates[1]}")
            print(f"📅 Rang dates destí: {target_dates[0]} - {target_dates[1]}")
            
            # Verificar clients únics
            source_cursor.execute("SELECT COUNT(DISTINCT client) FROM mesuresqualitat")
            source_clients = source_cursor.fetchone()[0]
            
            target_cursor.execute("SELECT COUNT(DISTINCT client) FROM mesuresqualitat")
            target_clients = target_cursor.fetchone()[0]
            
            print(f"🏢 Clients únics origen: {source_clients}")
            print(f"🏢 Clients únics destí: {target_clients}")
            
        source_adapter.close()
        target_adapter.close()
        
        return source_total == target_total
        
    except Exception as e:
        print(f"❌ Error verificant integritat: {e}")
        return False

def main():
    """Funció principal del script avançat"""
    parser = argparse.ArgumentParser(description='Còpia avançada de dades entre BBDD')
    parser.add_argument('--check-only', action='store_true', 
                       help='Només verificar connexions i comptar registres')
    parser.add_argument('--force', action='store_true',
                       help='Copiar sense confirmació')
    parser.add_argument('--verify', action='store_true',
                       help='Verificar integritat després de la còpia')
    
    args = parser.parse_args()
    
    print("="*70)
    print("CÒPIA AVANÇADA DE DADES ENTRE BASES DE DADES")
    print("="*70)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Carregar configuracions
    configs = load_db_configs()
    if not configs:
        return 1
    
    print(f"Origen: {configs['source']['database']} ({configs['source']['host']}:{configs['source']['port']})")
    print(f"Destí: {configs['target']['database']} ({configs['target']['host']}:{configs['target']['port']})")
    print("="*70)
    
    # Verificar connexions
    check_results = check_database_connections(configs)
    
    if not check_results['source_connected']:
        print("\n❌ No es pot connectar a la BBDD origen. Sortint.")
        return 1
    
    if not check_results['target_connected']:
        print("\n❌ No es pot connectar a la BBDD destí. Sortint.")
        return 1
    
    # Si només és verificació, sortir aquí
    if args.check_only:
        print("\n✅ Verificació completada.")
        return 0
    
    # Mostrar resum abans de copiar
    print(f"\n📋 RESUM ABANS DE LA CÒPIA:")
    print(f"   Registres origen: {check_results['source_count']:,}")
    print(f"   Registres destí: {check_results['target_count']:,}")
    
    if check_results['target_count'] > 0:
        print(f"\n⚠️  ADVERTÈNCIA: La taula destí ja conté {check_results['target_count']:,} registres.")
        print("   Aquests registres poden ser sobreescrits o duplicats.")
    
    # Confirmació (tret que sigui --force)
    if not args.force:
        response = input(f"\n❓ Voleu continuar amb la còpia? (S/N): ").strip().upper()
        if response not in ['S', 'SI', 'SÍ', 'Y', 'YES']:
            print("❌ Operació cancel·lada per l'usuari.")
            return 0
    
    try:
        # Executar còpia
        print("\n🔄 Iniciant còpia de dades...")
        scanner = NetworkScanner()
        result = scanner.copy_data_between_databases()
        
        if result['success']:
            print("\n✅ CÒPIA COMPLETADA CORRECTAMENT!")
            print(f"📊 Registres copiats: {result['records_copied']:,}")
            print(f"📊 Total registres: {result['records_total']:,}")
            print(f"📊 Registres saltats: {result.get('records_skipped', 0):,}")
            
            if result.get('errors'):
                print(f"\n⚠️  Errors durant la còpia:")
                for error in result['errors']:
                    print(f"   - {error}")
            
            # Verificar integritat si s'ha demanat
            if args.verify:
                if verify_data_integrity(configs):
                    print("\n✅ Verificació d'integritat correcta")
                else:
                    print("\n⚠️  Problemes detectats durant la verificació")
            
        else:
            print("\n❌ ERROR DURANT LA CÒPIA!")
            print(f"Error: {result['error']}")
            return 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operació cancel·lada per l'usuari")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        logger.error(f"Error inesperat: {e}")
        return 1
    
    print("\n🏁 Script finalitzat")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
