# test_orchestrator.py (a l'arrel o dins de /tests)
from src.services.data_processing_orchestrator import DataProcessingOrchestrator

if __name__ == "__main__":
    orchestrator = DataProcessingOrchestrator()
    result, msg = orchestrator.process_and_transform("ADIENT", "5704341")
    
    if result:
        print("✅ Tot correcte!")
        print(result)
    else:
        print(f"❌ Error: {msg}")
