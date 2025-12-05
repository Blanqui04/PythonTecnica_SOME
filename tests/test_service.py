# For testing charts without GUI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.services.spc_chart_service import generate_charts_for_study

def test_generate_charts():
    """Test per generar gràfiques SPC"""
    result = generate_charts_for_study("test_client", "test_project", batch_number="LOT001", show=False, save=False)
    if result["success"]:
        print(f"Generated charts for {len(result['chart_results'])} elements")
        print(f"Study statistics: {result['study_statistics']}")
    else:
        print(f"Info: {result.get('error', 'No data')}")