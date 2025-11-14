#!/usr/bin/env python3
"""
Test script per verificar la cerca flexible de referències i lots
"""

import sys
import os
# Afegir el directori root del projecte al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_flexible_reference_search():
    """Test cerca flexible de referències"""
    
    print("="*80)
    print("TEST 1: CERCA FLEXIBLE DE REFERÈNCIES")
    print("="*80)
    
    # Inicialitzar servei (carrega configuració automàticament)
    service = MeasurementHistoryService()
    
    # Test cases amb referències reals que existeixen
    test_cases = [
        {
            'client': 'AUTOLIV',
            'reference': '663962200',
            'description': 'Referència 663962200 (hauria de trobar 663962200A)'
        },
        {
            'client': 'AUTOLIV',
            'reference': '665220400',
            'description': 'Referència 665220400 (format 002_6652204_002)'
        },
        {
            'client': 'AUTOLIV',
            'reference': '665220500',
            'description': 'Referència 665220500 (format 002_6652205_002)'
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Test: {test['description']} ---")
        print(f"Client: {test['client']}, Referència: {test['reference']}")
        
        try:
            # Obtenir elements disponibles
            elements = service.get_available_elements(
                client=test['client'],
                project_reference=test['reference']
            )
            
            if elements:
                print(f"[OK] Trobats {len(elements)} elements")
                print(f"   Primer element: {elements[0]['element']}")
                print(f"   Referencia trobada: {elements[0].get('ref_client', 'N/A')}")
            else:
                print(f"[WARN] Cap element trobat")
                
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    service.close()


def test_flexible_lot_search():
    """Test cerca flexible de lots"""
    
    print("="*80)
    print("TEST 2: CERCA FLEXIBLE DE LOTS")
    print("="*80)
    
    # Inicialitzar servei
    service = MeasurementHistoryService()
    
    # Test cases amb lots que poden variar
    test_cases = [
        {
            'client': 'AUTOLIV',
            'reference': '663962200',
            'lot_partial': None,  # Sense filtrar per lot
            'description': 'Tots els lots disponibles per 663962200'
        },
        {
            'client': 'AUTOLIV',
            'reference': '663962200',
            'lot_partial': '2024',  # Buscar lots que continguin "2024"
            'description': 'Cerca per any 2024 en el lot'
        },
        {
            'client': 'AUTOLIV',
            'reference': '663962200B',
            'lot_partial': None,
            'description': 'Tots els lots per 663962200B'
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Test: {test['description']} ---")
        print(f"Client: {test['client']}, Referència: {test['reference']}, LOT parcial: {test['lot_partial']}")
        
        try:
            # Primer obtenir tots els lots disponibles
            all_lots = service.get_available_lots(
                client=test['client'],
                project_reference=test['reference']
            )
            
            print(f"Tots els lots disponibles: {len(all_lots)}")
            if all_lots:
                for i, lot in enumerate(all_lots[:5], 1):  # Mostrar només els 5 primers
                    print(f"   {i}. {lot['id_lot']} - {lot['count']} mesures - Última: {lot['last_measurement']}")
            
            # Ara buscar amb el lot parcial (si està definit)
            if test['lot_partial']:
                elements = service.get_available_elements(
                    client=test['client'],
                    project_reference=test['reference'],
                    batch_lot=test['lot_partial']
                )
                
                if elements:
                    print(f"[OK] Amb LOT '{test['lot_partial']}': Trobats {len(elements)} elements")
                else:
                    print(f"[WARN] Cap element trobat amb LOT '{test['lot_partial']}'")
                    
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    service.close()


def test_element_measurements():
    """Test obtenir mesures d'elements amb cerca flexible"""
    
    print("="*80)
    print("TEST 3: OBTENIR MESURES D'ELEMENTS AMB CERCA FLEXIBLE")
    print("="*80)
    
    # Inicialitzar servei
    service = MeasurementHistoryService()
    
    test_case = {
        'client': 'AUTOLIV',
        'reference': '663962200',
        'element': None,  # Agafarem el primer element disponible
        'lot_partial': None  # Sense filtrar per lot primer
    }
    
    print(f"Client: {test_case['client']}")
    print(f"Referència: {test_case['reference']}")
    print(f"Element: {test_case['element']}")
    print(f"LOT parcial: {test_case['lot_partial']}")
    
    try:
        # Primer obtenir elements disponibles
        elements = service.get_available_elements(
            client=test_case['client'],
            project_reference=test_case['reference'],
            batch_lot=test_case['lot_partial']
        )
        
        if elements:
            print(f"\n[OK] Elements disponibles: {len(elements)}")
            
            # Agafar el primer element
            first_element = elements[0]
            print(f"\nProvant amb primer element:")
            print(f"  - Element: {first_element['element']}")
            print(f"  - Pieza: {first_element['pieza']}")
            print(f"  - Datum: {first_element['datum']}")
            print(f"  - Property: {first_element['property']}")
            
            # Obtenir mesures
            measurements = service.get_element_measurements(
                client=test_case['client'],
                project_reference=test_case['reference'],
                element_name=first_element['element'],
                property_name=first_element['property'],
                batch_lot=test_case['lot_partial'],
                limit=10
            )
            
            if measurements:
                print(f"\n[OK] Mesures trobades: {len(measurements)}")
                for i, m in enumerate(measurements[:3], 1):
                    print(f"   {i}. Actual: {m.get('actual', 'N/A')}, LOT: {m.get('id_lot', 'N/A')}")
            else:
                print(f"[WARN] Cap mesura trobada")
        else:
            print(f"[WARN] Cap element disponible")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    service.close()


def main():
    """Executar tots els tests"""
    
    print("="*80)
    print("TESTS DE CERCA FLEXIBLE DE REFERÈNCIES I LOTS")
    print("="*80)
    
    try:
        test_flexible_reference_search()
        test_flexible_lot_search()
        test_element_measurements()
        
        print("\n" + "="*80)
        print("TESTS COMPLETATS")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error executant tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
