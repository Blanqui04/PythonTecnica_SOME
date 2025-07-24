# src/models/dimensional/dimensional_analyzer.py
import logging
from typing import List, Optional, Dict
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import parse_gdt_flags


def parse_tolerances(raw_tol, description: str) -> tuple[float, float, list[str]]:
    """
    Parse tolerance values from various input formats

    Args:
        raw_tol: Tolerance data (can be list, float, int, or string)
        description: Element description for GDT interpretation

    Returns:
        Tuple of (lower_tolerance, upper_tolerance, warnings)
    """
    warnings = []
    gdt_flags = parse_gdt_flags(description)
    logger = logging.getLogger(__name__)

    lower_tol, upper_tol = 0.0, 0.0

    try:
        if isinstance(raw_tol, list):
            if len(raw_tol) == 2:
                lower_tol, upper_tol = float(raw_tol[0]), float(raw_tol[1])
            elif len(raw_tol) == 1:
                t = float(raw_tol[0])
                lower_tol, upper_tol = _handle_single_tolerance(t, gdt_flags, warnings)
            else:
                warnings.append("Invalid tolerance list format - using zero tolerance")
                logger.warning(f"Invalid tolerance list length: {len(raw_tol)}")

        elif isinstance(raw_tol, (int, float)):
            t = float(raw_tol)
            lower_tol, upper_tol = _handle_single_tolerance(t, gdt_flags, warnings)

        elif isinstance(raw_tol, str):
            try:
                # Try to parse as single number
                t = float(raw_tol)
                lower_tol, upper_tol = _handle_single_tolerance(t, gdt_flags, warnings)
            except ValueError:
                # Try to parse as range (e.g., "+0.1/-0.05")
                if "/" in raw_tol:
                    parts = raw_tol.replace("+", "").split("/")
                    if len(parts) == 2:
                        upper_tol = float(parts[0])
                        lower_tol = float(parts[1])
                    else:
                        warnings.append("Could not parse tolerance string format")
                        logger.warning(f"Invalid tolerance string format: {raw_tol}")
                else:
                    warnings.append("Could not parse tolerance string")
                    logger.warning(f"Could not parse tolerance string: {raw_tol}")
        else:
            warnings.append("Unknown tolerance format - using zero tolerance")
            logger.warning(f"Unknown tolerance type: {type(raw_tol)}")

    except (ValueError, TypeError) as e:
        warnings.append(f"Error parsing tolerance: {str(e)}")
        logger.error(f"Tolerance parsing error: {str(e)}")
        lower_tol, upper_tol = 0.0, 0.0

    # Prevent negative tolerances in GD&T cases where they don't make sense
    if any(
        gdt_flags.get(k)
        for k in ("MMC", "LMC", "PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")
    ):
        if lower_tol > 0:
            lower_tol = -abs(lower_tol)  # Make sure lower tolerance is negative
        upper_tol = abs(upper_tol)  # Make sure upper tolerance is positive

    return lower_tol, upper_tol, warnings


def _handle_single_tolerance(
    t: float, gdt_flags: Dict[str, bool], warnings: List[str]
) -> tuple[float, float]:
    """Handle single tolerance value based on GDT flags"""
    if (
        gdt_flags.get("MIN")
        or gdt_flags.get("MMC")
        or gdt_flags.get("LMC")
        or gdt_flags.get("PROFILE")
    ):
        # Unilateral tolerance (only positive)
        lower_tol = 0.0
        upper_tol = abs(t)
    elif gdt_flags.get("MAX"):
        # Unilateral tolerance (only negative)
        lower_tol = -abs(t)
        upper_tol = 0.0
    else:
        # Bilateral tolerance (symmetric)
        upper_tol = abs(t)
        lower_tol = -abs(t)
        warnings.append(
            "Single tolerance value interpreted as symmetric bilateral tolerance."
        )

    return lower_tol, upper_tol


