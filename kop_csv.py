import os
import sys
import csv
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
import openpyxl
import pandas as pd
# Add other imports as needed from your original script
# from your_other_modules import dades_kop, tractar_estructura, tractar_dades_extra, combine_and_transpose_csv

# Configuration constants (can be moved to a config file later)
MASTER_FOLDER = r'\\server\SOME\Projectes en curs'
ADDRESS_KOP = r'5-FOLLOW-UP\1-KOP'
CSV_FOLDER = r'C:\Github\PythonTecnica_SOME\dades_escandall_csv'
DATASHEETS_FOLDER = r'C:\Github\PythonTecnica_SOME\datasheets_csv'

class KOPProcessor:
    """
    Class to handle KOP file processing with dynamic client and project parameters
    """
    
    def __init__(self, client=None, ref_project=None):
        """
        Initialize KOP processor with optional client and project parameters
        
        Args:
            client (str): Client name to search for
            ref_project (str): Project reference to search for
        """
        self.client = client
        self.ref_project = ref_project
        self.master_folder = MASTER_FOLDER
        self.address_kop = ADDRESS_KOP
        self.csv_folder = CSV_FOLDER
        self.datasheets_folder = DATASHEETS_FOLDER
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        try:
            os.makedirs(self.csv_folder, exist_ok=True)
            os.makedirs(self.datasheets_folder, exist_ok=True)
            print(f"Directories ensured: {self.csv_folder}, {self.datasheets_folder}")
        except Exception as e:
            print(f"Error creating directories: {e}")
    
    def set_parameters(self, client, ref_project):
        """
        Set client and project parameters
        
        Args:
            client (str): Client name
            ref_project (str): Project reference
        """
        self.client = client
        self.ref_project = ref_project
        print(f"Parameters set - Client: {client}, Project: {ref_project}")
    
    def trobar_arxiu_excel(self, client=None, ref_project=None):
        """
        Function to search for Excel file (KOP) for specified client
        within the project folder containing the specified reference.
        Now also accepts .xlsm files (with macros).
        
        Args:
            client (str): Client name (optional, uses instance variable if not provided)
            ref_project (str): Project reference (optional, uses instance variable if not provided)
            
        Returns:
            str: Path to Excel file if found, None otherwise
        """
        # Use provided parameters or fall back to instance variables
        search_client = client or self.client
        search_ref_project = ref_project or self.ref_project
        
        if not search_client or not search_ref_project:
            print("Error: Client and project reference must be provided!")
            return None
        
        print(f"Searching for Excel file - Client: {search_client}, Project: {search_ref_project}")
        
        try:
            client_folder = os.path.join(self.master_folder, search_client)
            
            if not os.path.exists(client_folder):
                print(f"Client folder not found: {client_folder}")
                return None
            
            print(f"Searching in client folder: {client_folder}")
            
            # Search for project folder containing the specified reference
            for root, dirs, files in os.walk(client_folder):
                for dir_name in dirs:
                    if search_ref_project in dir_name:
                        kop_folder = os.path.join(root, dir_name, self.address_kop)
                        print(f"Found project folder: {dir_name}")
                        print(f"Looking for KOP files in: {kop_folder}")
                        
                        if not os.path.exists(kop_folder):
                            print(f"KOP folder not found: {kop_folder}")
                            continue
                        
                        # Search for Excel file within project folder
                        for sub_root, sub_dirs, sub_files in os.walk(kop_folder):
                            for file in sub_files:
                                if file.endswith(('.xlsx', '.xls', '.xlsm')):
                                    excel_path = os.path.join(sub_root, file)
                                    print(f"Excel file found: {excel_path}")
                                    return excel_path
            
            print(f"No Excel file found for client '{search_client}' and project '{search_ref_project}'")
            return None
            
        except Exception as e:
            print(f"Error searching for Excel file: {e}")
            return None
    
    def process_kop_file(self, client=None, ref_project=None):
        """
        Main function to execute the complete data processing.
        """
        process_client = client or self.client
        process_ref_project = ref_project or self.ref_project

        if not process_client or not process_ref_project:
            error_msg = "Error: Client and project reference must be provided!"
            print(error_msg)
            return None, error_msg

        try:
            print(f"Starting KOP processing for Client: {process_client}, Project: {process_ref_project}")

            # Find Excel file
            escandall_path = self.trobar_arxiu_excel(process_client, process_ref_project)
            if not escandall_path:
                error_msg = f"No Excel file found for client '{process_client}' and project '{process_ref_project}'!"
                print(error_msg)
                return None, error_msg

            print(f"Processing Excel file: {escandall_path}")

            # Step 1: Extract sheets and save as temp CSVs
            wb = openpyxl.load_workbook(escandall_path, data_only=True)
            for sheet_name in ['ESTRUCTURA', 'Entrada Dades - Extres']:
                if sheet_name in wb.sheetnames:
                    wb[sheet_name].protection.sheet = False
            temp_path_1 = os.path.join(self.csv_folder, 'temp_unprotected.xlsx')
            temp_path_2 = os.path.join(self.csv_folder, 'temp_estructura.csv')
            temp_path_3 = os.path.join(self.csv_folder, 'temp_dades.csv')
            wb.save(temp_path_1)
            df_estructura = pd.read_excel(temp_path_1, sheet_name='ESTRUCTURA')
            df_dades = pd.read_excel(temp_path_1, sheet_name='Entrada Dades - Extres')
            df_estructura.to_csv(temp_path_2, index=False)
            df_dades.to_csv(temp_path_3, index=False)

            # Step 2: Clean structure CSV
            df = pd.read_csv(temp_path_2, header=None)
            df.dropna(how='all', inplace=True)
            df.dropna(how='all', axis=1, inplace=True)
            df.reset_index(drop=True, inplace=True)
            cleaned_data = []
            for _, row in df.iterrows():
                filtered_row = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() != '']
                if len(filtered_row) > 2:
                    filtered_row = filtered_row[:2]
                cleaned_data.append(filtered_row)
            csv_post_est = os.path.join(self.csv_folder, f"estructura {process_client} {process_ref_project}.csv")
            cleaned_df = pd.DataFrame(cleaned_data)
            cleaned_df.to_csv(csv_post_est, index=False, header=False)

            # Step 3: Clean extra data CSV
            df = pd.read_csv(temp_path_3, usecols=range(7), header=0)
            df.dropna(how='all', inplace=True)
            df = df.iloc[:, [1, 2, 5, 6]]
            df.dropna(how='all', inplace=True)
            p_1 = df.iloc[:, :2].dropna(how='all')
            p_2 = df.iloc[:, 2:].dropna(how='all')
            p_1.columns = ['Key', 'Value']
            p_2.columns = ['Key', 'Value']
            csv_post_dds = os.path.join(self.csv_folder, f"dades_extra {process_client} {process_ref_project}.csv")
            result = pd.concat([p_1, p_2], ignore_index=True)
            result.to_csv(csv_post_dds, index=False, header=False)

            # Step 4: Combine and transpose for datasheet
            df_estr = pd.read_csv(csv_post_est, header=None)
            df_dades = pd.read_csv(csv_post_dds, header=None)
            df_estr = df_estr.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)
            df_dades = df_dades.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)
            df_est_transposed = df_estr.T
            df_dades_transposed = df_dades.T
            combined_df = pd.concat([df_est_transposed, df_dades_transposed], axis=1)
            if len(combined_df) > 2:
                combined_df = combined_df.iloc[:2]
            csv_datasheet = os.path.join(self.datasheets_folder, f"dades_escandall {process_client} {process_ref_project}.csv")
            combined_df.to_csv(csv_datasheet, index=False, header=False)
            print(f"Fitxer combinat desat a: {csv_datasheet}")

            # Optionally, remove temp files
            for temp_file in [temp_path_1, temp_path_2, temp_path_3]:
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

            success_msg = f"Processing completed successfully!\nFiles generated:\n- {csv_post_est}\n- {csv_post_dds}\n- {csv_datasheet}"

            return csv_datasheet, success_msg

        except Exception as e:
            error_msg = f"Error processing KOP file: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    def get_status(self):
        """
        Get current processor status
        
        Returns:
            dict: Status information
        """
        return {
            'client': self.client,
            'ref_project': self.ref_project,
            'csv_folder': self.csv_folder,
            'datasheets_folder': self.datasheets_folder,
            'directories_exist': os.path.exists(self.csv_folder) and os.path.exists(self.datasheets_folder)
        }

