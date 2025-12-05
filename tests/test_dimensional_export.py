import json
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer

@pytest.fixture
def sample_dimensional_rows():
    client = "ClientA"
    ref_project = "ProjX"
    batch_number = "Batch123"

    rows = [
        {
            "element_id": "E1",
            "batch": batch_number,
            "cavity": "C1",
            "description": "Diameter Ø",
            "nominal": 10.0,
            "tolerance": [0.1, 0.2],
            "measurements": [10.05, 10.1, 9.95, 10.0],
            "datum_element_id": None,
            "datum_nominal": None,
            "datum_measurement": None,
        },
        {
            "element_id": "E2",
            "batch": batch_number,
            "cavity": "C2",
            "description": "Hole MMC",
            "nominal": 8.0,
            "tolerance": [0.0, 0.2],
            "measurements": [8.1, 8.05, 8.0, 8.2],
            "datum_element_id": "D1",
            "datum_nominal": 8.0,
            "datum_measurement": 7.9,
        },
        {
            "element_id": "E3",
            "batch": batch_number,
            "cavity": "C3",
            "description": "Slot LMC",
            "nominal": 5.0,
            "tolerance": [0.0, 0.1],
            "measurements": [5.05, 5.0, 5.1, 5.08],
            "datum_element_id": "D2",
            "datum_nominal": 5.0,
            "datum_measurement": 5.2,
        },
        {
            "element_id": "E4",
            "batch": batch_number,
            "cavity": "C4",
            "description": "Pin",
            "nominal": 12.0,
            "tolerance": 0.1,
            "measurements": [11.95, 12.05, 12.0, 12.1],
            "datum_element_id": None,
            "datum_nominal": None,
            "datum_measurement": None,
        },
        {
            "element_id": "E5",
            "batch": batch_number,
            "cavity": "C5",
            "description": "Flatness PROFILE",
            "nominal": 0.0,
            "tolerance": 0.5,
            "measurements": [0.2, 0.3, 0.1, 0.4],
            "datum_element_id": None,
            "datum_nominal": None,
            "datum_measurement": None,
        },
        {
            "element_id": "E6",
            "batch": batch_number,
            "cavity": "C6",
            "description": "Slot no datum",
            "nominal": 15.0,
            "tolerance": [0.2, 0.3],
            "measurements": [15.1, 15.2, 15.3, 15.4],
            "datum_element_id": None,
            "datum_nominal": None,
            "datum_measurement": None,
        },
    ]

    return client, ref_project, batch_number, rows


def test_export_dimensional_results(sample_dimensional_rows):
    client, ref_project, batch_number, rows = sample_dimensional_rows
    analyzer = DimensionalAnalyzer()
    results = [analyzer.analyze_row(row) for row in rows]

    export_folder = Path("./data/reports/dim")
    analyzer.export_results(results, client, ref_project, batch_number, folder_path=str(export_folder))

    base_filename = f"{client}_{ref_project}_{batch_number}_dimensional_state"
    json_path = export_folder / f"{base_filename}.json"
    csv_path = export_folder / f"{base_filename}.csv"

    # Assertions
    assert json_path.exists(), f"Expected JSON file not found: {json_path}"
    assert csv_path.exists(), f"Expected CSV file not found: {csv_path}"

    # ✅ Check JSON contents
    with open(json_path, "r", encoding="utf-8") as fjson:
        json_data = json.load(fjson)
        assert len(json_data) == 6
        for entry in json_data:
            assert "element_id" in entry
            assert "measurements" in entry
            assert isinstance(entry["measurements"], list)

            # Only one true GD&T flag should be retained
            gdts = entry.get("gdt_flags", {})
            true_flags = [k for k, v in gdts.items() if v is True]
            assert len(true_flags) <= 1

    # ✅ Check CSV contents (1 header + 6 rows)
    with open(csv_path, "r", encoding="utf-8") as fcsv:
        lines = fcsv.readlines()
        assert len(lines) == 7
        assert "measurements" in lines[0]  # header check

    print(f"\n✅ JSON exported to: {json_path.resolve()}")
    print(f"✅ CSV exported to: {csv_path.resolve()}")
