# src/gui/main_window.py
from src.data_processing.pipeline_manager import DataProcessingPipeline

class MainWindow:
    def __init__(self):
        self.pipeline = DataProcessingPipeline()
    
    def process_excel_button_clicked(self):
        client = self.client_input.text()
        ref_project = self.ref_project_input.text()
        
        result, message = self.pipeline.process_project(client, ref_project, 'kop')
        
        if result:
            self.show_success_message(message)
        else:
            self.show_error_message(message)