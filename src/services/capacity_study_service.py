# src/services/capacity_study_service.py
from src.models.capability.capability_study_manager import CapabilityStudyManager, StudyConfig

def perform_capability_study(client: str, ref_project: str, min_sample_size: int = 5, extrapolate=False):
    from src.models.capability.sample_data_manager import SampleDataManager

    sample_data = SampleDataManager.get_default_sample_data()

    config = StudyConfig(
        min_sample_size=min_sample_size,
        output_directory=f"data/spc/{client}_{ref_project}",
        include_extrapolation=extrapolate,
        export_detailed_results=True,
    )

    manager = CapabilityStudyManager(config)
    results = manager.run_capability_study(
        sample_data,
        study_id=f"{client}_{ref_project}",
        interactive_extrapolation=False
    )

    return results
