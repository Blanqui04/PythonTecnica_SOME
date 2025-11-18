"""
Test del nou sistema de consulta a 1000_SQB_qualitat
Verifica que les taules específiques per màquina funcionen correctament
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.measurement_history_service import MeasurementHistoryService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_new_system():
    """Test del nou sistema amb schema 1000_SQB_qualitat"""
    
    print("\n" + "="*80)
    print("TEST NOU SISTEMA - Schema 1000_SQB_qualitat")
    print("="*80)
    
    # Test 1: Inicialització amb mesures_gompc_projectes (per defecte)
    print("\n[TEST 1] Inicialització amb mesures_gompc_projectes")
    print("-" * 80)
    try:
        service = MeasurementHistoryService(machine='gompc_projectes')
        print(f"✅ Servei inicialitzat correctament")
        print(f"   Màquina: {service.machine_name}")
        print(f"   Schema: {service.schema}")
        print(f"   Taules: {service.table_keys}")
        service.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Test amb client i referència reals
    print("\n[TEST 2] Consulta d'elements disponibles")
    print("-" * 80)
    print("Escull una opció:")
    print("1. AUTOLIV - 665220400")
    print("2. BROSE - E00104-102")
    print("3. ZF - A027Y915")
    print("4. Client personalitzat")
    
    choice = input("\nOpció (1-4): ").strip()
    
    if choice == '1':
        client = "AUTOLIV"
        reference = "665220400"
    elif choice == '2':
        client = "BROSE"
        reference = "E00104-102"
    elif choice == '3':
        client = "ZF"
        reference = "A027Y915"
    elif choice == '4':
        client = input("Client: ").strip()
        reference = input("Referència: ").strip()
    else:
        print("Opció no vàlida, usant AUTOLIV - 665220400")
        client = "AUTOLIV"
        reference = "665220400"
    
    try:
        service = MeasurementHistoryService(machine='gompc_projectes')
        
        print(f"\n🔍 Cercant elements per {client} / {reference}...")
        elements = service.get_available_elements(
            client=client,
            project_reference=reference
        )
        
        if elements:
            print(f"\n✅ Trobats {len(elements)} elements:")
            for i, elem in enumerate(elements[:10], 1):  # Mostrar primers 10
                print(f"   {i}. {elem['element']} (Ref: {elem['ref_client']}, Count: {elem['count']})")
            
            if len(elements) > 10:
                print(f"   ... i {len(elements) - 10} més")
        else:
            print(f"\n⚠️ No s'han trobat elements per {client} / {reference}")
            print("   Pot ser que no hi hagi dades a mesures_gompc_projectes")
            print("   O que la referència no existeixi a la taula")
        
        service.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Obtenir LOTs distints
    if elements:
        print("\n[TEST 3] Obtenir LOTs distints")
        print("-" * 80)
        try:
            service = MeasurementHistoryService(machine='gompc_projectes')
            
            lots = service.get_distinct_lots(
                client=client,
                project_reference=reference
            )
            
            if lots:
                print(f"✅ Trobats {len(lots)} LOTs:")
                for i, lot in enumerate(lots[:5], 1):  # Mostrar primers 5
                    print(f"   {i}. {lot}")
                if len(lots) > 5:
                    print(f"   ... i {len(lots) - 5} més")
            else:
                print("⚠️ No s'han trobat LOTs")
            
            service.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 4: Obtenir mesures d'un element específic
    if elements:
        print("\n[TEST 4] Obtenir mesures d'un element")
        print("-" * 80)
        
        # Agafar primer element
        test_element = elements[0]['element']
        print(f"Element de test: {test_element}")
        
        try:
            service = MeasurementHistoryService(machine='gompc_projectes')
            
            measurements = service.get_element_measurements(
                client=client,
                project_reference=reference,
                element_name=test_element,
                limit=10
            )
            
            if measurements:
                print(f"✅ Trobades {len(measurements)} mesures:")
                for i, meas in enumerate(measurements[:5], 1):
                    print(f"   {i}. Actual: {meas['actual']}, Nominal: {meas['nominal']}, "
                          f"LOT: {meas['id_lot']}, Data: {meas['data_hora']}")
                if len(measurements) > 5:
                    print(f"   ... i {len(measurements) - 5} més")
            else:
                print("⚠️ No s'han trobat mesures")
            
            service.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 5: Test amb totes les màquines
    print("\n[TEST 5] Test amb totes les màquines (machine='all')")
    print("-" * 80)
    try:
        service = MeasurementHistoryService(machine='all')
        print(f"✅ Servei amb totes les màquines")
        print(f"   Taules: {service.table_keys}")
        
        elements_all = service.get_available_elements(
            client=client,
            project_reference=reference
        )
        print(f"   Elements trobats: {len(elements_all)}")
        
        service.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETAT")
    print("="*80)
    return True


if __name__ == "__main__":
    success = test_new_system()
    sys.exit(0 if success else 1)
