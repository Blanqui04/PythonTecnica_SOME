# src/reports/excel_spc_export_generator.py - PROFESSIONAL AUTOMOTIVE FORMAT
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import logging

from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Border, Side, Alignment, NamedStyle)
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image
from openpyxl.worksheet.page import PageMargins

from src.models.plotting.spc_data_loader import SPCDataLoader
from src.gui.logging_config import logger as base_logger


class ExcelSPCReportGenerator:
    """
    Professional Excel report generator for Statistical Process Control analysis.
    Creates comprehensive reports suitable for automotive industry PPAP documentation
    and major OEM requirements (VW, Mercedes, BMW, Tesla, etc.).
    """
    
    # Professional automotive industry color palette
    COLORS = {
        'primary_blue': '1B365D',       # Deep corporate blue (headers)
        'secondary_blue': '2E5266',     # Medium blue (section headers)
        'accent_blue': '4A90A4',        # Light blue (highlights)
        'white': 'FFFFFF',
        'light_gray': 'F7F8F9',        # Background sections
        'medium_gray': 'E1E5E9',       # Table borders
        'dark_gray': '2C3E50',         # Professional text
        'success_green': '27AE60',     # Capability indicators
        'warning_orange': 'F39C12',    # Warning values
        'danger_red': 'E74C3C',        # Critical values
        'table_header': 'ECF0F1',      # Table headers
        'table_alt': 'F8F9FA'          # Alternating rows
    }
    
    # Chart types and their professional display names
    CHART_TYPES = {
        'normality': 'NORMALITY ANALYSIS',
        'capability': 'PROCESS CAPABILITY',
        'individuals': 'I-CHART (INDIVIDUALS)',
        'moving_range': 'MR-CHART (MOVING RANGE)',
        'extrapolation': 'DISTRIBUTION ANALYSIS'
    }
    
    # Statistical parameters with professional descriptions (IMPROVED)
    STATISTICAL_PARAMETERS = {
        'sample_size': 'Sample Size (n)',
        'mean': 'Mean (X̄)',
        'nominal': 'Nominal Target',
        'std_short': 'Short-term Std Dev (s)',
        'std_long': 'Long-term Std Dev (σ)', 
        'cp': 'CP',
        'cpk': 'CPK',
        'pp': 'PP',
        'ppk': 'PPK',
        'ppm_short': 'PPM Defective (Short-term)',
        'ppm_long': 'PPM Defective (Long-term)',
        'p_value': 'Normality p-value',
        'ad_value': 'Anderson-Darling Statistic',
        'tolerance': 'Specification Limits',
        'lsl': 'Lower Specification Limit',
        'usl': 'Upper Specification Limit'
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
        
        self.logger.info(f"Initialized Professional Excel SPC Report Generator for {client}_{ref_project}_{batch_number}")

    def create_professional_styles(self):
        """Create professional automotive industry styles with improved borders"""
        if self.styles_created:
            return
            
        # Document title style
        doc_title = NamedStyle(name="doc_title")
        doc_title.font = Font(name='Arial', size=20, bold=True, color=self.COLORS['primary_blue'])
        doc_title.alignment = Alignment(horizontal='center', vertical='center')
        
        # Document subtitle style
        doc_subtitle = NamedStyle(name="doc_subtitle")
        doc_subtitle.font = Font(name='Arial', size=12, color=self.COLORS['dark_gray'])
        doc_subtitle.alignment = Alignment(horizontal='center', vertical='center')
        
        # Main header style (company info) with complete borders
        main_header = NamedStyle(name="main_header")
        main_header.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        main_header.fill = PatternFill(start_color=self.COLORS['primary_blue'], 
                                     end_color=self.COLORS['primary_blue'], 
                                     fill_type='solid')
        main_header.alignment = Alignment(horizontal='center', vertical='center')
        main_header.border = self.create_full_border('medium', self.COLORS['primary_blue'])
        
        # Section header style with complete borders
        section_header = NamedStyle(name="section_header")
        section_header.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        section_header.fill = PatternFill(start_color=self.COLORS['secondary_blue'], 
                                        end_color=self.COLORS['secondary_blue'], 
                                        fill_type='solid')
        section_header.alignment = Alignment(horizontal='center', vertical='center')
        section_header.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Table header style with complete borders
        table_header = NamedStyle(name="table_header")
        table_header.font = Font(name='Arial', size=9, bold=True, color=self.COLORS['dark_gray'])
        table_header.fill = PatternFill(start_color=self.COLORS['table_header'], 
                                      end_color=self.COLORS['table_header'], 
                                      fill_type='solid')
        table_header.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        table_header.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Parameter label style with complete borders
        param_label = NamedStyle(name="param_label")
        param_label.font = Font(name='Arial', size=9, bold=True, color=self.COLORS['dark_gray'])
        param_label.fill = PatternFill(start_color=self.COLORS['light_gray'], 
                                     end_color=self.COLORS['light_gray'], 
                                     fill_type='solid')
        param_label.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        param_label.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Data cell style with complete borders
        data_cell = NamedStyle(name="data_cell")
        data_cell.font = Font(name='Arial', size=9, color=self.COLORS['dark_gray'])
        data_cell.alignment = Alignment(horizontal='center', vertical='center')
        data_cell.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Chart title style
        chart_title = NamedStyle(name="chart_title")
        chart_title.font = Font(name='Arial', size=11, bold=True, color=self.COLORS['secondary_blue'])
        chart_title.alignment = Alignment(horizontal='center', vertical='center')
        chart_title.fill = PatternFill(start_color=self.COLORS['light_gray'], 
                                     end_color=self.COLORS['light_gray'], 
                                     fill_type='solid')
        chart_title.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Notes style with complete borders
        notes_style = NamedStyle(name="notes_style")
        notes_style.font = Font(name='Arial', size=9, color=self.COLORS['dark_gray'])
        notes_style.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        notes_style.border = self.create_full_border('thin', self.COLORS['medium_gray'])
        
        # Add all styles to workbook
        try:
            styles_to_add = [
                doc_title, doc_subtitle, main_header, section_header,
                table_header, param_label, data_cell, chart_title, notes_style
            ]
            
            for style in styles_to_add:
                self.workbook.add_named_style(style)
            
            self.styles_created = True
            self.logger.debug("Created all professional Excel styles with complete borders")
            
        except Exception as e:
            self.logger.error(f"Error creating styles: {e}")

    def create_full_border(self, style: str = 'thin', color: str = None) -> Border:
        """Create a complete border for all sides"""
        if color is None:
            color = self.COLORS['medium_gray']
        
        return Border(
            left=Side(style=style, color=color),
            right=Side(style=style, color=color),
            top=Side(style=style, color=color),
            bottom=Side(style=style, color=color)
        )

    def apply_complete_borders_to_range(self, ws: Worksheet, start_cell: str, end_cell: str):
        """Apply complete borders to a range of cells"""
        for row in ws[f"{start_cell}:{end_cell}"]:
            for cell in row:
                cell.border = self.create_full_border('thin', self.COLORS['medium_gray'])

    def extract_element_name(self, element_key: str) -> str:
        """Extract clean element name without cavity information"""
        # Remove cavity information from element name
        if " Cavity " in element_key:
            return element_key.split(" Cavity ")[0]
        elif "_cavity_" in element_key:
            return element_key.split("_cavity_")[0]
        elif " cavity " in element_key.lower():
            return element_key.lower().split(" cavity ")[0]
        return element_key

    def load_data(self) -> bool:
        """Load SPC data for the report"""
        try:
            folder_name = f"{self.client}_{self.ref_project}_{self.batch_number}"
            filename = f"{self.ref_project}_{self.batch_number}_complete_report.json"
            report_path = self.base_path / folder_name / filename
            
            if not report_path.exists():
                alt_folder_name = f"{self.client}_{self.ref_project}"
                alt_report_path = self.base_path / alt_folder_name / filename
                
                if alt_report_path.exists():
                    report_path = alt_report_path
                else:
                    self.logger.error("SPC report not found at either path")
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
        """Get the path to a specific chart file with improved error handling"""
        try:
            element_data = self.elements_data.get(element_key, {})
            original_element_name = element_data.get("element_name")
            cavity = element_data.get("cavity", "")
            
            if not original_element_name:
                original_element_name = self.extract_element_name(element_key)
            
            # Match exact filename format from SPCChartManager
            if cavity and str(cavity).strip():
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}_{cavity}.png"
            else:
                filename = f"{chart_type}_{self.batch_number}_{original_element_name}.png"
            
            chart_path = self.charts_path / filename
            
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
                     methodology: str = "CMM",
                     facility: str = "",
                     dimension_class: str = "CC") -> str:
        """
        Create the complete professional Excel SPC report
        Suitable for automotive industry clients (VW, Mercedes, BMW, Tesla, etc.)
        """
        try:
            if not self.load_data():
                raise ValueError("Failed to load SPC data")
            
            self.workbook = Workbook()
            
            # Remove default sheet
            if 'Sheet' in self.workbook.sheetnames:
                self.workbook.remove(self.workbook['Sheet'])
            
            self.create_professional_styles()
            
            # Create executive summary sheet first
            self.create_executive_summary_sheet()
            
            # Create detailed sheets for each element
            sheets_created = 0
            for element_key, element_data in self.elements_data.items():
                try:
                    # Create clean sheet name (Excel limitation: 31 characters max)
                    sheet_name = element_key[:31] if len(element_key) > 31 else element_key
                    # Remove invalid characters
                    invalid_chars = ['/', '\\', '[', ']', '*', '?', ':']
                    for char in invalid_chars:
                        sheet_name = sheet_name.replace(char, '_')
                    
                    ws = self.workbook.create_sheet(title=sheet_name)
                    
                    # Create professional element report
                    self.create_professional_element_report(
                        ws, element_key, element_data,
                        part_description, drawing_number, 
                        methodology, facility, dimension_class
                    )
                    
                    sheets_created += 1
                    self.logger.info(f"✓ Created professional sheet for element: {element_key}")
                    
                except Exception as e:
                    self.logger.error(f"✗ Failed to create sheet for element {element_key}: {e}")
                    continue
            
            if sheets_created == 0:
                raise ValueError("No sheets were created successfully")
            
            # Save the workbook with professional naming
            filename = f"{self.client}_{self.ref_project}_{self.batch_number}_SPC_Analysis_Report.xlsx"
            output_file = self.output_path / filename
            
            self.workbook.save(output_file)
            self.logger.info(f"✅ Professional automotive SPC report created: {output_file}")
            self.logger.info(f"📊 Report contains: 1 executive summary + {sheets_created} detailed element sheets")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating professional Excel report: {e}")
            raise

    def create_professional_element_report(self, 
                                         ws: Worksheet, 
                                         element_key: str, 
                                         element_data: Dict[str, Any],
                                         part_description: str,
                                         drawing_number: str,
                                         methodology: str,
                                         facility: str,
                                         dimension_class: str):
        """Create a professional automotive industry report for one element"""
        
        current_row = 1
        
        # Page 1: Header, Statistical Table, and First Two Charts
        current_row = self.create_professional_header(
            ws, current_row, element_key, part_description,
            drawing_number, methodology, facility, dimension_class, element_data
        )
        
        current_row = self.create_statistical_summary_table(ws, current_row, element_data)
        
        # First page charts: Normality and Capability
        current_row = self.create_first_page_charts(ws, current_row, element_key)
        
        # Page break preparation
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToHeight = False
        ws.page_setup.fitToWidth = 1
        
        # Page 2: Individual and MR charts, Extrapolation, Notes, and Signature
        current_row = self.create_second_page_charts(ws, current_row, element_key)
        
        current_row = self.create_notes_and_signature_section(ws, current_row)
        
        # Apply professional page formatting
        self.setup_professional_page_formatting(ws)

    def create_professional_header(self, 
                                 ws: Worksheet, 
                                 start_row: int, 
                                 element_key: str,
                                 part_description: str,
                                 drawing_number: str,
                                 methodology: str,
                                 facility: str,
                                 dimension_class: str,
                                 element_data: Dict[str, Any]) -> int:
        """Create professional automotive industry header with improved borders"""
        
        current_row = start_row
        
        # Add company logo
        logo_path = Path("./assets/images/gui/logo_some.png")
        if logo_path.exists():
            try:
                img = Image(str(logo_path))
                img.width = 245  # 6.5cm * 37.8 pixels/cm
                img.height = 57   # 1.5cm * 37.8 pixels/cm
                ws.add_image(img, f'A{current_row}')
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")
                current_row += 1
        
        # Document title and subtitle
        ws.merge_cells(f'C{current_row}:H{current_row}')
        title_cell = ws[f'C{current_row}']
        title_cell.value = "STATISTICAL PROCESS CONTROL"
        title_cell.style = 'doc_title'
        ws.row_dimensions[current_row].height = 35  # Increased height for title
        
        current_row += 1
        ws.merge_cells(f'C{current_row}:H{current_row}')
        subtitle_cell = ws[f'C{current_row}']
        subtitle_cell.value = "Capability Analysis Report"
        subtitle_cell.style = 'doc_subtitle'
        ws.row_dimensions[current_row].height = 25  # Increased height for subtitle
        
        current_row += 2
        
        # Professional information table
        # Header row with increased height
        ws.merge_cells(f'A{current_row}:H{current_row}')
        header_cell = ws[f'A{current_row}']
        header_cell.value = "PART & PROJECT INFORMATION"
        header_cell.style = 'main_header'
        ws.row_dimensions[current_row].height = 35  # Increased height for main header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Information grid - 4 columns layout with improved element name
        clean_element_name = self.extract_element_name(element_key)
        cavity_info = element_data.get('cavity', 'N/A')
        
        info_data = [
            ["Client:", self.client, "Part Description:", part_description],
            ["Project Reference:", self.ref_project, "Drawing Number:", drawing_number],
            ["Batch Number:", self.batch_number, "Methodology:", methodology],
            ["Quality Facility:", facility, "Dimension Class:", dimension_class],
            ["Element Name:", clean_element_name, "Cavity:", cavity_info]
        ]
        
        for row_data in info_data:
            ws.row_dimensions[current_row].height = 25  # Consistent row height
            
            # Labels (columns A and E)
            ws[f'A{current_row}'].value = row_data[0]
            ws[f'A{current_row}'].style = 'param_label'
            ws[f'E{current_row}'].value = row_data[2]
            ws[f'E{current_row}'].style = 'param_label'
            
            # Values (columns B-D and F-H) with merged cells
            ws.merge_cells(f'B{current_row}:D{current_row}')
            ws[f'B{current_row}'].value = row_data[1]
            ws[f'B{current_row}'].style = 'data_cell'
            
            ws.merge_cells(f'F{current_row}:H{current_row}')
            ws[f'F{current_row}'].value = row_data[3]
            ws[f'F{current_row}'].style = 'data_cell'
            
            # Apply borders to merged ranges
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            
            current_row += 1
        
        current_row += 1
        return current_row

    def create_statistical_summary_table(self, 
                                        ws: Worksheet, 
                                        start_row: int, 
                                        element_data: Dict[str, Any]) -> int:
        """Create professional statistical summary table with improved formatting and borders"""
        
        current_row = start_row
        
        # Section header with larger row
        ws.merge_cells(f'A{current_row}:H{current_row}')
        section_cell = ws[f'A{current_row}']
        section_cell.value = "STATISTICAL ANALYSIS RESULTS"
        section_cell.style = 'section_header'
        ws.row_dimensions[current_row].height = 35  # Increased height for section header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Table headers with properly merged cells
        ws.row_dimensions[current_row].height = 30  # Increased height for table headers
        
        # Parameter columns (A and E)
        ws[f'A{current_row}'].value = "Parameter"
        ws[f'A{current_row}'].style = 'table_header'
        ws[f'E{current_row}'].value = "Parameter"
        ws[f'E{current_row}'].style = 'table_header'
        
        # Value columns (B-D and F-H) - properly merged
        ws.merge_cells(f'B{current_row}:D{current_row}')
        ws[f'B{current_row}'].value = "Value"
        ws[f'B{current_row}'].style = 'table_header'
        
        ws.merge_cells(f'F{current_row}:H{current_row}')
        ws[f'F{current_row}'].value = "Value"
        ws[f'F{current_row}'].style = 'table_header'
        
        # Apply borders to all header cells
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Statistical parameters in two columns with improved labels
        left_params = [
            ('sample_size', 'Sample Size (n)', ''),
            ('mean', 'Mean (X̄)', '.4f'),
            ('nominal', 'Nominal Target', '.4f'),
            ('std_short', 'Short-term Std Dev (s)', '.4f'),
            ('std_long', 'Long-term Std Dev (σ)', '.4f')
        ]
        
        right_params = [
            ('cp', 'CP', '.3f'),
            ('cpk', 'CPK', '.3f'),
            ('pp', 'PP', '.3f'),
            ('ppk', 'PPK', '.3f'),
            ('p_value', 'Normality p-value', '.4f')
        ]
        
        max_rows = max(len(left_params), len(right_params))
        
        for i in range(max_rows):
            ws.row_dimensions[current_row].height = 25  # Consistent row height
            
            # Left side
            if i < len(left_params):
                key, label, fmt = left_params[i]
                ws[f'A{current_row}'].value = label
                ws[f'A{current_row}'].style = 'param_label'
                
                value = element_data.get(key, 'N/A')
                if isinstance(value, (int, float)) and value != 'N/A' and fmt:
                    formatted_value = f"{value:{fmt}}"
                else:
                    formatted_value = str(value)
                
                ws.merge_cells(f'B{current_row}:D{current_row}')
                ws[f'B{current_row}'].value = formatted_value
                ws[f'B{current_row}'].style = 'data_cell'
            
            # Right side
            if i < len(right_params):
                key, label, fmt = right_params[i]
                ws[f'E{current_row}'].value = label
                ws[f'E{current_row}'].style = 'param_label'
                
                value = element_data.get(key, 'N/A')
                if isinstance(value, (int, float)) and value != 'N/A' and fmt:
                    formatted_value = f"{value:{fmt}}"
                else:
                    formatted_value = str(value)
                
                ws.merge_cells(f'F{current_row}:H{current_row}')
                ws[f'F{current_row}'].value = formatted_value
                ws[f'F{current_row}'].style = 'data_cell'
            
            # Apply borders to entire row
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
        
        current_row += 1
        return current_row

    def create_first_page_charts(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Create first page charts: Normality and Capability with proper centering and titles"""
        
        current_row = start_row
        
        # Charts section header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        charts_header = ws[f'A{current_row}']
        charts_header.value = "STATISTICAL CONTROL CHARTS"
        charts_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 35  # Increased height for section header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 2  # Add some spacing
        
        # Normality Analysis
        normality_path = self.get_chart_path(element_key, 'normality')
        if normality_path:
            # Chart title with increased height and borders
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = self.CHART_TYPES['normality']
            ws[f'A{current_row}'].style = 'chart_title'
            ws.row_dimensions[current_row].height = 30  # Increased height for chart titles
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
            
            # Add normality chart (centered)
            current_row = self.add_centered_chart(ws, normality_path, current_row, target_height=300)
        
        current_row += 3  # More spacing between charts
        
        # Capability Analysis
        capability_path = self.get_chart_path(element_key, 'capability')
        if capability_path:
            # Chart title with increased height and borders
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = self.CHART_TYPES['capability']
            ws[f'A{current_row}'].style = 'chart_title'
            ws.row_dimensions[current_row].height = 30  # Increased height for chart titles
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
            
            # Add capability chart (centered)
            current_row = self.add_centered_chart(ws, capability_path, current_row, target_height=300)
        
        return current_row

    def create_second_page_charts(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Create second page charts: Individual and MR side by side, Distribution with data table"""
        
        current_row = start_row + 5  # Page break spacing
        
        # Individual and MR charts side by side
        individuals_path = self.get_chart_path(element_key, 'individuals')
        mr_path = self.get_chart_path(element_key, 'moving_range')
        
        if individuals_path or mr_path:
            # Chart titles in same row with increased height and borders
            ws.row_dimensions[current_row].height = 30  # Increased height for chart titles
            
            if individuals_path:
                ws.merge_cells(f'A{current_row}:D{current_row}')
                ws[f'A{current_row}'].value = self.CHART_TYPES['individuals']
                ws[f'A{current_row}'].style = 'chart_title'
                self.apply_complete_borders_to_range(ws, f'A{current_row}', f'D{current_row}')
            
            if mr_path:
                ws.merge_cells(f'E{current_row}:H{current_row}')
                ws[f'E{current_row}'].value = self.CHART_TYPES['moving_range']
                ws[f'E{current_row}'].style = 'chart_title'
                self.apply_complete_borders_to_range(ws, f'E{current_row}', f'H{current_row}')
            
            current_row += 1
            
            # Add charts side by side with proper sizing
            chart_row = current_row
            if individuals_path:
                current_row = self.add_side_by_side_chart(ws, individuals_path, chart_row, 'left', target_height=250)
            
            if mr_path:
                self.add_side_by_side_chart(ws, mr_path, chart_row, 'right', target_height=250)
            
            current_row = chart_row + 22  # Space for charts
        
        current_row += 3  # Spacing
        
        # Distribution chart with data table
        extrapolation_path = self.get_chart_path(element_key, 'extrapolation')
        if extrapolation_path:
            # Chart title with increased height and borders
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = self.CHART_TYPES['extrapolation']
            ws[f'A{current_row}'].style = 'chart_title'
            ws.row_dimensions[current_row].height = 30  # Increased height for chart titles
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
            
            # Add distribution chart (centered)
            current_row = self.add_centered_chart(ws, extrapolation_path, current_row, target_height=300)
            
            # Add measurement values table
            current_row = self.add_measurement_values_table(ws, current_row, element_key)
        
        return current_row

    def add_centered_chart(self, ws: Worksheet, chart_path: Path, start_row: int, target_height: int = 300) -> int:
        """Add a chart centered in the worksheet"""
        try:
            img = Image(str(chart_path))
            
            # Resize chart to target height while maintaining aspect ratio
            height_ratio = target_height / img.height
            img.height = target_height
            img.width = int(img.width * height_ratio)
            
            # Calculate center position (assuming 8 columns A-H)
            total_width = 8 * 64  # Approximate column width in pixels
            chart_width = img.width
            offset_columns = max(0, (total_width - chart_width) // (2 * 64))
            
            # Place chart in calculated center position
            anchor_col = chr(65 + offset_columns) if offset_columns < 8 else 'A'
            ws.add_image(img, f'{anchor_col}{start_row}')
            
            # Return row after chart (approximate)
            rows_used = (target_height // 15) + 2  # Approximate rows per chart
            return start_row + rows_used
            
        except Exception as e:
            self.logger.error(f"Error adding centered chart: {e}")
            return start_row + 2

    def add_side_by_side_chart(self, ws: Worksheet, chart_path: Path, row: int, position: str, target_height: int = 250) -> int:
        """Add a chart positioned side by side (left or right)"""
        try:
            img = Image(str(chart_path))
            
            # Resize chart to target height while maintaining aspect ratio
            height_ratio = target_height / img.height
            img.height = target_height
            img.width = int(img.width * height_ratio)
            
            # Position based on left or right
            if position == 'left':
                anchor_col = 'A'
            else:  # right
                anchor_col = 'E'
            
            ws.add_image(img, f'{anchor_col}{row}')
            
            # Return row after chart (approximate)
            rows_used = (target_height // 15) + 2
            return row + rows_used
            
        except Exception as e:
            self.logger.error(f"Error adding side-by-side chart: {e}")
            return row + 2

    def add_measurement_values_table(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Add a professional table with measurement values"""
        
        current_row = start_row + 2
        
        element_data = self.elements_data.get(element_key, {})
        measurements = element_data.get('measurements', [])
        if not measurements:
            return current_row
        
        # Table header with increased height and borders
        ws.merge_cells(f'A{current_row}:H{current_row}')
        table_header = ws[f'A{current_row}']
        table_header.value = "ACTUAL MEASUREMENT VALUES"
        table_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 30  # Increased height for section header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Create table with 8 columns (A-H) to fit the layout
        num_columns = 8
        num_rows = (len(measurements) + num_columns - 1) // num_columns  # Ceiling division
        
        # Create table with measurements
        for row_idx in range(num_rows):
            ws.row_dimensions[current_row].height = 25  # Consistent row height
            
            for col_idx in range(num_columns):
                measurement_idx = row_idx * num_columns + col_idx
                col_letter = chr(65 + col_idx)  # A-H
                
                if measurement_idx < len(measurements):
                    value = measurements[measurement_idx]
                    ws[f'{col_letter}{current_row}'].value = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                else:
                    ws[f'{col_letter}{current_row}'].value = ""
                
                ws[f'{col_letter}{current_row}'].style = 'data_cell'
            
            # Apply borders to entire row
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
        
        return current_row

    def create_notes_and_signature_section(self, ws: Worksheet, start_row: int) -> int:
        """Create professional notes and signature section with improved formatting"""
        
        current_row = start_row + 2
        
        # Notes section with increased height and borders
        ws.merge_cells(f'A{current_row}:H{current_row}')
        notes_header = ws[f'A{current_row}']
        notes_header.value = "TECHNICAL NOTES & OBSERVATIONS"
        notes_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 30  # Increased height for section header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Notes area (4 rows high for writing space)
        for i in range(4):
            ws.row_dimensions[current_row + i].height = 25  # Consistent height for notes area
        
        ws.merge_cells(f'A{current_row}:H{current_row + 3}')
        notes_cell = ws[f'A{current_row}']
        notes_cell.value = ""  # Empty for manual notes
        notes_cell.style = 'notes_style'
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row + 3}')
        
        current_row += 5
        
        # Signature section with increased height and borders
        ws.merge_cells(f'A{current_row}:H{current_row}')
        signature_header = ws[f'A{current_row}']
        signature_header.value = "QUALITY APPROVAL"
        signature_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 30  # Increased height for section header
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        
        current_row += 1
        
        # Position and Date section
        ws.row_dimensions[current_row].height = 25  # Consistent row height
        ws[f'A{current_row}'].value = "Position:"
        ws[f'A{current_row}'].style = 'param_label'
        ws.merge_cells(f'B{current_row}:D{current_row}')
        ws[f'B{current_row}'].value = "Project Leader"
        ws[f'B{current_row}'].style = 'data_cell'
        
        ws[f'E{current_row}'].value = "Date:"
        ws[f'E{current_row}'].style = 'param_label'
        ws.merge_cells(f'F{current_row}:H{current_row}')
        ws[f'F{current_row}'].value = datetime.now().strftime("%d/%m/%Y")
        ws[f'F{current_row}'].style = 'data_cell'
        
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        current_row += 1
        
        # Name and Signature section
        ws.row_dimensions[current_row].height = 25  # Consistent row height
        ws[f'A{current_row}'].value = "Name:"
        ws[f'A{current_row}'].style = 'param_label'
        ws.merge_cells(f'B{current_row}:D{current_row}')
        ws[f'B{current_row}'].style = 'data_cell'
        
        ws[f'E{current_row}'].value = "Signature:"
        ws[f'E{current_row}'].style = 'param_label'
        ws.merge_cells(f'F{current_row}:H{current_row}')
        ws[f'F{current_row}'].style = 'data_cell'
        
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        current_row += 3
        
        return current_row

    def setup_professional_page_formatting(self, ws: Worksheet):
        """Setup professional page formatting for automotive industry standards"""
        
        # Set column widths for optimal layout
        column_widths = {
            'A': 18,  'B': 12,  'C': 12,  'D': 12,
            'E': 18,  'F': 12,  'G': 12,  'H': 12
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Page setup for A4 portrait
        ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        
        # Professional margins
        ws.page_margins = PageMargins(
            left=0.7, right=0.7, top=0.8, bottom=0.8,
            header=0.3, footer=0.3
        )
        
        # Center horizontally
        ws.page_setup.horizontalCentered = True
        
        # Fit to page settings
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = False
        
        # Print settings
        ws.print_options.horizontalCentered = True
        ws.print_options.gridLines = False
        ws.print_options.headings = False
        
        # Header and footer for professional appearance
        ws.oddHeader.center.text = f"&14&B{self.client} - {self.ref_project}"
        ws.oddHeader.right.text = f"&10Batch: {self.batch_number}"
        
        ws.oddFooter.left.text = "&9Generated: &D &T"
        ws.oddFooter.center.text = "&9Statistical Process Control Report"
        ws.oddFooter.right.text = "&9Page &P of &N"
        
        # Apply same header/footer to even pages
        ws.evenHeader.center.text = f"&14&B{self.client} - {self.ref_project}"
        ws.evenHeader.right.text = f"&10Batch: {self.batch_number}"
        
        ws.evenFooter.left.text = "&9Generated: &D &T"
        ws.evenFooter.center.text = "&9Statistical Process Control Report"
        ws.evenFooter.right.text = "&9Page &P of &N"

    def get_capability_status_color(self, cpk_value: float) -> str:
        """Get color code based on capability index value"""
        if cpk_value >= 1.67:  # Excellent
            return self.COLORS['success_green']
        elif cpk_value >= 1.33:  # Acceptable
            return self.COLORS['warning_orange']
        else:  # Needs improvement
            return self.COLORS['danger_red']

    def create_executive_summary_sheet(self) -> None:
        """Create an improved executive summary cover sheet"""
        
        try:
            # Create summary sheet as first sheet
            summary_ws = self.workbook.create_sheet(title="Executive Summary", index=0)
            
            current_row = 1
            
            # Add company logo centered
            logo_path = Path("./assets/images/gui/logo_some.png")
            if logo_path.exists():
                try:
                    img = Image(str(logo_path))
                    img.width = 350  # Larger for cover page
                    img.height = 82   # Maintain aspect ratio
                    
                    # Center the logo
                    summary_ws.add_image(img, 'D1')  # Center position
                    current_row += 8  # More space after logo
                except Exception as e:
                    self.logger.warning(f"Could not add logo: {e}")
                    current_row += 1
            
            # Enhanced title section
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            title_cell = summary_ws[f'A{current_row}']
            title_cell.value = "STATISTICAL PROCESS CONTROL"
            title_cell.font = Font(name='Arial', size=28, bold=True, color=self.COLORS['primary_blue'])
            title_cell.alignment = Alignment(horizontal='center', vertical='center')
            summary_ws.row_dimensions[current_row].height = 45  # Large title height
            
            current_row += 1
            
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            subtitle_cell = summary_ws[f'A{current_row}']
            subtitle_cell.value = "COMPREHENSIVE ANALYSIS REPORT"
            subtitle_cell.font = Font(name='Arial', size=16, bold=True, color=self.COLORS['secondary_blue'])
            subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
            summary_ws.row_dimensions[current_row].height = 30
            
            current_row += 1
            
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            project_cell = summary_ws[f'A{current_row}']
            project_cell.value = f"{self.client} - {self.ref_project} - Batch {self.batch_number}"
            project_cell.font = Font(name='Arial', size=14, color=self.COLORS['dark_gray'])
            project_cell.alignment = Alignment(horizontal='center', vertical='center')
            summary_ws.row_dimensions[current_row].height = 25
            
            current_row += 4  # More spacing
            
            # Enhanced capability visualization
            current_row = self.create_enhanced_capability_visualization(summary_ws, current_row)
            current_row += 3
            
            # Enhanced project information section
            current_row = self.create_enhanced_project_info(summary_ws, current_row)
            current_row += 3
            
            # Enhanced elements summary table
            current_row = self.create_enhanced_elements_summary(summary_ws, current_row)
            
            # Set column widths for cover page
            column_widths = {
                'A': 25, 'B': 12, 'C': 12, 'D': 12, 'E': 12,
                'F': 12, 'G': 12, 'H': 12, 'I': 12, 'J': 15
            }
            for col, width in column_widths.items():
                summary_ws.column_dimensions[col].width = width
            
            # Setup page formatting
            self.setup_professional_page_formatting(summary_ws)
            
            self.logger.info("Created enhanced executive summary sheet")
            
        except Exception as e:
            self.logger.error(f"Error creating executive summary: {e}")

    def create_enhanced_capability_visualization(self, ws: Worksheet, start_row: int) -> int:
        """Create an enhanced capability status visualization"""
        
        current_row = start_row
        
        # Section header
        ws.merge_cells(f'A{current_row}:J{current_row}')
        vis_header = ws[f'A{current_row}']
        vis_header.value = "PROCESS CAPABILITY OVERVIEW"
        vis_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 35
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
        
        current_row += 1
        
        # Count capability statuses
        status_counts = {
            "Excellent (CPK ≥ 1.67)": 0,
            "Acceptable (1.33 ≤ CPK < 1.67)": 0,
            "Inadequate (CPK < 1.33)": 0,
            "N/A": 0
        }
        
        for element_data in self.elements_data.values():
            cpk = element_data.get('cpk', 0)
            if isinstance(cpk, (int, float)):
                if cpk >= 1.67:
                    status_counts["Excellent (CPK ≥ 1.67)"] += 1
                elif cpk >= 1.33:
                    status_counts["Acceptable (1.33 ≤ CPK < 1.67)"] += 1
                else:
                    status_counts["Inadequate (CPK < 1.33)"] += 1
            else:
                status_counts["N/A"] += 1
        
        # Enhanced visualization table
        ws.row_dimensions[current_row].height = 30
        headers = ["Capability Status", "Count", "Percentage", "Quality Level"]
        
        for col, header in enumerate(headers):
            start_col = col * 2 + 1  # A, C, E, G
            end_col = start_col + 1   # B, D, F, H
            ws.merge_cells(start_row=current_row, start_column=start_col, 
                          end_row=current_row, end_column=end_col)
            cell = ws.cell(row=current_row, column=start_col)
            cell.value = header
            cell.style = 'table_header'
        
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
        current_row += 1
        
        # Data rows with enhanced formatting
        colors = {
            "Excellent (CPK ≥ 1.67)": self.COLORS['success_green'],
            "Acceptable (1.33 ≤ CPK < 1.67)": self.COLORS['warning_orange'],
            "Inadequate (CPK < 1.33)": self.COLORS['danger_red'],
            "N/A": self.COLORS['medium_gray']
        }
        
        quality_levels = {
            "Excellent (CPK ≥ 1.67)": "World Class",
            "Acceptable (1.33 ≤ CPK < 1.67)": "Industry Standard",
            "Inadequate (CPK < 1.33)": "Needs Improvement",
            "N/A": "Insufficient Data"
        }
        
        total_elements = len(self.elements_data)
        
        for status, count in status_counts.items():
            if count == 0:
                continue
            
            ws.row_dimensions[current_row].height = 28
            
            # Status name
            ws.merge_cells(f'A{current_row}:B{current_row}')
            cell = ws[f'A{current_row}']
            cell.value = status
            cell.style = 'param_label'
            
            # Count
            ws.merge_cells(f'C{current_row}:D{current_row}')
            cell = ws[f'C{current_row}']
            cell.value = count
            cell.style = 'data_cell'
            cell.font = Font(name='Arial', size=10, bold=True)
            
            # Percentage
            ws.merge_cells(f'E{current_row}:F{current_row}')
            cell = ws[f'E{current_row}']
            percentage = (count / total_elements) * 100
            cell.value = f"{percentage:.1f}%"
            cell.style = 'data_cell'
            cell.font = Font(name='Arial', size=10, bold=True)
            
            # Quality level
            ws.merge_cells(f'G{current_row}:H{current_row}')
            cell = ws[f'G{current_row}']
            cell.value = quality_levels[status]
            cell.style = 'data_cell'
            cell.fill = PatternFill(start_color=colors[status], 
                                   end_color=colors[status], 
                                   fill_type='solid')
            if colors[status] == self.COLORS['danger_red']:
                cell.font = Font(name='Arial', size=9, bold=True, color='FFFFFF')
            else:
                cell.font = Font(name='Arial', size=9, bold=True)
            
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'H{current_row}')
            current_row += 1
        
        return current_row

    def create_enhanced_project_info(self, ws: Worksheet, start_row: int) -> int:
        """Create enhanced project information section"""
        
        current_row = start_row
        
        # Section header
        ws.merge_cells(f'A{current_row}:J{current_row}')
        info_header = ws[f'A{current_row}']
        info_header.value = "PROJECT INFORMATION"
        info_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 35
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
        
        current_row += 1
        
        # Enhanced project details with better layout
        project_info = [
            ["Client:", self.client, "Elements Analyzed:", str(len(self.elements_data))],
            ["Project Reference:", self.ref_project, "Report Generated:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Batch Number:", self.batch_number, "Software Version:", "SPC Professional v2.0"],
            ["Analysis Date:", datetime.now().strftime("%d/%m/%Y"), "Quality Standard:", "Automotive PPAP"]
        ]
        
        for info_row in project_info:
            ws.row_dimensions[current_row].height = 28
            
            # Left side
            ws[f'A{current_row}'].value = info_row[0]
            ws[f'A{current_row}'].style = 'param_label'
            ws.merge_cells(f'B{current_row}:E{current_row}')
            ws[f'B{current_row}'].value = info_row[1]
            ws[f'B{current_row}'].style = 'data_cell'
            ws[f'B{current_row}'].font = Font(name='Arial', size=10)
            
            # Right side
            ws[f'F{current_row}'].value = info_row[2]
            ws[f'F{current_row}'].style = 'param_label'
            ws.merge_cells(f'G{current_row}:J{current_row}')
            ws[f'G{current_row}'].value = info_row[3]
            ws[f'G{current_row}'].style = 'data_cell'
            ws[f'G{current_row}'].font = Font(name='Arial', size=10)
            
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
            current_row += 1
        
        return current_row

    def create_enhanced_elements_summary(self, ws: Worksheet, start_row: int) -> int:
        """Create enhanced elements summary table"""
        
        current_row = start_row
        
        # Section header
        ws.merge_cells(f'A{current_row}:J{current_row}')
        table_header = ws[f'A{current_row}']
        table_header.value = "DETAILED ELEMENTS ANALYSIS SUMMARY"
        table_header.style = 'section_header'
        ws.row_dimensions[current_row].height = 35
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
        
        current_row += 1
        
        # Enhanced table headers
        headers = [
            "Element", "Cavity", "Mean", "CP", "CPK", 
            "Short σ", "PP", "PPK", "Long σ", "Status"
        ]
        
        ws.row_dimensions[current_row].height = 30
        for i, header in enumerate(headers):
            col = chr(65 + i)  # A, B, C, etc.
            ws[f'{col}{current_row}'].value = header
            ws[f'{col}{current_row}'].style = 'table_header'
            ws[f'{col}{current_row}'].font = Font(name='Arial', size=10, bold=True)
        
        self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
        current_row += 1
        
        # Enhanced element data rows
        for element_key, element_data in self.elements_data.items():
            ws.row_dimensions[current_row].height = 25
            
            # Clean element name and cavity
            clean_name = self.extract_element_name(element_key)
            ws[f'A{current_row}'].value = clean_name
            ws[f'A{current_row}'].style = 'data_cell'
            ws[f'A{current_row}'].font = Font(name='Arial', size=9)
            
            ws[f'B{current_row}'].value = element_data.get('cavity', 'N/A')
            ws[f'B{current_row}'].style = 'data_cell'
            
            # Statistical values with improved formatting
            params = [
                ('mean', 'C', '.4f'),
                ('cp', 'D', '.3f'),
                ('cpk', 'E', '.3f'),
                ('std_short', 'F', '.4f'),
                ('pp', 'G', '.3f'),
                ('ppk', 'H', '.3f'),
                ('std_long', 'I', '.4f')
            ]
            
            for param, col, fmt in params:
                value = element_data.get(param, 'N/A')
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:{fmt}}"
                else:
                    formatted_value = str(value)
                
                ws[f'{col}{current_row}'].value = formatted_value
                ws[f'{col}{current_row}'].style = 'data_cell'
            
            # Enhanced status with color coding
            cpk = element_data.get('cpk', 0)
            if isinstance(cpk, (int, float)):
                if cpk >= 1.67:
                    status = "Excellent"
                    color = self.COLORS['success_green']
                    font_color = self.COLORS['dark_gray']
                elif cpk >= 1.33:
                    status = "Acceptable"
                    color = self.COLORS['warning_orange']
                    font_color = 'FFFFFF'
                else:
                    status = "Inadequate"
                    color = self.COLORS['danger_red']
                    font_color = 'FFFFFF'
            else:
                status = "N/A"
                color = self.COLORS['medium_gray']
                font_color = self.COLORS['dark_gray']
            
            status_cell = ws[f'J{current_row}']
            status_cell.value = status
            status_cell.style = 'data_cell'
            status_cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
            status_cell.font = Font(name='Arial', size=9, bold=True, color=font_color)
            
            self.apply_complete_borders_to_range(ws, f'A{current_row}', f'J{current_row}')
            current_row += 1
        
        return current_row