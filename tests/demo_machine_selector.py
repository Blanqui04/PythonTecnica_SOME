#!/usr/bin/env python3
"""
Demostració del selector de màquines en acció
Mostra com utilitzar la funcionalitat
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService


def demo_machine_selector():
    """Demostració interactiva del selector de màquines"""
    
    print("\n" + "="*80)
    print("DEMOSTRACIÓ: SELECTOR DE MÀQUINES PER ESTUDIS DE CAPACITAT")
    print("="*80)
    
    # 1. Mostrar màquines disponibles
    print("\n📋 PAS 1: Màquines disponibles")
    print("-" * 80)
    
    machines = MeasurementHistoryService.get_available_machines()
    
    for i, (key, info) in enumerate(machines.items(), 1):
        print(f"\n{i}. {info['name']} (key: '{key}')")
        print(f"   └─ {info['description']}")
        print(f"   └─ Taules: {', '.join(info['tables'])}")
    
    # 2. Exemple d'ús amb cada màquina
    print("\n\n🔍 PAS 2: Exemple de cerca amb cada màquina")
    print("-" * 80)
    
    test_client = "AUTOLIV"
    test_ref = "663962200"
    
    print(f"\nCercant elements per:")
    print(f"  Client: {test_client}")
    print(f"  Referència: {test_ref}")
    
    for key, info in machines.items():
        print(f"\n  ▶ Amb màquina: {info['name']}")
        
        service = MeasurementHistoryService(machine=key)
        elements = service.get_available_elements(
            client=test_client,
            project_reference=test_ref
        )
        
        print(f"    ✓ Resultats: {len(elements)} elements trobats")
        print(f"    ✓ Taules consultades: {', '.join(service.measurement_tables)}")
        
        if elements:
            elem = elements[0]
            print(f"    ✓ Primer element: {elem['element']} ({elem.get('property', 'N/A')})")
        
        service.close()
    
    # 3. Exemple amb filtre de LOT
    print("\n\n🎯 PAS 3: Cerca amb filtre de LOT")
    print("-" * 80)
    
    test_lot = "PRJ1229836"
    
    print(f"\nCercant amb LOT: {test_lot}")
    
    service = MeasurementHistoryService(machine='gompc_projectes')
    elements = service.get_available_elements(
        client=test_client,
        project_reference=test_ref,
        batch_lot=test_lot
    )
    
    print(f"  ✓ Elements amb LOT específic: {len(elements)}")
    
    if elements:
        print(f"\n  Primers 5 elements:")
        for i, elem in enumerate(elements[:5], 1):
            print(f"    {i}. {elem['element']} | {elem.get('property', 'N/A')} | {elem['count']} mesures")
    
    service.close()
    
    # 4. Comparativa de rendiment
    print("\n\n⚡ PAS 4: Comparativa de resultats")
    print("-" * 80)
    
    print("\n  Comparant diferents configuracions:")
    print(f"  {'Màquina':<25} {'Elements':<12} {'Descripció'}")
    print(f"  {'-'*25} {'-'*12} {'-'*40}")
    
    configs = [
        ('gompc_projectes', 'Només GOMPC Projectes'),
        ('gompc_nou', 'Només GOMPC Nou'),
        ('all', 'Totes les màquines')
    ]
    
    for machine_key, description in configs:
        service = MeasurementHistoryService(machine=machine_key)
        elements = service.get_available_elements(
            client=test_client,
            project_reference=test_ref
        )
        
        machine_name = service.get_current_machine()
        print(f"  {machine_name:<25} {len(elements):<12} {description}")
        
        service.close()
    
    # 5. Recomanacions d'ús
    print("\n\n💡 PAS 5: Recomanacions d'ús")
    print("-" * 80)
    
    print("\n  Quan utilitzar cada configuració:")
    print("\n  📊 GOMPC Projectes:")
    print("     └─ Quan necessites dades específiques de projectes dimensionals")
    print("     └─ Per estudis de capacitat de productes en fase de projecte")
    print("     └─ Més ràpid si saps que les dades són aquí")
    
    print("\n  🆕 GOMPC Nou:")
    print("     └─ Per mesures dimensionals més recents o actualitzades")
    print("     └─ Quan cerques dades noves no disponibles a Projectes")
    
    print("\n  🌐 Totes les màquines:")
    print("     └─ Quan no estàs segur d'on són les dades")
    print("     └─ Per obtenir una visió completa de totes les fonts")
    print("     └─ Opció per defecte més segura però pot ser més lenta")
    
    # Final
    print("\n" + "="*80)
    print("✅ DEMOSTRACIÓ COMPLETADA")
    print("="*80)
    print("\nEl selector de màquines està operatiu i funcional!")
    print("Ara pots utilitzar-lo a la interfície d'estudis de capacitat.\n")


if __name__ == "__main__":
    demo_machine_selector()
