# src/models/dimensional/measurement_validator.py
import logging
from typing import Dict, List, Any


def validate_measurements(record: Dict[str, Any]) -> bool:
    """
    Validate measurement record for dimensional analysis

    Args:
        record: Dictionary containing measurement data

    Returns:
        True if record is valid, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        # FIX: Check if this is a Note entry
        evaluation_type = record.get("evaluation_type", "Normal")
        is_note = evaluation_type == "Note"

        # Check required fields - different for Notes
        if is_note:
            required_fields = ["element_id", "description"]  # Notes don't need nominal or measurements
        else:
            required_fields = ["element_id", "description", "nominal"]
            
        for field in required_fields:
            if not record.get(field):
                logger.warning(f"Missing required field '{field}' in record")
                return False

        # FIX: Validate nominal value only for non-Note entries
        if not is_note:
            try:
                nominal = float(record["nominal"])
                if not (-1e6 <= nominal <= 1e6):  # Reasonable range check
                    logger.warning(f"Nominal value {nominal} is outside reasonable range")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid nominal value: {record.get('nominal')}")
                return False

        # FIX: Validate measurements - optional for Notes
        measurements = record.get("measurements", [])
        if not is_note and not measurements:
            logger.warning("No measurements provided for non-Note entry")
            return False

        if measurements:  # Only validate if measurements exist
            if not isinstance(measurements, list):
                logger.warning("Measurements must be a list")
                return False

            # Check measurement values
            valid_measurements = []
            for i, measurement in enumerate(measurements):
                try:
                    value = float(measurement)
                    if not (-1e6 <= value <= 1e6):  # Reasonable range check
                        logger.warning(
                            f"Measurement {i + 1} value {value} is outside reasonable range"
                        )
                        continue
                    valid_measurements.append(value)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid measurement value at position {i + 1}: {measurement}"
                    )
                    continue

            # FIX: For non-Note entries, require at least one valid measurement
            if not is_note and not valid_measurements:
                logger.warning("No valid measurements found for non-Note entry")
                return False

            # Update record with valid measurements only
            record["measurements"] = valid_measurements

        # Validate tolerance if provided
        tolerance = record.get("tolerance")
        if tolerance is not None:
            if not _validate_tolerance(tolerance):
                logger.warning(f"Invalid tolerance format: {tolerance}")
                # Don't fail validation, just warn

        # Validate optional fields
        batch = record.get("batch")
        if batch is not None and not str(batch).strip():
            logger.warning("Empty batch value")

        cavity = record.get("cavity")
        if cavity is not None and not str(cavity).strip():
            logger.warning("Empty cavity value")
        
        classe = record.get("classe")
        if classe is not None and not str(classe).strip():
            logger.warning("Empty class value")

        # Validate datum references if present
        datum_element_id = record.get("datum_element_id")
        datum_nominal = record.get("datum_nominal")
        datum_measurement = record.get("datum_measurement")

        if datum_element_id is not None:
            if datum_nominal is not None:
                try:
                    float(datum_nominal)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid datum nominal value: {datum_nominal}")

            if datum_measurement is not None:
                try:
                    float(datum_measurement)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid datum measurement value: {datum_measurement}"
                    )

        return True

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False


def _validate_tolerance(tolerance: Any) -> bool:
    """
    Validate tolerance format

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
                return True  # Empty tolerance list is valid (means no tolerance)
            elif len(tolerance) <= 2:
                for tol in tolerance:
                    try:
                        tol_val = float(tol)
                        if not (-1e6 <= tol_val <= 1e6):
                            return False
                    except (ValueError, TypeError):
                        return False
                return True
            else:
                return False  # Too many tolerance values

        elif isinstance(tolerance, str):
            if not tolerance.strip():
                return True  # Empty string is valid

            # Try to parse as number
            try:
                float(tolerance)
                return True
            except ValueError:
                pass

            # Try to parse as range (e.g., "+0.1/-0.05")
            if "/" in tolerance:
                parts = tolerance.replace("+", "").split("/")
                if len(parts) == 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return True
                    except ValueError:
                        return False

            return False

        else:
            return False

    except Exception:
        return False


