from src.data_processing.utils.excel_reader import ExcelReaderFactory
from .data_processor import DataProcessor
from .data_transformer import DataTransformer
import json
import os
from datetime import datetime, date

def convert_datetime(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class DataProcessingPipeline:
    """Main pipeline for processing Excel files"""
    
    def __init__(self):
        self.excel_reader_factory = ExcelReaderFactory()
        self.data_processor = DataProcessor()
    
    def process_project(self, client, ref_project, client_type='kop'):
        """Process a project's Excel file"""
        try:
            
            reader = self.excel_reader_factory.create_reader(client_type)   # Step 1: Create appropriate reader
            excel_path = reader.find_excel_file(client, ref_project)        # Step 2: Find Excel file
            raw_data = reader.read_excel(excel_path)                        # Step 3: Read Excel data
            
            # Step 4: Process data
            print(f"Processing data for client type: {client_type}")
            # For now, all clients use the same processing method
            # We can add specialized processing methods if needed in the future
            processed_data = self.data_processor.process_kop_data(raw_data, client, ref_project)
            
            self._save_processed_data(processed_data, client, ref_project)  # Step 5: Save processed data as JSON
            
            return processed_data, f"Successfully processed {client} - {ref_project}"
            
        except Exception as e:
            return None, f"Error processing project: {str(e)}"
    
    def _save_processed_data(self, data, client, ref_project):
        """Save processed data as JSON"""
        filename = f"processed_{client}_{ref_project}.json"
        filepath = os.path.join('data/processed/datasheets', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=convert_datetime)
    
    def run_transformation(self, client, project, datasheet_name):
        transformer = DataTransformer(client, project)
        return transformer.transform_datasheet(datasheet_name)

