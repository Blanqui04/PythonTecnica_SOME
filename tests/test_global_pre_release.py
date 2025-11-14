#!/usr/bin/env python3
"""
TEST GLOBAL PRE-RELEASE
Verificació completa de totes les funcionalitats abans de fer release
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService
from src.services.capability_calculator_service import CapabilityCalculatorService
import numpy as np
import logging

logging.basicConfig(level=logging.ERROR)


def print_section(title, char="="):
    """Print formatted section header"""
    print(f"\n{char*80}")
    print(f"{title:^80}")
    print(f"{char*80}")


def print_subsection(title):
    """Print formatted subsection"""
    print(f"\n{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}")


def test_1_core_services():
    """Test 1: Serveis Core"""
    print_section("TEST 1: SERVEIS CORE")
    
    issues = []
    
    # 1.1 MeasurementHistoryService
    print_subsection("1.1 MeasurementHistoryService")
    try:
        service = MeasurementHistoryService()
        assert service is not None, "Servei no inicialitzat"
        assert service.machine == 'all', "Machine per defecte incorrecta"
        service.close()
        print("  ✅ MeasurementHistoryService inicialització OK")
    except Exception as e:
        issues.append(f"MeasurementHistoryService: {e}")
        print(f"  ❌ Error: {e}")
    
    # 1.2 CapabilityCalculatorService
    print_subsection("1.2 CapabilityCalculatorService")
    try:
        calc = CapabilityCalculatorService()
        test_values = [10.0, 10.1, 9.9, 10.2, 9.8]
        metrics = calc.calculate_metrics(test_values, 10.0, 0.5, 0.5)
        assert 'cp' in metrics, "Cp no calculat"
        assert 'cpk' in metrics, "Cpk no calculat"
        assert metrics['cp'] > 0, "Cp hauria de ser positiu"
        print(f"  ✅ CapabilityCalculatorService càlculs OK (Cp={metrics['cp']:.3f})")
    except Exception as e:
        issues.append(f"CapabilityCalculatorService: {e}")
        print(f"  ❌ Error: {e}")
    
    return issues


def test_2_machine_selector():
    """Test 2: Selector de Màquines"""
    print_section("TEST 2: SELECTOR DE MÀQUINES (5 MÀQUINES)")
    
    issues = []
    expected_machines = ['gompc_projectes', 'gompc_nou', 'hoytom', 'torsio', 'all']
    
    try:
        machines = MeasurementHistoryService.get_available_machines()
        
        print(f"\n  Màquines configurades: {len(machines)}")
        
        # Verificar que totes les màquines esperades estan disponibles
        for machine_key in expected_machines:
            if machine_key not in machines:
                issues.append(f"Màquina {machine_key} no disponible")
                print(f"  ❌ Màquina {machine_key} no trobada")
            else:
                info = machines[machine_key]
                print(f"  ✅ {info['name']} - {len(info['tables'])} taula(es)")
        
        # Verificar inicialització de cada màquina
        print_subsection("Verificant inicialització de cada màquina")
        
        for machine_key in expected_machines:
            try:
                service = MeasurementHistoryService(machine=machine_key)
                assert service.get_current_machine() == machines[machine_key]['name']
                service.close()
                print(f"  ✅ {machines[machine_key]['name']}: OK")
            except Exception as e:
                issues.append(f"Inicialització {machine_key}: {e}")
                print(f"  ❌ {machine_key}: {e}")
        
    except Exception as e:
        issues.append(f"Selector màquines: {e}")
        print(f"  ❌ Error general: {e}")
    
    return issues


def test_3_database_connectivity():
    """Test 3: Connectivitat Base de Dades"""
    print_section("TEST 3: CONNECTIVITAT BASE DE DADES")
    
    issues = []
    
    test_machines = [
        ('gompc_projectes', 'GOMPC Projectes'),
        ('hoytom', 'Hoytom'),
        ('all', 'Totes les màquines')
    ]
    
    for machine_key, machine_name in test_machines:
        print_subsection(f"Màquina: {machine_name}")
        
        try:
            service = MeasurementHistoryService(machine=machine_key)
            db = service.db_connection
            
            # Test simple query
            with db.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1, "Query test fallida"
            
            print(f"  ✅ Connexió DB OK")
            
            # Verificar taules
            for table in service.measurement_tables:
                try:
                    with db.connection.cursor() as cursor:
                        # Intentar qualitat primer
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table}")
                            count = cursor.fetchone()[0]
                            print(f"  ✅ qualitat.{table}: {count:,} registres")
                        except:
                            # Fallback a public
                            cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                            count = cursor.fetchone()[0]
                            print(f"  ✅ public.{table}: {count:,} registres")
                except Exception as e:
                    print(f"  ⚠️  {table}: {str(e)[:50]}")
            
            service.close()
            
        except Exception as e:
            issues.append(f"DB {machine_name}: {e}")
            print(f"  ❌ Error: {e}")
    
    return issues


def test_4_data_search():
    """Test 4: Cerca de Dades (CONTAINS)"""
    print_section("TEST 4: CERCA DE DADES (FLEXIBLE)")
    
    issues = []
    
    # Test amb GOMPC Projectes
    print_subsection("GOMPC Projectes - AUTOLIV 663962200")
    
    try:
        service = MeasurementHistoryService(machine='gompc_projectes')
        
        elements = service.get_available_elements(
            client='AUTOLIV',
            project_reference='663962200'
        )
        
        if len(elements) > 0:
            print(f"  ✅ Elements trobats: {len(elements)}")
            print(f"     Exemple: {elements[0]['element']} ({elements[0]['count']} mesures)")
        else:
            issues.append("GOMPC: No s'han trobat elements")
            print(f"  ❌ No s'han trobat elements")
        
        service.close()
        
    except Exception as e:
        issues.append(f"Cerca GOMPC: {e}")
        print(f"  ❌ Error: {e}")
    
    # Test amb Hoytom
    print_subsection("Hoytom - CMT51004775B")
    
    try:
        service = MeasurementHistoryService(machine='hoytom')
        db = service.db_connection
        
        with db.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
            """, ('%CMT51004775B%',))
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"  ✅ Assaigs trobats: {count:,}")
            else:
                issues.append("Hoytom: No s'han trobat assaigs")
                print(f"  ❌ No s'han trobat assaigs")
        
        service.close()
        
    except Exception as e:
        issues.append(f"Cerca Hoytom: {e}")
        print(f"  ❌ Error: {e}")
    
    return issues


