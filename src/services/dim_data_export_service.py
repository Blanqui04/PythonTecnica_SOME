# src/services/enhanced_data_export_service.py
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
# from openpyxl.drawing.image import Image
# from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.worksheet import Worksheet
from src.models.dimensional.dimensional_result import DimensionalResult


class DataExportService:
    """Enhanced service for exporting dimensional analysis results with professional Excel reports"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Report styling constants
        self.HEADER_FONT = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        self.TITLE_FONT = Font(name='Arial', size=16, bold=True, color='2C3E50')
        self.SUBTITLE_FONT = Font(name='Arial', size=11, bold=True, color='34495E')
        self.DATA_FONT = Font(name='Arial', size=10)
        self.SMALL_FONT = Font(name='Arial', size=8)
        
        self.HEADER_FILL = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
        self.GOOD_FILL = PatternFill(start_color='D5F4E6', end_color='D5F4E6', fill_type='solid')
        self.BAD_FILL = PatternFill(start_color='FADBD8', end_color='FADBD8', fill_type='solid')
        self.WARNING_FILL = PatternFill(start_color='FCF3CF', end_color='FCF3CF', fill_type='solid')
        
        self.THIN_BORDER = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        self.THICK_BORDER = Border(
            left=Side(style='thick'), right=Side(style='thick'),
            top=Side(style='thick'), bottom=Side(style='thick')
        )

    def export_comprehensive_results(
        self, 
        results: List[DimensionalResult],
        export_dir: str,
        base_filename: str,
        metadata: Dict[str, Any],
        summary_data: Optional[Dict] = None,
        table_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, str]:
        """
        Export comprehensive results including Excel report, JSON, CSV, and by-cavity analysis
        
        Args:
            results: List of DimensionalResult objects
            export_dir: Directory to save files
            base_filename: Base filename without extension
            metadata: Report metadata (client, project, batch, etc.)
            summary_data: Summary widget data
            table_data: Original table data
            
        Returns:
            Dict with paths to created files
        """
        if not results:
            raise ValueError("No results to export")

        # Ensure export directory exists
        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        export_paths = {}
        
        try:
            self.logger.info(f"🚀 Starting comprehensive export to {export_dir}")
            
            # 1. Create Excel Report (Priority)
            excel_path = os.path.join(export_dir, f"{base_filename}_REPORT_{timestamp}.xlsx")
            self._create_excel_report(excel_path, results, metadata, summary_data, table_data)
            export_paths['excel_report'] = excel_path
            
            # 2. Export by Cavity (JSON and CSV)
            cavity_paths = self._export_by_cavity(export_dir, base_filename, timestamp, results, table_data)
            export_paths.update(cavity_paths)
            
            # 3. Export comprehensive JSON
            json_path = os.path.join(export_dir, f"{base_filename}_complete_{timestamp}.json")
            self._export_comprehensive_json(json_path, results, metadata, summary_data, table_data)
            export_paths['comprehensive_json'] = json_path
            
            # 4. Export summary CSV
            csv_path = os.path.join(export_dir, f"{base_filename}_summary_{timestamp}.csv")
            self._export_summary_csv(csv_path, results, metadata)
            export_paths['summary_csv'] = csv_path
            
            # 5. Export metadata sheet (separate)
            metadata_path = os.path.join(export_dir, f"{base_filename}_metadata_{timestamp}.xlsx")
            self._create_metadata_workbook(metadata_path, metadata, summary_data)
            export_paths['metadata'] = metadata_path
            
            self.logger.info(f"✅ Comprehensive export completed - {len(export_paths)} files created")
            return export_paths
            
        except Exception as e:
            self.logger.error(f"❌ Export failed: {str(e)}", exc_info=True)
            raise

    def _create_excel_report(
        self, 
        filepath: str, 
        results: List[DimensionalResult],
        metadata: Dict[str, Any],
        summary_data: Optional[Dict] = None,
        table_data: Optional[pd.DataFrame] = None
    ):
        """Create professional Excel report with company header and cavity separation"""
        wb = Workbook()
        
        # Group results by cavity
        cavity_groups = self._group_results_by_cavity(results)
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create summary sheet first
        self._create_summary_sheet(wb, results, metadata, summary_data)
        
        # Create cavity sheets
        for cavity_num in sorted(cavity_groups.keys()):
            cavity_results = cavity_groups[cavity_num]
            sheet_name = f"Cavity_{cavity_num}"
            self._create_cavity_report_sheet(wb, sheet_name, cavity_results, metadata, cavity_num)
        
        # Create combined overview if multiple cavities
        if len(cavity_groups) > 1:
            self._create_combined_overview_sheet(wb, results, metadata)
        
        wb.save(filepath)
        self.logger.info(f"📊 Excel report created: {os.path.basename(filepath)}")

    def _create_cavity_report_sheet(
        self, 
        wb: Workbook, 
        sheet_name: str, 
        cavity_results: List[DimensionalResult],
        metadata: Dict[str, Any],
        cavity_num: int
    ):
        """Create individual cavity report sheet with professional formatting"""
        ws = wb.create_sheet(sheet_name)
        current_row = 1
        
        # Company Header Section
        current_row = self._add_company_header(ws, metadata, cavity_num, current_row)
        current_row += 2
        
        # Data Table Header
        headers = [
            'Element ID', 'Description', 'Measuring Instrument', 
            'Measure 1', 'Measure 2', 'Measure 3', 'Measure 4', 'Measure 5',
            'Min', 'Max', 'Mean', 'Std Dev', 'Nominal', 'Lower Tol', 'Upper Tol', 'Status'
        ]
        
        # Apply header styling
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
        
        current_row += 1
        
        # Data rows
        for result in cavity_results:
            self._add_result_row(ws, current_row, result)
            current_row += 1
        
        # Add spacing and comments section
        current_row += 3
        self._add_comments_section(ws, current_row, metadata)
        
        # Auto-adjust column widths
        self._adjust_column_widths(ws)
        
        # Add conditional formatting for status
        self._apply_status_formatting(ws, len(cavity_results) + 1, len(headers))

    def _add_company_header(self, ws: Worksheet, metadata: Dict[str, Any], cavity_num: int, start_row: int) -> int:
        """Add professional company header with metadata"""
        current_row = start_row
        
        # Main title
        title_cell = ws.cell(row=current_row, column=1, value="DIMENSIONAL ANALYSIS REPORT")
        title_cell.font = self.TITLE_FONT
        title_cell.alignment = Alignment(horizontal='center')
        ws.merge_cells(f'A{current_row}:P{current_row}')
        current_row += 2
        
        # Company info section (2 columns layout)
        info_data = [
            ('Client:', metadata.get('client_name', 'N/A'), 'Project:', metadata.get('project_ref', 'N/A')),
            ('Part Number:', metadata.get('part_number', 'N/A'), 'Drawing Number:', metadata.get('drawing_number', 'N/A')),
            ('Batch Number:', metadata.get('batch_number', 'N/A'), 'Cavity Analyzed:', f"Cavity {cavity_num}"),
            ('Project Leader:', metadata.get('project_leader', 'N/A'), 'Inspector:', metadata.get('inspector', 'N/A')),
            ('Quality Facility:', metadata.get('quality_facility', 'N/A'), 'Date:', datetime.now().strftime('%Y-%m-%d')),
            ('Normative:', metadata.get('normative', 'ISO 1101'), 'Report Type:', metadata.get('report_type', 'Standard')),
        ]
        
        for left_label, left_value, right_label, right_value in info_data:
            # Left side
            label_cell = ws.cell(row=current_row, column=1, value=left_label)
            label_cell.font = self.SUBTITLE_FONT
            value_cell = ws.cell(row=current_row, column=2, value=left_value)
            value_cell.font = self.DATA_FONT
            
            # Right side
            label_cell_r = ws.cell(row=current_row, column=9, value=right_label)
            label_cell_r.font = self.SUBTITLE_FONT
            value_cell_r = ws.cell(row=current_row, column=10, value=right_value)
            value_cell_r.font = self.DATA_FONT
            
            current_row += 1
        
        return current_row

    def _add_result_row(self, ws: Worksheet, row: int, result: DimensionalResult):
        """Add a result data row to the worksheet"""
        # Calculate statistics
        measurements = [m for m in result.measurements if m is not None]
        min_val = min(measurements) if measurements else None
        max_val = max(measurements) if measurements else None
        mean_val = sum(measurements) / len(measurements) if measurements else None
        
        # Calculate standard deviation
        std_val = None
        if measurements and len(measurements) > 1:
            variance = sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)
            std_val = variance ** 0.5
        
        # Data values
        data = [
            result.element_id,
            result.description,
            getattr(result, 'measuring_instrument', 'N/A'),
            *[f"{m:.4f}" if m is not None else '' for m in result.measurements[:5]],
            f"{min_val:.4f}" if min_val is not None else '',
            f"{max_val:.4f}" if max_val is not None else '',
            f"{mean_val:.4f}" if mean_val is not None else '',
            f"{std_val:.4f}" if std_val is not None else '',
            f"{result.nominal:.4f}" if result.nominal is not None else '',
            f"{result.lower_tolerance:.4f}" if result.lower_tolerance is not None else '',
            f"{result.upper_tolerance:.4f}" if result.upper_tolerance is not None else '',
            result.status.value if hasattr(result.status, 'value') else str(result.status)
        ]
        
        # Add data to cells
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = self.DATA_FONT
            cell.border = self.THIN_BORDER
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Apply status-based formatting for the status column
            if col == len(data):  # Status column
                status = result.status.value if hasattr(result.status, 'value') else str(result.status)
                if status == 'GOOD':
                    cell.fill = self.GOOD_FILL
                elif status == 'BAD':
                    cell.fill = self.BAD_FILL
                elif status == 'WARNING':
                    cell.fill = self.WARNING_FILL

    def _add_comments_section(self, ws: Worksheet, start_row: int, metadata: Dict[str, Any]):
        """Add comments and signature section"""
        current_row = start_row
        
        # Comments header
        comments_header = ws.cell(row=current_row, column=1, value="COMMENTS / OBSERVATIONS:")
        comments_header.font = self.SUBTITLE_FONT
        ws.merge_cells(f'A{current_row}:P{current_row}')
        current_row += 1
        
        # Comments box (merge several rows and columns)
        for i in range(5):  # 5 rows for comments
            ws.merge_cells(f'A{current_row}:P{current_row}')
            comment_cell = ws.cell(row=current_row, column=1, value='')
            comment_cell.border = self.THIN_BORDER
            current_row += 1
        
        current_row += 2
        
        # Signature section
        signature_data = [
            ('Project Leader:', metadata.get('project_leader', ''), 'Signature:', ''),
            ('Inspector:', metadata.get('inspector', ''), 'Date:', datetime.now().strftime('%Y-%m-%d')),
        ]
        
        for left_label, left_value, right_label, right_value in signature_data:
            # Left side
            label_cell = ws.cell(row=current_row, column=1, value=left_label)
            label_cell.font = self.SUBTITLE_FONT
            value_cell = ws.cell(row=current_row, column=4, value=left_value)
            value_cell.font = self.DATA_FONT
            
            # Right side
            label_cell_r = ws.cell(row=current_row, column=9, value=right_label)
            label_cell_r.font = self.SUBTITLE_FONT
            value_cell_r = ws.cell(row=current_row, column=12, value=right_value)
            value_cell_r.font = self.DATA_FONT
            
            current_row += 1

    def _create_summary_sheet(self, wb: Workbook, results: List[DimensionalResult], metadata: Dict[str, Any], summary_data: Optional[Dict]):
        """Create executive summary sheet"""
        ws = wb.create_sheet("Executive Summary", 0)
        current_row = 1
        
        # Title
        title = ws.cell(row=current_row, column=1, value="DIMENSIONAL ANALYSIS - EXECUTIVE SUMMARY")
        title.font = self.TITLE_FONT
        title.alignment = Alignment(horizontal='center')
        ws.merge_cells(f'A{current_row}:H{current_row}')
        current_row += 3
        
        # Key statistics
        total_results = len(results)
        good_count = sum(1 for r in results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'GOOD')
        bad_count = sum(1 for r in results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'BAD')
        warning_count = sum(1 for r in results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'WARNING')
        success_rate = (good_count / total_results) * 100 if total_results > 0 else 0
        
        summary_stats = [
            ('Total Dimensions Analyzed:', total_results),
            ('Passed (GOOD):', good_count),
            ('Failed (BAD):', bad_count),
            ('Warnings:', warning_count),
            ('Success Rate:', f"{success_rate:.1f}%"),
            ('Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        
        for label, value in summary_stats:
            label_cell = ws.cell(row=current_row, column=1, value=label)
            label_cell.font = self.SUBTITLE_FONT
            value_cell = ws.cell(row=current_row, column=3, value=value)
            value_cell.font = self.DATA_FONT
            current_row += 1
        
        current_row += 2
        
        # Cavity breakdown
        cavity_groups = self._group_results_by_cavity(results)
        if len(cavity_groups) > 1:
            cavity_header = ws.cell(row=current_row, column=1, value="CAVITY BREAKDOWN:")
            cavity_header.font = self.SUBTITLE_FONT
            current_row += 1
            
            for cavity_num in sorted(cavity_groups.keys()):
                cavity_results = cavity_groups[cavity_num]
                cavity_good = sum(1 for r in cavity_results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'GOOD')
                cavity_rate = (cavity_good / len(cavity_results)) * 100 if cavity_results else 0
                
                cavity_info = f"Cavity {cavity_num}: {cavity_good}/{len(cavity_results)} passed ({cavity_rate:.1f}%)"
                cavity_cell = ws.cell(row=current_row, column=1, value=cavity_info)
                cavity_cell.font = self.DATA_FONT
                current_row += 1

    def _create_combined_overview_sheet(self, wb: Workbook, results: List[DimensionalResult], metadata: Dict[str, Any]):
        """Create combined overview sheet with all cavities"""
        ws = wb.create_sheet("Combined Overview")
        current_row = 1
        
        # Title
        title = ws.cell(row=current_row, column=1, value="COMBINED CAVITY OVERVIEW")
        title.font = self.TITLE_FONT
        title.alignment = Alignment(horizontal='center')
        ws.merge_cells(f'A{current_row}:Q{current_row}')
        current_row += 2
        
        # Headers
        headers = [
            'Cavity', 'Element ID', 'Description', 'Measuring Instrument', 
            'Measure 1', 'Measure 2', 'Measure 3', 'Measure 4', 'Measure 5',
            'Min', 'Max', 'Mean', 'Std Dev', 'Nominal', 'Lower Tol', 'Upper Tol', 'Status'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
        
        current_row += 1
        
        # Group by cavity and add data
        cavity_groups = self._group_results_by_cavity(results)
        for cavity_num in sorted(cavity_groups.keys()):
            for result in cavity_groups[cavity_num]:
                # Add cavity number as first column
                cavity_cell = ws.cell(row=current_row, column=1, value=cavity_num)
                cavity_cell.font = self.DATA_FONT
                cavity_cell.border = self.THIN_BORDER
                cavity_cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Add result data (shifted by one column due to cavity column)
                self._add_result_row_with_offset(ws, current_row, result, 1)
                current_row += 1
        
        self._adjust_column_widths(ws)

    def _add_result_row_with_offset(self, ws: Worksheet, row: int, result: DimensionalResult, col_offset: int = 0):
        """Add result row with column offset"""
        # Calculate statistics
        measurements = [m for m in result.measurements if m is not None]
        min_val = min(measurements) if measurements else None
        max_val = max(measurements) if measurements else None
        mean_val = sum(measurements) / len(measurements) if measurements else None
        
        std_val = None
        if measurements and len(measurements) > 1:
            variance = sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)
            std_val = variance ** 0.5
        
        data = [
            result.element_id,
            result.description,
            getattr(result, 'measuring_instrument', 'N/A'),
            *[f"{m:.4f}" if m is not None else '' for m in result.measurements[:5]],
            f"{min_val:.4f}" if min_val is not None else '',
            f"{max_val:.4f}" if max_val is not None else '',
            f"{mean_val:.4f}" if mean_val is not None else '',
            f"{std_val:.4f}" if std_val is not None else '',
            f"{result.nominal:.4f}" if result.nominal is not None else '',
            f"{result.lower_tolerance:.4f}" if result.lower_tolerance is not None else '',
            f"{result.upper_tolerance:.4f}" if result.upper_tolerance is not None else '',
            result.status.value if hasattr(result.status, 'value') else str(result.status)
        ]
        
        for col, value in enumerate(data, 2 + col_offset):  # Start from column 2 due to cavity column
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = self.DATA_FONT
            cell.border = self.THIN_BORDER
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            if col == len(data) + 1 + col_offset:  # Status column
                status = result.status.value if hasattr(result.status, 'value') else str(result.status)
                if status == 'GOOD':
                    cell.fill = self.GOOD_FILL
                elif status == 'BAD':
                    cell.fill = self.BAD_FILL
                elif status == 'WARNING':
                    cell.fill = self.WARNING_FILL

    def _create_metadata_workbook(self, filepath: str, metadata: Dict[str, Any], summary_data: Optional[Dict]):
        """Create separate metadata workbook for internal use"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Analysis Metadata"
        
        current_row = 1
        
        # Title
        title = ws.cell(row=current_row, column=1, value="DIMENSIONAL ANALYSIS METADATA")
        title.font = self.TITLE_FONT
        current_row += 3
        
        # Metadata sections
        sections = [
            ("Project Information", [
                ("Client Name", metadata.get('client_name', 'N/A')),
                ("Project Reference", metadata.get('project_ref', 'N/A')),
                ("Batch Number", metadata.get('batch_number', 'N/A')),
                ("Part Number", metadata.get('part_number', 'N/A')),
                ("Drawing Number", metadata.get('drawing_number', 'N/A')),
                ("Report Type", metadata.get('report_type', 'N/A')),
            ]),
            ("Quality Information", [
                ("Project Leader", metadata.get('project_leader', 'N/A')),
                ("Inspector", metadata.get('inspector', 'N/A')),
                ("Quality Facility", metadata.get('quality_facility', 'N/A')),
                ("Normative", metadata.get('normative', 'ISO 1101')),
                ("Analysis Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ]),
        ]
        
        if summary_data:
            sections.append(("Session Summary", [
                ("Session Duration", summary_data.get('session_info', {}).get('duration', 'N/A')),
                ("Studies Run", summary_data.get('metrics', {}).get('studies_run', 0)),
                ("Total Edits", summary_data.get('metrics', {}).get('edits_made', 0)),
                ("Data Completeness", f"{summary_data.get('metrics', {}).get('completeness', 0):.1f}%"),
                ("Modifications Made", len(summary_data.get('comparison_data', {}).get('modifications', []))),
            ]))
        
        for section_title, section_data in sections:
            # Section header
            header = ws.cell(row=current_row, column=1, value=section_title)
            header.font = self.SUBTITLE_FONT
            current_row += 1
            
            # Section data
            for label, value in section_data:
                label_cell = ws.cell(row=current_row, column=1, value=label)
                label_cell.font = self.DATA_FONT
                value_cell = ws.cell(row=current_row, column=2, value=value)
                value_cell.font = self.DATA_FONT
                current_row += 1
            
            current_row += 1
        
        wb.save(filepath)
        self.logger.info(f"📋 Metadata workbook created: {os.path.basename(filepath)}")

    def _export_by_cavity(self, export_dir: str, base_filename: str, timestamp: str, results: List[DimensionalResult], table_data: Optional[pd.DataFrame]) -> Dict[str, str]:
        """Export results separated by cavity"""
        cavity_dir = os.path.join(export_dir, "by_cavity")
        os.makedirs(cavity_dir, exist_ok=True)
        
        cavity_groups = self._group_results_by_cavity(results)
        export_paths = {}
        
        for cavity_num, cavity_results in cavity_groups.items():
            # JSON export
            json_path = os.path.join(cavity_dir, f"{base_filename}_cavity_{cavity_num}_{timestamp}.json")
            cavity_data = {
                "metadata": {
                    "cavity_number": cavity_num,
                    "total_dimensions": len(cavity_results),
                    "export_timestamp": datetime.now().isoformat(),
                },
                "results": [r.to_dict() for r in cavity_results]
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(cavity_data, f, indent=2, ensure_ascii=False, default=str)
            
            # CSV export
            csv_path = os.path.join(cavity_dir, f"{base_filename}_cavity_{cavity_num}_{timestamp}.csv")
            cavity_df = self._results_to_dataframe(cavity_results)
            cavity_df.to_csv(csv_path, index=False, encoding='utf-8')
            
            export_paths[f'cavity_{cavity_num}_json'] = json_path
            export_paths[f'cavity_{cavity_num}_csv'] = csv_path
            
            self.logger.info(f"🏭 Cavity {cavity_num} exported: {len(cavity_results)} dimensions")
        
        return export_paths

    def _export_comprehensive_json(self, filepath: str, results: List[DimensionalResult], metadata: Dict[str, Any], summary_data: Optional[Dict], table_data: Optional[pd.DataFrame]):
        """Export comprehensive JSON with all data"""
        export_data = {
            "metadata": {
                **metadata,
                "export_timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "export_format_version": "2.0",
            },
            "results": [r.to_dict() for r in results],
            "cavity_breakdown": self._get_cavity_statistics(results),
        }
        
        if summary_data:
            export_data["summary_data"] = summary_data
        
        if table_data is not None:
            export_data["original_table_data"] = table_data.to_dict('records')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📄 Comprehensive JSON exported: {os.path.basename(filepath)}")

    def _export_summary_csv(self, filepath: str, results: List[DimensionalResult], metadata: Dict[str, Any]):
        """Export summary CSV with key metrics"""
        summary_df = self._results_to_dataframe(results)
        
        # Add metadata as header comments
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write("# Dimensional Analysis Summary Report\n")
            f.write(f"# Client: {metadata.get('client_name', 'N/A')}\n")
            f.write(f"# Project: {metadata.get('project_ref', 'N/A')}\n")
            f.write(f"# Batch: {metadata.get('batch_number', 'N/A')}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("#\n")
            
            # Write the actual CSV data
            summary_df.to_csv(f, index=False)
        
        self.logger.info(f"📊 Summary CSV exported: {os.path.basename(filepath)}")

    def _group_results_by_cavity(self, results: List[DimensionalResult]) -> Dict[int, List[DimensionalResult]]:
        """Group results by cavity number"""
        cavity_groups = {}
        for result in results:
            cavity = getattr(result, 'cavity', 1) or 1
            if cavity not in cavity_groups:
                cavity_groups[cavity] = []
            cavity_groups[cavity].append(result)
        return cavity_groups

    def _get_cavity_statistics(self, results: List[DimensionalResult]) -> Dict[int, Dict[str, Any]]:
        """Get statistics for each cavity"""
        cavity_groups = self._group_results_by_cavity(results)
        cavity_stats = {}
        
        for cavity_num, cavity_results in cavity_groups.items():
            total = len(cavity_results)
            good = sum(1 for r in cavity_results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'GOOD')
            bad = sum(1 for r in cavity_results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'BAD')
            warning = sum(1 for r in cavity_results if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == 'WARNING')
            
            cavity_stats[cavity_num] = {
                'total_dimensions': total,
                'passed': good,
                'failed': bad,
                'warnings': warning,
                'success_rate': (good / total) * 100 if total > 0 else 0
            }
        
        return cavity_stats

    def _results_to_dataframe(self, results: List[DimensionalResult]) -> pd.DataFrame:
        """Convert results to DataFrame for CSV export"""
        data = []
        for result in results:
            # Calculate statistics
            measurements = [m for m in result.measurements if m is not None]
            min_val = min(measurements) if measurements else None
            max_val = max(measurements) if measurements else None
            mean_val = sum(measurements) / len(measurements) if measurements else None
            
            std_val = None
            if measurements and len(measurements) > 1:
                variance = sum((x - mean_val) ** 2 for x in measurements) / (len(measurements) - 1)
                std_val = variance ** 0.5
            
            row_data = {
                'element_id': result.element_id,
                'description': result.description,
                'cavity': getattr(result, 'cavity', 1),
                'measuring_instrument': getattr(result, 'measuring_instrument', 'N/A'),
                'nominal': result.nominal,
                'lower_tolerance': result.lower_tolerance,
                'upper_tolerance': result.upper_tolerance,
                'measurement_1': result.measurements[0] if len(result.measurements) > 0 else None,
                'measurement_2': result.measurements[1] if len(result.measurements) > 1 else None,
                'measurement_3': result.measurements[2] if len(result.measurements) > 2 else None,
                'measurement_4': result.measurements[3] if len(result.measurements) > 3 else None,
                'measurement_5': result.measurements[4] if len(result.measurements) > 4 else None,
                'min_value': min_val,
                'max_value': max_val,
                'mean_value': mean_val,
                'std_deviation': std_val,
                'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
                'out_of_spec_count': getattr(result, 'out_of_spec_count', 0),
                'warnings': '; '.join(getattr(result, 'warnings', [])),
            }
            data.append(row_data)
        
        return pd.DataFrame(data)

    def _adjust_column_widths(self, ws: Worksheet):
        """Auto-adjust column widths for better readability"""
        column_widths = {
            'A': 12,  # Element ID
            'B': 25,  # Description
            'C': 15,  # Measuring Instrument
            'D': 10, 'E': 10, 'F': 10, 'G': 10, 'H': 10,  # Measurements
            'I': 8, 'J': 8,   # Min/Max
            'K': 10, 'L': 10,  # Mean/Std
            'M': 10, 'N': 10, 'O': 10,  # Nominal/Tolerances
            'P': 12,  # Status
            'Q': 8,   # Extra column if needed
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    def _apply_status_formatting(self, ws: Worksheet, data_start_row: int, num_columns: int):
        """Apply conditional formatting based on status column"""
        # This would typically use openpyxl's conditional formatting
        # For now, formatting is applied during data insertion
        pass

    def generate_export_summary(self, export_paths: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """Generate a summary of exported files"""
        summary_lines = [
            "EXPORT SUMMARY",
            "=" * 50,
            f"Client: {metadata.get('client_name', 'N/A')}",
            f"Project: {metadata.get('project_ref', 'N/A')}",
            f"Batch: {metadata.get('batch_number', 'N/A')}",
            f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "EXPORTED FILES:",
            "-" * 20,
        ]
        
        file_descriptions = {
            'excel_report': '📊 Main Excel Report (for client)',
            'comprehensive_json': '📄 Complete JSON data',
            'summary_csv': '📈 Summary CSV data',
            'metadata': '📋 Metadata workbook (internal)',
        }
        
        for key, path in export_paths.items():
            if key in file_descriptions:
                summary_lines.append(f"{file_descriptions[key]}: {os.path.basename(path)}")
            elif 'cavity' in key:
                cavity_num = key.split('_')[1]
                file_type = key.split('_')[-1].upper()
                summary_lines.append(f"🏭 Cavity {cavity_num} {file_type}: {os.path.basename(path)}")
        
        summary_lines.extend([
            "",
            "NOTES:",
            "- Main Excel report is formatted for client presentation",
            "- Metadata workbook contains internal analysis data",
            "- Cavity files provide detailed breakdown by cavity",
            "- JSON files contain complete technical data",
        ])
        
        return "\n".join(summary_lines)