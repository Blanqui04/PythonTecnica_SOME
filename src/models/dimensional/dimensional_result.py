# models/dimensional/dimensional_result.py
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from enum import Enum


class DimensionalStatus(str, Enum):
    OK = "OK"
    NOK = "NOK"
    WARNING = "WARNING"
    TED = "T.E.D."
    TO_CHECK = "TO CHECK"  # New status for notes


@dataclass
class DimensionalResult:
    element_id: str
    batch: str
    cavity: str
    classe: str
    description: str
    nominal: float
    lower_tolerance: Optional[float]
    upper_tolerance: Optional[float]
    measurements: List[float]
    deviation: List[float]
    mean: float
    std_dev: float
    out_of_spec_count: int
    status: DimensionalStatus  # Use Enum here for type safety
    gdt_flags: dict
    # Optional fields for MMC/LMC
    datum_element_id: Optional[str] = None
    effective_tolerance_upper: Optional[float] = None
    effective_tolerance_lower: Optional[float] = None

    # New optional fields
    feature_type: Optional[str] = None
    warnings: Optional[List[str]] = field(default_factory=list)
    measuring_instrument: Optional[str] = None
    evaluation_type: Optional[str] = None
    
    # Process capability fields for classified dimensions (CC, SC, IC)
    pp: Optional[float] = None  # Process performance index
    ppk: Optional[float] = None  # Process performance capability index

    def to_dict(self) -> dict:
        # Convert dataclass to dict, but serialize enums and lists properly
        d = asdict(self)
        # Convert enum to string
        d["status"] = (self.status.value if isinstance(self.status, Enum) else self.status)
        # Join warnings list to simple list if None, ensure JSON serializable
        if d.get("warnings") is None:
            d["warnings"] = []
        return d

    def has_classification(self) -> bool:
        """Check if dimension has a valid classification for process capability"""
        return self.classe and self.classe.upper() in ["CC", "SC", "IC"]
    
    def should_calculate_process_capability(self) -> bool:
        """Determine if process capability should be calculated"""
        return (self.has_classification() and 
                len(self.measurements) > 1 and  # Need multiple measurements
                self.std_dev > 0 and  # Need variation
                self.lower_tolerance is not None and 
                self.upper_tolerance is not None)
    
    def get_tolerance_range(self) -> Optional[float]:
        """Get the total tolerance range"""
        if self.lower_tolerance is not None and self.upper_tolerance is not None:
            return abs(self.upper_tolerance - self.lower_tolerance)
        return None