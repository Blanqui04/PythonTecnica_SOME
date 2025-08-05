# src/services/spc_export_service.py
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

from ..reports.spc_export_generator import ExcelSPCReportGenerator
from ..models.plotting.spc_charts_manager import SPCChartManager
from src.gui.logging_config import logger as base_logger


class ExcelReportService:
    """
    Service class that integrates Excel report generation with the existing SPC chart system.
    Provides a complete workflow from data analysis to professional report generation.
    """
    
    # Dimension classification mappings
    DIMENSION_CLASSES = {
        'critical': 'CC',      # Critical Characteristic
        'significant': 'SC',   # Significant Characteristic  
        'important': 'IC',     # Important Characteristic
        'standard': '',        # Standard dimension
    }
    
    # Methodology mappings
    METHODOLOGIES = {
        'cmm': 'CMM (Coordinate Measuring Machine)',
        'msa': 'MSA (Measurement System Analysis)',
        'manual': 'Manual Measurement',
        'optical': 'Optical Measurement System',
        'laser': 'Laser Measurement System',
        'gauge': 'Gauge Measurement',
    }

    def __init__(
        self,
        client: str,
        ref_project: str,
        batch_number: str,
        base_path: str = "./data/spc",
        charts_path: str = "./data/reports/charts", 
        excel_output_path: str = "./data/reports/excel",
        logger: Optional[logging.Logger] = None
    ):
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.base_path = Path(base_path)
        self.charts_path = Path(charts_path)
        self.excel_output_path = Path(excel_output_path)
        self.logger = logger or base_logger.getChild(self.__class__.__name__)
        
        # Initialize components
        self.chart_manager = None
        self.excel_generator = None
        self.elements_summary = {}
        
        self.logger.info(f"Initialized ExcelReportService for {client}_{ref_project}_{batch_number}")

    def initialize_services(self) -> bool:
        """Initialize the chart manager and Excel generator services"""
        try:
            # Initialize chart manager
            self.chart_manager = SPCChartManager(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number,
                base_path=str(self.base_path),
                output_dir=str(self.charts_path),
                logger=self.logger
            )
            
            # Load chart data
            if not self.chart_manager.load_data():
                self.logger.error("Failed to load chart data")
                return False
            
            # Initialize Excel generator
            self.excel_generator = ExcelSPCReportGenerator(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number,
                base_path=str(self.base_path),
                charts_path=str(self.charts_path),
                output_path=str(self.excel_output_path),
                logger=self.logger
            )
            
            # Get elements summary
            self.elements_summary = self.chart_manager.get_elements_summary()
            
            self.logger.info("Services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing services: {e}")
            return False

    def generate_complete_report(
        self,
        part_description: str,
        drawing_number: str,
        methodology: str = "cmm",
        facility: str = "",
        dimension_class: str = "critical",
        generate_charts: bool = True,
        open_file: bool = True
    ) -> Tuple[bool, str]:
        """
        Generate a complete SPC report with charts and Excel documentation
        
        Args:
            part_description: Description of the part being analyzed
            drawing_number: Technical drawing number
            methodology: Measurement methodology key
            facility: Manufacturing facility name
            dimension_class: Dimension classification key
            generate_charts: Whether to generate charts first
            open_file: Whether to open the generated file
            
        Returns:
            Tuple[bool, str]: (Success status, file path or error message)
        """
        try:
            self.logger.info("Starting complete report generation")
            
            # Initialize services if not already done
            if not self.chart_manager or not self.excel_generator:
                if not self.initialize_services():
                    return False, "Failed to initialize services"
            
            # Generate charts if requested
            if generate_charts:
                self.logger.info("Generating SPC charts...")
                chart_results = self.chart_manager.create_all_charts(
                    show=False, 
                    save=True
                )
                
                # Check if charts were generated successfully
                successful_charts = sum(
                    sum(elem_results.values()) for elem_results in chart_results.values()
                )
                total_charts = sum(
                    len(elem_results) for elem_results in chart_results.values()
                )
                
                self.logger.info(f"Generated {successful_charts}/{total_charts} charts")
                
                if successful_charts == 0:
                    return False, "No charts were generated successfully"
            
            # Resolve methodology and dimension class
            methodology_display = self.METHODOLOGIES.get(methodology.lower(), methodology)
            dimension_class_code = self.DIMENSION_CLASSES.get(dimension_class.lower(), dimension_class)
            
            # Set default facility if not provided
            if not facility:
                facility = "SOME Manufacturing Facility"
            
            # Generate Excel report
            self.logger.info("Generating Excel report...")
            excel_file = self.excel_generator.create_report(
                part_description=part_description,
                drawing_number=drawing_number,
                methodology=methodology_display,
                facility=facility,
                dimension_class=dimension_class_code
            )
            
            self.logger.info(f"Excel report generated: {excel_file}")
            
            # Open file if requested
            if open_file:
                success = self.open_excel_file(excel_file)
                if success:
                    self.logger.info("Excel file opened successfully")
                else:
                    self.logger.warning("Could not open Excel file automatically")
            
            return True, excel_file
            
        except Exception as e:
            error_msg = f"Error generating complete report: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def generate_charts_only(self, 
                           chart_types: Optional[List[str]] = None,
                           elements: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Generate only the SPC charts without Excel report
        
        Args:
            chart_types: List of chart types to generate
            elements: List of elements to process
            
        Returns:
            Tuple[bool, str]: (Success status, message)
        """
        try:
            if not self.chart_manager:
                if not self.initialize_services():
                    return False, "Failed to initialize chart manager"
            
            chart_results = self.chart_manager.create_all_charts(
                chart_types=chart_types,
                elements=elements,
                show=False,
                save=True
            )
            
            successful_charts = sum(
                sum(elem_results.values()) for elem_results in chart_results.values()
            )
            total_charts = sum(
                len(elem_results) for elem_results in chart_results.values()
            )
            
            message = f"Generated {successful_charts}/{total_charts} charts successfully"
            self.logger.info(message)
            
            return successful_charts > 0, message
            
        except Exception as e:
            error_msg = f"Error generating charts: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def generate_excel_only(self,
                          part_description: str,
                          drawing_number: str,
                          methodology: str = "cmm",
                          facility: str = "",
                          dimension_class: str = "critical",
                          open_file: bool = True) -> Tuple[bool, str]:
        """
        Generate only the Excel report (assumes charts already exist)
        
        Args:
            part_description: Description of the part being analyzed
            drawing_number: Technical drawing number
            methodology: Measurement methodology key
            facility: Manufacturing facility name
            dimension_class: Dimension classification key
            open_file: Whether to open the generated file
            
        Returns:
            Tuple[bool, str]: (Success status, file path or error message)
        """
        try:
            if not self.excel_generator:
                if not self.initialize_services():
                    return False, "Failed to initialize Excel generator"
            
            # Resolve parameters
            methodology_display = self.METHODOLOGIES.get(methodology.lower(), methodology)
            dimension_class_code = self.DIMENSION_CLASSES.get(dimension_class.lower(), dimension_class)
            
            if not facility:
                facility = "SOME Manufacturing Facility"
            
            # Generate Excel report
            excel_file = self.excel_generator.create_report(
                part_description=part_description,
                drawing_number=drawing_number,
                methodology=methodology_display,
                facility=facility,
                dimension_class=dimension_class_code
            )
            
            # Open file if requested
            if open_file:
                self.open_excel_file(excel_file)
            
            return True, excel_file
            
        except Exception as e:
            error_msg = f"Error generating Excel report: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_available_elements(self) -> List[str]:
        """Get list of available elements for analysis"""
        if not self.elements_summary:
            if not self.initialize_services():
                return []
        return list(self.elements_summary.keys())

    def get_element_info(self, element_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific element"""
        if not self.elements_summary:
            if not self.initialize_services():
                return {}
        return self.elements_summary.get(element_name, {})

    def get_study_statistics(self) -> Dict[str, Any]:
        """Get overall study statistics"""
        if not self.chart_manager:
            if not self.initialize_services():
                return {}
        
        try:
            # This method might not exist in the current implementation
            # but can be added to SPCChartManager
            return getattr(self.chart_manager, 'get_study_statistics', lambda: {})()
        except:
            return {}

    def validate_charts_exist(self) -> Dict[str, List[str]]:
        """
        Validate which charts exist for each element
        
        Returns:
            Dict mapping element names to lists of available chart types
        """
        available_charts = {}
        
        if not self.elements_summary:
            if not self.initialize_services():
                return available_charts
        
        chart_types = ['capability', 'normality', 'extrapolation', 'individuals', 'moving_range']
        
        for element_name in self.elements_summary.keys():
            element_charts = []
            for chart_type in chart_types:
                chart_filename = f"{self.ref_project}_{self.batch_number}_{element_name}_{chart_type}.png"
                chart_path = self.charts_path / chart_filename
                
                if chart_path.exists():
                    element_charts.append(chart_type)
            
            available_charts[element_name] = element_charts
        
        return available_charts

    def open_excel_file(self, file_path: str) -> bool:
        """Open the Excel file with the default application"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"Excel file does not exist: {file_path}")
                return False
            
            if platform.system() == "Windows":
                os.startfile(str(file_path))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path)], check=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening Excel file: {e}")
            return False

    def open_charts_folder(self) -> bool:
        """Open the charts folder in the file explorer"""
        try:
            if not self.charts_path.exists():
                self.logger.error(f"Charts folder does not exist: {self.charts_path}")
                return False
            
            if platform.system() == "Windows":
                os.startfile(str(self.charts_path))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.charts_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(self.charts_path)], check=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening charts folder: {e}")
            return False

    def get_report_summary(self) -> Dict[str, Any]:
        """Get a summary of the current study for reporting"""
        summary = {
            'client': self.client,
            'ref_project': self.ref_project,
            'batch_number': self.batch_number,
            'elements_count': len(self.elements_summary),
            'elements': list(self.elements_summary.keys()),
            'charts_available': self.validate_charts_exist(),
            'paths': {
                'base_path': str(self.base_path),
                'charts_path': str(self.charts_path),
                'excel_output_path': str(self.excel_output_path)
            }
        }
        
        return summary


# Example usage and testing
def example_usage():
    """Example of how to use the ExcelReportService"""
    
    # Initialize service
    service = ExcelReportService(
        client="BMW",
        ref_project="SEAT_BELT_BUCKLE_v2.1", 
        batch_number="LOT2024_001"
    )
    
    # Generate complete report
    success, result = service.generate_complete_report(
        part_description="Safety Belt Buckle Assembly - Critical Dimension Analysis",
        drawing_number="BMW-SB-2024-001-Rev.C",
        methodology="cmm",
        facility="SOME Manufacturing Plant - Barcelona",
        dimension_class="critical",
        generate_charts=True,
        open_file=True
    )
    
    if success:
        print(f"✅ Complete report generated successfully!")
        print(f"📁 File location: {result}")
        
        # Get summary
        summary = service.get_report_summary()
        print(f"📊 Report summary:")
        print(f"   - Elements analyzed: {summary['elements_count']}")
        print(f"   - Elements: {', '.join(summary['elements'])}")
        
    else:
        print(f"❌ Error generating report: {result}")


if __name__ == "__main__":
    example_usage()