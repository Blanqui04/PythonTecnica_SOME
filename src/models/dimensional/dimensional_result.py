# models/dimensional/dimensional_result.
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from enum import Enum


class DimensionalStatus(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    WARNING = "WARNING"


@dataclass
class DimensionalResult:
    element_id: str
    batch: str
    cavity: str
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

    def to_dict(self) -> dict:
        # Convert dataclass to dict, but serialize enums and lists properly
        d = asdict(self)
        # Convert enum to string
        d["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        # Join warnings list to simple list if None, ensure JSON serializable
        if d.get("warnings") is None:
            d["warnings"] = []
        return d
