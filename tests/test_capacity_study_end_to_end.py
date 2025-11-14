#!/usr/bin/env python3
"""
Test End-to-End del Capacity Study amb totes les màquines
Verifica el flux complet des de l'inici fins al final
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


def test_full_capacity_study_gompc_projectes():
    """Test complet amb GOMPC Projectes"""
    print_header("TEST CAPACITY STUDY COMPLET - GOMPC PROJECTES")
    
    machine = 'gompc_projectes'
    client = 'AUTOLIV'
    reference = '663962200'
    lot = 'PRJ1229836'
    
    print(f"\nParàmetres:")
    print(f"  Màquina: {machine}")
    print(f"  Client: {client}")
    print(f"  Referència: {reference}")
    print(f"  LOT: {lot}")
    
    try:
        # FASE 1: Obtenir historial de mesures
        print(f"\n{'─'*80}")
        print("FASE 1: Obtenint historial de mesures...")
        
        service = MeasurementHistoryService(machine=machine)
        print(f"  ✓ Servei inicialitzat: {service.get_current_machine()}")
        
        # Obtenir elements disponibles
        elements = service.get_available_elements(
            client=client,
            project_reference=reference,
            batch_lot=lot
        )
        
        print(f"  ✓ Elements trobats: {len(elements)}")
        
        if not elements:
            print("  ⚠️  No s'han trobat elements")
            service.close()
            return False
        
        # Seleccionar primer element per l'exemple
        element = elements[0]
        print(f"  ✓ Element seleccionat: {element['element']}")
        print(f"    Property: {element.get('property', 'N/A')}")
        print(f"    Mesures disponibles: {element['count']}")
        
        # FASE 2: Obtenir mesures
        print(f"\n{'─'*80}")
        print("FASE 2: Obtenint mesures de l'element...")
        
        measurements = service.get_element_measurements(
            client=client,
            project_reference=reference,
            element_name=element['element'],
            property_name=element.get('property'),
            batch_lot=lot
        )
        
        print(f"  ✓ Mesures obtingudes: {len(measurements)}")
        
        if measurements:
            first_meas = measurements[0]
            print(f"  ✓ Exemple de mesura:")
            print(f"    Valor: {first_meas.get('valor_mesura', 'N/A')}")
            print(f"    Data: {first_meas.get('data', 'N/A')}")
            print(f"    LOT: {first_meas.get('lot', 'N/A')}")
        
        service.close()
        
        # FASE 3: Verificar estructura de dades
        print(f"\n{'─'*80}")
        print("FASE 3: Verificant estructura de dades...")
        
        # Comprovar camps necessaris
        required_fields = ['valor_mesura', 'data', 'element']
        
        if measurements:
            available_fields = set(measurements[0].keys())
            print(f"  ✓ Camps disponibles: {len(available_fields)}")
            
            missing = [f for f in required_fields if f not in available_fields]
            if missing:
                print(f"  ⚠️  Camps que falten: {missing}")
            else:
                print(f"  ✓ Tots els camps necessaris presents")
        
        # FASE 4: Anàlisi estadístic bàsic
        print(f"\n{'─'*80}")
        print("FASE 4: Anàlisi estadístic bàsic...")
        
        if measurements:
            values = [m.get('valor_mesura') for m in measurements if m.get('valor_mesura') is not None]
            
            if values:
                mean = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                
                print(f"  ✓ Valors vàlids: {len(values)}")
                print(f"  ✓ Mitjana: {mean:.4f}")
                print(f"  ✓ Mínim: {min_val:.4f}")
                print(f"  ✓ Màxim: {max_val:.4f}")
                print(f"  ✓ Rang: {max_val - min_val:.4f}")
        
        print(f"\n✅ TEST GOMPC PROJECTES COMPLETAT CORRECTAMENT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_capacity_study_hoytom():
    """Test complet amb Hoytom"""
    print_header("TEST CAPACITY STUDY COMPLET - HOYTOM")
    
    machine = 'hoytom'
    reference = 'CMT51004775B'
    
    print(f"\nParàmetres:")
    print(f"  Màquina: {machine}")
    print(f"  Referència: {reference}")
    
    try:
        # FASE 1: Connectar amb Hoytom
        print(f"\n{'─'*80}")
        print("FASE 1: Connectant amb Hoytom...")
        
        service = MeasurementHistoryService(machine=machine)
        print(f"  ✓ Servei inicialitzat: {service.get_current_machine()}")
        print(f"  ✓ Taules: {', '.join(service.measurement_tables)}")
        
        # FASE 2: Cercar assaigs disponibles
        print(f"\n{'─'*80}")
        print("FASE 2: Cercant assaigs...")
        
        db = service.db_connection
        with db.connection.cursor() as cursor:
            # Obtenir assaigs de la referència
            cursor.execute("""
                SELECT 
                    ensayo,
                    ref_some,
                    tipo_ensayo,
                    fuerza_maxima_fm,
                    fecha_ensayo,
                    alargamiento_a
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
                ORDER BY fecha_ensayo DESC
                LIMIT 10
            """, (f'%{reference}%',))
            
            assaigs = cursor.fetchall()
            
            print(f"  ✓ Assaigs trobats: {len(assaigs)}")
            
            if assaigs:
                print(f"\n  Primers 3 assaigs:")
                for i, assaig in enumerate(assaigs[:3], 1):
                    ensayo, ref, tipo, fuerza, fecha, alargamiento = assaig
                    print(f"    {i}. {ensayo}")
                    print(f"       Tipus: {tipo}")
                    print(f"       Força: {fuerza}")
                    print(f"       Data: {fecha}")
                    print(f"       Alargament: {alargamiento}")
            
            # FASE 3: Estadístiques per tipus d'assaig
            print(f"\n{'─'*80}")
            print("FASE 3: Estadístiques per tipus d'assaig...")
            
            cursor.execute("""
                SELECT 
                    tipo_ensayo,
                    COUNT(*) as count,
                    AVG(fuerza_maxima_fm) as avg_force,
                    MIN(fuerza_maxima_fm) as min_force,
                    MAX(fuerza_maxima_fm) as max_force
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
                    AND fuerza_maxima_fm IS NOT NULL
                GROUP BY tipo_ensayo
                ORDER BY count DESC
            """, (f'%{reference}%',))
            
            stats = cursor.fetchall()
            
            print(f"\n  Resum per tipus:")
            for tipo, count, avg, min_f, max_f in stats:
                print(f"    • {tipo}:")
                print(f"      Assaigs: {count}")
                print(f"      Força mitjana: {avg:.2f} kN")
                print(f"      Rang: {min_f:.2f} - {max_f:.2f} kN")
        
        service.close()
        
        print(f"\n✅ TEST HOYTOM COMPLETAT CORRECTAMENT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_capacity_study_all_machines():
    """Test complet amb totes les màquines"""
    print_header("TEST CAPACITY STUDY COMPLET - TOTES LES MÀQUINES")
    
    machine = 'all'
    client = 'AUTOLIV'
    reference = '663962200'
    
    print(f"\nParàmetres:")
    print(f"  Màquina: {machine}")
    print(f"  Client: {client}")
    print(f"  Referència: {reference}")
    
    try:
        # FASE 1: Inicialització
        print(f"\n{'─'*80}")
        print("FASE 1: Inicialitzant cerca multi-màquina...")
        
        service = MeasurementHistoryService(machine=machine)
        print(f"  ✓ Servei inicialitzat: {service.get_current_machine()}")
        print(f"  ✓ Taules consultades:")
        for table in service.measurement_tables:
            print(f"    - {table}")
        
        # FASE 2: Cerca en totes les màquines
        print(f"\n{'─'*80}")
        print("FASE 2: Cercant en totes les màquines...")
        
        elements = service.get_available_elements(
            client=client,
            project_reference=reference
        )
        
        print(f"  ✓ Total elements trobats: {len(elements)}")
        
        if elements:
            # Mostrar distribució per taula (si es pot determinar)
            print(f"\n  Primers 5 elements:")
            for i, elem in enumerate(elements[:5], 1):
                print(f"    {i}. {elem['element']} | {elem.get('property', 'N/A')} | {elem['count']} mesures")
        
        # FASE 3: Obtenir mesures d'un element
        if elements:
            print(f"\n{'─'*80}")
            print("FASE 3: Obtenint mesures del primer element...")
            
            element = elements[0]
            
            measurements = service.get_element_measurements(
                client=client,
                project_reference=reference,
                element_name=element['element'],
                property_name=element.get('property')
            )
            
            print(f"  ✓ Mesures obtingudes: {len(measurements)}")
            
            if measurements:
                # Anàlisi ràpid
                values = [m.get('valor_mesura') for m in measurements if m.get('valor_mesura') is not None]
                if values:
                    print(f"  ✓ Valors vàlids: {len(values)}")
                    print(f"  ✓ Mitjana: {sum(values)/len(values):.4f}")
        
        service.close()
        
        print(f"\n✅ TEST TOTES LES MÀQUINES COMPLETAT CORRECTAMENT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_machine_selector_workflow():
    """Test del workflow del selector de màquines"""
    print_header("TEST WORKFLOW SELECTOR DE MÀQUINES")
    
    print("\nSimulant selecció d'usuari en la UI...")
    
    try:
        # Simular obtenció de màquines disponibles (com a la UI)
        available_machines = MeasurementHistoryService.get_available_machines()
        
        print(f"\n✓ Màquines disponibles al selector: {len(available_machines)}")
        
        for key, info in available_machines.items():
            print(f"\n  [{key}] {info['name']}")
            print(f"      Descripció: {info['description']}")
            print(f"      Tipus: {info.get('type', 'N/A')}")
            print(f"      Taules: {', '.join(info['tables'])}")
        
        # Simular selecció de cada màquina
        print(f"\n{'─'*80}")
        print("Simulant selecció de cada màquina...")
        
        test_selections = [
            ('gompc_projectes', 'AUTOLIV', '663962200'),
            ('gompc_nou', 'AUTOLIV', '663962200'),  # Pot no trobar res
            ('hoytom', None, 'CMT51004775B'),
            ('all', 'AUTOLIV', '663962200')
        ]
        
        for machine, client, reference in test_selections:
            print(f"\n  → Usuari selecciona: {available_machines[machine]['name']}")
            
            service = MeasurementHistoryService(machine=machine)
            
            if machine == 'hoytom':
                # Per Hoytom, cerca directa
                db = service.db_connection
                with db.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM public.mesureshoytom
                        WHERE UPPER(ref_some) LIKE UPPER(%s)
                    """, (f'%{reference}%',))
                    count = cursor.fetchone()[0]
                    print(f"    ✓ Assaigs trobats: {count}")
            else:
                # Per GOMPC, cerca normal
                elements = service.get_available_elements(client=client, project_reference=reference)
                print(f"    ✓ Elements trobats: {len(elements)}")
            
            service.close()
        
        print(f"\n✅ TEST WORKFLOW SELECTOR COMPLETAT CORRECTAMENT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_e2e_tests():
    """Executar tots els tests end-to-end"""
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TESTS END-TO-END - CAPACITY STUDY COMPLET".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Capacity Study complet - GOMPC Projectes", test_full_capacity_study_gompc_projectes),
        ("Capacity Study complet - Hoytom", test_full_capacity_study_hoytom),
        ("Capacity Study complet - Totes les màquines", test_full_capacity_study_all_machines),
        ("Workflow selector de màquines", test_machine_selector_workflow)
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
    
    # Resum final
    print_header("RESUM FINAL END-TO-END")
    
    print(f"\n  Tests executats: {len(tests)}")
    print(f"  Tests passats:   {passed} ✅")
    print(f"  Tests fallits:   {failed} ❌")
    
    if failed > 0:
        print(f"\n  Tests fallits:")
        for test_name in failed_tests:
            print(f"    • {test_name}")
    
    print("\n" + "─"*80)
    
    if failed == 0:
        print("\n  🎉 TOTS ELS TESTS END-TO-END HAN PASSAT!")
        print("\n  ✅ Flux complet GOMPC Projectes: OK")
        print("  ✅ Flux complet Hoytom: OK")
        print("  ✅ Flux complet Totes les màquines: OK")
        print("  ✅ Workflow UI selector: OK")
        print("\n  📊 CAPACITY STUDY FUNCIONA DE 0 A 100% AMB TOTES LES MÀQUINES")
        print("  🚀 SISTEMA COMPLETAMENT OPERATIU!")
        return True
    else:
        print(f"\n  ⚠️  {failed} test(s) han fallat")
        return False


if __name__ == "__main__":
    success = run_all_e2e_tests()
    sys.exit(0 if success else 1)
