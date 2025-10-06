#!/usr/bin/env python3
"""
Script per corregir els LOTs a la taula mesuresqualitat

El problema: Molts registres tenen id_lot amb format "LOT_data_hora" 
en comptes d'un codi alfanumèric de LOT real (7-10 dígits)

La solució: 
1. Identificar registres amb LOT problemàtic (format LOT_data_hora)
2. Generar un LOT alfanumèric coherent basat en client, referència i data
3. Actualitzar tant id_lot com id_referencia_some
"""

import sys
import os
import hashlib
import re
from datetime import datetime
sys.path.append(os.path.join(os.getcwd(), 'src'))

from database.quality_measurement_adapter import QualityMeasurementDBAdapter
from services.network_scanner import NetworkScanner
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_valid_lot_code(lot_string):
    """
    Verifica si un codi de LOT és vàlid (7 dígits alfanumèrics)
    
    Args:
        lot_string: String a verificar
        
    Returns:
        bool: True si és un LOT vàlid
    """
    if not lot_string or lot_string in ['nan', 'null', 'NULL', '']:
        return False
    
    # Un LOT vàlid ha de ser exactament 7 caràcters alfanumèrics
    return bool(re.match(r'^[A-Za-z0-9]{7}$', str(lot_string)))

def generate_lot_code(client, ref_client, original_lot, existing_lots=None):
    """
    Genera un codi de LOT alfanumèric de 7 dígits
    
    Args:
        client: Nom del client
        ref_client: Referència del client  
        original_lot: LOT original (pot ser data, text, etc.)
        existing_lots: Set de LOTs existents per evitar duplicats
        
    Returns:
        str: Codi de LOT alfanumèric de exactament 7 caràcters
    """
    # Crear un hash basat en client + referència + lot original per garantir consistència
    hash_input = f"{client}_{ref_client}_{original_lot}".replace(' ', '_').upper()
    hash_obj = hashlib.md5(hash_input.encode())
    hash_hex = hash_obj.hexdigest().upper()
    
    # Generar prefix de 3 caràcters basat en client
    client_clean = re.sub(r'[^A-Za-z0-9]', '', str(client))[:3].upper().ljust(3, 'X')
    
    # Usar 4 caràcters del hash per completar els 7 dígits
    hash_part = hash_hex[:4]
    
    # Format del LOT: [3 chars del client][4 chars del hash] = 7 caràcters
    lot_code = f"{client_clean}{hash_part}"
    
    # Si el LOT ja existeix, modificar fins trobar un únic
    if existing_lots and lot_code in existing_lots:
        counter = 1
        base_code = lot_code[:6]  # Primers 6 caràcters
        while f"{base_code}{counter:X}" in existing_lots:  # Últim caràcter hexadecimal
            counter += 1
            if counter > 15:  # Si arribem al límit hex (F), canviar estratègia
                # Usar més del hash
                hash_part = hash_hex[counter-16:counter-12]
                lot_code = f"{client_clean}{hash_part}"
                break
        else:
            lot_code = f"{base_code}{counter:X}"
    
    return lot_code

def extract_date_from_lot_string(lot_string):
    """
    Extreu la data d'un string LOT_data_hora
    
    Args:
        lot_string: String amb format LOT_2024_11_14_12_56_00
        
    Returns:
        tuple: (year, month, day, hour, minute, second) o None si no es pot parsear
    """
    # Patró per LOT_YYYY_MM_DD_HH_MM_SS
    pattern = r'LOT_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})'
    match = re.match(pattern, lot_string)
    
    if match:
        return tuple(map(int, match.groups()))
    return None

