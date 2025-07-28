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
            "flatness": "⏥",
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

        # Enhanced GD&T patterns with more flexible matching
        self.gdt_patterns = {
            # Position patterns - more flexible
            "position": re.compile(
                r"(?:position|true\s*position|tp|⌖)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
            
            # Parallelism with symbol support
            "parallelism": re.compile(
                r"(?:parallelism|∥)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            
            # Perpendicularity with symbol support
            "perpendicularity": re.compile(
                r"(?:perpendicularity|⊥)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
            
            # Angularity
            "angularity": re.compile(
                r"(?:angularity|∠)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            
            # Profile - enhanced to catch bilateral notation
            "profile": re.compile(
                r"(?:profile|⌓|⌒)\s*(?:of\s*(?:line|surface))?\s*[øΦ]?\s*([\d.,]+)\s*(?:bilateral|bil)?\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            
            # Form tolerances
            "flatness": re.compile(r"(?:flatness|⏥)\s*[øΦ]?\s*([\d.,]+)", re.IGNORECASE),
            "circularity": re.compile(r"(?:circularity|roundness|○)\s*[øΦ]?\s*([\d.,]+)", re.IGNORECASE),
            "cylindricity": re.compile(r"(?:cylindricity|⌭)\s*[øΦ]?\s*([\d.,]+)", re.IGNORECASE),
            "straightness": re.compile(
                r"(?:straightness|⏤)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?", re.IGNORECASE
            ),
            
            # Location tolerances
            "concentricity": re.compile(
                r"(?:concentricity|◎)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            "symmetry": re.compile(
                r"(?:symmetry|≡)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            
            # Runout tolerances
            "runout": re.compile(
                r"(?:circular\s*runout|runout|↗)(?!\s*total)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            "total_runout": re.compile(
                r"(?:total\s*runout|↗↗)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
        }

        # Add material condition detection improvements
        self.material_condition_patterns = {
            "M": re.compile(r"[\(Ⓜ]M[\)Ⓜ]|MMC", re.IGNORECASE),
            "L": re.compile(r"[\(Ⓛ]L[\)Ⓛ]|LMC", re.IGNORECASE),
            "S": re.compile(r"[\(Ⓢ]S[\)Ⓢ]|RFS", re.IGNORECASE),
        }

    def parse_gdt_description(self, description: str) -> Dict[str, any]:
        """Enhanced GD&T parsing with better error handling"""
        gdt_info = {
            "has_gdt": False,
            "tolerance_type": None,
            "tolerance_value": None,
            "material_condition": None,
            "datum_references": [],
            "feature_type": "dimension",
            "warnings": [],
            "is_bilateral_profile": False,  # New flag for bilateral profiles
        }

        if not description or not description.strip():
            return gdt_info

        try:
            # Check each GD&T pattern
            for tolerance_type, pattern in self.gdt_patterns.items():
                match = pattern.search(description)
                if match:
                    gdt_info["has_gdt"] = True
                    gdt_info["tolerance_type"] = tolerance_type

                    # Extract tolerance value with better error handling
                    try:
                        raw_value = match.group(1).replace(",", ".")
                        gdt_info["tolerance_value"] = float(raw_value)
                        
                        # Check for negative values (shouldn't happen in GD&T)
                        if gdt_info["tolerance_value"] <= 0:
                            gdt_info["warnings"].append(f"Invalid negative/zero tolerance value: {raw_value}")
                            
                    except (ValueError, AttributeError, IndexError) as e:
                        gdt_info["warnings"].append(f"Could not parse tolerance value: {match.group(1) if match.groups() else 'N/A'}")

                    # Extract material condition with improved detection
                    mc_detected = None
                    for mc_type, mc_pattern in self.material_condition_patterns.items():
                        if mc_pattern.search(description):
                            mc_detected = mc_type
                            break
                    
                    if mc_detected:
                        gdt_info["material_condition"] = mc_detected
                    elif len(match.groups()) > 1 and match.group(2):
                        # Fallback to original method
                        mc_text = match.group(2).strip("()")
                        gdt_info["material_condition"] = mc_text.upper()

                    # Extract datum references with improved parsing
                    datum_text = ""
                    if len(match.groups()) > 2 and match.group(3):
                        datum_text = match.group(3).strip()
                    
                    # Also search the entire description for datum references
                    datum_pattern = re.compile(r"(?:datum|ref)\s*[:=]?\s*([A-Z][\s|,]*[A-Z]?[\s|,]*[A-Z]?)", re.IGNORECASE)
                    datum_match = datum_pattern.search(description)
                    if datum_match and not datum_text:
                        datum_text = datum_match.group(1)
                    
                    if datum_text:
                        # Split on common separators
                        datums = re.findall(r"[A-Z]", datum_text.upper())
                        gdt_info["datum_references"] = list(set(datums))  # Remove duplicates

                    # Check for bilateral profile
                    if tolerance_type == "profile" and re.search(r"bilateral|bil", description, re.IGNORECASE):
                        gdt_info["is_bilateral_profile"] = True

                    break

            # If no pattern matched, try a generic GD&T detection
            if not gdt_info["has_gdt"]:
                generic_gdt = re.search(r"[⌖◎≡∥⊥∠⌓⌒○⌭⏥⏤↗][\s]*[\d.,]+", description)
                if generic_gdt:
                    gdt_info["has_gdt"] = True
                    gdt_info["tolerance_type"] = "unknown_gdt"
                    gdt_info["warnings"].append("GD&T symbols detected but pattern not recognized")

            # Determine feature type
            gdt_info["feature_type"] = self._determine_feature_type_from_gdt(description, gdt_info)

            # Additional validation
            warnings = self._validate_gdt_callout(gdt_info)
            gdt_info["warnings"].extend(warnings)

        except Exception as e:
            self.logger.error(f"Error parsing GD&T description '{description}': {str(e)}")
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

    def convert_gdt_to_tolerance_range(self, gdt_info: Dict, nominal: float) -> Tuple[float, float]:
        """Enhanced GD&T to tolerance conversion with better nominal=0 handling"""
        if not gdt_info.get("has_gdt") or not gdt_info.get("tolerance_value"):
            return 0.0, 0.0

        tolerance_type = gdt_info.get("tolerance_type")
        tolerance_value = gdt_info.get("tolerance_value")
        material_condition = gdt_info.get("material_condition")
        is_bilateral_profile = gdt_info.get("is_bilateral_profile", False)

        # Form tolerances - always unilateral positive (deviation from perfect form)
        if tolerance_type in ["flatness", "circularity", "cylindricity", "straightness"]:
            # These are always measured as deviation from perfect form
            # For nominal=0 features, this is still valid
            return 0.0, tolerance_value

        # Position tolerance - depends on feature type and material condition
        elif tolerance_type == "position":
            # Position is always bilateral around true position
            # For holes (internal features): typically bilateral
            # For pins/bosses (external features): typically bilateral
            # Material condition affects bonus tolerance, not base range
            return -tolerance_value, tolerance_value

        # Orientation tolerances - bilateral unless specified otherwise
        elif tolerance_type in ["parallelism", "perpendicularity", "angularity"]:
            # These control orientation, so bilateral makes sense
            return -tolerance_value, tolerance_value

        # Profile tolerances - special handling for nominal=0 and bilateral
        elif tolerance_type in ["profile", "profile_line", "profile_surface"]:
            if is_bilateral_profile:
                # Explicitly bilateral profile
                return -tolerance_value / 2, tolerance_value / 2
            else:
                # Default profile interpretation
                if nominal == 0:
                    # For nominal=0 profiles, often the tolerance is unilateral
                    # (measuring deviation from ideal surface)
                    return 0.0, tolerance_value
                else:
                    # Standard bilateral profile
                    return -tolerance_value / 2, tolerance_value / 2

        # Runout tolerances - always unilateral positive (measuring wobble/variation)
        elif tolerance_type in ["runout", "total_runout"]:
            return 0.0, tolerance_value

        # Concentricity and symmetry - bilateral
        elif tolerance_type in ["concentricity", "symmetry"]:
            return -tolerance_value, tolerance_value

        # Unknown GDT type - conservative bilateral
        else:
            return -tolerance_value, tolerance_value
    

    def debug_gdt_parsing(description):
        interpreter = GDTInterpreter()
        result = interpreter.parse_gdt_description(description)
        print(f"Description: {description}")
        print(f"Parsed: {result}")
        return result

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

    def extract_tolerance_from_gdt(self, description: str, nominal: float = 0.0) -> Tuple[List[float], List[str]]:
        """Enhanced tolerance extraction with better error handling"""
        warnings = []

        if not description or not description.strip():
            return [], ["Empty description provided"]

        # Parse GD&T information
        gdt_info = self.parse_gdt_description(description)

        if not gdt_info["has_gdt"]:
            # Check if this might be a measurement note or informative dimension
            if any(keyword in description.lower() for keyword in ["note", "ref", "informative", "typical", "typ"]):
                warnings.append("Appears to be informative/reference dimension - no tolerance applied")
            else:
                warnings.append("No GD&T callout detected in description")
            return [], warnings

        if not gdt_info.get("tolerance_value"):
            warnings.append("GD&T detected but no valid tolerance value found")
            return [], warnings

        # Convert to tolerance range
        try:
            lower_tol, upper_tol = self.convert_gdt_to_tolerance_range(gdt_info, nominal)
            
            # Validation
            if lower_tol == 0.0 and upper_tol == 0.0:
                warnings.append("GD&T conversion resulted in zero tolerance")
            
            # Add context for nominal=0 cases
            if nominal == 0 and gdt_info.get("tolerance_type") in ["profile", "flatness", "straightness"]:
                warnings.append(f"Nominal=0 with {gdt_info['tolerance_type']} - interpreted as deviation from ideal")

        except Exception as e:
            self.logger.error(f"Error converting GD&T to tolerance range: {str(e)}")
            warnings.append(f"Error in GD&T conversion: {str(e)}")
            return [], warnings

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