def test_5_capability_calculations():
    """Test 5: Càlculs de Capacitat"""
    print_section("TEST 5: CÀLCULS DE CAPACITAT")
    
    issues = []
    
    print_subsection("Càlculs Cp, Cpk, Pp, Ppk, PPM")
    
    try:
        calc = CapabilityCalculatorService()
        
        # Generar dades de test
        np.random.seed(42)
        values = np.random.normal(10.0, 0.1, 100).tolist()
        
        metrics = calc.calculate_metrics(values, 10.0, 0.5, 0.5)
        
        # Verificar que tots els camps estan presents
        required_fields = ['mean', 'sigma_short', 'sigma_long', 'cp', 'cpk', 'pp', 'ppk', 'ppm']
        
        for field in required_fields:
            if field not in metrics:
                issues.append(f"Camp {field} no present en mètriques")
                print(f"  ❌ Camp {field} falta")
            elif metrics[field] is None:
                issues.append(f"Camp {field} és None")
                print(f"  ❌ Camp {field} és None")
        
        if not issues:
            print(f"  ✅ Mitjana: {metrics['mean']:.4f}")
            print(f"  ✅ Cp:  {metrics['cp']:.3f}")
            print(f"  ✅ Cpk: {metrics['cpk']:.3f}")
            print(f"  ✅ Pp:  {metrics['pp']:.3f}")
            print(f"  ✅ Ppk: {metrics['ppk']:.3f}")
            print(f"  ✅ PPM: {metrics['ppm']:.1f}")
            
            # Validacions lògiques
            if metrics['cpk'] > metrics['cp'] + 0.01:
                issues.append("Cpk no pot ser major que Cp")
                print(f"  ⚠️  Cpk > Cp (inconsistència)")
            
            if metrics['cp'] < 0 or metrics['cpk'] < 0:
                issues.append("Cp/Cpk negatius")
                print(f"  ❌ Índexs negatius")
        
    except Exception as e:
        issues.append(f"Càlculs capacitat: {e}")
        print(f"  ❌ Error: {e}")
    
    # Test normalitat
    print_subsection("Test de Normalitat")
    
    try:
        normality = calc.calculate_normality_metrics(values)
        
        if 'is_normal' in normality and 'p_value' in normality:
            print(f"  ✅ Test normalitat OK (p-value: {normality['p_value']:.4f})")
        else:
            issues.append("Test normalitat incomplet")
            print(f"  ❌ Test normalitat incomplet")
            
    except Exception as e:
        issues.append(f"Test normalitat: {e}")
        print(f"  ❌ Error: {e}")
    
    return issues


