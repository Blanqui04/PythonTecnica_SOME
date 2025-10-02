# src/statistics/plotting/spc_charts_manager.py - FIXED VERSION WITH EXTRAPOLATION DEBUG
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import os

from .logging_config import logger as base_logger

from .spc_data_loader import SPCDataLoader
from .i_chart import IChart
from .mr_chart import MRChart
from .x_chart import XBarChart
from .r_chart import RChart
from .s_chart import SChart
from .capability_chart import CapabilityChart
from .distribution_chart import DistributionSPCChart
from .normality_plot import NormalityAnalysisChart


class SPCChartManager:
    """
    Manager class for creating SPC charts from loaded data.
    Handles multiple chart types and elements.
    """

    CHART_TYPES = {
        "normality": NormalityAnalysisChart,
        "individuals": IChart,
        "moving_range": MRChart,
        "capability": CapabilityChart,
        "distribution": DistributionSPCChart,
        "xbar": XBarChart,  # NEW
        "r_chart": RChart,  # NEW
        "s_chart": SChart,  # NEW
    }

    def __init__(
        self,
        client: str,
        ref_project: str,
        batch_number: str,
        base_path: str = "./data/spc",
        output_dir: str = "./data/reports/charts",
        lang: str = "ca",
        logger: Optional[logging.Logger] = None,
    ):
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.lang = lang
        self.logger = logger or base_logger.getChild(self.__class__.__name__)

        # Compose folder and filename
        self.folder_name = f"{self.client}_{self.ref_project}_{self.batch_number}"
        self.filename = f"{self.ref_project}_{self.batch_number}_complete_report.json"

        self.logger.info(
            f"Initialized SPCChartManager for study folder '{self.folder_name}', file '{self.filename}'"
        )
        self.elements_data = {}

    def load_data(self) -> bool:
        """
        Load SPC data from the complete report.

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        self.logger.info(f"Loading data for: {self.folder_name}/{self.filename}")
        report_path = self.base_path / self.folder_name / self.filename

        if not report_path.exists():
            self.logger.error(f"SPC report not found at path: {report_path}")
            # Also check alternative path structure
            alt_folder_name = f"{self.client}_{self.ref_project}"
            alt_report_path = self.base_path / alt_folder_name / self.filename
            
            if alt_report_path.exists():
                self.logger.info(f"Found report at alternative path: {alt_report_path}")
                report_path = alt_report_path
                self.folder_name = alt_folder_name
            else:
                self.logger.error(f"SPC report not found at alternative path either: {alt_report_path}")
                return False

        try:
            self.elements_data = SPCDataLoader(
                self.ref_project, self.base_path
            ).load_complete_report(report_path)
            
            if not self.elements_data:
                self.logger.error(f"No data loaded from report: {report_path}")
                return False
                
            self.logger.info(f"Successfully loaded data for {len(self.elements_data)} elements")
            
            # DEBUG: Log extrapolated values for each element
            for element_key, element_data in self.elements_data.items():
                extrap_values = element_data.get("extrapolated_values", [])
                original_values = element_data.get("original_values", [])
                self.logger.info(f"Element '{element_key}': {len(original_values)} original, {len(extrap_values)} extrapolated values")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Exception loading report: {e}", exc_info=True)
            return False

    def _convert_element_data_for_chart(
        self, element_key: str, element_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert loaded element data to the format expected by chart classes.
        FIXED: Ensure cavity information is preserved and extrapolation data is properly handled.
        """
        self.logger.debug(f"Converting data for element key '{element_key}'")

        # Get extrapolated values
        extrapolated_values = element_data.get("extrapolated_values", [])
        original_values = element_data.get("original_values", [])
        
        # Enhanced debug logging for extrapolation
        self.logger.info(f"EXTRAPOLATION DEBUG for '{element_key}':")
        self.logger.info(f"  Original values count: {len(original_values)}")
        self.logger.info(f"  Extrapolated values count: {len(extrapolated_values)}")
        self.logger.info(f"  Extrapolated values sample: {extrapolated_values[:5]}...")

        # Map the loaded data to the format expected by chart classes
        chart_data = {
            "element_name": element_key,  # Use the composite key for chart processing
            "sample_data": original_values,
            "nominal": element_data.get("nominal", 0),
            "tolerance": element_data.get("tolerance", [-1, 1]),
            "std_short": element_data.get("std_short"),
            "std_long": element_data.get("std_long"),
            "pval_ad": element_data.get("p_value"),
            "ad": element_data.get("ad_value"),
            "ad_result": element_data.get("p_value", 0) > 0.05
            if element_data.get("p_value") is not None
            else None,
            "output_dir": str(self.output_dir),
            "mean": element_data.get("mean"),
            "sample_size": element_data.get("sample_size"),
            "cp": element_data.get("cp"),
            "cpk": element_data.get("cpk"),
            "pp": element_data.get("pp"),
            "ppk": element_data.get("ppk"),
            "ppm_short": element_data.get("ppm_short"),
            "ppm_long": element_data.get("ppm_long"),
            "cavity": element_data.get("cavity", ""),
        }

        # CRITICAL: Add extrapolation data if available
        if extrapolated_values:
            chart_data["extrapolated_values"] = extrapolated_values
            chart_data["extrapolated_ad_value"] = element_data.get("extrapolated_ad_value")
            chart_data["extrapolated_p_value"] = element_data.get("extrapolated_p_value")
            self.logger.info(f"✓ Added extrapolation data for element '{element_key}' ({len(extrapolated_values)} values)")
        else:
            self.logger.warning(f"⚠ No extrapolation data found for element '{element_key}'")

        return chart_data
