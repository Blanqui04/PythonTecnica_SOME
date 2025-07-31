# src/models/dimensional/gdt_interpreter.py - OPTIMIZED VERSION
import re
import logging
from typing import Dict, List, Tuple
from functools import lru_cache


class GDTInterpreter:
    """Optimized GD&T interpreter with caching"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)  # Reduce logging overhead
        
        # Compile patterns once for better performance
        self._compile_patterns()
        
        # Cache for parsed descriptions
        self._parse_cache = {}

    def _compile_patterns(self):
        """Compile all regex patterns once"""
        self.gdt_patterns = {
            "position": re.compile(
                r"(?:position|true\s*position|tp|⌖)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
            "flatness": re.compile(
                r"(?:flatness|⏥)\s*[øΦ]?\s*([\d.,]+)(?:\s*([A-Z]))?", 
                re.IGNORECASE
            ),
            "parallelism": re.compile(
                r"(?:parallelism|∥)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            "perpendicularity": re.compile(
                r"(?:perpendicularity|⊥)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
            "angularity": re.compile(
                r"(?:angularity|∠)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            "profile": re.compile(
                r"(?:profile|⌓|⌒)\s*(?:of\s*(?:line|surface))?\s*[øΦ]?\s*([\d.,]+)\s*(?:bilateral|bil)?\s*(\([MLS]\))?\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", 
                re.IGNORECASE
            ),
            "circularity": re.compile(r"(?:circularity|roundness|○)\s*[øΦ]?\s*([\d.,]+)", re.IGNORECASE),
            "cylindricity": re.compile(r"(?:cylindricity|⌭)\s*[øΦ]?\s*([\d.,]+)", re.IGNORECASE),
            "straightness": re.compile(
                r"(?:straightness|⏤)\s*[øΦ]?\s*([\d.,]+)\s*(\([MLS]\))?", re.IGNORECASE
            ),
            "concentricity": re.compile(
                r"(?:concentricity|◎)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            "symmetry": re.compile(
                r"(?:symmetry|≡)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            "runout": re.compile(
                r"(?:circular\s*runout|runout|↗)(?!\s*total)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?", re.IGNORECASE
            ),
            "total_runout": re.compile(
                r"(?:total\s*runout|↗↗)\s*[øΦ]?\s*([\d.,]+)\s*([A-Z][\s|]*[A-Z]?[\s|]*[A-Z]?)?",
                re.IGNORECASE,
            ),
        }

        self.material_condition_patterns = {
            "M": re.compile(r"[\(Ⓜ]M[\)Ⓜ]|MMC", re.IGNORECASE),
            "L": re.compile(r"[\(Ⓛ]L[\)Ⓛ]|LMC", re.IGNORECASE),
            "S": re.compile(r"[\(Ⓢ]S[\)Ⓢ]|RFS", re.IGNORECASE),
        }

    @lru_cache(maxsize=256)
    def parse_gdt_description(self, description: str) -> Dict[str, any]:
        """Cached GD&T parsing for performance"""
        if not description or not description.strip():
            return {"has_gdt": False, "warnings": []}
        
        # Check cache first
        if description in self._parse_cache:
            return self._parse_cache[description]
        
        gdt_info = {
            "has_gdt": False,
            "tolerance_type": None,
            "tolerance_value": None,
            "material_condition": None,
            "datum_references": [],
            "feature_type": "dimension",
            "warnings": [],
            "is_bilateral_profile": False,
        }

        try:
            # Check each GD&T pattern (most common first for efficiency)
            priority_patterns = ["position", "flatness", "parallelism", "perpendicularity"]
            other_patterns = [k for k in self.gdt_patterns.keys() if k not in priority_patterns]
            
            for tolerance_type in priority_patterns + other_patterns:
                pattern = self.gdt_patterns[tolerance_type]
                match = pattern.search(description)
                if match:
                    gdt_info["has_gdt"] = True
                    gdt_info["tolerance_type"] = tolerance_type

                    # Extract tolerance value
                    try:
                        raw_value = match.group(1).replace(",", ".")
                        gdt_info["tolerance_value"] = float(raw_value)
                        
                        if gdt_info["tolerance_value"] <= 0:
                            gdt_info["warnings"].append(f"Invalid tolerance value: {raw_value}")
                            
                    except (ValueError, AttributeError, IndexError):
                        gdt_info["warnings"].append("Could not parse tolerance value")

                    # Extract material condition (simplified)
                    for mc_type, mc_pattern in self.material_condition_patterns.items():
                        if mc_pattern.search(description):
                            gdt_info["material_condition"] = mc_type
                            break

                    # Extract datum references (simplified)
                    if len(match.groups()) > 2 and match.group(3):
                        datum_text = match.group(3).strip()
                        datums = re.findall(r"[A-Z]", datum_text.upper())
                        gdt_info["datum_references"] = list(set(datums))

                    # Check for bilateral profile
                    if tolerance_type == "profile" and re.search(r"bilateral|bil", description, re.IGNORECASE):
                        gdt_info["is_bilateral_profile"] = True

                    break

            # Cache the result
            self._parse_cache[description] = gdt_info

        except Exception as e:
            gdt_info["warnings"].append(f"GD&T parsing error: {str(e)}")

        return gdt_info

    def convert_gdt_to_tolerance_range(self, gdt_info: Dict, nominal: float) -> Tuple[float, float]:
        """Optimized GD&T to tolerance conversion"""
        if not gdt_info.get("has_gdt") or not gdt_info.get("tolerance_value"):
            return 0.0, 0.0

        tolerance_type = gdt_info.get("tolerance_type")
        tolerance_value = gdt_info.get("tolerance_value")

        # Fast lookup for tolerance conversion
        if tolerance_type in ["flatness", "circularity", "cylindricity", "straightness"]:
            return 0.0, tolerance_value
        elif tolerance_type == "position":
            return -tolerance_value, tolerance_value if nominal == 0.0 else (-tolerance_value, tolerance_value)
        elif tolerance_type in ["parallelism", "perpendicularity", "angularity"]:
            return -tolerance_value, tolerance_value
        elif tolerance_type in ["profile", "profile_line", "profile_surface"]:
            if gdt_info.get("is_bilateral_profile"):
                return -tolerance_value / 2, tolerance_value / 2
            else:
                return -tolerance_value / 2, tolerance_value / 2
        elif tolerance_type in ["runout", "total_runout"]:
            return 0.0, tolerance_value
        elif tolerance_type in ["concentricity", "symmetry"]:
            return -tolerance_value, tolerance_value
        else:
            return -tolerance_value, tolerance_value

    def extract_tolerance_from_gdt(self, description: str, nominal: float = 0.0) -> Tuple[List[float], List[str]]:
        """Optimized tolerance extraction"""
        if not description or not description.strip():
            return [], ["Empty description"]

        # Parse GD&T information (uses cache)
        gdt_info = self.parse_gdt_description(description)

        if not gdt_info["has_gdt"]:
            # Quick check for informative dimensions
            if any(keyword in description.lower() for keyword in ["ref", "typ", "note"]):
                return [], ["Informative dimension"]
            return [], ["No GD&T callout detected"]

        if not gdt_info.get("tolerance_value"):
            return [], ["No tolerance value found"]

        # Convert to tolerance range
        try:
            lower_tol, upper_tol = self.convert_gdt_to_tolerance_range(gdt_info, nominal)
            warnings = gdt_info.get("warnings", [])
            
            if lower_tol == 0.0 and upper_tol == 0.0:
                warnings.append("GD&T conversion resulted in zero tolerance")
            
            return [lower_tol, upper_tol], warnings

        except Exception as e:
            return [], [f"GD&T conversion error: {str(e)}"]

    @lru_cache(maxsize=128)
    def format_gdt_display(self, description: str) -> str:
        """Cached GD&T symbol formatting"""
        if not description:
            return description
            
        formatted = description

        # Fast replacements for common symbols
        replacements = {
            "position": "⌖",
            "concentricity": "◎",
            "symmetry": "≡",
            "parallelism": "∥",
            "perpendicularity": "⊥",
            "angularity": "∠",
            "flatness": "⏥",
            "straightness": "⏤",
            "circularity": "○",
            "cylindricity": "⌭",
            "profile": "⌓",
            "runout": "↗",
            "total runout": "↗↗",
            "(M)": "Ⓜ",
            "(L)": "Ⓛ",
            "(S)": "Ⓢ",
            "diameter": "Ø",
            "dia": "Ø",
            "diam": "Ø",
        }

        # Apply replacements efficiently
        for text, symbol in replacements.items():
            if text.lower() in formatted.lower():
                pattern = re.compile(re.escape(text), re.IGNORECASE)
                formatted = pattern.sub(symbol, formatted)

        return formatted


@lru_cache(maxsize=512)
def create_enhanced_gdt_flags(description: str) -> Dict[str, bool]:
    """Cached GD&T flags creation for performance"""
    if not description:
        return {"HAS_GDT": False}
    
    # Use a simplified approach for performance
    desc_lower = description.lower()
    
    # Fast keyword detection
    gdt_keywords = {
        "position": ["position", "true position", "tp", "⌖"],
        "flatness": ["flatness", "⏥"],
        "parallelism": ["parallelism", "∥"],
        "perpendicularity": ["perpendicularity", "⊥"],
        "angularity": ["angularity", "∠"],
        "profile": ["profile", "⌓", "⌒"],
        "circularity": ["circularity", "roundness", "○"],
        "cylindricity": ["cylindricity", "⌭"],
        "straightness": ["straightness"],
        "concentricity": ["concentricity", "◎"],
        "symmetry": ["symmetry", "≡"],
        "runout": ["runout", "↗"],
        "total_runout": ["total runout", "↗↗"],
    }
    
    # Material conditions
    has_mmc = any(mc in desc_lower for mc in ["(m)", "mmc", "ⓜ"])
    has_lmc = any(mc in desc_lower for mc in ["(l)", "lmc", "ⓛ"])
    has_rfs = any(mc in desc_lower for mc in ["(s)", "rfs", "ⓢ"])
    
    # Detect GD&T type and create flags
    flags = {
        "HAS_GDT": False,
        "MMC": has_mmc,
        "LMC": has_lmc,
        "RFS": has_rfs,
        "HAS_DATUMS": bool(re.search(r"[A-Z]", description.upper())),
        "DATUM_COUNT": len(re.findall(r"[A-Z]", description.upper())),
        # Initialize all tolerance type flags
        "POSITION": False,
        "PARALLELISM": False,
        "PERPENDICULARITY": False,
        "ANGULARITY": False,
        "PROFILE": False,
        "FLATNESS": False,
        "CIRCULARITY": False,
        "CYLINDRICITY": False,
        "STRAIGHTNESS": False,
        "CONCENTRICITY": False,
        "SYMMETRY": False,
        "RUNOUT": False,
        "TOTAL_RUNOUT": False,
        # Legacy flags
        "MIN": False,
        "MAX": False,
    }
    
    # Check for GD&T keywords
    for gdt_type, keywords in gdt_keywords.items():
        if any(keyword in desc_lower for keyword in keywords):
            flags["HAS_GDT"] = True
            flags[gdt_type.upper()] = True
            break  # Stop at first match for performance
    
    return flags