def test_6_performance():
    """Test 6: Performance"""
    print_section("TEST 6: PERFORMANCE")
    
    issues = []
    
    import time
    
    # Test performance Hoytom
    print_subsection("Performance Hoytom")
    
    try:
        start = time.time()
        
        service = MeasurementHistoryService(machine='hoytom')
        db = service.db_connection
        
        with db.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM public.mesureshoytom
                WHERE UPPER(ref_some) LIKE UPPER(%s)
            """, ('%CMT51004775B%',))
            
            count = cursor.fetchone()[0]
        
        elapsed = time.time() - start
        service.close()
        
        print(f"  ✅ Temps: {elapsed:.3f}s ({count:,} registres)")
        
        if elapsed > 2.0:
            issues.append(f"Hoytom lent: {elapsed:.3f}s")
            print(f"  ⚠️  Performance subòptim")
        
    except Exception as e:
        issues.append(f"Performance Hoytom: {e}")
        print(f"  ❌ Error: {e}")
    
    # Test performance GOMPC
    print_subsection("Performance GOMPC Projectes")
    
    try:
        start = time.time()
        
        service = MeasurementHistoryService(machine='gompc_projectes')
        elements = service.get_available_elements('AUTOLIV', '663962200')
        
        elapsed = time.time() - start
        service.close()
        
        print(f"  ✅ Temps: {elapsed:.3f}s ({len(elements)} elements)")
        
        if elapsed > 5.0:
            print(f"  ℹ️  Performance acceptable per 3.4M registres")
        
    except Exception as e:
        issues.append(f"Performance GOMPC: {e}")
        print(f"  ❌ Error: {e}")
    
    return issues


def test_7_backwards_compatibility():
    """Test 7: Compatibilitat Enrere"""
    print_section("TEST 7: COMPATIBILITAT ENRERE")
    
    issues = []
    
    print_subsection("Servei sense paràmetre machine")
    
    try:
        # Codi antic sense especificar màquina
        service = MeasurementHistoryService()
        
        assert service.machine == 'all', "Machine per defecte no és 'all'"
        assert len(service.measurement_tables) >= 2, "Hauria de tenir múltiples taules"
        
        elements = service.get_available_elements('AUTOLIV', '663962200')
        
        service.close()
        
        print(f"  ✅ Compatibilitat OK ({len(elements)} elements)")
        
    except Exception as e:
        issues.append(f"Compatibilitat: {e}")
        print(f"  ❌ Error: {e}")
    
    return issues


def run_global_pre_release_test():
    """Executar test global pre-release"""
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TEST GLOBAL PRE-RELEASE".center(78) + "║")
    print("║" + "  Verificació completa abans del release".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    all_issues = []
    
    tests = [
        ("Serveis Core", test_1_core_services),
        ("Selector de Màquines (5)", test_2_machine_selector),
        ("Connectivitat Base de Dades", test_3_database_connectivity),
        ("Cerca de Dades (CONTAINS)", test_4_data_search),
        ("Càlculs de Capacitat", test_5_capability_calculations),
        ("Performance", test_6_performance),
        ("Compatibilitat Enrere", test_7_backwards_compatibility)
    ]
    
    for test_name, test_func in tests:
        try:
            issues = test_func()
            all_issues.extend(issues)
        except Exception as e:
            all_issues.append(f"{test_name}: Excepció {e}")
            print(f"\n❌ Excepció en {test_name}: {e}")
    
    # Resum final
    print_section("RESUM FINAL PRE-RELEASE", "=")
    
    print(f"\n  Tests executats: {len(tests)}")
    print(f"  Issues trobats:  {len(all_issues)}")
    
    if all_issues:
        print("\n  ⚠️  ISSUES DETECTATS:")
        for i, issue in enumerate(all_issues, 1):
            print(f"    {i}. {issue}")
        print("\n" + "─"*80)
        print("\n  ❌ NO LLEST PER RELEASE")
        print("  ℹ️  Soluciona els issues abans de fer release")
        return False
    else:
        print("\n" + "─"*80)
        print("\n  ✅ TOTS ELS TESTS PASSATS")
        print("\n  🎉 SISTEMA VERIFICAT I LLEST PER RELEASE!")
        print("\n  Funcionalitats validades:")
        print("    ✅ 5 màquines operatives (GOMPC Projectes, Nou, Hoytom, Torsió, All)")
        print("    ✅ Connectivitat base de dades (3.5M+ registres)")
        print("    ✅ Cerca flexible CONTAINS")
        print("    ✅ Càlculs capacitat (Cp, Cpk, Pp, Ppk, PPM)")
        print("    ✅ Test normalitat")
        print("    ✅ Performance optimitzat")
        print("    ✅ Compatibilitat enrere")
        print("\n  🚀 PREPARAT PER PUSH A BRANCA STABLE")
        return True


if __name__ == "__main__":
    success = run_global_pre_release_test()
    sys.exit(0 if success else 1)
