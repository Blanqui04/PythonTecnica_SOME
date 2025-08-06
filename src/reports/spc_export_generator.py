# src/reports/excel_spc_export_generator.py - FIXED VERSION
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import logging

from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Border, Side, Alignment, NamedStyle)
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image

from src.models.plotting.spc_data_loader import SPCDataLoader
from src.gui.logging_config import logger as base_logger


class ExcelSPCReportGenerator:
    """
    Professional Excel report generator for Statistical Process Control analysis.
    Creates comprehensive reports suitable for automotive industry PPAP documentation.
    FIXED: Proper chart path resolution and error handling.
    """
    
    # Corporate colors based on SOME company branding
    COLORS = {
        'primary_blue': '2C3E50',      # Dark blue (main header)
        'secondary_blue': '34495E',     # Medium blue (subheaders)
        'accent_blue': '3498DB',        # Light blue (highlights)
        'white': 'FFFFFF',
        'light_gray': 'F8F9FA',        # Background
        'medium_gray': 'DEE2E6',       # Borders
        'dark_gray': '495057',         # Text
        'success_green': '28A745',     # Good values
        'warning_orange': 'FFC107',    # Warning values
        'danger_red': 'DC3545',        # Critical values
        'professional_gray': 'F5F5F5'  # Table backgrounds
    }
    
    # Chart types and their display names
    CHART_TYPES = {
        'capability': 'Process Capability Chart',
        'normality': 'Normality Analysis',
        'extrapolation': 'Distribution Analysis',
        'individuals': 'Individual Values Chart (I-Chart)',
        'moving_range': 'Moving Range Chart (MR-Chart)'
    }
    
    # Statistical parameters and their descriptions
    STATISTICAL_PARAMETERS = {
        'sample_size': 'Sample Size (n)',
        'mean': 'Mean (X̄)',
        'nominal': 'Nominal Value',
        'std_short': 'Short-term Std Dev (σ_st)',
        'std_long': 'Long-term Std Dev (σ_lt)', 
        'cp': 'Process Capability (Cp)',
        'cpk': 'Process Capability Index (Cpk)',
        'pp': 'Process Performance (Pp)',
        'ppk': 'Process Performance Index (Ppk)',
        'ppm_short': 'PPM Defects (Short-term)',
        'ppm_long': 'PPM Defects (Long-term)',
        'p_value': 'Anderson-Darling p-value',
        'ad_value': 'Anderson-Darling Statistic',
        'tolerance': 'Tolerance Range',
        'lsl': 'Lower Specification Limit (LSL)',
        'usl': 'Upper Specification Limit (USL)'
    }

    def __init__(
        self,
        client: str,
        ref_project: str,
        batch_number: str,
        base_path: str = "./data/spc",
        charts_path: str = "./data/reports/charts",
        output_path: str = "./data/reports/excel",
        logger: Optional[logging.Logger] = None
    ):
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.base_path = Path(base_path)
        self.charts_path = Path(charts_path)
        self.output_path = Path(output_path)
        self.logger = logger or base_logger.getChild(self.__class__.__name__)
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data
        self.elements_data = {}
        self.workbook = None
        self.styles_created = False
        
        self.logger.info(f"Initialized Excel SPC Report Generator for {client}_{ref_project}_{batch_number}")
        self.logger.info(f"Charts will be read from: {self.charts_path}")

    def create_styles(self):
        """Create all the styles needed for the professional report"""
        if self.styles_created:
            return
            
        # Main header style
        main_header = NamedStyle(name="main_header")
        main_header.font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
        main_header.fill = PatternFill(start_color=self.COLORS['primary_blue'], 
                                     end_color=self.COLORS['primary_blue'], 
                                     fill_type='solid')
        main_header.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        main_header.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Section header style
        section_header = NamedStyle(name="section_header")
        section_header.font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
        section_header.fill = PatternFill(start_color=self.COLORS['secondary_blue'], 
                                        end_color=self.COLORS['secondary_blue'], 
                                        fill_type='solid')
        section_header.alignment = Alignment(horizontal='center', vertical='center')
        section_header.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Data header style
        data_header = NamedStyle(name="data_header")
        data_header.font = Font(name='Calibri', size=11, bold=True, color=self.COLORS['dark_gray'])
        data_header.fill = PatternFill(start_color=self.COLORS['light_gray'], 
                                     end_color=self.COLORS['light_gray'], 
                                     fill_type='solid')
        data_header.alignment = Alignment(horizontal='center', vertical='center')
        data_header.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Data cell style
        data_cell = NamedStyle(name="data_cell")
        data_cell.font = Font(name='Calibri', size=10, color=self.COLORS['dark_gray'])
        data_cell.alignment = Alignment(horizontal='center', vertical='center')
        data_cell.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Parameter name style
        param_name = NamedStyle(name="param_name")
        param_name.font = Font(name='Calibri', size=10, bold=True, color=self.COLORS['dark_gray'])
        param_name.fill = PatternFill(start_color=self.COLORS['professional_gray'], 
                                    end_color=self.COLORS['professional_gray'], 
                                    fill_type='solid')
        param_name.alignment = Alignment(horizontal='left', vertical='center')
        param_name.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Title style
        title_style = NamedStyle(name="title_style")
        title_style.font = Font(name='Calibri', size=18, bold=True, color=self.COLORS['primary_blue'])
        title_style.alignment = Alignment(horizontal='center', vertical='center')
        
        # Subtitle style
        subtitle_style = NamedStyle(name="subtitle_style")
        subtitle_style.font = Font(name='Calibri', size=12, color=self.COLORS['dark_gray'])
        subtitle_style.alignment = Alignment(horizontal='center', vertical='center')
        
        # Add styles to workbook
        try:
            self.workbook.add_named_style(main_header)
            self.workbook.add_named_style(section_header)
            self.workbook.add_named_style(data_header)
            self.workbook.add_named_style(data_cell)
            self.workbook.add_named_style(param_name)
            self.workbook.add_named_style(title_style)
            self.workbook.add_named_style(subtitle_style)
            
            self.styles_created = True
            self.logger.debug("Created all Excel styles successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating styles: {e}")

    def load_data(self) -> bool:
        """Load SPC data for the report"""
        try:
            # Try primary folder structure first
            folder_name = f"{self.client}_{self.ref_project}_{self.batch_number}"
            filename = f"{self.ref_project}_{self.batch_number}_complete_report.json"
            report_path = self.base_path / folder_name / filename
            
            if not report_path.exists():
                # Try alternative folder structure
                alt_folder_name = f"{self.client}_{self.ref_project}"
                alt_report_path = self.base_path / alt_folder_name / filename
                
                if alt_report_path.exists():
                    self.logger.info(f"Using alternative path: {alt_report_path}")
                    report_path = alt_report_path
                else:
                    self.logger.error(f"SPC report not found at either path:\n  Primary: {report_path}\n  Alternative: {alt_report_path}")
                    return False
            
            data_loader = SPCDataLoader(self.ref_project, self.base_path)
            self.elements_data = data_loader.load_complete_report(report_path)
            
            if not self.elements_data:
                self.logger.error("No elements data loaded")
                return False
                
            self.logger.info(f"Loaded data for {len(self.elements_data)} elements")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return False

    def get_chart_path(self, element_key: str, chart_type: str) -> Optional[Path]:
        """
        Get the path to a specific chart file.
        CRITICAL FIX: Use the exact same logic as the chart generation.
        """
        try:
            # Get element data to extract original name and cavity
            element_data = self.elements_data.get(element_key, {})
            
            # Extract original element name
            original_element_name = element_data.get("element_name")
            cavity = element_data.get("cavity", "")
            
            # If we don't have the original name, extract from composite key
            if not original_element_name:
                if " Cavity " in element_key:
                    original_element_name = element_key.split(" Cavity ")[0]
                elif "_cavity_" in element_key:
                    original_element_name = element_key.split("_cavity_")[0]
                else:
                    original_element_name = element_key
                
                self.logger.warning(f"Extracted original element name '{original_element_name}' from key '{element_key}'")
            
            # CRITICAL: Match the exact filename format from SPCChartManager
            # Format: {chart_type}_{batch_number}_{original_element_name}_{cavity}.png
            if cavity and str(cavity).strip():
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
            else:
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
            
            chart_path = self.charts_path / filename
            
            self.logger.debug(f"Chart path for {element_key}/{chart_type}: {chart_path}")
            
            if chart_path.exists():
                return chart_path
            else:
                self.logger.warning(f"Chart not found: {chart_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting chart path for {element_key}/{chart_type}: {e}")
            return None

    def create_report(self, 
                     part_description: str = "",
                     drawing_number: str = "",
                     methodology: str = "MSA",
                     facility: str = "",
                     dimension_class: str = "CC") -> str:
        """
        Create the complete Excel SPC report
        
        Args:
            part_description: Description of the part being analyzed
            drawing_number: Technical drawing number
            methodology: Measurement methodology (MSA, CMM, etc.)
            facility: Manufacturing facility name
            dimension_class: Dimension classification (CC, SC, IC)
            
        Returns:
            str: Path to the generated Excel file
        """
        try:
            # Load data first
            if not self.load_data():
                raise ValueError("Failed to load SPC data")
            
            # Create workbook
            self.workbook = Workbook()
            
            # Remove default sheet
            if 'Sheet' in self.workbook.sheetnames:
                self.workbook.remove(self.workbook['Sheet'])
            
            # Create styles
            self.create_styles()
            
            # Create a sheet for each element
            sheets_created = 0
            for element_key, element_data in self.elements_data.items():
                self.logger.info(f"Creating sheet for element: {element_key}")
                
                try:
                    # Create worksheet with truncated name if necessary
                    sheet_name = element_key[:31] if len(element_key) > 31 else element_key
                    # Replace invalid characters for sheet names
                    sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace('[', '').replace(']', '')
                    
                    ws = self.workbook.create_sheet(title=sheet_name)
                    
                    # Create the report content for this element
                    self.create_element_sheet(
                        ws, element_key, element_data,
                        part_description, drawing_number, 
                        methodology, facility, dimension_class
                    )
                    
                    sheets_created += 1
                    self.logger.info(f"✓ Created sheet for element: {element_key}")
                    
                except Exception as e:
                    self.logger.error(f"✗ Failed to create sheet for element {element_key}: {e}")
                    continue
            
            if sheets_created == 0:
                raise ValueError("No sheets were created successfully")
            
            # Save the workbook
            filename = f"{self.ref_project}_{self.batch_number}_SPC_Report.xlsx"
            output_file = self.output_path / filename
            
            self.workbook.save(output_file)
            self.logger.info(f"Excel report saved: {output_file} ({sheets_created} sheets)")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error creating Excel report: {e}")
            raise

    def create_element_sheet(self, 
                           ws: Worksheet, 
                           element_key: str, 
                           element_data: Dict[str, Any],
                           part_description: str,
                           drawing_number: str,
                           methodology: str,
                           facility: str,
                           dimension_class: str):
        """Create a complete sheet for one element"""
        
        current_row = 1
        
        # 1. Header section
        current_row = self.create_header_section(
            ws, current_row, element_key, part_description, 
            drawing_number, methodology, facility, dimension_class
        )
        
        # 2. Statistical summary table
        current_row = self.create_statistical_summary(ws, current_row, element_data)
        
        # 3. Charts section
        current_row = self.create_charts_section(ws, current_row, element_key)
        
        # 4. Notes and signature section
        current_row = self.create_notes_signature_section(ws, current_row)
        
        # Set column widths
        self.set_column_widths(ws)
        
        # Set page setup
        self.setup_page_formatting(ws)

    def create_header_section(self, 
                            ws: Worksheet, 
                            start_row: int, 
                            element_key: str,
                            part_description: str,
                            drawing_number: str,
                            methodology: str,
                            facility: str,
                            dimension_class: str) -> int:
        """Create the professional header section"""
        
        current_row = start_row
        
        # Add logo
        logo_path = Path("./assets/images/gui/logo_some.png")
        if logo_path.exists():
            try:
                img = Image(str(logo_path))
                # Resize logo to fit nicely
                img.height = 80
                img.width = int(img.width * (80 / img.height))  # Maintain aspect ratio
                ws.add_image(img, f'A{current_row}')
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")
        
        # Main title - merge across multiple columns
        ws.merge_cells(f'D{current_row}:J{current_row}')
        title_cell = ws[f'D{current_row}']
        title_cell.value = "STATISTICAL CAPABILITY ANALYSIS"
        title_cell.style = 'title_style'
        
        current_row += 2
        
        # Company info and part info side by side
        # Left side - Company info
        ws[f'A{current_row}'] = "Client:"
        ws[f'A{current_row}'].style = 'param_name'
        ws[f'B{current_row}'] = self.client
        ws[f'B{current_row}'].style = 'data_cell'
        
        ws[f'A{current_row + 1}'] = "Reference:"
        ws[f'A{current_row + 1}'].style = 'param_name'
        ws[f'B{current_row + 1}'] = self.ref_project
        ws[f'B{current_row + 1}'].style = 'data_cell'
        
        ws[f'A{current_row + 2}'] = "Batch Number:"
        ws[f'A{current_row + 2}'].style = 'param_name'
        ws[f'B{current_row + 2}'] = self.batch_number
        ws[f'B{current_row + 2}'].style = 'data_cell'
        
        ws[f'A{current_row + 3}'] = "Facility:"
        ws[f'A{current_row + 3}'].style = 'param_name'
        ws[f'B{current_row + 3}'] = facility
        ws[f'B{current_row + 3}'].style = 'data_cell'
        
        # Right side - Part info
        ws[f'F{current_row}'] = "Part Description:"
        ws[f'F{current_row}'].style = 'param_name'
        ws[f'G{current_row}'] = part_description
        ws[f'G{current_row}'].style = 'data_cell'
        
        ws[f'F{current_row + 1}'] = "Drawing Number:"
        ws[f'F{current_row + 1}'].style = 'param_name'
        ws[f'G{current_row + 1}'] = drawing_number
        ws[f'G{current_row + 1}'].style = 'data_cell'
        
        ws[f'F{current_row + 2}'] = "Methodology:"
        ws[f'F{current_row + 2}'].style = 'param_name'
        ws[f'G{current_row + 2}'] = methodology
        ws[f'G{current_row + 2}'].style = 'data_cell'
        
        ws[f'F{current_row + 3}'] = "Dimension Class:"
        ws[f'F{current_row + 3}'].style = 'param_name'
        ws[f'G{current_row + 3}'] = dimension_class
        ws[f'G{current_row + 3}'].style = 'data_cell'
        
        current_row += 5
        
        # Element section header
        ws.merge_cells(f'A{current_row}:J{current_row}')
        element_header = ws[f'A{current_row}']
        element_header.value = f"ELEMENT ANALYSIS: {element_key}"
        element_header.style = 'section_header'
        
        current_row += 2
        
        return current_row

    def create_statistical_summary(self, 
                                 ws: Worksheet, 
                                 start_row: int, 
                                 element_data: Dict[str, Any]) -> int:
        """Create the statistical summary table"""
        
        current_row = start_row
        
        # Section title
        ws.merge_cells(f'A{current_row}:J{current_row}')
        summary_title = ws[f'A{current_row}']
        summary_title.value = "STATISTICAL SUMMARY"
        summary_title.style = 'data_header'
        
        current_row += 1
        
        # Create summary table in two columns
        left_col_params = [
            ('sample_size', 'Sample Size (n)'),
            ('mean', 'Mean (X̄)'),
            ('nominal', 'Nominal Value'),
            ('std_short', 'Short-term Std Dev (σ_st)'),
            ('std_long', 'Long-term Std Dev (σ_lt)'),
            ('tolerance', 'Tolerance Range'),
        ]
        
        right_col_params = [
            ('cp', 'Process Capability (Cp)'),
            ('cpk', 'Process Capability Index (Cpk)'),
            ('pp', 'Process Performance (Pp)'),
            ('ppk', 'Process Performance Index (Ppk)'),
            ('p_value', 'Anderson-Darling p-value'),
            ('ad_value', 'Anderson-Darling Statistic'),
        ]
        
        # Left column
        for i, (key, display_name) in enumerate(left_col_params):
            row = current_row + i
            ws[f'A{row}'] = display_name
            ws[f'A{row}'].style = 'param_name'
            
            value = element_data.get(key, 'N/A')
            if isinstance(value, (int, float)) and value != 'N/A':
                if key in ['cp', 'cpk', 'pp', 'ppk']:
                    formatted_value = f"{value:.3f}"
                elif key in ['p_value']:
                    formatted_value = f"{value:.4f}"
                elif key in ['std_short', 'std_long', 'mean']:
                    formatted_value = f"{value:.4f}"
                elif key == 'tolerance':
                    if isinstance(value, list) and len(value) == 2:
                        formatted_value = f"[{value[0]:.3f}, {value[1]:.3f}]"
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            ws[f'B{row}'] = formatted_value
            ws[f'B{row}'].style = 'data_cell'
        
        # Right column
        for i, (key, display_name) in enumerate(right_col_params):
            row = current_row + i
            ws[f'F{row}'] = display_name
            ws[f'F{row}'].style = 'param_name'
            
            value = element_data.get(key, 'N/A')
            if isinstance(value, (int, float)) and value != 'N/A':
                if key in ['cp', 'cpk', 'pp', 'ppk']:
                    formatted_value = f"{value:.3f}"
                elif key in ['p_value']:
                    formatted_value = f"{value:.4f}"
                elif key in ['ad_value']:
                    formatted_value = f"{value:.4f}"
                else:
                    formatted_value = f"{value:.4f}"
            else:
                formatted_value = str(value)
            
            ws[f'G{row}'] = formatted_value
            ws[f'G{row}'].style = 'data_cell'
        
        current_row += max(len(left_col_params), len(right_col_params)) + 2
        
        return current_row

    def create_charts_section(self, 
                            ws: Worksheet, 
                            start_row: int, 
                            element_key: str) -> int:
        """Create the charts section with IMPROVED chart path resolution"""
        
        current_row = start_row
        
        # Section title
        ws.merge_cells(f'A{current_row}:J{current_row}')
        charts_title = ws[f'A{current_row}']
        charts_title.value = "STATISTICAL CONTROL CHARTS"
        charts_title.style = 'data_header'
        
        current_row += 2
        
        # Add each chart with enhanced error handling
        charts_added = 0
        for chart_type, chart_display_name in self.CHART_TYPES.items():
            chart_path = self.get_chart_path(element_key, chart_type)
            
            if chart_path and chart_path.exists():
                try:
                    # Add chart title
                    ws.merge_cells(f'A{current_row}:J{current_row}')
                    chart_title_cell = ws[f'A{current_row}']
                    chart_title_cell.value = chart_display_name
                    chart_title_cell.style = 'param_name'
                    
                    current_row += 1
                    
                    # Add chart image with better error handling
                    img = Image(str(chart_path))
                    
                    # Resize to fit nicely in Excel (maintain aspect ratio)
                    max_width = 600  # pixels
                    max_height = 400  # pixels
                    
                    aspect_ratio = img.width / img.height
                    if img.width > max_width:
                        img.width = max_width
                        img.height = int(max_width / aspect_ratio)
                    
                    if img.height > max_height:
                        img.height = max_height
                        img.width = int(max_height * aspect_ratio)
                    
                    # Position chart
                    ws.add_image(img, f'A{current_row}')
                    
                    # Skip rows based on chart size (approximate)
                    rows_to_skip = int(img.height / 20) + 2  # Approximate row height
                    current_row += rows_to_skip
                    
                    charts_added += 1
                    
                    self.logger.info(f"✓ Added chart: {chart_display_name} for {element_key}")
                    
                except Exception as e:
                    self.logger.error(f"✗ Error adding chart {chart_type} for {element_key}: {e}")
                    # Add error message in the sheet
                    ws[f'A{current_row}'] = f"Error loading {chart_display_name}: {str(e)}"
                    current_row += 2
            else:
                self.logger.warning(f"⚠ Chart not found: {chart_type} for {element_key}")
                # Add note about missing chart
                ws[f'A{current_row}'] = f"{chart_display_name}: Chart not available"
                ws[f'A{current_row}'].style = 'param_name'
                current_row += 2
        
        if charts_added == 0:
            ws[f'A{current_row}'] = "No charts available for this element"
            ws[f'A{current_row}'].style = 'param_name'
            current_row += 2
        else:
            self.logger.info(f"Added {charts_added}/{len(self.CHART_TYPES)} charts for element {element_key}")
        
        return current_row

    def create_notes_signature_section(self, 
                                     ws: Worksheet, 
                                     start_row: int) -> int:
        """Create notes and signature section"""
        
        current_row = start_row
        
        # Notes section
        ws.merge_cells(f'A{current_row}:J{current_row}')
        notes_title = ws[f'A{current_row}']
        notes_title.value = "NOTES"
        notes_title.style = 'data_header'
        
        current_row += 1
        
        # Merge several rows for notes
        ws.merge_cells(f'A{current_row}:J{current_row + 3}')
        notes_cell = ws[f'A{current_row}']
        notes_cell.value = ""  # Empty for manual entry
        notes_cell.style = 'data_cell'
        notes_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        
        current_row += 5
        
        # Signature section
        current_row += 2
        
        # Date
        ws[f'A{current_row}'] = "Date:"
        ws[f'A{current_row}'].style = 'param_name'
        ws[f'B{current_row}'] = datetime.now().strftime("%Y-%m-%d")
        ws[f'B{current_row}'].style = 'data_cell'
        
        # Responsible signature
        ws[f'F{current_row}'] = "Responsible:"
        ws[f'F{current_row}'].style = 'param_name'
        ws.merge_cells(f'G{current_row}:I{current_row}')
        ws[f'G{current_row}'].style = 'data_cell'
        
        current_row += 2
        
        # Project leader
        ws[f'A{current_row}'] = "PROJECT LEADER:"
        ws[f'A{current_row}'].style = 'param_name'
        ws.merge_cells(f'B{current_row}:I{current_row}')
        ws[f'B{current_row}'].style = 'data_cell'
        
        current_row += 3
        
        return current_row

    def set_column_widths(self, ws: Worksheet):
        """Set appropriate column widths"""
        column_widths = {
            'A': 25,  'B': 20,  'C': 15,  'D': 15,  'E': 15,
            'F': 25,  'G': 20,  'H': 15,  'I': 15,  'J': 15
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    def setup_page_formatting(self, ws: Worksheet):
        """Setup page formatting for professional appearance"""
        # Set page orientation to landscape for better chart visibility
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        
        # Set margins
        ws.page_margins.left = 0.7
        ws.page_margins.right = 0.7
        ws.page_margins.top = 0.75
        ws.page_margins.bottom = 0.75
        
        # Set print area to fit content
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        
        # Add header and footer
        ws.oddHeader.center.text = "Statistical Capability Analysis Report"
        ws.oddFooter.left.text = f"Client: {self.client}"
        ws.oddFooter.center.text = f"Reference: {self.ref_project}"
        ws.oddFooter.right.text = "Page &P of &N"