# Global processor instance
_kop_processor = KOPProcessor()

def main(client=None, ref_project=None):
    """
    Main function to be called from UI
    
    Args:
        client (str): Client name
        ref_project (str): Project reference
        
    Returns:
        tuple: (csv_datasheet_path, processing_result) or (None, error_message)
    """
    global _kop_processor
    
    if client and ref_project:
        _kop_processor.set_parameters(client, ref_project)
    
    return _kop_processor.process_kop_file()

def set_global_parameters(client, ref_project):
    """
    Set global parameters for the processor
    
    Args:
        client (str): Client name
        ref_project (str): Project reference
    """
    global _kop_processor
    _kop_processor.set_parameters(client, ref_project)

def get_processor_status():
    """
    Get current processor status
    
    Returns:
        dict: Status information
    """
    global _kop_processor
    return _kop_processor.get_status()

# Legacy support - maintain original variable names for backward compatibility
def get_client():
    """Get current client"""
    return _kop_processor.client

def get_ref_project():
    """Get current project reference"""
    return _kop_processor.ref_project

# Set default values for backward compatibility
client = None  # Will be set dynamically
ref_project = None  # Will be set dynamically

# Only execute if run directly (for testing)
if __name__ == "__main__":
    # Test the processor
    test_client = 'AUTOLIV'
    test_ref_project = '665220400'
    
    print("Testing KOP processor...")
    result_path, result_msg = main(test_client, test_ref_project)
    
    if result_path:
        print(f"Success: {result_msg}")
    else:
        print(f"Error: {result_msg}")
