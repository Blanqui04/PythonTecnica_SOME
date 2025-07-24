# src/models/dimensional/gdt_interpreter.py
import re
import logging
from typing import Dict, List, Tuple


class GDTInterpreter:
    """Enhanced GD&T interpreter for dimensional analysis"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # GD&T symbol mappings
        self.gdt_symbols = {
            # Form tolerances
            "straightness": "⏤",
            "flatness": "⏤",
            "circularity": "○",
            "cylindricity": "⌭",
            # Orientation tolerances
            "parallelism": "∥",
            "perpendicularity": "⊥",
            "angularity": "∠",
            # Location tolerances
            "position": "⌖",
            "concentricity": "◎",
            "symmetry": "≡",
            # Profile tolerances
            "profile_line": "⌒",
            "profile_surface": "⌓",
            "profile": "⌓",
            # Runout tolerances
            "runout": "↗",
            "total_runout": "↗↗",
            # Material condition modifiers
            "mmc": "Ⓜ",
            "lmc": "Ⓛ",
            "rfs": "Ⓢ",
            # Common symbols
            "diameter": "Ø",
            "radius": "R",
            "spherical_diameter": "SØ",
            "spherical_radius": "SR",
        }

        # Pattern for GD&T callouts
        self.gdt_patterns = {
            "position": re.compile(
                r"position\s+([\d.,]+)\s*(\([MLS]\))?\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?",
                re.IGNORECASE,
            ),
            "parallelism": re.compile(
                r"parallelism\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "perpendicularity": re.compile(
                r"perpendicularity\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?",
                re.IGNORECASE,
            ),
            "angularity": re.compile(
                r"angularity\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "profile": re.compile(
                r"profile\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "flatness": re.compile(r"flatness\s+([\d.,]+)", re.IGNORECASE),
            "circularity": re.compile(r"circularity\s+([\d.,]+)", re.IGNORECASE),
            "cylindricity": re.compile(r"cylindricity\s+([\d.,]+)", re.IGNORECASE),
            "straightness": re.compile(
                r"straightness\s+([\d.,]+)\s*(\([MLS]\))?", re.IGNORECASE
            ),
            "concentricity": re.compile(
                r"concentricity\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "symmetry": re.compile(
                r"symmetry\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "runout": re.compile(
                r"runout\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?", re.IGNORECASE
            ),
            "total_runout": re.compile(
                r"total\s+runout\s+([\d.,]+)\s*([A-Z]\s*[A-Z]?\s*[A-Z]?)?",
                re.IGNORECASE,
            ),
        }

        # Material condition patterns
        self.material_condition_patterns = {
            "M": re.compile(r"\(M\)", re.IGNORECASE),
            "L": re.compile(r"\(L\)", re.IGNORECASE),
            "S": re.compile(r"\(S\)", re.IGNORECASE),
        }

    def parse_gdt_description(self, description: str) -> Dict[str, any]:
        """
        Parse GD&T information from description

        Args:
            description: Description string containing GD&T callout

        Returns:
            Dictionary containing parsed GD&T information
        """
        gdt_info = {
            "has_gdt": False,
            "tolerance_type": None,
            "tolerance_value": None,
            "material_condition": None,
            "datum_references": [],
            "feature_type": "dimension",
            "warnings": [],
        }

        try:
            # Check each GD&T pattern
            for tolerance_type, pattern in self.gdt_patterns.items():
                match = pattern.search(description)
                if match:
                    gdt_info["has_gdt"] = True
                    gdt_info["tolerance_type"] = tolerance_type

                    # Extract tolerance value
                    try:
                        gdt_info["tolerance_value"] = float(
                            match.group(1).replace(",", ".")
                        )
                    except (ValueError, AttributeError):
                        gdt_info["warnings"].append(
                            f"Could not parse tolerance value: {match.group(1)}"
                        )

                    # Extract material condition (if present)
                    if len(match.groups()) > 1 and match.group(2):
                        mc_text = match.group(2).strip("()")
                        gdt_info["material_condition"] = mc_text.upper()

                    # Extract datum references (if present)
                    if len(match.groups()) > 2 and match.group(3):
                        datum_text = match.group(3).strip()
                        datums = re.findall(r"[A-Z]", datum_text.upper())
                        gdt_info["datum_references"] = datums

                    break

            # Determine feature type
            gdt_info["feature_type"] = self._determine_feature_type_from_gdt(
                description, gdt_info
            )

            # Additional validation
            warnings = self._validate_gdt_callout(gdt_info)
            gdt_info["warnings"].extend(warnings)

        except Exception as e:
            self.logger.error(
                f"Error parsing GD&T description '{description}': {str(e)}"
            )
            gdt_info["warnings"].append(f"GD&T parsing error: {str(e)}")

        return gdt_info

    def _determine_feature_type_from_gdt(self, description: str, gdt_info: Dict) -> str:
        """Determine feature type based on GD&T and description"""
        desc_lower = description.lower()
        tolerance_type = gdt_info.get("tolerance_type")

        # GD&T-specific feature types
        if tolerance_type in ["position", "concentricity"]:
            if any(keyword in desc_lower for keyword in ["hole", "bore", "orifice"]):
                return "hole_position"
            elif any(keyword in desc_lower for keyword in ["pin", "shaft", "boss"]):
                return "pin_position"
            else:
                return "feature_position"

        elif tolerance_type in ["parallelism", "perpendicularity", "angularity"]:
            return "orientation"

        elif tolerance_type in ["profile", "profile_line", "profile_surface"]:
            return "profile"

        elif tolerance_type in ["flatness", "straightness"]:
            return "form"

        elif tolerance_type in ["circularity", "cylindricity"]:
            return "form_circular"

        elif tolerance_type in ["runout", "total_runout"]:
            return "runout"

        # Fallback to traditional feature type determination
        feature_mappings = {
            "diameter": ["diam", "ø", "circle", "dia", "diameter"],
            "hole": ["hole", "bore", "orifice"],
            "slot": ["slot", "ranura", "groove", "channel"],
            "pin": ["pin", "shaft", "rod", "boss"],
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

        return "dimension"

    def _validate_gdt_callout(self, gdt_info: Dict) -> List[str]:
        """Validate GD&T callout for common issues"""
        warnings = []

        tolerance_type = gdt_info.get("tolerance_type")
        material_condition = gdt_info.get("material_condition")
        datum_references = gdt_info.get("datum_references", [])

        if not gdt_info.get("has_gdt"):
            return warnings

        # Check material condition applicability
        if material_condition:
            if tolerance_type in ["flatness", "circularity", "cylindricity"]:
                warnings.append(
                    f"Material condition modifier not applicable to {tolerance_type}"
                )
            elif tolerance_type == "straightness" and material_condition in ["L", "S"]:
                warnings.append("LMC/RFS not typically used with straightness of axis")

        # Check datum reference requirements
        if tolerance_type in [
            "position",
            "parallelism",
            "perpendicularity",
            "angularity",
            "profile",
            "concentricity",
            "symmetry",
            "runout",
            "total_runout",
        ]:
            if not datum_references:
                warnings.append(f"{tolerance_type} typically requires datum references")
            elif tolerance_type == "position" and len(datum_references) < 2:
                warnings.append(
                    "Position tolerance typically requires at least 2 datum references"
                )

        elif tolerance_type in ["flatness", "circularity", "cylindricity"]:
            if datum_references:
                warnings.append(f"{tolerance_type} should not have datum references")

        # Check tolerance value reasonableness
        tolerance_value = gdt_info.get("tolerance_value")
        if tolerance_value:
            if tolerance_value <= 0:
                warnings.append("Tolerance value must be positive")
            elif tolerance_value > 100:
                warnings.append("Tolerance value seems unusually large")
            elif tolerance_value < 0.001:
                warnings.append("Tolerance value seems unusually small")

        return warnings

    def convert_gdt_to_tolerance_range(
        self, gdt_info: Dict, nominal: float
    ) -> Tuple[float, float]:
        """
        Convert GD&T callout to equivalent bilateral tolerance range

        Args:
            gdt_info: Parsed GD&T information
            nominal: Nominal dimension value

        Returns:
            Tuple of (lower_tolerance, upper_tolerance)
        """
        if not gdt_info.get("has_gdt") or not gdt_info.get("tolerance_value"):
            return 0.0, 0.0

        tolerance_type = gdt_info.get("tolerance_type")
        tolerance_value = gdt_info.get("tolerance_value")
        material_condition = gdt_info.get("material_condition")

        # Form tolerances - typically unilateral positive
        if tolerance_type in [
            "flatness",
            "circularity",
            "cylindricity",
            "straightness",
        ]:
            return 0.0, tolerance_value

        # Position tolerance - depends on material condition
        elif tolerance_type == "position":
            if material_condition == "M":  # MMC
                # At MMC, get full tolerance; at LMC get bonus
                return -tolerance_value, tolerance_value
            elif material_condition == "L":  # LMC
                # At LMC, get full tolerance; at MMC get bonus
                return -tolerance_value, tolerance_value
            else:  # RFS or no modifier
                return -tolerance_value, tolerance_value

        # Orientation tolerances - typically bilateral
        elif tolerance_type in ["parallelism", "perpendicularity", "angularity"]:
            return -tolerance_value, tolerance_value

        # Profile tolerances - bilateral unless otherwise specified
        elif tolerance_type in ["profile", "profile_line", "profile_surface"]:
            return -tolerance_value / 2, tolerance_value / 2

        # Runout tolerances - unilateral positive
        elif tolerance_type in ["runout", "total_runout"]:
            return 0.0, tolerance_value

        # Default bilateral
        else:
            return -tolerance_value, tolerance_value

    def format_gdt_display(self, description: str) -> str:
        """
        Format description with proper GD&T symbols for display

        Args:
            description: Raw description text

        Returns:
            Formatted description with GD&T symbols
        """
        formatted = description

        # Replace text with symbols
        replacements = {
            # Geometric characteristics
            "position": "⌖",
            "concentricity": "◎",
            "symmetry": "≡",
            "parallelism": "∥",
            "perpendicularity": "⊥",
            "angularity": "∠",
            "profile line": "⌒",
            "profile surface": "⌓",
            "profile": "⌓",
            "circularity": "○",
            "cylindricity": "⌭",
            "flatness": "⏤",
            "straightness": "⏤",
            "runout": "↗",
            "total runout": "↗↗",
            # Material conditions
            "(M)": "Ⓜ",
            "(L)": "Ⓛ",
            "(S)": "Ⓢ",
            # Common symbols
            "diameter": "Ø",
            "dia": "Ø",
            "diam": "Ø",
        }

        for text, symbol in replacements.items():
            # Case insensitive replacement
            pattern = re.compile(re.escape(text), re.IGNORECASE)
            formatted = pattern.sub(symbol, formatted)

        return formatted

    def extract_tolerance_from_gdt(
        self, description: str, nominal: float = 0.0
    ) -> Tuple[List[float], List[str]]:
        """
        Extract tolerance values from GD&T description

        Args:
            description: Description containing GD&T callout
            nominal: Nominal dimension (for context)

        Returns:
            Tuple of (tolerance_list, warnings)
        """
        warnings = []

        # Parse GD&T information
        gdt_info = self.parse_gdt_description(description)

        if not gdt_info["has_gdt"]:
            return [], ["No GD&T callout detected"]

        # Convert to tolerance range
        lower_tol, upper_tol = self.convert_gdt_to_tolerance_range(gdt_info, nominal)

        # Add any parsing warnings
        warnings.extend(gdt_info.get("warnings", []))

        return [lower_tol, upper_tol], warnings


def create_enhanced_gdt_flags(description: str) -> Dict[str, bool]:
    """
    Create enhanced GD&T flags dictionary from description

    Args:
        description: Description string

    Returns:
        Dictionary of GD&T flags
    """
    interpreter = GDTInterpreter()
    gdt_info = interpreter.parse_gdt_description(description)

    # Create flags dictionary
    flags = {
        # Basic flags
        "HAS_GDT": gdt_info["has_gdt"],
        "MMC": gdt_info["material_condition"] == "M",
        "LMC": gdt_info["material_condition"] == "L",
        "RFS": gdt_info["material_condition"] == "S",
        # Tolerance types
        "POSITION": gdt_info["tolerance_type"] == "position",
        "PARALLELISM": gdt_info["tolerance_type"] == "parallelism",
        "PERPENDICULARITY": gdt_info["tolerance_type"] == "perpendicularity",
        "ANGULARITY": gdt_info["tolerance_type"] == "angularity",
        "PROFILE": gdt_info["tolerance_type"]
        in ["profile", "profile_line", "profile_surface"],
        "FLATNESS": gdt_info["tolerance_type"] == "flatness",
        "CIRCULARITY": gdt_info["tolerance_type"] == "circularity",
        "CYLINDRICITY": gdt_info["tolerance_type"] == "cylindricity",
        "STRAIGHTNESS": gdt_info["tolerance_type"] == "straightness",
        "CONCENTRICITY": gdt_info["tolerance_type"] == "concentricity",
        "SYMMETRY": gdt_info["tolerance_type"] == "symmetry",
        "RUNOUT": gdt_info["tolerance_type"] == "runout",
        "TOTAL_RUNOUT": gdt_info["tolerance_type"] == "total_runout",
        # Feature characteristics
        "HAS_DATUMS": len(gdt_info["datum_references"]) > 0,
        "DATUM_COUNT": len(gdt_info["datum_references"]),
        # Legacy compatibility flags
        "MIN": False,  # Deprecated
        "MAX": False,  # Deprecated
    }

    return flags
