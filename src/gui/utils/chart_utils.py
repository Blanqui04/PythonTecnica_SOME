# src/gui/utils/chart_utils.py
import os
from typing import Dict, List, Tuple


class ChartPathResolver:
    """Utility class for resolving chart file paths"""
    
    @staticmethod
    def get_study_directory(client: str, ref_project: str) -> str:
        """Get the study directory path"""
        return os.path.join("data", "spc", f"{client}_{ref_project}")
    
    @staticmethod
    def get_charts_directory(ref_project: str) -> str:
        """Get the charts directory path - UPDATED for new structure"""
        return os.path.join("data", "reports", "charts", ref_project)
    
    @staticmethod
    def get_report_path(client: str, ref_project: str, batch_number: str = None) -> str:
        """Get the complete report JSON path"""
        if batch_number:
            study_dir = ChartPathResolver.get_study_directory(client, ref_project)
            return os.path.join(study_dir, f"{ref_project}_{batch_number}_complete_report.json")
        else:
            study_dir = ChartPathResolver.get_study_directory(client, ref_project)
            return os.path.join(study_dir, f"{client}_{ref_project}_complete_report.json")
    
    @staticmethod
    def get_chart_path(ref_project: str, batch_number: str, element_name: str, chart_type: str, cavity: str = None) -> str:
        """Get path for a specific chart - COMPLETELY FIXED to match chart generation"""
        charts_dir = ChartPathResolver.get_charts_directory(ref_project)
        
        # FIXED: Use exact same filename format as SPCChartManager
        if cavity and str(cavity).strip():
            filename = f"{chart_type}_{batch_number}_{element_name}_{cavity}.png"
        else:
            filename = f"{chart_type}_{batch_number}_{element_name}.png"
            
        return os.path.join(charts_dir, filename)
    
    @staticmethod
    def get_available_charts(ref_project: str, batch_number: str, element_name: str, cavity: str = None) -> List[str]:
        """Get list of available chart types for an element - FIXED pattern matching"""
        charts_dir = ChartPathResolver.get_charts_directory(ref_project)
        
        if not os.path.exists(charts_dir):
            return []
        
        chart_types = []
        
        # FIXED: Search pattern based on exact filename format from SPCChartManager
        if cavity and str(cavity).strip():
            pattern_suffix = f"_{batch_number}_{element_name}_{cavity}.png"
        else:
            pattern_suffix = f"_{batch_number}_{element_name}.png"
        
        print(f"DEBUG: Looking for files ending with: {pattern_suffix}")
        print(f"DEBUG: In directory: {charts_dir}")
        
        if os.path.exists(charts_dir):
            files_found = os.listdir(charts_dir)
            print(f"DEBUG: Files in directory: {files_found}")
        
        for filename in os.listdir(charts_dir):
            if filename.endswith(pattern_suffix):
                # Extract chart type from beginning of filename
                chart_type = filename.replace(pattern_suffix, "")
                chart_types.append(chart_type)
                print(f"DEBUG: Found chart type: {chart_type} from file: {filename}")
        
        print(f"DEBUG: Available chart types: {chart_types}")
        return chart_types
    
    @staticmethod
    def validate_study_files(client: str, ref_project: str, batch_number: str = None) -> Tuple[bool, str]:
        """Validate that required study files exist"""
        study_dir = ChartPathResolver.get_study_directory(client, ref_project)
        
        if not os.path.exists(study_dir):
            return False, f"Study directory not found: {study_dir}"
        
        report_path = ChartPathResolver.get_report_path(client, ref_project, batch_number)
        if not os.path.exists(report_path):
            return False, f"Report file not found: {report_path}"
        
        charts_dir = ChartPathResolver.get_charts_directory(ref_project)
        if not os.path.exists(charts_dir):
            return False, f"Charts directory not found: {charts_dir}"
        
        return True, "All required files found"


class ChartDisplayHelper:
    """Helper class for chart display operations"""
    
    CHART_TYPE_NAMES = {
        "capability": "Capacitat",
        "normality": "Normalitat",
        "i_chart": "Gràfic I", 
        "mr_chart": "Gràfic MR",
        "extrapolation": "Extrapolació"
    }
    
    @staticmethod
    def get_chart_display_name(chart_type: str) -> str:
        """Get user-friendly display name for chart type"""
        return ChartDisplayHelper.CHART_TYPE_NAMES.get(chart_type, chart_type.title())
    
    @staticmethod
    def get_chart_priority_order() -> List[str]:
        """Get preferred order for displaying chart tabs"""
        return ["capability", "normality", "i_chart", "mr_chart", "extrapolation"]
    
    @staticmethod
    def format_element_info(element_data: Dict) -> str:
        """Format element information for display"""
        info_lines = []
        
        if 'element_name' in element_data:
            info_lines.append(f"Element: {element_data['element_name']}")
        
        if 'sample_count' in element_data:
            info_lines.append(f"Mostres: {element_data['sample_count']}")
            
        if 'nominal' in element_data:
            info_lines.append(f"Nominal: {element_data['nominal']}")
            
        if 'tolerances' in element_data:
            info_lines.append(f"Toleràncies: {element_data['tolerances']}")
            
        if 'cp' in element_data:
            cp_value = element_data['cp']
            if isinstance(cp_value, (int, float)):
                info_lines.append(f"Cp: {cp_value:.3f}")
            else:
                info_lines.append(f"Cp: {cp_value}")
                
        if 'cpk' in element_data:
            cpk_value = element_data['cpk']
            if isinstance(cpk_value, (int, float)):
                info_lines.append(f"Cpk: {cpk_value:.3f}")
            else:
                info_lines.append(f"Cpk: {cpk_value}")
        
        return "\n".join(info_lines)