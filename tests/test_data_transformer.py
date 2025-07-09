import unittest
from unittest.mock import patch, MagicMock
from src.data_processing.data_transformer import DataTransformer
import pandas as pd
import os

class TestDataTransformer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create sample test data
        os.makedirs('tests/test_data/datasheets', exist_ok=True)
        sample_data = pd.DataFrame({
            '13 - Nº Expedient:': ['PRJ-001'],
            'Caixa:': ['1001 - Standard Box'],
            'Pallet:': ['PAL-001 - Euro Pallet']
        })
        sample_data.to_csv('tests/test_data/datasheets/sample_datasheet.csv', index=False)

    def setUp(self):
        # Mock config
        self.config = {
            'PATHS': {
                'base_dir': 'tests/test_data',
                'datasheets_dir': 'datasheets',
                'db_export_dir': 'db_export',
                'log_dir': 'logs'
            }
        }
        self.transformer = DataTransformer('TEST_CLIENT', 'TEST_PROJECT')
        self.transformer.config = MagicMock()
        self.transformer.config.__getitem__.side_effect = self.config.__getitem__

    def test_successful_transformation(self):
        # Test basic transformation workflow
        result = self.transformer.transform_datasheet('sample_datasheet')
        self.assertIsInstance(result, dict)
        self.assertIn('embalatge', result)
        
    def test_missing_datasheet(self):
        with self.assertRaises(FileNotFoundError):
            self.transformer.transform_datasheet('non_existent_datasheet')
            
    def test_cw_date_conversion(self):
        # Test calendar week conversion
        self.assertEqual(self.transformer.cw_date('CW24/23'), '2023-06-12')
        self.assertEqual(self.transformer.cw_date('Invalid'), 'Invalid')
        
    def test_extract_cavitats(self):
        self.assertEqual(self.transformer.extract_cavitats('2 (LH+RH)'), 2)
        self.assertEqual(self.transformer.extract_cavitats('1+1'), 2)
        self.assertEqual(self.transformer.extract_cavitats('1 LH'), 1)
        
    # Add tests for each transformation method

if __name__ == '__main__':
    unittest.main()