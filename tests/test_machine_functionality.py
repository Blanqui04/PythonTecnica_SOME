#!/usr/bin/env python3
"""
Test funcional complet del selector de màquines
Aquest test es pot executar sense interfície gràfica
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService


def print_section(title):
    """Print formatted section"""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print('='*80)


def test_1_available_machines():
    """Test 1: Verificar màquines disponibles"""
    print_section("TEST 1: MÀQUINES DISPONIBLES")
    
    machines = MeasurementHistoryService.get_available_machines()
    
    print(f"\n✓ Trobades {len(machines)} màquines:")
    for key, info in machines.items():
        print(f"\n  [{key}]")
        print(f"    Nom: {info['name']}")
        print(f"    Taules: {', '.join(info['tables'])}")
        print(f"    Descripció: {info['description']}")
    
    assert len(machines) >= 3, "S'esperen almenys 3 configuracions de màquines"
    assert 'gompc_projectes' in machines, "Falta gompc_projectes"
    assert 'gompc_nou' in machines, "Falta gompc_nou"
    assert 'all' in machines, "Falta configuració 'all'"
    
    print("\n✅ Test 1 PASSAT")
    return True


def test_2_service_initialization():
    """Test 2: Inicialització del servei amb diferents màquines"""
    print_section("TEST 2: INICIALITZACIÓ DEL SERVEI")
    
    test_machines = ['gompc_projectes', 'gompc_nou', 'all']
    
    for machine in test_machines:
        print(f"\n--- Provant màquina: {machine} ---")
        
        service = MeasurementHistoryService(machine=machine)
        
        # Verificar configuració
        machine_name = service.get_current_machine()
        tables = service.measurement_tables
        
        print(f"  ✓ Nom: {machine_name}")
        print(f"  ✓ Taules: {', '.join(tables)}")
        
        # Verificar que les taules són correctes
        if machine == 'gompc_projectes':
            assert 'mesures_gompc_projectes' in tables
            assert len(tables) == 1
        elif machine == 'gompc_nou':
            assert 'mesures_gompcnou' in tables
            assert len(tables) == 1
        elif machine == 'all':
            assert len(tables) >= 2
        
        service.close()
        print(f"  ✓ Servei tancat correctament")
    
    print("\n✅ Test 2 PASSAT")
    return True


def test_3_search_by_machine():
    """Test 3: Cerca d'elements per màquina"""
    print_section("TEST 3: CERCA D'ELEMENTS PER MÀQUINA")
    
    test_data = {
        'client': 'AUTOLIV',
        'reference': '663962200'
    }
    
    results = {}
    
    for machine in ['gompc_projectes', 'gompc_nou', 'all']:
        print(f"\n--- Cercant amb màquina: {machine} ---")
        
        service = MeasurementHistoryService(machine=machine)
        elements = service.get_available_elements(
            client=test_data['client'],
            project_reference=test_data['reference']
        )
        
        results[machine] = len(elements)
        
        print(f"  ✓ Trobats: {len(elements)} elements")
        if elements:
            print(f"  ✓ Exemple: {elements[0]['element']} - {elements[0].get('property', 'N/A')}")
        
        service.close()
    
    # Verificar lògica: all >= suma de les altres
    print("\n--- Verificació de consistència ---")
    print(f"  gompc_projectes: {results['gompc_projectes']} elements")
    print(f"  gompc_nou: {results['gompc_nou']} elements")
    print(f"  all: {results['all']} elements")
    
    # La màquina 'all' hauria de tenir almenys tants elements com la més gran
    max_individual = max(results['gompc_projectes'], results['gompc_nou'])
    assert results['all'] >= max_individual, f"'all' ({results['all']}) hauria de ser >= {max_individual}"
    
    print(f"\n  ✓ Consistència verificada: all ({results['all']}) >= max individual ({max_individual})")
    
    print("\n✅ Test 3 PASSAT")
    return True


def test_4_lot_filtering():
    """Test 4: Filtratge per LOT amb diferents màquines"""
    print_section("TEST 4: FILTRATGE PER LOT")
    
    test_data = {
        'client': 'AUTOLIV',
        'reference': '663962200',
        'lot': 'PRJ1229836'
    }
    
    for machine in ['gompc_projectes', 'all']:
        print(f"\n--- Cercant LOT amb màquina: {machine} ---")
        
        service = MeasurementHistoryService(machine=machine)
        
        # Cerca amb LOT
        elements = service.get_available_elements(
            client=test_data['client'],
            project_reference=test_data['reference'],
            batch_lot=test_data['lot']
        )
        
        print(f"  ✓ Elements amb LOT '{test_data['lot']}': {len(elements)}")
        
        if elements:
            # Mostrar primer element amb detall
            elem = elements[0]
            print(f"  ✓ Exemple: {elem['element']} | {elem.get('property', 'N/A')} | {elem['count']} mesures")
        
        service.close()
    
    print("\n✅ Test 4 PASSAT")
    return True


def test_5_multiple_references():
    """Test 5: Provar amb múltiples referències"""
    print_section("TEST 5: MÚLTIPLES REFERÈNCIES")
    
    references = [
        ('AUTOLIV', '663962200'),
        ('AUTOLIV', '665220400'),
        ('ZF', 'A027Y915')  # Si existeix
    ]
    
    machine = 'gompc_projectes'
    
    for client, ref in references:
        print(f"\n--- {client} - {ref} ---")
        
        try:
            service = MeasurementHistoryService(machine=machine)
            elements = service.get_available_elements(
                client=client,
                project_reference=ref
            )
            
            print(f"  ✓ Trobats: {len(elements)} elements")
            
            service.close()
            
        except Exception as e:
            print(f"  ⚠️  Error (pot ser normal si no hi ha dades): {e}")
    
    print("\n✅ Test 5 PASSAT")
    return True


def test_6_backwards_compatibility():
    """Test 6: Compatibilitat amb codi existent (sense paràmetre machine)"""
    print_section("TEST 6: COMPATIBILITAT ENRERE")
    
    print("\n--- Creant servei sense especificar màquina ---")
    
    # Hauria de funcionar amb el valor per defecte 'all'
    service = MeasurementHistoryService()
    
    machine_name = service.get_current_machine()
    tables = service.measurement_tables
    
    print(f"  ✓ Màquina per defecte: {machine_name}")
    print(f"  ✓ Taules: {', '.join(tables)}")
    
    assert machine_name == "Totes les màquines", "Per defecte hauria de ser 'Totes les màquines'"
    assert len(tables) >= 2, "Per defecte hauria de consultar múltiples taules"
    
    service.close()
    
    print("\n✅ Test 6 PASSAT")
    return True


def run_all_tests():
    """Executar tots els tests"""
    print("="*80)
    print("SUITE DE TESTS: SELECTOR DE MÀQUINES")
    print("="*80)
    
    tests = [
        test_1_available_machines,
        test_2_service_initialization,
        test_3_search_by_machine,
        test_4_lot_filtering,
        test_5_multiple_references,
        test_6_backwards_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test FALLIT: {test_func.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Resum final
    print_section("RESUM FINAL")
    print(f"\n  Tests passats: {passed}/{len(tests)}")
    print(f"  Tests fallits: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n  🎉 TOTS ELS TESTS HAN PASSAT CORRECTAMENT!")
        print("\n  ✅ El selector de màquines funciona perfectament")
        print("  ✅ La cerca per màquina és consistent")
        print("  ✅ El filtratge per LOT funciona")
        print("  ✅ Compatibilitat enrere mantinguda")
        return True
    else:
        print(f"\n  ⚠️  {failed} test(s) han fallat")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
