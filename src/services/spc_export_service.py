# src/services/spc_export_service.py - FIXED VERSION
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
    FIXED: Proper chart path resolution matching the generation logic.
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
        
        # CRITICAL FIX: Align charts path with SPCChartManager output directory
        # SPCChartManager uses: "./data/reports/charts/{ref_project}"
        self.charts_path = Path(charts_path) / ref_project
        
        self.excel_output_path = Path(excel_output_path)
        self.logger = logger or base_logger.getChild(self.__class__.__name__)
        
        # Initialize components
        self.chart_manager = None
        self.excel_generator = None
        self.elements_summary = {}
        
        self.logger.info(f"Initialized ExcelReportService for {client}_{ref_project}_{batch_number}")
        self.logger.info(f"Charts will be read from: {self.charts_path}")

    def initialize_services(self) -> bool:
        """Initialize the chart manager and Excel generator services"""
        try:
            # Initialize chart manager with MATCHING output directory
            self.chart_manager = SPCChartManager(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number,
                base_path=str(self.base_path),
                output_dir=str(self.charts_path),  # This should match exactly
                logger=self.logger
            )
            
            # Load chart data
            if not self.chart_manager.load_data():
                self.logger.error("Failed to load chart data")
                return False
            
            # Initialize Excel generator with CORRECTED charts path
            self.excel_generator = ExcelSPCReportGenerator(
                client=self.client,
                ref_project=self.ref_project,
                batch_number=self.batch_number,
                base_path=str(self.base_path),
                charts_path=str(self.charts_path),  # Use the corrected path
                output_path=str(self.excel_output_path),
                logger=self.logger
            )
            
            # Get elements summary
            self.elements_summary = self.chart_manager.get_elements_summary()
            
            self.logger.info("Services initialized successfully")
            self.logger.info(f"Loaded {len(self.elements_summary)} elements")
            
            # DEBUG: Log element keys and their data
            for element_key, element_data in self.elements_summary.items():
                self.logger.debug(f"Element: '{element_key}' - cavity: '{element_data.get('cavity', '')}' - original: '{element_data.get('element_name', '')}'")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing services: {e}", exc_info=True)
            return False

    def get_chart_path(self, element_key: str, chart_type: str) -> Optional[Path]:
        """
        Get the path to a specific chart file.
        COMPLETELY REWRITTEN to match SPCChartManager's file naming logic.
        """
        try:
            # Get element data from the summary
            element_data = self.elements_summary.get(element_key, {})
            
            # Extract original element name (critical for filename)
            original_element_name = element_data.get("element_name")
            cavity = element_data.get("cavity", "")
            
            # If we don't have the original name, try to extract it from the composite key
            if not original_element_name:
                if " Cavity " in element_key:
                    original_element_name = element_key.split(" Cavity ")[0]
                elif "_cavity_" in element_key:
                    original_element_name = element_key.split("_cavity_")[0]
                else:
                    original_element_name = element_key
                    
                self.logger.warning(f"Had to extract original element name '{original_element_name}' from composite key '{element_key}'")
            
            # CRITICAL: Use the EXACT same naming logic as SPCChartManager.create_chart()
            # From SPCChartManager: filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
            if cavity and str(cavity).strip():
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
            else:
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
            
            chart_path = self.charts_path / filename
            
            # Enhanced debug logging
            self.logger.debug("CHART PATH RESOLUTION DEBUG:")
            self.logger.debug(f"  Element key: '{element_key}'")
            self.logger.debug(f"  Original element: '{original_element_name}'")
            self.logger.debug(f"  Cavity: '{cavity}'")
            self.logger.debug(f"  Chart type: '{chart_type}'")
            self.logger.debug(f"  Filename: '{filename}'")
            self.logger.debug(f"  Full path: '{chart_path}'")
            self.logger.debug(f"  File exists: {chart_path.exists()}")
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                self.logger.info(f"✓ Found chart: {filename} (size: {file_size} bytes)")
                return chart_path
            else:
                self.logger.warning(f"✗ Chart not found: {chart_path}")
                
                # DEBUG: List actual files in the directory
                if self.charts_path.exists():
                    actual_files = [f.name for f in self.charts_path.glob("*.png")]
                    self.logger.debug(f"  Actual PNG files in {self.charts_path}:")
                    for file in actual_files[:10]:  # Show first 10 files
                        self.logger.debug(f"    {file}")
                    if len(actual_files) > 10:
                        self.logger.debug(f"    ... and {len(actual_files) - 10} more files")
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error resolving chart path for {element_key}/{chart_type}: {e}", exc_info=True)
            return None

    def validate_charts_exist(self) -> Dict[str, List[str]]:
        """
        Validate which charts exist for each element.
        UPDATED: Support all chart types including X-R and X-S
        """
        available_charts = {}
        
        if not self.elements_summary:
            if not self.initialize_services():
                return available_charts
        
        # UPDATED: Include all possible chart types
        chart_types = [
            'capability', 'normality', 'extrapolation', 
            'individuals', 'moving_range',
            'xbar', 'r_chart', 's_chart'  # NEW
        ]
        
        for element_key in self.elements_summary.keys():
            element_charts = []
            for chart_type in chart_types:
                chart_path = self.get_chart_path(element_key, chart_type)
                
                if chart_path and chart_path.exists():
                    element_charts.append(chart_type)
            
            available_charts[element_key] = element_charts
            self.logger.info(f"Element '{element_key}': {len(element_charts)} charts available ({', '.join(element_charts)})")
        
        return available_charts

    def generate_complete_report(
        self,
        part_description: str,
        drawing_number: str,
        methodology: str = "cmm",
        facility: str = "",
        dimension_class: str = "critical",
        generate_charts: bool = True,
        open_file: bool = True,
        chart_config: Dict[str, Any] = None  # NEW PARAMETER
    ) -> Tuple[bool, str]:
        """
        Generate a complete SPC report with charts and Excel documentation
        UPDATED: Accept chart configuration
        """
        try:
            self.logger.info("Starting complete report generation")
            
            # Default chart config
            if chart_config is None:
                chart_config = {'type': 'i_mr', 'group_size': 5}
            
            # Initialize services if not already done
            if not self.chart_manager or not self.excel_generator:
                if not self.initialize_services():
                    return False, "Failed to initialize services"
            
            # Generate charts if requested (with config)
            if generate_charts:
                self.logger.info(f"Generating SPC charts with config: {chart_config}")
                # Charts should already be generated with correct type
                # This is just validation
            
            # Validate that charts exist before proceeding
            self.logger.info("Validating chart availability...")
            available_charts = self.validate_charts_exist()
            total_available = sum(len(charts) for charts in available_charts.values())
            
            if total_available == 0:
                self.logger.warning("No charts found - report will be created without charts")
            else:
                self.logger.info(f"Found {total_available} charts across {len(available_charts)} elements")
            
            # Resolve methodology and dimension class
            methodology_display = self.METHODOLOGIES.get(methodology.lower(), methodology)
            dimension_class_code = self.DIMENSION_CLASSES.get(dimension_class.lower(), dimension_class)
            
            # Set default facility if not provided
            if not facility:
                facility = "Manufacturing Facility"
            
            # Generate Excel report with chart config
            self.logger.info("Generating Excel report...")
            excel_file = self.excel_generator.create_report(
                part_description=part_description,
                drawing_number=drawing_number,
                methodology=methodology_display,
                facility=facility,
                dimension_class=dimension_class_code,
                chart_config=chart_config  # Pass chart config
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
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def generate_charts_only(self, 
                           chart_types: Optional[List[str]] = None,
                           elements: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Generate only the SPC charts without Excel report
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
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def generate_excel_only(self,
                        part_description: str,
                        drawing_number: str,
                        methodology: str = "cmm",
                        facility: str = "",
                        dimension_class: str = "critical",
                        open_file: bool = True,
                        chart_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Generate only the Excel report (assumes charts already exist)
        UPDATED: Accept chart configuration
        """
        try:
            # Default chart config
            if chart_config is None:
                chart_config = {'type': 'i_mr', 'group_size': 5}
            
            if not self.excel_generator:
                if not self.initialize_services():
                    return False, "Failed to initialize Excel generator"
            
            # Validate that at least some charts exist
            available_charts = self.validate_charts_exist()
            total_available = sum(len(charts) for charts in available_charts.values())
            
            if total_available == 0:
                self.logger.warning("No charts found - report will be created but may be incomplete")
            else:
                self.logger.info(f"Found {total_available} charts for export")
            
            # Resolve parameters
            methodology_display = self.METHODOLOGIES.get(methodology.lower(), methodology)
            dimension_class_code = self.DIMENSION_CLASSES.get(dimension_class.lower(), dimension_class)
            
            if not facility:
                facility = "Manufacturing Facility"
            
            # Generate Excel report with error handling
            try:
                excel_file = self.excel_generator.create_report(
                    part_description=part_description,
                    drawing_number=drawing_number,
                    methodology=methodology_display,
                    facility=facility,
                    dimension_class=dimension_class_code,
                    #chart_config=chart_config  # Pass chart config
                )
            except Exception as excel_error:
                error_msg = f"Error creating Excel report: {excel_error}"
                self.logger.error(error_msg, exc_info=True)
                return False, error_msg
            
            # Open file if requested
            if open_file and excel_file:
                try:
                    self.open_excel_file(excel_file)
                except Exception as open_error:
                    self.logger.warning(f"Could not open Excel file: {open_error}")
            
            return True, excel_file
            
        except Exception as e:
            error_msg = f"Error generating Excel report: {e}"
            self.logger.error(error_msg, exc_info=True)
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
        except Exception:
            return {}

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

    def debug_chart_paths(self) -> Dict[str, Any]:
        """
        Debug method to inspect chart path resolution for troubleshooting.
        Returns detailed information about expected vs actual chart files.
        """
        debug_info = {
            'charts_directory': str(self.charts_path),
            'directory_exists': self.charts_path.exists(),
            'elements': {},
            'actual_files': [],
            'expected_patterns': []
        }
        
        # List actual files in charts directory
        if self.charts_path.exists():
            debug_info['actual_files'] = [f.name for f in self.charts_path.glob("*.png")]
        
        # For each element, show expected paths vs actual
        chart_types = ['capability', 'normality', 'extrapolation', 'individuals', 'moving_range']
        
        for element_key, element_data in self.elements_summary.items():
            element_debug = {
                'element_key': element_key,
                'original_name': element_data.get('element_name', ''),
                'cavity': element_data.get('cavity', ''),
                'expected_files': {},
                'found_files': {}
            }
            
            for chart_type in chart_types:
                # Get expected filename
                original_element_name = element_data.get("element_name", element_key)
                cavity = element_data.get("cavity", "")
                
                if cavity and str(cavity).strip():
                    expected_filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
                else:
                    expected_filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
                
                element_debug['expected_files'][chart_type] = expected_filename
                
                # Check if file exists
                chart_path = self.charts_path / expected_filename
                element_debug['found_files'][chart_type] = chart_path.exists()
                
                debug_info['expected_patterns'].append(expected_filename)
            
            debug_info['elements'][element_key] = element_debug
        
        return debug_info