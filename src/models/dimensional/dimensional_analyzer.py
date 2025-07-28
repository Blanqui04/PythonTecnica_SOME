# src/models/dimensional/dimensional_analyzer.py - FIXED VERSION
import logging
from typing import List, Optional, Dict
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import GDTInterpreter, create_enhanced_gdt_flags


class DimensionalAnalyzer:
    """Enhanced analyzer for dimensional measurement data with improved GD&T and nominal=0 handling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gdt_interpreter = GDTInterpreter()

    def parse_tolerances(self, raw_tol, description: str, nominal: float) -> tuple[float, float, list[str]]:
        """Enhanced tolerance parsing with better GD&T and nominal=0 handling"""
        warnings = []
        gdt_flags = create_enhanced_gdt_flags(description)

        # Check if this is a GDT feature that should be handled differently
        is_gdt_feature = any(gdt_flags.get(k) for k in ("PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM", 
                                                        "PERPENDICULARITY", "ANGULARITY", "CONCENTRICITY", 
                                                        "POSITION", "STRAIGHTNESS", "CYLINDRICITY", "RUNOUT", 
                                                        "TOTAL_RUNOUT", "SYMMETRY"))

        # Check if this is an informative/reference measurement
        is_informative = self._is_informative_measurement(description)

        # Attempt to derive from GD&T if no usable tolerance provided
        if not raw_tol or (isinstance(raw_tol, list) and len(raw_tol) == 0):
            tol_list, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
            if tol_list and len(tol_list) == 2:
                return float(tol_list[0]), float(tol_list[1]), gdt_warnings
            else:
                # Enhanced fallback logic
                if is_informative:
                    warnings.extend(gdt_warnings)
                    warnings.append("Informative measurement - no tolerance evaluation")
                    return 0.0, 0.0, warnings
                elif is_gdt_feature:
                    warnings.extend(gdt_warnings)
                    warnings.append("GD&T tolerance could not be extracted - using default evaluation")
                    # For GDT features with nominal=0, use a reasonable default
                    if nominal == 0:
                        return 0.0, 0.1, warnings  # Allow 0.1 deviation for unspecified GDT
                    else:
                        return -0.1, 0.1, warnings  # Symmetric tolerance for unspecified GDT
                else:
                    return 0.0, 0.0, gdt_warnings

        lower_tol, upper_tol = 0.0, 0.0

        try:
            if isinstance(raw_tol, list):
                if len(raw_tol) == 2:
                    lower_tol, upper_tol = float(raw_tol[0]), float(raw_tol[1])
                elif len(raw_tol) == 1:
                    t = float(raw_tol[0])
                    lower_tol, upper_tol = self._handle_single_tolerance(t, gdt_flags, warnings)
                else:
                    warnings.append("Invalid tolerance list format - using zero tolerance")

            elif isinstance(raw_tol, (int, float)):
                t = float(raw_tol)
                lower_tol, upper_tol = self._handle_single_tolerance(t, gdt_flags, warnings)

            elif isinstance(raw_tol, str):
                try:
                    t = float(raw_tol)
                    lower_tol, upper_tol = self._handle_single_tolerance(t, gdt_flags, warnings)
                except ValueError:
                    if "/" in raw_tol:
                        parts = raw_tol.replace("+", "").split("/")
                        if len(parts) == 2:
                            try:
                                upper_tol = float(parts[0])
                                lower_tol = -float(parts[1])  # Make negative for lower tolerance
                            except ValueError:
                                warnings.append("Could not parse tolerance string values")
                        else:
                            warnings.append("Could not parse tolerance string format")
                    elif "±" in raw_tol or "+/-" in raw_tol:
                        # Handle symmetric tolerance notation
                        try:
                            tol_val = float(raw_tol.replace("±", "").replace("+/-", "").strip())
                            lower_tol, upper_tol = -abs(tol_val), abs(tol_val)
                        except ValueError:
                            warnings.append("Could not parse symmetric tolerance")
                    else:
                        warnings.append("Could not parse tolerance string")
            else:
                warnings.append("Unknown tolerance format - using zero tolerance")

        except (ValueError, TypeError) as e:
            warnings.append(f"Error parsing tolerance: {str(e)}")
            lower_tol, upper_tol = 0.0, 0.0

        # Enhanced GD&T tolerance adjustment
        if any(gdt_flags.get(k) for k in ("MMC", "LMC", "PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")):
            if lower_tol > 0:
                lower_tol = -abs(lower_tol)
            upper_tol = abs(upper_tol)

        return lower_tol, upper_tol, warnings

    def _handle_single_tolerance(self, t: float, gdt_flags: Dict[str, bool], warnings: List[str]) -> tuple[float, float]:
        """Enhanced single tolerance handling"""
        if gdt_flags.get("MIN") or gdt_flags.get("MMC") or gdt_flags.get("LMC") or gdt_flags.get("PROFILE"):
            return 0.0, abs(t)
        elif gdt_flags.get("MAX"):
            return -abs(t), 0.0
        elif any(gdt_flags.get(k) for k in ("FLATNESS", "CIRCULARITY", "CYLINDRICITY", "STRAIGHTNESS", "RUNOUT")):
            # Form and runout tolerances are typically unilateral positive
            return 0.0, abs(t)
        else:
            warnings.append("Single tolerance interpreted as symmetric bilateral.")
            return -abs(t), abs(t)

    def _is_informative_measurement(self, description: str) -> bool:
        """Check if measurement is informative/reference only"""
        informative_keywords = [
            "note", "ref", "reference", "informative", "typical", "typ", 
            "approx", "approximately", "nominal", "basic", "info"
        ]
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in informative_keywords)

    def apply_bonus_tolerance(
        self,
        gdt_flags: Dict[str, bool],
        lower_tol: float,
        upper_tol: float,
        datum_nominal: Optional[float],
        datum_measurement: Optional[float],
    ) -> tuple[float, float]:
        """Enhanced bonus tolerance calculation"""
        effective_lower_tol = lower_tol
        effective_upper_tol = upper_tol

        if (gdt_flags.get("MMC") or gdt_flags.get("LMC")) and datum_nominal is not None and datum_measurement is not None:
            try:
                if gdt_flags.get("MMC"):
                    # Maximum Material Condition - bonus when feature departs from MMC
                    mmc_size = datum_nominal + (lower_tol if lower_tol < 0 else 0)
                    bonus = abs(mmc_size - datum_measurement)
                    if datum_measurement < mmc_size:  # Departed from MMC
                        effective_upper_tol += bonus
                        effective_lower_tol -= bonus  # Bonus applies to both directions
                elif gdt_flags.get("LMC"):
                    # Least Material Condition - bonus when feature departs from LMC
                    lmc_size = datum_nominal + (upper_tol if upper_tol > 0 else 0)
                    bonus = abs(datum_measurement - lmc_size)
                    if datum_measurement > lmc_size:  # Departed from LMC
                        effective_upper_tol += bonus
                        effective_lower_tol -= bonus  # Bonus applies to both directions
            except Exception as e:
                self.logger.warning(f"Bonus tolerance calculation error: {str(e)}")

        return effective_lower_tol, effective_upper_tol

    def analyze_row(self, row: dict) -> DimensionalResult:
        """Enhanced row analysis with improved error handling and nominal=0 support"""
        try:
            element_id = str(row.get("element_id", "Unknown"))
            batch = str(row.get("batch", "Unknown"))
            cavity = str(row.get("cavity", "Unknown"))
            classe = str(row.get("class", "Unknown"))
            description = str(row.get("description", ""))

            # FIX: Handle evaluation_type for Notes
            evaluation_type = row.get("evaluation_type", "Normal")
            is_note = evaluation_type == "Note"

            # Enhanced nominal handling - nominal=0 is perfectly valid
            try:
                nominal = float(row["nominal"]) if row.get("nominal") is not None else 0.0
            except (ValueError, TypeError, KeyError):
                if not is_note:  # Notes don't need nominal values
                    return self._create_error_result(row, "Invalid or missing nominal value")
                nominal = 0.0

            # FIX: Handle measurements for Notes - they may not have any
            measurements = row.get("measurements", [])
            if is_note:
                # For Notes, measurements are optional
                if not measurements:
                    measurements = []
                else:
                    try:
                        measurements = [float(m) for m in measurements if m is not None and str(m).strip() != ""]
                    except (ValueError, TypeError):
                        measurements = []
            else:
                # For regular dimensions, measurements are required
                if not measurements:
                    return self._create_error_result(row, "No measurements provided")
                try:
                    measurements = [float(m) for m in measurements if m is not None and str(m).strip() != ""]
                except (ValueError, TypeError):
                    return self._create_error_result(row, "Invalid measurement values")
                if not measurements:
                    return self._create_error_result(row, "No valid measurements found")

            # FIX: Calculate deviations (handle empty measurements for Notes)
            deviation = [m - nominal for m in measurements] if measurements else []
            
            # Get tolerance information
            raw_tol = row.get("tolerance", [])
            gdt_flags = create_enhanced_gdt_flags(description)

            # Parse tolerances with enhanced logic
            lower_tol, upper_tol, tol_warnings = self.parse_tolerances(raw_tol, description, nominal)

            # FIX: Handle force_status properly
            force_status = row.get("force_status", "AUTO")

            # Check if this is an informative measurement
            is_informative = (lower_tol == 0.0 and upper_tol == 0.0 and 
                            not any(gdt_flags.get(k) for k in gdt_flags if gdt_flags.get(k))) or \
                           self._is_informative_measurement(description) or is_note

            # Get datum information for bonus tolerance calculation
            datum_element_id = row.get("datum_element_id")
            datum_nominal = row.get("datum_nominal")
            datum_measurement = row.get("datum_measurement")

            # Apply bonus tolerance
            effective_lower_tol, effective_upper_tol = self.apply_bonus_tolerance(
                gdt_flags, lower_tol, upper_tol, datum_nominal, datum_measurement
            )

            # FIX: Determine status based on force_status first
            if force_status == "GOOD":
                status = DimensionalStatus.GOOD
                out_of_spec = []
                eval_warnings = ["Status forced to GOOD"]
            elif force_status == "BAD":
                status = DimensionalStatus.BAD
                out_of_spec = measurements  # All measurements considered out of spec
                eval_warnings = ["Status forced to BAD"]
            else:  # AUTO evaluation
                # Calculate limits only if we have measurements to evaluate
                if measurements and not is_informative:
                    lower_limit = nominal + effective_lower_tol
                    upper_limit = nominal + effective_upper_tol

                    if effective_lower_tol == 0.0 and effective_upper_tol == 0.0:
                        # Zero tolerance - only exact matches pass
                        out_of_spec = [m for m in measurements if m != nominal]
                        status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD
                        eval_warnings = ["Zero tolerance - only exact nominal values acceptable"]
                    else:
                        # Standard tolerance evaluation
                        out_of_spec = [m for m in measurements if not (lower_limit <= m <= upper_limit)]
                        status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD
                        eval_warnings = []
                else:
                    # For informative measurements or notes without measurements
                    out_of_spec = []
                    status = DimensionalStatus.GOOD
                    eval_warnings = ["Informative/Note - no pass/fail evaluation"] if is_informative else []

            # FIX: Calculate statistics (handle empty measurements)
            if measurements:
                avg = mean(measurements)
                sd = stdev(measurements) if len(measurements) > 1 else 0.0
            else:
                avg = 0.0
                sd = 0.0

            feature_type = self.gdt_interpreter._determine_feature_type_from_gdt(description, gdt_flags)

            # Compile warnings
            warnings = tol_warnings + eval_warnings

            # Add measurement count warnings (skip for Notes)
            if not is_note and measurements:
                if len(measurements) < 5:
                    warnings.append(f"Only {len(measurements)} measurements provided; 5+ recommended.")

                if len(measurements) == 1:
                    warnings.append("Only 1 measurement - no statistical analysis possible.")

            # Enhanced variability analysis (only if we have multiple measurements)
            if len(measurements) > 1:
                if avg != 0:
                    cv = (sd / abs(avg)) * 100
                    if cv > 10:
                        warnings.append(f"High variability detected (CV = {cv:.1f}%)")
                else:
                    # When average is 0, use standard deviation directly as variability indicator
                    if sd > 0.05:  # Threshold for "high" absolute variability when avg=0
                        warnings.append(f"High absolute variability detected (σ = {sd:.4f}) around zero nominal")

            # Special warnings for GDT features with nominal=0
            if nominal == 0 and any(gdt_flags.get(k) for k in ("PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")):
                if not is_informative:
                    warnings.append("GD&T feature with zero nominal - verify tolerance interpretation")

            # Check for out-of-spec patterns (only if we have measurements)
            if len(out_of_spec) > 0 and len(measurements) > 1:
                if len(out_of_spec) == len(measurements):
                    warnings.append("All measurements out of specification - check setup")
                elif len(out_of_spec) / len(measurements) > 0.5:
                    warnings.append(f"{len(out_of_spec)}/{len(measurements)} measurements out of spec - process issue likely")

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
            self.logger.error(f"Row analysis error for element {row.get('element_id', 'Unknown')}: {str(e)}")
            return self._create_error_result(row, f"Analysis error: {str(e)}")

    def _create_error_result(self, row: dict, error_message: str) -> DimensionalResult:
        """Enhanced error result creation with better defaults"""
        return DimensionalResult(
            element_id=str(row.get("element_id", "Unknown")),
            batch=str(row.get("batch", "Unknown")),
            cavity=str(row.get("cavity", "Unknown")),
            classe=str(row.get("class", "Unknown")),
            description=str(row.get("description", "")),
            nominal=float(row.get("nominal", 0.0)) if row.get("nominal") is not None else 0.0,
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
            feature_type="dimension",
            warnings=[error_message],
        )