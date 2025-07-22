from statistics import mean, stdev
from .dimensional_result import DimensionalResult
from .gdt_interpreter import parse_gdt_flags


class DimensionalAnalyzer:
    def analyze_row(self, row: dict) -> DimensionalResult:
        element_id = row["element_id"]
        batch = row["batch"]
        cavity = row["cavity"]
        description = row["description"]
        nominal = float(row["nominal"])
        measurements = [float(m) for m in row["measurements"]]
        deviation = [m - nominal for m in measurements]

        raw_tol = row["tolerance"]

        # Early check for empty tolerance list - no acceptable range
        if isinstance(raw_tol, list) and len(raw_tol) == 0:
            return DimensionalResult(
                element_id=element_id,
                batch=batch,
                cavity=cavity,
                description=description,
                nominal=nominal,
                lower_tolerance=None,
                upper_tolerance=None,
                measurements=measurements,
                deviation=deviation,
                mean=mean(measurements) if measurements else 0.0,
                std_dev=stdev(measurements) if len(measurements) > 1 else 0.0,
                out_of_spec_count=len(measurements),
                status="BAD",
                gdt_flags=parse_gdt_flags(description),
                datum_element_id=row.get("datum_element_id"),
                effective_tolerance_upper=None,
                effective_tolerance_lower=None,
                feature_type=None,
                warnings=["No tolerance provided"],
            )

        lower_tol, upper_tol = 0.0, 0.0

        # Parse tolerance list or number
        if isinstance(raw_tol, list):
            if len(raw_tol) == 2:
                lower_tol, upper_tol = float(raw_tol[0]), float(raw_tol[1])
            elif len(raw_tol) == 1:
                t = float(raw_tol[0])
                lower_tol = t if t < 0 else 0.0
                upper_tol = t if t > 0 else 0.0
        elif isinstance(raw_tol, (int, float)):
            t = float(raw_tol)
            lower_tol = t if t < 0 else 0.0
            upper_tol = t if t > 0 else 0.0

        # Parse GD&T flags
        gdt_flags = parse_gdt_flags(description)

        # Override tolerance for MIN/MAX flags
        if gdt_flags.get("MIN"):
            lower_tol = 0.0
        if gdt_flags.get("MAX"):
            upper_tol = 0.0

        # Initialize effective tolerances
        effective_upper_tol = upper_tol
        effective_lower_tol = lower_tol

        # Handle MMC/LMC
        datum_element_id = row.get("datum_element_id")
        datum_nominal = row.get("datum_nominal")
        datum_measurement = row.get("datum_measurement")

        if (
            (gdt_flags.get("MMC") or gdt_flags.get("LMC"))
            and datum_nominal is not None
            and datum_measurement is not None
        ):
            if gdt_flags.get("MMC"):
                mmc_size = datum_nominal + (lower_tol if lower_tol < 0 else 0)
                bonus_tol = mmc_size - datum_measurement
                if bonus_tol > 0:
                    effective_upper_tol = upper_tol + bonus_tol

            elif gdt_flags.get("LMC"):
                lmc_size = datum_nominal + (upper_tol if upper_tol > 0 else 0)
                bonus_tol = datum_measurement - lmc_size
                if bonus_tol > 0:
                    # Apply bonus to lower_tol (extend downward), never above 0
                    effective_lower_tol = lower_tol + bonus_tol
                    effective_lower_tol = min(effective_lower_tol, 0.0)

        # Determine spec limits
        lower_limit = nominal + effective_lower_tol
        upper_limit = nominal + effective_upper_tol

        # If both tolerances are zero, enforce exact match
        if lower_tol == 0.0 and upper_tol == 0.0:
            out_of_spec = [m for m in measurements if m != nominal]
        else:
            out_of_spec = [
                m for m in measurements if not (lower_limit <= m <= upper_limit)
            ]

        status = "GOOD" if len(out_of_spec) == 0 else "BAD"

        # Compute statistics
        avg = mean(measurements) if measurements else 0.0
        sd = stdev(measurements) if len(measurements) > 1 else 0.0

        # Infer feature type
        desc_lower = description.lower()
        if any(k in desc_lower for k in ["diam", "ø", "circle", "dia"]):
            feature_type = "diameter"
        elif any(k in desc_lower for k in ["hole", "bore"]):
            feature_type = "hole"
        elif any(k in desc_lower for k in ["slot", "ranura", "groove"]):
            feature_type = "slot"
        elif "pin" in desc_lower:
            feature_type = "pin"
        else:
            feature_type = "pin"

        warnings = []
        if len(measurements) < 5:
            warnings.append(
                f"WARNING: Only {len(measurements)} measurements provided; 5 or more recommended."
            )
        if len(measurements) == 1:
            warnings.append(
                "WARNING: Only 1 measurement provided; results may be unreliable."
            )

        return DimensionalResult(
            element_id=element_id,
            batch=batch,
            cavity=cavity,
            description=description,
            nominal=nominal,
            lower_tolerance=lower_tol,
            upper_tolerance=upper_tol,
            measurements=measurements,
            deviation=deviation,
            mean=avg,
            std_dev=sd,
            out_of_spec_count=len(out_of_spec),
            status=status,
            gdt_flags=gdt_flags,
            datum_element_id=datum_element_id,
            effective_tolerance_upper=effective_upper_tol,
            effective_tolerance_lower=effective_lower_tol,
            feature_type=feature_type,
            warnings=warnings,
        )
