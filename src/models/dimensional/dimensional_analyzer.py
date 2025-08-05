# src/models/dimensional/dimensional_analyzer.py - OPTIMIZED VERSION WITH PROCESS CAPABILITY
import logging
from typing import List, Dict, Any
from statistics import mean, stdev
from .dimensional_result import DimensionalResult, DimensionalStatus
from .gdt_interpreter import GDTInterpreter, create_enhanced_gdt_flags
import pandas as pd


class DimensionalAnalyzer:
    """Optimized analyzer for dimensional measurement data with process capability"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)  # Only errors
        self.gdt_interpreter = GDTInterpreter()

    def analyze_row(self, record: Dict[str, Any]) -> DimensionalResult:
        """Optimized row analysis with evaluation type support and process capability"""
        try:
            # Extract basic info
            element_id = str(record.get("element_id", "Unknown"))
            batch = str(record.get("batch", "Unknown"))
            cavity = str(record.get("cavity", "Unknown"))
            classe = str(record.get("class", "Unknown"))
            measuring_instrument = str(record.get("measuring_instrument", "Unknown"))
            evaluation_type = record.get("evaluation_type", "Normal")
            description = str(record.get("description", ""))
            
            # Handle nominal
            try:
                nominal = float(record["nominal"]) if pd.notna(record.get("nominal")) else 0.0
            except (ValueError, TypeError, KeyError):
                nominal = 0.0
            
            # Handle measurements
            measurements = record.get("measurements", [])
            if not isinstance(measurements, list):
                measurements = []

            if evaluation_type == "Note":
                avg = None
                sd = None
                self.logger.info(f"Note dimension {element_id}: Statistics set to None")
            else:
                avg = mean(measurements) if measurements else 0.0
                sd = stdev(measurements) if measurements and len(measurements) > 1 else 0.0


            deviation = [m - nominal for m in measurements] if measurements else []  # Calculate deviations

            # Handle tolerances based on evaluation type
            lower_tol, upper_tol, warnings = self._process_tolerances(record, evaluation_type, description, nominal)
            
            # Determine status based on evaluation type
            status, out_of_spec_count = self._determine_status(
                record, evaluation_type, measurements, nominal, lower_tol, upper_tol)

            # Create GD&T flags only if needed
            gdt_flags = {}
            if evaluation_type == "GD&T":
                gdt_flags = create_enhanced_gdt_flags(description)
            
            # Determine feature type
            feature_type = self._determine_feature_type_fast(description, evaluation_type)
            
            # Add measurement warnings only for critical cases
            if evaluation_type not in ["Note", "Basic", "Informative"] and measurements:
                if len(measurements) == 1:
                    warnings.append("Single measurement - no statistical analysis")
            
            # Calculate process capability for classified dimensions
            if evaluation_type == "Note":
                pp = None
                ppk = None
            else:
                pp, ppk = self._calculate_process_capability(
                    measurements, avg, sd, nominal, lower_tol, upper_tol, classe, evaluation_type
                )

            return DimensionalResult(
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
                mean=avg if evaluation_type != "Note" else None,
                std_dev=sd if evaluation_type != "Note" else None,
                out_of_spec_count=out_of_spec_count,
                status=status,
                gdt_flags=gdt_flags,
                datum_element_id=record.get("datum_element_id"),
                effective_tolerance_upper=upper_tol if upper_tol != 0.0 else None,
                effective_tolerance_lower=lower_tol if lower_tol != 0.0 else None,
                feature_type=feature_type,
                warnings=warnings,
                evaluation_type=evaluation_type,
                measuring_instrument=measuring_instrument,
                pp=pp if evaluation_type != "Note" else None,
                ppk=ppk if evaluation_type != "Note" else None,
            )
        except Exception as e:
            self.logger.error(f"Analysis error for {record.get('element_id', 'Unknown')}: {str(e)}")
            return self._create_error_result(record, f"Analysis error: {str(e)}")
    
    def _calculate_process_capability(self, measurements: List[float], mean_val: float, 
                                    std_dev: float, nominal: float, lower_tol: float, 
                                    upper_tol: float, classe: str, evaluation_type: str) -> tuple[float, float]:
        """Calculate Pp and Ppk for classified dimensions (CC, SC, IC)"""
        # Only calculate for classified dimensions with valid data
        if not classe or classe.upper() not in ["CC", "SC", "IC"]:
            return None, None
        
        # Skip for notes, basic, informative
        if evaluation_type in ["Note", "Basic", "Informative"]:
            return None, None
        
        # Need measurements, valid std dev, and tolerances
        if (not measurements or len(measurements) < 2 or std_dev <= 0 or 
            lower_tol == 0.0 and upper_tol == 0.0):
            return None, None
        
        try:
            # Calculate specification limits
            if lower_tol is not None and upper_tol is not None:
                # Bilateral tolerance
                lsl = nominal + lower_tol  # Lower Specification Limit
                usl = nominal + upper_tol  # Upper Specification Limit
                tolerance_range = abs(upper_tol - lower_tol)
                
                # Pp (Process Performance) = Tolerance Width / (6 * std_dev)
                pp = tolerance_range / (6 * std_dev)
                
                # Ppk (Process Performance Capability) = min(Ppu, Ppl)
                # Ppu = (USL - mean) / (3 * std_dev)
                # Ppl = (mean - LSL) / (3 * std_dev)
                ppu = (usl - mean_val) / (3 * std_dev)
                ppl = (mean_val - lsl) / (3 * std_dev)
                ppk = min(ppu, ppl)
                
            elif upper_tol is not None and upper_tol > 0:
                # Unilateral upper tolerance (common for positional tolerances)
                usl = nominal + upper_tol
                lsl = nominal  # Or could be 0 depending on context
                
                # For unilateral tolerance, use available limit
                pp = upper_tol / (3 * std_dev)  # Modified for unilateral
                ppu = (usl - mean_val) / (3 * std_dev)
                ppk = ppu  # Only upper capability
                
            else:
                return None, None
            
            # Round to reasonable decimal places
            pp = round(pp, 3) if pp is not None else None
            ppk = round(ppk, 3) if ppk is not None else None
            
            return pp, ppk
            
        except (ZeroDivisionError, ValueError, TypeError) as e:
            self.logger.warning(f"Process capability calculation error: {str(e)}")
            return None, None
    
    def _process_tolerances(self, record: Dict[str, Any], evaluation_type: str, description: str, nominal: float) -> tuple[float, float, List[str]]:
        """Optimized tolerance processing based on evaluation type"""
        warnings = []
        lower_tol = 0.0
        upper_tol = 0.0
        
        # For Basic/Informative, no tolerance evaluation needed
        if evaluation_type in ["Basic", "Informative"]:
            return 0.0, 0.0, ["No tolerance evaluation for " + evaluation_type]
        
        # For Notes, minimal tolerance processing
        if evaluation_type == "Note":
            return 0.0, 0.0, []
        
        # Get tolerance values from record
        raw_lower_tol = record.get("lower_tolerance")
        raw_upper_tol = record.get("upper_tolerance")
        
        # Parse tolerances
        try:
            if pd.notna(raw_lower_tol):
                lower_tol = float(raw_lower_tol)
            if pd.notna(raw_upper_tol):
                upper_tol = float(raw_upper_tol)
        except (ValueError, TypeError):
            warnings.append("Invalid tolerance values")
        
        # For GD&T, try to extract from description if no explicit tolerances
        if evaluation_type == "GD&T" and lower_tol == 0.0 and upper_tol == 0.0 and description:
            try:
                gdt_tolerance, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                if gdt_tolerance and len(gdt_tolerance) >= 2:
                    lower_tol = float(gdt_tolerance[0])
                    upper_tol = float(gdt_tolerance[1])
                    warnings.extend(gdt_warnings)
            except Exception as e:
                warnings.append(f"GD&T tolerance extraction failed: {str(e)}")
        
        return lower_tol, upper_tol, warnings
    
    def _determine_status(self, record: Dict[str, Any], evaluation_type: str, measurements: List[float], 
                     nominal: float, lower_tol: float, upper_tol: float) -> tuple[DimensionalStatus, int]:
        """Optimized status determination with evaluation type support and TO CHECK for notes"""
        force_status = record.get("force_status", "AUTO")
        
        # Handle Notes first - default to TO_CHECK unless forced
        if evaluation_type == "Note":
            if force_status == "GOOD":
                self.logger.info(f"Note {record.get('element_id', 'Unknown')}: Forced to GOOD")
                return DimensionalStatus.GOOD, 0
            elif force_status == "BAD":
                self.logger.info(f"Note {record.get('element_id', 'Unknown')}: Forced to BAD")
                return DimensionalStatus.BAD, len(measurements) if measurements else 0
            else:
                self.logger.info(f"Note {record.get('element_id', 'Unknown')}: Default TO_CHECK status")
                return DimensionalStatus.TO_CHECK, 0    # Default for notes is TO_CHECK

        # Handle forced status for non-notes
        if force_status == "GOOD":
            return DimensionalStatus.GOOD, 0
        elif force_status == "BAD":
            return DimensionalStatus.BAD, len(measurements)
        elif force_status == "TED":
            return DimensionalStatus.TED, len(measurements)
        elif force_status == "WARNING":
            return DimensionalStatus.WARNING, len(measurements)
        elif force_status == "TO CHECK":
            return DimensionalStatus.TO_CHECK, len(measurements)
        
        # Handle different evaluation types
        if evaluation_type in ["Basic", "Informative"]:
            return DimensionalStatus.TED, 0  # Will be displayed as T.E.D. in UI
        
        if not measurements:
            return DimensionalStatus.WARNING, 0
        
        # AUTO evaluation for Normal and GD&T
        if lower_tol == 0.0 and upper_tol == 0.0:
            return DimensionalStatus.GOOD, 0  # No tolerance to evaluate against
        
        out_of_spec = []    # Standard tolerance evaluation
        
        if nominal == 0.0 and lower_tol == 0.0 and upper_tol > 0.0:
            out_of_spec = [m for m in measurements if m < 0 or m > upper_tol]                       # Unilateral positive tolerance for nominal=0
        elif nominal == 0.0 and lower_tol < 0.0 and upper_tol > 0.0:
            out_of_spec = [m for m in measurements if abs(m) > max(abs(lower_tol), abs(upper_tol))] # Bilateral tolerance for nominal=0
        else:
            # Standard bilateral tolerance check
            lower_limit = nominal + lower_tol
            upper_limit = nominal + upper_tol
            out_of_spec = [m for m in measurements if not (lower_limit <= m <= upper_limit)]
        
        status = DimensionalStatus.GOOD if not out_of_spec else DimensionalStatus.BAD
        return status, len(out_of_spec)
    
    def _determine_feature_type_fast(self, description: str, evaluation_type: str) -> str:
        """Fast feature type determination"""
        if evaluation_type in ["Basic", "Informative"]:
            return evaluation_type.lower()
        
        if evaluation_type == "Note":
            return "note"
        
        if not description:
            return "dimension"
        
        desc_lower = description.lower()
        
        # Quick keyword matching
        if any(k in desc_lower for k in ["ø", "diam", "dia"]):
            return "diameter"
        elif any(k in desc_lower for k in ["hole", "bore"]):
            return "hole"
        elif any(k in desc_lower for k in ["flatness", "position"]):
            return "gdt_" + evaluation_type.lower()
        elif "angle" in desc_lower or "°" in desc_lower:
            return "angle"
        
        return "dimension"
    
    def _create_error_result(self, record: Dict[str, Any], error_message: str) -> DimensionalResult:
        """Create minimal error result"""
        return DimensionalResult(
            element_id=str(record.get("element_id", "Unknown")),
            batch=str(record.get("batch", "Unknown")),
            cavity=str(record.get("cavity", "Unknown")),
            classe=str(record.get("class", "Unknown")),
            description=str(record.get("description", "")),
            nominal=0.0,
            lower_tolerance=None,
            upper_tolerance=None,
            measurements=[],
            deviation=[],
            mean=0.0,
            std_dev=0.0,
            out_of_spec_count=0,
            status=DimensionalStatus.BAD,
            gdt_flags={},
            datum_element_id=None,
            effective_tolerance_upper=None,
            effective_tolerance_lower=None,
            feature_type="dimension",
            warnings=[error_message],
            evaluation_type=record.get("evaluation_type", "Normal"),
            measuring_instrument=str(record.get("measuring_instrument", "")),
            pp=None,
            ppk=None
        )