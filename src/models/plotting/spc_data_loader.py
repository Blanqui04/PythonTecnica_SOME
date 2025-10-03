# src/models/plotting/spc_data_loader.py - FIXED VERSION WITH PROPER CAVITY MATCHING
import os
import json
from .logging_config import logger as base_logger


class SPCDataLoader:
    def __init__(self, study_id, base_path="./data/spc"):
        self.study_id = study_id
        self.base_path = base_path
        self.elements_data = {}
        self.logger = base_logger.getChild(self.__class__.__name__)

    @staticmethod
    def create_element_key(element_name: str, cavity: str = None) -> str:
        """Create a unique key for element+cavity combinations"""
        if cavity and str(cavity).strip():
            return f"{element_name} Cavity {cavity}"
        return element_name

    def load_complete_report(self, report_path: str = None):
        # If no path is passed, try to find one as before (legacy behavior)
        if report_path is None:
            nested_path = (
                f"{self.base_path}/{self.study_id}/{self.study_id}_complete_report.json"
            )
            flat_path = f"{self.base_path}/{self.study_id}_complete_report.json"

            if os.path.exists(nested_path):
                report_path = nested_path
            elif os.path.exists(flat_path):
                report_path = flat_path
            else:
                self.logger.error(
                    f"Report not found in either location:\n{nested_path}\n{flat_path}"
                )
                return None

        try:
            self.logger.info(f"Loading complete report from: {report_path}")
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            self.logger.info(f"✓ Loaded JSON report from {report_path}")
        except Exception as e:
            self.logger.error(f"✗ Failed to load JSON report: {e}")
            return None

        detailed_results = report.get("detailed_results", [])
        extrapolation_results = report.get("extrapolation_results", [])

        if not detailed_results:
            self.logger.warning("No detailed_results found in JSON report.")
            return None

        # DEBUG: Log the structure we're working with
        self.logger.info("EXTRAPOLATION MATCHING DEBUG:")
        self.logger.info(f"  Detailed results count: {len(detailed_results)}")
        self.logger.info(f"  Extrapolation results count: {len(extrapolation_results)}")

        # CRITICAL FIX: Build extrapolation lookup by matching array indices
        # Since the extrapolation results appear to correspond to detailed results by index
        extrapolation_lookup = {}
        
        # Log what we have in extrapolation results
        for i, extrap in enumerate(extrapolation_results):
            element_name = extrap.get("element_name", "Unknown")
            cavity = extrap.get("cavity", "")
            extrap_count = len(extrap.get("extrapolated_values", []))
            self.logger.info(f"  Extrapolation[{i}]: element='{element_name}', cavity='{cavity}', values={extrap_count}")

        # Strategy 1: Try to match by index if counts match
        if len(detailed_results) == len(extrapolation_results):
            self.logger.info("✓ Counts match - using index-based matching")
            for i, detail in enumerate(detailed_results):
                detail_element = detail.get("element_name")
                detail_cavity = detail.get("cavity", "")
                
                if i < len(extrapolation_results):
                    extrap = extrapolation_results[i]
                    extrap_element = extrap.get("element_name")
                    
                    # Verify elements match
                    if detail_element == extrap_element:
                        lookup_key = self.create_element_key(detail_element, detail_cavity)
                        extrapolation_lookup[lookup_key] = extrap
                        self.logger.info(f"  ✓ Matched by index[{i}]: '{lookup_key}' -> {len(extrap.get('extrapolated_values', []))} values")
                    else:
                        self.logger.warning(f"  ⚠ Element mismatch at index {i}: '{detail_element}' != '{extrap_element}'")
        else:
            # Strategy 2: Try name-based matching (fallback)
            self.logger.info("⚠ Counts don't match - using name-based matching")
            
            # First, try exact name + cavity matching
            for extrap in extrapolation_results:
                element_name = extrap.get("element_name")
                cavity = extrap.get("cavity", "")
                if element_name:
                    lookup_key = self.create_element_key(element_name, cavity)
                    extrapolation_lookup[lookup_key] = extrap
                    self.logger.info(f"  Added direct match: '{lookup_key}'")
            
            # If that doesn't work, try matching by element name only
            if not extrapolation_lookup:
                self.logger.info("  No direct matches found - trying element name only")
                extrap_by_element = {}
                for extrap in extrapolation_results:
                    element_name = extrap.get("element_name")
                    if element_name:
                        if element_name not in extrap_by_element:
                            extrap_by_element[element_name] = []
                        extrap_by_element[element_name].append(extrap)
                
                # Now assign to detailed results
                for detail in detailed_results:
                    detail_element = detail.get("element_name")
                    detail_cavity = detail.get("cavity", "")
                    
                    if detail_element in extrap_by_element:
                        available_extraps = extrap_by_element[detail_element]
                        if available_extraps:
                            # Take the first available extrapolation for this element
                            extrap = available_extraps.pop(0)
                            lookup_key = self.create_element_key(detail_element, detail_cavity)
                            extrapolation_lookup[lookup_key] = extrap
                            self.logger.info(f"  ✓ Assigned by element name: '{lookup_key}'")

        # Log final lookup table
        self.logger.info("FINAL EXTRAPOLATION LOOKUP:")
        for key, extrap in extrapolation_lookup.items():
            count = len(extrap.get("extrapolated_values", []))
            self.logger.info(f"  '{key}' -> {count} extrapolated values")

        self.elements_data = {}

        # Process detailed results
        for element_info in detailed_results:
            element_name = element_info.get("element_name")
            if not element_name:
                continue

            # Get cavity and create composite key
            cavity = element_info.get("cavity", "")
            element_key = self.create_element_key(element_name, cavity)
            
            # Look up extrapolation data using the composite key
            extrapolated = extrapolation_lookup.get(element_key, {})
            extrap_values = extrapolated.get("extrapolated_values", [])
            
            # Store using composite key to prevent overwrites
            self.elements_data[element_key] = {
                "element_name": element_name,  # CRITICAL: Keep original element name
                "cavity": cavity,  # CRITICAL: Store cavity separately
                "nominal": element_info.get("nominal"),
                "batch": element_info.get("batch_number"),
                "tolerance": element_info.get("tolerance"),
                "mean": element_info.get("statistics", {}).get("mean"),
                "sample_size": element_info.get("statistics", {}).get("sample_size"),
                "original_values": element_info.get("original_values", []),
                "std_short": element_info.get("statistics", {}).get("std_short"),
                "std_long": element_info.get("statistics", {}).get("std_long"),
                "cp": element_info.get("capability", {}).get("cp"),
                "cpk": element_info.get("capability", {}).get("cpk"),
                "pp": element_info.get("capability", {}).get("pp"),
                "ppk": element_info.get("capability", {}).get("ppk"),
                "ppm_short": element_info.get("capability", {}).get("ppm_short"),
                "ppm_long": element_info.get("capability", {}).get("ppm_long"),
                "ad_value": element_info.get("statistics", {}).get("ad_value"),  # FIXED: was "ad_statistic"
                "p_value": element_info.get("statistics", {}).get("p_value"),
                "instrument": element_info.get("instrument", "CMM"),  # ADD THIS
                "class": element_info.get("class", "CC"),              # ADD THIS
                "sigma": element_info.get("sigma", "6σ"),              # ADD THIS
                "extrapolated_values": extrap_values,  # CRITICAL: Store extrapolated values
                "extrapolated_ad_value": extrapolated.get("ad_statistic"),
                "extrapolated_p_value": extrapolated.get("p_value"),
            }
            
            # Log what we're storing for debugging
            original_count = len(element_info.get("original_values", []))
            extrap_count = len(extrap_values)
            self.logger.info(
                f"✓ Loaded element '{element_key}': "
                f"{original_count} original + {extrap_count} extrapolated values"
            )

        # Final summary
        total_elements = len(self.elements_data)
        elements_with_extrapolation = sum(1 for data in self.elements_data.values() 
                                        if len(data.get("extrapolated_values", [])) > 0)
        
        self.logger.info("LOADING SUMMARY:")
        self.logger.info(f"  Total elements loaded: {total_elements}")
        self.logger.info(f"  Elements with extrapolation: {elements_with_extrapolation}")
        
        return self.elements_data

    def get_element_data(self, element_name):
        """Get element data by key (which might be composite)"""
        return self.elements_data.get(element_name)

    def get_element_data_by_name_and_cavity(self, element_name: str, cavity: str = None):
        """Get element data by element name and cavity"""
        key = self.create_element_key(element_name, cavity)
        return self.elements_data.get(key)