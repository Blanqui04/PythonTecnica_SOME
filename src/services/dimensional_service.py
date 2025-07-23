# src/services/dimensional_service.
import pandas as pd
import logging
from typing import List, Optional, Callable
from src.models.dimensional.dimensional_analyzer import DimensionalAnalyzer
from src.models.dimensional.measurement_validator import validate_measurements
from src.models.dimensional.dimensional_result import DimensionalResult


class DimensionalService:
    """Service for processing dimensional measurement data"""
    
    def __init__(self):
        self.analyzer = DimensionalAnalyzer()
        self.logger = logging.getLogger(__name__)
        
    def process_dataframe(self, df: pd.DataFrame, progress_callback: Optional[Callable] = None) -> List[DimensionalResult]:
        """
        Process a dataframe of dimensional measurements
        
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
        
        self.logger.info(f"Starting processing of {total_rows} measurement records")
        
        for idx, row in df.iterrows():
            try:
                # Update progress
                if progress_callback:
                    progress = int((processed_count / total_rows) * 100)
                    progress_callback(progress)
                
                # Convert row to dict and process
                record = self._prepare_record(row)
                
                if self._validate_record(record):
                    result = self.analyzer.analyze_row(record)
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
            
        self.logger.info(f"Processing completed: {len(results)} successful, {error_count} errors")
        return results
    
    def _prepare_record(self, row: pd.Series) -> dict:
        """
        Prepare a measurement record from a pandas Series
        
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
        
        # Prepare tolerance data
        record["tolerance"] = self._prepare_tolerance_data(record)
        
        # Ensure required numeric fields are properly converted
        for field in ["nominal"]:
            if field in record and pd.notna(record[field]):
                try:
                    record[field] = float(record[field])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid {field} value: {record[field]}")
                    record[field] = 0.0
        
        return record
    
    def _prepare_tolerance_data(self, record: dict) -> List[float]:
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
    
    def _validate_record(self, record: dict) -> bool:
        """
        Validate a measurement record has required data
        
        Args:
            record: Dictionary containing measurement record
            
        Returns:
            True if record is valid, False otherwise
        """
        # Check required fields
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
        
        # Use the existing validator if available
        try:
            return validate_measurements(record)
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
    
    def get_processing_summary(self, results: List[DimensionalResult]) -> dict:
        """
        Generate a summary of processing results
        
        Args:
            results: List of DimensionalResult objects
            
        Returns:
            Dictionary containing summary statistics
        """
        if not results:
            return {"total": 0, "good": 0, "bad": 0, "warning": 0, "success_rate": 0.0}
        
        total = len(results)
        good = sum(1 for r in results if r.status.value == "GOOD")
        bad = sum(1 for r in results if r.status.value == "BAD")
        warning = sum(1 for r in results if r.status.value == "WARNING")
        success_rate = (good / total) * 100 if total > 0 else 0.0
        
        return {
            "total": total,
            "good": good,
            "bad": bad,
            "warning": warning,
            "success_rate": success_rate
        }