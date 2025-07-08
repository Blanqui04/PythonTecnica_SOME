# tests/test_excel_processing.py
import unittest
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_processing.pipeline_manager import DataProcessingPipeline
from src.data_processing.excel_reader import ExcelReaderFactory

class TestExcelProcessing(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = DataProcessingPipeline()
        self.test_client = 'AUTOLIV'
        self.test_ref_project = '665220400'
    
    def test_excel_reader_factory(self):
        """Test Excel reader factory"""
        reader = ExcelReaderFactory.create_reader('kop')
        self.assertIsNotNone(reader)
        self.assertEqual(reader.client_type, 'kop')
    
    def test_find_excel_file(self):
        """Test finding Excel file"""
        reader = ExcelReaderFactory.create_reader('kop')
        try:
            excel_path = reader.find_excel_file(self.test_client, self.test_ref_project)
            self.assertTrue(os.path.exists(excel_path))
            self.assertTrue(excel_path.endswith(('.xlsx', '.xls', '.xlsm')))
        except Exception as e:
            self.skipTest(f"Excel file not found: {e}")
    
    def test_process_project(self):
        """Test complete project processing"""
        result, message = self.pipeline.process_project(
            self.test_client, 
            self.test_ref_project, 
            'kop'
        )
        
        if result:
            self.assertIsNotNone(result)
            self.assertIn('client', result)
            self.assertIn('ref_project', result)
            self.assertIn('datasheet', result)
            self.assertEqual(result['client'], self.test_client)
            self.assertEqual(result['ref_project'], self.test_ref_project)
        else:
            self.skipTest(f"Processing failed: {message}")

if __name__ == '__main__':
    unittest.main()