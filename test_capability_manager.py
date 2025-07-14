#!/usr/bin/env python3
"""
Short test script for CapabilityStudyManager
"""

import sys
import os
from datetime import datetime

from src.models.capability.capability_study_manager import CapabilityStudyManager, StudyConfig
from src.models.capability.sample_data_manager import SampleDataManager


def test_capability_study_manager():
    """Test the CapabilityStudyManager with default sample data"""
    
    print("=" * 60)
    print("Testing CapabilityStudyManager")
    print("=" * 60)
    
    try:
        # Get default sample data
        print("1. Getting default sample data...")
        default_data = SampleDataManager.get_default_sample_data()
        print(f"   Loaded {len(default_data)} test elements")
        for e in default_data:
            print(f"   - {e.name} ({e.element_type})")

        # Test 1: Quick Study
        print("\n2. Running quick study...")
        manager = CapabilityStudyManager(config=StudyConfig(min_sample_size=5))
        quick_results = manager.run_quick_study(default_data)
        
        if quick_results.get("success"):
            print("   ✓ Quick study completed successfully")
            print(f"   - Elements analyzed: {quick_results['elements_analyzed']}")
            summary = quick_results['summary_statistics']
            print(f"   - Successful analyses: {summary['successful_analyses']}")
            print(f"   - Failed analyses: {summary['failed_analyses']}")
            if 'capability_indices' in summary:
                cp_mean = summary['capability_indices']['cp']['mean']
                cpk_mean = summary['capability_indices']['cpk']['mean']
                print(f"   - Average CP: {cp_mean:.3f}")
                print(f"   - Average CPK: {cpk_mean:.3f}")
        else:
            print("   ✗ Quick study failed:")
            print(f"   Error: {quick_results.get('error')}")
            return False
        
        # Test 2: Full Study (without interactive extrapolation)
        print("\n3. Running full study...")
        config = StudyConfig(
                min_sample_size=5,
                #output_directory="test_output",
                include_extrapolation=True,
                export_detailed_results=True,
                export_summary=True
            )
        
        full_manager = CapabilityStudyManager(config)
        study_results = full_manager.run_capability_study(
            default_data,
            study_id="test_study",
            interactive_extrapolation=False
        )
        
        print("   ✓ Full study completed successfully")
        print(f"   - Study ID: {study_results.study_id}")
        print(f"   - Elements analyzed: {study_results.elements_analyzed}")
        print(f"   - Successful analyses: {study_results.successful_analyses}")
        print(f"   - Failed analyses: {study_results.failed_analyses}")
        print(f"   - Output files created: {len(study_results.output_files)}")
        
        for file_path in study_results.output_files:
            print(f"     - {file_path}")
        
        # Test 3: Get recommendations
        print("\n4. Getting study recommendations...")
        recommendations = full_manager.get_study_recommendations(study_results)
        
        if recommendations:
            print("   Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   ✓ No specific recommendations - all results look good!")
        
        # Test 4: Test validation with insufficient data
        print("\n5. Testing validation with insufficient data...")
        insufficient_data = default_data[:1]  # Only one element
        validation_errors = full_manager.validate_study_data(insufficient_data)
        
        if validation_errors:
            print("   ✓ Validation correctly detected insufficient data:")
            for error in validation_errors:
                print(f"     - {error}")
        else:
            print("   ✗ Validation should have detected insufficient data")
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files():
    """Clean up test output files"""
    import shutil
    if os.path.exists("test_output"):
        shutil.rmtree("test_output")
        print("Cleaned up test output directory")


if __name__ == "__main__":
    print("Starting CapabilityStudyManager Test...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_capability_study_manager()
    
    if success:
        print(f"\n🎉 All tests passed! ({datetime.now().strftime('%H:%M:%S')})")
        response = input("\nClean up test output files? (y/n): ").lower().strip()
        if response == 'y':
            cleanup_test_files()
    else:
        print(f"\n❌ Tests failed! ({datetime.now().strftime('%H:%M:%S')})")
        sys.exit(1)
