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
        self.master_folder = r'\\server\SOME\Projectes en curs'
        self.csv_folder = r'C:\Github\PythonTecnica_SOME\data\temp'
        self.processed_folder = r'C:\Github\PythonTecnica_SOME\data\processed'
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
            
            if not os.path.exists(client_folder):
                raise FileNotFoundError(f"Client folder not found: {client_folder}")
            
            # Search for project folder containing the reference
            for root, dirs, files in os.walk(client_folder):
                for dir_name in dirs:
                    if ref_project in dir_name:
                        kop_folder = os.path.join(root, dir_name, self.address_kop)
                        
                        if not os.path.exists(kop_folder):
                            continue
                        
                        # Search for Excel file
                        for sub_root, sub_dirs, sub_files in os.walk(kop_folder):
                            for file in sub_files:
                                if file.endswith(('.xlsx', '.xls', '.xlsm')):
                                    return os.path.join(sub_root, file)
            
            raise FileNotFoundError(f"No Excel file found for client '{client}' and project '{ref_project}'")
            
        except Exception as e:
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

class ExcelReaderFactory:
    """Factory to create appropriate Excel reader"""
    
    @staticmethod
    def create_reader(client_type):
        if client_type.lower() == 'kop' or client_type.lower() == 'autoliv':
            return KOPExcelReader()
        else:
            # Add other readers as needed
            return KOPExcelReader()  # Default to KOP for now