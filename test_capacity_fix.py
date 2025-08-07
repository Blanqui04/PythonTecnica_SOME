#!/usr/bin/env python3
"""
Script de test per verificar que l'arreglo de l'estudi de capacitats funciona
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.measurement_history_service import MeasurementHistoryService

def test_measurement_service():
    """Test del servei de mesures"""
    try:
        print("=== TEST SERVEI DE MESURES ===")
        
        service = MeasurementHistoryService()
        print("✓ Servei inicialitzat correctament")
        
        # Test 1: Obtenir elements disponibles
        print("\n1. Provant obtenir elements disponibles...")
        elements = service.get_available_elements("ZF", "A027Y915")
        print(f"✓ Trobats {len(elements)} elements")
        
        if elements:
            print("Primer element trobat:")
            first_element = elements[0]
            print(f"   - Element: {first_element['element']}")
            print(f"   - Pieza: {first_element['pieza']}")
            print(f"   - Datum: {first_element['datum']}")
            print(f"   - Property: {first_element['property']}")
            print(f"   - Count: {first_element['count']}")
            
            # Test 2: Construir ID de l'element i obtenir mesures
            element_id = f"{first_element['element']}|{first_element['pieza']}|{first_element['datum']}|{first_element['property']}"
            print(f"\n2. Provant obtenir mesures per element ID: {element_id}")
            
            measurements = service.get_element_measurement_history("ZF", "A027Y915", element_id, limit=5)
            print(f"✓ Trobades {len(measurements)} mesures")
            
            if measurements:
                print("Primera mesura trobada:")
                first_measurement = measurements[0]
                print(f"   - Valor: {first_measurement['valor_mesura']}")
                print(f"   - Data: {first_measurement['data_hora']}")
                print(f"   - Nominal: {first_measurement['nominal']}")
                print(f"   - Tol_neg: {first_measurement['tol_neg']}")
                print(f"   - Tol_pos: {first_measurement['tol_pos']}")
                print(f"   - Cavitat: {first_measurement.get('cavitat', 'N/A')}")
            else:
                print("⚠️ Cap mesura trobada per aquest element")
        else:
            print("⚠️ Cap element trobat")
        
        service.close()
        print("\n✓ Test completat exitosament!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durant el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_measurement_service()
    sys.exit(0 if success else 1)
