# src/services/capacity_study_service.py
from src.models.capability.capability_study_manager import (
    CapabilityStudyManager,
    StudyConfig,
)


def perform_capability_study(
    client: str,
    ref_project: str,
    elements: list,
    min_sample_size: int = 5,
    extrapolate=False,
):
    """
    Perform capability study with the provided elements

    Args:
        client: Client name
        ref_project: Project reference
        elements: List of elements with their data (from ElementInputWidget)
        min_sample_size: Minimum sample size
        extrapolate: Whether to extrapolate results

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

    config = StudyConfig(
        min_sample_size=min_sample_size,
        output_directory=f"data/spc/{client}_{ref_project}",
        include_extrapolation=extrapolate,
        export_detailed_results=True,
    )

    manager = CapabilityStudyManager(config)
    results = manager.run_capability_study(
        sample_data, study_id=f"{client}_{ref_project}", interactive_extrapolation=False
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
    # This function needs to be implemented based on your CapabilityStudyManager's expected format
    # For now, I'll provide a basic structure that you'll need to adapt

    sample_data = []

    for element in elements:
        # Convert each element to the format your system expects
        sample_entry = {
            "element_id": element["element_id"],
            "class": element["class"],
            "cavity": element["cavity"],
            "batch": element["batch"],
            "nominal": element["nominal"],
            "tolerance_minus": element["tol_minus"],
            "tolerance_plus": element["tol_plus"],
            "measurements": element["values"],
            # Add any other fields your system needs
        }
        sample_data.append(sample_entry)

    return sample_data
