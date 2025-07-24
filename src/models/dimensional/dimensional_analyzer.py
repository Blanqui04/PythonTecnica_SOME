import logging
from typing import List, Optional, Dict
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import GDTInterpreter, create_enhanced_gdt_flags


class DimensionalAnalyzer:
    """Analyzer for dimensional measurement data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gdt_interpreter = GDTInterpreter()

    def parse_tolerances(self, raw_tol, description: str, nominal: float) -> tuple[float, float, list[str]]:
        warnings = []
        gdt_flags = create_enhanced_gdt_flags(description)

        # Attempt to derive from GD&T if no usable tolerance provided
        if not raw_tol or (isinstance(raw_tol, list) and len(raw_tol) == 0):
            tol_list, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
            if tol_list:
                return float(tol_list[0]), float(tol_list[1]), gdt_warnings
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
                            upper_tol = float(parts[0])
                            lower_tol = float(parts[1])
                        else:
                            warnings.append("Could not parse tolerance string format")
                    else:
                        warnings.append("Could not parse tolerance string")
            else:
                warnings.append("Unknown tolerance format - using zero tolerance")

        except (ValueError, TypeError) as e:
            warnings.append(f"Error parsing tolerance: {str(e)}")
            lower_tol, upper_tol = 0.0, 0.0

        if any(gdt_flags.get(k) for k in ("MMC", "LMC", "PROFILE", "FLATNESS", "CIRCULARITY", "PARALLELISM")):
            if lower_tol > 0:
                lower_tol = -abs(lower_tol)
            upper_tol = abs(upper_tol)

        return lower_tol, upper_tol, warnings

    def _handle_single_tolerance(self, t: float, gdt_flags: Dict[str, bool], warnings: List[str]) -> tuple[float, float]:
        if gdt_flags.get("MIN") or gdt_flags.get("MMC") or gdt_flags.get("LMC") or gdt_flags.get("PROFILE"):
            return 0.0, abs(t)
        elif gdt_flags.get("MAX"):
            return -abs(t), 0.0
        else:
            warnings.append("Single tolerance interpreted as symmetric bilateral.")
            return -abs(t), abs(t)

    def apply_bonus_tolerance(
        self,
        gdt_flags: Dict[str, bool],
        lower_tol: float,
        upper_tol: float,
        datum_nominal: Optional[float],
        datum_measurement: Optional[float],
    ) -> tuple[float, float]:
        effective_lower_tol = lower_tol
        effective_upper_tol = upper_tol

        if (gdt_flags.get("MMC") or gdt_flags.get("LMC")) and datum_nominal is not None and datum_measurement is not None:
            try:
                if gdt_flags.get("MMC"):
                    mmc_size = datum_nominal + (lower_tol if lower_tol < 0 else 0)
                    bonus = abs(mmc_size - datum_measurement)
                    if datum_measurement < mmc_size:
                        effective_upper_tol += bonus
                elif gdt_flags.get("LMC"):
                    lmc_size = datum_nominal + (upper_tol if upper_tol > 0 else 0)
                    bonus = abs(datum_measurement - lmc_size)
                    if datum_measurement > lmc_size:
                        effective_upper_tol += bonus
            except Exception as e:
                self.logger.warning(f"Bonus tolerance error: {str(e)}")

        return effective_lower_tol, effective_upper_tol

    def analyze_row(self, row: dict) -> DimensionalResult:
        try:
            element_id = str(row.get("element_id", "Unknown"))
            batch = str(row.get("batch", "Unknown"))
            cavity = str(row.get("cavity", "Unknown"))
            classe = str(row.get("class", "Unknown"))
            description = str(row.get("description", ""))

            try:
                nominal = float(row["nominal"])
            except (ValueError, TypeError, KeyError):
                return self._create_error_result(row, "Invalid or missing nominal value")

            measurements = row.get("measurements", [])
            if not measurements:
                return self._create_error_result(row, "No measurements provided")

            try:
                measurements = [float(m) for m in measurements if m is not None]
            except (ValueError, TypeError):
                return self._create_error_result(row, "Invalid measurement values")

            if not measurements:
                return self._create_error_result(row, "No valid measurements found")

            deviation = [m - nominal for m in measurements]
            raw_tol = row.get("tolerance", [])
            gdt_flags = create_enhanced_gdt_flags(description)

            lower_tol, upper_tol, tol_warnings = self.parse_tolerances(raw_tol, description, nominal)

            datum_element_id = row.get("datum_element_id")
            datum_nominal = row.get("datum_nominal")
            datum_measurement = row.get("datum_measurement")

            effective_lower_tol, effective_upper_tol = self.apply_bonus_tolerance(
                gdt_flags, lower_tol, upper_tol, datum_nominal, datum_measurement
            )

            lower_limit = nominal + effective_lower_tol
            upper_limit = nominal + effective_upper_tol

            out_of_spec = [m for m in measurements if not (lower_limit <= m <= upper_limit)]
            status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD

            avg = mean(measurements)
            sd = stdev(measurements) if len(measurements) > 1 else 0.0
            feature_type = self.gdt_interpreter._determine_feature_type_from_gdt(description, {})

            warnings = tol_warnings[:]

            if len(measurements) < 5:
                warnings.append(f"Only {len(measurements)} measurements provided; 5+ recommended.")

            if len(measurements) == 1:
                warnings.append("Only 1 measurement - no statistical analysis possible.")

            if len(measurements) > 1 and avg != 0:
                cv = (sd / abs(avg)) * 100
                if cv > 10:
                    warnings.append(f"High variability detected (CV = {cv:.1f}%)")

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
            self.logger.error(f"Row analysis error: {str(e)}")
            return self._create_error_result(row, f"Analysis error: {str(e)}")

    def _create_error_result(self, row: dict, error_message: str) -> DimensionalResult:
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
