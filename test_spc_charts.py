# test_charts.py
"""
Test script for SPC Chart Manager
Run this from the root directory to test chart generation
"""

import json
import sys
import logging
from pathlib import Path


# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent / "src" / "models" / "plotting"))

from src.models.plotting.spc_charts_manager import SPCChartManager


def setup_logging():
    """Setup detailed logging for testing"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/test_charts.log', mode='w', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


def create_test_data():
    """Create test data that mimics the structure expected by SPCDataLoader"""
    test_data = {
        "detailed_results": [
            {
                "element_name": "Element_A",
                "nominal": 10.0,
                "tolerance": [-0.5, 0.5],
                "original_values": [10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4],
                "statistics": {
                    "mean": 10.234,
                    "sample_size": 20,
                    "std_short": 0.112,
                    "std_long": 0.125,
                    "ad_statistic": 0.358,
                    "p_value": 0.412
                },
                "capability": {
                    "cp": 1.48,
                    "cpk": 1.32,
                    "pp": 1.33,
                    "ppk": 1.18,
                    "ppm_short": 145.2,
                    "ppm_long": 287.4
                }
            },
            {
                "element_name": "Element_B",
                "nominal": 5.0,
                "tolerance": [-0.3, 0.3],
                "original_values": [5.09, 5.14, 4.97, 5.11, 5.04, 5.16, 4.99, 5.07, 5.13, 5.02],
                "statistics": {
                    "mean": 5.063,
                    "sample_size": 20,
                    "std_short": 0.067,
                    "std_long": 0.071,
                    "ad_statistic": 0.234,
                    "p_value": 0.783
                },
                "capability": {
                    "cp": 1.49,
                    "cpk": 1.41,
                    "pp": 1.41,
                    "ppk": 1.33,
                    "ppm_short": 98.7,
                    "ppm_long": 156.3
                }
            }
        ],
        "extrapolation_results": [
            {
                "element_name": "Element_A",
                "extrapolated_values": [10.08, 10.31, 10.19, 10.42, 10.25, 10.13, 10.36, 10.21, 10.17, 10.28,
                                        10.14, 10.33, 10.22, 10.39, 10.26, 10.11, 10.34, 10.18, 10.29, 10.15,
                                        10.07, 10.32, 10.24, 10.41, 10.16, 10.38, 10.20, 10.27, 10.12, 10.35,
                                        10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4, 
                                        10.15, 10.25, 10.18, 10.32, 10.28, 10.12, 10.35, 10.22, 10.17, 10.29,
                                        10.08, 10.31, 10.19, 10.42, 10.25, 10.13, 10.36, 10.21, 10.17, 10.28,
                                        10.14, 10.33, 10.22, 10.39, 10.26, 10.11, 10.34, 10.18, 10.29, 10.15,
                                        10.07, 10.32, 10.24, 10.41, 10.16, 10.38, 10.20, 10.27, 10.12, 10.35,
                                        10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4, 
                                        10.15, 10.25, 10.18, 10.32, 10.28, 10.12, 10.35, 10.22, 10.17, 10.29,
                                        10.08, 10.31, 10.19, 10.42, 10.25, 10.13, 10.36, 10.21, 10.17, 10.28,
                                        10.14, 10.33, 10.22, 10.39, 10.26, 10.11, 10.34, 10.18, 10.29, 10.15,
                                        10.07, 10.32, 10.24, 10.41, 10.16, 10.38, 10.20, 10.27, 10.12, 10.35,
                                        10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4, 
                                        10.15, 10.25, 10.18, 10.32, 10.28, 10.12, 10.35, 10.22, 10.17, 10.29,
                                        10.08, 10.31, 10.19, 10.42, 10.25, 10.13, 10.36, 10.21, 10.17, 10.28,
                                        10.14, 10.33, 10.22, 10.39, 10.26, 10.11, 10.34, 10.18, 10.29, 10.15,
                                        10.07, 10.32, 10.24, 10.41, 10.16, 10.38, 10.20, 10.27, 10.12, 10.35,
                                        10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4, 
                                        10.15, 10.25, 10.18, 10.32, 10.28, 10.12, 10.35, 10.22, 10.17, 10.29,
                                        10.08, 10.31, 10.19, 10.42, 10.25, 10.13, 10.36, 10.21, 10.17, 10.28,
                                        10.14, 10.33, 10.22, 10.39, 10.26, 10.11, 10.34, 10.18, 10.29, 10.15,
                                        10.07, 10.32, 10.24, 10.41, 10.16, 10.38, 10.20, 10.27, 10.12, 10.35,
                                        10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4, 
                                        10.15, 10.25, 10.18, 10.32, 10.28, 10.12, 10.35, 10.22, 10.17, 10.29],
                "ad_statistic": 0.278,
                "p_value": 0.634
            },
            {
                "element_name": "Element_B",
                "extrapolated_values": [5.04, 5.13, 5.07, 4.96, 5.16, 5.02, 4.94, 5.19, 5.05, 5.00,
                                      5.08, 5.15, 4.98, 5.12, 5.03, 5.17, 4.97, 5.06, 5.14, 5.01,
                                      5.09, 5.11, 4.99, 5.18, 5.04, 4.95, 5.13, 5.07, 5.16, 5.02,
                                      5.04, 5.13, 5.07, 4.96, 5.16, 5.02, 4.94, 5.19, 5.05, 5.00,
                                      5.08, 5.15, 4.98, 5.12, 5.03, 5.17, 4.97, 5.06, 5.14, 5.01,
                                      5.09, 5.11, 4.99, 5.18, 5.04, 4.95, 5.13, 5.07, 5.16, 5.02,
                                      5.04, 5.13, 5.07, 4.96, 5.16, 5.02, 4.94, 5.19, 5.05, 5.00,
                                      5.08, 5.15, 4.98, 5.12, 5.03, 5.17, 4.97, 5.06, 5.14, 5.01,
                                      5.09, 5.11, 4.99, 5.18, 5.04, 4.95, 5.13, 5.07, 5.16, 5.02,
                                      5.04, 5.13, 5.07, 4.96, 5.16, 5.02, 4.94, 5.19, 5.05, 5.00,
                                      5.08, 5.15, 4.98, 5.12, 5.03, 5.17, 4.97, 5.06, 5.14, 5.01,
                                      5.09, 5.11, 4.99, 5.18, 5.04, 4.95, 5.13, 5.07, 5.16, 5.02,
                                      5.04, 5.13, 5.07, 4.96, 5.16, 5.02, 4.94, 5.19, 5.05, 5.00,
                                      5.08, 5.15, 4.98, 5.12, 5.03, 5.17, 4.97, 5.06, 5.14, 5.01,
                                      5.09, 5.11, 4.99, 5.18, 5.04, 4.95, 5.13, 5.07, 5.16, 5.02],
                "ad_statistic": 0.198,
                "p_value": 0.821
            }
            # Element_C has no extrapolation data
        ]
    }
    return test_data


def test_chart_manager():
    """Test the SPCChartManager with generated test data"""
    logger = setup_logging()
    logger.info("Starting SPC Chart Manager test")
    
    # Create test data directories
    data_dir = Path("./data/spc")
    output_dir = Path("./data/reports/statistics")
    
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    study_id = "test_study"
    test_data_file = data_dir / f"{study_id}_complete_report.json"
    
    try:
        # Create test data file
        logger.info(f"Creating test data file: {test_data_file}")
        test_data = create_test_data()
        
        with open(test_data_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        logger.info("Test data file created successfully")
        
        # Initialize chart manager
        logger.info("Initializing SPCChartManager")
        manager = SPCChartManager(
            study_id=study_id,
            base_path=str(data_dir),
            output_dir=str(output_dir),
            lang="ca",
            logger=logger
        )
        
        # Load data
        logger.info("Loading data...")
        if not manager.load_data():
            logger.error("Failed to load data")
            return False
            
        # Get elements summary
        logger.info("Getting elements summary...")
        summary = manager.get_elements_summary()
        logger.info("Elements summary:")
        for element_name, info in summary.items():
            logger.info(f"  {element_name}: {info}")
        
        # Test creating individual charts
        logger.info("Testing individual chart creation...")
        elements = list(summary.keys())
        
        if elements:
            first_element = elements[0]
            logger.info(f"Creating normality chart for '{first_element}'")
            success = manager.create_chart(first_element, 'normality', show=False, save=True)
            if success:
                logger.info("Individual chart creation successful")
            else:
                logger.error("Individual chart creation failed")
        
        # Test creating all charts
        logger.info("Testing bulk chart creation...")
        results = manager.create_all_charts(
            show=False,  # Set to True if you want to see the charts
            save=True
        )
        
        # Log results
        logger.info("Chart creation results:")
        total_charts = 0
        successful_charts = 0
        
        for element_name, element_results in results.items():
            logger.info(f"  {element_name}:")
            for chart_type, success in element_results.items():
                status = "SUCCESS" if success else "FAILED"
                logger.info(f"    {chart_type}: {status}")
                total_charts += 1
                if success:
                    successful_charts += 1
        
        logger.info(f"Overall results: {successful_charts}/{total_charts} charts created successfully")
        
        # List created files
        logger.info("Created chart files:")
        for chart_file in output_dir.glob("*.png"):
            logger.info(f"  {chart_file}")
            
        return successful_charts == total_charts
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
        
    finally:
        # Clean up test data file
        try:
            if test_data_file.exists():
                test_data_file.unlink()
                logger.info("Test data file cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up test data file: {e}")


def main():
    """Main test function"""
    print("=" * 60)
    print("SPC Chart Manager Test")
    print("=" * 60)
    
    success = test_chart_manager()
    
    if success:
        print("\n✅ All tests passed successfully!")
        print("Check the ./output/charts/ directory for generated charts.")
        print("Check test_charts.log for detailed logging information.")
    else:
        print("\n❌ Some tests failed!")
        print("Check test_charts.log for error details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())