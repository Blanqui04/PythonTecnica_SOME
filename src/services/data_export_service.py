import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import platform

logger = logging.getLogger(__name__)

def get_downloads_folder():
    """Get the user's Downloads folder path across different operating systems"""
    try:
        if platform.system() == "Windows":
            # For Windows, use the USERPROFILE environment variable
            user_home = os.path.expanduser("~")
            downloads_path = Path(user_home) / "Downloads"
        elif platform.system() == "Darwin":  # macOS
            user_home = os.path.expanduser("~")
            downloads_path = Path(user_home) / "Downloads"
        else:  # Linux and other Unix-like systems
            user_home = os.path.expanduser("~")
            downloads_path = Path(user_home) / "Downloads"
            
        # Create Downloads folder if it doesn't exist (unlikely but safe)
        downloads_path.mkdir(parents=True, exist_ok=True)
        
        return downloads_path
    except Exception as e:
        logger.warning(f"Could not access Downloads folder: {e}. Using fallback directory.")
        # Fallback to a local exports directory
        fallback_path = Path("data/exports")
        fallback_path.mkdir(parents=True, exist_ok=True)
        return fallback_path

def export_analysis_data(analysis_type: str, ref_project: str, client: str = None) -> dict:
    """
    Export analysis data based on the analysis type and project reference.
    Files are saved to the user's Downloads folder.
    
    Args:
        analysis_type: Type of analysis ('dimensional' or 'capacity')
        ref_project: Project reference
        client: Client name (optional)
        
    Returns:
        dict: Result with success status, filename, filepath, and other details
    """
    try:
        # Get user's Downloads folder
        downloads_dir = get_downloads_folder()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_part = f"{client}_" if client else ""
        filename = f"{client_part}{ref_project}_{analysis_type}_export_{timestamp}.xlsx"
        filepath = downloads_dir / filename
        
        # Generate sample data based on analysis type
        if analysis_type == "dimensional":
            data = generate_dimensional_data(ref_project, client)
        elif analysis_type == "capacity":
            data = generate_capacity_data(ref_project, client)
        else:
            return {
                'success': False,
                'error': f"Unknown analysis type: {analysis_type}"
            }
        
        # Export to Excel with multiple sheets
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Calculate total records
        total_records = sum(len(df) for df in data.values())
        
        logger.info(f"Successfully exported {analysis_type} data for project {ref_project} to Downloads folder")
        
        return {
            'success': True,
            'filename': filename,
            'filepath': str(filepath),
            'downloads_folder': str(downloads_dir),
            'records_count': total_records,
            'sheets': list(data.keys())
        }
        
    except Exception as e:
        logger.error(f"Error exporting {analysis_type} data: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_dimensional_data(ref_project: str, client: str = None) -> dict:
    """Generate sample dimensional analysis data"""
    
    # Main dimensional analysis data
    dimensional_df = pd.DataFrame({
        'Project_Reference': [ref_project] * 10,
        'Client': [client or 'N/A'] * 10,
        'Part_Number': [f'PART_{i:03d}' for i in range(1, 11)],
        'Dimension': [f'DIM_{i}' for i in range(1, 11)],
        'Nominal_Value': [10.0 + i * 0.5 for i in range(10)],
        'Tolerance_Upper': [0.1 + i * 0.01 for i in range(10)],
        'Tolerance_Lower': [-(0.1 + i * 0.01) for i in range(10)],
        'Measured_Value': [10.0 + i * 0.5 + (i % 3 - 1) * 0.02 for i in range(10)],
        'Deviation': [(i % 3 - 1) * 0.02 for i in range(10)],
        'Status': ['OK' if abs((i % 3 - 1) * 0.02) < 0.05 else 'NOK' for i in range(10)],
        'Measurement_Date': [datetime.now().strftime("%Y-%m-%d") for _ in range(10)]
    })
    
    # Summary statistics
    summary_df = pd.DataFrame({
        'Metric': ['Total_Parts', 'Parts_OK', 'Parts_NOK', 'Pass_Rate_%', 'Avg_Deviation'],
        'Value': [
            len(dimensional_df),
            len(dimensional_df[dimensional_df['Status'] == 'OK']),
            len(dimensional_df[dimensional_df['Status'] == 'NOK']),
            round(len(dimensional_df[dimensional_df['Status'] == 'OK']) / len(dimensional_df) * 100, 2),
            round(dimensional_df['Deviation'].mean(), 4)
        ]
    })
    
    # Tolerance analysis
    tolerance_df = pd.DataFrame({
        'Dimension': [f'DIM_{i}' for i in range(1, 11)],
        'Tolerance_Range': [0.2 + i * 0.02 for i in range(10)],
        'Actual_Range': [0.15 + i * 0.015 for i in range(10)],
        'Utilization_%': [round((0.15 + i * 0.015) / (0.2 + i * 0.02) * 100, 1) for i in range(10)]
    })
    
    return {
        'Dimensional_Analysis': dimensional_df,
        'Summary_Statistics': summary_df,
        'Tolerance_Analysis': tolerance_df
    }

def generate_capacity_data(ref_project: str, client: str = None) -> dict:
    """Generate sample capacity analysis data"""
    
    # Main capacity study data
    capacity_df = pd.DataFrame({
        'Project_Reference': [ref_project] * 30,
        'Client': [client or 'N/A'] * 30,
        'Sample_ID': [f'S_{i:03d}' for i in range(1, 31)],
        'Process': ['Process_A'] * 30,
        'Measurement': [100.0 + i * 0.1 + (i % 5 - 2) * 0.5 for i in range(30)],
        'Subgroup': [(i // 5) + 1 for i in range(30)],
        'Operator': [f'OP_{(i % 3) + 1}' for i in range(30)],
        'Measurement_Date': [datetime.now().strftime("%Y-%m-%d") for _ in range(30)]
    })
    
    # Capability indices
    mean_val = capacity_df['Measurement'].mean()
    std_val = capacity_df['Measurement'].std()
    usl = 105.0  # Upper Specification Limit
    lsl = 95.0   # Lower Specification Limit
    
    cp = (usl - lsl) / (6 * std_val)
    cpk = min((usl - mean_val) / (3 * std_val), (mean_val - lsl) / (3 * std_val))
    
    capability_df = pd.DataFrame({
        'Index': ['Mean', 'Std_Dev', 'USL', 'LSL', 'Cp', 'Cpk', 'Pp', 'Ppk'],
        'Value': [
            round(mean_val, 3),
            round(std_val, 3),
            usl,
            lsl,
            round(cp, 3),
            round(cpk, 3),
            round(cp, 3),  # Simplified: using same as Cp
            round(cpk, 3)  # Simplified: using same as Cpk
        ]
    })
    
    # Control chart data
    subgroup_stats = capacity_df.groupby('Subgroup')['Measurement'].agg(['mean', 'std']).reset_index()
    subgroup_stats['Range'] = capacity_df.groupby('Subgroup')['Measurement'].apply(lambda x: x.max() - x.min()).values
    subgroup_stats['UCL_Mean'] = mean_val + 3 * std_val / (30**0.5)
    subgroup_stats['LCL_Mean'] = mean_val - 3 * std_val / (30**0.5)
    
    return {
        'Capacity_Data': capacity_df,
        'Capability_Indices': capability_df,
        'Control_Chart_Stats': subgroup_stats
    }

def export_csv_data(analysis_type: str, ref_project: str, client: str = None) -> dict:
    """
    Export analysis data as CSV files (alternative to Excel).
    Files are saved to the user's Downloads folder.
    
    Args:
        analysis_type: Type of analysis ('dimensional' or 'capacity')
        ref_project: Project reference
        client: Client name (optional)
        
    Returns:
        dict: Result with success status and file details
    """
    try:
        # Get user's Downloads folder
        downloads_dir = get_downloads_folder()
        
        # Generate data
        if analysis_type == "dimensional":
            data = generate_dimensional_data(ref_project, client)
        elif analysis_type == "capacity":
            data = generate_capacity_data(ref_project, client)
        else:
            return {
                'success': False,
                'error': f"Unknown analysis type: {analysis_type}"
            }
        
        # Export each sheet as separate CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_part = f"{client}_" if client else ""
        files_created = []
        
        for sheet_name, df in data.items():
            filename = f"{client_part}{ref_project}_{analysis_type}_{sheet_name}_{timestamp}.csv"
            filepath = downloads_dir / filename
            df.to_csv(str(filepath), index=False)
            files_created.append(filename)
        
        # Calculate total records
        total_records = sum(len(df) for df in data.values())
        
        logger.info(f"Successfully exported {analysis_type} CSV data for project {ref_project} to Downloads folder")
        
        return {
            'success': True,
            'files': files_created,
            'filepath': str(downloads_dir),
            'downloads_folder': str(downloads_dir),
            'records_count': total_records
        }
        
    except Exception as e:
        logger.error(f"Error exporting {analysis_type} CSV data: {e}")
        return {
            'success': False,
            'error': str(e)
        }
