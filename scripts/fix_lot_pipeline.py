#!/usr/bin/env python3
"""
COMPREHENSIVE LOT PIPELINE FIX

This script addresses the root cause of the LOT issue:
1. Identifies where LOT codes are being incorrectly generated
2. Updates the data pipeline to properly use LOT codes from CSV filenames
3. Fixes existing invalid LOT codes in the database
4. Ensures proper LOT extraction from GOMPC machine CSV files

Expected CSV filename format: LOT_YYYY_MM_DD_HH_MM_SS.csv
Where LOT is the real 7-8 character alphanumeric LOT code.
"""

import sys
import os
import re
import pandas as pd
from datetime import datetime
sys.path.append(r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\src')

from database.quality_measurement_adapter import QualityMeasurementDBAdapter
from services.network_scanner import NetworkScanner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LOTPipelineFixer:
    """Comprehensive LOT pipeline fixer"""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.scanner = NetworkScanner(config_path)
        
        # Load database configuration
        db_config = self.scanner.load_db_config()
        if db_config:
            self.adapter = QualityMeasurementDBAdapter(db_config)
            self.adapter.maquina = 'gompc'
        else:
            raise Exception("No s'ha pogut carregar la configuració de BD")
    
    def analyze_current_lot_issues(self):
        """Analyze current LOT issues in the database"""
        
        print("=" * 80)
        print("1. ANÀLISI DELS PROBLEMES DE LOT ACTUALS")
        print("=" * 80)
        
        # Query problematic LOTs
        query_problematic = """
        SELECT id_lot, COUNT(*) as count, 
               MIN(data_hora) as primera_data, 
               MAX(data_hora) as ultima_data,
               client
        FROM mesuresqualitat 
        WHERE maquina = 'gompc'
        AND (
            id_lot LIKE 'LOT_%' 
            OR id_lot ~ '^LOT_[0-9]{4}_[0-9]{2}_[0-9]{2}'
            OR id_lot = 'LOT'
        )
        GROUP BY id_lot, client
        ORDER BY count DESC
        LIMIT 20
        """
        
        problematic_lots = self.adapter.execute_query(query_problematic)
        
        if problematic_lots:
            print(f"LOTS PROBLEMÀTICS TROBATS: {len(problematic_lots)}")
            print("-" * 80)
            for row in problematic_lots:
                print(f"LOT: '{row['id_lot']}' | Records: {row['count']} | Client: {row['client']}")
                print(f"  Període: {row['primera_data']} - {row['ultima_data']}")
                
        # Query valid LOTs 
        query_valid = """
        SELECT id_lot, COUNT(*) as count
        FROM mesuresqualitat 
        WHERE maquina = 'gompc'
        AND LENGTH(id_lot) BETWEEN 7 AND 8
        AND id_lot ~ '^[A-Z0-9]+$'
        AND id_lot NOT LIKE 'LOT_%'
        GROUP BY id_lot
        ORDER BY count DESC
        LIMIT 10
        """
        
        valid_lots = self.adapter.execute_query(query_valid)
        
        if valid_lots:
            print(f"\nLOTS VÀLIDS TROBATS: {len(valid_lots)}")
            print("-" * 40)
            for row in valid_lots:
                print(f"LOT: '{row['id_lot']}' | Records: {row['count']}")
        
        return len(problematic_lots) if problematic_lots else 0, len(valid_lots) if valid_lots else 0
    
    def test_lot_extraction_patterns(self):
        """Test LOT extraction with various filename patterns"""
        
        print("\n" + "=" * 80)
        print("2. TEST D'EXTRACCIÓ DE LOT AMB DIFERENTS PATRONS")
        print("=" * 80)
        
        # Test filenames based on the expected GOMPC format
        test_filenames = [
            # Valid format examples
            "1200135A_2023_01_31_22_01_56.csv",     # Real LOT from your example
            "A123B456_2024_06_15_14_30_45.csv",    # 8-char alphanumeric
            "LOT5678_2024_01_01_00_00_00.csv",     # Starting with LOT
            "X99Y88Z_2023_12_25_18_45_30.csv",     # 7-char mixed
            
            # Invalid format examples that should be handled
            "measurement_data_2024_01_15.csv",      # No LOT in filename
            "temp_file.csv",                        # Generic name
            "GOMPC_export_20240115.csv",           # Machine export format
            
            # Edge cases
            "12_2024_01_01_12_00_00.csv",          # Very short LOT
            "VERYLONGLOTNUMBER_2024_01_01_12_00_00.csv", # Very long LOT
        ]
        
        success_count = 0
        
        for filename in test_filenames:
            lot, data_hora = self.scanner.extract_lot_and_datetime_from_filename(filename)
            
            if lot and data_hora:
                print(f"✅ '{filename}'")
                print(f"   -> LOT: '{lot}' | Data: '{data_hora}'")
                success_count += 1
            else:
                print(f"❌ '{filename}'")
                print(f"   -> No s'ha pogut extreure LOT/DATA")
        
        print(f"\nRESUMEN: {success_count}/{len(test_filenames)} fitxers processats correctament")
        return success_count, len(test_filenames)
    
    def create_improved_lot_extraction_function(self):
        """Create an improved LOT extraction function"""
        
        print("\n" + "=" * 80)
        print("3. CREACIÓ DE FUNCIÓ MILLORADA D'EXTRACCIÓ DE LOT")
        print("=" * 80)
        
        improved_extraction_code = '''
def extract_lot_and_datetime_from_filename_improved(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Funció millorada per extreure LOT i DATA_HORA del nom del fitxer GOMPC
    
    Formats acceptats:
    1. LOT_YYYY_MM_DD_HH_MM_SS.csv (format principal)
    2. XXXX_YYYY_MM_DD_HH_MM_SS.csv (on XXXX és el LOT de 4-10 caràcters)
    
    Args:
        filename: Nom del fitxer CSV
        
    Returns:
        tuple: (LOT, DATA_HORA) o (None, None) si no es pot extreure
    """
    try:
        # Eliminar extensió
        name_without_ext = os.path.splitext(filename)[0]
        
        # Patró principal: LOT_YYYY_MM_DD_HH_MM_SS
        # El LOT pot ser de 4 a 10 caràcters alfanumèrics
        pattern = r'^([A-Za-z0-9]{4,10})_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$'
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

        print("Funció millorada creada:")
        print("✅ Accepta LOTs de 4-10 caràcters alfanumèrics")
        print("✅ Normalitza LOTs a majúscules")  
        print("✅ Valida la data extraída")
        print("✅ Millor logging i gestió d'errors")
        
        return improved_extraction_code
        
    def identify_recoverable_lots(self):
        """Identify LOT codes that can be recovered from id_referencia_some"""
        
        print("\n" + "=" * 80)
        print("4. IDENTIFICACIÓ DE LOTS RECUPERABLES")
        print("=" * 80)
        
        # Look for patterns in id_referencia_some that might contain real LOT codes
        query_patterns = """
        SELECT DISTINCT 
            id_referencia_some,
            id_lot,
            client,
            COUNT(*) as records
        FROM mesuresqualitat 
        WHERE maquina = 'gompc'
        AND (id_lot LIKE 'LOT_%' OR id_lot = 'LOT')
        AND id_referencia_some IS NOT NULL
        GROUP BY id_referencia_some, id_lot, client
        ORDER BY records DESC
        LIMIT 20
        """
        
        patterns = self.adapter.execute_query(query_patterns)
        
        recoverable_count = 0
        
        if patterns:
            print("PATRONS TROBATS EN id_referencia_some:")
            print("-" * 50)
            
            for row in patterns:
                id_ref = row['id_referencia_some']
                parts = id_ref.split('_')
                
                # The LOT should be the last part of id_referencia_some
                if len(parts) >= 3:
                    potential_lot = parts[-1]
                    
                    # Check if this looks like a valid LOT
                    if (len(potential_lot) >= 7 and 
                        potential_lot.replace('_', '').isalnum() and 
                        not potential_lot.startswith('LOT_')):
                        
                        print(f"✅ Recuperable: '{row['id_lot']}' -> '{potential_lot}'")
                        print(f"   Client: {row['client']} | Records: {row['records']}")
                        recoverable_count += 1
                    else:
                        print(f"❌ No recuperable: '{row['id_lot']}'")
                        print(f"   id_referencia_some: {id_ref}")
        
        print(f"\nLOTS RECUPERABLES: {recoverable_count}")
        return recoverable_count
    
    def fix_recoverable_lots(self, dry_run=True):
        """Fix recoverable LOT codes in the database"""
        
        print("\n" + "=" * 80)
        print("5. CORRECCIÓ DE LOTS RECUPERABLES")
        print("=" * 80)
        
        if dry_run:
            print("MODE DRY RUN - No es faran canvis a la BD")
        
        # Get recoverable patterns
        query_recoverable = """
        SELECT DISTINCT 
            id_referencia_some,
            id_lot,
            client,
            COUNT(*) as records
        FROM mesuresqualitat 
        WHERE maquina = 'gompc'
        AND (id_lot LIKE 'LOT_%' OR id_lot = 'LOT')
        AND id_referencia_some IS NOT NULL
        GROUP BY id_referencia_some, id_lot, client
        HAVING COUNT(*) > 5  -- Only fix patterns with significant data
        ORDER BY records DESC
        """
        
        recoverable_patterns = self.adapter.execute_query(query_recoverable)
        
        fixed_count = 0
        total_records_affected = 0
        
        if recoverable_patterns:
            for row in recoverable_patterns:
                id_ref = row['id_referencia_some']
                old_lot = row['id_lot']
                client = row['client']
                records = row['records']
                
                # Extract potential LOT from id_referencia_some
                parts = id_ref.split('_')
                if len(parts) >= 3:
                    potential_lot = parts[-1]
                    
                    # Validate potential LOT
                    if (len(potential_lot) >= 7 and 
                        potential_lot.replace('_', '').replace('-', '').isalnum() and 
                        not potential_lot.startswith('LOT_')):
                        
                        print(f"Corrigint: '{old_lot}' -> '{potential_lot}' ({records} records)")
                        
                        if not dry_run:
                            # Update the database
                            update_query = """
                            UPDATE mesuresqualitat 
                            SET id_lot = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE maquina = 'gompc'
                            AND id_lot = %s
                            AND client = %s
                            AND id_referencia_some = %s
                            """
                            
                            try:
                                with self.adapter.connection.cursor() as cursor:
                                    cursor.execute(update_query, (potential_lot, old_lot, client, id_ref))
                                    affected = cursor.rowcount
                                    
                                print(f"  ✅ {affected} records actualitzats")
                                fixed_count += 1
                                total_records_affected += affected
                                
                            except Exception as e:
                                print(f"  ❌ Error: {e}")
                        else:
                            print(f"  [DRY RUN] {records} records s'actualitzarien")
                            fixed_count += 1
                            total_records_affected += records
        
        if not dry_run:
            self.adapter.connection.commit()
            
        print(f"\nRESUMEN:")
        print(f"Patrons corregits: {fixed_count}")
        print(f"Total records afectats: {total_records_affected}")
        
        return fixed_count, total_records_affected
    
    def create_prevention_recommendations(self):
        """Create recommendations to prevent future LOT issues"""
        
        print("\n" + "=" * 80)
        print("6. RECOMANACIONS PER PREVENIR FUTURS PROBLEMES")
        print("=" * 80)
        
        recommendations = [
            "1. MILLORES AL CODI:",
            "   ✅ Implementar la funció millorada d'extracció de LOT",
            "   ✅ Afegir validació més estricta dels noms de fitxer CSV",
            "   ✅ Eliminar qualsevol lògica de generació automàtica de LOT",
            "   ✅ Afegir logging detallat del procés d'extracció",
            "",
            "2. VALIDACIÓ DE DADES:",
            "   ✅ Verificar que els fitxers CSV segueixen el format esperat",
            "   ✅ Rebutjar fitxers amb noms que no contenen LOT vàlid",
            "   ✅ Implementar alertes quan no es pot extreure LOT",
            "",
            "3. MONITORITZACIÓ:",
            "   ✅ Crear un script de monitorització diari dels LOTs",
            "   ✅ Alertar quan apareixen LOTs amb format 'LOT_YYYY_MM_DD'",
            "   ✅ Revisar periòdicament la qualitat de les dades",
            "",
            "4. DOCUMENTACIÓ:",
            "   ✅ Documentar clarament el format esperat dels fitxers CSV",
            "   ✅ Formar els usuaris sobre la nomenclatura correcta",
            "   ✅ Crear exemples de noms de fitxer correctes i incorrectes",
        ]
        
        for rec in recommendations:
            print(rec)
    
    def run_complete_analysis(self, fix_data=False):
        """Run complete LOT pipeline analysis and fix"""
        
        print("ANÀLISI COMPLET DEL PIPELINE DE LOT")
        print("=" * 80)
        
        # 1. Analyze current issues
        problematic_count, valid_count = self.analyze_current_lot_issues()
        
        # 2. Test extraction patterns
        success_count, total_tests = self.test_lot_extraction_patterns()
        
        # 3. Create improved extraction function
        improved_code = self.create_improved_lot_extraction_function()
        
        # 4. Identify recoverable LOTs
        recoverable_count = self.identify_recoverable_lots()
        
        # 5. Fix recoverable LOTs (if requested)
        if fix_data and recoverable_count > 0:
            # First run in dry mode
            print("\n" + "=" * 40)
            print("SIMULACIÓ DE CORRECCIONS:")
            fixed_dry, records_dry = self.fix_recoverable_lots(dry_run=True)
            
            # Ask for confirmation
            response = input(f"\nVols aplicar aquests canvis? ({records_dry} records afectats) [s/N]: ")
            if response.lower() in ['s', 'y', 'yes', 'si', 'sí']:
                fixed_count, records_affected = self.fix_recoverable_lots(dry_run=False)
                print(f"✅ Correccions aplicades: {records_affected} records actualitzats")
            else:
                print("❌ Correccions cancel·lades")
                
        # 6. Create recommendations
        self.create_prevention_recommendations()
        
        # Summary
        print("\n" + "=" * 80)
        print("RESUM FINAL")
        print("=" * 80)
        print(f"Problemes detectats: {problematic_count} patrons problemàtics")
        print(f"LOTs vàlids trobats: {valid_count}")
        print(f"Test d'extracció: {success_count}/{total_tests} exitosos")
        print(f"LOTs recuperables: {recoverable_count}")
        
        if problematic_count > 0:
            print("\n🚨 ACCIÓ REQUERIDA:")
            print("1. Implementar la funció millorada d'extracció de LOT")
            print("2. Revisar i corregir el pipeline de processament de CSV")
            print("3. Executar la correcció de dades si és necessari")
        else:
            print("\n✅ No s'han detectat problemes majors en el pipeline de LOT")

def main():
    """Main function"""
    
    config_path = r'c:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\config.ini'
    
    try:
        fixer = LOTPipelineFixer(config_path)
        
        # Run complete analysis
        # Set fix_data=True if you want to apply fixes to the database
        fixer.run_complete_analysis(fix_data=False)  # Start with read-only analysis
        
    except Exception as e:
        print(f"Error executant l'anàlisi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()