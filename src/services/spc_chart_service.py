# src/services/spc_chart_service.py
import os
import logging
from typing import Dict, List, Optional, Tuple, Any

from src.models.plotting.spc_charts_manager import SPCChartManager


class SPCChartService:
    """Service layer for managing SPC chart operations"""
    
    def __init__(self, study_id: str):
        self.study_id = study_id
        self.logger = logging.getLogger(__name__)
        self.chart_manager = None
        self.elements_data = {}
        
    def initialize_chart_manager(self) -> bool:
        """Initialize the chart manager and load data"""
        try:
            self.logger.info(f"Initializing chart manager for study: {self.study_id}")
            
            # Create chart manager
            self.chart_manager = SPCChartManager(self.study_id)
            
            # Load data
            if not self.chart_manager.load_data():
                self.logger.error(f"Failed to load data for study: {self.study_id}")
                return False
                
            # Get elements summary
            self.elements_data = self.chart_manager.get_elements_summary()
            self.logger.info(f"Loaded data for {len(self.elements_data)} elements")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing chart manager: {e}")
            return False
    
    def generate_all_charts(self, show: bool = False, save: bool = True) -> Dict[str, Dict[str, bool]]:
        """Generate all charts for all elements"""
        if not self.chart_manager:
            self.logger.error("Chart manager not initialized. Call initialize_chart_manager() first.")
            return {}
            
        try:
            self.logger.info("Starting chart generation for all elements")
            
            # Generate charts using the manager
            results = self.chart_manager.create_all_charts(show=show, save=save)
            
            # Log results
            total_charts = sum(len(elem_results) for elem_results in results.values())
            successful_charts = sum(
                sum(elem_results.values()) for elem_results in results.values()
            )
            
            self.logger.info(
                f"Chart generation completed: {successful_charts}/{total_charts} charts created"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
            return {}
    
    def generate_charts_for_element(
        self, 
        element_name: str, 
        chart_types: Optional[List[str]] = None,
        show: bool = False, 
        save: bool = True
    ) -> Dict[str, bool]:
        """Generate charts for a specific element"""
        if not self.chart_manager:
            self.logger.error("Chart manager not initialized.")
            return {}
            
        if element_name not in self.elements_data:
            self.logger.error(f"Element '{element_name}' not found in data")
            return {}
            
        try:
            self.logger.info(f"Generating charts for element: {element_name}")
            
            # Use all available chart types if not specified
            if chart_types is None:
                chart_types = list(self.chart_manager.CHART_TYPES.keys())
            
            results = {}
            for chart_type in chart_types:
                # Skip extrapolation if no extrapolated data
                if chart_type == "extrapolation":
                    extrapolated_values = self.elements_data[element_name].get(
                        "extrapolated_values", []
                    )
                    if not extrapolated_values:
                        self.logger.info(
                            f"No extrapolated values for '{element_name}'. Skipping extrapolation chart."
                        )
                        results[chart_type] = False
                        continue
                
                # Create the chart
                success = self.chart_manager.create_chart(
                    element_name, chart_type, show=show, save=save
                )
                results[chart_type] = success
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating charts for element {element_name}: {e}")
            return {}
    
    def get_elements_summary(self) -> Dict[str, Any]:
        """Get summary of all elements"""
        return self.elements_data.copy()
    
    def get_element_info(self, element_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific element"""
        return self.elements_data.get(element_name, {})
    
    def get_available_chart_types(self) -> List[str]:
        """Get list of available chart types"""
        if not self.chart_manager:
            return []
        return list(self.chart_manager.CHART_TYPES.keys())
    
    def get_chart_file_path(self, element_id: str, chart_type: str) -> str:
        filename = f"{self.study_id}_{element_id}_{chart_type}.png"
        return os.path.join("data", "reports", "charts", filename)

    
    def validate_study_data(self) -> Tuple[bool, str]:
        """Validate that study data is available and complete"""
        try:
            # Check if study directory exists
            if not self.chart_manager:
                return False, "Chart manager not initialized"
            
            if not os.path.exists(self.chart_manager.output_dir):
                return False, f"Study directory not found: {self.chart_manager.output_dir}"
            
            # Check if elements data is loaded
            if not self.elements_data:
                return False, "No elements data loaded"
            
            # Check if at least one element has data
            if not any(self.elements_data.values()):
                return False, "No valid element data found"
            
            return True, f"Study data validated successfully for {len(self.elements_data)} elements"
            
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
        
        for element_name, element_data in self.elements_data.items():
            # Count samples
            sample_count = element_data.get("sample_count", 0)
            if isinstance(sample_count, int):
                stats["total_samples"] += sample_count
            
            # Check for extrapolation
            if element_data.get("extrapolated_values"):
                stats["elements_with_extrapolation"] += 1
            
            # Collect capability indices
            cp = element_data.get("cp")
            if isinstance(cp, (int, float)):
                cp_values.append(cp)
            
            cpk = element_data.get("cpk")
            if isinstance(cpk, (int, float)):
                cpk_values.append(cpk)
        
        # Calculate averages
        if cp_values:
            stats["avg_cp"] = sum(cp_values) / len(cp_values)
        
        if cpk_values:
            stats["avg_cpk"] = sum(cpk_values) / len(cpk_values)
        
        return stats


def create_spc_chart_service(client: str, ref_project: str) -> SPCChartService:
    """Factory function to create SPC chart service"""
    study_id = f"{client}_{ref_project}"
    return SPCChartService(study_id)


def generate_charts_for_study(client: str, ref_project: str, show: bool = False, save: bool = True) -> Dict[str, Any]:
    """Convenience function to generate charts for a study"""
    service = create_spc_chart_service(client, ref_project)
    
    # Initialize
    if not service.initialize_chart_manager():
        return {"success": False, "error": "Failed to initialize chart manager"}
    
    # Validate data
    valid, message = service.validate_study_data()
    if not valid:
        return {"success": False, "error": message}
    
    # Generate charts
    results = service.generate_all_charts(show=show, save=save)
    
    return {
        "success": True,
        "chart_results": results,
        "elements_summary": service.get_elements_summary(),
        "study_statistics": service.get_study_statistics()
    }