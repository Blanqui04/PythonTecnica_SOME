# src/models/dimensional/measurement_validator.py - OPTIMIZED VERSION
import logging
from typing import Dict, List, Any
from functools import lru_cache


# Cache for validation results to improve performance
@lru_cache(maxsize=1000)
def _cached_float_validation(value: str, min_val: float = -1e6, max_val: float = 1e6) -> bool:
    """Cached float validation for performance"""
    try:
        float_val = float(value)
        return min_val <= float_val <= max_val
    except (ValueError, TypeError):
        return False


def validate_measurements(record: Dict[str, Any]) -> bool:
    """
    Optimized validation of measurement record for dimensional analysis
    Args:
        record: Dictionary containing measurement data
    Returns:
        True if record is valid, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        # Get evaluation type for faster processing
        evaluation_type = record.get("evaluation_type", "Normal")
        is_note = evaluation_type == "Note"
        is_basic_informative = evaluation_type in ["Basic", "Informative"]

        # Fast path: Check required fields based on evaluation type
        if is_note:
            required_fields = ["element_id", "description"]  # Notes don't need nominal or measurements
        elif is_basic_informative:
            required_fields = ["element_id", "description", "nominal"]  # Basic/Informative need nominal
        else:
            required_fields = ["element_id", "description", "nominal"]  # Normal/GD&T need nominal
            
        # Quick required field validation
        for field in required_fields:
            if not record.get(field):
                logger.warning(f"Missing required field '{field}' in record")
                return False

        # Validate nominal value for non-Note entries
        if not is_note:
            nominal_str = str(record["nominal"])
            if not _cached_float_validation(nominal_str):
                logger.warning(f"Invalid nominal value: {record.get('nominal')}")
                return False

        # Optimized measurement validation
        measurements = record.get("measurements", [])
        if measurements is not None:
            # Fast type check
            if not isinstance(measurements, list):
                logger.warning("Measurements must be a list")
                return False

            # Quick measurement validation with early exit
            valid_count = 0
            for i, measurement in enumerate(measurements):
                if measurement is not None:
                    measurement_str = str(measurement)
                    if _cached_float_validation(measurement_str):
                        valid_count += 1
                    else:
                        logger.warning(f"Invalid measurement at position {i + 1}: {measurement}")

            # Update record with valid count (avoid recreating list for performance)
            if valid_count == 0 and not is_note and not is_basic_informative:
                logger.warning("No valid measurements found for dimension requiring measurements")
                return False

        # Quick tolerance validation (skip detailed validation for performance)
        tolerance = record.get("tolerance")
        if tolerance is not None and not _validate_tolerance_fast(tolerance):
            logger.warning(f"Invalid tolerance format: {tolerance}")
            # Don't fail validation, just warn

        # Fast validation of optional string fields
        for field in ["batch", "cavity", "classe"]:
            value = record.get(field)
            if value is not None and not str(value).strip():
                logger.warning(f"Empty {field} value")

        # Quick datum validation
        if record.get("datum_element_id") is not None:
            for datum_field in ["datum_nominal", "datum_measurement"]:
                datum_value = record.get(datum_field)
                if datum_value is not None:
                    datum_str = str(datum_value)
                    if not _cached_float_validation(datum_str):
                        logger.warning(f"Invalid {datum_field} value: {datum_value}")

        return True

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False


@lru_cache(maxsize=500)
def _validate_tolerance_fast(tolerance: Any) -> bool:
    """
    Fast tolerance validation with caching

    Args:
        tolerance: Tolerance value in various formats

    Returns:
        True if tolerance format is valid
    """
    try:
        if isinstance(tolerance, (int, float)):
            return -1e6 <= float(tolerance) <= 1e6

        elif isinstance(tolerance, list):
            if len(tolerance) == 0:
                return True  # Empty tolerance list is valid
            elif len(tolerance) <= 2:
                return all(_cached_float_validation(str(tol)) for tol in tolerance)
            else:
                return False  # Too many tolerance values

        elif isinstance(tolerance, str):
            if not tolerance.strip():
                return True  # Empty string is valid

            # Quick numeric check
            if _cached_float_validation(tolerance):
                return True

            # Quick range check (e.g., "+0.1/-0.05")
            if "/" in tolerance:
                parts = tolerance.replace("+", "").split("/")
                if len(parts) == 2:
                    return all(_cached_float_validation(part) for part in parts)

            return False
        else:
            return False

    except Exception:
        return False


def validate_batch_consistency_optimized(records: List[Dict[str, Any]]) -> List[str]:
    """
    Optimized batch consistency validation
    Args:
        records: List of measurement record dictionaries
    Returns:
        List of warning messages
    """
    warnings = []
    logger = logging.getLogger(__name__)

    if not records:
        return ["No records to validate"]

    try:
        # Fast duplicate detection
        element_ids = [record.get("element_id") for record in records if record.get("element_id")]
        if len(element_ids) != len(set(element_ids)):
            duplicates = [eid for eid in set(element_ids) if element_ids.count(eid) > 1]
            warnings.append(f"Duplicate element IDs found: {', '.join(duplicates[:5])}")  # Limit output

        # Quick batch consistency check
        batches = {record.get("batch") for record in records if record.get("batch")}
        if len(batches) > 1:
            warnings.append(f"Multiple batch numbers found: {len(batches)} different batches")

        # Optimized measurement count check - exclude Notes
        non_note_records = [r for r in records if r.get("evaluation_type") != "Note"]
        if non_note_records:
            measurement_counts = []
            for record in non_note_records:
                measurements = record.get("measurements", [])
                if isinstance(measurements, list):
                    measurement_counts.append(len(measurements))
                else:
                    measurement_counts.append(0)
            
            if measurement_counts:
                min_measurements = min(measurement_counts)
                max_measurements = max(measurement_counts)
                if max_measurements - min_measurements > 2:
                    warnings.append(f"Inconsistent measurement counts: {min_measurements} to {max_measurements}")

        # Quick nominal consistency check (sample first 10 for performance)
        sample_records = records[:10] if len(records) > 10 else records
        element_nominals = {}
        for record in sample_records:
            eid = record.get("element_id")
            nominal = record.get("nominal")
            if eid and nominal is not None:
                try:
                    nominal_val = float(nominal)
                    if eid in element_nominals:
                        if abs(element_nominals[eid] - nominal_val) > 1e-6:
                            warnings.append(f"Inconsistent nominal values detected for element {eid}")
                            break  # Exit early to avoid spam
                    else:
                        element_nominals[eid] = nominal_val
                except (ValueError, TypeError):
                    pass

        # Quick check for missing critical fields
        missing_field_count = 0
        for record in records[:20]:  # Sample for performance
            evaluation_type = record.get("evaluation_type", "Normal")
            is_note = evaluation_type == "Note"
            
            if is_note:
                critical_fields = ["element_id", "description"]
            else:
                critical_fields = ["element_id", "description", "nominal"]
                
            for field in critical_fields:
                if not record.get(field):
                    missing_field_count += 1
                    break  # One missing field per record is enough

        if missing_field_count > 0:
            warnings.append(f"Approximately {missing_field_count} records missing required fields")

        # Quick measurement availability check - exclude Notes
        empty_measurement_count = 0
        for record in non_note_records[:20]:  # Sample for performance
            measurements = record.get("measurements", [])
            if not measurements or len(measurements) == 0:
                empty_measurement_count += 1

        if empty_measurement_count > 0:
            warnings.append(f"Approximately {empty_measurement_count} non-Note records have no measurements")

        # Quick statistical validity check
        if len(non_note_records) > 0:
            single_measurement_sample = sum(
                1 for record in non_note_records[:20] 
                if record.get("measurements") and len(record.get("measurements", [])) == 1
            )
            if single_measurement_sample > len(non_note_records[:20]) * 0.5:
                warnings.append("Many records have only single measurements - statistical analysis limited")

        return warnings

    except Exception as e:
        logger.error(f"Batch validation error: {str(e)}")
        return [f"Batch validation error: {str(e)}"]


def sanitize_record_optimized(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized record sanitization with minimal copying
    
    Args:
        record: Raw measurement record dictionary
    Returns:
        Cleaned and sanitized record dictionary
    """
    logger = logging.getLogger(__name__)
    
    # Work on the original record to avoid copying (careful approach)
    try:
        # Clean string fields in-place
        string_fields = ["element_id", "description", "batch", "cavity", "class", "datum_element_id"]
        for field in string_fields:
            if field in record and record[field] is not None:
                cleaned = str(record[field]).strip()
                record[field] = cleaned if cleaned else None

        # Clean numeric fields
        numeric_fields = ["nominal", "datum_nominal", "datum_measurement"]
        for field in numeric_fields:
            if field in record and record[field] is not None:
                try:
                    record[field] = float(record[field])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {field} to float: {record[field]}")
                    record[field] = None

        # Clean measurements list efficiently
        measurements = record.get("measurements")
        if measurements is not None:
            if not isinstance(measurements, list):
                # Try to convert single value to list
                try:
                    record["measurements"] = [float(measurements)]
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert measurements to list: {measurements}")
                    record["measurements"] = []
            else:
                # Clean measurements in-place
                clean_measurements = []
                for measurement in measurements:
                    if measurement is not None:
                        try:
                            clean_measurements.append(float(measurement))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping invalid measurement: {measurement}")
                record["measurements"] = clean_measurements

        return record

    except Exception as e:
        logger.error(f"Error sanitizing record: {str(e)}")
        return record


