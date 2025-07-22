# For testing charts without GUI
from src.services.spc_chart_service import generate_charts_for_study

result = generate_charts_for_study("test_client", "test_project", show=True, save=True)
if result["success"]:
    print(f"Generated charts for {len(result['chart_results'])} elements")
    print(f"Study statistics: {result['study_statistics']}")
else:
    print(f"Error: {result['error']}")