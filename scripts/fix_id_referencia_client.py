#!/usr/bin/env python3
"""
Script per corregir les dades de id_referencia_client a la taula mesuresqualitat

El problema: id_referencia_client conté el nom del client en lloc de la referència
La solució: Extreure la referència de id_referencia_some (després del primer "_")

Format de id_referencia_some: Client_ReferènciaClient_LOT
Exemple: "ADAPTER TRW_ADAPTERS ACR_LOT_2025_06_04_01_38_11"
         Client: "ADAPTER TRW"
         Referència: "ADAPTERS ACR" (això és el que ha d'anar a id_referencia_client)
         LOT: "LOT_2025_06_04_01_38_11"
"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from database.quality_measurement_adapter import QualityMeasurementDBAdapter
from services.network_scanner import NetworkScanner
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_client_reference(id_referencia_some):
    """
    Extreu la referència del client de id_referencia_some
    
    Format esperat: Client_ReferènciaClient_LOT
    Exemple: "ADAPTER TRW_ADAPTERS ACR_LOT_2025_06_04_01_38_11"
    Retorna: "ADAPTERS ACR"
    """
    if not id_referencia_some:
        return None
    
    parts = id_referencia_some.split('_')
    
    if len(parts) < 3:
        logger.warning(f"Format no esperat en id_referencia_some: {id_referencia_some}")
        return None
    
    # El primer part és el client, el segon és la referència que busquem
    # Però pot ser que la referència tingui múltiples parts separades per "_"
    # Així que agafem tot després del primer "_" i abans del "_LOT"
    
    # Trobar l'índex de "LOT"
    lot_index = -1
    for i, part in enumerate(parts):
        if part.startswith('LOT'):
            lot_index = i
            break
    
    if lot_index <= 1:
        logger.warning(f"No s'ha trobat LOT o format incorrecte: {id_referencia_some}")
        return None
    
    # La referència són les parts entre l'índex 1 i lot_index
    reference_parts = parts[1:lot_index]
    client_reference = '_'.join(reference_parts)
    
    return client_reference

def needs_correction(id_referencia_some, id_referencia_client, client):
    """
    Determina si un registre necessita correció
    
    Un registre necessita correció si:
    1. id_referencia_client és igual al nom del client (en lloc de la referència)
    2. La referència extreta de id_referencia_some és diferent de id_referencia_client
    """
    if not id_referencia_some or not id_referencia_client or not client:
        return False
    
    # Si id_referencia_client és igual al client, probablement està malament
    if id_referencia_client == client:
        return True
    
    # També comprovar si la referència extreta és diferent de l'actual
    correct_reference = extract_client_reference(id_referencia_some)
    if correct_reference and correct_reference != id_referencia_client:
        return True
    
    return False

def fix_id_referencia_client():
    """
    Funció principal per corregir id_referencia_client
    """
    # Carregar configuració de la base de dades
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
        # Obtenir tots els registres que necessiten correció
        logger.info("Obtenint registres que necessiten correció...")
        
        query = """
        SELECT id_referencia_some, id_element, id_referencia_client, client
        FROM mesuresqualitat
        WHERE id_referencia_some IS NOT NULL
        AND id_referencia_client IS NOT NULL
        AND client IS NOT NULL
        ORDER BY id_referencia_some, id_element
        """
        
        results = adapter.execute_query(query)
        logger.info(f"Trobats {len(results)} registres per processar")
        
        # Processar registres en lots
        batch_size = 1000
        total_updated = 0
        total_errors = 0
        total_skipped = 0
        
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            logger.info(f"Processant lot {i//batch_size + 1} ({len(batch)} registres)...")
            
            for record in batch:
                id_referencia_some, id_element, current_id_referencia_client, client = record
                
                # Comprovar si necessita correció
                if not needs_correction(id_referencia_some, current_id_referencia_client, client):
                    total_skipped += 1
                    continue
                
                # Extreure la referència correcta
                correct_reference = extract_client_reference(id_referencia_some)
                
                if correct_reference and correct_reference != current_id_referencia_client:
                    # Actualitzar el registre
                    try:
                        update_query = """
                        UPDATE mesuresqualitat 
                        SET id_referencia_client = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id_referencia_some = %s AND id_element = %s
                        """
                        
                        adapter.execute_query(update_query, (correct_reference, id_referencia_some, id_element))
                        total_updated += 1
                        
                        if total_updated % 100 == 0:
                            logger.info(f"Actualitzats {total_updated} registres...")
                            
                    except Exception as e:
                        logger.error(f"Error actualitzant registre {id_referencia_some}/{id_element}: {e}")
                        total_errors += 1
        
        logger.info(f"Procés completat:")
        logger.info(f"  - Total registres processats: {len(results)}")
        logger.info(f"  - Registres actualitzats: {total_updated}")
        logger.info(f"  - Registres omesos (ja correctes): {total_skipped}")
        logger.info(f"  - Errors: {total_errors}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error general durant la correció: {e}")
        return False
    
    finally:
        if adapter.connection:
            adapter.connection.close()

def preview_changes():
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
        # Obtenir una mostra diversa dels registres, prioritzant els que necessiten correció
        query = """
        SELECT id_referencia_some, id_referencia_client, client
        FROM mesuresqualitat
        WHERE id_referencia_some IS NOT NULL
        AND id_referencia_client IS NOT NULL
        AND client IS NOT NULL
        AND id_referencia_client = client
        LIMIT 15
        """
        problematic_results = adapter.execute_query(query)
        
        # També obtenir alguns registres que ja són correctes per comparar
        query2 = """
        SELECT DISTINCT id_referencia_some, id_referencia_client, client
        FROM mesuresqualitat
        WHERE id_referencia_some IS NOT NULL
        AND id_referencia_client IS NOT NULL
        AND client IS NOT NULL
        AND id_referencia_client != client
        LIMIT 15
        """
        correct_results = adapter.execute_query(query2)
        
        # Combinar els resultats
        results = problematic_results + correct_results
        
        results = adapter.execute_query(query)
        
        print("\n" + "="*80)
        print("PREVISUALITZACIÓ DELS CANVIS")
        print("="*80)
        
        needs_change = 0
        already_correct = 0
        
        for record in results:
            id_referencia_some, current_id_referencia_client, client = record
            correct_reference = extract_client_reference(id_referencia_some)
            
            print(f"\nid_referencia_some: {id_referencia_some}")
            print(f"client: {client}")
            print(f"id_referencia_client (actual): {current_id_referencia_client}")
            print(f"id_referencia_client (correcte): {correct_reference}")
            
            if needs_correction(id_referencia_some, current_id_referencia_client, client):
                print(">>> NECESSITA CANVI <<<")
                needs_change += 1
            else:
                print(">>> JA ÉS CORRECTE <<<")
                already_correct += 1
            print("-" * 50)
        
        print(f"\nRESUM:")
        print(f"- Registres que necessiten canvi: {needs_change}")
        print(f"- Registres ja correctes: {already_correct}")
        
    finally:
        if adapter.connection:
            adapter.connection.close()

if __name__ == "__main__":
    print("Script de Correció de id_referencia_client")
    print("==========================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_changes()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("\nINICIANT CORRECIÓ DE DADES...")
        fix_id_referencia_client()
    else:
        print("\nÚs:")
        print("  python fix_id_referencia_client.py --preview    # Mostrar previsualització")
        print("  python fix_id_referencia_client.py --fix       # Executar la correció")