# spc_charts_manager.py
    def create_chart(
        self, element_key: str, chart_type: str, show: bool = False, save: bool = True,
        subgroup_size: int = 5  # NEW parameter
    ) -> bool:
        """Create a single chart for a specific element and chart type."""
        self.logger.info(f"Creating {chart_type} chart for element key '{element_key}'")

        if chart_type not in self.CHART_TYPES:
            self.logger.error(f"Unknown chart type: {chart_type}")
            return False

        if element_key not in self.elements_data:
            self.logger.error(f"Element key '{element_key}' not found in loaded data")
            return False

        try:
            chart_class = self.CHART_TYPES[chart_type]
            element_data = self.elements_data[element_key]
            
            # ENHANCED: Better extrapolation chart availability check
            if chart_type == "extrapolation":
                extrapolated_values = element_data.get("extrapolated_values", [])
                original_values = element_data.get("original_values", [])
                
                self.logger.info(f"EXTRAPOLATION CHART CHECK for '{element_key}':")
                self.logger.info(f"  Extrapolated values: {len(extrapolated_values)}")
                self.logger.info(f"  Original values: {len(original_values)}")
                
                # Allow extrapolation chart if we have extrapolated data OR more than 10 real values
                has_extrapolated = len(extrapolated_values) > 0
                has_real_values_gt10 = len(original_values) > 10
                
                if not (has_extrapolated or has_real_values_gt10):
                    self.logger.warning(
                        f"⚠ Cannot create extrapolation chart for '{element_key}': "
                        f"no extrapolated data ({len(extrapolated_values)}) and original data <= 10 ({len(original_values)})"
                    )
                    return False
                
                self.logger.info(
                    f"✓ Extrapolation chart CAN be created for '{element_key}': "
                    f"extrapolated={has_extrapolated}, real>10={has_real_values_gt10}"
                )
            
            # CRITICAL FIX: Extract original element name and cavity correctly
            original_element_name = element_data.get("element_name")
            cavity = element_data.get("cavity", "")
            
            self.logger.info(f"Element data: key='{element_key}', original_name='{original_element_name}', cavity='{cavity}'")
            
            # Convert element data to chart format
            chart_data = self._convert_element_data_for_chart(element_key, element_data)

            # Create temporary JSON file with proper data structure
            temp_data = {element_key: chart_data}
            
            # DEBUG: Log the temp data for extrapolation charts
            if chart_type == "extrapolation":
                self.logger.info("TEMP DATA for extrapolation chart:")
                self.logger.info(f"  Has extrapolated_values: {'extrapolated_values' in chart_data}")
                self.logger.info(f"  Extrapolated values count: {len(chart_data.get('extrapolated_values', []))}")
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as temp_file:
                json.dump(temp_data, temp_file, indent=2)
                temp_file_path = temp_file.name

            try:
                save_path = None
                if save:
                    # CRITICAL FIX: Use original element name for filename, not composite key
                    if cavity and str(cavity).strip():
                        filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
                    else:
                        filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
                    
                    charts_dir = Path(self.output_dir)
                    save_path = charts_dir / filename
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Enhanced logging
                    self.logger.info("CHART GENERATION DEBUG:")
                    self.logger.info(f"  Element key: {element_key}")
                    self.logger.info(f"  Original element: {original_element_name}")
                    self.logger.info(f"  Cavity: '{cavity}'")
                    self.logger.info(f"  Chart type: {chart_type}")
                    self.logger.info(f"  Filename: {filename}")
                    self.logger.info(f"  Full path: {save_path}")

                # Create and run chart with enhanced error handling
                # Create chart with subgroup_size if applicable
                try:
                    if chart_type in ['xbar', 'r_chart', 's_chart']:
                        chart = chart_class(
                            input_json_path=temp_file_path,
                            lang=self.lang,
                            show=show,
                            save_path=save_path,
                            element_name=element_key,
                            logger=self.logger,
                            subgroup_size=subgroup_size  # Pass subgroup size
                        )
                    else:
                        chart = chart_class(
                            input_json_path=temp_file_path,
                            lang=self.lang,
                            show=show,
                            save_path=save_path,
                            element_name=element_key,
                            logger=self.logger,
                        )
                    
                    self.logger.info(f"✓ Chart instance created for {chart_type}")
                except Exception as chart_init_error:
                    self.logger.error(f"✗ Failed to create chart instance: {chart_init_error}", exc_info=True)
                    return False

                # CRITICAL: Actually generate the chart
                self.logger.info(f"About to call chart.plot() for {chart_type}")
                try:
                    chart.plot()
                    self.logger.info(f"✓ chart.plot() completed for {chart_type}")
                except Exception as plot_error:
                    self.logger.error(f"✗ Error in chart.plot(): {plot_error}", exc_info=True)
                    # For extrapolation charts, log additional debug info
                    if chart_type == "extrapolation":
                        self.logger.error("EXTRAPOLATION PLOT FAILURE DEBUG:")
                        self.logger.error(f"  Temp file: {temp_file_path}")
                        self.logger.error(f"  Chart data keys: {list(chart_data.keys())}")
                        self.logger.error(f"  Has extrapolated_values: {'extrapolated_values' in chart_data}")
                    return False

                # CRITICAL: Verify file was created
                if save_path:
                    if save_path.exists():
                        file_size = save_path.stat().st_size
                        self.logger.info(f"✓ Chart file created: {save_path} (size: {file_size} bytes)")
                        return True
                    else:
                        self.logger.error(f"✗ Chart file NOT created: {save_path}")
                        return False
                else:
                    # If not saving, assume success if plot() didn't throw
                    return True

            finally:
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file: {e}")

        except Exception as e:
            self.logger.error(f"Failed to create chart for {element_key}: {e}", exc_info=True)
            return False

    def create_all_charts(
        self,
        chart_types: Optional[List[str]] = None,
        elements: Optional[List[str]] = None,
        show: bool = False,
        save: bool = True,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Create all charts for specified elements and chart types.
        UPDATED: Better handling of extrapolation charts.
        """
        if not self.elements_data:
            self.logger.error("No elements data loaded. Call load_data() first.")
            return {}

        # Use defaults if not specified
        chart_types = chart_types or list(self.CHART_TYPES.keys())
        elements = elements or list(self.elements_data.keys())

        self.logger.info(
            f"Creating charts for {len(elements)} elements and {len(chart_types)} chart types"
        )
        self.logger.info(f"Elements: {elements}")
        self.logger.info(f"Chart types: {chart_types}")

        results = {}

        for element_key in elements:
            if element_key not in self.elements_data:
                self.logger.warning(
                    f"Element '{element_key}' not found in loaded data. Skipping."
                )
                continue

            element_results = {}

            for chart_type in chart_types:
                # ENHANCED: Better extrapolation chart check with detailed logging
                if chart_type == "extrapolation":
                    element_data = self.elements_data[element_key]
                    extrapolated_values = element_data.get("extrapolated_values", [])
                    original_values = element_data.get("original_values", [])
                    
                    has_extrapolated = len(extrapolated_values) > 0
                    has_real_values_gt10 = len(original_values) > 10
                    
                    self.logger.info(
                        f"EXTRAPOLATION AVAILABILITY CHECK for '{element_key}': "
                        f"extrapolated={len(extrapolated_values)}, original={len(original_values)}, "
                        f"can_create={'YES' if (has_extrapolated or has_real_values_gt10) else 'NO'}"
                    )
                    
                    if not (has_extrapolated or has_real_values_gt10):
                        self.logger.info(
                            f"Skipping extrapolation chart for '{element_key}': "
                            f"insufficient data (need extrapolated values OR >10 original values)"
                        )
                        element_results[chart_type] = False
                        continue

                # Create the chart with detailed logging
                self.logger.info(f"Attempting to create {chart_type} chart for '{element_key}'")
                success = self.create_chart(
                    element_key, chart_type, show=show, save=save
                )
                element_results[chart_type] = success
                
                # Log result
                status = "SUCCESS" if success else "FAILED"
                self.logger.info(f"{chart_type} chart for '{element_key}': {status}")

            results[element_key] = element_results

        # Log detailed summary
        total_charts = sum(len(elem_results) for elem_results in results.values())
        successful_charts = sum(
            sum(elem_results.values()) for elem_results in results.values()
        )
        failed_charts = total_charts - successful_charts

        self.logger.info(
            f"Chart creation complete: {successful_charts}/{total_charts} charts created successfully"
        )
        
        if failed_charts > 0:
            self.logger.warning(f"{failed_charts} charts failed to create")
            # Log which charts failed
            for element_key, element_results in results.items():
                failed_chart_types = [chart_type for chart_type, success in element_results.items() if not success]
                if failed_chart_types:
                    self.logger.warning(f"Failed charts for '{element_key}': {', '.join(failed_chart_types)}")

        return results

    def get_elements_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all loaded elements and their available data.

        Returns:
            Dict containing summary information for each element
        """
        if not self.elements_data:
            self.logger.warning("No elements data loaded")
            return {}

        summary = {}

        try:
            for element_key, element_data in self.elements_data.items():
                if not element_data:  # Handle None or empty element_data
                    self.logger.warning(f"Empty data for element '{element_key}'")
                    continue
                
                # Get extrapolated values for accurate has_extrapolation flag
                extrapolated_values = element_data.get("extrapolated_values", [])
                original_values = element_data.get("original_values", [])
                
                # CRITICAL FIX: Store both the composite key and original element info
                summary[element_key] = {
                    "sample_size": len(original_values),
                    "has_extrapolation": len(extrapolated_values) > 0,  # Use actual extrapolated values count
                    "has_normality_test": element_data.get("p_value") is not None,
                    "nominal": element_data.get("nominal"),
                    "tolerance": element_data.get("tolerance"),
                    "mean": element_data.get("mean"),
                    "cp": element_data.get("cp"),
                    "cpk": element_data.get("cpk"),
                    "cavity": element_data.get("cavity", ""),
                    "class": element_data.get("class", ""),
                    "element_name": element_data.get("element_name"),  # Store original name
                    "extrapolated_count": len(extrapolated_values),  # Additional debug info
                }
                
                # Debug logging for extrapolation
                self.logger.debug(
                    f"Summary for '{element_key}': has_extrapolation={len(extrapolated_values) > 0}, "
                    f"extrapolated_count={len(extrapolated_values)}, sample_size={len(original_values)}"
                )

            self.logger.info(f"Generated summary for {len(summary)} elements")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating elements summary: {e}", exc_info=True)
            return {}