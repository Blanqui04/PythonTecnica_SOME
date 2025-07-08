import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.data_processing.pipeline_manager import DataProcessingPipeline

def test_kop_processing():
    """Simple test function"""
    pipeline = DataProcessingPipeline()
    
    # Test parameters
    test_client = 'ADIENT'
    test_ref_project = '5850717'
    
    print(f"Testing KOP processing for {test_client} - {test_ref_project}")
    print("-" * 50)
    
    try:
        result, message = pipeline.process_project(test_client, test_ref_project, 'kop')
        
        if result:
            print("✅ SUCCESS!")
            print(f"Message: {message}")
            print(f"Client: {result['client']}")
            print(f"Project: {result['ref_project']}")
            print(f"Processed at: {result['processed_at']}")
            print(f"Datasheet entries: {len(result['datasheet'])}")
        else:
            print("❌ FAILED!")
            print(f"Error: {message}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_kop_processing()