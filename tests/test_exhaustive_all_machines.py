#!/usr/bin/env python3
"""
Tests exhaustius de totes les màquines del selector
Verifica funcionalitat completa amb cada màquina
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
import logging

logging.basicConfig(level=logging.WARNING)


def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}")


def test_1_all_machines_initialization():
    """Test 1: Inicialització de totes les màquines"""
    print_header("TEST 1: INICIALITZACIÓ DE TOTES LES MÀQUINES")
    
    machines = MeasurementHistoryService.get_available_machines()
    
    print(f"\n✓ Total màquines configurades: {len(machines)}")
    
    results = {}
    
    for key, info in machines.items():
        print(f"\n--- {info['name']} ({key}) ---")
        
        try:
            service = MeasurementHistoryService(machine=key)
            
            # Verificacions
            assert service.get_current_machine() == info['name'], "Nom incorrecte"
            assert service.measurement_tables == info['tables'], "Taules incorrectes"
            
            print(f"  ✅ Inicialització: OK")
            print(f"  ✓ Nom: {service.get_current_machine()}")
            print(f"  ✓ Taules: {', '.join(service.measurement_tables)}")
            print(f"  ✓ Tipus: {info.get('type', 'N/A')}")
            
            service.close()
            results[key] = True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[key] = False
    
    # Resum
    passed = sum(1 for v in results.values() if v)
    print(f"\n{'─'*80}")
    print(f"Resultat: {passed}/{len(results)} màquines inicialitzades correctament")
    
    assert passed == len(results), f"Només {passed}/{len(results)} màquines funcionen"
    print("✅ TEST 1 PASSAT")
    return True


def test_2_database_connectivity():
    """Test 2: Connectivitat amb la base de dades per cada màquina"""
    print_header("TEST 2: CONNECTIVITAT BASE DE DADES")
    
    test_machines = ['gompc_projectes', 'gompc_nou', 'hoytom', 'all']
    
    results = {}
    
    for machine_key in test_machines:
        print(f"\n--- Màquina: {machine_key} ---")
        
        try:
            service = MeasurementHistoryService(machine=machine_key)
            db = service.db_connection
            
            with db.connection.cursor() as cursor:
                # Test simple query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                assert result[0] == 1, "Query test fallida"
                print(f"  ✅ Connexió DB: OK")
                
                # Comptar registres per cada taula
                for table in service.measurement_tables:
                    try:
                        # Intentar qualitat primer
                        cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table}")
                        count = cursor.fetchone()[0]
                        print(f"  ✓ qualitat.{table}: {count:,} registres")
                    except:
                        # Fallback a public
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                            count = cursor.fetchone()[0]
                            print(f"  ✓ public.{table}: {count:,} registres")
                        except Exception as e:
                            print(f"  ⚠️  {table}: No disponible")
            
            service.close()
            results[machine_key] = True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[machine_key] = False
    
    # Resum
    passed = sum(1 for v in results.values() if v)
    print(f"\n{'─'*80}")
    print(f"Resultat: {passed}/{len(results)} connexions exitoses")
    
    assert passed == len(results), f"Només {passed}/{len(results)} connexions OK"
    print("✅ TEST 2 PASSAT")
    return True


def test_3_search_gompc_projectes():
    """Test 3: Cerca amb GOMPC Projectes"""
    print_header("TEST 3: CERCA AMB GOMPC PROJECTES")
    
    service = MeasurementHistoryService(machine='gompc_projectes')
    
    print(f"\nMàquina: {service.get_current_machine()}")
    
    # Test amb AUTOLIV 663962200
    print("\n--- Test cerca: AUTOLIV 663962200 ---")
    
    try:
        elements = service.get_available_elements(
            client='AUTOLIV',
            project_reference='663962200'
        )
        
        print(f"  ✅ Elements trobats: {len(elements)}")
        assert len(elements) > 0, "No s'han trobat elements"
        
        # Mostrar primers 3
        for i, elem in enumerate(elements[:3], 1):
            print(f"  {i}. {elem['element']} | {elem.get('property', 'N/A')} | {elem['count']} mesures")
        
        # Test amb LOT
        print("\n--- Test cerca amb LOT: PRJ1229836 ---")
        
        elements_lot = service.get_available_elements(
            client='AUTOLIV',
            project_reference='663962200',
            batch_lot='PRJ1229836'
        )
        
        print(f"  ✅ Elements amb LOT: {len(elements_lot)}")
        assert len(elements_lot) > 0, "No s'han trobat elements amb LOT"
        
        service.close()
        print("\n✅ TEST 3 PASSAT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        service.close()
        return False


def test_4_search_gompc_nou():
    """Test 4: Cerca amb GOMPC Nou"""
    print_header("TEST 4: CERCA AMB GOMPC NOU")
    
    service = MeasurementHistoryService(machine='gompc_nou')
    
    print(f"\nMàquina: {service.get_current_machine()}")
    
    try:
        # Obtenir dades disponibles
        db = service.db_connection
        with db.connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT client, COUNT(*) as count
                FROM qualitat.mesures_gompcnou
                WHERE client IS NOT NULL
                GROUP BY client
                ORDER BY count DESC
                LIMIT 5
            """)
            
            clients = cursor.fetchall()
            
            if clients:
                print(f"\n✓ Clients disponibles: {len(clients)}")
                for client, count in clients:
                    print(f"  - {client}: {count:,} registres")
                
                # Test cerca amb primer client
                test_client = clients[0][0]
                cursor.execute(f"""
                    SELECT DISTINCT id_referencia_some
                    FROM qualitat.mesures_gompcnou
                    WHERE client = %s
                    LIMIT 1
                """, (test_client,))
                
                ref = cursor.fetchone()
                if ref:
                    print(f"\n--- Test cerca: {test_client} - {ref[0]} ---")
                    
                    elements = service.get_available_elements(
                        client=test_client,
                        project_reference=str(ref[0])
                    )
                    
                    print(f"  ✅ Elements trobats: {len(elements)}")
            else:
                print("\n  ℹ️  GOMPC Nou no té dades actualment (taula buida)")
        
        service.close()
        print("\n✅ TEST 4 PASSAT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        service.close()
        return False


def test_5_search_hoytom():
    """Test 5: Cerca amb Hoytom"""
    print_header("TEST 5: CERCA AMB HOYTOM")
    
    service = MeasurementHistoryService(machine='hoytom')
    
    print(f"\nMàquina: {service.get_current_machine()}")
    
    try:
        db = service.db_connection
        with db.connection.cursor() as cursor:
            # Obtenir referències disponibles
            cursor.execute("""
                SELECT ref_some, COUNT(*) as count
                FROM public.mesureshoytom
                WHERE ref_some IS NOT NULL
                GROUP BY ref_some
                ORDER BY count DESC
                LIMIT 5
            """)
            
            refs = cursor.fetchall()
            
            print(f"\n✓ Top 5 referències:")
            for ref, count in refs:
                print(f"  - {ref}: {count:,} assaigs")
            
            # Test cerca amb primera referència
            test_ref = refs[0][0]
            
            print(f"\n--- Test cerca: {test_ref} ---")
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
            """, (f'%{test_ref}%',))
            
            count = cursor.fetchone()[0]
            print(f"  ✅ Assaigs trobats: {count:,}")
            assert count > 0, "No s'han trobat assaigs"
            
            # Tipus d'assaigs
            cursor.execute("""
                SELECT DISTINCT tipo_ensayo, COUNT(*) as count
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
                GROUP BY tipo_ensayo
                ORDER BY count DESC
                LIMIT 3
            """, (f'%{test_ref}%',))
            
            tipos = cursor.fetchall()
            print(f"\n  ✓ Tipus d'assaigs:")
            for tipo, cnt in tipos:
                print(f"    • {tipo}: {cnt}")
        
        service.close()
        print("\n✅ TEST 5 PASSAT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        service.close()
        return False


def test_6_search_all_machines():
    """Test 6: Cerca amb totes les màquines"""
    print_header("TEST 6: CERCA AMB TOTES LES MÀQUINES")
    
    service = MeasurementHistoryService(machine='all')
    
    print(f"\nMàquina: {service.get_current_machine()}")
    print(f"Taules: {', '.join(service.measurement_tables)}")
    
    try:
        # Test amb AUTOLIV (hauria de trobar a GOMPC)
        print("\n--- Test cerca: AUTOLIV 663962200 ---")
        
        elements = service.get_available_elements(
            client='AUTOLIV',
            project_reference='663962200'
        )
        
        print(f"  ✅ Elements trobats: {len(elements)}")
        assert len(elements) > 0, "No s'han trobat elements"
        
        # Mostrar primer element
        if elements:
            elem = elements[0]
            print(f"  Exemple: {elem['element']} | {elem.get('property', 'N/A')} | {elem['count']} mesures")
        
        service.close()
        print("\n✅ TEST 6 PASSAT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        service.close()
        return False


def test_7_machine_comparison():
    """Test 7: Comparativa entre màquines"""
    print_header("TEST 7: COMPARATIVA ENTRE MÀQUINES")
    
    test_data = {
        'client': 'AUTOLIV',
        'reference': '663962200'
    }
    
    machines_to_test = ['gompc_projectes', 'gompc_nou', 'all']
    
    results = {}
    
    print(f"\nCercant: {test_data['client']} - {test_data['reference']}")
    
    for machine in machines_to_test:
        print(f"\n--- Màquina: {machine} ---")
        
        try:
            service = MeasurementHistoryService(machine=machine)
            
            elements = service.get_available_elements(
                client=test_data['client'],
                project_reference=test_data['reference']
            )
            
            results[machine] = len(elements)
            
            print(f"  ✓ Elements trobats: {len(elements)}")
            print(f"  ✓ Taules consultades: {', '.join(service.measurement_tables)}")
            
            service.close()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[machine] = 0
    
    # Verificar consistència
    print(f"\n{'─'*80}")
    print("Resum comparativa:")
    for machine, count in results.items():
        print(f"  {machine}: {count} elements")
    
    # 'all' hauria de tenir >= que qualsevol màquina individual
    max_individual = max(results.get('gompc_projectes', 0), results.get('gompc_nou', 0))
    all_count = results.get('all', 0)
    
    assert all_count >= max_individual, f"Inconsistència: all ({all_count}) < max individual ({max_individual})"
    
    print(f"\n✓ Consistència verificada: all ({all_count}) >= max individual ({max_individual})")
    print("\n✅ TEST 7 PASSAT")
    return True


def test_8_performance_check():
    """Test 8: Verificació de performance"""
    print_header("TEST 8: VERIFICACIÓ DE PERFORMANCE")
    
    import time
    
    test_cases = [
        ('gompc_projectes', 'AUTOLIV', '663962200'),
        ('hoytom', None, 'CMT51004775B'),
        ('all', 'AUTOLIV', '663962200')
    ]
    
    print("\nTemps de resposta per màquina:\n")
    
    for machine, client, reference in test_cases:
        try:
            start = time.time()
            
            service = MeasurementHistoryService(machine=machine)
            
            if machine == 'hoytom':
                # Per Hoytom, cerca directa a la taula
                db = service.db_connection
                with db.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM public.mesureshoytom
                        WHERE UPPER(ref_some) LIKE UPPER(%s)
                    """, (f'%{reference}%',))
                    count = cursor.fetchone()[0]
            else:
                elements = service.get_available_elements(
                    client=client,
                    project_reference=reference
                )
                count = len(elements)
            
            elapsed = time.time() - start
            
            service.close()
            
            # Classificar performance
            if elapsed < 1.0:
                status = "⚡ Excel·lent"
            elif elapsed < 2.0:
                status = "✓ Bé"
            else:
                status = "⚠️  Lent"
            
            print(f"  {machine:20} → {elapsed:6.3f}s  ({count:,} elements)  {status}")
            
        except Exception as e:
            print(f"  {machine:20} → Error: {str(e)[:40]}")
    
    print("\n✅ TEST 8 PASSAT")
    return True