def prepare_record_for_analysis_optimized(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized record preparation for dimensional analysis
    Args:
        record: Raw measurement record
    Returns:
        Prepared record ready for DimensionalAnalyzer.analyze_row()
    """
    logger = logging.getLogger(__name__)

    # Sanitize in-place for performance
    prepared = sanitize_record_optimized(record)

    # Quick validation
    if not validate_measurements(prepared):
        logger.error(f"Record validation failed for element {prepared.get('element_id', 'Unknown')}")
        return prepared  # Return as-is, analyzer will handle the error

    # Set default values efficiently
    defaults = {
        "batch": "Unknown",
        "cavity": "Unknown", 
        "description": "",
    }
    
    for field, default_value in defaults.items():
        if field not in prepared or prepared[field] is None:
            prepared[field] = default_value

    # Ensure element_id is string
    if "element_id" in prepared and prepared["element_id"] is not None:
        prepared["element_id"] = str(prepared["element_id"])

    return prepared


def validate_process_capability_requirements(record: Dict[str, Any]) -> List[str]:
    """
    Validate requirements for process capability calculation
    
    Args:
        record: Measurement record dictionary
    Returns:
        List of validation warnings
    """
    warnings = []
    
    classe = record.get("class", "")
    if not classe or classe.upper() not in ["CC", "SC", "IC"]:
        return warnings  # No process capability needed
    
    evaluation_type = record.get("evaluation_type", "Normal")
    if evaluation_type in ["Note", "Basic", "Informative"]:
        warnings.append(f"Process capability not calculated for {evaluation_type} entries")
        return warnings
    
    measurements = record.get("measurements", [])
    if not measurements or len(measurements) < 2:
        warnings.append("Process capability requires at least 2 measurements")
    
    if not record.get("lower_tolerance") or not record.get("upper_tolerance"):
        warnings.append("Process capability requires both upper and lower tolerances")
    
    return warnings


# Batch processing functions for better performance
def validate_records_batch(records: List[Dict[str, Any]], max_workers: int = 4) -> tuple[List[bool], List[str]]:
    """
    Batch validate multiple records with optional parallel processing
    
    Args:
        records: List of measurement records
        max_workers: Maximum number of worker threads (set to 1 to disable threading)
    Returns:
        Tuple of (validation_results, batch_warnings)
    """
    if max_workers == 1 or len(records) < 10:
        # Serial processing for small batches
        validation_results = [validate_measurements(record) for record in records]
        batch_warnings = validate_batch_consistency_optimized(records)
    else:
        # Could implement parallel processing here if needed
        # For now, use serial processing
        validation_results = [validate_measurements(record) for record in records]
        batch_warnings = validate_batch_consistency_optimized(records)
    
    return validation_results, batch_warnings