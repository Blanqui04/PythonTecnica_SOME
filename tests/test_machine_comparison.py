#!/usr/bin/env python3
"""
Test comparatiu entre màquines per verificar diferències
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
import logging

logging.basicConfig(level=logging.WARNING)


def test_machine_comparison():
    """Compara resultats entre diferents màquines"""
    
    print("\n" + "="*80)
    print("TEST COMPARATIU ENTRE MÀQUINES")
    print("="*80)
    
    # Test amb diferents clients i referències
    test_cases = [
        {
            'name': 'AUTOLIV 663962200',
            'client': 'AUTOLIV',
            'reference': '663962200',
            'expected': 'Hauria d\'estar només a GOMPC Projectes'
        },
        {
            'name': 'AUTOLIV 665220400',
            'client': 'AUTOLIV',
            'reference': '665220400',
            'expected': 'Hauria d\'estar només a GOMPC Projectes'
        }
    ]
    
    machines_to_test = ['gompc_projectes', 'gompc_nou', 'all']
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"Expected: {test['expected']}")
        print(f"{'='*80}")
        
        results = {}
        
        for machine in machines_to_test:
            try:
                service = MeasurementHistoryService(machine=machine)
                elements = service.get_available_elements(
                    client=test['client'],
                    project_reference=test['reference']
                )
                
                results[machine] = {
                    'count': len(elements),
                    'machine_name': service.get_current_machine(),
                    'tables': service.measurement_tables
                }
                
                service.close()
                
            except Exception as e:
                results[machine] = {
                    'error': str(e)
                }
        
        # Mostrar resultats comparatius
        print(f"\nResultats:")
        for machine, result in results.items():
            if 'error' in result:
                print(f"  ❌ {machine}: ERROR - {result['error']}")
            else:
                print(f"  ✓ {machine} ({result['machine_name']}): {result['count']} elements")
                print(f"     Taules: {', '.join(result['tables'])}")
        
        # Verificar consistència
        if results.get('all', {}).get('count', 0) >= results.get('gompc_projectes', {}).get('count', 0):
            print(f"\n  ✅ Consistència OK: 'all' >= 'gompc_projectes'")
        else:
            print(f"\n  ⚠️  Inconsistència: 'all' < 'gompc_projectes'")


def test_machine_specific_data():
    """Test que verifica dades específiques de cada màquina"""
    
    print("\n" + "="*80)
    print("TEST DADES ESPECÍFIQUES PER MÀQUINA")
    print("="*80)
    
    # Test GOMPC Projectes
    print("\n--- GOMPC PROJECTES ---")
    try:
        service = MeasurementHistoryService(machine='gompc_projectes')
        
        # Obtenir clients disponibles
        with service.connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT client, COUNT(*) as count
                FROM qualitat.mesures_gompc_projectes
                WHERE client IS NOT NULL
                GROUP BY client
                ORDER BY count DESC
                LIMIT 5
            """)
            clients = cursor.fetchall()
            
            print("Top 5 clients:")
            for client, count in clients:
                print(f"  {client}: {count:,} registres")
        
        service.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test GOMPC Nou
    print("\n--- GOMPC NOU ---")
    try:
        service = MeasurementHistoryService(machine='gompc_nou')
        
        with service.connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT client, COUNT(*) as count
                FROM qualitat.mesures_gompcnou
                WHERE client IS NOT NULL
                GROUP BY client
                ORDER BY count DESC
                LIMIT 5
            """)
            clients = cursor.fetchall()
            
            print("Top 5 clients:")
            for client, count in clients:
                print(f"  {client}: {count:,} registres")
        
        service.close()
        
    except Exception as e:
        print(f"ERROR: {e}")


def test_lot_search_by_machine():
    """Test cerca de lots específics per màquina"""
    
    print("\n" + "="*80)
    print("TEST CERCA DE LOTS ESPECÍFICS")
    print("="*80)
    
    test_lots = [
        {
            'client': 'AUTOLIV',
            'reference': '663962200',
            'lot': 'PRJ1229836',
            'machine': 'gompc_projectes'
        },
        {
            'client': 'AUTOLIV',
            'reference': '663962200',
            'lot': 'PRJ',  # Cerca parcial
            'machine': 'all'
        }
    ]
    
    for test in test_lots:
        print(f"\n--- Test LOT: {test['lot']} ---")
        print(f"Client: {test['client']}")
        print(f"Referència: {test['reference']}")
        print(f"Màquina: {test['machine']}")
        
        try:
            service = MeasurementHistoryService(machine=test['machine'])
            
            # Obtenir elements amb aquest LOT
            elements = service.get_available_elements(
                client=test['client'],
                project_reference=test['reference'],
                batch_lot=test['lot']
            )
            
            print(f"\n✓ Trobats {len(elements)} elements")
            
            if elements:
                # Mostrar primers 3 elements
                for i, elem in enumerate(elements[:3], 1):
                    print(f"  {i}. {elem['element']} | {elem['property']}: {elem['count']} mesures")
                
                # Obtenir lots únics
                lots = service.get_available_lots(
                    client=test['client'],
                    project_reference=test['reference']
                )
                
                # Filtrar lots que contenen el patró
                matching_lots = [lot for lot in lots if test['lot'].upper() in lot['id_lot'].upper()]
                
                print(f"\n  Lots que contenen '{test['lot']}': {len(matching_lots)}")
                for lot in matching_lots[:5]:
                    print(f"    - {lot['id_lot']}: {lot['count']} mesures")
            
            service.close()
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


def test_element_measurements_by_machine():
    """Test obtenció de mesures d'un element específic per màquina"""
    
    print("\n" + "="*80)
    print("TEST MESURES D'ELEMENTS ESPECÍFICS")
    print("="*80)
    
    test = {
        'client': 'AUTOLIV',
        'reference': '663962200',
        'element': ' DATUM A',
        'property': 'flatness_tolerance',
        'limit': 10
    }
    
    machines = ['gompc_projectes', 'all']
    
    for machine in machines:
        print(f"\n--- Màquina: {machine} ---")
        
        try:
            service = MeasurementHistoryService(machine=machine)
            
            measurements = service.get_element_measurements(
                client=test['client'],
                project_reference=test['reference'],
                element=test['element'],
                property_name=test['property'],
                limit=test['limit']
            )
            
            print(f"✓ Obtingudes {len(measurements)} mesures")
            print(f"  Màquina utilitzada: {service.get_current_machine()}")
            print(f"  Taules consultades: {', '.join(service.measurement_tables)}")
            
            if measurements:
                print(f"\n  Primeres 3 mesures:")
                for i, m in enumerate(measurements[:3], 1):
                    print(f"    {i}. Actual: {m.get('actual')}, Nominal: {m.get('nominal')}, LOT: {m.get('id_lot')}")
            
            service.close()
            
        except Exception as e:
            print(f"❌ ERROR: {e}")


def main():
    """Executar tots els tests"""
    
    print("="*80)
    print("TESTS COMPLETS DE FUNCIONALITAT DE MÀQUINES")
    print("="*80)
    
    test_machine_comparison()
    test_machine_specific_data()
    test_lot_search_by_machine()
    test_element_measurements_by_machine()
    
    print("\n" + "="*80)
    print("✅ TOTS ELS TESTS COMPLETATS")
    print("="*80)


if __name__ == "__main__":
    main()
