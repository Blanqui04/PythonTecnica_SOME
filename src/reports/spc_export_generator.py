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
from openpyxl.worksheet.header_footer import HeaderFooter

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
        'normality': 'Normality Analysis',
        'capability': 'Process Capability Analysis',
        'individuals': 'Individual Values Control Chart (I-Chart)',
        'moving_range': 'Moving Range Control Chart (MR-Chart)',
        'extrapolation': 'Distribution Analysis'
    }
    
    # Statistical parameters with professional descriptions
    STATISTICAL_PARAMETERS = {
        'sample_size': 'Sample Size (n)',
        'mean': 'Process Mean (X̄)',
        'nominal': 'Nominal Target',
        'std_short': 'Short-term Std Dev (σ)',
        'std_long': 'Long-term Std Dev (σ)', 
        'cp': 'Process Capability (Cp)',
        'cpk': 'Process Capability Index (Cpk)',
        'pp': 'Process Performance (Pp)',
        'ppk': 'Process Performance Index (Ppk)',
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
        """Create professional automotive industry styles"""
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
        
        # Main header style (company info)
        main_header = NamedStyle(name="main_header")
        main_header.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        main_header.fill = PatternFill(start_color=self.COLORS['primary_blue'], 
                                     end_color=self.COLORS['primary_blue'], 
                                     fill_type='solid')
        main_header.alignment = Alignment(horizontal='center', vertical='center')
        main_header.border = Border(
            left=Side(style='medium', color=self.COLORS['primary_blue']),
            right=Side(style='medium', color=self.COLORS['primary_blue']),
            top=Side(style='medium', color=self.COLORS['primary_blue']),
            bottom=Side(style='medium', color=self.COLORS['primary_blue'])
        )
        
        # Section header style
        section_header = NamedStyle(name="section_header")
        section_header.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        section_header.fill = PatternFill(start_color=self.COLORS['secondary_blue'], 
                                        end_color=self.COLORS['secondary_blue'], 
                                        fill_type='solid')
        section_header.alignment = Alignment(horizontal='center', vertical='center')
        section_header.border = Border(
            left=Side(style='thin', color=self.COLORS['medium_gray']),
            right=Side(style='thin', color=self.COLORS['medium_gray']),
            top=Side(style='thin', color=self.COLORS['medium_gray']),
            bottom=Side(style='thin', color=self.COLORS['medium_gray'])
        )
        
        # Table header style
        table_header = NamedStyle(name="table_header")
        table_header.font = Font(name='Arial', size=9, bold=True, color=self.COLORS['dark_gray'])
        table_header.fill = PatternFill(start_color=self.COLORS['table_header'], 
                                      end_color=self.COLORS['table_header'], 
                                      fill_type='solid')
        table_header.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        table_header.border = Border(
            left=Side(style='thin', color=self.COLORS['medium_gray']),
            right=Side(style='thin', color=self.COLORS['medium_gray']),
            top=Side(style='thin', color=self.COLORS['medium_gray']),
            bottom=Side(style='thin', color=self.COLORS['medium_gray'])
        )
        
        # Parameter label style
        param_label = NamedStyle(name="param_label")
        param_label.font = Font(name='Arial', size=9, bold=True, color=self.COLORS['dark_gray'])
        param_label.fill = PatternFill(start_color=self.COLORS['light_gray'], 
                                     end_color=self.COLORS['light_gray'], 
                                     fill_type='solid')
        param_label.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        param_label.border = Border(
            left=Side(style='thin', color=self.COLORS['medium_gray']),
            right=Side(style='thin', color=self.COLORS['medium_gray']),
            top=Side(style='thin', color=self.COLORS['medium_gray']),
            bottom=Side(style='thin', color=self.COLORS['medium_gray'])
        )
        
        # Data cell style
        data_cell = NamedStyle(name="data_cell")
        data_cell.font = Font(name='Arial', size=9, color=self.COLORS['dark_gray'])
        data_cell.alignment = Alignment(horizontal='center', vertical='center')
        data_cell.border = Border(
            left=Side(style='thin', color=self.COLORS['medium_gray']),
            right=Side(style='thin', color=self.COLORS['medium_gray']),
            top=Side(style='thin', color=self.COLORS['medium_gray']),
            bottom=Side(style='thin', color=self.COLORS['medium_gray'])
        )
        
        # Chart title style
        chart_title = NamedStyle(name="chart_title")
        chart_title.font = Font(name='Arial', size=11, bold=True, color=self.COLORS['secondary_blue'])
        chart_title.alignment = Alignment(horizontal='center', vertical='center')
        
        # Notes style
        notes_style = NamedStyle(name="notes_style")
        notes_style.font = Font(name='Arial', size=9, color=self.COLORS['dark_gray'])
        notes_style.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        notes_style.border = Border(
            left=Side(style='thin', color=self.COLORS['medium_gray']),
            right=Side(style='thin', color=self.COLORS['medium_gray']),
            top=Side(style='thin', color=self.COLORS['medium_gray']),
            bottom=Side(style='thin', color=self.COLORS['medium_gray'])
        )
        
        # Add all styles to workbook
        try:
            styles_to_add = [
                doc_title, doc_subtitle, main_header, section_header,
                table_header, param_label, data_cell, chart_title, notes_style
            ]
            
            for style in styles_to_add:
                self.workbook.add_named_style(style)
            
            self.styles_created = True
            self.logger.debug("Created all professional Excel styles")
            
        except Exception as e:
            self.logger.error(f"Error creating styles: {e}")

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
                if " Cavity " in element_key:
                    original_element_name = element_key.split(" Cavity ")[0]
                elif "_cavity_" in element_key:
                    original_element_name = element_key.split("_cavity_")[0]
                else:
                    original_element_name = element_key
            
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
        
        # First page charts: Normality and Capability side by side
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
        """Create professional automotive industry header"""
        
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
        
        current_row += 1
        ws.merge_cells(f'C{current_row}:H{current_row}')
        subtitle_cell = ws[f'C{current_row}']
        subtitle_cell.value = "Capability Analysis Report"
        subtitle_cell.style = 'doc_subtitle'
        
        current_row += 2
        
        # Professional information table
        # Header row
        ws.merge_cells(f'A{current_row}:H{current_row}')
        header_cell = ws[f'A{current_row}']
        header_cell.value = "PART & PROJECT INFORMATION"
        header_cell.style = 'main_header'
        
        current_row += 1
        
        # Information grid - 4 columns layout
        info_data = [
            ["Client:", self.client, "Part Description:", part_description],
            ["Project Reference:", self.ref_project, "Drawing Number:", drawing_number],
            ["Batch Number:", self.batch_number, "Methodology:", methodology],
            ["Quality Facility:", facility, "Dimension Class:", dimension_class],
            ["Element Name:", element_key, "Cavity:", element_data.get('cavity', 'N/A')]
        ]
        
        for row_data in info_data:
            # Labels (columns A and E)
            ws[f'A{current_row}'].value = row_data[0]
            ws[f'A{current_row}'].style = 'param_label'
            ws[f'E{current_row}'].value = row_data[2]
            ws[f'E{current_row}'].style = 'param_label'
            
            # Values (columns B-D and F-H)
            ws.merge_cells(f'B{current_row}:D{current_row}')
            ws[f'B{current_row}'].value = row_data[1]
            ws[f'B{current_row}'].style = 'data_cell'
            
            ws.merge_cells(f'F{current_row}:H{current_row}')
            ws[f'F{current_row}'].value = row_data[3]
            ws[f'F{current_row}'].style = 'data_cell'
            
            current_row += 1
        
        current_row += 1
        return current_row

    def create_statistical_summary_table(self, 
                                        ws: Worksheet, 
                                        start_row: int, 
                                        element_data: Dict[str, Any]) -> int:
        """Create professional statistical summary table"""
        
        current_row = start_row
        
        # Section header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        section_cell = ws[f'A{current_row}']
        section_cell.value = "STATISTICAL ANALYSIS RESULTS"
        section_cell.style = 'section_header'
        
        current_row += 1
        
        # Table headers
        headers = ["Parameter", "Value", "Parameter", "Value"]
        for i, header in enumerate(headers):
            col_letter = chr(65 + i * 2)  # A, C, E, G
            if i in [1, 3]:  # Value columns
                ws.merge_cells(f'{col_letter}{current_row}:{chr(ord(col_letter) + 1)}{current_row}')
            ws[f'{col_letter}{current_row}'].value = header
            ws[f'{col_letter}{current_row}'].style = 'table_header'
        
        current_row += 1
        
        # Statistical parameters in two columns
        left_params = [
            ('sample_size', 'Sample Size (n)', ''),
            ('mean', 'Process Mean (X̄)', '.4f'),
            ('nominal', 'Nominal Target', '.4f'),
            ('std_short', 'Short-term Std Dev (σ)', '.4f'),
            ('std_long', 'Long-term Std Dev (σ)', '.4f')
        ]
        
        right_params = [
            ('cp', 'Process Capability (Cp)', '.3f'),
            ('cpk', 'Process Capability Index (Cpk)', '.3f'),
            ('pp', 'Process Performance (Pp)', '.3f'),
            ('ppk', 'Process Performance Index (Ppk)', '.3f'),
            ('p_value', 'Normality p-value', '.4f')
        ]
        
        max_rows = max(len(left_params), len(right_params))
        
        for i in range(max_rows):
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
                
                ws.merge_cells(f'B{current_row}:C{current_row}')
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
            
            current_row += 1
        
        current_row += 1
        return current_row

    def create_first_page_charts(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Create first page charts: Normality and Capability stacked vertically"""
        
        current_row = start_row
        
        # Charts section header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        charts_header = ws[f'A{current_row}']
        charts_header.value = "STATISTICAL CONTROL CHARTS"
        charts_header.style = 'section_header'
        
        current_row += 1
        
        # Normality Analysis (top)
        normality_path = self.get_chart_path(element_key, 'normality')
        if normality_path:
            # Normality chart title
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = "NORMALITY ANALYSIS"
            ws[f'A{current_row}'].style = 'chart_title'
            current_row += 1
            
            # Add normality chart (centered, controlled height ~10cm/378px)
            try:
                img = Image(str(normality_path))
                # Maintain aspect ratio while controlling height
                target_height = 200  # ~7cm (balance between visibility and space)
                height_ratio = target_height / img.height
                img.height = target_height
                img.width = int(img.width * height_ratio)
                
                # Center the image by calculating column offset
                col_offset = max(0, (8 - (img.width // 64)) // 2)  # Approximate column calculation
                anchor_col = chr(65 + col_offset)  # A, B, etc.
                
                ws.add_image(img, f'{anchor_col}{current_row}')
                current_row += 15  # Approximate row height for chart
            except Exception as e:
                self.logger.error(f"Error adding normality chart: {e}")
                current_row += 2
        
        current_row += 2  # Spacing between charts
        
        # Capability Analysis (bottom)
        capability_path = self.get_chart_path(element_key, 'capability')
        if capability_path:
            # Capability chart title
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = "PROCESS CAPABILITY"
            ws[f'A{current_row}'].style = 'chart_title'
            current_row += 1
            
            # Add capability chart (centered, controlled height)
            try:
                img = Image(str(capability_path))
                target_height = 200  # ~7cm
                height_ratio = target_height / img.height
                img.height = target_height
                img.width = int(img.width * height_ratio)
                
                col_offset = max(0, (8 - (img.width // 64)) // 2)
                anchor_col = chr(65 + col_offset)
                
                ws.add_image(img, f'{anchor_col}{current_row}')
                current_row += 15  # Approximate row height for chart
            except Exception as e:
                self.logger.error(f"Error adding capability chart: {e}")
                current_row += 2
        
        return current_row

    def create_second_page_charts(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Create second page charts: Individual and MR side by side, Extrapolation below"""
        
        current_row = start_row
        
        # Force page break by setting row height for spacing
        current_row += 5  # Add some spacing for page break
        
        # Individual and MR charts side by side
        individuals_path = self.get_chart_path(element_key, 'individuals')
        mr_path = self.get_chart_path(element_key, 'moving_range')
        
        if individuals_path or mr_path:
            # Chart titles in same row
            if individuals_path:
                ws.merge_cells(f'A{current_row}:D{current_row}')
                ws[f'A{current_row}'].value = "I-CHART (INDIVIDUALS)"
                ws[f'A{current_row}'].style = 'chart_title'
            
            if mr_path:
                ws.merge_cells(f'E{current_row}:H{current_row}')
                ws[f'E{current_row}'].value = "MR-CHART (MOVING RANGE)"
                ws[f'E{current_row}'].style = 'chart_title'
            
            current_row += 1
            
            # Add charts (controlled height ~10cm/378px)
            if individuals_path:
                try:
                    img = Image(str(individuals_path))
                    target_height = 200  # ~7cm
                    height_ratio = target_height / img.height
                    img.height = target_height
                    img.width = int(img.width * height_ratio)
                    
                    ws.add_image(img, f'A{current_row}')
                except Exception as e:
                    self.logger.error(f"Error adding individual chart: {e}")
            
            if mr_path:
                try:
                    img = Image(str(mr_path))
                    target_height = 200  # ~7cm
                    height_ratio = target_height / img.height
                    img.height = target_height
                    img.width = int(img.width * height_ratio)
                    
                    ws.add_image(img, f'E{current_row}')
                except Exception as e:
                    self.logger.error(f"Error adding MR chart: {e}")
            
            current_row += 15  # Approximate row height for charts
        
        current_row += 2  # Spacing
        
        # Extrapolation chart (full width, if exists)
        extrapolation_path = self.get_chart_path(element_key, 'extrapolation')
        if extrapolation_path:
            ws.merge_cells(f'A{current_row}:H{current_row}')
            ws[f'A{current_row}'].value = "DISTRIBUTION ANALYSIS"
            ws[f'A{current_row}'].style = 'chart_title'
            
            current_row += 1
            
            try:
                img = Image(str(extrapolation_path))
                target_height = 200  # ~7cm
                height_ratio = target_height / img.height
                img.height = target_height
                img.width = int(img.width * height_ratio)
                
                # Center the image
                col_offset = max(0, (8 - (img.width // 64)) // 2)
                anchor_col = chr(65 + col_offset)
                
                ws.add_image(img, f'{anchor_col}{current_row}')
                current_row += 15  # Approximate row height
                
                # Add actual values table below the chart
                current_row = self.add_extrapolation_data_table(ws, current_row, element_key)
                
            except Exception as e:
                self.logger.error(f"Error adding extrapolation chart: {e}")
                current_row += 2
        
        return current_row

    def add_extrapolation_data_table(self, ws: Worksheet, start_row: int, element_key: str) -> int:
        """Add a table with the actual values used in extrapolation analysis"""
        
        current_row = start_row + 2
        
        element_data = self.elements_data.get(element_key, {})
        measurements = element_data.get('measurements', [])
        if not measurements:
            return current_row
        
        # Table header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        table_header = ws[f'A{current_row}']
        table_header.value = "ACTUAL MEASUREMENT VALUES"
        table_header.style = 'section_header'
        
        current_row += 1
        
        # Determine how many columns we need (10 values per row)
        num_columns = 10
        num_rows = (len(measurements) // num_columns) + (1 if len(measurements) % num_columns else 0)
        
        # Create table with 10 columns
        for row_idx in range(num_rows):
            for col_idx in range(num_columns):
                measurement_idx = row_idx * num_columns + col_idx
                if measurement_idx < len(measurements):
                    value = measurements[measurement_idx]
                    col_letter = chr(65 + col_idx)  # A-J
                    ws[f'{col_letter}{current_row}'].value = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                    ws[f'{col_letter}{current_row}'].style = 'data_cell'
                    ws[f'{col_letter}{current_row}'].border = Border(
                        left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))
                else:
                    # Empty cell with border
                    col_letter = chr(65 + col_idx)
                    ws[f'{col_letter}{current_row}'].value = ""
                    ws[f'{col_letter}{current_row}'].style = 'data_cell'
                    ws[f'{col_letter}{current_row}'].border = Border(
                        left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))
            
            current_row += 1
        
        return current_row

    def create_notes_and_signature_section(self, ws: Worksheet, start_row: int) -> int:
        """Create professional notes and signature section with updated labels"""
        
        current_row = start_row + 2
        
        # Notes section
        ws.merge_cells(f'A{current_row}:H{current_row}')
        notes_header = ws[f'A{current_row}']
        notes_header.value = "TECHNICAL NOTES & OBSERVATIONS"
        notes_header.style = 'section_header'
        
        current_row += 1
        
        # Notes area (4 rows high for writing space)
        ws.merge_cells(f'A{current_row}:H{current_row + 3}')
        notes_cell = ws[f'A{current_row}']
        notes_cell.value = ""  # Empty for manual notes
        notes_cell.style = 'notes_style'
        
        current_row += 5
        
        # Signature section
        ws.merge_cells(f'A{current_row}:H{current_row}')
        signature_header = ws[f'A{current_row}']
        signature_header.value = "QUALITY APPROVAL"
        signature_header.style = 'section_header'
        
        current_row += 1
        
        # Position section
        ws[f'A{current_row}'].value = "Position:"
        ws[f'A{current_row}'].style = 'param_label'
        ws.merge_cells(f'B{current_row}:D{current_row}')
        ws[f'B{current_row}'].value = "Project Leader"
        ws[f'B{current_row}'].style = 'data_cell'
        
        # Date section
        ws[f'E{current_row}'].value = "Date:"
        ws[f'E{current_row}'].style = 'param_label'
        ws.merge_cells(f'F{current_row}:H{current_row}')
        ws[f'F{current_row}'].value = datetime.now().strftime("%d/%m/%Y")
        ws[f'F{current_row}'].style = 'data_cell'
        
        current_row += 1
        
        # Name field
        ws[f'A{current_row}'].value = "Name:"
        ws[f'A{current_row}'].style = 'param_label'
        ws.merge_cells(f'B{current_row}:D{current_row}')
        ws[f'B{current_row}'].style = 'data_cell'
        
        # Signature field
        ws[f'E{current_row}'].value = "Signature:"
        ws[f'E{current_row}'].style = 'param_label'
        ws.merge_cells(f'F{current_row}:H{current_row}')
        ws[f'F{current_row}'].style = 'data_cell'
        
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

    def add_professional_chart_with_error_handling(self, 
                                                  ws: Worksheet, 
                                                  chart_path: Path, 
                                                  anchor_cell: str,
                                                  width: int = 300,
                                                  title: str = "") -> bool:
        """
        Add a chart with professional error handling and sizing
        
        Returns:
            bool: True if chart was added successfully, False otherwise
        """
        try:
            if not chart_path or not chart_path.exists():
                # Add placeholder for missing chart
                ws[anchor_cell].value = f"Chart not available: {title}"
                ws[anchor_cell].style = 'param_label'
                return False
            
            img = Image(str(chart_path))
            
            # Professional sizing with aspect ratio preservation
            if img.width > width:
                ratio = width / img.width
                img.width = width
                img.height = int(img.height * ratio)
            
            # Ensure reasonable height limits
            if img.height > 250:
                ratio = 250 / img.height
                img.height = 250
                img.width = int(img.width * ratio)
            
            ws.add_image(img, anchor_cell)
            self.logger.debug(f"Successfully added chart: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding chart {title}: {e}")
            # Add error message in cell
            ws[anchor_cell].value = f"Error loading chart: {title}"
            ws[anchor_cell].style = 'param_label'
            return False

    def get_capability_status_color(self, cpk_value: float) -> str:
        """
        Get color code based on capability index value
        Following automotive industry standards
        """
        if cpk_value >= 1.67:  # Excellent
            return self.COLORS['success_green']
        elif cpk_value >= 1.33:  # Acceptable
            return self.COLORS['warning_orange']
        else:  # Needs improvement
            return self.COLORS['danger_red']

    def add_capability_interpretation(self, 
                                    ws: Worksheet, 
                                    start_row: int, 
                                    element_data: Dict[str, Any]) -> int:
        """Add capability interpretation section for automotive standards"""
        
        current_row = start_row
        
        # Capability interpretation header
        ws.merge_cells(f'A{current_row}:H{current_row}')
        interp_header = ws[f'A{current_row}']
        interp_header.value = "CAPABILITY ASSESSMENT"
        interp_header.style = 'section_header'
        
        current_row += 1
        
        # Get capability values
        cp = element_data.get('cp', 0)
        cpk = element_data.get('cpk', 0)
        
        # Capability status
        if isinstance(cpk, (int, float)):
            if cpk >= 1.67:
                status = "EXCELLENT - Process highly capable"
                status_color = self.COLORS['success_green']
            elif cpk >= 1.33:
                status = "ACCEPTABLE - Process capable"
                status_color = self.COLORS['warning_orange']
            elif cpk >= 1.0:
                status = "MARGINAL - Process minimally capable"
                status_color = self.COLORS['warning_orange']
            else:
                status = "INADEQUATE - Process improvement required"
                status_color = self.COLORS['danger_red']
        else:
            status = "UNABLE TO ASSESS - Insufficient data"
            status_color = self.COLORS['medium_gray']
        
        # Status display
        ws[f'A{current_row}'].value = "Process Status:"
        ws[f'A{current_row}'].style = 'param_label'
        
        ws.merge_cells(f'B{current_row}:H{current_row}')
        status_cell = ws[f'B{current_row}']
        status_cell.value = status
        status_cell.style = 'data_cell'
        status_cell.fill = PatternFill(start_color=status_color, end_color=status_color, fill_type='solid')
        
        if status_color in [self.COLORS['danger_red'], self.COLORS['warning_orange']]:
            status_cell.font = Font(name='Arial', size=9, bold=True, color='FFFFFF')
        else:
            status_cell.font = Font(name='Arial', size=9, bold=True, color=self.COLORS['dark_gray'])
        
        current_row += 2
        return current_row

    def create_executive_summary_sheet(self) -> None:
        """Create an executive summary cover sheet with all elements overview"""
        
        try:
            # Create summary sheet as first sheet
            summary_ws = self.workbook.create_sheet(title="Executive Summary", index=0)
            
            current_row = 1
            
            # Add company logo with exact dimensions (6.5cm wide x 1.5cm high)
            logo_path = Path("./assets/images/gui/logo_some.png")
            if logo_path.exists():
                try:
                    img = Image(str(logo_path))
                    img.width = 245  # 6.5cm * 37.8 pixels/cm
                    img.height = 57   # 1.5cm * 37.8 pixels/cm
                    summary_ws.add_image(img, f'A{current_row}')
                    current_row += 4  # Space after logo
                except Exception as e:
                    self.logger.warning(f"Could not add logo: {e}")
                    current_row += 1
            
            # Title
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            title_cell = summary_ws[f'A{current_row}']
            title_cell.value = "STATISTICAL PROCESS CONTROL REPORT"
            title_cell.style = 'doc_title'
            
            current_row += 1
            
            # Subtitle
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            subtitle_cell = summary_ws[f'A{current_row}']
            subtitle_cell.value = f"{self.client} - {self.ref_project} - Batch {self.batch_number}"
            subtitle_cell.style = 'doc_subtitle'
            
            current_row += 3
            
            # Add capability visualization chart
            current_row = self.add_capability_visualization(summary_ws, current_row)
            current_row += 2
            
            # Project information box
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            info_header = summary_ws[f'A{current_row}']
            info_header.value = "PROJECT INFORMATION"
            info_header.style = 'section_header'
            
            current_row += 1
            
            # Project details in two columns
            project_info_left = [
                ["Client:", self.client],
                ["Project Reference:", self.ref_project],
                ["Batch Number:", self.batch_number],
                ["Report Date:", datetime.now().strftime("%d/%m/%Y")]]
            
            project_info_right = [
                ["Elements Analyzed:", str(len(self.elements_data))],
                ["Generated On:", datetime.now().strftime("%d/%m/%Y %H:%M")],
                ["Software Version:", "SPC Professional v1.0"]
            ]
            
            for i, (label, value) in enumerate(project_info_left):
                summary_ws[f'A{current_row + i}'].value = label
                summary_ws[f'A{current_row + i}'].style = 'param_label'
                summary_ws.merge_cells(f'B{current_row + i}:E{current_row + i}')
                summary_ws[f'B{current_row + i}'].value = value
                summary_ws[f'B{current_row + i}'].style = 'data_cell'
                summary_ws[f'B{current_row + i}'].border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
            
            for i, (label, value) in enumerate(project_info_right):
                summary_ws[f'G{current_row + i}'].value = label
                summary_ws[f'G{current_row + i}'].style = 'param_label'
                summary_ws.merge_cells(f'H{current_row + i}:J{current_row + i}')
                summary_ws[f'H{current_row + i}'].value = value
                summary_ws[f'H{current_row + i}'].style = 'data_cell'
                summary_ws[f'H{current_row + i}'].border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
            
            current_row += max(len(project_info_left), len(project_info_right)) + 2
            
            # Elements summary table
            summary_ws.merge_cells(f'A{current_row}:J{current_row}')
            table_header = summary_ws[f'A{current_row}']
            table_header.value = "PROCESS CAPABILITY SUMMARY"
            table_header.style = 'section_header'
            
            current_row += 1
            
            # Table headers with shorter names
            headers = [
                "Element", "Cavity", "Mean", 
                "CP", "CPK", "σ Short", 
                "PP", "PPK", "σ Long", 
                "Status"
            ]
            
            for i, header in enumerate(headers):
                col = chr(65 + i)  # A, B, C, etc.
                summary_ws[f'{col}{current_row}'].value = header
                summary_ws[f'{col}{current_row}'].style = 'table_header'
                summary_ws[f'{col}{current_row}'].border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
            
            current_row += 1
            
            # Element data rows
            for element_key, element_data in self.elements_data.items():
                # Element name and cavity
                summary_ws[f'A{current_row}'].value = element_key
                summary_ws[f'A{current_row}'].style = 'data_cell'
                summary_ws[f'B{current_row}'].value = element_data.get('cavity', 'N/A')
                summary_ws[f'B{current_row}'].style = 'data_cell'
                
                # Mean value
                mean = element_data.get('mean', 'N/A')
                if isinstance(mean, (int, float)):
                    summary_ws[f'C{current_row}'].value = f"{mean:.4f}"
                else:
                    summary_ws[f'C{current_row}'].value = str(mean)
                summary_ws[f'C{current_row}'].style = 'data_cell'
                
                # Short-term capability
                for i, param in enumerate(['cp', 'cpk', 'std_short']):
                    col = chr(68 + i)  # D, E, F
                    value = element_data.get(param, 'N/A')
                    if isinstance(value, (int, float)):
                        if param == 'std_short':
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = f"{value:.3f}"
                    else:
                        formatted_value = str(value)
                    
                    summary_ws[f'{col}{current_row}'].value = formatted_value
                    summary_ws[f'{col}{current_row}'].style = 'data_cell'
                
                # Long-term capability
                for i, param in enumerate(['pp', 'ppk', 'std_long']):
                    col = chr(71 + i)  # G, H, I
                    value = element_data.get(param, 'N/A')
                    if isinstance(value, (int, float)):
                        if param == 'std_long':
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = f"{value:.3f}"
                    else:
                        formatted_value = str(value)
                    
                    summary_ws[f'{col}{current_row}'].value = formatted_value
                    summary_ws[f'{col}{current_row}'].style = 'data_cell'
                
                # Status based on Cpk
                cpk = element_data.get('cpk', 0)
                if isinstance(cpk, (int, float)):
                    if cpk >= 1.67:
                        status = "Excellent"
                        color = self.COLORS['success_green']
                    elif cpk >= 1.33:
                        status = "Acceptable"
                        color = self.COLORS['warning_orange']
                    else:
                        status = "Inadequate"
                        color = self.COLORS['danger_red']
                else:
                    status = "N/A"
                    color = self.COLORS['medium_gray']
                
                status_cell = summary_ws[f'J{current_row}']
                status_cell.value = status
                status_cell.style = 'data_cell'
                status_cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
                
                if color in [self.COLORS['danger_red']]:
                    status_cell.font = Font(name='Arial', size=9, bold=True, color='FFFFFF')
                
                # Apply borders to all cells in row
                for col in range(1, 11):  # Columns A-J
                    cell = summary_ws.cell(row=current_row, column=col)
                    cell.border = Border(
                        left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))
                
                current_row += 1
            
            # Set column widths
            column_widths = {
                'A': 30, 'B': 10, 'C': 12, 'D': 8, 'E': 8, 
                'F': 10, 'G': 8, 'H': 8, 'I': 10, 'J': 12
            }
            for col, width in column_widths.items():
                summary_ws.column_dimensions[col].width = width
            
            # Setup page formatting
            self.setup_professional_page_formatting(summary_ws)
            
            self.logger.info("Created executive summary sheet")
            
        except Exception as e:
            self.logger.error(f"Error creating executive summary: {e}")

    def add_capability_visualization(self, ws: Worksheet, start_row: int) -> int:
        """Add a visual representation of capability status distribution"""
        
        current_row = start_row
        
        # Create a simple visualization table showing capability distribution
        ws.merge_cells(f'A{current_row}:J{current_row}')
        vis_header = ws[f'A{current_row}']
        vis_header.value = "CAPABILITY STATUS DISTRIBUTION"
        vis_header.style = 'section_header'
        
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
        
        # Create visualization table
        headers = ["Status", "Count", "Percentage", "Visualization"]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=current_row, column=col*2-1)  # A, C, E, G
            ws.merge_cells(start_row=current_row, start_column=col*2-1,
                        end_row=current_row, end_column=col*2)
            cell.value = header
            cell.style = 'table_header'
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
        
        current_row += 1
        
        # Add data rows
        colors = {
            "Excellent (CPK ≥ 1.67)": self.COLORS['success_green'],
            "Acceptable (1.33 ≤ CPK < 1.67)": self.COLORS['warning_orange'],
            "Inadequate (CPK < 1.33)": self.COLORS['danger_red'],
            "N/A": self.COLORS['medium_gray']
        }
        
        total_elements = len(self.elements_data)
        
        for status, count in status_counts.items():
            if count == 0:
                continue
                
            # Status name
            ws.merge_cells(start_row=current_row, start_column=1,
                        end_row=current_row, end_column=2)
            cell = ws.cell(row=current_row, column=1)
            cell.value = status
            cell.style = 'param_label'
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Count
            ws.merge_cells(start_row=current_row, start_column=3,
                        end_row=current_row, end_column=4)
            cell = ws.cell(row=current_row, column=3)
            cell.value = count
            cell.style = 'data_cell'
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Percentage
            ws.merge_cells(start_row=current_row, start_column=5,
                        end_row=current_row, end_column=6)
            cell = ws.cell(row=current_row, column=5)
            percentage = (count / total_elements) * 100
            cell.value = f"{percentage:.1f}%"
            cell.style = 'data_cell'
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Visualization bar
            ws.merge_cells(start_row=current_row, start_column=7,
                        end_row=current_row, end_column=8)
            cell = ws.cell(row=current_row, column=7)
            cell.value = " " * int(percentage / 5)  # Simple text bar
            cell.style = 'data_cell'
            cell.fill = PatternFill(start_color=colors[status], 
                                end_color=colors[status], 
                                fill_type='solid')
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
            
            current_row += 1
        
        return current_row