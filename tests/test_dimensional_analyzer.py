import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer


@pytest.mark.parametrize(
    "row,expected_status,description",
    [
        # ✅ GD&T positional with measurements inside [0, 0.5]
        (
            {
                "element_id": "GD1",
                "batch": "B1",
                "cavity": "C1",
                "description": "GD&T positional tolerance",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.1, 0.2, 0.3, 0.5],
            },
            "OK",
            "All measurements within GD&T range [0.0, 0.5]",
        ),
        # ✅ Boundary checks
        (
            {
                "element_id": "GD2",
                "batch": "B2",
                "cavity": "C2",
                "description": "GD&T boundary values",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.0, 0.5],
            },
            "OK",
            "Measurements at tolerance boundaries",
        ),
        # ❌ One value above upper limit
        (
            {
                "element_id": "GD3",
                "batch": "B3",
                "cavity": "C3",
                "description": "GD&T above upper limit",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.6],
            },
            "NOK",
            "Measurement above GD&T upper tolerance",
        ),
        # ❌ GD&T with zero tolerance, non-zero measurement
        (
            {
                "element_id": "GD4",
                "batch": "B4",
                "cavity": "C4",
                "description": "GD&T exact tolerance",
                "nominal": 0.0,
                "tolerance": [0.0, 0.0],
                "measurements": [0.001],
            },
            "NOK",
            "Zero tolerance: any non-nominal value is out",
        ),
        # ✅ MMC: bonus extends upper tolerance
        (
            {
                "element_id": "GD5",
                "batch": "B5",
                "cavity": "C5",
                "description": "GD&T MMC with bonus",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.6, 0.7, 0.85],
                "datum_element_id": "D1",
                "datum_nominal": 10.0,
                "datum_measurement": 9.4,  # bonus = 0.6 → 0.5 + 0.6 = 1.1 max
            },
            "OK",
            "Bonus tolerance from MMC extends upper limit",
        ),
        # ❌ MMC: measurement beyond bonus range
        (
            {
                "element_id": "GD6",
                "batch": "B6",
                "cavity": "C6",
                "description": "GD&T MMC with exceeded bonus",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [1.2, 1.0, 0.9, 1.1],
                "datum_element_id": "D2",
                "datum_nominal": 10.0,
                "datum_measurement": 9.5,  # bonus = 0.5 → extended to 1.0
            },
            "NOK",
            "Measurement beyond MMC bonus limit",
        ),
        # ✅ LMC: bonus extends upper limit
        (
            {
                "element_id": "GD7",
                "batch": "B7",
                "cavity": "C7",
                "description": "GD&T LMC with bonus",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.6],
                "datum_element_id": "D3",
                "datum_nominal": 10.0,
                "datum_measurement": 10.7,  # LMC bonus = 0.2 → upper = 0.7
            },
            "OK",
            "LMC bonus increases upper limit",
        ),
        # ❌ No datum → no bonus → out of spec
        (
            {
                "element_id": "GD8",
                "batch": "B8",
                "cavity": "C8",
                "description": "GD&T MMC without datum info",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.7],
                # No datum fields
            },
            "NOK",
            "Bonus tolerance ignored without datum",
        ),
        # ❌ Missing tolerance completely
        (
            {
                "element_id": "GD9",
                "batch": "B9",
                "cavity": "C9",
                "description": "GD&T with missing tolerance",
                "nominal": 0.0,
                "tolerance": [],
                "measurements": [0.0],
            },
            "NOK",
            "Missing tolerance treated as NOK",
        ),
        # ✅ Dimensional feature with symmetric tolerance (1 value)
        (
            {
                "element_id": "D1",
                "batch": "B10",
                "cavity": "C10",
                "description": "Simple dimensional (not GD&T)",
                "nominal": 10.0,
                "tolerance": [0.2],
                "measurements": [10.0, 10.1, 10.15],
            },
            "OK",
            "Symmetric tolerance interpreted for non-GD&T",
        ),
        # ✅ GD&T feature with single value = upper only
        (
            {
                "element_id": "GD10",
                "batch": "B11",
                "cavity": "C11",
                "description": "GD&T PROFILE with single tolerance",
                "nominal": 0.0,
                "tolerance": [0.25],
                "measurements": [0.2, 0.25],
            },
            "OK",
            "GD&T PROFILE treated with upper tolerance only",
        ),
        # ❌ GD&T single tolerance exceeded
        (
            {
                "element_id": "GD11",
                "batch": "B12",
                "cavity": "C12",
                "description": "GD&T with single value and over",
                "nominal": 0.0,
                "tolerance": [0.25],
                "measurements": [0.26],
            },
            "NOK",
            "GD&T single value exceeded",
        ),
    ],
)
def test_gdt_mmc_lmc_tolerance_handling(row, expected_status, description):
    analyzer = DimensionalAnalyzer()
    result = analyzer.analyze_row(row)

    assert result.status == expected_status, f"Status mismatch: {description}"

    # Type checks
    assert isinstance(result.nominal, float)
    assert isinstance(result.measurements, list)
    assert all(isinstance(m, float) for m in result.measurements)
    assert isinstance(result.mean, float)
    assert isinstance(result.std_dev, float)
    assert result.std_dev >= 0.0

    # Determine actual limits
    eff_lower = (
        result.effective_tolerance_lower
        if result.effective_tolerance_lower is not None
        else result.lower_tolerance
    )
    eff_upper = (
        result.effective_tolerance_upper
        if result.effective_tolerance_upper is not None
        else result.upper_tolerance
    )

    if eff_upper is not None and result.upper_tolerance is not None:
        assert eff_upper >= result.upper_tolerance
    if eff_lower is not None:
        assert eff_lower >= 0.0  # GD&T always positive lower

    lower_limit = result.nominal + eff_lower if eff_lower is not None else None
    upper_limit = result.nominal + eff_upper if eff_upper is not None else None

    if lower_limit is not None and upper_limit is not None:
        out_count = sum(m < lower_limit or m > upper_limit for m in result.measurements)
        assert out_count == result.out_of_spec_count

        if expected_status == "NOK":
            assert any(m < lower_limit or m > upper_limit for m in result.measurements)

        if expected_status == "OK":
            assert all(lower_limit <= m <= upper_limit for m in result.measurements)

    if result.lower_tolerance == 0.0 and result.upper_tolerance == 0.0:
        for m in result.measurements:
            assert m == result.nominal or abs(m - result.nominal) > 0.0

    if not row.get("tolerance"):
        assert expected_status == "NOK"

    if len(row.get("tolerance", [])) == 1:
        if any(result.gdt_flags.get(k) for k in ("MMC", "LMC", "PROFILE", "MIN")):
            assert result.lower_tolerance == 0.0
            assert result.upper_tolerance == row["tolerance"][0]
        else:
            assert result.upper_tolerance == abs(row["tolerance"][0])
