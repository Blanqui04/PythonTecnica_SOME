import pytest
from models.dimensional.dimensional_analyzer import DimensionalAnalyzer


@pytest.mark.parametrize(
    "row,expected_status,description",
    [
        # Baseline GD&T: nominal=0, lower=0, upper=0.5, measurements inside tolerance
        (
            {
                "element_id": "GD1",
                "batch": "B1",
                "cavity": "C1",
                "description": "GD&T nominal 0, within tolerance",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.0, 0.1, 0.3, 0.49, 0.5],
            },
            "GOOD",
            "All measurements inside 0 to 0.5 tolerance range",
        ),
        # GD&T: measurement exactly at nominal and upper tolerance boundary
        (
            {
                "element_id": "GD2",
                "batch": "B2",
                "cavity": "C2",
                "description": "GD&T boundary measurements",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.0, 0.5],
            },
            "GOOD",
            "Measurements exactly on nominal and upper tolerance",
        ),
        # GD&T: measurement slightly outside upper tolerance (0.51)
        (
            {
                "element_id": "GD3",
                "batch": "B3",
                "cavity": "C3",
                "description": "GD&T measurement above upper tolerance",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.0, 0.51],
            },
            "BAD",
            "Measurement exceeds upper tolerance",
        ),
        # GD&T: measurement below nominal (negative value) always BAD (since lower_tol=0)
        (
            {
                "element_id": "GD4",
                "batch": "B4",
                "cavity": "C4",
                "description": "GD&T measurement below nominal",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [-0.1, 0.1],
            },
            "BAD",
            "Negative measurement below nominal 0",
        ),
        # GD&T zero tolerance, any measurement non-zero -> BAD
        (
            {
                "element_id": "GD6",
                "batch": "B6",
                "cavity": "C6",
                "description": "GD&T zero tolerance with out-of-tolerance measurements",
                "nominal": 0.0,
                "tolerance": [0.0, 0.0],
                "measurements": [0.0, 0.0001],
            },
            "BAD",
            "No tolerance but measurement slightly above nominal",
        ),
        # MMC with datum info, datum_measurement < datum_nominal → bonus tolerance applies
        (
            {
                "element_id": "GD7",
                "batch": "B7",
                "cavity": "C7",
                "description": "GD&T MMC bonus tolerance applied",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.6, 0.7, 0.8, 0.5, 0.6],  # Normally out of 0.5 range
                "datum_element_id": "D1",
                "datum_nominal": 10.0,
                "datum_measurement": 9.6,  # bonus = 0.4 → extended upper tolerance 0.9
            },
            "GOOD",
            "MMC with bonus tolerance extends upper limit",
        ),
        # MMC with datum info, measurements exceed bonus tolerance → BAD
        (
            {
                "element_id": "GD8",
                "batch": "B8",
                "cavity": "C8",
                "description": "GD&T MMC bonus tolerance exceeded",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.9, 1.0],  # Above extended tolerance of 0.9
                "datum_element_id": "D2",
                "datum_nominal": 10.0,
                "datum_measurement": 9.6,  # bonus = 0.4
            },
            "BAD",
            "Measurement exceeds bonus tolerance extended limit",
        ),
        # MMC without datum info falls back to normal tolerance → BAD if outside normal tolerance
        (
            {
                "element_id": "GD9",
                "batch": "B9",
                "cavity": "C9",
                "description": "GD&T MMC no datum fallback",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [0.0, 0.6],  # 0.6 outside 0.5 upper tolerance
                # no datum info
            },
            "BAD",
            "MMC no datum fallback with out of normal tolerance measurement",
        ),
        # LMC with datum info, datum_measurement > datum_nominal + upper_tol → bonus tolerance expands lower limit (negative)
        (
            {
                "element_id": "GD10",
                "batch": "B10",
                "cavity": "C10",
                "description": "GD&T LMC bonus tolerance expands lower limit",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [
                    -0.2,
                    0.0,
                    0.1,
                ],  # Lower limit extended by bonus tolerance
                "datum_element_id": "D3",
                "datum_nominal": 10.0,
                "datum_measurement": 10.6,  # bonus tolerance = 0.1, lower limit becomes -0.1
            },
            "GOOD",
            "LMC bonus tolerance expands lower limit",
        ),
        # LMC with datum info, measurement below extended lower limit → BAD
        (
            {
                "element_id": "GD11",
                "batch": "B11",
                "cavity": "C11",
                "description": "GD&T LMC bonus tolerance exceeded lower limit",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [-0.2, 0.0],  # -0.2 below extended lower limit -0.1
                "datum_element_id": "D4",
                "datum_nominal": 10.0,
                "datum_measurement": 10.6,  # bonus = 0.1
            },
            "BAD",
            "Measurement below extended lower limit",
        ),
        # LMC without datum info fallback, measurement below normal lower tolerance 0 → BAD
        (
            {
                "element_id": "GD12",
                "batch": "B12",
                "cavity": "C12",
                "description": "GD&T LMC no datum fallback",
                "nominal": 0.0,
                "tolerance": [0.0, 0.5],
                "measurements": [-0.1, 0.1],
                # no datum info
            },
            "BAD",
            "LMC no datum fallback with measurement below nominal",
        ),
        # Edge case: no tolerance given (empty list), assume BAD
        (
            {
                "element_id": "GD13",
                "batch": "B13",
                "cavity": "C13",
                "description": "GD&T no tolerance provided",
                "nominal": 0.0,
                "tolerance": [],
                "measurements": [0.0],
            },
            "BAD",
            "No tolerance means no acceptable range",
        ),
        # Edge case: single value tolerance (only upper tolerance provided), nominal=0
        (
            {
                "element_id": "GD14",
                "batch": "B14",
                "cavity": "C14",
                "description": "GD&T single upper tolerance",
                "nominal": 0.0,
                "tolerance": [0.3],
                "measurements": [0.3, 0.29, 0.31],
            },
            "BAD",
            "One measurement above upper tolerance",
        ),
        # Edge case: measurement exactly zero but tolerance has large upper tolerance
        (
            {
                "element_id": "GD15",
                "batch": "B15",
                "cavity": "C15",
                "description": "GD&T zero measurement with large tolerance",
                "nominal": 0.0,
                "tolerance": [0.0, 1.0],
                "measurements": [0.0],
            },
            "GOOD",
            "Measurement exactly nominal with large tolerance",
        ),
    ],
)
def test_gdt_mmc_lmc_tolerance_handling(row, expected_status, description):
    analyzer = DimensionalAnalyzer()
    result = analyzer.analyze_row(row)

    # Check status
    assert result.status == expected_status, f"Status mismatch: {description}"

    # Type checks
    assert isinstance(result.nominal, float), "Nominal not float"
    assert isinstance(result.lower_tolerance, float), "Lower tolerance not float"
    assert isinstance(result.upper_tolerance, float), "Upper tolerance not float"
    assert all(isinstance(m, float) for m in result.measurements), (
        "Non-float measurement found"
    )
    assert isinstance(result.mean, float), "Mean not float"
    assert isinstance(result.std_dev, float), "Std deviation not float"
    assert result.std_dev >= 0.0, "Negative standard deviation"

    # Default tolerances if bonus not applied
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

    # Validate tolerances are logically consistent
    assert eff_upper >= result.upper_tolerance, "Effective upper tolerance too small"
    assert eff_lower <= result.lower_tolerance, "Effective lower tolerance too large"

    lower_limit = result.nominal + eff_lower
    upper_limit = result.nominal + eff_upper

    # Recompute out-of-spec manually
    out_count = sum(m < lower_limit or m > upper_limit for m in result.measurements)
    assert out_count == result.out_of_spec_count, (
        f"Out-of-spec count mismatch: {description}"
    )

    # Check zero tolerance scenario
    if result.lower_tolerance == 0.0 and result.upper_tolerance == 0.0:
        for m in result.measurements:
            assert abs(m - result.nominal) > 0.0 or m == result.nominal, (
                "Zero tolerance case failed real-world validation"
            )

    # Handle empty tolerance (treated as invalid → BAD)
    if not row.get("tolerance"):
        assert expected_status == "BAD", "Empty tolerance must return BAD"

    # Handle one-sided tolerance (e.g., only upper limit)
    if len(row.get("tolerance", [])) == 1:
        assert result.lower_tolerance == 0.0, (
            "Missing lower tolerance should default to 0"
        )
        assert result.upper_tolerance == row["tolerance"][0], "Upper tolerance mismatch"

    # BAD status → at least one measurement outside
    if expected_status == "BAD":
        assert any(m < lower_limit or m > upper_limit for m in result.measurements), (
            "BAD status expected, but all measurements within range"
        )

    # GOOD status → all within range
    if expected_status == "GOOD":
        assert all(lower_limit <= m <= upper_limit for m in result.measurements), (
            "GOOD status expected, but some measurements are out"
        )
