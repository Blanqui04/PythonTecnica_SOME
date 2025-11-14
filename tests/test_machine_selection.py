#!/usr/bin/env python3
"""
Test de selecció de màquines per estudis de capacitat
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
import logging

logging.basicConfig(level=logging.WARNING)


def test_machine_selection():
    """Test selecció de màquines"""
    
    print("\n" + "="*80)
    print("TEST DE SELECCIÓ DE MÀQUINES")
    print("="*80)
    
    # Mostrar màquines disponibles
    machines = MeasurementHistoryService.get_available_machines()
    
    print("\nMàquines disponibles:")
    for key, info in machines.items():
        print(f"\n  [{key}]")
        print(f"    Nom: {info['name']}")
        print(f"    Taules: {', '.join(info['tables'])}")
        print(f"    Descripció: {info['description']}")
    
    # Test amb cada màquina
    test_cases = [
        {
            'machine': 'gompc_projectes',
            'client': 'AUTOLIV',
            'reference': '663962200'
        },
        {
            'machine': 'all',
            'client': 'AUTOLIV',
            'reference': '663962200'
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Test amb màquina: {test['machine']}")
        print(f"{'='*80}")
        
        try:
            service = MeasurementHistoryService(machine=test['machine'])
            print(f"\n[OK] Servei inicialitzat: {service.get_current_machine()}")
            print(f"   Taules utilitzades: {service.measurement_tables}")
            
            # Buscar elements
            elements = service.get_available_elements(
                client=test['client'],
                project_reference=test['reference']
            )
            
            if elements:
                print(f"\n[OK] Trobats {len(elements)} elements")
                # Mostrar primers 3
                for i, el in enumerate(elements[:3], 1):
                    print(f"   {i}. Element: {el['element']} | Property: {el['property']} | Count: {el['count']}")
            else:
                print(f"\n[WARN] Cap element trobat")
            
            service.close()
            
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()


def test_lot_search_by_machine():
    """Test cerca de lots per màquina específica"""
    
    print("\n" + "="*80)
    print("TEST CERCA DE LOTS PER MÀQUINA")
    print("="*80)
    
    test_cases = [
        {
            'machine': 'gompc_projectes',
            'client': 'AUTOLIV',
            'reference': '663962200',
            'lot_partial': 'PRJ1229836'
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Test: {test['machine']} ---")
        print(f"Client: {test['client']}")
        print(f"Referència: {test['reference']}")
        print(f"LOT parcial: {test['lot_partial']}")
        
        try:
            service = MeasurementHistoryService(machine=test['machine'])
            
            # Obtenir tots els lots disponibles
            lots = service.get_available_lots(
                client=test['client'],
                project_reference=test['reference']
            )
            
            print(f"\n[OK] Lots disponibles: {len(lots)}")
            for i, lot in enumerate(lots[:5], 1):
                print(f"   {i}. {lot['id_lot']}: {lot['count']} mesures (última: {lot['last_measurement']})")
            
            # Buscar amb LOT parcial
            if test['lot_partial']:
                elements = service.get_available_elements(
                    client=test['client'],
                    project_reference=test['reference'],
                    batch_lot=test['lot_partial']
                )
                
                print(f"\n[OK] Elements amb LOT '{test['lot_partial']}': {len(elements)}")
                for i, el in enumerate(elements[:3], 1):
                    print(f"   {i}. {el['element']} | {el['property']}: {el['count']} mesures")
            
            service.close()
            
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Executar tots els tests"""
    
    print("="*80)
    print("TESTS DE SELECCIÓ DE MÀQUINES PER ESTUDIS DE CAPACITAT")
    print("="*80)
    
    test_machine_selection()
    test_lot_search_by_machine()
    
    print("\n" + "="*80)
    print("TESTS COMPLETATS")
    print("="*80)


if __name__ == "__main__":
    main()
