# src/services/spc_chart_service.py - COMPLETE FIX FOR EXTRAPOLATION CHARTS
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from PyQt5.QtCore import QObject, pyqtSignal

from src.models.plotting.spc_charts_manager import SPCChartManager

class SPCChartService(QObject):
    chart_data_ready = pyqtSignal(dict)  # New signal for thread-safe chart creation
    
    """Service layer for managing SPC chart operations"""

    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.study_id = f"{ref_project}_{batch_number}"

        self.logger = logging.getLogger(__name__)
        self.chart_manager = None
        self.elements_data = {}

    def initialize_chart_manager(self) -> bool:
        try:
            self.logger.info(f"Initializing chart manager for study: {self.study_id}")

            # Create consistent paths for data and charts
            base_data_path = "./data/spc"
            charts_output_dir = f"./data/reports/charts/{self.ref_project}"

            # Initialize the chart manager with proper parameters
            self.chart_manager = SPCChartManager(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number,
                base_path=base_data_path,
                output_dir=charts_output_dir,
            )

            # Check if the chart manager was created successfully
            if not self.chart_manager:
                self.logger.error("Failed to create chart manager instance")
                return False

            # Try to load data
            if not self.chart_manager.load_data():
                self.logger.error(f"Failed to load data for study: {self.study_id}")
                return False

            # Get elements summary with error handling
            try:
                self.elements_data = self.chart_manager.get_elements_summary()
                if not self.elements_data:
                    self.logger.warning("No elements data returned from chart manager")
                    self.elements_data = {}
                
                self.logger.info(f"Loaded data for {len(self.elements_data)} elements")
                
                # DEBUG: Log extrapolation data availability
                for element_key, element_data in self.elements_data.items():
                    has_extrap = element_data.get("has_extrapolation", False)
                    sample_size = element_data.get("sample_size", 0)
                    self.logger.info(f"Element '{element_key}': has_extrapolation={has_extrap}, sample_size={sample_size}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error getting elements summary: {e}")
                # Initialize empty elements_data to prevent further errors
                self.elements_data = {}
                return False

        except Exception as e:
            self.logger.error(f"Error initializing chart manager: {e}", exc_info=True)
            return False

    def generate_all_charts(
        self, show: bool = False, save: bool = True
    ) -> Dict[str, Dict[str, bool]]:
        """Generate all charts for all elements"""
        if not self.chart_manager:
            self.logger.error(
                "Chart manager not initialized. Call initialize_chart_manager() first."
            )
            return {}

        try:
            self.logger.info("Starting chart generation for all elements")

            # Generate charts using the manager
            results = self.chart_manager.create_all_charts(show=show, save=save)

            # Log results with detailed extrapolation info
            total_charts = sum(len(elem_results) for elem_results in results.values())
            successful_charts = sum(
                sum(elem_results.values()) for elem_results in results.values()
            )

            # Log extrapolation chart results specifically
            for element_key, element_results in results.items():
                if 'extrapolation' in element_results:
                    extrap_success = element_results['extrapolation']
                    self.logger.info(f"Extrapolation chart for '{element_key}': {'SUCCESS' if extrap_success else 'FAILED'}")

            self.logger.info(
                f"Chart generation completed: {successful_charts}/{total_charts} charts created"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}", exc_info=True)
            return {}

    def generate_charts_for_element(
        self,
        element_key: str,  # This is now the composite key like "N100 Cavity 1"
        chart_types: Optional[List[str]] = None,
        show: bool = False,
        save: bool = True,
    ) -> Dict[str, bool]:
        """Generate charts for a specific element"""
        if not self.chart_manager:
            self.logger.error("Chart manager not initialized.")
            return {}

        if element_key not in self.elements_data:
            self.logger.error(f"Element key '{element_key}' not found in data")
            return {}

        try:
            self.logger.info(f"Generating charts for element key: {element_key}")

            # Use all available chart types if not specified
            if chart_types is None:
                chart_types = list(self.chart_manager.CHART_TYPES.keys())

            results = {}
            for chart_type in chart_types:
                # Enhanced extrapolation check
                if chart_type == "extrapolation":
                    element_data = self.elements_data.get(element_key, {})
                    has_extrapolation = element_data.get("has_extrapolation", False)
                    sample_size = element_data.get("sample_size", 0)
                    
                    self.logger.info(
                        f"Extrapolation check for '{element_key}': "
                        f"has_extrapolation={has_extrapolation}, sample_size={sample_size}"
                    )
                    
                    # Allow extrapolation chart if we have extrapolated data OR real data > 10
                    if not has_extrapolation and sample_size <= 10:
                        self.logger.info(
                            f"Skipping extrapolation chart for '{element_key}': "
                            f"no extrapolated data and sample size <= 10"
                        )
                        results[chart_type] = False
                        continue

                # Create the chart using the composite key
                success = self.chart_manager.create_chart(
                    element_key, chart_type, show=show, save=save
                )
                results[chart_type] = success
                
                # Log specific failure for extrapolation
                if chart_type == "extrapolation" and not success:
                    self.logger.error(f"FAILED to create extrapolation chart for '{element_key}'")

            return results

        except Exception as e:
            self.logger.error(
                f"Error generating charts for element {element_key}: {e}", exc_info=True
            )
            return {}

    def prepare_chart_data(self, element_key: str, chart_type: str) -> dict:
        """Prepare chart data in worker thread without creating figures"""
        try:
            element_data = self.elements_data.get(element_key, {})
            chart_data = {
                'element_key': element_key,
                'chart_type': chart_type,
                'data': element_data,
                'config': self.chart_manager.get_chart_config(element_key, chart_type)
            }
            return chart_data
        except Exception as e:
            self.logger.error(f"Error preparing chart data: {e}")
            return None

    def generate_all_charts_threadsafe(self, show: bool = False, save: bool = True) -> dict:
        """Thread-safe version of chart generation"""
        results = {}
        
        for element_key in self.elements_data:
            results[element_key] = {}
            for chart_type in self.chart_manager.CHART_TYPES:
                chart_data = self.prepare_chart_data(element_key, chart_type)
                if chart_data:
                    self.chart_data_ready.emit(chart_data)
                    results[element_key][chart_type] = True
                else:
                    results[element_key][chart_type] = False
                    
        return results

    def get_elements_summary(self) -> Dict[str, Any]:
        """Get summary of all elements including cavity information"""
        if not self.elements_data:
            self.logger.warning("No elements data available")
            return {}
        
        # Ensure cavity information is preserved in the summary
        enhanced_summary = {}
        for element_key, element_data in self.elements_data.items():
            enhanced_summary[element_key] = element_data.copy() if element_data else {}
            
            # Make sure cavity information is available
            if 'cavity' not in enhanced_summary[element_key]:
                enhanced_summary[element_key]['cavity'] = element_data.get('cavity', '') if element_data else ''
        
        return enhanced_summary

    def get_element_info(self, element_key: str) -> Dict[str, Any]:
        """Get detailed information for a specific element"""
        return self.elements_data.get(element_key, {})

    def get_available_chart_types(self) -> List[str]:
        """Get list of available chart types"""
        if not self.chart_manager:
            return []
        return list(self.chart_manager.CHART_TYPES.keys())

    def get_chart_file_path(self, element_key: str, chart_type: str, cavity: str = None) -> str:
        """Get the file path for a specific chart - COMPLETELY FIXED"""
        try:
            charts_dir = f"data/reports/charts/{self.ref_project}"
            
            # CRITICAL FIX: Get the original element name from stored data
            element_data = self.elements_data.get(element_key, {})
            original_element_name = element_data.get("element_name")
            
            # If we can't find the original name, extract from composite key
            if not original_element_name:
                # For keys like "N100 Cavity 1", extract "N100"
                if " Cavity " in element_key:
                    original_element_name = element_key.split(" Cavity ")[0]
                elif "_cavity_" in element_key:
                    original_element_name = element_key.split("_cavity_")[0]
                else:
                    original_element_name = element_key
            
            # Get cavity from element data (preferred) or parameter
            element_cavity = element_data.get('cavity', '')
            if not cavity:
                cavity = element_cavity
            
            # CRITICAL FIX: Use the EXACT same format as chart generation in SPCChartManager
            if cavity and str(cavity).strip():
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
            else:
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
            
            chart_path = os.path.join(charts_dir, filename)
            
            # Debug logging
            self.logger.debug("PATH GENERATION DEBUG:")
            self.logger.debug(f"  Element key: {element_key}")
            self.logger.debug(f"  Original element: {original_element_name}")
            self.logger.debug(f"  Cavity: '{cavity}'")
            self.logger.debug(f"  Final filename: {filename}")
            self.logger.debug(f"  Full path: {chart_path}")
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Error getting chart path: {e}")
            # Simple fallback
            fallback_filename = f"{chart_type}_{self.batch_number}_{element_key}.png"
            return os.path.join("data", "reports", "charts", self.ref_project, fallback_filename)

    def validate_study_data(self) -> Tuple[bool, str]:
        """Validate that study data is available and complete"""
        try:
            # Check if chart manager is initialized
            if not self.chart_manager:
                return False, "Chart manager not initialized"

            # Check if the data file exists
            data_path = self.chart_manager.base_path / self.chart_manager.folder_name / self.chart_manager.filename
            if not data_path.exists():
                return False, f"Study data file not found: {data_path}"

            # Check if elements data is loaded
            if not self.elements_data:
                return False, "No elements data loaded"

            # Check if at least one element has data
            if not any(self.elements_data.values()):
                return False, "No valid element data found"

            return (
                True,
                f"Study data validated successfully for {len(self.elements_data)} elements",
            )

        except Exception as e:
            return False, f"Validation error: {e}"

    def get_study_statistics(self) -> Dict[str, Any]:
        """Get overall study statistics"""
        if not self.elements_data:
            return {}

        stats = {
            "total_elements": len(self.elements_data),
            "elements_with_extrapolation": 0,
            "total_samples": 0,
            "avg_cp": 0,
            "avg_cpk": 0,
        }

        cp_values = []
        cpk_values = []

        for element_key, element_data in self.elements_data.items():
            if not element_data:  # Skip if element_data is None or empty
                continue
                
            # Count samples
            sample_size = element_data.get("sample_size", 0)
            if isinstance(sample_size, int):
                stats["total_samples"] += sample_size

            # Check for extrapolation
            if element_data.get("has_extrapolation", False):
                stats["elements_with_extrapolation"] += 1

            # Collect capability indices
            cp = element_data.get("cp")
            if isinstance(cp, (int, float)) and cp is not None:
                cp_values.append(cp)

            cpk = element_data.get("cpk")
            if isinstance(cpk, (int, float)) and cpk is not None:
                cpk_values.append(cpk)

        # Calculate averages
        if cp_values:
            stats["avg_cp"] = sum(cp_values) / len(cp_values)

        if cpk_values:
            stats["avg_cpk"] = sum(cpk_values) / len(cpk_values)

        return stats


def create_spc_chart_service(
    client: str, ref_project: str, batch_number: str
) -> SPCChartService:
    """Factory function to create SPC chart service"""
    return SPCChartService(client, ref_project, batch_number)


def generate_charts_for_study(
    client: str,
    ref_project: str,
    batch_number: str,
    show: bool = False,
    save: bool = True,
) -> Dict[str, Any]:
    """Convenience function to generate charts for a study"""
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting chart generation for study: {client}_{ref_project}_{batch_number}")

    service = create_spc_chart_service(client, ref_project, batch_number)

    # Initialize with better error handling
    if not service.initialize_chart_manager():
        error_msg = "Failed to initialize chart manager"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    # Validate data with better error handling
    valid, message = service.validate_study_data()
    if not valid:
        logger.error(f"Data validation failed: {message}")
        return {"success": False, "error": message}

    # Generate charts
    try:
        results = service.generate_all_charts(show=show, save=save)
        
        return {
            "success": True,
            "chart_results": results,
            "elements_summary": service.get_elements_summary(),
            "study_statistics": service.get_study_statistics(),
        }
    except Exception as e:
        error_msg = f"Error during chart generation: {e}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}