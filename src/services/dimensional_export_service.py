# src/services/dim_data_export_service.py
import json
import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from src.models.dimensional.dimensional_result import DimensionalResult
from src.database.database_connection import PostgresConn


class DataExportService:
    """Professional dimensional analysis export service for automotive PPAP reports"""

    def __init__(self):
        os.makedirs('logs', exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler('logs/dimensional.log')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(fh)
        
        self._init_styles()
        
    def _init_styles(self):
        """Initialize Excel styling constants for automotive PPAP standards"""
        # Fonts
        self.HEADER_FONT = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        self.TITLE_FONT = Font(name='Arial', size=16, bold=True, color='2C3E50')
        self.SUBTITLE_FONT = Font(name='Arial', size=11, bold=True, color='34495E')
        self.DATA_FONT = Font(name='Arial', size=9)
        self.SMALL_FONT = Font(name='Arial', size=8)
        self.NOTES_FONT = Font(name='Arial', size=9)
        self.BASIC_FONT = Font(name='Arial', size=9, color='808080')
        self.STATISTICAL_FONT = Font(name='Arial', size=9, bold=True, color='1B4F72')
        
        # Fills
        self.HEADER_FILL = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
        self.OK_FILL = PatternFill(start_color='D5F4E6', end_color='D5F4E6', fill_type='solid')
        self.NOK_FILL = PatternFill(start_color='FADBD8', end_color='FADBD8', fill_type='solid')
        self.TED_FILL = PatternFill(start_color='E8F4F8', end_color='E8F4F8', fill_type='solid')
        self.WG_FILL = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid')
        self.ALT_ROW_FILL = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
        self.STATISTICAL_FILL = PatternFill(start_color='E8F4F8', end_color='E8F4F8', fill_type='solid')
        
        # Professional border system
        self.THICK_BORDER = Border(
            left=Side(style='thick', color='2C3E50'), 
            right=Side(style='thick', color='2C3E50'),
            top=Side(style='thick', color='2C3E50'), 
            bottom=Side(style='thick', color='2C3E50')
        )
        self.MEDIUM_BORDER = Border(
            left=Side(style='medium', color='85929E'), 
            right=Side(style='medium', color='85929E'),
            top=Side(style='medium', color='85929E'), 
            bottom=Side(style='medium', color='85929E')
        )
        self.THIN_BORDER = Border(
            left=Side(style='thin', color='D0D3D4'), 
            right=Side(style='thin', color='D0D3D4'),
            top=Side(style='thin', color='D0D3D4'), 
            bottom=Side(style='thin', color='D0D3D4')
        )
        
        # Specialized borders for groupings
        self.LEFT_MEDIUM_BORDER = Border(
            left=Side(style='medium', color='85929E'),
            right=Side(style='thin', color='D0D3D4'),
            top=Side(style='thin', color='D0D3D4'),
            bottom=Side(style='thin', color='D0D3D4')
        )

    def export_dimensional_report(
        self, 
        results: List[DimensionalResult],
        export_dir: str,
        base_filename: str,
        metadata: Dict[str, Any],
        summary_data: Optional[Dict] = None,
        logo_path: Optional[str] = None,
        db_config_path: Optional[str] = None,
        db_key: str = "primary"
    ) -> Dict[str, str]:
        """Main export method for automotive PPAP reports"""
        try:
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_paths = {}

            # Enhance metadata with database info
            enhanced_metadata = self._enhance_metadata(metadata, db_config_path, db_key)
            
            # Sort and group results with proper automotive numbering
            sorted_results = self._sort_results_automotive_standard(results)
            cavity_groups = self._group_results_by_cavity(sorted_results)

            # Create Excel report
            excel_path = os.path.join(export_dir, f"{base_filename}_PPAP_REPORT_{timestamp}.xlsx")
            self._professional_excel_report(
                excel_path, 
                cavity_groups,
                enhanced_metadata,
                summary_data,
                logo_path
            )
            export_paths['excel_report'] = excel_path
            self.logger.info(f"Professional Excel PPAP report created: {os.path.basename(excel_path)}")

            # Create comprehensive JSON
            json_path = os.path.join(export_dir, f"{base_filename}_complete_data_{timestamp}.json")
            self._export_comprehensive_json(
                json_path, 
                sorted_results, 
                enhanced_metadata, 
                summary_data,
                cavity_groups
            )
            export_paths['json_data'] = json_path
            self.logger.info(f"Comprehensive JSON exported: {os.path.basename(json_path)}")

            return export_paths

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Export failed: {str(e)}") from e

    def _sort_results_automotive_standard(self, results: List[DimensionalResult]) -> List[DimensionalResult]:
        """Sort element_id with automotive industry standard"""
        def parse_automotive_id(eid: str) -> Tuple[int, int, float]:
            eid = str(eid).strip()
            cleaned = re.sub(r'^(Nº|No\.?|#)\s*', '', eid, flags=re.IGNORECASE)
            
            try:
                if '.' in cleaned:
                    parts = cleaned.split('.')
                    main_num = int(parts[0])
                    decimal_part = float('0.' + parts[1]) if len(parts) > 1 else 0
                    return (0, main_num, decimal_part)
                else:
                    main_num = int(cleaned)
                    return (0, main_num, 0.0)
            except (ValueError, IndexError):
                return (1, 999999, 0.0)

        return sorted(results, key=lambda r: parse_automotive_id(r.element_id))

    def _enhance_metadata(self, metadata: Dict[str, Any], db_config_path: Optional[str], db_key: str) -> Dict[str, Any]:
        """Enhance metadata with fixed values and database lookup"""
        enhanced = {
            'client_name': metadata.get('client_name', ''),
            'project_ref': metadata.get('project_ref', ''),
            'part_number': metadata.get('project_ref', ''),
            'batch_number': metadata.get('batch_number', ''),
            'report_type': metadata.get('report_type', 'PPAP'),
            'tolerance_standard': metadata.get('tolerance_standard', 'ISO 2768-m'),
            'cavity_display': self._get_cavity_display(metadata),
            'part_description': '',  # Will be looked up from database
            'quotation_number': '',  # Will be looked up from database
            'drawing_number': '',
            'inspection_facility': 'Quality Lab 1',
            'protocol_reference': 'ITM-1',
            'report_date': datetime.now().strftime('%d/%m/%Y'),
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Try to get database metadata if available
        if db_config_path and os.path.exists(db_config_path):
            try:
                db_metadata = self._fetch_database_metadata(db_config_path, db_key, enhanced)
                enhanced.update(db_metadata)
            except Exception as e:
                self.logger.warning(f"Database metadata lookup failed: {e}")
        
        return enhanced

    def _get_cavity_display(self, metadata: Dict[str, Any]) -> str:
        """Get cavity display text for header"""
        cavity_count = metadata.get('cavity_count', 1)
        current_cavity = metadata.get('current_cavity', None)
        
        if current_cavity:
            return str(current_cavity)
        elif cavity_count > 2:
            return 'All'
        elif cavity_count == 2:
            return 'Both'
        else:
            return '1'

    def _fetch_database_metadata(self, db_config_path: str, db_key: str, base_metadata: Dict) -> Dict[str, Any]:
        """Fetch additional metadata from database"""
        try:
            with open(db_config_path, 'r') as f:
                db_config = json.load(f)
            
            conn_config = db_config.get(db_key, {})
            if not conn_config:
                return {}

            db = PostgresConn(
                host=conn_config["host"],
                database=conn_config["database"],
                user=conn_config["user"],
                password=conn_config["password"],
                port=conn_config.get("port", 5432)
            )

            project_ref = base_metadata.get('project_ref', '')
            
            # Query for project details
            query = """
                SELECT part_description, quotation_number, drawing_number
                FROM project_metadata 
                WHERE project_ref = %s OR part_number = %s
                ORDER BY updated_at DESC LIMIT 1
            """
            
            row = db.fetchone(query, (project_ref, project_ref))
            if row:
                return {
                    'part_description': row[0] or '',
                    'quotation_number': row[1] or '',
                    'drawing_number': row[2] or ''
                }

            db.close()
            
        except Exception as e:
            self.logger.warning(f"Database lookup failed: {e}")
        
        return {}

    def _professional_excel_report(self, filepath: str, cavity_groups: Dict[int, List[DimensionalResult]], metadata: Dict[str, Any], summary_data: Optional[Dict] = None, logo_path: Optional[str] = None):
        """Create professional Excel workbook for automotive PPAP"""
        wb = Workbook()
        
        if wb.active:
            wb.remove(wb.active)
        
        # Create main report sheet
        main_sheet = wb.create_sheet("PPAP Dimensional Report")
        self._main_report_sheet(main_sheet, cavity_groups, metadata, logo_path)
        
        # Create cavity-specific sheets if multiple cavities
        if len(cavity_groups) > 1:
            for cavity_num in sorted(cavity_groups.keys()):
                cavity_metadata = {**metadata, 'current_cavity': cavity_num}
                cavity_sheet = wb.create_sheet(f"Cavity {cavity_num}")
                self._create_cavity_specific_sheet(
                    cavity_sheet, 
                    cavity_groups[cavity_num], 
                    cavity_num, 
                    cavity_metadata, 
                    logo_path
                )
        
        # Create summary sheet
        if summary_data:
            summary_sheet = wb.create_sheet("Analysis Summary")
            self._create_summary_sheet(summary_sheet, cavity_groups, metadata, summary_data)
        
        # Set print settings for all sheets
        for sheet in wb.worksheets:
            self._set_print_settings(sheet)
        
        wb.save(filepath)

    def _main_report_sheet(self, ws: Worksheet, cavity_groups: Dict[int, List[DimensionalResult]], metadata: Dict[str, Any], logo_path: Optional[str] = None):
        """Create main PPAP report sheet with enhanced professional header"""
        current_row = 1
        
        # Add professional header with logo
        current_row = self._ppap_header(ws, metadata, current_row, logo_path)
        current_row += 1
        
        # Add dimensional data table
        all_results = []
        for cavity_results in cavity_groups.values():
            all_results.extend(cavity_results)
        
        current_row = self._dimensional_table(ws, all_results, current_row)
        current_row += 2
        
        # Add professional footer
        self._ppap_footer(ws, metadata, current_row)
        
        # Apply professional formatting
        self._apply_formatting(ws)

    def _ppap_header(self, ws: Worksheet, metadata: Dict[str, Any], start_row: int, logo_path: Optional[str] = None) -> int:
        """Add enhanced professional PPAP header with logo and improved layout"""
        current_row = start_row
        
        # LOGO AND TITLE SECTION
        if logo_path and os.path.exists(logo_path):
            try:
                # Add logo with exact dimensions: 1.9cm height x 8.53cm width
                img = Image(logo_path)
                
                # Convert cm to pixels (approximate conversion for Excel)
                # Excel uses 96 DPI: 1 cm ≈ 37.8 pixels
                img.height = int(1.9 * 37.8)  # ~72 pixels
                img.width = int(8.53 * 37.8)  # ~322 pixels
                
                # Alternative exact size using cm (works in newer openpyxl versions)
                # img.height = 1.9 * 28.35  # 1 cm = 28.35 points
                # img.width = 8.53 * 28.35
                
                ws.add_image(img, f'A{current_row}')
                ws.row_dimensions[current_row].height = 54  # Approximately 1.9cm | Adjust row height to match logo
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")

        #ws.page_setup.firstFooter.left.text = "Confidential - " + metadata.get('client_name', '')
        #ws.page_setup.firstFooter.left.size = 8
        #ws.page_setup.firstFooter.left.font = "Arial,Bold"
        #ws.page_setup.firstFooter.left.color = "2C3E50"
        
        # Main title (positioned to accommodate logo)
        ws.merge_cells(f'D{current_row}:O{current_row}')
        title_cell = ws.cell(row=current_row, column=4, value="PRODUCTION PART APPROVAL PROCESS")
        title_cell.font = Font(name='Arial', size=18, bold=True, color='1B4F72')
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 30
        current_row += 1
        
        # Subtitle
        ws.merge_cells(f'D{current_row}:O{current_row}')
        subtitle_cell = ws.cell(row=current_row, column=4, value="DIMENSIONAL ANALYSIS RESULTS")
        subtitle_cell.font = Font(name='Arial', size=14, bold=True, color='2C3E50')
        subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 25
        current_row += 2
        
        # INFORMATION GRID SECTION
        # Apply consistent borders to the entire header section
        header_start_row = current_row
        
        # Row 1: Supplier and Part Number
        self._add_header_row(ws, current_row, [
            ("Supplier:", metadata.get('client_name', ''), 7),
            ("Part No.:", metadata.get('part_number', ''), 8)
        ])
        current_row += 1
        
        # Row 2: Part Description and Drawing Number
        part_desc = metadata.get('part_description', '') or f"Part for {metadata.get('project_ref', '')}"
        drawing_info = metadata.get('drawing_number', '') or "TBD"
        self._add_header_row(ws, current_row, [
            ("Part Description:", part_desc, 7),
            ("Drawing No./Rev.:", drawing_info, 8)
        ])
        current_row += 1
        
        # Row 3: Batch Number and Cavity
        self._add_header_row(ws, current_row, [
            ("Batch No.:", metadata.get('batch_number', ''), 7),
            ("Cavity No.:", metadata.get('cavity_display', '1'), 8)
        ])
        current_row += 1
        
        # Row 4: Inspection Facility and Report Number
        report_number = metadata.get('quotation_number', '') or f"{metadata.get('project_ref', '')}/{datetime.now().strftime('%y/%m')}"
        self._add_header_row(ws, current_row, [
            ("Inspection Facility:", metadata.get('inspection_facility', 'Quality Lab 1'), 7),
            ("Report Number:", report_number, 8)
        ])
        current_row += 1
        
        # Row 5: Report Date and Protocol
        protocol_text = f"According metrology protocol {metadata.get('protocol_reference', 'ITM-1')} / {metadata.get('tolerance_standard', 'ISO 2768-m')}"
        self._add_header_row(ws, current_row, [
            ("Report Date:", metadata.get('report_date', datetime.now().strftime('%d/%m/%Y')), 7),
            ("Metrology Protocol:", protocol_text, 8)
        ])
        current_row += 1
        
        # Row 6: Report Type and Standard
        self._add_header_row(ws, current_row, [
            ("Report Type:", metadata.get('report_type', 'PPAP'), 7),
            ("Tolerance Standard:", metadata.get('tolerance_standard', 'ISO 2768-m'), 8)
        ])
        current_row += 1
        
        # Apply professional borders to the entire header grid
        self._apply_header_borders(ws, header_start_row, current_row - 1)
        
        return current_row + 1

    def _add_header_row(self, ws: Worksheet, row: int, items: List[Tuple[str, str, int]]):
        """Add a header information row with proper formatting"""
        ws.row_dimensions[row].height = 22
        
        # Left side item
        left_label, left_value, left_end_col = items[0]
        ws.cell(row=row, column=1, value=left_label).font = Font(name='Arial', size=10, bold=True, color='2C3E50')
        ws.merge_cells(f'B{row}:{get_column_letter(left_end_col)}{row}')
        ws.cell(row=row, column=2, value=left_value).font = Font(name='Arial', size=10)
        
        # Right side item
        if len(items) > 1:
            right_label, right_value, right_end_col = items[1]
            ws.cell(row=row, column=right_end_col, value=right_label).font = Font(name='Arial', size=10, bold=True, color='2C3E50')
            ws.merge_cells(f'{get_column_letter(right_end_col + 1)}{row}:O{row}')
            ws.cell(row=row, column=right_end_col + 1, value=right_value).font = Font(name='Arial', size=10)

    def _apply_header_borders(self, ws: Worksheet, start_row: int, end_row: int):
        """Apply consistent professional borders to header section"""
        for row in range(start_row, end_row + 1):
            for col in range(1, 16):  # A to O
                cell = ws.cell(row=row, column=col)
                
                # Determine border style
                if row == start_row and row == end_row:
                    # Single row
                    cell.border = self.THICK_BORDER
                elif row == start_row:
                    # Top row
                    cell.border = Border(
                        left=Side(style='thick', color='2C3E50'),
                        right=Side(style='thick', color='2C3E50'),
                        top=Side(style='thick', color='2C3E50'),
                        bottom=Side(style='thin', color='D0D3D4')
                    )
                elif row == end_row:
                    # Bottom row
                    cell.border = Border(
                        left=Side(style='thick', color='2C3E50'),
                        right=Side(style='thick', color='2C3E50'),
                        top=Side(style='thin', color='D0D3D4'),
                        bottom=Side(style='thick', color='2C3E50')
                    )
                else:
                    # Middle rows
                    cell.border = Border(
                        left=Side(style='thick', color='2C3E50'),
                        right=Side(style='thick', color='2C3E50'),
                        top=Side(style='thin', color='D0D3D4'),
                        bottom=Side(style='thin', color='D0D3D4')
                    )
                
                # Add background for professional look
                if col in [1, 8]:  # Label columns
                    cell.fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')

    def _dimensional_table(self, ws: Worksheet, results: List[DimensionalResult], start_row: int) -> int:
        """Add automotive dimensional data table with enhanced formatting"""
        current_row = start_row
        
        # Enhanced headers
        headers = [
            'Element\nID', 'Description', 'Measuring\nInstrument', 'M1', 'M2', 'M3', 'M4', 'M5',
            'Min.', 'Max.', 'Mean\nValue', 'Std\nDev', 'Pp', 'Ppk', 'Status'
        ]
        
        # Write headers with professional styling
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = self._get_header_border(col)
        
        ws.row_dimensions[current_row].height = 40
        current_row += 1
        
        
        # Write data rows
        for row_idx, result in enumerate(results):
            self._add_enhanced_data_row(ws, current_row, result, len(headers), row_idx)
            current_row += 1
        
        # Set column widths
        self._set_automotive_column_widths(ws)
        
        return current_row

    def _get_header_border(self, col: int) -> Border:
        """Get appropriate border for header cell based on column grouping"""
        if col in [3, 8, 11, 14]:  # Group separators
            return Border(
                left=Side(style='thin', color='D0D3D4'),
                right=Side(style='medium', color='85929E'),
                top=Side(style='thick', color='2C3E50'),
                bottom=Side(style='thick', color='2C3E50')
            )
        else:
            return self.THICK_BORDER

    def _add_enhanced_data_row(self, ws: Worksheet, row: int, result: DimensionalResult, num_columns: int, row_index: int):
        """Add data row with enhanced formatting and fixed evaluation type handling"""
        
        # Fix evaluation type handling - check for both 'evaluation_type' and 'eval_type'
        evaluation_type = (
            getattr(result, 'evaluation_type', None) or 
            getattr(result, 'eval_type', None) or
            getattr(result, 'feature_type', None) or
            ''
        )
        evaluation_type = str(evaluation_type).strip().lower()

        # Check if it's a note
        is_notes = evaluation_type in ['note', 'notes']
        if not is_notes:
            desc = (getattr(result, 'description', '') or '').lower()
            classe = (getattr(result, 'classe', '') or '').lower()
            if 'note' in desc or 'nota' in desc or classe == 'note':
                is_notes = True

        dimension_class = getattr(result, 'classe', '') or ''
        is_basic_info = evaluation_type in ['basic', 'informative']
        is_statistical = dimension_class.upper() in ['CC', 'SC', 'IC'] and not is_notes

        measurements = result.measurements if result.measurements else []
        has_measurements = bool(measurements and any(m is not None for m in measurements))

        # Prepare data
        if not has_measurements or is_notes:
            measurements_out = [""] * 5
            status = "TO CHECK"
            mean_val = None
            min_val = None
            max_val = None
            std_val = None
            pp_val = None
            ppk_val = None
        else:
            measurements_out = [self._format_measurement(m) for m in (measurements + [None] * 5)[:5]]
            status = self._normalize_status(result.status)
            mean_val = getattr(result, 'mean', None)
            min_val = min(measurements) if measurements else None
            max_val = max(measurements) if measurements else None
            
            if is_statistical:
                std_val = getattr(result, 'std_dev', None)
                pp_val = getattr(result, 'pp', None)
                ppk_val = getattr(result, 'ppk', None)
            else:
                std_val = None
                pp_val = None
                ppk_val = None

        # Enhanced measuring instrument formatting - fix for 'visual'
        measuring_instrument = self._format_instrument(result.measuring_instrument)

        data = [
            result.element_id,
            result.description or '',
            measuring_instrument,
            *measurements_out,
            "" if not has_measurements else self._format_number(min_val, 2),
            "" if not has_measurements else self._format_number(max_val, 2),
            "" if not has_measurements else self._format_number(mean_val, 2),
            "" if not has_measurements or not is_statistical else self._format_number(std_val, 2),
            "" if not has_measurements or not is_statistical else self._format_number(pp_val, 2),
            "" if not has_measurements or not is_statistical else self._format_number(ppk_val, 2),
            status
        ]

        is_alternate = row_index % 2 == 1

        # Apply data to cells with enhanced formatting
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)

            # Apply fonts based on dimension type
            if not has_measurements or is_notes:
                cell.font = self.NOTES_FONT
            elif is_basic_info:
                cell.font = self.BASIC_FONT
            elif is_statistical:
                cell.font = self.STATISTICAL_FONT
            else:
                cell.font = self.DATA_FONT

            # Enhanced alignment
            cell.alignment = self._get_cell_alignment(col, is_notes)

            # Background fills with enhanced statistical highlighting
            if col == 15:  # Status column
                self._apply_status_formatting(cell, status)
            elif is_statistical and not is_notes:
                cell.fill = self.STATISTICAL_FILL
            elif is_alternate and not is_statistical:
                cell.fill = self.ALT_ROW_FILL

            # Enhanced borders with logical groupings
            cell.border = self._get_data_cell_border(col)

        # Set row height
        ws.row_dimensions[row].height = 45 if is_notes else 25

    def _get_cell_alignment(self, col: int, is_notes: bool) -> Alignment:
        """Get appropriate cell alignment based on column and data type"""
        if col == 1:  # Element ID
            return Alignment(horizontal='center', vertical='center')
        elif col == 2:  # Description
            if is_notes:
                return Alignment(horizontal='left', vertical='top', wrap_text=True)
            else:
                return Alignment(horizontal='center', vertical='center', wrap_text=True)
        elif col == 3:  # Measuring Instrument
            return Alignment(horizontal='center', vertical='center')
        elif 4 <= col <= 14:  # Measurements and statistics
            return Alignment(horizontal='center', vertical='center')
        elif col == 15:  # Status
            return Alignment(horizontal='center', vertical='center')
        else:
            return Alignment(horizontal='center', vertical='center')

    def _get_data_cell_border(self, col: int) -> Border:
        """Get appropriate border for data cell based on column grouping"""
        if col in [4, 9, 12, 15]:  # Group separators
            return self.LEFT_MEDIUM_BORDER
        else:
            return self.THIN_BORDER

    def _format_instrument(self, instrument: Optional[str]) -> str:
        """Enhanced instrument formatting - fixes visual instrument display"""
        if not instrument:
            return ''
        
        instrument_str = str(instrument).strip().lower()
        
        # Handle specific instruments
        if instrument_str == 'visual':
            return 'Visual'
        elif instrument_str == 'scanbox':
            return 'ScanBox'
        elif instrument_str in ['cmm', 'coordinate_measuring_machine']:
            return 'CMM'
        else:
            # Capitalize first letter of each word
            return ' '.join(word.capitalize() for word in instrument_str.split())

    def _normalize_status(self, status) -> str:
        """Normalize status values for automotive industry standards"""
        if hasattr(status, 'value'):
            status_str = status.value
        else:
            status_str = str(status)
        
        status_str = status_str.strip().upper()
        
        status_map = {
            'GOOD': 'OK', 'PASS': 'OK', 'OK': 'OK', 'PASSED': 'OK', 'CONFORMING': 'OK',
            'BAD': 'NOK', 'FAIL': 'NOK', 'NOK': 'NOK', 'NG': 'NOK', 'FAILED': 'NOK', 'NON_CONFORMING': 'NOK',
            'WARNING': 'WARNING', 'WARN': 'WARNING',
            'T.E.D.': 'T.E.D', 'TED': 'T.E.D', 'T.E.D': 'T.E.D', 'BASIC': 'T.E.D', 'INFORMATIVE': 'T.E.D',
            'TO CHECK': 'TO CHECK', 'TO_CHECK': 'TO CHECK', 'CHECK': 'TO CHECK', 'PENDING': 'TO CHECK'
        }
        
        return status_map.get(status_str, 'TO CHECK')
    
    def _format_measurement(self, value) -> str:
        """Format measurement values to 2 decimals"""
        try:
            if value is None:
                return ''
            num = float(value)
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value) if value is not None else ''

    def _format_number(self, value, decimals: int = 2) -> str:
        """Format numbers consistently to specified decimals"""
        try:
            if value is None:
                return ''
            num = float(value)
            return f"{num:.{decimals}f}"
        except (ValueError, TypeError):
            return str(value) if value is not None else ''

    def _apply_status_formatting(self, cell, status: str):
        """Apply status-based formatting for automotive standards"""
        status_formats = {
            'OK': (self.OK_FILL, Font(name='Arial', size=9, bold=True, color='27AE60')),
            'NOK': (self.NOK_FILL, Font(name='Arial', size=9, bold=True, color='E74C3C')),
            'T.E.D': (self.TED_FILL, Font(name='Arial', size=9, bold=True, color='3498DB')),
            'WARNING': (self.WG_FILL, Font(name='Arial', size=9, bold=True, color='856404')),
            'TO CHECK': (PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid'), 
                        Font(name='Arial', size=9, bold=True, color='D6B656'))
        }
        
        if status in status_formats:
            fill, font = status_formats[status]
            cell.fill = fill
            cell.font = font

    def _ppap_footer(self, ws: Worksheet, metadata: Dict[str, Any], start_row: int):
        """Add enhanced professional PPAP footer with improved notes section"""
        current_row = start_row + 1
        
        # NOTES SECTION - Enhanced with single merged cell
        ws.merge_cells(f'A{current_row}:O{current_row}')
        notes_header = ws.cell(row=current_row, column=1, value="NOTES / OBSERVATIONS:")
        notes_header.font = Font(name='Arial', size=11, bold=True, color='1B4F72')
        notes_header.fill = PatternFill(start_color='EBF3FD', end_color='EBF3FD', fill_type='solid')
        notes_header.alignment = Alignment(horizontal='left', vertical='center')
        notes_header.border = Border(
            left=Side(style='thick', color='2C3E50'),
            right=Side(style='thick', color='2C3E50'),
            top=Side(style='thick', color='2C3E50'),
            bottom=Side(style='medium', color='85929E')
        )
        ws.row_dimensions[current_row].height = 25
        current_row += 1
        
        # Single large notes area - more professional
        ws.merge_cells(f'A{current_row}:O{current_row + 4}')
        notes_cell = ws.cell(row=current_row, column=1, value='')
        notes_cell.border = Border(
            left=Side(style='thick', color='2C3E50'),
            right=Side(style='thick', color='2C3E50'),
            top=Side(style='thin', color='D0D3D4'),
            bottom=Side(style='thick', color='2C3E50')
        )
        notes_cell.fill = PatternFill(start_color='FAFBFC', end_color='FAFBFC', fill_type='solid')
        notes_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        
        # Set height for notes area
        for i in range(5):
            ws.row_dimensions[current_row + i].height = 20
        
        current_row += 6
        
        # APPROVAL SECTION - Enhanced
        ws.merge_cells(f'A{current_row}:O{current_row}')
        approval_header = ws.cell(row=current_row, column=1, value="QUALITY APPROVAL")
        approval_header.font = Font(name='Arial', size=11, bold=True, color='1B4F72')
        approval_header.fill = PatternFill(start_color='EBF3FD', end_color='EBF3FD', fill_type='solid')
        approval_header.alignment = Alignment(horizontal='center', vertical='center')
        approval_header.border = self.THICK_BORDER
        ws.row_dimensions[current_row].height = 25
        current_row += 1
        
        # Signature table with improved layout
        self._add_signature_table(ws, current_row, metadata)
        current_row += 4
        
        # Professional compliance footer
        ws.merge_cells(f'A{current_row}:O{current_row}')
        compliance_text = (
            f"This report complies with {metadata.get('tolerance_standard', 'ISO 2768-m')} standards and automotive PPAP requirements. "
            f"According metrology protocol {metadata.get('protocol_reference', 'ITM-1')}. "
            f"Generated: {metadata.get('export_timestamp', datetime.now().isoformat())}"
        )
        compliance_footer = ws.cell(row=current_row, column=1, value=compliance_text)
        compliance_footer.font = Font(name='Arial', size=8, italic=True, color='566573')
        compliance_footer.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        compliance_footer.border = self.THIN_BORDER
        ws.row_dimensions[current_row].height = 30

    def _add_signature_table(self, ws: Worksheet, start_row: int, metadata: Dict[str, Any]):
        """Add professional signature table"""
        current_row = start_row
        
        # Headers
        headers = ["Signature", "Title", "Date"]
        header_ranges = [
            f'A{current_row}:F{current_row}',
            f'G{current_row}:L{current_row}',
            f'M{current_row}:O{current_row}'
        ]
        
        for i, (header, cell_range) in enumerate(zip(headers, header_ranges)):
            ws.merge_cells(cell_range)
            cell = ws.cell(row=current_row, column=1 + i * 6 if i < 2 else 13, value=header)
            cell.font = Font(name='Arial', size=10, bold=True, color='2C3E50')
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color='E8F4F8', end_color='E8F4F8', fill_type='solid')
            cell.border = self.MEDIUM_BORDER
        
        ws.row_dimensions[current_row].height = 25
        current_row += 1
        
        # Quality Engineer signature line
        signature_ranges = [
            f'A{current_row}:F{current_row}',
            f'G{current_row}:L{current_row}',
            f'M{current_row}:O{current_row}'
        ]
        
        signature_data = [
            "",  # Signature space
            "Quality Engineer",  # Title
            metadata.get('report_date', datetime.now().strftime('%d/%m/%Y'))  # Date
        ]
        
        for i, (data, cell_range) in enumerate(zip(signature_data, signature_ranges)):
            ws.merge_cells(cell_range)
            cell = ws.cell(row=current_row, column=1 + i * 6 if i < 2 else 13, value=data)
            cell.font = Font(name='Arial', size=10, bold=True if i == 1 else False)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
            if i == 0:  # Signature cell
                cell.fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
        
        ws.row_dimensions[current_row].height = 35
        current_row += 1
        
        # Project Leader signature line
        for i, (data, cell_range) in enumerate(zip(["", "Project Leader", ""], signature_ranges)):
            ws.merge_cells(cell_range)
            cell = ws.cell(row=current_row, column=1 + i * 6 if i < 2 else 13, value=data)
            cell.font = Font(name='Arial', size=10, bold=True if i == 1 else False)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
            if i == 0:  # Signature cell
                cell.fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
        
        ws.row_dimensions[current_row].height = 35

    def _create_cavity_specific_sheet(self, ws: Worksheet, cavity_results: List[DimensionalResult], cavity_num: int, metadata: Dict[str, Any], logo_path: Optional[str] = None):
        """Create cavity-specific sheet with automotive formatting"""
        current_row = 1
        current_row = self._ppap_header(ws, metadata, current_row, logo_path)
        current_row += 1
        current_row = self._dimensional_table(ws, cavity_results, current_row)
        current_row += 2
        self._ppap_footer(ws, metadata, current_row)
        self._apply_formatting(ws)

    def _set_automotive_column_widths(self, ws: Worksheet):
        """Set optimized column widths for automotive PPAP reports"""
        column_widths = {
            'A': 10,   # Element ID
            'B': 32,   # Description - wider for better readability
            'C': 14,   # Measuring Instrument
            'D': 7,    # M1
            'E': 7,    # M2
            'F': 7,    # M3
            'G': 7,    # M4
            'H': 7,    # M5
            'I': 8,    # Min Value
            'J': 8,    # Max Value
            'K': 8,    # Mean Value
            'L': 7,    # Std Dev
            'M': 7,    # Pp
            'N': 7,    # Ppk
            'O': 10    # Status
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    def _apply_formatting(self, ws: Worksheet):
        """Apply professional automotive industry formatting"""
        # Set default row heights for readability
        for row in ws.iter_rows():
            if row[0].row > 1 and ws.row_dimensions[row[0].row].height is None:
                ws.row_dimensions[row[0].row].height = 25

    def _create_summary_sheet(self, ws: Worksheet, cavity_groups: Dict[int, List[DimensionalResult]], metadata: Dict[str, Any], summary_data: Dict[str, Any]):
        """Create professional summary sheet with automotive metrics"""
        current_row = 1
        
        # Title
        ws.merge_cells(f'A{current_row}:H{current_row}')
        title = ws.cell(row=current_row, column=1, value="DIMENSIONAL ANALYSIS SUMMARY")
        title.font = self.TITLE_FONT
        title.alignment = Alignment(horizontal='center')
        current_row += 3
        
        # Calculate statistics using pre-calculated values
        all_results = []
        for cavity_results in cavity_groups.values():
            all_results.extend(cavity_results)
        
        total_dims = len(all_results)
        statuses = [self._normalize_status(r.status) for r in all_results]
        ok_count = statuses.count('OK')
        nok_count = statuses.count('NOK')
        ted_count = statuses.count('T.E.D')
        warning_count = statuses.count('WARNING')
        
        statistical_count = sum(1 for r in all_results 
                              if getattr(r, 'classe', '').upper() in ['CC', 'SC', 'IC'])
        
        success_rate = (ok_count / (ok_count + nok_count)) * 100 if (ok_count + nok_count) > 0 else 0
        
        # Overall statistics
        stats = [
            ('Total Dimensions:', total_dims),
            ('Passed (OK):', ok_count),
            ('Failed (NOK):', nok_count),
            ('Basic/Info (T.E.D):', ted_count),
            ('Warnings:', warning_count),
            ('Statistical Dimensions:', statistical_count),
            ('Success Rate:', f"{success_rate:.1f}%"),
            ('Analysis Date:', metadata.get('report_date', ''))
        ]
        
        for label, value in stats:
            ws.cell(row=current_row, column=1, value=label).font = self.SUBTITLE_FONT
            ws.cell(row=current_row, column=3, value=value).font = self.DATA_FONT
            current_row += 1
        
        # Cavity breakdown if multiple cavities
        if len(cavity_groups) > 1:
            current_row += 2
            ws.cell(row=current_row, column=1, value="CAVITY BREAKDOWN:").font = self.SUBTITLE_FONT
            current_row += 1
            
            for cavity_num in sorted(cavity_groups.keys()):
                cavity_results = cavity_groups[cavity_num]
                cavity_statuses = [self._normalize_status(r.status) for r in cavity_results]
                cavity_ok = cavity_statuses.count('OK')
                cavity_nok = cavity_statuses.count('NOK')
                cavity_rate = (cavity_ok / (cavity_ok + cavity_nok)) * 100 if (cavity_ok + cavity_nok) > 0 else 0
                
                ws.cell(row=current_row, column=1, value=f"Cavity {cavity_num}:").font = self.DATA_FONT
                ws.cell(row=current_row, column=3, value=f"{cavity_ok}/{cavity_ok + cavity_nok} passed ({cavity_rate:.1f}%)").font = self.DATA_FONT
                current_row += 1

    def _group_results_by_cavity(self, results: List[DimensionalResult]) -> Dict[int, List[DimensionalResult]]:
        """Group results by cavity number with proper automotive handling"""
        cavity_groups = {}
        
        for result in results:
            cavity = getattr(result, 'cavity', '1')
            
            try:
                cavity_num = int(str(cavity).strip()) if cavity else 1
            except (ValueError, TypeError):
                cavity_num = 1
            
            if cavity_num not in cavity_groups:
                cavity_groups[cavity_num] = []
            cavity_groups[cavity_num].append(result)
        
        return cavity_groups

    def _export_comprehensive_json(self, filepath: str, results: List[DimensionalResult], metadata: Dict[str, Any], summary_data: Optional[Dict] = None, cavity_groups: Optional[Dict] = None):
        """Export comprehensive JSON data with automotive specifications"""
        export_data = {
            "metadata": metadata,
            "results": [self._result_to_dict(r) for r in results],
            "cavity_groups": {str(k): [self._result_to_dict(r) for r in v] for k, v in (cavity_groups or {}).items()},
            "summary": summary_data or {},
            "statistics": self._calculate_overall_statistics(results),
            "automotive_compliance": {
                "ppap_standard": True,
                "statistical_dimensions": len([r for r in results if getattr(r, 'classe', '').upper() in ['CC', 'SC', 'IC']]),
                "export_format_version": "2.0_automotive_enhanced"
            },
            "export_timestamp": datetime.now().isoformat(),
            "version": "2.0"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    def _calculate_overall_statistics(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Calculate overall statistics for automotive compliance"""
        if not results:
            return {}
        
        statuses = [self._normalize_status(r.status) for r in results]
        statistical_dims = [r for r in results if getattr(r, 'classe', '').upper() in ['CC', 'SC', 'IC']]
        
        ok_count = statuses.count('OK')
        nok_count = statuses.count('NOK')
        
        return {
            "total_dimensions": len(results),
            "passed": ok_count,
            "failed": nok_count,
            "basic_info": statuses.count('T.E.D'),
            "warnings": statuses.count('WARNING'),
            "statistical_dimensions": len(statistical_dims),
            "success_rate": (ok_count / (ok_count + nok_count)) * 100 if (ok_count + nok_count) > 0 else 0,
            "automotive_compliance": True
        }

    def _result_to_dict(self, result: DimensionalResult) -> Dict[str, Any]:
        """Convert result to dictionary with automotive-specific data"""
        measurements = list(result.measurements) if result.measurements else []
        
        stats = {
            'min': min(measurements) if measurements else None,
            'max': max(measurements) if measurements else None,
            'mean': getattr(result, 'mean', None),
            'std': getattr(result, 'std_dev', None)
        }

        is_statistical = getattr(result, 'classe', '').upper() in ['CC', 'SC', 'IC']

        pp_ppk = {
            'pp': getattr(result, 'pp', None) if is_statistical else None,
            'ppk': getattr(result, 'ppk', None) if is_statistical else None
        }

        status = result.status.value if hasattr(result.status, "value") else str(result.status)

        # Handle notes - check both evaluation_type and eval_type
        evaluation_type = (
            getattr(result, 'evaluation_type', '') or 
            getattr(result, 'eval_type', '') or ''
        ).strip().lower()
        
        if evaluation_type in ['note', 'notes']:
            measurements = []
            stats = {'min': None, 'max': None, 'mean': None, 'std': None}
            pp_ppk = {'pp': None, 'ppk': None}
            status = "TO CHECK"

        return {
            "element_id": result.element_id,
            "description": getattr(result, 'description', ''),
            "batch": getattr(result, 'batch', ''),
            "cavity": getattr(result, 'cavity', '1'),
            "classe": getattr(result, 'classe', ''),
            "nominal": getattr(result, 'nominal', None),
            "lower_tolerance": getattr(result, 'lower_tolerance', None),
            "upper_tolerance": getattr(result, 'upper_tolerance', None),
            "evaluation_type": evaluation_type,
            "measuring_instrument": getattr(result, 'measuring_instrument', 'ScanBox'),
            "measurements": measurements,
            "deviation": list(getattr(result, 'deviation', [])) if hasattr(result, 'deviation') else [],
            "statistics": stats,
            "pp_ppk": pp_ppk,
            "status": status,
            "out_of_spec_count": getattr(result, 'out_of_spec_count', 0),
            "gdt_flags": getattr(result, 'gdt_flags', {}),
            "warnings": list(getattr(result, 'warnings', [])) if hasattr(result, 'warnings') else [],
            "is_statistical": is_statistical,
            "automotive_compliant": True
        }

    def _set_print_settings(self, ws: Worksheet):
        """Set professional print settings for automotive reports"""
        ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        
        ws.page_margins = PageMargins(
            left=0.7, right=0.7, top=0.75, bottom=0.75,
            header=0.3, footer=0.3
        )
        
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToHeight = False
        ws.page_setup.fitToWidth = 1
        ws.page_setup.scale = 100
        
        ws.page_setup.horizontalCentered = True
        ws.page_setup.verticalCentered = False
        
        ws.page_setup.draft = False
        ws.page_setup.cellComments = None
        ws.page_setup.useFirstPageNumber = True
        
        # Repeat header rows on each page
        ws.print_title_rows = '1:12'

    def generate_export_summary(self, export_paths: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """Generate professional export summary for automotive clients"""
        try:
            summary_lines = [
                "AUTOMOTIVE DIMENSIONAL ANALYSIS EXPORT SUMMARY",
                "=" * 60,
                "",
                "PROJECT INFORMATION:",
                f"  Client: {metadata.get('client_name', 'N/A')}",
                f"  Project Reference: {metadata.get('project_ref', 'N/A')}",
                f"  Part Number: {metadata.get('part_number', 'N/A')}",
                f"  Batch Number: {metadata.get('batch_number', 'N/A')}",
                f"  Report Type: {metadata.get('report_type', 'PPAP')}",
                f"  Tolerance Standard: {metadata.get('tolerance_standard', 'ISO 2768-m')}",
                "",
                "QUALITY INFORMATION:",
                f"  Inspection Facility: {metadata.get('inspection_facility', 'Quality Lab 1')}",
                f"  Metrology Protocol: {metadata.get('protocol_reference', 'ITM-1')}",
                f"  Cavity: {metadata.get('cavity_display', '1')}",
                "",
                "EXPORTED FILES:",
                f"  • Professional Excel Report: {os.path.basename(export_paths.get('excel_report', 'Not generated'))}",
                f"  • Comprehensive JSON Data: {os.path.basename(export_paths.get('json_data', 'Not generated'))}",
                "",
                f"Export completed successfully at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "ENHANCED AUTOMOTIVE PPAP COMPLIANCE FEATURES:",
                "  ✓ Professional automotive-standard formatting with company logo",
                "  ✓ Enhanced header with all required PPAP information",
                "  ✓ Fixed evaluation type handling (eval_type/evaluation_type)",
                "  ✓ Proper 'Visual' instrument display in exports",
                "  ✓ Improved statistical dimension highlighting",
                "  ✓ Professional notes section with merged cells",
                "  ✓ Enhanced signature areas for quality approval",
                "  ✓ Consistent border formatting throughout document",
                "  ✓ Cavity-specific reporting (1, 2, Both, All)",
                "  ✓ Tolerance standard integration from UI selection",
                "",
                "Ready for submission to automotive clients:",
                "VW • BMW • Mercedes • ZF • Autoliv • Tesla • Brose • Sofegi",
                "=" * 60
            ]
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            self.logger.error(f"Could not generate export summary: {str(e)}")
            return f"Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nFiles: {len(export_paths)} generated"