def apply_bonus_tolerance(
    gdt_flags: Dict[str, bool],
    lower_tol: float,
    upper_tol: float,
    datum_nominal: Optional[float],
    datum_measurement: Optional[float],
) -> tuple[float, float]:
    """
    Apply bonus tolerance for MMC/LMC conditions

    Args:
        gdt_flags: Dictionary of GDT flags
        lower_tol: Lower tolerance value
        upper_tol: Upper tolerance value
        datum_nominal: Nominal value of datum feature
        datum_measurement: Actual measurement of datum feature

    Returns:
        Tuple of (effective_lower_tolerance, effective_upper_tolerance)
    """
    effective_lower_tol = lower_tol
    effective_upper_tol = upper_tol

    if (
        (gdt_flags.get("MMC") or gdt_flags.get("LMC"))
        and datum_nominal is not None
        and datum_measurement is not None
    ):
        try:
            if gdt_flags.get("MMC"):
                # Maximum Material Condition
                mmc_size = datum_nominal + (lower_tol if lower_tol < 0 else 0)
                bonus_tol = abs(mmc_size - datum_measurement)
                if datum_measurement < mmc_size:  # Material condition allows bonus
                    effective_upper_tol = upper_tol + bonus_tol

            elif gdt_flags.get("LMC"):
                # Least Material Condition
                lmc_size = datum_nominal + (upper_tol if upper_tol > 0 else 0)
                bonus_tol = abs(datum_measurement - lmc_size)
                if datum_measurement > lmc_size:  # Material condition allows bonus
                    effective_upper_tol = upper_tol + bonus_tol

        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Error calculating bonus tolerance: {str(e)}"
            )

    return effective_lower_tol, effective_upper_tol


