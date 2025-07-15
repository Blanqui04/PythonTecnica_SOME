# src/statistics/plotting/spc_chart_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import os

from base_chart import get_spc_logger
from normality_plot import NormalityAnalysisChart


class SPCDataLoader:
    def __init__(self, study_id, base_path="./data/spc"):
        self.study_id = study_id
        self.base_path = base_path
        self.elements_data = {}
        self.logger = get_spc_logger()

    def load_complete_report(self):
        path = f"{self.base_path}/{self.study_id}_complete_report.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                report = json.load(f)
            self.logger.info(f"Loaded JSON report from {path}")
        except Exception as e:
            self.logger.error(f"Failed to load JSON report: {e}")
            return

        detailed_results = report.get("detailed_results", [])
        extrapolation_results = report.get("extrapolation_results", [])

        if not detailed_results:
            self.logger.warning("No detailed_results found in JSON report.")
            return

        # Build a lookup dict for extrapolation results by element_name
        extrapolation_lookup = {
            item["element_name"]: item for item in extrapolation_results if "element_name" in item
        }

        for element_info in detailed_results:
            element_name = element_info.get("element_name")
            if not element_name:
                continue

            extrapolated = extrapolation_lookup.get(element_name, {})

            self.elements_data[element_name] = {
                "nominal": element_info.get("nominal"),
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
                "ad_value": element_info.get("statistics", {}).get("ad_statistic"),
                "p_value": element_info.get("statistics", {}).get("p_value"),
                "extrapolated_values": extrapolated.get("extrapolated_values", []),
                "extrapolated_ad_value": extrapolated.get("ad_statistic"),
                "extrapolated_p_value": extrapolated.get("p_value"),
            }

        return self.elements_data

    def get_element_data(self, element_name):
        return self.elements_data.get(element_name)


