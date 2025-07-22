# models/dimensional/measurement_validator.py

from typing import Tuple, List


def validate_measurements(row: dict) -> Tuple[bool, List[str]]:
    warnings = []
    try:
        measurements = row.get("measurements")
        if not isinstance(measurements, list):
            return False, ["Measurements must be a list."]
        if len(measurements) < 1:
            return False, ["No measurements provided."]

        for m in measurements:
            _ = float(m)

        if len(measurements) < 5:
            warnings.append(
                f"Only {len(measurements)} measurements provided; recommended is 5 or more."
            )
        if len(measurements) == 1:
            warnings.append(
                "Only 1 measurement provided; dimensional analysis results may be unreliable."
            )

        return True, warnings

    except (ValueError, TypeError):
        return False, ["All measurements must be convertible to float."]
