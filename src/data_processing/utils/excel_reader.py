from abc import ABC, abstractmethod
import os
import pandas as pd
import openpyxl
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

class ExcelReaderBase(ABC):
    """Base class for Excel readers"""
    
    def __init__(self, client_type):
        self.client_type = client_type
        self.master_folder = r"\\server.some.local\\SOME\Projectes en curs"
        self.csv_folder = r"C:\Github\PythonTecnica_SOME\data\temp"
        self.processed_folder = r"C:\Github\PythonTecnica_SOME\data\processed"
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        os.makedirs(self.csv_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
    
    @abstractmethod
    def find_excel_file(self, client, ref_project):
        """Find Excel file for specific client and project"""
        pass
    
    @abstractmethod
    def read_excel(self, file_path):
        """Read and process Excel file"""
        pass

class KOPExcelReader(ExcelReaderBase):
    """Reader for KOP Excel files"""
    
    def __init__(self):
        super().__init__('kop')
        self.address_kop = r'5-FOLLOW-UP\1-KOP'
    
    def find_excel_file(self, client, ref_project):
        """Find KOP Excel file"""
        try:
            client_folder = os.path.join(self.master_folder, client)
            print(f"Looking for client folder: {client_folder}")
            
            if not os.path.exists(client_folder):
                raise FileNotFoundError(f"Client folder not found: {client_folder}")
            
            # Normalize the reference by stripping leading zeros if needed
            ref_project_normalized = ref_project.lstrip('0')
            
            print(f"Searching for project with reference: {ref_project}")
            print(f"Also searching with normalized reference: {ref_project_normalized}")
            
            # Search for project folder containing the reference
            for root, dirs, files in os.walk(client_folder, topdown=True):
                print(f"Scanning directory: {root}")
                print(f"Found directories: {dirs}")
                
                for dir_name in dirs:
                    # Normalize the directory name for comparison
                    dir_parts = dir_name.split('_')
                    dir_parts_normalized = [part.lstrip('0') for part in dir_parts]
                    
                    found_match = False
                    match_reason = ""
                    
                    # Original reference check
                    if ref_project in dir_name:
                        found_match = True
                        match_reason = f"Direct match of {ref_project} in {dir_name}"
                    
                    # Check normalized reference against normalized directory parts
                    if not found_match and ref_project_normalized:
                        for part in dir_parts_normalized:
                            if ref_project_normalized == part:
                                found_match = True
                                match_reason = f"Normalized match: {ref_project_normalized} in {dir_name} parts"
                                break
                    
                    if found_match:
                        print(f"Found matching directory: {dir_name}. Reason: {match_reason}")
                        
                        # Try multiple possible KOP folder paths
                        kop_paths = [
                            os.path.join(root, dir_name, self.address_kop),
                            os.path.join(root, dir_name, "5-FOLLOW-UP", "KOP"),
                            os.path.join(root, dir_name, "FOLLOW-UP", "KOP"),
                            os.path.join(root, dir_name, "FOLLOW UP", "KOP"),
                            os.path.join(root, dir_name, "FOLLOW-UP"),
                            os.path.join(root, dir_name, "KOP")
                        ]
                        
                        for kop_path in kop_paths:
                            print(f"Checking KOP path: {kop_path}")
                            
                            if not os.path.exists(kop_path):
                                continue
                                
                            # Search for Excel file
                            for sub_root, sub_dirs, sub_files in os.walk(kop_path):
                                print(f"Checking for Excel files in: {sub_root}")
                                print(f"Files: {sub_files}")
                                
                                for file in sub_files:
                                    if file.endswith(('.xlsx', '.xls', '.xlsm')):
                                        return os.path.join(sub_root, file)
            
            print(f"File not found. Completed searching in '{client_folder}' for project '{ref_project}'")
            raise FileNotFoundError(f"No Excel file found for client '{client}' and project '{ref_project}'")
            
        except Exception as e:
            print(f"Exception occurred during search: {str(e)}")
            raise Exception(f"Error searching for Excel file: {e}")
    
    def read_excel(self, file_path):
        """Read and process KOP Excel file"""
        try:
            # Load workbook and unprotect sheets
            wb = openpyxl.load_workbook(file_path, data_only=True)
            for sheet_name in ['ESTRUCTURA', 'Entrada Dades - Extres']:
                if sheet_name in wb.sheetnames:
                    wb[sheet_name].protection.sheet = False
            
            # Save temporary unprotected file
            temp_path = os.path.join(self.csv_folder, 'temp_unprotected.xlsx')
            wb.save(temp_path)
            
            # Read specific sheets
            df_estructura = pd.read_excel(temp_path, sheet_name='ESTRUCTURA')
            df_dades = pd.read_excel(temp_path, sheet_name='Entrada Dades - Extres')
            
            # Clean up temp file
            os.remove(temp_path)
            
            return {
                'estructura': df_estructura,
                'dades_extra': df_dades
            }
            
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}")

class ZFExcelReader(KOPExcelReader):
    """Reader specifically for ZF Excel files"""
    
    def __init__(self):
        super().__init__()
        # Try alternative KOP paths that might be specific to ZF
        self.address_kop = r'5-FOLLOW-UP\1-KOP'
        
    def find_excel_file(self, client, ref_project):
        """Override to handle ZF specific directory structures"""
        try:
            client_folder = os.path.join(self.master_folder, client)
            print(f"ZF Reader - Looking for client folder: {client_folder}")
            
            if not os.path.exists(client_folder):
                raise FileNotFoundError(f"Client folder not found: {client_folder}")
                
            # For ZF, try direct path first based on the known structure
            specific_path = os.path.join(
                client_folder, 
                f"{ref_project}_004938000152 - SENSOR BRACKET LH+RH (ME)", 
                "5-FOLLOW-UP", 
                "1-KOP"
            )
            
            print(f"ZF Reader - Trying specific path: {specific_path}")
            
            if os.path.exists(specific_path):
                for sub_root, sub_dirs, sub_files in os.walk(specific_path):
                    for file in sub_files:
                        if file.endswith(('.xlsx', '.xls', '.xlsm')):
                            return os.path.join(sub_root, file)
            
            # If direct path failed, try the normalized search approach from the parent class
            return super().find_excel_file(client, ref_project)
            
        except Exception as e:
            print(f"ZF Exception occurred during search: {str(e)}")
            raise Exception(f"Error searching for ZF Excel file: {e}")

class ExcelReaderFactory:
    """Factory to create appropriate Excel reader"""
    
    @staticmethod
    def create_reader(client_type):
        # Convert to lowercase for case-insensitive comparison
        client_type_lower = client_type.lower()
        
        if client_type_lower == 'kop' or client_type_lower == 'autoliv':
            return KOPExcelReader()
        elif client_type_lower == 'zf':
            print("Using ZF specific Excel reader")
            return ZFExcelReader()
        else:
            print(f"No specific reader for {client_type}, defaulting to KOP reader")
            return KOPExcelReader()  # Default to KOP for now