# src/models/dimensional/dimensional_analyzer.py
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import parse_gdt_flags


def parse_tolerances(raw_tol, description: str) -> tuple[float, float, list[str]]:
    warnings = []
    gdt_flags = parse_gdt_flags(description)

    lower_tol, upper_tol = 0.0, 0.0

    if isinstance(raw_tol, list):
        if len(raw_tol) == 2:
            lower_tol, upper_tol = float(raw_tol[0]), float(raw_tol[1])
        elif len(raw_tol) == 1:
            t = float(raw_tol[0])
            if (
                gdt_flags.get("MIN")
                or gdt_flags.get("MMC")
                or gdt_flags.get("LMC")
                or gdt_flags.get("PROFILE")
            ):
                lower_tol = 0.0
                upper_tol = abs(t)
            elif gdt_flags.get("MAX"):
                lower_tol = abs(t)
                upper_tol = 0.0
            else:
                upper_tol = abs(t)
                lower_tol = 0.0
                warnings.append(
                    "Single tolerance value interpreted as symmetric dimensional tolerance."
                )
    elif isinstance(raw_tol, (int, float)):
        t = float(raw_tol)
        if (
            gdt_flags.get("MIN")
            or gdt_flags.get("MMC")
            or gdt_flags.get("LMC")
            or gdt_flags.get("PROFILE")
        ):
            lower_tol = 0.0
            upper_tol = abs(t)
        elif gdt_flags.get("MAX"):
            lower_tol = abs(t)
            upper_tol = 0.0
        else:
            upper_tol = abs(t)
            lower_tol = 0.0
            warnings.append(
                "Single numeric tolerance interpreted as symmetric dimensional tolerance."
            )

    # Prevent negative tolerances in GD&T cases
    if any(
        gdt_flags.get(k)
        for k in ("MMC", "LMC", "PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")
    ):
        lower_tol = max(0.0, lower_tol)
        upper_tol = max(0.0, upper_tol)

    return lower_tol, upper_tol, warnings


def apply_bonus_tolerance(
    gdt_flags, lower_tol, upper_tol, datum_nominal, datum_measurement
) -> tuple[float, float]:
    effective_lower_tol = lower_tol
    effective_upper_tol = upper_tol

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
                effective_upper_tol = upper_tol + bonus_tol

    return effective_lower_tol, effective_upper_tol


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
        gdt_flags = parse_gdt_flags(description)

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
                status=DimensionalStatus.BAD,
                gdt_flags=gdt_flags,
                datum_element_id=row.get("datum_element_id"),
                effective_tolerance_upper=None,
                effective_tolerance_lower=None,
                feature_type=None,
                warnings=["No tolerance provided"],
            )

        # Parse tolerances
        lower_tol, upper_tol, tol_warnings = parse_tolerances(raw_tol, description)

        # Effective tolerances
        datum_element_id = row.get("datum_element_id")
        datum_nominal = row.get("datum_nominal")
        datum_measurement = row.get("datum_measurement")

        effective_lower_tol, effective_upper_tol = apply_bonus_tolerance(
            gdt_flags, lower_tol, upper_tol, datum_nominal, datum_measurement
        )

        lower_limit = nominal + effective_lower_tol
        upper_limit = nominal + effective_upper_tol

        if lower_tol == 0.0 and upper_tol == 0.0:
            out_of_spec = [m for m in measurements if m != nominal]
        else:
            out_of_spec = [
                m for m in measurements if not (lower_limit <= m <= upper_limit)
            ]

        status = (
            DimensionalStatus.GOOD if len(out_of_spec) == 0 else DimensionalStatus.BAD
        )

        avg = mean(measurements) if measurements else 0.0
        sd = stdev(measurements) if len(measurements) > 1 else 0.0

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
        warnings += tol_warnings

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