def fix_lot_codes():
    """
    Funció principal per corregir els codis de LOT
    """
    scanner = NetworkScanner()
    db_config = scanner.load_db_config()
    
    if not db_config:
        logger.error("No s'ha pogut carregar la configuració de la base de dades")
        return False
    
    adapter = QualityMeasurementDBAdapter(db_config)
    
    if not adapter.connect():
        logger.error("No s'ha pogut connectar a la base de dades")
        return False
    
    try:
        # 1. Obtenir tots els LOTs existents que són correctes (7 dígits alfanumèrics)
        logger.info("Obtenint LOTs existents correctes...")
        existing_lots_query = """
        SELECT DISTINCT id_lot
        FROM mesuresqualitat
        WHERE id_lot IS NOT NULL
        AND id_lot ~ '^[A-Za-z0-9]{7}$'
        """
        
        existing_results = adapter.execute_query(existing_lots_query)
        existing_lots = set(row[0] for row in existing_results)
        logger.info(f"Trobats {len(existing_lots)} LOTs correctes existents (7 dígits)")
        
        # 2. Obtenir registres problemàtics (tots els que NO siguin exactament 7 dígits alfanumèrics)
        logger.info("Obtenint registres amb LOTs problemàtics...")
        
        problematic_query = """
        SELECT client, id_referencia_client, id_lot, 
               COUNT(*) as count,
               MIN(id_referencia_some) as sample_ref_some,
               MIN(id_element) as sample_element
        FROM mesuresqualitat
        WHERE (id_lot IS NULL 
               OR id_lot = 'nan' 
               OR id_lot = 'PROVA' 
               OR id_lot = 'PPAP'
               OR id_lot = 'prova'
               OR id_lot LIKE 'LOT_%'
               OR id_lot !~ '^[A-Za-z0-9]{7}$')
        AND client IS NOT NULL
        AND client != 'nan'
        AND id_referencia_client IS NOT NULL
        AND id_referencia_client != 'nan'
        GROUP BY client, id_referencia_client, id_lot
        ORDER BY count DESC, client, id_referencia_client
        """
        
        problematic_results = adapter.execute_query(problematic_query)
        logger.info(f"Trobats {len(problematic_results)} grups de LOTs problemàtics")
        
        # 3. Processar cada grup i generar LOTs correctes
        total_updated = 0
        total_errors = 0
        lot_mapping = {}  # Per mantenir consistència
        
        for group in problematic_results:
            client, ref_client, old_lot, count, sample_ref_some, sample_element = group
            
            # Saltar si ja és un LOT vàlid de 7 dígits (per si de cas)
            if is_valid_lot_code(old_lot):
                logger.info(f"Saltant LOT ja vàlid: {old_lot}")
                continue
            
            # Generar el nou LOT
            new_lot = generate_lot_code(client, ref_client, old_lot or "UNKNOWN", existing_lots)
            existing_lots.add(new_lot)  # Afegir per evitar duplicats
            lot_mapping[str(old_lot)] = new_lot
            
            logger.info(f"Client: {client}, Ref: {ref_client}")
            logger.info(f"  LOT antic: '{old_lot}'")
            logger.info(f"  LOT nou: {new_lot}")
            logger.info(f"  Registres afectats: {count}")
            
            try:
                # 4. Actualitzar id_lot (gestionar NULLs correctament)
                if old_lot is None or str(old_lot).lower() in ['nan', 'null', '']:
                    update_lot_query = """
                    UPDATE mesuresqualitat 
                    SET id_lot = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE client = %s 
                    AND id_referencia_client = %s 
                    AND (id_lot IS NULL OR id_lot = 'nan')
                    """
                    adapter.execute_query(update_lot_query, (new_lot, client, ref_client))
                else:
                    update_lot_query = """
                    UPDATE mesuresqualitat 
                    SET id_lot = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE client = %s 
                    AND id_referencia_client = %s 
                    AND id_lot = %s
                    """
                    adapter.execute_query(update_lot_query, (new_lot, client, ref_client, old_lot))
                
                # 5. Actualitzar id_referencia_some (només si conté el lot problemàtic)
                if old_lot and str(old_lot) != 'nan' and len(str(old_lot)) > 3:
                    update_ref_some_query = """
                    UPDATE mesuresqualitat 
                    SET id_referencia_some = REPLACE(id_referencia_some, %s, %s),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE client = %s 
                    AND id_referencia_client = %s 
                    AND id_lot = %s
                    AND id_referencia_some LIKE %s
                    """
                    like_pattern = f"%{old_lot}%"
                    adapter.execute_query(update_ref_some_query, (old_lot, new_lot, client, ref_client, new_lot, like_pattern))
                
                total_updated += count
                logger.info(f"  ✅ Actualitzat correctament")
                
            except Exception as e:
                logger.error(f"  ❌ Error actualitzant: {e}")
                total_errors += count
            
            print("-" * 60)
        
        logger.info(f"Procés completat:")
        logger.info(f"  - Total registres actualitzats: {total_updated}")
        logger.info(f"  - Errors: {total_errors}")
        logger.info(f"  - LOTs generats: {len(lot_mapping)}")
        
        # Mostrar el mapatge de LOTs
        print("\n" + "="*80)
        print("MAPATGE DE LOTS")
        print("="*80)
        for old_lot, new_lot in lot_mapping.items():
            print(f"{old_lot} -> {new_lot}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error general durant la correció: {e}")
        return False
    
    finally:
        if adapter.connection:
            adapter.connection.close()

