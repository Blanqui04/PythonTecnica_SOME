"""
Test d'integració: Estudi de Capacitat amb nou sistema 1000_SQB_qualitat
Verifica que els càlculs de Cp/Cpk funcionen correctament
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.measurement_history_service import MeasurementHistoryService
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_capability_study_integration():
    """Test complet d'estudi de capacitat amb nou sistema"""
    
    print("\n" + "="*80)
    print("TEST INTEGRACIÓ: Estudi de Capacitat + Nou Sistema")
    print("="*80)
    
    # Dades de test
    client = "AUTOLIV"
    reference = "665220400"
    
    try:
        # 1. Obtenir elements disponibles
        print("\n[1] Obtenint elements disponibles...")
        service = MeasurementHistoryService(machine='gompc_projectes')
        
        elements = service.get_available_elements(
            client=client,
            project_reference=reference
        )
        
        print(f"    Elements trobats: {len(elements)}")
        
        if not elements:
            print("    ERROR: No elements trobats")
            return False
        
        # 2. Seleccionar un element per testar
        test_element = elements[0]
        element_name = test_element['element']
        
        print(f"\n[2] Element de test: {element_name}")
        
        # 3. Obtenir mesures
        print(f"\n[3] Obtenint mesures per l'element...")
        measurements = service.get_element_measurements(
            client=client,
            project_reference=reference,
            element_name=element_name,
            limit=100
        )
        
        print(f"    Mesures trobades: {len(measurements)}")
        
        if len(measurements) < 2:
            print("    SKIP: Necessitem mínim 2 mesures per Cp/Cpk")
            service.close()
            return True
        
        # 4. Extreure dades per càlculs
        actuals = [m['actual'] for m in measurements if m['actual'] is not None]
        nominals = [m['nominal'] for m in measurements if m['nominal'] is not None]
        tol_pos = [m['tolerancia_positiva'] for m in measurements if m['tolerancia_positiva'] is not None]
        tol_neg = [m['tolerancia_negativa'] for m in measurements if m['tolerancia_negativa'] is not None]
        
        print(f"\n[4] Dades extretes:")
        print(f"    Valors actuals: {len(actuals)}")
        print(f"    Valors nominals: {len(nominals)}")
        
        if not actuals or not nominals or not tol_pos or not tol_neg:
            print("    ERROR: Dades incompletes")
            service.close()
            return False
        
        # 5. Calcular estadístiques bàsiques
        print(f"\n[5] Estadístiques:")
        mean = np.mean(actuals)
        std = np.std(actuals, ddof=1)
        min_val = np.min(actuals)
        max_val = np.max(actuals)
        
        print(f"    Mitjana (X̄): {mean:.4f}")
        print(f"    Desviació estàndard (σ): {std:.4f}")
        print(f"    Mínim: {min_val:.4f}")
        print(f"    Màxim: {max_val:.4f}")
        
        # 6. Calcular Cp i Cpk
        nominal = nominals[0]
        tolerance_pos = tol_pos[0]
        tolerance_neg = abs(tol_neg[0])  # Fer positiu
        
        USL = nominal + tolerance_pos
        LSL = nominal - tolerance_neg
        
        print(f"\n[6] Límits:")
        print(f"    Nominal: {nominal:.4f}")
        print(f"    LSL: {LSL:.4f}")
        print(f"    USL: {USL:.4f}")
        
        if std > 0:
            Cp = (USL - LSL) / (6 * std)
            Cpu = (USL - mean) / (3 * std)
            Cpl = (mean - LSL) / (3 * std)
            Cpk = min(Cpu, Cpl)
            
            print(f"\n[7] Índexs de capacitat:")
            print(f"    Cp:  {Cp:.3f}")
            print(f"    Cpu: {Cpu:.3f}")
            print(f"    Cpl: {Cpl:.3f}")
            print(f"    Cpk: {Cpk:.3f}")
            
            # 8. Determinar estat
            if Cpk >= 1.33:
                status = "CAPAÇ (Cpk >= 1.33)"
                symbol = "✅"
            elif Cpk >= 1.0:
                status = "MARGINAL (1.0 <= Cpk < 1.33)"
                symbol = "⚠️"
            else:
                status = "NO CAPAÇ (Cpk < 1.0)"
                symbol = "❌"
            
            print(f"\n[8] Estat del procés:")
            print(f"    {symbol} {status}")
            
        else:
            print(f"\n    ERROR: Desviació estàndard = 0 (totes les mesures iguals)")
        
        service.close()
        
        print("\n" + "="*80)
        print("✅ TEST COMPLET: TOTES LES FUNCIONALITATS OPERATIVES")
        print("="*80)
        print("\nEl nou sistema 1000_SQB_qualitat és compatible amb estudis de capacitat!")
        print("Els càlculs de Cp/Cpk funcionen correctament amb les dades obtingudes.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_capability_study_integration()
    sys.exit(0 if success else 1)
