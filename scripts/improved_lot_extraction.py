#!/usr/bin/env python3
"""
IMPROVED LOT EXTRACTION FUNCTION

This script provides the improved LOT extraction function and demonstrates
how to fix the LOT pipeline issues without requiring database access.
"""

import sys
import os
import re
from datetime import datetime
from typing import Tuple, Optional
sys.path.append(r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\src')

def extract_lot_and_datetime_from_filename_improved(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Funció millorada per extreure LOT i DATA_HORA del nom del fitxer GOMPC
    
    Formats acceptats:
    1. LOT_YYYY_MM_DD_HH_MM_SS.csv (format principal)
    2. XXXX_YYYY_MM_DD_HH_MM_SS.csv (on XXXX és el LOT de 4-12 caràcters)
    
    Args:
        filename: Nom del fitxer CSV
        
    Returns:
        tuple: (LOT, DATA_HORA) o (None, None) si no es pot extreure
    """
    try:
        # Eliminar extensió
        name_without_ext = os.path.splitext(filename)[0]
        
        # Patró principal: LOT_YYYY_MM_DD_HH_MM_SS
        # El LOT pot ser de 4 a 12 caràcters alfanumèrics
        pattern = r'^([A-Za-z0-9]{4,12})_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
        match = re.match(pattern, name_without_ext)
        
        if match:
            lot = match.group(1).upper()  # Normalitzar a majúscules
            year = match.group(2)
            month = match.group(3)
            day = match.group(4)
            hour = match.group(5)
            minute = match.group(6)
            second = match.group(7)
            
            # Validar data
            try:
                data_hora_obj = datetime(int(year), int(month), int(day), 
                                       int(hour), int(minute), int(second))
                data_hora = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                
                print(f"✅ LOT extret: '{lot}' del fitxer '{filename}'")
                return lot, data_hora
                
            except ValueError as e:
                print(f"❌ Data invàlida en fitxer {filename}: {e}")
                return None, None
        else:
            print(f"❌ Format no reconegut: {filename}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error extraient LOT de {filename}: {e}")
        return None, None

def test_lot_extraction():
    """Test the improved LOT extraction with various filename patterns"""
    
    print("=" * 80)
    print("TEST DE LA FUNCIÓ MILLORADA D'EXTRACCIÓ DE LOT")
    print("=" * 80)
    
    # Test filenames based on expected GOMPC format
    test_filenames = [
        # Valid format examples (these should work)
        "1200135A_2023_01_31_22_01_56.csv",      # Your real example
        "A123B456_2024_06_15_14_30_45.csv",     # 8-char alphanumeric  
        "LOT5678_2024_01_01_00_00_00.csv",      # Starting with LOT
        "X99Y88Z_2023_12_25_18_45_30.csv",      # 7-char mixed
        "ABCD_2024_03_15_09_30_22.csv",         # 4-char minimum
        "VERYLONGCODE_2024_01_01_12_00_00.csv", # 12-char maximum
        
        # Invalid format examples (these should fail gracefully)
        "measurement_data_2024_01_15.csv",       # No timestamp format
        "temp_file.csv",                         # Generic name
        "GOMPC_export_20240115.csv",            # Different format
        "12_2024_01_01_12_00_00.csv",           # Too short LOT (2 chars)
        "TOOLONGLOTNUMBER_2024_01_01_12_00_00.csv", # Too long LOT (16 chars)
        "ABC_2024_13_01_12_00_00.csv",          # Invalid month (13)
        "XYZ_2024_02_30_12_00_00.csv",          # Invalid date (Feb 30)
    ]
    
    success_count = 0
    valid_expected = 6  # First 6 should be valid
    
    print("FITXERS QUE HAURIEN DE SER VÀLIDS:")
    print("-" * 40)
    
    for i, filename in enumerate(test_filenames):
        lot, data_hora = extract_lot_and_datetime_from_filename_improved(filename)
        
        if i < valid_expected:  # Expected to be valid
            if lot and data_hora:
                print(f"{i+1:2d}. ✅ '{filename}'")
                print(f"     LOT: '{lot}' | Data: '{data_hora}'")
                success_count += 1
            else:
                print(f"{i+1:2d}. ❌ '{filename}' (havia de ser vàlid)")
        else:  # Expected to be invalid
            if lot and data_hora:
                print(f"{i+1:2d}. ⚠️  '{filename}' (no havia de ser vàlid)")
                print(f"     LOT: '{lot}' | Data: '{data_hora}'")
            else:
                print(f"{i+1:2d}. ✅ '{filename}' (correctament rebutjat)")
    
    print(f"\nRESULTAT: {success_count}/{valid_expected} fitxers vàlids processats correctament")
    return success_count >= valid_expected

def create_network_scanner_patch():
    """Create a patch for the NetworkScanner class"""
    
    patch_code = '''
# PATCH PER A network_scanner.py
# Substitueix la funció extract_lot_and_datetime_from_filename existent

def extract_lot_and_datetime_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Funció millorada per extreure LOT i DATA_HORA del nom del fitxer GOMPC
    
    Format esperat: LOT_YYYY_MM_DD_HH_MM_SS.csv
    On LOT és un codi alfanumèric de 4-12 caràcters
    
    Args:
        filename: Nom del fitxer (ex: "1200135A_2023_01_31_22_01_56.csv")
        
    Returns:
        tuple: (LOT, DATA_HORA) o (None, None) si no es pot extreure
    """
    try:
        # Eliminar l'extensió
        name_without_ext = os.path.splitext(filename)[0]
        
        # Patró regex millorat per LOT_YYYY_MM_DD_HH_MM_SS
        # LOT: 4-12 caràcters alfanumèrics
        pattern = r'^([A-Za-z0-9]{4,12})_(\\d{4})_(\\d{2})_(\\d{2})_(\\d{2})_(\\d{2})_(\\d{2})$'
        match = re.match(pattern, name_without_ext)
        
        if match:
            lot = match.group(1).upper()  # Normalitzar a majúscules
            year = match.group(2)
            month = match.group(3) 
            day = match.group(4)
            hour = match.group(5)
            minute = match.group(6)
            second = match.group(7)
            
            # Validar que la data és vàlida
            try:
                data_hora_obj = datetime(int(year), int(month), int(day),
                                       int(hour), int(minute), int(second))
                # Construir DATA_HORA en format ISO
                data_hora = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                
                logger.info(f"LOT extret correctament: '{lot}' del fitxer '{filename}'")
                return lot, data_hora
                
            except ValueError as e:
                logger.warning(f"Data invàlida en fitxer {filename}: {e}")
                return None, None
        else:
            logger.warning(f"Format de fitxer no reconegut: {filename}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error extraient LOT de {filename}: {e}")
        return None, None
'''

    print("\n" + "=" * 80)
    print("PATCH PER A network_scanner.py")
    print("=" * 80)
    print("Per aplicar aquest patch:")
    print("1. Obre: src/services/network_scanner.py")
    print("2. Localitza la funció extract_lot_and_datetime_from_filename (línia ~595)")
    print("3. Substitueix-la per aquesta versió millorada:")
    print("-" * 40)
    print(patch_code)
    
def create_data_fix_recommendations():
    """Create recommendations for fixing existing data"""
    
    print("\n" + "=" * 80)
    print("RECOMANACIONS PER CORREGIR DADES EXISTENTS")
    print("=" * 80)
    
    recommendations = [
        "1. IDENTIFICAR REGISTRES PROBLEMÀTICS:",
        "   SQL: SELECT id_lot, COUNT(*) FROM mesuresqualitat",
        "        WHERE maquina='gompc' AND id_lot LIKE 'LOT_%'",
        "        GROUP BY id_lot ORDER BY COUNT(*) DESC;",
        "",
        "2. RECUPERAR LOTS REALS DES DE id_referencia_some:",
        "   - Els LOTs reals estan en la tercera part d'id_referencia_some",
        "   - Format: CLIENT_REFERENCIA_LOT_REAL", 
        "   - Extraure i actualitzar id_lot amb el valor real",
        "",
        "3. SQL DE CORRECCIÓ (EXEMPLE):",
        "   UPDATE mesuresqualitat SET",
        "   id_lot = SPLIT_PART(id_referencia_some, '_', 3)",
        "   WHERE maquina='gompc' AND id_lot LIKE 'LOT_%'",
        "   AND SPLIT_PART(id_referencia_some, '_', 3) ~ '^[A-Z0-9]{7,8}$';",
        "",
        "4. VERIFICACIÓ POST-CORRECCIÓ:",
        "   - Comprovar que tots els LOTs tenen format correcte",
        "   - Validar que no hi ha LOTs duplicats incorrectes",  
        "   - Executar tests de consistència de dades",
        "",
        "5. MONITORITZACIÓ FUTURA:",
        "   - Crear alertes per LOTs amb format 'LOT_YYYY_MM_DD'",
        "   - Revisar diàriament la qualitat dels LOTs nous",
        "   - Implementar validació en temps real",
    ]
    
    for rec in recommendations:
        print(rec)

def main():
    """Main function to run the LOT extraction improvements"""
    
    print("MILLORES DEL SISTEMA D'EXTRACCIÓ DE LOT")
    print("=" * 80)
    print("Aquest script proporciona:")
    print("✅ Funció millorada d'extracció de LOT")
    print("✅ Tests per validar el funcionament") 
    print("✅ Patch per aplicar al NetworkScanner")
    print("✅ Recomanacions per corregir dades existents")
    print()
    
    # Test the improved function
    success = test_lot_extraction()
    
    if success:
        print("\n🎉 TOTS ELS TESTS HAN PASSAT CORRECTAMENT!")
    else:
        print("\n⚠️  ALGUNS TESTS HAN FALLAT - Revisar la implementació")
    
    # Provide patch and recommendations  
    create_network_scanner_patch()
    create_data_fix_recommendations()
    
    print("\n" + "=" * 80)
    print("RESUM I PASSOS SEGÜENTS")
    print("=" * 80)
    print("1. ✅ Aplicar el patch a network_scanner.py")
    print("2. 🔍 Connectar a la base de dades per analitzar dades existents")
    print("3. 🔧 Executar correccions de dades si és necessari") 
    print("4. 📊 Implementar monitorització per prevenir futurs problemes")
    print("5. 📝 Documentar el format correcte dels fitxers CSV")
    
    print(f"\n✅ Script completat satisfactòriament!")

if __name__ == "__main__":
    main()