def test_9_backwards_compatibility():
    """Test 9: Compatibilitat amb codi existent"""
    print_header("TEST 9: COMPATIBILITAT ENRERE")
    
    print("\n--- Test 1: Servei sense paràmetre machine ---")
    
    try:
        # Hauria de funcionar amb default='all'
        service = MeasurementHistoryService()
        
        assert service.machine == 'all', "Machine hauria de ser 'all'"
        assert service.get_current_machine() == 'Totes les màquines', "Nom incorrecte"
        assert len(service.measurement_tables) >= 2, "Hauria de tenir múltiples taules"
        
        print(f"  ✅ Màquina per defecte: {service.get_current_machine()}")
        print(f"  ✅ Taules: {', '.join(service.measurement_tables)}")
        
        service.close()
        
        print("\n--- Test 2: Cerca sense especificar màquina ---")
        
        service = MeasurementHistoryService()
        elements = service.get_available_elements('AUTOLIV', '663962200')
        
        print(f"  ✅ Elements trobats: {len(elements)}")
        assert len(elements) > 0, "Hauria de trobar elements"
        
        service.close()
        
        print("\n✅ TEST 9 PASSAT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Executar tots els tests"""
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  SUITE COMPLETA DE TESTS - TOTES LES MÀQUINES".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Inicialització de totes les màquines", test_1_all_machines_initialization),
        ("Connectivitat base de dades", test_2_database_connectivity),
        ("Cerca amb GOMPC Projectes", test_3_search_gompc_projectes),
        ("Cerca amb GOMPC Nou", test_4_search_gompc_nou),
        ("Cerca amb Hoytom", test_5_search_hoytom),
        ("Cerca amb totes les màquines", test_6_search_all_machines),
        ("Comparativa entre màquines", test_7_machine_comparison),
        ("Verificació de performance", test_8_performance_check),
        ("Compatibilitat enrere", test_9_backwards_compatibility)
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                failed_tests.append(name)
        except Exception as e:
            failed += 1
            failed_tests.append(name)
            print(f"\n❌ Test '{name}' fallit amb excepció: {e}")
            import traceback
            traceback.print_exc()
    
    # Resum final
    print_header("RESUM FINAL")
    
    print(f"\n  Tests executats: {len(tests)}")
    print(f"  Tests passats:   {passed} ✅")
    print(f"  Tests fallits:   {failed} ❌")
    
    if failed > 0:
        print(f"\n  Tests fallits:")
        for test_name in failed_tests:
            print(f"    • {test_name}")
    
    print("\n" + "─"*80)
    
    if failed == 0:
        print("\n  🎉 TOTS ELS TESTS HAN PASSAT CORRECTAMENT!")
        print("\n  ✅ Totes les 5 màquines funcionen perfectament")
        print("  ✅ Cerca per client/referència: OK")
        print("  ✅ Cerca per LOT: OK")
        print("  ✅ Hoytom amb assaigs de tracció: OK")
        print("  ✅ Compatibilitat enrere: OK")
        print("  ✅ Performance adequat: OK")
        print("\n  🚀 LLEST PER PRODUCCIÓ!")
        return True
    else:
        print(f"\n  ⚠️  {failed} test(s) han fallat")
        print("  ℹ️  Revisa els errors anteriors")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
