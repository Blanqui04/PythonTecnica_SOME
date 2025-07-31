# src/services/enhanced_dimensional_service.py - OPTIMIZED VERSION
import pandas as pd
import logging
from typing import List, Optional, Callable, Dict, Any
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer
from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus
from src.models.dimensional.gdt_interpreter import GDTInterpreter


class DimensionalService:
    """Optimized service for processing dimensional measurement data"""
    
    def __init__(self):
        self.analyzer = DimensionalAnalyzer()
        self.gdt_interpreter = GDTInterpreter()
        self.logger = logging.getLogger(__name__)
        # Reduce logging overhead
        self.logger.setLevel(logging.WARNING)  # Only warnings and errors
        
    def process_dataframe(self, df: pd.DataFrame, progress_callback: Optional[Callable] = None) -> List[DimensionalResult]:
        """Optimized DataFrame processing with batch operations"""
        if df.empty:
            self.logger.error("Empty DataFrame provided")
            return []
        
        results = []
        total_rows = len(df)
        
        self.logger.warning(f"Processing {total_rows} records...")
        
        # Validate required columns once
        required_cols = ['element_id', 'description']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return []
        
        # Pre-process numeric columns in batch
        numeric_cols = ['nominal', 'lower_tolerance', 'upper_tolerance'] + \
                      [f'measurement_{i}' for i in range(1, 6)]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Process rows in batches for better performance
        batch_size = 10
        processed_count = 0
        
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch = df.iloc[start_idx:end_idx]
            
            for idx, row in batch.iterrows():
                try:
                    record = self._prepare_record_optimized(row, idx)
                    
                    if self._validate_record_fast(record):
                        result = self.analyzer.analyze_row(record)
                        results.append(result)
                    else:
                        # Create minimal error result
                        error_result = self._create_error_result(record, "Validation failed")
                        results.append(error_result)
                        
                except Exception as e:
                    self.logger.error(f"Error processing row {idx}: {str(e)}")
                    error_result = self._create_error_result(row.to_dict(), f"Processing error: {str(e)}")
                    results.append(error_result)
                
                processed_count += 1
                
                # Update progress less frequently
                if progress_callback and processed_count % batch_size == 0:
                    progress = int((processed_count / total_rows) * 100)
                    progress_callback(progress)
        
        # Final progress update
        if progress_callback:
            progress_callback(100)
        
        self.logger.warning(f"Processed {len(results)} records successfully")
        return results
    
    def _prepare_record_optimized(self, row: pd.Series, idx: int) -> Dict[str, Any]:
        """Optimized record preparation with minimal logging"""
        record = row.to_dict()
        
        # Handle measurements efficiently
        measurements = []
        for i in range(1, 6):
            key = f"measurement_{i}"
            value = record.get(key)
            if pd.notna(value) and value != "":
                try:
                    measurements.append(float(value))
                except (ValueError, TypeError):
                    continue
        
        record["measurements"] = measurements
        
        # Handle evaluation type
        evaluation_type = record.get("evaluation_type", "Normal")
        if pd.isna(evaluation_type) or evaluation_type == "":
            evaluation_type = "Normal"
        record["evaluation_type"] = evaluation_type
        
        # Handle GD&T only if needed
        description = str(record.get("description", ""))
        if description and evaluation_type == "GD&T":
            formatted_description = self.gdt_interpreter.format_gdt_display(description)
            record["description"] = formatted_description
            gdt_info = self.gdt_interpreter.parse_gdt_description(description)
            record["gdt_info"] = gdt_info
        
        # Handle numeric fields efficiently
        for field in ["nominal", "lower_tolerance", "upper_tolerance"]:
            value = record.get(field)
            if pd.notna(value):
                try:
                    record[field] = float(value)
                except (ValueError, TypeError):
                    record[field] = 0.0 if field == "nominal" else None
            else:
                record[field] = 0.0 if field == "nominal" else None
        
        # Extract tolerances efficiently
        lower_tol = record.get("lower_tolerance")
        upper_tol = record.get("upper_tolerance")
        nominal = record.get("nominal", 0.0)
        
        tolerance_list = []
        if pd.notna(lower_tol) and pd.notna(upper_tol):
            tolerance_list = [float(lower_tol), float(upper_tol)]
        elif pd.notna(lower_tol):
            lower_val = float(lower_tol)
            if evaluation_type == "GD&T" and nominal == 0.0:
                tolerance_list = [0.0, abs(lower_val)]
            else:
                tolerance_list = [-abs(lower_val), abs(lower_val)]
        elif pd.notna(upper_tol):
            upper_val = float(upper_tol)
            if evaluation_type == "GD&T" and nominal == 0.0:
                tolerance_list = [0.0, abs(upper_val)]
            else:
                tolerance_list = [-abs(upper_val), abs(upper_val)]
        elif description and evaluation_type == "GD&T":
            # Only extract GD&T tolerance if explicitly GD&T type
            gdt_tolerance, _ = self.gdt_interpreter.extract_tolerance_from_gdt(description, nominal)
            if gdt_tolerance and len(gdt_tolerance) >= 2:
                tolerance_list = gdt_tolerance
        
        record["tolerance"] = tolerance_list
        
        # Handle force_status
        force_status = record.get("force_status", "AUTO")
        if pd.isna(force_status) or force_status == "":
            record["force_status"] = "AUTO"
        else:
            record["force_status"] = str(force_status).upper()
        
        return record
    
    def _validate_record_fast(self, record: Dict[str, Any]) -> bool:
        """Fast validation with minimal checks"""
        # Basic required fields
        if not record.get("element_id") or not record.get("description"):
            return False
        
        evaluation_type = record.get("evaluation_type", "Normal")
        
        # For Notes, minimal validation
        if evaluation_type == "Note":
            return True
        
        # For Basic/Informative, check nominal only
        if evaluation_type in ["Basic", "Informative"]:
            nominal = record.get("nominal")
            return nominal is not None
        
        # For Normal/GD&T, check nominal and measurements
        nominal = record.get("nominal")
        measurements = record.get("measurements", [])
        
        if nominal is None:
            return False
        
        if not measurements:
            return False
        
        return True
    
    def _create_error_result(self, record: Dict[str, Any], error_message: str, element_id: str = None) -> DimensionalResult:
        """Create minimal error result"""
        element_id = element_id or str(record.get("element_id", "Unknown"))
        
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
            measuring_instrument=str(record.get("measuring_instrument", "")),
            evaluation_type=str(record.get("evaluation_type", "Normal"))
        )
    
    def get_processing_summary(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Optimized summary generation"""
        if not results:
            return {"total": 0, "good": 0, "bad": 0, "warning": 0, "success_rate": 0.0,
                    "gdt_count": 0, "feature_types": {}, "cavity_summary": {}, 
                    "evaluation_types": {}}
        
        total = len(results)
        status_counts = {"GOOD": 0, "BAD": 0, "WARNING": 0}
        evaluation_types = {}
        feature_types = {}
        cavity_summary = {}
        gdt_count = 0
        
        # Single pass through results
        for result in results:
            # Status count
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Evaluation types
            eval_type = getattr(result, 'evaluation_type', 'Normal')
            evaluation_types[eval_type] = evaluation_types.get(eval_type, 0) + 1
            
            # Feature types
            ft = result.feature_type or "dimension"
            feature_types[ft] = feature_types.get(ft, 0) + 1
            
            # Cavity analysis
            cavity = result.cavity
            if cavity not in cavity_summary:
                cavity_summary[cavity] = {"total": 0, "good": 0, "bad": 0}
            cavity_summary[cavity]["total"] += 1
            if status == "GOOD":
                cavity_summary[cavity]["good"] += 1
            elif status == "BAD":
                cavity_summary[cavity]["bad"] += 1
            
            # GD&T count
            if result.gdt_flags.get('HAS_GDT', False):
                gdt_count += 1
        
        return {
            "total": total,
            "good": status_counts.get("GOOD", 0),
            "bad": status_counts.get("BAD", 0),
            "warning": status_counts.get("WARNING", 0),
            "success_rate": (status_counts.get("GOOD", 0) / total) * 100 if total > 0 else 0.0,
            "gdt_count": gdt_count,
            "gdt_percentage": (gdt_count / total) * 100 if total > 0 else 0.0,
            "feature_types": feature_types,
            "cavity_summary": cavity_summary,
            "evaluation_types": evaluation_types
        }