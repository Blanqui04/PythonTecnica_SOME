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
    """Optimized professional dimensional analysis export service for automotive PPAP reports"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_styles()
        
    def _init_styles(self):
        """Initialize Excel styling constants - optimized"""
        # Fonts
        self.HEADER_FONT = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        self.TITLE_FONT = Font(name='Arial', size=16, bold=True, color='2C3E50')
        self.SUBTITLE_FONT = Font(name='Arial', size=11, bold=True, color='34495E')
        self.DATA_FONT = Font(name='Arial', size=9)
        self.SMALL_FONT = Font(name='Arial', size=8)
        
        # Fills
        self.HEADER_FILL = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
        self.OK_FILL = PatternFill(start_color='D5F4E6', end_color='D5F4E6', fill_type='solid')
        self.NOK_FILL = PatternFill(start_color='FADBD8', end_color='FADBD8', fill_type='solid')
        self.TED_FILL = PatternFill(start_color='E8F4F8', end_color='E8F4F8', fill_type='solid')
        self.INFO_FILL = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
        
        # Borders
        self.THIN_BORDER = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        self.THICK_BORDER = Border(
            left=Side(style='thick'), right=Side(style='thick'),
            top=Side(style='thick'), bottom=Side(style='thick')
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
        """Main optimized export method"""
        try:
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_paths = {}

            # Enhance metadata with database info
            enhanced_metadata = self._enhance_metadata(metadata, db_config_path, db_key)
            
            # Sort and group results
            sorted_results = self._sort_results_by_element_id(results)
            cavity_groups = self._group_results_by_cavity(sorted_results)

            # Create Excel report
            excel_path = os.path.join(export_dir, f"{base_filename}_PPAP_REPORT_{timestamp}.xlsx")
            self._create_professional_excel_report(
                excel_path, 
                cavity_groups,
                enhanced_metadata,
                summary_data,
                logo_path
            )
            export_paths['excel_report'] = excel_path
            self.logger.info(f"📊 Professional Excel PPAP report created: {os.path.basename(excel_path)}")

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
            self.logger.info(f"📁 Comprehensive JSON exported: {os.path.basename(json_path)}")

            return export_paths

        except Exception as e:
            self.logger.error(f"❌ Export failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Export failed: {str(e)}") from e

    def _enhance_metadata(self, metadata: Dict[str, Any], db_config_path: Optional[str], db_key: str) -> Dict[str, Any]:
        """Enhance metadata with database information and fallbacks"""
        enhanced = {
            'client_name': metadata.get('client_name', ''),
            'project_ref': metadata.get('project_ref', ''),
            'part_number': metadata.get('project_ref', ''),  # Part number = project_ref
            'batch_number': metadata.get('batch_number', ''),
            'report_type': metadata.get('report_type', 'PPAP'),
            'drawing_number': '',
            'quotation_number': '',
            'project_leader_name': '',
            'project_leader_title': 'Quality Engineer',
            'quality_facility': '',
            'normative': 'ISO 2768-m',
            'inspector': '',
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Try to get database metadata
        if db_config_path and os.path.exists(db_config_path):
            try:
                with open(db_config_path, 'r') as f:
                    db_config = json.load(f)
                
                conn_config = db_config.get(db_key, {})
                if conn_config:
                    db_metadata = self._fetch_database_metadata(conn_config, enhanced)
                    enhanced.update(db_metadata)
            except Exception as e:
                self.logger.warning(f"Could not enhance metadata from database: {e}")
        
        return enhanced

    def _fetch_database_metadata(self, conn_config: Dict, base_metadata: Dict) -> Dict[str, Any]:
        """Fetch metadata from database with error handling"""
        try:
            db = PostgresConn(
                host=conn_config["host"],
                database=conn_config["database"],
                user=conn_config["user"],
                password=conn_config["password"],
                port=conn_config.get("port", 5432)
            )

            # Try multiple table structures
            queries = [
                """SELECT part_number, drawing_number, quotation_number, 
                         project_leader_name, project_leader_title, quality_facility, 
                         normative, inspector
                  FROM project_metadata 
                  WHERE project_ref = %s OR part_number = %s
                  ORDER BY updated_at DESC LIMIT 1""",
                
                """SELECT part_number, drawing_number, quotation_number, 
                         project_leader, '' as title, quality_facility, 
                         normative, inspector
                  FROM projects 
                  WHERE project_ref = %s OR part_number = %s
                  ORDER BY created_at DESC LIMIT 1"""
            ]

            project_ref = base_metadata.get('project_ref', '')
            
            for query in queries:
                try:
                    row = db.fetchone(query, (project_ref, project_ref))
                    if row:
                        return {
                            'part_number': row[0] or base_metadata['part_number'],
                            'drawing_number': row[1] or '',
                            'quotation_number': row[2] or '',
                            'project_leader_name': row[3] or '',
                            'project_leader_title': row[4] or 'Quality Engineer',
                            'quality_facility': row[5] or '',
                            'normative': row[6] or 'ISO 2768-m',
                            'inspector': row[7] or ''
                        }
                except Exception:
                    continue

            db.close()
            
        except Exception as e:
            self.logger.warning(f"Database metadata fetch failed: {e}")
        
        return {}

    def _create_professional_excel_report(
        self,
        filepath: str,
        cavity_groups: Dict[int, List[DimensionalResult]],
        metadata: Dict[str, Any],
        summary_data: Optional[Dict] = None,
        logo_path: Optional[str] = None
    ):
        """Create professional Excel workbook optimized for automotive PPAP"""
        wb = Workbook()
        
        # Remove default sheet
        if wb.active:
            wb.remove(wb.active)
        
        # Create main report sheet
        main_sheet = wb.create_sheet("PPAP Dimensional Report")
        self._create_main_report_sheet(main_sheet, cavity_groups, metadata, logo_path)
        
        # Create cavity-specific sheets if multiple cavities
        if len(cavity_groups) > 1:
            for cavity_num in sorted(cavity_groups.keys()):
                cavity_sheet = wb.create_sheet(f"Cavity {cavity_num}")
                self._create_cavity_specific_sheet(
                    cavity_sheet, 
                    cavity_groups[cavity_num], 
                    cavity_num, 
                    metadata, 
                    logo_path
                )
        
        # Create summary sheet
        if summary_data:
            summary_sheet = wb.create_sheet("Analysis Summary")
            self._create_summary_sheet(summary_sheet, cavity_groups, metadata, summary_data)
        
        # Create metadata sheet
        metadata_sheet = wb.create_sheet("Report Metadata")
        self._create_metadata_sheet(metadata_sheet, metadata, summary_data)
        
        # Set print settings for all sheets
        for sheet in wb.worksheets:
            self._set_print_settings(sheet)
        
        wb.save(filepath)

    def _create_main_report_sheet(
        self,
        ws: Worksheet,
        cavity_groups: Dict[int, List[DimensionalResult]],
        metadata: Dict[str, Any],
        logo_path: Optional[str] = None
    ):
        """Create main PPAP report sheet with professional header and data"""
        current_row = 1
        
        # Add professional header
        current_row = self._add_ppap_header(ws, metadata, current_row, logo_path)
        current_row += 2
        
        # Add dimensional data table
        all_results = []
        for cavity_results in cavity_groups.values():
            all_results.extend(cavity_results)
        
        current_row = self._add_dimensional_data_table(ws, all_results, current_row)
        current_row += 3
        
        # Add professional footer
        self._add_ppap_footer(ws, metadata, current_row)
        
        # Apply formatting
        self._apply_professional_formatting(ws)

    def _add_ppap_header(
        self, 
        ws: Worksheet, 
        metadata: Dict[str, Any], 
        start_row: int, 
        logo_path: Optional[str] = None
    ) -> int:
        """Add professional PPAP header"""
        current_row = start_row
        
        # Logo and title row
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path)
                img.height = 50
                img.width = 100
                ws.add_image(img, f'A{current_row}')
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")
        
        # Main title
        ws.merge_cells(f'E{current_row}:M{current_row}')
        title_cell = ws.cell(row=current_row, column=5, value="DIMENSIONAL ANALYSIS REPORT")
        title_cell.font = self.TITLE_FONT
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Report type
        ws.merge_cells(f'N{current_row}:Q{current_row}')
        type_cell = ws.cell(row=current_row, column=14, value=f"{metadata.get('report_type', 'PPAP')} REPORT")
        type_cell.font = Font(name='Arial', size=12, bold=True, color='E74C3C')
        type_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        current_row += 3
        
        # Information table
        info_data = [
            ('Client / Supplier:', metadata.get('client_name', ''), 'Part Number:', metadata.get('part_number', '')),
            ('Drawing Number:', metadata.get('drawing_number', ''), 'Batch Number:', metadata.get('batch_number', '')),
            ('Project Reference:', metadata.get('project_ref', ''), 'Report Date:', metadata.get('report_date', '')),
            ('Quality Facility:', metadata.get('quality_facility', ''), 'Normative:', metadata.get('normative', 'ISO 2768-m')),
            ('Project Leader:', metadata.get('project_leader_name', ''), 'Inspector:', metadata.get('inspector', ''))
        ]
        
        for left_label, left_value, right_label, right_value in info_data:
            # Left side
            ws.cell(row=current_row, column=1, value=left_label).font = self.SUBTITLE_FONT
            ws.merge_cells(f'B{current_row}:H{current_row}')
            ws.cell(row=current_row, column=2, value=left_value).font = self.DATA_FONT
            
            # Right side  
            ws.cell(row=current_row, column=10, value=right_label).font = self.SUBTITLE_FONT
            ws.merge_cells(f'K{current_row}:Q{current_row}')
            ws.cell(row=current_row, column=11, value=right_value).font = self.DATA_FONT
            
            # Apply borders
            for col in range(1, 18):
                ws.cell(row=current_row, column=col).border = self.THIN_BORDER
            
            current_row += 1
        
        return current_row

    def _add_dimensional_data_table(self, ws: Worksheet, results: List[DimensionalResult], start_row: int) -> int:
        """Add optimized dimensional data table"""
        current_row = start_row
        
        # Table headers
        headers = [
            'Element ID', 'Description', 'Nominal', 'Lower Spec', 'Upper Spec',
            'Unit', 'Instrument', 'M1', 'M2', 'M3', 'M4', 'M5',
            'Min', 'Max', 'Mean', 'Std Dev', 'Status'
        ]
        
        # Write headers with styling
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = self.THICK_BORDER
        
        ws.row_dimensions[current_row].height = 35
        current_row += 1
        
        # Write data rows
        for result in results:
            self._add_data_row(ws, current_row, result, len(headers))
            current_row += 1
        
        # Auto-size columns
        self._auto_size_columns(ws, len(headers))
        
        return current_row

    def _add_data_row(self, ws: Worksheet, row: int, result: DimensionalResult, num_columns: int):
        """Add optimized data row with proper formatting and TED/alternate-row support"""
        # Determine if it's a TED row
        is_ted = self._get_status_display_safe(result) == 'T.E.D'

        # Calculate statistics
        measurements = [m for m in result.measurements if m is not None]
        stats = self._calculate_statistics(measurements)

        # Get spec limits (unless TED)
        lower_spec, upper_spec = (None, None) if is_ted else self._get_spec_limits_safe(result)

        # Format values
        data = [
            result.element_id,
            getattr(result, 'description', ''),
            '' if is_ted else self._format_number(getattr(result, 'nominal', None)),
            '' if is_ted else self._format_number(lower_spec),
            '' if is_ted else self._format_number(upper_spec),
            self._format_unit(getattr(result, 'unit', '')),
            self._format_instrument(getattr(result, 'measuring_instrument', '')),
            *[self._format_number(m) for m in (result.measurements + [None] * 5)[:5]],
            self._format_number(stats['min']),
            self._format_number(stats['max']),
            self._format_number(stats['mean']),
            self._format_number(stats['std']),
            self._get_status_display_safe(result)
        ]

        # Alternate row fill (only for non-status cells)
        alt_fill = PatternFill(start_color='FBFBFB', end_color='FBFBFB', fill_type='solid') if row % 2 == 0 else None
        ted_font = Font(name='Arial', size=9, italic=True, color='7F8C8D') if is_ted else self.DATA_FONT

        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = ted_font if col < num_columns else self.DATA_FONT  # Apply TED color except to status cell
            cell.border = self.THIN_BORDER
            cell.alignment = Alignment(horizontal='center', vertical='center')

            # Status cell (last)
            if col == num_columns:
                self._apply_status_formatting(cell, data[-1])
            elif not is_ted and alt_fill:
                cell.fill = alt_fill


    def _calculate_statistics(self, measurements: List[float]) -> Dict[str, Optional[float]]:
        """Calculate statistics with error handling"""
        if not measurements:
            return {'min': None, 'max': None, 'mean': None, 'std': None}
        
        try:
            mean_val = sum(measurements) / len(measurements)
            std_val = None
            if len(measurements) > 1:
                variance = sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)
                std_val = variance ** 0.5
            
            return {
                'min': min(measurements),
                'max': max(measurements),
                'mean': mean_val,
                'std': std_val
            }
        except Exception:
            return {'min': None, 'max': None, 'mean': None, 'std': None}

    def _get_spec_limits_safe(self, result: DimensionalResult) -> Tuple[Optional[float], Optional[float]]:
        """Get specification limits with comprehensive error handling"""
        try:
            # Try explicit tolerances first
            lower = getattr(result, 'lower_tolerance', None)
            upper = getattr(result, 'upper_tolerance', None)
            if lower is not None and upper is not None:
                return float(lower), float(upper)
            
            # Try nominal ± tolerance
            nominal = getattr(result, 'nominal', None)
            if nominal is not None:
                plus_tol = getattr(result, 'plus_tolerance', 0) or 0
                minus_tol = getattr(result, 'minus_tolerance', 0) or 0
                return float(nominal) - abs(float(minus_tol)), float(nominal) + abs(float(plus_tol))
            
        except (ValueError, TypeError, AttributeError):
            pass
        
        return None, None
    
    def _format_unit(self, unit: Optional[str]) -> str:
        """Format unit consistently and smartly"""
        if not unit:
            return ''
        u = str(unit).strip().lower()
        if 'µ' in u or 'micro' in u or 'um' in u or 'μ' in u:
            return 'μm'
        if 'deg' in u or '°' in u or 'º' in u:
            return 'º'
        return unit

    def _format_instrument(self, instrument: Optional[str]) -> str:
        """Respect actual instrument name or leave blank"""
        if not instrument:
            return ''
        i = str(instrument).strip()
        return i.capitalize() if i.lower() == 'visual' else i

    def _get_status_display_safe(self, result: DimensionalResult) -> str:
        """Get status display with robust error handling and TED detection"""
        try:
            raw_status = str(getattr(result, 'status', '')).strip().upper()
            if hasattr(result.status, 'value'):
                raw_status = str(result.status.value).strip().upper()
        except AttributeError:
            raw_status = ''

        description = str(getattr(result, 'description', '')).lower()

        if 'ted' in raw_status or 't.e.d' in raw_status:
            return 'T.E.D'
        if any(keyword in description for keyword in ['basic', 'informative', 'reference', 'ref', 't.e.d']):
            return 'T.E.D'

        status_map = {
            'GOOD': 'OK', 'PASS': 'OK', 'OK': 'OK',
            'BAD': 'NOK', 'FAIL': 'NOK', 'NOK': 'NOK', 'NG': 'NOK',
            'WARNING': 'WARNING', 'T.E.D.': 'T.E.D', 'TED': 'T.E.D'
        }

        return status_map.get(raw_status, 'WARNING')


    def _format_number(self, value) -> str:
        """Format numbers consistently"""
        try:
            if value is None:
                return ''
            num = float(value)
            return f"{num:.3f}" if abs(num) < 1 else f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value) if value is not None else ''

    def _apply_status_formatting(self, cell, status: str):
        """Apply status-based formatting"""
        status_formats = {
            'OK': (self.OK_FILL, Font(name='Arial', size=9, bold=True, color='27AE60')),
            'NOK': (self.NOK_FILL, Font(name='Arial', size=9, bold=True, color='E74C3C')),
            'T.E.D': (self.TED_FILL, Font(name='Arial', size=9, bold=True, color='3498DB')),
            'WARNING': (PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid'), 
                       Font(name='Arial', size=9, bold=True, color='856404'))
        }
        
        if status in status_formats:
            fill, font = status_formats[status]
            cell.fill = fill
            cell.font = font

    def _add_ppap_footer(self, ws: Worksheet, metadata: Dict[str, Any], start_row: int):
        """Add professional PPAP footer with signatures"""
        current_row = start_row
        
        # Notes section
        ws.merge_cells(f'A{current_row}:Q{current_row}')
        notes_cell = ws.cell(row=current_row, column=1, value="NOTES / OBSERVATIONS:")
        notes_cell.font = self.SUBTITLE_FONT
        notes_cell.border = self.THIN_BORDER
        current_row += 1
        
        # Notes box (4 rows)
        for i in range(4):
            for col in range(1, 18):
                cell = ws.cell(row=current_row, column=col, value='')
                cell.border = self.THIN_BORDER
            ws.row_dimensions[current_row].height = 20
            current_row += 1
        
        current_row += 1
        
        # Signature section
        # Project Leader
        ws.cell(row=current_row, column=2, value="PROJECT LEADER:").font = self.SUBTITLE_FONT
        ws.cell(row=current_row + 1, column=2, value=metadata.get('project_leader_name', '')).font = self.DATA_FONT
        ws.cell(row=current_row + 2, column=2, value=metadata.get('project_leader_title', 'Quality Engineer')).font = self.SMALL_FONT
        ws.cell(row=current_row + 3, column=2, value="Signature: _________________").font = self.DATA_FONT
        
        # Date
        ws.cell(row=current_row, column=12, value="DATE:").font = self.SUBTITLE_FONT
        ws.cell(row=current_row + 1, column=12, value=metadata.get('report_date', '')).font = self.DATA_FONT

    def _create_cavity_specific_sheet(
        self,
        ws: Worksheet,
        cavity_results: List[DimensionalResult],
        cavity_num: int,
        metadata: Dict[str, Any],
        logo_path: Optional[str] = None
    ):
        """Create cavity-specific sheet"""
        cavity_metadata = {**metadata, 'title_suffix': f" - Cavity {cavity_num}"}
        
        current_row = 1
        current_row = self._add_ppap_header(ws, cavity_metadata, current_row, logo_path)
        current_row += 2
        current_row = self._add_dimensional_data_table(ws, cavity_results, current_row)
        current_row += 3
        self._add_ppap_footer(ws, metadata, current_row)
        self._apply_professional_formatting(ws)

    def _create_summary_sheet(
        self,
        ws: Worksheet,
        cavity_groups: Dict[int, List[DimensionalResult]],
        metadata: Dict[str, Any],
        summary_data: Dict[str, Any]
    ):
        """Create professional summary sheet"""
        current_row = 1
        
        # Title
        ws.merge_cells(f'A{current_row}:H{current_row}')
        title = ws.cell(row=current_row, column=1, value="DIMENSIONAL ANALYSIS SUMMARY")
        title.font = self.TITLE_FONT
        title.alignment = Alignment(horizontal='center')
        current_row += 3
        
        # Calculate overall statistics
        all_results = []
        for cavity_results in cavity_groups.values():
            all_results.extend(cavity_results)
        
        total_dims = len(all_results)
        ok_count = sum(1 for r in all_results if self._get_status_display_safe(r) == 'OK')
        nok_count = sum(1 for r in all_results if self._get_status_display_safe(r) == 'NOK')
        ted_count = sum(1 for r in all_results if self._get_status_display_safe(r) == 'T.E.D')
        success_rate = (ok_count / (ok_count + nok_count)) * 100 if (ok_count + nok_count) > 0 else 0
        
        # Overall statistics
        stats = [
            ('Total Dimensions:', total_dims),
            ('Passed (OK):', ok_count),
            ('Failed (NOK):', nok_count),
            ('Basic/Info (T.E.D):', ted_count),
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
                cavity_ok = sum(1 for r in cavity_results if self._get_status_display_safe(r) == 'OK')
                cavity_nok = sum(1 for r in cavity_results if self._get_status_display_safe(r) == 'NOK')
                cavity_rate = (cavity_ok / (cavity_ok + cavity_nok)) * 100 if (cavity_ok + cavity_nok) > 0 else 0
                
                ws.cell(row=current_row, column=1, value=f"Cavity {cavity_num}:").font = self.DATA_FONT
                ws.cell(row=current_row, column=3, value=f"{cavity_ok}/{cavity_ok + cavity_nok} passed ({cavity_rate:.1f}%)").font = self.DATA_FONT
                current_row += 1

    def _create_metadata_sheet(self, ws: Worksheet, metadata: Dict[str, Any], summary_data: Optional[Dict]):
        """Create metadata sheet"""
        current_row = 1
        
        ws.merge_cells(f'A{current_row}:B{current_row}')
        title = ws.cell(row=current_row, column=1, value="REPORT METADATA")
        title.font = self.TITLE_FONT
        current_row += 3
        
        # Metadata sections
        sections = [
            ("Project Information", [
                ("Client Name", metadata.get('client_name', '')),
                ("Project Reference", metadata.get('project_ref', '')),
                ("Part Number", metadata.get('part_number', '')),
                ("Drawing Number", metadata.get('drawing_number', '')),
                ("Batch Number", metadata.get('batch_number', '')),
                ("Report Type", metadata.get('report_type', 'PPAP'))
            ]),
            ("Quality Information", [
                ("Project Leader", metadata.get('project_leader_name', '')),
                ("Project Leader Title", metadata.get('project_leader_title', '')),
                ("Quality Facility", metadata.get('quality_facility', '')),
                ("Inspector", metadata.get('inspector', '')),
                ("Normative Standard", metadata.get('normative', 'ISO 2768-m'))
            ]),
            ("Export Information", [
                ("Export Date", metadata.get('report_date', '')),
                ("Export Timestamp", metadata.get('export_timestamp', '')),
                ("Software Version", "2.0")
            ])
        ]
        
        for section_title, section_data in sections:
            ws.cell(row=current_row, column=1, value=section_title).font = self.SUBTITLE_FONT
            current_row += 1
            
            for label, value in section_data:
                ws.cell(row=current_row, column=1, value=label).font = self.DATA_FONT
                ws.cell(row=current_row, column=2, value=value).font = self.DATA_FONT
                current_row += 1
            
            current_row += 1

    def _export_comprehensive_json(
        self,
        filepath: str,
        results: List[DimensionalResult],
        metadata: Dict[str, Any],
        summary_data: Optional[Dict] = None,
        cavity_groups: Optional[Dict] = None
    ):
        """Export comprehensive JSON data"""
        export_data = {
            "metadata": metadata,
            "results": [self._result_to_dict(r) for r in results],
            "cavity_groups": {str(k): [self._result_to_dict(r) for r in v] for k, v in (cavity_groups or {}).items()},
            "summary": summary_data or {},
            "statistics": self._calculate_overall_statistics(results),
            "export_timestamp": datetime.now().isoformat(),
            "version": "2.0"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    def _calculate_overall_statistics(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Calculate overall statistics for JSON export"""
        if not results:
            return {}
        
        statuses = [self._get_status_display_safe(r) for r in results]
        
        return {
            "total_dimensions": len(results),
            "passed": statuses.count('OK'),
            "failed": statuses.count('NOK'),
            "basic_info": statuses.count('T.E.D'),
            "warnings": statuses.count('WARNING'),
            "success_rate": (statuses.count('OK') / (statuses.count('OK') + statuses.count('NOK'))) * 100 if (statuses.count('OK') + statuses.count('NOK')) > 0 else 0
        }

    def _apply_professional_formatting(self, ws: Worksheet):
        """Apply professional formatting to worksheet"""
        # Set column widths for readability
        column_widths = {
            'A': 12, 'B': 25, 'C': 10, 'D': 10, 'E': 10, 'F': 8, 'G': 15,
            'H': 8, 'I': 8, 'J': 8, 'K': 8, 'L': 8, 'M': 8, 'N': 8, 'O': 8, 'P': 10, 'Q': 10
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    def _auto_size_columns(self, ws: Worksheet, num_columns: int):
        """Auto-size columns with limits"""
        for col_num in range(1, num_columns + 1):
            column_letter = get_column_letter(col_num)
            max_length = 8  # Minimum width
            
            for row in ws.iter_rows(min_col=col_num, max_col=col_num):
                for cell in row:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
            
            # Set width with reasonable limits
            adjusted_width = min(max_length + 2, 30)  # Max 30 characters
            ws.column_dimensions[column_letter].width = adjusted_width

    def _set_print_settings(self, ws: Worksheet):
        """Set professional print settings"""
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToHeight = False
        ws.page_setup.fitToWidth = 1
        
        # Set margins
        ws.page_margins = PageMargins(
            left=0.5, right=0.5, top=0.75, bottom=0.75, 
            header=0.3, footer=0.3
        )
        
        # Print titles (repeat first row on each page)
        ws.print_title_rows = '1:1'

    def _sort_results_by_element_id(self, results: List[DimensionalResult]) -> List[DimensionalResult]:
        """Sort element_id with numeric awareness (e.g. Nº1000 > Nº200)"""
        def parse_numeric(eid: str) -> Tuple[int, str]:
            eid = str(eid)
            # Remove prefix like 'Nº' or 'No.' etc.
            cleaned = re.sub(r'^(Nº|No\.?)\s*', '', eid, flags=re.IGNORECASE)
            try:
                return (0, int(cleaned))  # numeric ID
            except ValueError:
                return (1, eid)  # fallback string

        return sorted(results, key=lambda r: parse_numeric(r.element_id))

    def _group_results_by_cavity(self, results: List[DimensionalResult]) -> Dict[int, List[DimensionalResult]]:
        """Group results by cavity number with fallback"""
        cavity_groups = {}
        
        for result in results:
            cavity = getattr(result, 'cavity', 1) or 1  # Default to cavity 1
            if cavity not in cavity_groups:
                cavity_groups[cavity] = []
            cavity_groups[cavity].append(result)
        
        return cavity_groups

    def _result_to_dict(self, result: DimensionalResult) -> Dict[str, Any]:
        """Convert result to dictionary with comprehensive data"""
        measurements = list(result.measurements) if result.measurements else []
        stats = self._calculate_statistics([m for m in measurements if m is not None])
        
        return {
            "element_id": result.element_id,
            "description": getattr(result, 'description', ''),
            "class": getattr(result, 'class', ''),
            "nominal": getattr(result, 'nominal', None),
            "lower_tolerance": getattr(result, 'lower_tolerance', None),
            "upper_tolerance": getattr(result, 'upper_tolerance', None),
            "plus_tolerance": getattr(result, 'plus_tolerance', None),
            "minus_tolerance": getattr(result, 'minus_tolerance', None),
            "measuring_instrument": getattr(result, 'measuring_instrument', 'ScanBox'),
            "unit": getattr(result, 'unit', 'mm'),
            "status": str(getattr(result, 'status', 'NOK')),
            "status_display": self._get_status_display_safe(result),
            "measurements": measurements,
            "statistics": stats,
            "cavity": getattr(result, 'cavity', 1),
            "spec_limits": {
                "lower": self._get_spec_limits_safe(result)[0],
                "upper": self._get_spec_limits_safe(result)[1]
            }
        }

    def generate_export_summary(self, export_paths: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """Generate professional export summary"""
        try:
            summary_lines = [
                "DIMENSIONAL ANALYSIS EXPORT SUMMARY",
                "=" * 50,
                "",
                "PROJECT INFORMATION:",
                f"  Client: {metadata.get('client_name', 'N/A')}",
                f"  Project Reference: {metadata.get('project_ref', 'N/A')}",
                f"  Part Number: {metadata.get('part_number', 'N/A')}",
                f"  Batch Number: {metadata.get('batch_number', 'N/A')}",
                f"  Report Type: {metadata.get('report_type', 'PPAP')}",
                "",
                "QUALITY INFORMATION:",
                f"  Project Leader: {metadata.get('project_leader_name', 'N/A')}",
                f"  Quality Facility: {metadata.get('quality_facility', 'N/A')}",
                f"  Normative Standard: {metadata.get('normative', 'ISO 2768-m')}",
                "",
                "EXPORTED FILES:",
                f"  • Professional Excel Report: {os.path.basename(export_paths.get('excel_report', 'Not generated'))}",
                f"  • Comprehensive JSON Data: {os.path.basename(export_paths.get('json_data', 'Not generated'))}",
                "",
                f"Export completed successfully at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "The Excel report includes:",
                "  - Professional PPAP-compliant header with company information",
                "  - Complete dimensional analysis data table",
                "  - Cavity-specific sheets (if multiple cavities)",
                "  - Comprehensive analysis summary",
                "  - Detailed metadata for traceability",
                "  - Professional footer with signature areas",
                "",
                "Ready for client presentation and regulatory submission.",
                "=" * 50
            ]
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            self.logger.error(f"Could not generate export summary: {str(e)}")
            return f"Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nFiles: {len(export_paths)} generated"