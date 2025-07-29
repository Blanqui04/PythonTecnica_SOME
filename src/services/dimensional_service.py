# src/services/enhanced_dimensional_service.py - FIXED VERSION
import pandas as pd
import logging
from typing import List, Optional, Callable, Dict, Any
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer
from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus
from src.models.dimensional.gdt_interpreter import GDTInterpreter


class DimensionalService:
    """Enhanced service for processing dimensional measurement data with improved GD&T support"""
    
    def __init__(self):
        self.analyzer = DimensionalAnalyzer()
        self.gdt_interpreter = GDTInterpreter()
        self.logger = logging.getLogger(__name__)
        
        # Configure logger for detailed output
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        
    def process_dataframe(self, df: pd.DataFrame, progress_callback: Optional[Callable] = None) -> List[DimensionalResult]:
        """Process DataFrame with proper error handling and tolerance processing"""
        results = []
        total_rows = len(df)
        processed_count = 0
        error_count = 0
        
        self.logger.info("🔧 " + "="*80)
        self.logger.info(f"🔧 DIMENSIONAL SERVICE: Starting processing of {total_rows} records")
        self.logger.info("🔧 " + "="*80)
        
        # Validate input DataFrame
        if df.empty:
            self.logger.error("❌ Empty DataFrame provided to service")
            return []
        
        # Log DataFrame structure
        self.logger.info("📊 DataFrame structure:")
        self.logger.info(f"   - Shape: {df.shape}")
        self.logger.info(f"   - Columns: {list(df.columns)}")
        
        # Required columns check
        required_cols = ['element_id', 'description']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.logger.error(f"❌ Missing required columns: {missing_cols}")
            return []
        
        for idx, row in df.iterrows():
            try:
                # Update progress
                if progress_callback:
                    progress = int((processed_count / total_rows) * 100)
                    progress_callback(progress)
                
                element_id = row.get('element_id', f'Row_{idx}')
                self.logger.debug(f"🔧 Processing element: {element_id} (row {idx})")
                
                # STEP 1: Prepare record with exhaustive logging
                record = self._prepare_record(row, idx)
                
                # STEP 2: Validate record
                if self._validate_record(record, element_id):
                    # STEP 3: Analyze the record using the analyzer
                    result = self.analyzer.analyze_row(record)
                    results.append(result)
                    
                    # Log the result
                    self.logger.debug(f"✅ {element_id}: {result.status.value} - {len(result.warnings)} warnings")
                    
                    # Log warnings if any
                    if result.warnings:
                        for warning in result.warnings:
                            self.logger.debug(f"⚠️ {element_id}: {warning}")
                else:
                    error_count += 1
                    self.logger.warning(f"❌ Skipping invalid record {element_id} at row {idx}")
                    
                processed_count += 1
                
                # Log progress periodically
                if processed_count % 10 == 0:
                    self.logger.info(f"📈 Service progress: {processed_count}/{total_rows} ({processed_count/total_rows*100:.1f}%)")
                
            except Exception as e:
                error_count += 1
                element_id = row.get('element_id', f'Row_{idx}')
                self.logger.error(f"❌ CRITICAL ERROR processing element {element_id}: {str(e)}")
                self.logger.error(f"❌ Full exception for {element_id}:", exc_info=True)
                
                # Create error result to maintain count
                error_result = self._create_error_result(row, f"Processing error: {str(e)}", element_id)
                results.append(error_result)
                processed_count += 1
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(100)
        
        # Final summary
        self.logger.info("🔧 " + "="*80)
        self.logger.info("🔧 SERVICE PROCESSING COMPLETED")
        self.logger.info(f" - Total processed: {processed_count}/{total_rows}")
        self.logger.info(f" - Successful: {len(results) - error_count}")
        self.logger.info(f" - Errors: {error_count}")
        self.logger.info(f" - Success rate: {((len(results) - error_count)/total_rows)*100:.1f}%")
        self.logger.info("🔧 " + "="*80)
        
        return results
    
    def _prepare_record(self, row: pd.Series, idx: int) -> Dict[str, Any]:
        """FIXED: Prepare a measurement record with proper tolerance handling"""
        element_id = row.get('element_id', f'Row_{idx}')
        self.logger.debug(f"🔧 Preparing record for {element_id}")
        
        record = row.to_dict()
        
        # Ensure all relevant fields are present and normalized
        record["class"] = row.get("class", "")
        record["measuring_instrument"] = row.get("measuring_instrument", "")
        record["evaluation_type"] = row.get("evaluation_type", "Normal")
        
        # STEP 1: Extract measurements with detailed logging
        measurements = []
        self.logger.debug(f"🔧 {element_id}: Extracting measurements...")
        
        for i in range(1, 6):
            key = f"measurement_{i}"
            if key in record:
                value = record[key]
                self.logger.debug(f"🔧 {element_id}: {key} = {value} (type: {type(value)})")
                
                if pd.notna(value) and str(value).strip() != "":
                    try:
                        float_value = float(value)
                        measurements.append(float_value)
                        self.logger.debug(f"✅ {element_id}: {key} = {float_value} (valid)")
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"❌ {element_id}: Invalid {key} value '{value}': {str(e)}")
                        continue
                else:
                    self.logger.debug(f"🔧 {element_id}: {key} is null/empty")
            else:
                self.logger.debug(f"🔧 {element_id}: {key} column not found")
        
        record["measurements"] = measurements
        self.logger.debug(f"🔧 {element_id}: Extracted {len(measurements)} measurements: {measurements}")
        
        # STEP 2: Handle description and GD&T
        description = str(record.get("description", ""))
        self.logger.debug(f"🔧 {element_id}: Description = '{description}'")
        
        if description:
            # Format GD&T symbols
            formatted_description = self.gdt_interpreter.format_gdt_display(description)
            record["description"] = formatted_description
            
            # Parse GD&T information
            gdt_info = self.gdt_interpreter.parse_gdt_description(description)
            record["gdt_info"] = gdt_info
            
            self.logger.debug(f"🔧 {element_id}: GD&T analysis - has_gdt: {gdt_info.get('has_gdt', False)}")
        
        # STEP 3: Handle numeric fields - FIXED FOR NOMINAL=0
        for field in ["nominal", "lower_tolerance", "upper_tolerance"]:
            if field in record:
                value = record[field]
                self.logger.debug(f"🔧 {element_id}: {field} = {value} (type: {type(value)})")
                
                if pd.notna(value):
                    try:
                        float_value = float(value)
                        record[field] = float_value
                        self.logger.debug(f"✅ {element_id}: {field} = {float_value} (converted)")
                        
                        # CRITICAL FIX: Log nominal=0 cases specifically
                        if field == "nominal" and float_value == 0.0:
                            self.logger.info(f"🎯 {element_id}: NOMINAL=0 detected - this is valid for GD&T")
                            
                    except (ValueError, TypeError):
                        self.logger.warning(f"❌ {element_id}: Invalid {field} value: {value}")
                        if field == "nominal":
                            record[field] = 0.0
                            self.logger.debug(f"🔧 {element_id}: {field} defaulted to zero")
                        else:
                            record[field] = None
                else:
                    # Handle None/NaN values
                    if field == "nominal":
                        record[field] = 0.0
                        self.logger.debug(f"🔧 {element_id}: {field} was None - defaulted to zero")
                    else:
                        record[field] = None
        
        # STEP 4: CRITICAL FIX - Extract and validate tolerances properly
        lower_tol = record.get("lower_tolerance")
        upper_tol = record.get("upper_tolerance")
        nominal = record.get("nominal", 0.0)
        evaluation_type = record.get("evaluation_type", "Normal")
        
        self.logger.debug(f"🔧 {element_id}: Tolerance extraction:")
        self.logger.debug(f"   - lower_tolerance: {lower_tol}")
        self.logger.debug(f"   - upper_tolerance: {upper_tol}")
        self.logger.debug(f"   - nominal: {nominal}")
        self.logger.debug(f"   - evaluation_type: {evaluation_type}")
        
        # Prepare tolerance list for analyzer
        tolerance_list = []
        
        # FIXED: Handle different tolerance scenarios properly
        if pd.notna(lower_tol) and pd.notna(upper_tol):
            # Both tolerances provided
            tolerance_list = [float(lower_tol), float(upper_tol)]
            self.logger.debug(f"✅ {element_id}: Both tolerances provided: {tolerance_list}")
            
        elif pd.notna(lower_tol) and pd.isna(upper_tol):
            # Only lower tolerance provided
            lower_val = float(lower_tol)
            if evaluation_type == "GD&T" and nominal == 0.0:
                # GD&T with nominal=0: unilateral tolerance
                tolerance_list = [0.0, abs(lower_val)]
                self.logger.debug(f"✅ {element_id}: GD&T unilateral tolerance: {tolerance_list}")
            else:
                # Symmetric tolerance
                tolerance_list = [-abs(lower_val), abs(lower_val)]
                self.logger.debug(f"✅ {element_id}: Symmetric tolerance from lower: {tolerance_list}")
                
        elif pd.isna(lower_tol) and pd.notna(upper_tol):
            # Only upper tolerance provided
            upper_val = float(upper_tol)
            if evaluation_type == "GD&T" and nominal == 0.0:
                # GD&T with nominal=0: unilateral tolerance
                tolerance_list = [0.0, abs(upper_val)]
                self.logger.debug(f"✅ {element_id}: GD&T unilateral tolerance: {tolerance_list}")
            else:
                # Symmetric tolerance
                tolerance_list = [-abs(upper_val), abs(upper_val)]
                self.logger.debug(f"✅ {element_id}: Symmetric tolerance from upper: {tolerance_list}")
        else:
            # No explicit tolerances - try GD&T extraction
            self.logger.debug(f"🔧 {element_id}: No explicit tolerances - checking GD&T")
            if description:
                gdt_tolerance, gdt_warnings = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
                if gdt_tolerance and len(gdt_tolerance) >= 1:
                    tolerance_list = gdt_tolerance
                    record.setdefault("gdt_warnings", []).extend(gdt_warnings)
                    self.logger.debug(f"✅ {element_id}: GD&T tolerance extracted: {tolerance_list}")
                else:
                    self.logger.warning(f"⚠️ {element_id}: No tolerances found - will use force_status or default")
        
        # Store tolerance list in record for analyzer
        record["tolerance"] = tolerance_list
        
        # STEP 5: Handle force_status
        force_status = record.get("force_status", "AUTO")
        if pd.isna(force_status) or force_status == "":
            record["force_status"] = "AUTO"
        else:
            record["force_status"] = str(force_status).upper()
        
        self.logger.debug(f"🔧 {element_id}: Final record prepared:")
        self.logger.debug(f"   - force_status: {record['force_status']}")
        self.logger.debug(f"   - evaluation_type: {record['evaluation_type']}")
        self.logger.debug(f"   - tolerance: {record.get('tolerance', [])}")
        self.logger.debug(f"   - measurements count: {len(measurements)}")
        
        return record
    
    def _validate_record(self, record: Dict[str, Any], element_id: str) -> bool:
        """FIXED: Enhanced record validation with detailed logging"""
        self.logger.debug(f"🔧 Validating record for {element_id}")
        
        # Check if this is a Note entry
        evaluation_type = record.get("evaluation_type", "Normal")
        is_note = evaluation_type == "Note"
        
        # Basic validation
        if is_note:
            required_fields = ["element_id", "description"]
        else:
            required_fields = ["element_id", "description"]  # Removed "nominal" as it can be 0
            
        for field in required_fields:
            value = record.get(field)
            # FIXED: Check for None/empty explicitly, allow 0 for nominal
            if value is None or (isinstance(value, str) and not value.strip()):
                if field == "nominal" and value == 0:
                    continue  # nominal=0 is valid
                self.logger.warning(f"❌ {element_id}: Missing required field: {field}")
                return False
        
        # FIXED: Check nominal value properly (allow 0)
        if not is_note:
            nominal = record.get("nominal")
            if nominal is None:
                self.logger.warning(f"❌ {element_id}: Nominal value is None")
                return False
            
            try:
                nominal_float = float(nominal)
                self.logger.debug(f"✅ {element_id}: Nominal value {nominal_float} is valid (including zero)")
            except (ValueError, TypeError):
                self.logger.warning(f"❌ {element_id}: Invalid nominal value: {nominal}")
                return False
        
        # Check measurements for non-Note entries
        measurements = record.get("measurements", [])
        if not is_note and not measurements:
            self.logger.warning(f"❌ {element_id}: No valid measurements found for non-Note entry")
            return False
        
        self.logger.debug(f"✅ {element_id}: Record validation passed")
        return True
    
    def _create_error_result(self, record: Dict[str, Any], error_message: str, element_id: str = None) -> DimensionalResult:
        """Create a result object for error cases"""
        element_id = element_id if element_id is not None else str(record.get("element_id", "Unknown"))
        
        return DimensionalResult(
            element_id=element_id,
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
            feature_type="dimension",
            warnings=[error_message],
        )

    def _determine_feature_type(self, description: str) -> str:
        """Determine feature type from description"""
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
        """Generate an enhanced summary of processing results"""
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
            ft = result.feature_type or "dimension"
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