def preview_lot_fixes():
    """
    Mostra una previsualització dels canvis que es farien
    """
    scanner = NetworkScanner()
    db_config = scanner.load_db_config()
    
    if not db_config:
        logger.error("No s'ha pogut carregar la configuració de la base de dades")
        return
    
    adapter = QualityMeasurementDBAdapter(db_config)
    
    if not adapter.connect():
        logger.error("No s'ha pogut connectar a la base de dades")
        return
    
    try:
        # Obtenir mostra de registres problemàtics (tots els formats invàlids)
        query = """
        SELECT client, id_referencia_client, id_lot, 
               COUNT(*) as count,
               MIN(id_referencia_some) as sample_ref_some
        FROM mesuresqualitat
        WHERE (id_lot IS NULL 
               OR id_lot = 'nan' 
               OR id_lot = 'PROVA' 
               OR id_lot = 'PPAP'
               OR id_lot = 'prova'
               OR id_lot LIKE 'LOT_%'
               OR id_lot !~ '^[A-Za-z0-9]{7}$')
        AND client IS NOT NULL
        AND client != 'nan'
        AND id_referencia_client IS NOT NULL
        AND id_referencia_client != 'nan'
        GROUP BY client, id_referencia_client, id_lot
        ORDER BY count DESC
        LIMIT 15
        """
        
        results = adapter.execute_query(query)
        
        print("\n" + "="*80)
        print("PREVISUALITZACIÓ DELS CANVIS DE LOT")
        print("="*80)
        
        existing_lots = set()
        
        for record in results:
            client, ref_client, old_lot, count, sample_ref_some = record
            
            # Saltar LOTs ja vàlids
            if is_valid_lot_code(old_lot):
                continue
                
            new_lot = generate_lot_code(client, ref_client, old_lot or "UNKNOWN", existing_lots)
            existing_lots.add(new_lot)
            
            print(f"\nClient: {client}")
            print(f"Referència: {ref_client}")
            print(f"LOT actual: '{old_lot}' ({'NULL/nan' if not old_lot or str(old_lot).lower() in ['nan', 'null'] else 'problemàtic'})")
            print(f"LOT nou: {new_lot} (7 dígits alfanumèrics)")
            print(f"Registres afectats: {count}")
            print(f"id_referencia_some mostra: {sample_ref_some}")
            print("-" * 60)
        
    finally:
        if adapter.connection:
            adapter.connection.close()

if __name__ == "__main__":
    print("Script de Correció de Codis de LOT")
    print("==================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_lot_fixes()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("\nINICIANT CORRECIÓ DE CODIS DE LOT...")
        fix_lot_codes()
    else:
        print("\nÚs:")
        print("  python fix_lot_codes.py --preview    # Mostrar previsualització")
        print("  python fix_lot_codes.py --fix       # Executar la correció")