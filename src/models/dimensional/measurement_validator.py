# models/dimensional/measurement_validator.py

from typing import Tuple, List
from math import isnan, isinf

def validate_measurements(row: dict) -> Tuple[bool, List[str]]:
    warnings = []
    try:
        measurements = row.get("measurements")
        if not isinstance(measurements, list):
            return False, ["Measurements must be a list."]
        if len(measurements) < 1:
            return False, ["No measurements provided."]

        floats = []
        for m in measurements:
            val = float(m)
            if isnan(val) or isinf(val):
                return False, [f"Invalid measurement value: {m}"]
            floats.append(val)

        unique_vals = set(floats)
        if len(unique_vals) == 1:
            warnings.append("All measurements are identical; no variation detected.")

        if len(floats) < 5:
            warnings.append(f"Only {len(floats)} measurements provided; 5 or more recommended.")
        if len(floats) == 1:
            warnings.append("Only 1 measurement provided; dimensional analysis results may be unreliable.")

        return True, warnings

    except (ValueError, TypeError):
        return False, ["All measurements must be numeric."]

