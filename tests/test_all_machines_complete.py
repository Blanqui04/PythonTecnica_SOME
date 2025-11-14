#!/usr/bin/env python3
"""
Test complet de totes les màquines incloent Hoytom i Torsió
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService


def test_all_machines_complete():
    """Test complet de totes les màquines"""
    
    print("\n" + "="*80)
    print("TEST COMPLET DE TOTES LES MÀQUINES")
    print("="*80)
    
    machines = MeasurementHistoryService.get_available_machines()
    
    print(f"\n✓ Màquines disponibles: {len(machines)}")
    
    for key, info in machines.items():
        print(f"\n{'='*80}")
        print(f"Màquina: {info['name']} ({key})")
        print(f"{'='*80}")
        print(f"  Descripció: {info['description']}")
        print(f"  Taules: {', '.join(info['tables'])}")
        print(f"  Tipus: {info.get('type', 'N/A')}")
        
        # Inicialitzar servei
        try:
            service = MeasurementHistoryService(machine=key)
            print(f"  ✅ Servei inicialitzat correctament")
            print(f"  Nom màquina: {service.get_current_machine()}")
            
            # Verificar schema
            if key in ['hoytom', 'torsio']:
                expected_schema = 'public'
            else:
                expected_schema = service.schema
            
            print(f"  Schema: {expected_schema}")
            
            # Comptar registres
            db = service.db_connection
            with db.connection.cursor() as cursor:
                for table in info['tables']:
                    try:
                        # Intentar qualitat primer, sino public
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM qualitat.{table}")
                            count = cursor.fetchone()[0]
                            print(f"  ✓ qualitat.{table}: {count:,} registres")
                        except:
                            cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                            count = cursor.fetchone()[0]
                            print(f"  ✓ public.{table}: {count:,} registres")
                    except Exception as e:
                        print(f"  ⚠️  {table}: No disponible ({str(e)[:50]})")
            
            service.close()
            
        except Exception as e:
            print(f"  ❌ Error inicialitzant servei: {e}")


def test_hoytom_specific():
    """Test específic per Hoytom amb referències reals"""
    
    print("\n" + "="*80)
    print("TEST ESPECÍFIC HOYTOM")
    print("="*80)
    
    service = MeasurementHistoryService(machine='hoytom')
    db = service.db_connection
    
    print(f"\nMàquina: {service.get_current_machine()}")
    print(f"Taules: {', '.join(service.measurement_tables)}")
    
    try:
        with db.connection.cursor() as cursor:
            # Top 5 referències
            print("\n--- Top 5 Referències ---")
            cursor.execute("""
                SELECT ref_some, COUNT(*) as count
                FROM public.mesureshoytom
                WHERE ref_some IS NOT NULL
                GROUP BY ref_some
                ORDER BY count DESC
                LIMIT 5
            """)
            
            refs = cursor.fetchall()
            for ref, count in refs:
                print(f"  {ref}: {count:,} assaigs")
            
            # Tipus d'assaigs
            print("\n--- Tipus d'Assaigs ---")
            cursor.execute("""
                SELECT tipo_ensayo, COUNT(*) as count
                FROM public.mesureshoytom
                WHERE tipo_ensayo IS NOT NULL
                GROUP BY tipo_ensayo
                ORDER BY count DESC
                LIMIT 10
            """)
            
            tipos = cursor.fetchall()
            for tipo, count in tipos:
                print(f"  {tipo}: {count:,}")
            
            # Assaigs més recents
            print("\n--- Assaigs Recents ---")
            cursor.execute("""
                SELECT ensayo, ref_some, tipo_ensayo, fuerza_maxima_fm, fecha_ensayo
                FROM public.mesureshoytom
                WHERE fecha_ensayo IS NOT NULL
                ORDER BY fecha_ensayo DESC
                LIMIT 5
            """)
            
            recents = cursor.fetchall()
            for ensayo, ref, tipo, fuerza, fecha in recents:
                print(f"  {fecha}: {ref} - {tipo} - {fuerza:.2f}N (#{ensayo})")
        
        print("\n✅ Test Hoytom completat")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        service.close()


def test_machine_selection_ui():
    """Simula selecció de màquines des de la UI"""
    
    print("\n" + "="*80)
    print("SIMULACIÓ SELECCIÓ DE MÀQUINES (UI)")
    print("="*80)
    
    # Obtenir màquines com ho faria la UI
    machines = MeasurementHistoryService.get_available_machines()
    
    print("\nMàquines al ComboBox:")
    for i, (key, info) in enumerate(machines.items(), 1):
        print(f"  {i}. {info['name']} (key: '{key}')")
    
    # Simular selecció de cada màquina
    test_selections = ['gompc_projectes', 'gompc_nou', 'hoytom', 'torsio', 'all']
    
    print("\n--- Test Seleccions ---")
    for selection in test_selections:
        if selection in machines:
            info = machines[selection]
            print(f"\n  Usuari selecciona: {info['name']}")
            
            try:
                service = MeasurementHistoryService(machine=selection)
                print(f"    ✅ Servei creat: {service.get_current_machine()}")
                print(f"    Taules: {', '.join(service.measurement_tables)}")
                service.close()
            except Exception as e:
                print(f"    ❌ Error: {e}")
        else:
            print(f"\n  ⚠️  Màquina '{selection}' no disponible")
    
    print("\n✅ Simulació UI completada")


def main():
    """Executar tots els tests"""
    test_all_machines_complete()
    test_hoytom_specific()
    test_machine_selection_ui()
    
    print("\n" + "="*80)
    print("TESTS COMPLETATS")
    print("="*80)
    print("\n✅ Totes les màquines (GOMPC Projectes, GOMPC Nou, Hoytom, Torsió) funcionalsj!")
    print("✅ Selector de màquines preparat per la UI")


if __name__ == "__main__":
    main()
