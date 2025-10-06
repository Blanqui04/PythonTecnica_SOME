#!/usr/bin/env python3
"""
Script de debug per analitzar el processament dels LOT durant la càrrega de dades.

Analitza:
1. Formats dels noms de fitxers CSV reals
2. Extracció de LOT dels noms de fitxers
3. Que passa durant el processament del DataFrame
4. Com es guarden els LOT a la base de dades
"""

import sys
import os
import pandas as pd
sys.path.append(r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\src')

from services.network_scanner import NetworkScanner
from database.quality_measurement_adapter import QualityMeasurementDBAdapter
import logging

# Configurar logging per veure els detalls
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_lot_processing():
    """Debug del processament dels LOT"""
    
    config_path = r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\config.ini'
    
    print("=" * 80)
    print("DEBUG DEL PROCESSAMENT DE LOT")
    print("=" * 80)
    
    try:
        # 1. VERIFICAR NOMS DE FITXERS CSV REALS
        print("\n1. ANALITZANT ESTRUCTURA DE FITXERS...")
        
        # Buscar fitxers CSV als directoris habituals de GOMPC
        possible_dirs = [
            r'\\172.26.5.159\some\PROJECTES\GOMPC',
            r'\\172.26.5.159\some\PROJECTES\GOMPCNOU',
            r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\data\raw',
            r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\data\spc',
            r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\data\temp'
        ]
        
        csv_files_found = []
        for directory in possible_dirs:
            if os.path.exists(directory):
                print(f"Explorant directori: {directory}")
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.csv'):
                            csv_files_found.append(os.path.join(root, file))
                            if len(csv_files_found) >= 10:  # Limitar per no sobrecarregar
                                break
                    if len(csv_files_found) >= 10:
                        break
            else:
                print(f"Directori NO trobat: {directory}")
        
        # 2. ANALITZAR NOMS DE FITXERS TROBATS
        print(f"\n2. FITXERS CSV TROBATS ({len(csv_files_found)}):")
        scanner = NetworkScanner(config_path)
        
        for i, csv_path in enumerate(csv_files_found[:10], 1):
            filename = os.path.basename(csv_path)
            print(f"\n{i}. Fitxer: {filename}")
            
            # Intentar extreure LOT
            lot, data_hora = scanner.extract_lot_and_datetime_from_filename(filename)
            print(f"   LOT extret: '{lot}'")
            print(f"   Data extreta: '{data_hora}'")
            
            # Verificar si segueix el patró esperat
            if lot and data_hora:
                print(f"   ✅ Segueix el patró esperat")
            else:
                print(f"   ❌ NO segueix el patró esperat")
                # Mostrar què passaria amb formats alternatius
                print(f"   Possible formats alternatius:")
                # Provar altres patrons comuns
                import re
                name_without_ext = os.path.splitext(filename)[0]
                
                # Patró 1: només data al final
                pattern1 = r'.*(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
                if re.match(pattern1, name_without_ext):
                    print(f"     - Conté data al final: SÍ")
                else:
                    print(f"     - Conté data al final: NO")
                
                # Patró 2: LOT literal
                if 'LOT' in filename.upper():
                    print(f"     - Conté 'LOT' literal: SÍ")
                else:
                    print(f"     - Conté 'LOT' literal: NO")
        
        # 3. SIMULAR PROCESSAMENT DE FITXER
        if csv_files_found:
            print(f"\n3. SIMULANT PROCESSAMENT DEL PRIMER FITXER...")
            first_csv = csv_files_found[0]
            filename = os.path.basename(first_csv)
            
            print(f"Fitxer a processar: {filename}")
            
            # Extreure dades com ho fa el NetworkScanner
            lot, data_hora = scanner.extract_lot_and_datetime_from_filename(filename)
            print(f"LOT extret: '{lot}'")
            print(f"Data extreta: '{data_hora}'")
            
            if lot and data_hora:
                # Simular lectura CSV
                try:
                    df = scanner.read_csv_file(first_csv, "TEST_CLIENT", "TEST_REF", lot, data_hora)
                    if df is not None:
                        print(f"CSV llegit correctament: {len(df)} files")
                        if 'LOT' in df.columns:
                            unique_lots = df['LOT'].unique()
                            print(f"LOT values únics al DataFrame: {unique_lots}")
                        else:
                            print("❌ Columna LOT no trobada al DataFrame")
                    else:
                        print("❌ Error llegint el CSV")
                except Exception as e:
                    print(f"❌ Error processant CSV: {e}")
        
        # 4. CONSULTAR BASE DE DADES PER EXEMPLES REALS
        print(f"\n4. CONSULTANT BASE DE DADES...")
        try:
            # Carregar config de BD
            db_config = scanner.load_db_config()
            if db_config:
                adapter = QualityMeasurementDBAdapter(db_config)
                adapter.maquina = 'gompc'
                
                # Consultar exemples recents
                query = """
                SELECT id_lot, data_hora, client, id_referencia_client
                FROM mesuresqualitat 
                WHERE maquina = 'gompc'
                ORDER BY data_hora DESC
                LIMIT 5
                """
                
                result = adapter.execute_query(query)
                if result:
                    print("Exemples recents de la BD:")
                    for row in result:
                        print(f"  LOT: '{row['id_lot']}' | Client: {row['client']} | Ref: {row['id_referencia_client']}")
                        
                        # Verificar si el LOT segueix patró problemàtic
                        lot_val = row['id_lot']
                        if lot_val.startswith('LOT_') and len(lot_val.split('_')) >= 4:
                            print(f"    ❌ Patró problemàtic detectat: {lot_val}")
                        elif len(lot_val) == 8 and lot_val.replace('_', '').isalnum():
                            print(f"    ✅ LOT sembla correcte: {lot_val}")
                        else:
                            print(f"    ❓ LOT format desconegut: {lot_val}")
                
            else:
                print("❌ No es pot carregar la configuració de BD")
                
        except Exception as e:
            print(f"❌ Error consultant BD: {e}")
    
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_lot_processing()