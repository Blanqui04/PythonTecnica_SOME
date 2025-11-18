"""Test all machine tables with new mappings"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.measurement_history_service import MeasurementHistoryService

def test_table(machine_name: str):
    """Test a specific machine table"""
    print(f"\n{'='*60}")
    print(f"TESTING: {machine_name}")
    print(f"{'='*60}")
    
    try:
        service = MeasurementHistoryService(machine=machine_name)
        print(f"✓ Service initialized")
        print(f"  Schema: {service.schema}")
        print(f"  Tables: {service.table_keys}")
        
        # Test elements with a reference to filter results
        print(f"\nSearching for elements (with sample reference)...")
        # Use a sample reference to limit results
        elements = service.get_available_elements('AUTOLIV', '665220400')
        print(f"✓ Found {len(elements)} elements")
        
        if elements:
            print(f"\nFirst 3 elements:")
            for i, elem in enumerate(elements[:3], 1):
                print(f"  {i}. {elem}")
            
            # Test LOTs for first element
            first_elem = elements[0]
            print(f"\nSearching LOTs for: {first_elem}")
            lots = service.get_distinct_lots(first_elem)
            print(f"✓ Found {len(lots)} LOTs")
            
            if lots:
                print(f"  First LOT: {lots[0]}")
                
                # Test measurements
                print(f"\nFetching measurements...")
                measurements = service.get_element_measurements(
                    first_elem, 
                    lots[0]
                )
                print(f"✓ Retrieved {len(measurements)} measurements")
                
                if measurements:
                    first_meas = measurements[0]
                    print(f"\nFirst measurement:")
                    print(f"  Element: {first_meas.get('element')}")
                    print(f"  Valor: {first_meas.get('actual')}")
                    print(f"  Data: {first_meas.get('data_hora')}")
        
        print(f"\n{'='*60}")
        print(f"✓ {machine_name} - ALL TESTS PASSED")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ {machine_name} - FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    machines = ['hoytom', 'torsio', 'zwick']
    results = {}
    
    for machine in machines:
        results[machine] = test_table(machine)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for machine, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{machine:15} {status}")
    print(f"{'='*60}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
