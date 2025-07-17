# src/services/capacity_study_service.py

from src.models.capability.capability_study_manager import (
    CapabilityStudyManager,
    StudyConfig,
)
from src.models.capability.extrapolation_manager import ExtrapolationConfig


def perform_capability_study(
    client: str,
    ref_project: str,
    elements: list,
    extrap_config: dict = None,
    min_sample_size: int = 5,
):
    """
    Perform capability study with the provided elements

    Args:
        client: Client name
        ref_project: Project reference
        elements: List of elements with their data (from ElementInputWidget)
        extrap_config: Extrapolation configuration dict from GUI
        min_sample_size: Minimum sample size

    Returns:
        Study results
    """
    # If no elements provided, fall back to default behavior
    if not elements:
        from src.models.capability.sample_data_manager import SampleDataManager

        sample_data = SampleDataManager.get_default_sample_data()
    else:
        # Convert elements to the format expected by your capability study
        sample_data = _convert_elements_to_sample_data(elements)

    # Handle extrapolation configuration
    include_extrapolation = False
    extrapolation_config = None

    if extrap_config and extrap_config.get("include_extrapolation", False):
        include_extrapolation = True
        extrap_params = extrap_config.get("extrapolation_config", {})

        # Create ExtrapolationConfig with GUI parameters
        extrapolation_config = ExtrapolationConfig(
            target_p_value=extrap_params.get("target_p_value", 0.05),
            max_attempts=extrap_params.get("max_attempts", 100),
            available_sizes=[
                extrap_params.get("target_size", 100)
            ],  # Use selected size
        )
        print(f"YEEEEEEEE [DEBUG] Extrapolation target size from GUI: {extrap_params.get('target_size')}")


    config = StudyConfig(
        min_sample_size=min_sample_size,
        output_directory=f"data/spc/{client}_{ref_project}",
        include_extrapolation=include_extrapolation,
        extrapolation_config=extrapolation_config,
        export_detailed_results=True,
    )

    manager = CapabilityStudyManager(config)

    results = manager.run_capability_study(
        sample_data,
        study_id=f"{client}_{ref_project}",
        interactive_extrapolation=False,
    )

    return results


def _convert_elements_to_sample_data(elements):
    """
    Convert elements from ElementInputWidget format to the format expected by CapabilityStudyManager

    Args:
        elements: List of dictionaries with element data

    Returns:
        Sample data in the format expected by your capability study manager
    """
    sample_data = []

    for element in elements:
        # Convert each element to the format your system expects
        sample_entry = {
            "element_id": element["element_id"],
            "class": element["class"],
            "cavity": element["cavity"],
            "batch": element["batch"],
            "nominal": element["nominal"],
            "tol_minus": element["tol_minus"],
            "tol_plus": element["tol_plus"],
            "values": element["values"],
        }
        sample_data.append(sample_entry)

    return sample_data
