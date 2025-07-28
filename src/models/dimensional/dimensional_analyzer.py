# src/models/dimensional/dimensional_analyzer.py - FIXED VERSION
import logging
from typing import List, Optional, Dict, Any
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import GDTInterpreter, create_enhanced_gdt_flags
import pandas as pd


class DimensionalAnalyzer:
    """Enhanced analyzer for dimensional measurement data with improved GD&T and nominal=0 handling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gdt_interpreter = GDTInterpreter()

    def parse_tolerances(
        self, raw_tol, description: str, nominal: float
    ) -> tuple[float, float, list[str]]:
        """Enhanced tolerance parsing with better GD&T and nominal=0 handling"""
        warnings = []
        gdt_flags = create_enhanced_gdt_flags(description)

        # Check if this is a GDT feature that should be handled differently
        is_gdt_feature = any(
            gdt_flags.get(k)
            for k in (
                "PROFILE",
                "FLATNESS",
                "CIRCULARITY",
                "PARALLELISM",
                "PERPENDICULARITY",
                "ANGULARITY",
                "CONCENTRICITY",
                "POSITION",
                "STRAIGHTNESS",
                "CYLINDRICITY",
                "RUNOUT",
                "TOTAL_RUNOUT",
                "SYMMETRY",
            )
        )

        # Check if this is an informative/reference measurement
        is_informative = self._is_informative_measurement(description)

        # Attempt to derive from GD&T if no usable tolerance provided
        if not raw_tol or (isinstance(raw_tol, list) and len(raw_tol) == 0):
            tol_list, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(
                description, nominal
            )
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
                    warnings.append(
                        "GD&T tolerance could not be extracted - using default evaluation"
                    )
                    # For GDT features with nominal=0, use a reasonable default
                    if nominal == 0:
                        return (
                            0.0,
                            0.1,
                            warnings,
                        )  # Allow 0.1 deviation for unspecified GDT
                    else:
                        return (
                            -0.1,
                            0.1,
                            warnings,
                        )  # Symmetric tolerance for unspecified GDT
                else:
                    return 0.0, 0.0, gdt_warnings

        lower_tol, upper_tol = 0.0, 0.0

        try:
            if isinstance(raw_tol, list):
                if len(raw_tol) == 2:
                    lower_tol, upper_tol = float(raw_tol[0]), float(raw_tol[1])
                elif len(raw_tol) == 1:
                    t = float(raw_tol[0])
                    lower_tol, upper_tol = self._handle_single_tolerance(
                        t, gdt_flags, warnings
                    )
                else:
                    warnings.append(
                        "Invalid tolerance list format - using zero tolerance"
                    )

            elif isinstance(raw_tol, (int, float)):
                t = float(raw_tol)
                lower_tol, upper_tol = self._handle_single_tolerance(
                    t, gdt_flags, warnings
                )

            elif isinstance(raw_tol, str):
                try:
                    t = float(raw_tol)
                    lower_tol, upper_tol = self._handle_single_tolerance(
                        t, gdt_flags, warnings
                    )
                except ValueError:
                    if "/" in raw_tol:
                        parts = raw_tol.replace("+", "").split("/")
                        if len(parts) == 2:
                            try:
                                upper_tol = float(parts[0])
                                lower_tol = -float(
                                    parts[1]
                                )  # Make negative for lower tolerance
                            except ValueError:
                                warnings.append(
                                    "Could not parse tolerance string values"
                                )
                        else:
                            warnings.append("Could not parse tolerance string format")
                    elif "±" in raw_tol or "+/-" in raw_tol:
                        # Handle symmetric tolerance notation
                        try:
                            tol_val = float(
                                raw_tol.replace("±", "").replace("+/-", "").strip()
                            )
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
        if any(
            gdt_flags.get(k)
            for k in ("MMC", "LMC", "PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")
        ):
            if lower_tol > 0:
                lower_tol = -abs(lower_tol)
            upper_tol = abs(upper_tol)

        return lower_tol, upper_tol, warnings

    def _handle_single_tolerance(
        self, t: float, gdt_flags: Dict[str, bool], warnings: List[str]
    ) -> tuple[float, float]:
        """Enhanced single tolerance handling"""
        if (
            gdt_flags.get("MIN")
            or gdt_flags.get("MMC")
            or gdt_flags.get("LMC")
            or gdt_flags.get("PROFILE")
        ):
            return 0.0, abs(t)
        elif gdt_flags.get("MAX"):
            return -abs(t), 0.0
        elif any(
            gdt_flags.get(k)
            for k in (
                "FLATNESS",
                "CIRCULARITY",
                "CYLINDRICITY",
                "STRAIGHTNESS",
                "RUNOUT",
            )
        ):
            # Form and runout tolerances are typically unilateral positive
            return 0.0, abs(t)
        else:
            warnings.append("Single tolerance interpreted as symmetric bilateral.")
            return -abs(t), abs(t)

    def _is_informative_measurement(self, description: str) -> bool:
        """Check if measurement is informative/reference only"""
        informative_keywords = [
            "note",
            "ref",
            "reference",
            "informative",
            "typical",
            "typ",
            "approx",
            "approximately",
            "nominal",
            "basic",
            "info",
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

        if (
            (gdt_flags.get("MMC") or gdt_flags.get("LMC"))
            and datum_nominal is not None
            and datum_measurement is not None
        ):
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

    def analyze_row(self, record: Dict[str, Any]) -> DimensionalResult:
        """
        COMPLETELY FIXED analyze_row with proper measurements, tolerances, and statistics
        """
        try:
            element_id = str(record.get("element_id", "Unknown"))
            batch = str(record.get("batch", "Unknown"))
            cavity = str(record.get("cavity", "Unknown"))
            classe = str(record.get("class", "Unknown"))
            description = str(record.get("description", ""))

            self.logger.debug(f"🔧 ANALYZER: Processing {element_id}")

            # Handle evaluation_type for Notes
            evaluation_type = record.get("evaluation_type", "Normal")
            is_note = evaluation_type == "Note"
            self.logger.debug(f"🔧 {element_id}: is_note = {is_note}")

            # Handle nominal value
            try:
                nominal = float(record["nominal"]) if pd.notna(record.get("nominal")) else 0.0
            except (ValueError, TypeError, KeyError):
                if not is_note:
                    return self._create_error_result(record, "Invalid or missing nominal value")
                nominal = 0.0

            self.logger.debug(f"🔧 {element_id}: nominal = {nominal}")

            # Handle measurements - extract from record
            measurements = record.get("measurements", [])
            if not isinstance(measurements, list):
                measurements = []
            
            # Ensure all measurements are floats
            valid_measurements = []
            for i, m in enumerate(measurements):
                if pd.notna(m):
                    try:
                        valid_measurements.append(float(m))
                        self.logger.debug(f"🔧 {element_id}: measurement_{i+1} = {float(m)}")
                    except (ValueError, TypeError):
                        self.logger.warning(f"❌ {element_id}: Invalid measurement at position {i}: {m}")
                        continue

            measurements = valid_measurements
            self.logger.debug(f"🔧 {element_id}: Final measurements = {measurements}")

            # For Notes, measurements are optional
            if not is_note and not measurements:
                return self._create_error_result(record, "No valid measurements provided")

            # Calculate deviations
            deviation = [m - nominal for m in measurements] if measurements else []
            self.logger.debug(f"🔧 {element_id}: deviations = {deviation}")

            # Handle tolerances
            lower_tol = 0.0
            upper_tol = 0.0
            tol_warnings = []

            # Get tolerance values from record
            raw_lower_tol = record.get("lower_tolerance")
            raw_upper_tol = record.get("upper_tolerance")

            self.logger.debug(f"🔧 {element_id}: raw_lower_tol = {raw_lower_tol}")
            self.logger.debug(f"🔧 {element_id}: raw_upper_tol = {raw_upper_tol}")

            # Parse tolerances
            try:
                if pd.notna(raw_lower_tol):
                    lower_tol = float(raw_lower_tol)
                if pd.notna(raw_upper_tol):
                    upper_tol = float(raw_upper_tol)
            except (ValueError, TypeError) as e:
                if not is_note:
                    tol_warnings.append(f"Invalid tolerance values: {str(e)}")

            self.logger.debug(f"🔧 {element_id}: parsed tolerances = [{lower_tol}, {upper_tol}]")

            # Try to extract from GD&T if no tolerances provided
            if lower_tol == 0.0 and upper_tol == 0.0 and description:
                try:
                    gdt_tolerance, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                    if gdt_tolerance and len(gdt_tolerance) >= 2:
                        lower_tol = float(gdt_tolerance[0])
                        upper_tol = float(gdt_tolerance[1])
                        tol_warnings.extend(gdt_warnings)
                        self.logger.debug(f"🔧 {element_id}: GD&T tolerances = [{lower_tol}, {upper_tol}]")
                except Exception as e:
                    self.logger.warning(f"❌ {element_id}: GD&T tolerance extraction failed: {str(e)}")

            # Create GD&T flags
            gdt_flags = create_enhanced_gdt_flags(description)

            # Handle force_status - THIS IS CRITICAL
            force_status = record.get("force_status", "AUTO")
            self.logger.debug(f"🔧 {element_id}: force_status = {force_status}")

            # Determine status based on force_status FIRST
            if force_status == "GOOD":
                status = DimensionalStatus.GOOD
                out_of_spec = []
                eval_warnings = ["Status set to GOOD by user"]
                self.logger.debug(f"🔧 {element_id}: Status forced to GOOD")
            elif force_status == "BAD":
                status = DimensionalStatus.BAD
                out_of_spec = measurements.copy()  # All measurements considered out of spec
                eval_warnings = ["Status forced to BAD"]
                self.logger.debug(f"🔧 {element_id}: Status forced to BAD")
            else:  # AUTO evaluation
                if is_note:
                    # Notes default to GOOD when AUTO
                    status = DimensionalStatus.GOOD
                    out_of_spec = []
                    eval_warnings = ["Note entry - defaulted to GOOD"]
                    self.logger.debug(f"🔧 {element_id}: Note entry, status = GOOD")
                elif measurements:
                    # Enhanced tolerance evaluation with GD&T support
                    if lower_tol == 0.0 and upper_tol == 0.0:
                        # Check if this is a GD&T feature that should still be evaluated
                        is_gdt_feature = any(gdt_flags.get(k) for k in ["POSITION", "FLATNESS", "CIRCULARITY", 
                                                                       "PARALLELISM", "PERPENDICULARITY", "ANGULARITY", 
                                                                       "CONCENTRICITY", "PROFILE", "STRAIGHTNESS", 
                                                                       "CYLINDRICITY", "RUNOUT", "TOTAL_RUNOUT"])
                        
                        if is_gdt_feature and nominal == 0.0:
                            # Special handling for GD&T features with nominal=0
                            # These measure deviation from theoretical exact (position) or perfect form (flatness)
                            self.logger.debug(f"🔧 {element_id}: GD&T feature with nominal=0 detected")
                            
                            # Try to extract tolerance from description
                            try:
                                gdt_tolerance, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                                if gdt_tolerance and len(gdt_tolerance) >= 2:
                                    gdt_lower = float(gdt_tolerance[0])
                                    gdt_upper = float(gdt_tolerance[1])
                                    
                                    self.logger.debug(f"🔧 {element_id}: Extracted GD&T tolerance = [{gdt_lower}, {gdt_upper}]")
                                    
                                    # For nominal=0 GD&T features, check absolute values against upper limit
                                    if gdt_flags.get("POSITION"):
                                        # Position: check if deviation is within tolerance zone
                                        out_of_spec = [m for m in measurements if abs(m) > gdt_upper]
                                    elif gdt_flags.get("FLATNESS") or gdt_flags.get("STRAIGHTNESS"):
                                        # Form tolerances: always positive deviation from perfect form
                                        out_of_spec = [m for m in measurements if m < 0 or m > gdt_upper]
                                    else:
                                        # Other GD&T: bilateral tolerance
                                        out_of_spec = [m for m in measurements if not (gdt_lower <= m <= gdt_upper)]
                                    
                                    status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD
                                    eval_warnings = [f"GD&T evaluation with tolerance [{gdt_lower}, {gdt_upper}]"]
                                    
                                    # Update tolerance values for result
                                    lower_tol = gdt_lower
                                    upper_tol = gdt_upper
                                    
                                    self.logger.debug(f"🔧 {element_id}: GD&T evaluation - {len(out_of_spec)} out of spec")
                                else:
                                    # GD&T feature but no extractable tolerance
                                    status = DimensionalStatus.GOOD
                                    out_of_spec = []
                                    eval_warnings = ["GD&T feature detected but tolerance not extractable - defaulted to GOOD"]
                                    self.logger.debug(f"🔧 {element_id}: GD&T feature, no extractable tolerance")
                            except Exception as e:
                                self.logger.warning(f"❌ {element_id}: Error extracting GD&T tolerance: {str(e)}")
                                status = DimensionalStatus.GOOD
                                out_of_spec = []
                                eval_warnings = ["GD&T tolerance extraction failed - defaulted to GOOD"]
                        else:
                            # No tolerance provided - informative measurement
                            status = DimensionalStatus.GOOD
                            out_of_spec = []
                            eval_warnings = ["No tolerance provided - informative measurement"]
                            self.logger.debug(f"🔧 {element_id}: No tolerance, status = GOOD (informative)")
                    else:
                        # Standard tolerance evaluation
                        lower_limit = nominal + lower_tol
                        upper_limit = nominal + upper_tol
                        
                        self.logger.debug(f"🔧 {element_id}: limits = [{lower_limit}, {upper_limit}]")
                        
                        # Special handling for nominal=0 with explicit tolerances
                        if nominal == 0.0 and lower_tol == 0.0 and upper_tol > 0.0:
                            # Unilateral positive tolerance for nominal=0 (common for GD&T form tolerances)
                            out_of_spec = [m for m in measurements if m < 0 or m > upper_tol]
                            self.logger.debug(f"🔧 {element_id}: Nominal=0 unilateral evaluation")
                        elif nominal == 0.0 and lower_tol < 0.0 and upper_tol > 0.0:
                            # Bilateral tolerance for nominal=0 (common for position tolerances)
                            out_of_spec = [m for m in measurements if abs(m) > max(abs(lower_tol), abs(upper_tol))]
                            self.logger.debug(f"🔧 {element_id}: Nominal=0 bilateral evaluation")
                        else:
                            # Standard bilateral tolerance check
                            out_of_spec = []
                            for i, m in enumerate(measurements):
                                if not (lower_limit <= m <= upper_limit):
                                    out_of_spec.append(m)
                                    self.logger.debug(f"❌ {element_id}: measurement_{i+1} = {m} OUT OF SPEC")
                                else:
                                    self.logger.debug(f"✅ {element_id}: measurement_{i+1} = {m} OK")
                        
                        status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD
                        eval_warnings = []
                        
                        self.logger.debug(f"🔧 {element_id}: {len(out_of_spec)} out of {len(measurements)} out of spec")
                        self.logger.debug(f"🔧 {element_id}: Final status = {status.value}")
                else:
                    # No measurements to evaluate
                    status = DimensionalStatus.GOOD
                    out_of_spec = []
                    eval_warnings = ["No measurements to evaluate"]
                    self.logger.debug(f"🔧 {element_id}: No measurements, status = GOOD")

            # Calculate statistics
            if measurements:
                avg = mean(measurements)
                sd = stdev(measurements) if len(measurements) > 1 else 0.0
            else:
                avg = 0.0
                sd = 0.0

            self.logger.debug(f"🔧 {element_id}: Statistics - mean = {avg}, std = {sd}")

            # Determine feature type
            feature_type = self._determine_feature_type(description)

            # Compile warnings
            warnings = tol_warnings + eval_warnings

            # Add measurement count warnings (skip for Notes)
            if not is_note and measurements:
                if len(measurements) < 5:
                    warnings.append(f"Only {len(measurements)} measurements provided; 5+ recommended.")
                if len(measurements) == 1:
                    warnings.append("Only 1 measurement - no statistical analysis possible.")

            # Create result
            result = DimensionalResult(
                element_id=element_id,
                batch=batch,
                cavity=cavity,
                classe=classe,
                description=description,
                nominal=nominal,
                lower_tolerance=lower_tol if lower_tol != 0.0 else None,
                upper_tolerance=upper_tol if upper_tol != 0.0 else None,
                measurements=measurements,
                deviation=deviation,
                mean=avg,
                std_dev=sd,
                out_of_spec_count=len(out_of_spec),
                status=status,
                gdt_flags=gdt_flags,
                datum_element_id=record.get("datum_element_id"),
                effective_tolerance_upper=upper_tol if upper_tol != 0.0 else None,
                effective_tolerance_lower=lower_tol if lower_tol != 0.0 else None,
                feature_type=feature_type,
                warnings=warnings,
            )

            self.logger.debug(f"✅ {element_id}: Analysis complete - Status: {result.status.value}")
            return result

        except Exception as e:
            self.logger.error(f"❌ ANALYZER ERROR for element {record.get('element_id', 'Unknown')}: {str(e)}")
            self.logger.error("❌ Full exception:", exc_info=True)
            return self._create_error_result(record, f"Analysis error: {str(e)}")

    def _determine_feature_type(self, description: str) -> str:
        """
        Determine feature type from description
        """
        if not description:
            return "dimension"
            
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
            "angle": ["angle", "angular", "degree", "°", "º"],
            "radius": ["radius", "rad", "r="],
            "chamfer": ["chamfer", "bevel"],
            "fillet": ["fillet", "round"],
            "thread": ["thread", "screw", "bolt"],
            "flatness": ["flatness"],
            "position": ["position"],
        }

        for feature_type, keywords in feature_mappings.items():
            if any(keyword in desc_lower for keyword in keywords):
                return feature_type

        return "dimension"  # Default fallback

    def _create_error_result(self, record: Dict[str, Any], error_message: str) -> DimensionalResult:
        """Create a result object for error cases"""
        return DimensionalResult(
            element_id=str(record.get("element_id", "Unknown")),
            batch=str(record.get("batch", "Unknown")),
            cavity=str(record.get("cavity", "Unknown")),
            classe=str(record.get("class", "Unknown")),
            description=str(record.get("description", "")),
            nominal=float(record.get("nominal", 0.0)) if pd.notna(record.get("nominal")) else 0.0,
            lower_tolerance=None,
            upper_tolerance=None,
            measurements=[],
            deviation=[],
            mean=0.0,
            std_dev=0.0,
            out_of_spec_count=0,
            status=DimensionalStatus.BAD,
            gdt_flags={},
            datum_element_id=record.get("datum_element_id"),
            effective_tolerance_upper=None,
            effective_tolerance_lower=None,
            feature_type=self._determine_feature_type(record.get("description", "")),
            warnings=[error_message],
        )