class SPCChartManager:
    """
    Manager class for creating SPC charts from loaded data.
    Handles multiple chart types and elements.
    """
    
    CHART_TYPES = {
        'normality': NormalityAnalysisChart,
        # Add more chart types here as they are implemented
        # 'control': ControlChart,
        # 'capability': CapabilityChart,
    }

    def __init__(self, study_id: str, base_path: str = "./data/spc", 
                 output_dir: str = "./output/charts", lang: str = "ca",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the SPC Chart Manager.
        
        Args:
            study_id: Study identifier
            base_path: Base path for data files
            output_dir: Output directory for charts
            lang: Language for chart labels
            logger: Optional logger instance
        """
        self.study_id = study_id
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.lang = lang
        self.logger = logger or get_spc_logger()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data loader
        self.data_loader = SPCDataLoader(study_id, base_path)
        self.elements_data = {}
        
        self.logger.info(f"Initialized SPCChartManager for study '{study_id}'")

    def load_data(self) -> bool:
        """
        Load SPC data from the complete report.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        self.logger.info(f"Loading data for study '{self.study_id}'")
        
        try:
            self.elements_data = self.data_loader.load_complete_report()
            if not self.elements_data:
                self.logger.error("No elements data loaded")
                return False
                
            self.logger.info(f"Successfully loaded data for {len(self.elements_data)} elements: {list(self.elements_data.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}", exc_info=True)
            return False

    def _convert_element_data_for_chart(self, element_name: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert loaded element data to the format expected by chart classes.
        
        Args:
            element_name: Name of the element
            element_data: Raw element data from loader
            
        Returns:
            Dict containing data formatted for chart classes
        """
        self.logger.debug(f"Converting data for element '{element_name}'")
        
        # Map the loaded data to the format expected by NormalityAnalysisChart
        chart_data = {
            "element_name": element_name,
            "sample_data": element_data.get("original_values", []),
            "nominal": element_data.get("nominal", 0),
            "tolerance": element_data.get("tolerance", [-1, 1]),
            "std_short_term": element_data.get("std_short"),
            "std_long_term": element_data.get("std_long"),
            "pval_ad": element_data.get("p_value"),
            "ad": element_data.get("ad_value"),
            "ad_result": element_data.get("p_value", 0) > 0.05 if element_data.get("p_value") is not None else None,
            "output_dir": str(self.output_dir),
            "mean": element_data.get("mean"),
            "sample_size": element_data.get("sample_size"),
            "cp": element_data.get("cp"),
            "cpk": element_data.get("cpk"),
            "pp": element_data.get("pp"),
            "ppk": element_data.get("ppk"),
            "ppm_short": element_data.get("ppm_short"),
            "ppm_long": element_data.get("ppm_long"),
        }
        
        # Add extrapolation data if available
        extrapolated_values = element_data.get("extrapolated_values", [])
        if extrapolated_values:
            chart_data["extrapolated_values"] = extrapolated_values
            chart_data["extrapolated_ad_value"] = element_data.get("extrapolated_ad_value")
            chart_data["extrapolated_p_value"] = element_data.get("extrapolated_p_value")
            
        return chart_data

    def create_chart(self, element_name: str, chart_type: str, 
                    show: bool = False, save: bool = True) -> bool:
        """
        Create a single chart for a specific element and chart type.
        
        Args:
            element_name: Name of the element
            chart_type: Type of chart to create
            show: Whether to display the chart
            save: Whether to save the chart
            
        Returns:
            bool: True if chart created successfully, False otherwise
        """
        self.logger.info(f"Creating {chart_type} chart for element '{element_name}'")
        
        if chart_type not in self.CHART_TYPES:
            self.logger.error(f"Unknown chart type: {chart_type}")
            return False
            
        if element_name not in self.elements_data:
            self.logger.error(f"Element '{element_name}' not found in loaded data")
            return False
            
        try:
            # Get the chart class
            chart_class = self.CHART_TYPES[chart_type]
            
            # Convert element data to chart format
            element_data = self.elements_data[element_name]
            chart_data = self._convert_element_data_for_chart(element_name, element_data)
            
            # Create temporary JSON file with chart data
            temp_data = {element_name: chart_data}
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
                json.dump(temp_data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Determine save path
                save_path = None
                if save:
                    save_path = self.output_dir / f"{self.study_id}_{element_name}_{chart_type}.png"
                
                # Create chart instance
                chart = chart_class(
                    input_json_path=temp_file_path,
                    lang=self.lang,
                    show=show,
                    save_path=save_path,
                    element_name=element_name,
                    logger=self.logger
                )
                
                # Generate the chart
                chart.plot()
                
                self.logger.info(f"Successfully created {chart_type} chart for '{element_name}'")
                if save_path:
                    self.logger.info(f"Chart saved to: {save_path}")
                    
                return True
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to create {chart_type} chart for '{element_name}': {e}", exc_info=True)
            return False

    def create_all_charts(self, chart_types: Optional[List[str]] = None, 
                         elements: Optional[List[str]] = None,
                         show: bool = False, save: bool = True) -> Dict[str, Dict[str, bool]]:
        """
        Create all charts for specified elements and chart types.
        
        Args:
            chart_types: List of chart types to create (default: all available)
            elements: List of elements to process (default: all loaded elements)
            show: Whether to display charts
            save: Whether to save charts
            
        Returns:
            Dict mapping element names to chart creation results
        """
        if not self.elements_data:
            self.logger.error("No elements data loaded. Call load_data() first.")
            return {}
            
        # Use defaults if not specified
        chart_types = chart_types or list(self.CHART_TYPES.keys())
        elements = elements or list(self.elements_data.keys())
        
        self.logger.info(f"Creating charts for {len(elements)} elements and {len(chart_types)} chart types")
        self.logger.info(f"Elements: {elements}")
        self.logger.info(f"Chart types: {chart_types}")
        
        results = {}
        
        for element_name in elements:
            if element_name not in self.elements_data:
                self.logger.warning(f"Element '{element_name}' not found in loaded data. Skipping.")
                continue
                
            element_results = {}
            
            for chart_type in chart_types:
                # Skip extrapolation charts if no extrapolated data
                if chart_type == 'extrapolation':
                    extrapolated_values = self.elements_data[element_name].get("extrapolated_values", [])
                    if not extrapolated_values:
                        self.logger.info(f"No extrapolated values for '{element_name}'. Skipping extrapolation chart.")
                        element_results[chart_type] = False
                        continue
                
                # Create the chart
                success = self.create_chart(element_name, chart_type, show=show, save=save)
                element_results[chart_type] = success
                
            results[element_name] = element_results
            
        # Log summary
        total_charts = sum(len(elem_results) for elem_results in results.values())
        successful_charts = sum(sum(elem_results.values()) for elem_results in results.values())
        
        self.logger.info(f"Chart creation complete: {successful_charts}/{total_charts} charts created successfully")
        
        return results

    def get_elements_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all loaded elements and their available data.
        
        Returns:
            Dict containing summary information for each element
        """
        if not self.elements_data:
            return {}
            
        summary = {}
        
        for element_name, element_data in self.elements_data.items():
            summary[element_name] = {
                "sample_size": len(element_data.get("original_values", [])),
                "has_extrapolation": bool(element_data.get("extrapolated_values", [])),
                "has_normality_test": element_data.get("p_value") is not None,
                "nominal": element_data.get("nominal"),
                "tolerance": element_data.get("tolerance"),
                "mean": element_data.get("mean"),
                "cp": element_data.get("cp"),
                "cpk": element_data.get("cpk"),
            }
            
        return summary


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    study_id = 'test_study'
    manager = SPCChartManager(study_id)
    
    if manager.load_data():
        print("Data loaded successfully")
        summary = manager.get_elements_summary()
        print(f"Elements summary: {summary}")
        
        # Create all available charts
        results = manager.create_all_charts(show=True, save=True)
        print(f"Chart creation results: {results}")
    else:
        print("Failed to load data")