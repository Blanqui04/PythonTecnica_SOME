# src/services/enhanced_dimensional_service.py
import pandas as pd
import logging
from typing import List, Optional, Callable, Dict, Any
from statistics import mean, stdev
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer
from src.models.dimensional.measurement_validator import validate_measurements, prepare_record_for_analysis
from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus
from src.models.dimensional.gdt_interpreter import GDTInterpreter, create_enhanced_gdt_flags


class DimensionalService:
    """Enhanced service for processing dimensional measurement data with improved GD&T support"""
    
    def __init__(self):
        self.analyzer = DimensionalAnalyzer()
        self.gdt_interpreter = GDTInterpreter()
        self.logger = logging.getLogger(__name__)
        
    def process_dataframe(self, df: pd.DataFrame, progress_callback: Optional[Callable] = None) -> List[DimensionalResult]:
        """
        Process a dataframe of dimensional measurements with enhanced GD&T support
        
        Args:
            df: DataFrame containing measurement data
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of DimensionalResult objects
        """
        results = []
        total_rows = len(df)
        processed_count = 0
        error_count = 0
        
        self.logger.info(f"Starting enhanced processing of {total_rows} measurement records")
        
        for idx, row in df.iterrows():
            try:
                # Update progress
                if progress_callback:
                    progress = int((processed_count / total_rows) * 100)
                    progress_callback(progress)
                
                # Convert row to dict and process
                record = self._prepare_enhanced_record(row)
                
                if self._validate_enhanced_record(record):
                    result = self._analyze_enhanced_row(record)
                    results.append(result)
                    
                    # Log warnings if any
                    if result.warnings:
                        self.logger.warning(f"Element {record.get('element_id', 'Unknown')}: {'; '.join(result.warnings)}")
                else:
                    error_count += 1
                    self.logger.warning(f"Skipping invalid record at row {idx}: {record.get('element_id', 'Unknown')}")
                    
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                element_id = row.get('element_id', f'Row_{idx}')
                self.logger.error(f"Error processing element {element_id}: {str(e)}")
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(100)
            
        self.logger.info(f"Enhanced processing completed: {len(results)} successful, {error_count} errors")
        return results
    
    def _prepare_enhanced_record(self, row: pd.Series) -> Dict[str, Any]:
        """
        Prepare a measurement record from a pandas Series with enhanced GD&T handling
        
        Args:
            row: Pandas Series containing measurement data
            
        Returns:
            Dictionary with prepared measurement data
        """
        record = row.to_dict()
        
        # Extract measurements from measurement_1 to measurement_5
        measurements = []
        for i in range(1, 6):
            key = f"measurement_{i}"
            if key in record and pd.notna(record[key]):
                try:
                    value = float(record[key])
                    measurements.append(value)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid measurement value in {key}: {record[key]}")
                    continue
        
        record["measurements"] = measurements
        
        # Enhanced GD&T handling for description
        description = str(record.get("description", ""))
        if description:
            # Format GD&T symbols properly
            formatted_description = self.gdt_interpreter.format_gdt_display(description)
            record["description"] = formatted_description
            
            # Parse GD&T information
            gdt_info = self.gdt_interpreter.parse_gdt_description(description)
            record["gdt_info"] = gdt_info
            
            # If GD&T tolerance is found and no separate tolerance provided, use GD&T
            if gdt_info['has_gdt'] and gdt_info['tolerance_value']:
                nominal = float(record.get("nominal", 0)) if pd.notna(record.get("nominal")) else 0.0
                if not self._has_explicit_tolerance(record):
                    gdt_tolerance, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                    if gdt_tolerance:
                        record["tolerance"] = gdt_tolerance
                        record["gdt_warnings"] = gdt_warnings
        
        # Prepare tolerance data (existing logic)
        if "tolerance" not in record:
            record["tolerance"] = self._prepare_tolerance_data(record)
        
        # Ensure required numeric fields are properly converted
        for field in ["nominal", "lower_tolerance", "upper_tolerance"]:
            if field in record and pd.notna(record[field]):
                try:
                    record[field] = float(record[field])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid {field} value: {record[field]}")
                    if field == "nominal":
                        record[field] = 0.0
                    else:
                        record[field] = None
        
        return record
    
    def _has_explicit_tolerance(self, record: Dict[str, Any]) -> bool:
        """Check if record has explicit tolerance values"""
        lower_tol = record.get("lower_tolerance")
        upper_tol = record.get("upper_tolerance")
        
        return (pd.notna(lower_tol) and lower_tol != 0) or (pd.notna(upper_tol) and upper_tol != 0)
    
    def _prepare_tolerance_data(self, record: Dict[str, Any]) -> List[float]:
        """
        Prepare tolerance data from lower_tolerance and upper_tolerance fields
        
        Args:
            record: Dictionary containing measurement record
            
        Returns:
            List of tolerance values [lower, upper] or empty list if invalid
        """
        lower_tol = record.get("lower_tolerance")
        upper_tol = record.get("upper_tolerance")
        
        tolerances = []
        
        # Handle lower tolerance
        if pd.notna(lower_tol):
            try:
                tolerances.append(float(lower_tol))
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid lower_tolerance: {lower_tol}")
        
        # Handle upper tolerance
        if pd.notna(upper_tol):
            try:
                tolerances.append(float(upper_tol))
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid upper_tolerance: {upper_tol}")
        
        # If we only have one tolerance value, duplicate it for symmetric tolerance
        if len(tolerances) == 1:
            if pd.notna(lower_tol) and pd.isna(upper_tol):
                # Only lower tolerance provided, make it symmetric
                tolerances = [-abs(tolerances[0]), abs(tolerances[0])]
            elif pd.isna(lower_tol) and pd.notna(upper_tol):
                # Only upper tolerance provided, make it symmetric
                tolerances = [-abs(tolerances[0]), abs(tolerances[0])]
        elif len(tolerances) == 2:
            # Both tolerances provided, ensure proper order
            tolerances.sort()
        
        return tolerances
    
    def _validate_enhanced_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a measurement record with enhanced GD&T validation
        
        Args:
            record: Dictionary containing measurement record
            
        Returns:
            True if record is valid, False otherwise
        """
        # Basic validation
        required_fields = ["element_id", "description", "nominal"]
        for field in required_fields:
            if not record.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Check we have at least one measurement
        measurements = record.get("measurements", [])
        if not measurements:
            self.logger.warning(f"No valid measurements found for element {record.get('element_id')}")
            return False
        
        # Enhanced GD&T validation
        gdt_info = record.get("gdt_info", {})
        if gdt_info.get('has_gdt'):
            gdt_warnings = gdt_info.get('warnings', [])
            if gdt_warnings:
                for warning in gdt_warnings:
                    self.logger.warning(f"GD&T validation for {record.get('element_id')}: {warning}")
        
        # Use existing validator with enhancements
        try:
            prepared_record = prepare_record_for_analysis(record)
            return validate_measurements(prepared_record)
        except Exception as e:
            self.logger.error(f"Enhanced validation error: {str(e)}")
            return False
    
    def _analyze_enhanced_row(self, record: Dict[str, Any]) -> DimensionalResult:
        """
        Analyze a single measurement row with enhanced GD&T support
        
        Args:
            record: Dictionary containing measurement data
            
        Returns:
            DimensionalResult object
        """
        try:
            # Extract basic information
            element_id = str(record.get("element_id", "Unknown"))
            batch = str(record.get("batch", "Unknown"))
            cavity = str(record.get("cavity", "Unknown"))
            classe = str(record.get("class", "Unknown"))
            description = str(record.get("description", ""))

            # Convert nominal to float
            try:
                nominal = float(record["nominal"])
            except (ValueError, TypeError, KeyError):
                return self._create_error_result(record, "Invalid or missing nominal value")

            # Extract measurements
            measurements = record.get("measurements", [])
            if not measurements:
                return self._create_error_result(record, "No measurements provided")

            # Ensure all measurements are floats
            try:
                measurements = [float(m) for m in measurements if m is not None]
            except (ValueError, TypeError):
                return self._create_error_result(record, "Invalid measurement values")

            if not measurements:
                return self._create_error_result(record, "No valid measurements found")

            # Calculate deviations
            deviation = [m - nominal for m in measurements]

            # Enhanced GD&T flags
            gdt_flags = create_enhanced_gdt_flags(description)
            gdt_info = record.get("gdt_info", {})

            # Handle tolerance - prefer GD&T if available
            tolerance_list = record.get("tolerance", [])
            if not tolerance_list and gdt_info.get('has_gdt'):
                # Extract from GD&T
                tolerance_list, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                if gdt_warnings:
                    record.setdefault("gdt_warnings", []).extend(gdt_warnings)

            # Handle missing tolerance
            if not tolerance_list or (isinstance(tolerance_list, list) and len(tolerance_list) == 0):
                return self._create_no_tolerance_result(record, measurements, deviation, gdt_flags)

            # Parse tolerances
            if len(tolerance_list) == 2:
                lower_tol, upper_tol = tolerance_list
            elif len(tolerance_list) == 1:
                # Single tolerance - make symmetric unless GD&T specifies otherwise
                tol_val = tolerance_list[0]
                if gdt_info.get('tolerance_type') in ['flatness', 'circularity', 'cylindricity', 'runout']:
                    lower_tol, upper_tol = 0.0, abs(tol_val)
                else:
                    lower_tol, upper_tol = -abs(tol_val), abs(tol_val)
            else:
                return self._create_error_result(record, "Invalid tolerance format")

            # Calculate limits
            lower_limit = nominal + lower_tol
            upper_limit = nominal + upper_tol

            # Check measurements against limits
            if lower_tol == 0.0 and upper_tol == 0.0:
                # Exact match required
                out_of_spec = [m for m in measurements if abs(m - nominal) > 1e-6]
            else:
                # Normal tolerance check
                out_of_spec = [m for m in measurements if not (lower_limit <= m <= upper_limit)]

            # Determine status
            status = DimensionalStatus.GOOD if len(out_of_spec) == 0 else DimensionalStatus.BAD

            # Calculate statistics
            avg = mean(measurements)
            sd = stdev(measurements) if len(measurements) > 1 else 0.0

            # Determine feature type
            feature_type = gdt_info.get('feature_type', self._determine_feature_type(description))

            # Generate warnings
            warnings = []
            
            # Add GD&T warnings
            if gdt_info.get('warnings'):
                warnings.extend(gdt_info['warnings'])
            if record.get("gdt_warnings"):
                warnings.extend(record["gdt_warnings"])

            # Standard warnings
            if len(measurements) < 5:
                warnings.append(f"Only {len(measurements)} measurements provided; 5 recommended for statistical validity.")

            if len(measurements) == 1:
                warnings.append("Only 1 measurement provided; statistical analysis not possible.")

            # Check for measurement consistency
            if len(measurements) > 1:
                cv = (sd / abs(avg)) * 100 if avg != 0 else 0
                if cv > 10:  # Coefficient of variation > 10%
                    warnings.append(f"High measurement variability detected (CV = {cv:.1f}%)")

            # GD&T specific warnings
            if gdt_flags.get('HAS_GDT'):
                if gdt_flags.get('MMC') or gdt_flags.get('LMC'):
                    warnings.append("Material condition modifiers applied - bonus tolerance possible")
                
                if gdt_flags.get('HAS_DATUMS') and not record.get('datum_element_id'):
                    warnings.append("GD&T callout references datums but no datum measurements provided")

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
                datum_element_id=record.get("datum_element_id"),
                effective_tolerance_upper=upper_tol,
                effective_tolerance_lower=lower_tol,
                feature_type=feature_type,
                warnings=warnings,
            )

        except Exception as e:
            self.logger.error(f"Error analyzing row for element {record.get('element_id', 'Unknown')}: {str(e)}")
            return self._create_error_result(record, f"Analysis error: {str(e)}")

    def _create_error_result(self, record: Dict[str, Any], error_message: str) -> DimensionalResult:
        """Create a result object for error cases"""
        return DimensionalResult(
            element_id=str(record.get("element_id", "Unknown")),
            batch=str(record.get("batch", "Unknown")),
            cavity=str(record.get("cavity", "Unknown")),
            classe=str(record.get("class", "Unknown")),
            description=str(record.get("description", "")),
            nominal=float(record.get("nominal", 0.0)) if record.get("nominal") is not None else 0.0,
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

    def _create_no_tolerance_result(self, record: Dict[str, Any], measurements: List[float], 
                                   deviation: List[float], gdt_flags: Dict[str, bool]) -> DimensionalResult:
        """Create a result object when no tolerance is provided"""
        nominal = float(record.get("nominal", 0.0))

        return DimensionalResult(
            element_id=str(record.get("element_id", "Unknown")),
            batch=str(record.get("batch", "Unknown")),
            cavity=str(record.get("cavity", "Unknown")),
            classe=str(record.get("class", "Unknown")),
            description=str(record.get("description", "")),
            nominal=nominal,
            lower_tolerance=None,
            upper_tolerance=None,
            measurements=measurements,
            deviation=deviation,
            mean=mean(measurements) if measurements else 0.0,
            std_dev=stdev(measurements) if len(measurements) > 1 else 0.0,
            out_of_spec_count=len(measurements),  # All considered out of spec without tolerance
            status=DimensionalStatus.BAD,
            gdt_flags=gdt_flags,
            datum_element_id=record.get("datum_element_id"),
            effective_tolerance_upper=None,
            effective_tolerance_lower=None,
            feature_type=self._determine_feature_type(record.get("description", "")),
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
    
    def get_processing_summary(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """
        Generate an enhanced summary of processing results
        
        Args:
            results: List of DimensionalResult objects
            
        Returns:
            Dictionary containing summary statistics
        """
        if not results:
            return {
                "total": 0, "good": 0, "bad": 0, "warning": 0, "success_rate": 0.0,
                "gdt_count": 0, "feature_types": {}, "cavity_summary": {}
            }
        
        total = len(results)
        good = sum(1 for r in results if r.status.value == "GOOD")
        bad = sum(1 for r in results if r.status.value == "BAD")
        warning = sum(1 for r in results if r.status.value == "WARNING")
        success_rate = (good / total) * 100 if total > 0 else 0.0
        
        # GD&T analysis
        gdt_count = sum(1 for r in results if r.gdt_flags.get('HAS_GDT', False))
        
        # Feature type analysis
        feature_types = {}
        for result in results:
            ft = result.feature_type
            feature_types[ft] = feature_types.get(ft, 0) + 1
        
        # Cavity analysis
        cavity_summary = {}
        for result in results:
            cavity = result.cavity
            if cavity not in cavity_summary:
                cavity_summary[cavity] = {"total": 0, "good": 0, "bad": 0}
            cavity_summary[cavity]["total"] += 1
            if result.status.value == "GOOD":
                cavity_summary[cavity]["good"] += 1
            elif result.status.value == "BAD":
                cavity_summary[cavity]["bad"] += 1
        
        return {
            "total": total,
            "good": good,
            "bad": bad,
            "warning": warning,
            "success_rate": success_rate,
            "gdt_count": gdt_count,
            "gdt_percentage": (gdt_count / total) * 100 if total > 0 else 0.0,
            "feature_types": feature_types,
            "cavity_summary": cavity_summary
        }