class DimensionalAnalyzer:
    """Analyzer for dimensional measurement data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_row(self, row: dict) -> DimensionalResult:
        """
        Analyze a single measurement row

        Args:
            row: Dictionary containing measurement data

        Returns:
            DimensionalResult object
        """
        try:
            # Extract basic information
            element_id = str(row.get("element_id", "Unknown"))
            batch = str(row.get("batch", "Unknown"))
            cavity = str(row.get("cavity", "Unknown"))
            classe = str(row.get("class", "Unknown"))
            description = str(row.get("description", ""))

            # Convert nominal to float
            try:
                nominal = float(row["nominal"])
            except (ValueError, TypeError, KeyError):
                return self._create_error_result(
                    row, "Invalid or missing nominal value"
                )

            # Extract measurements
            measurements = row.get("measurements", [])
            if not measurements:
                return self._create_error_result(row, "No measurements provided")

            # Ensure all measurements are floats
            try:
                measurements = [float(m) for m in measurements if m is not None]
            except (ValueError, TypeError):
                return self._create_error_result(row, "Invalid measurement values")

            if not measurements:
                return self._create_error_result(row, "No valid measurements found")

            # Calculate deviations
            deviation = [m - nominal for m in measurements]

            # Parse tolerances
            raw_tol = row.get("tolerance", [])
            gdt_flags = parse_gdt_flags(description)

            # Handle missing tolerance
            if not raw_tol or (isinstance(raw_tol, list) and len(raw_tol) == 0):
                return self._create_no_tolerance_result(
                    row, measurements, deviation, gdt_flags
                )

            # Parse tolerances
            lower_tol, upper_tol, tol_warnings = parse_tolerances(raw_tol, description)

            # Apply bonus tolerance if applicable
            datum_element_id = row.get("datum_element_id")
            datum_nominal = row.get("datum_nominal")
            datum_measurement = row.get("datum_measurement")

            effective_lower_tol, effective_upper_tol = apply_bonus_tolerance(
                gdt_flags, lower_tol, upper_tol, datum_nominal, datum_measurement
            )

            # Calculate limits
            lower_limit = nominal + effective_lower_tol
            upper_limit = nominal + effective_upper_tol

            # Check measurements against limits
            if lower_tol == 0.0 and upper_tol == 0.0:
                # Exact match required
                out_of_spec = [m for m in measurements if abs(m - nominal) > 1e-6]
            else:
                # Normal tolerance check
                out_of_spec = [
                    m for m in measurements if not (lower_limit <= m <= upper_limit)
                ]

            # Determine status
            status = (
                DimensionalStatus.GOOD
                if len(out_of_spec) == 0
                else DimensionalStatus.BAD
            )

            # Calculate statistics
            avg = mean(measurements)
            sd = stdev(measurements) if len(measurements) > 1 else 0.0

            # Determine feature type
            feature_type = self._determine_feature_type(description)

            # Generate warnings
            warnings = []
            warnings.extend(tol_warnings)

            if len(measurements) < 5:
                warnings.append(
                    f"Only {len(measurements)} measurements provided; 5 or more recommended for statistical validity."
                )

            if len(measurements) == 1:
                warnings.append(
                    "Only 1 measurement provided; statistical analysis not possible."
                )

            # Check for measurement consistency
            if len(measurements) > 1:
                cv = (sd / abs(avg)) * 100 if avg != 0 else 0
                if cv > 10:  # Coefficient of variation > 10%
                    warnings.append(
                        f"High measurement variability detected (CV = {cv:.1f}%)"
                    )

            # Check if measurements are clustered at limits
            if measurements:
                near_lower = sum(
                    1
                    for m in measurements
                    if abs(m - lower_limit) < abs(upper_tol - lower_tol) * 0.1
                )
                near_upper = sum(
                    1
                    for m in measurements
                    if abs(m - upper_limit) < abs(upper_tol - lower_tol) * 0.1
                )

                if near_lower > len(measurements) * 0.5:
                    warnings.append(
                        "Many measurements near lower limit - process may be marginal"
                    )
                elif near_upper > len(measurements) * 0.5:
                    warnings.append(
                        "Many measurements near upper limit - process may be marginal"
                    )

            return DimensionalResult(
                element_id=element_id,
                batch=batch,
                cavity=cavity,
                classe=classe,
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

        except Exception as e:
            self.logger.error(
                f"Error analyzing row for element {row.get('element_id', 'Unknown')}: {str(e)}"
            )
            return self._create_error_result(row, f"Analysis error: {str(e)}")

    def _create_error_result(self, row: dict, error_message: str) -> DimensionalResult:
        """Create a result object for error cases"""
        return DimensionalResult(
            element_id=str(row.get("element_id", "Unknown")),
            batch=str(row.get("batch", "Unknown")),
            cavity=str(row.get("cavity", "Unknown")),
            classe=str(row.get("class", "Unknown")),
            description=str(row.get("description", "")),
            nominal=float(row.get("nominal", 0.0))
            if row.get("nominal") is not None
            else 0.0,
            lower_tolerance=None,
            upper_tolerance=None,
            measurements=[],
            deviation=[],
            mean=0.0,
            std_dev=0.0,
            out_of_spec_count=0,
            status=DimensionalStatus.BAD,
            gdt_flags={},
            datum_element_id=row.get("datum_element_id"),
            effective_tolerance_upper=None,
            effective_tolerance_lower=None,
            feature_type=self._determine_feature_type(row.get("description", "")),
            warnings=[error_message],
        )

    def _create_no_tolerance_result(
        self,
        row: dict,
        measurements: List[float],
        deviation: List[float],
        gdt_flags: dict,
    ) -> DimensionalResult:
        """Create a result object when no tolerance is provided"""
        nominal = float(row.get("nominal", 0.0))

        return DimensionalResult(
            element_id=str(row.get("element_id", "Unknown")),
            batch=str(row.get("batch", "Unknown")),
            cavity=str(row.get("cavity", "Unknown")),
            classe=str(row.get("class", "Unknown")),
            description=str(row.get("description", "")),
            nominal=nominal,
            lower_tolerance=None,
            upper_tolerance=None,
            measurements=measurements,
            deviation=deviation,
            mean=mean(measurements) if measurements else 0.0,
            std_dev=stdev(measurements) if len(measurements) > 1 else 0.0,
            out_of_spec_count=len(
                measurements
            ),  # All considered out of spec without tolerance
            status=DimensionalStatus.BAD,
            gdt_flags=gdt_flags,
            datum_element_id=row.get("datum_element_id"),
            effective_tolerance_upper=None,
            effective_tolerance_lower=None,
            feature_type=self._determine_feature_type(row.get("description", "")),
            warnings=["No tolerance provided - cannot determine compliance"],
        )

    def _determine_feature_type(self, description: str) -> str:
        """
        Determine feature type from description

        Args:
            description: Feature description string

        Returns:
            Feature type string
        """
        desc_lower = description.lower()

        # Define feature type mappings
        feature_mappings = {
            "diameter": ["diam", "ø", "circle", "dia", "diameter"],
            "hole": ["hole", "bore", "orifice"],
            "slot": ["slot", "ranura", "groove", "channel"],
            "pin": ["pin", "shaft", "rod"],
            "length": ["length", "distance", "spacing"],
            "width": ["width", "breadth"],
            "height": ["height", "depth", "thickness"],
            "angle": ["angle", "angular", "degree", "°"],
            "radius": ["radius", "rad", "r="],
            "chamfer": ["chamfer", "bevel"],
            "fillet": ["fillet", "round"],
            "thread": ["thread", "screw", "bolt"],
        }

        for feature_type, keywords in feature_mappings.items():
            if any(keyword in desc_lower for keyword in keywords):
                return feature_type

        return "dimension"  # Default fallback
