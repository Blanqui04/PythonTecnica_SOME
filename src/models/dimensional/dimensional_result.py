# models/dimensional/dimensional_result.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


@dataclass
class DimensionalResult:
    element_id: str
    batch: str
    cavity: str
    description: str
    nominal: float
    lower_tolerance: float
    upper_tolerance: float
    measurements: List[float]
    deviation: List[float]
    mean: float
    std_dev: float
    out_of_spec_count: int
    status: str  # "GOOD" or "BAD"
    gdt_flags: dict
    # Optional fields for MMC/LMC
    datum_element_id: Optional[str] = None
    effective_tolerance_upper: Optional[float] = None
    effective_tolerance_lower: Optional[float] = None

    # New optional fields
    feature_type: Optional[str] = None
    warnings: Optional[List[str]] = None


class DimensionalStatus(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    WARNING = "WARNING"