def validate_batch_consistency(records: List[Dict[str, Any]]) -> List[str]:
    """
    Validate consistency across a batch of measurement records

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
        # Check for duplicate element IDs
        element_ids = [record.get("element_id") for record in records]
        element_id_counts = {}
        for eid in element_ids:
            if eid:
                element_id_counts[eid] = element_id_counts.get(eid, 0) + 1

        duplicates = [eid for eid, count in element_id_counts.items() if count > 1]
        if duplicates:
            warnings.append(f"Duplicate element IDs found: {', '.join(duplicates)}")

        # Check batch consistency
        batches = set(record.get("batch") for record in records if record.get("batch"))
        if len(batches) > 1:
            warnings.append(
                f"Multiple batch numbers found: {', '.join(map(str, batches))}"
            )

        # FIX: Check measurement count consistency - exclude Notes
        non_note_records = [r for r in records if r.get("evaluation_type") != "Note"]
        if non_note_records:
            measurement_counts = [len(record.get("measurements", [])) for record in non_note_records]
            min_measurements = min(measurement_counts) if measurement_counts else 0
            max_measurements = max(measurement_counts) if measurement_counts else 0

            if max_measurements - min_measurements > 2:
                warnings.append(
                    f"Inconsistent measurement counts: {min_measurements} to {max_measurements}"
                )

        # Check nominal value consistency for same element IDs
        element_nominals = {}
        for record in records:
            eid = record.get("element_id")
            nominal = record.get("nominal")
            if eid and nominal is not None:
                try:
                    nominal_val = float(nominal)
                    if eid in element_nominals:
                        if abs(element_nominals[eid] - nominal_val) > 1e-6:
                            warnings.append(
                                f"Inconsistent nominal values for element {eid}"
                            )
                    else:
                        element_nominals[eid] = nominal_val
                except (ValueError, TypeError):
                    pass

        # Check tolerance consistency for same element IDs
        element_tolerances = {}
        for record in records:
            eid = record.get("element_id")
            tolerance = record.get("tolerance")
            if eid and tolerance is not None:
                if eid in element_tolerances:
                    if element_tolerances[eid] != tolerance:
                        warnings.append(
                            f"Inconsistent tolerance values for element {eid}"
                        )
                else:
                    element_tolerances[eid] = tolerance

        # FIX: Check for missing critical fields across all records - different for Notes
        for record in records:
            is_note = record.get("evaluation_type") == "Note"
            if is_note:
                critical_fields = ["element_id", "description"]
            else:
                critical_fields = ["element_id", "description", "nominal", "measurements"]
                
            for field in critical_fields:
                if not record.get(field):
                    warnings.append(f"Record {record.get('element_id', 'Unknown')} missing required field '{field}'")

        # FIX: Check for empty measurement lists - exclude Notes
        empty_measurements = sum(
            1
            for record in records
            if record.get("evaluation_type") != "Note" and (
                not record.get("measurements") or len(record.get("measurements", [])) == 0
            )
        )
        if empty_measurements > 0:
            warnings.append(f"{empty_measurements} non-Note records have no measurements")

        # Check for statistical validity concerns - exclude Notes
        non_note_with_measurements = [
            record for record in records 
            if record.get("evaluation_type") != "Note" and record.get("measurements")
        ]
        
        if non_note_with_measurements:
            single_measurement_count = sum(
                1 for record in non_note_with_measurements 
                if len(record.get("measurements", [])) == 1
            )
            if single_measurement_count > len(non_note_with_measurements) * 0.5:
                warnings.append(
                    "Over 50% of measurement records have only single measurements - statistical analysis limited"
                )

        # Check for reasonable measurement ranges - exclude Notes
        all_measurements = []
        for record in records:
            if record.get("evaluation_type") != "Note":
                measurements = record.get("measurements", [])
                try:
                    all_measurements.extend(
                        [float(m) for m in measurements if m is not None]
                    )
                except (ValueError, TypeError):
                    pass

        if all_measurements:
            min_val = min(all_measurements)
            max_val = max(all_measurements)
            range_val = max_val - min_val

            # Check for suspiciously large ranges
            if range_val > 1000:
                warnings.append(
                    f"Very large measurement range detected: {range_val:.2f}"
                )

            # Check for all measurements being identical (potential data entry error)
            if len(set(all_measurements)) == 1 and len(all_measurements) > 1:
                warnings.append(
                    "All measurements are identical - possible data entry error"
                )

        # Check datum reference consistency
        datum_records = [record for record in records if record.get("datum_element_id")]
        if datum_records:
            datum_elements = set(
                record.get("datum_element_id") for record in datum_records
            )

            # Check if datum elements are also present as regular elements
            regular_elements = set(record.get("element_id") for record in records)
            missing_datums = datum_elements - regular_elements
            if missing_datums:
                warnings.append(
                    f"Datum elements not found in records: {', '.join(missing_datums)}"
                )

            # Check for consistent datum values
            for datum_id in datum_elements:
                datum_nominals = set()
                datum_measurements = set()

                for record in datum_records:
                    if record.get("datum_element_id") == datum_id:
                        if record.get("datum_nominal") is not None:
                            try:
                                datum_nominals.add(float(record.get("datum_nominal")))
                            except (ValueError, TypeError):
                                pass
                        if record.get("datum_measurement") is not None:
                            try:
                                datum_measurements.add(
                                    float(record.get("datum_measurement"))
                                )
                            except (ValueError, TypeError):
                                pass

                if len(datum_nominals) > 1:
                    warnings.append(f"Inconsistent datum nominal values for {datum_id}")
                if len(datum_measurements) > 1:
                    warnings.append(
                        f"Inconsistent datum measurement values for {datum_id}"
                    )

        return warnings

    except Exception as e:
        logger.error(f"Batch validation error: {str(e)}")
        return [f"Batch validation error: {str(e)}"]


def sanitize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and clean measurement record data

    Args:
        record: Raw measurement record dictionary

    Returns:
        Cleaned and sanitized record dictionary
    """
    logger = logging.getLogger(__name__)
    sanitized = record.copy()

    try:
        # Clean string fields
        string_fields = [
            "element_id",
            "description",
            "batch",
            "cavity",
            "class"
            "datum_element_id",
        ]
        for field in string_fields:
            if field in sanitized and sanitized[field] is not None:
                sanitized[field] = str(sanitized[field]).strip()
                if not sanitized[field]:  # Empty after stripping
                    sanitized[field] = None

        # Clean numeric fields
        numeric_fields = ["nominal", "datum_nominal", "datum_measurement"]
        for field in numeric_fields:
            if field in sanitized and sanitized[field] is not None:
                try:
                    sanitized[field] = float(sanitized[field])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not convert {field} to float: {sanitized[field]}"
                    )
                    sanitized[field] = None

        # Clean measurements list
        if "measurements" in sanitized:
            measurements = sanitized["measurements"]
            if measurements is not None:
                if not isinstance(measurements, list):
                    # Try to convert single value to list
                    try:
                        sanitized["measurements"] = [float(measurements)]
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not convert measurements to list: {measurements}"
                        )
                        sanitized["measurements"] = []
                else:
                    # Clean each measurement
                    clean_measurements = []
                    for i, measurement in enumerate(measurements):
                        if measurement is not None:
                            try:
                                clean_measurements.append(float(measurement))
                            except (ValueError, TypeError):
                                logger.warning(
                                    f"Skipping invalid measurement at position {i}: {measurement}"
                                )
                        else:
                            logger.warning(f"Skipping None measurement at position {i}")
                    sanitized["measurements"] = clean_measurements

        # Clean tolerance field (keep as-is since it can be various formats)
        # The tolerance validation is handled separately in _validate_tolerance

        return sanitized

    except Exception as e:
        logger.error(f"Error sanitizing record: {str(e)}")
        return record  # Return original if sanitization fails


def validate_dimensional_result_compatibility(record: Dict[str, Any]) -> List[str]:
    """
    Validate that a record is compatible with DimensionalResult requirements

    Args:
        record: Measurement record dictionary

    Returns:
        List of compatibility warnings
    """
    warnings = []

    # Check required fields for DimensionalResult
    required_fields = {
        "element_id": str,
        "batch": str,
        "cavity": str,
        "description": str,
        "nominal": (int, float),
        "measurements": list,
    }

    for field, expected_type in required_fields.items():
        if field not in record or record[field] is None:
            warnings.append(f"Missing required field '{field}' for DimensionalResult")
        elif not isinstance(record[field], expected_type):
            if field == "nominal" and isinstance(record[field], str):
                try:
                    float(record[field])  # Check if string can be converted to float
                except ValueError:
                    warnings.append(
                        f"Field '{field}' cannot be converted to numeric type"
                    )
            else:
                warnings.append(
                    f"Field '{field}' has incorrect type. Expected {expected_type.__name__}, got {type(record[field]).__name__}"
                )

    # Check measurements list contents
    measurements = record.get("measurements", [])
    if measurements:
        non_numeric_count = 0
        for i, measurement in enumerate(measurements):
            try:
                float(measurement)
            except (ValueError, TypeError):
                non_numeric_count += 1

        if non_numeric_count > 0:
            warnings.append(
                f"{non_numeric_count} measurements cannot be converted to numeric values"
            )

    # Check optional fields that need specific types
    optional_numeric_fields = ["datum_nominal", "datum_measurement"]
    for field in optional_numeric_fields:
        if field in record and record[field] is not None:
            try:
                float(record[field])
            except (ValueError, TypeError):
                warnings.append(
                    f"Optional field '{field}' cannot be converted to numeric type"
                )

    return warnings


def prepare_record_for_analysis(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare and validate a record for dimensional analysis

    Args:
        record: Raw measurement record

    Returns:
        Prepared record ready for DimensionalAnalyzer.analyze_row()
    """
    logger = logging.getLogger(__name__)

    # First sanitize the record
    prepared = sanitize_record(record)

    # Validate the record
    if not validate_measurements(prepared):
        logger.error(
            f"Record validation failed for element {prepared.get('element_id', 'Unknown')}"
        )
        return prepared  # Return as-is, analyzer will handle the error

    # Check compatibility with DimensionalResult
    compatibility_warnings = validate_dimensional_result_compatibility(prepared)
    if compatibility_warnings:
        logger.warning(
            f"Compatibility issues for element {prepared.get('element_id', 'Unknown')}: {compatibility_warnings}"
        )

    # Set default values for optional fields that DimensionalResult expects
    if "batch" not in prepared or prepared["batch"] is None:
        prepared["batch"] = "Unknown"

    if "cavity" not in prepared or prepared["cavity"] is None:
        prepared["cavity"] = "Unknown"

    if "description" not in prepared or prepared["description"] is None:
        prepared["description"] = ""

    # Ensure element_id is string
    if "element_id" in prepared and prepared["element_id"] is not None:
        prepared["element_id"] = str(prepared["element_id"])

    return prepared
