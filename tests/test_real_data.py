#!/usr/bin/env python3
"""
Test amb dades reals que existeixen a la BD
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
import logging

logging.basicConfig(level=logging.WARNING)  # Reduir logs
logger = logging.getLogger(__name__)


def test_with_real_lots():
    """Test amb LOTs reals d'AUTOLIV"""
    
    print("\n" + "="*80)
    print("TEST AMB LOTS REALS D'AUTOLIV")
    print("="*80)
    
    service = MeasurementHistoryService()
    
    # Test amb LOTs reals que sabem que existeixen
    test_cases = [
        {
            'client': 'AUTOLIV',
            'lot_partial': 'PRJ1235461A',
            'description': 'LOT complet PRJ1235461A'
        },
        {
            'client': 'AUTOLIV',
            'lot_partial': 'PRJ123',  # Només part del LOT
            'description': 'Part del LOT: PRJ123 (hauria de trobar PRJ1235461A, PRJ1229447A, etc.)'
        },
        {
            'client': 'AUTOLIV',
            'lot_partial': '1235',  # Part numèrica
            'description': 'Part numèrica: 1235'
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Test: {test['description']} ---")
        print(f"Client: {test['client']}, LOT parcial: {test['lot_partial']}")
        
        try:
            # Buscar elements amb cerca flexible de LOT
            # Com que id_referencia_client és NULL, passem una cadena buida o qualsevol
            elements = service.get_available_elements(
                client=test['client'],
                project_reference='',  # Buit perquè no hi ha referències
                batch_lot=test['lot_partial']
            )
            
            if elements:
                print(f"✅ Trobats {len(elements)} elements")
                # Mostrar els primers 5 elements
                for i, el in enumerate(elements[:5], 1):
                    print(f"   {i}. Element: {el['element']}, Property: {el['property']}, Count: {el['count']}")
            else:
                print(f"⚠️  Cap element trobat")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    service.close()


def test_get_measurements_with_lot():
    """Test obtenir mesures amb cerca flexible de LOT"""
    
    print("\n" + "="*80)
    print("TEST OBTENIR MESURES AMB LOT FLEXIBLE")
    print("="*80)
    
    service = MeasurementHistoryService()
    
    try:
        # Primer obtenir elements disponibles
        print("\n1. Obtenint elements disponibles per LOT 'PRJ123'...")
        elements = service.get_available_elements(
            client='AUTOLIV',
            project_reference='',
            batch_lot='PRJ123'
        )
        
        if elements:
            print(f"✅ Trobats {len(elements)} elements")
            
            # Agafar el primer element
            first_element = elements[0]
            print(f"\n2. Provant amb primer element:")
            print(f"   - Element: {first_element['element']}")
            print(f"   - Property: {first_element['property']}")
            
            # Obtenir mesures
            measurements = service.get_element_measurements(
                client='AUTOLIV',
                project_reference='',
                element_name=first_element['element'],
                property_name=first_element['property'],
                batch_lot='PRJ123',
                limit=10
            )
            
            if measurements:
                print(f"\n✅ Mesures trobades: {len(measurements)}")
                for i, m in enumerate(measurements[:3], 1):
                    print(f"   {i}. Actual: {m.get('actual', 'N/A')}, LOT: {m.get('id_lot', 'N/A')}")
            else:
                print(f"⚠️  Cap mesura trobada")
        else:
            print(f"⚠️  Cap element disponible")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    service.close()


def main():
    """Executar tests"""
    
    print("="*80)
    print("TESTS AMB DADES REALS DE LA BD")
    print("="*80)
    
    test_with_real_lots()
    test_get_measurements_with_lot()
    
    print("\n" + "="*80)
    print("TESTS COMPLETATS")
    print("="*80)


if __name__ == "__main__":
    main()
