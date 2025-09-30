# src/services/capacity_study_service.py - FIXED VERSION
import logging
from typing import List, Dict, Any, Optional

from src.models.capability.capability_study_manager import (
    CapabilityStudyManager,
    StudyConfig,
)
from src.models.capability.extrapolation_manager import ExtrapolationConfig
from src.services.spc_chart_service import SPCChartService

logger = logging.getLogger(__name__)


def perform_capability_study(
    client: str,
    ref_project: str,
    elements: List[Dict[str, Any]],
    extrap_config: Optional[Dict[str, Any]] = None,
    min_sample_size: int = 5,
    batch_number: str = None,
) -> Dict[str, Any]:
    """
    Perform capability study with the provided elements and generate charts.
    
    Args:
        client: Client name
        ref_project: Project reference
        elements: List of elements with their data (from ElementInputWidget)
        extrap_config: Extrapolation configuration dict from GUI
        min_sample_size: Minimum sample size
        batch_number: Batch number for the study
    
    Returns:
        Dict containing:
            - study_results: Raw capability study results
            - chart_results: Chart generation results
            - elements_summary: Summary of elements with chart info
            - success: Boolean indicating overall success
    """
    
    logger.info(f"Starting capability study for {client}_{ref_project}_{batch_number}")
    logger.info(f"Processing {len(elements)} elements")
    
    try:
        # Step 1: Convert elements to sample data format
        sample_data = _convert_elements_to_sample_data(elements, batch_number)
        logger.debug(f"Converted {len(sample_data)} elements to sample data")
        
        # Step 2: Setup extrapolation configuration
        include_extrapolation = False
        extrapolation_config = None
        target_size = None
        
        if extrap_config and extrap_config.get("include_extrapolation", False):
            include_extrapolation = True
            extrap_params = extrap_config.get("extrapolation_config", {})
            target_size = extrap_params.get("target_size", 100)
            
            extrapolation_config = ExtrapolationConfig(
                target_p_value=extrap_params.get("target_p_value", 0.05),
                max_attempts=extrap_params.get("max_attempts", 100),
                available_sizes=[target_size],
            )
            
            logger.info(f"Extrapolation enabled: target_size={target_size}, target_p_value={extrap_params.get('target_p_value', 0.05)}")
        else:
            logger.info("Extrapolation disabled")
        
        # Step 3: Setup output directory with batch number
        output_dir = f"data/spc/{client}_{ref_project}_{batch_number}"
        
        config = StudyConfig(
            min_sample_size=min_sample_size,
            output_directory=output_dir,
            include_extrapolation=include_extrapolation,
            extrapolation_config=extrapolation_config,
            export_detailed_results=True,
        )
        
        # Step 4: Run capability study
        logger.info("Running capability study...")
        manager = CapabilityStudyManager(config)
        study_id = f"{ref_project}_{batch_number}"
        
        study_results = manager.run_capability_study(
            sample_data,
            study_id=study_id,
            interactive_extrapolation=False,
        )
        
        logger.info("Capability study completed successfully")
        
        # Step 5: Generate SPC charts
        logger.info("Initializing chart generation...")
        chart_service = SPCChartService(client, ref_project, batch_number)
        
        if not chart_service.initialize_chart_manager():
            logger.error("Failed to initialize chart manager")
            return {
                "success": False,
                "error": "Failed to initialize chart manager",
                "study_results": study_results,
            }
        
        # Validate study data
        valid, message = chart_service.validate_study_data()
        if not valid:
            logger.error(f"Study data validation failed: {message}")
            return {
                "success": False,
                "error": f"Data validation failed: {message}",
                "study_results": study_results,
            }
        
        logger.info("Generating charts for all elements...")
        chart_results = chart_service.generate_all_charts(show=False, save=True)
        
        # Log chart generation results
        total_charts = sum(len(elem_results) for elem_results in chart_results.values())
        successful_charts = sum(
            sum(elem_results.values()) for elem_results in chart_results.values()
        )
        
        logger.info(f"Chart generation completed: {successful_charts}/{total_charts} charts created")
        
        # Step 6: Get elements summary with chart information
        elements_summary = chart_service.get_elements_summary()
        study_statistics = chart_service.get_study_statistics()
        
        return {
            "success": True,
            "study_results": study_results,
            "chart_results": chart_results,
            "elements_summary": elements_summary,
            "study_statistics": study_statistics,
            "chart_service": chart_service,  # Pass service for later use
        }
        
    except Exception as e:
        logger.error(f"Error performing capability study: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


def _convert_elements_to_sample_data(
    elements: List[Dict[str, Any]], 
    batch_number: str
) -> List[Dict[str, Any]]:
    """
    Convert elements from ElementInputWidget format to CapabilityStudyManager format.
    
    Args:
        elements: List of dictionaries with element data from GUI
        batch_number: Batch number to assign to all elements
    
    Returns:
        List of sample data dictionaries in the correct format
    """
    sample_data = []
    
    for element in elements:
        # Extract cavity information properly
        cavity = element.get("cavity", "")
        
        sample_entry = {
            "element_id": element["element_id"],
            "class": element.get("class", ""),
            "cavity": cavity,
            "batch_number": batch_number,
            "nominal": element["nominal"],
            "tol_minus": element["tol_minus"],
            "tol_plus": element["tol_plus"],
            "values": element["values"],
        }
        
        sample_data.append(sample_entry)
        
        logger.debug(
            f"Converted element: {element['element_id']}, "
            f"cavity: '{cavity}', "
            f"values: {len(element['values'])}"
        )
    
    return sample_data


def regenerate_charts_only(
    client: str,
    ref_project: str,
    batch_number: str,
    chart_types: Optional[List[str]] = None,
    elements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Regenerate charts without re-running the capability study.
    Useful for when data already exists but charts need to be recreated.
    
    Args:
        client: Client name
        ref_project: Project reference
        batch_number: Batch number
        chart_types: Optional list of chart types to generate
        elements: Optional list of element names to generate charts for
    
    Returns:
        Dict with chart generation results
    """
    logger.info(f"Regenerating charts for {client}_{ref_project}_{batch_number}")
    
    try:
        chart_service = SPCChartService(client, ref_project, batch_number)
        
        if not chart_service.initialize_chart_manager():
            return {
                "success": False,
                "error": "Failed to initialize chart manager"
            }
        
        valid, message = chart_service.validate_study_data()
        if not valid:
            return {
                "success": False,
                "error": f"Data validation failed: {message}"
            }
        
        chart_results = chart_service.generate_all_charts(
            show=False, 
            save=True
        )
        
        return {
            "success": True,
            "chart_results": chart_results,
            "elements_summary": chart_service.get_elements_summary(),
            "study_statistics": chart_service.get_study_statistics(),
        }
        
    except Exception as e:
        logger.error(f"Error regenerating charts: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }