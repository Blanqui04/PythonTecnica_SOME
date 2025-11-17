"""
Unit Tests for Enhanced Features
Tests the 4 new functionalities:
1. SearchHistoryManager
2. SearchHistoryDialog
3. MultiLOTComparisonDialog  
4. ReferenceTemplateDialog
5. Integration with ElementInputWidget

Run: python -m pytest tests/test_enhanced_features.py -v
"""

import unittest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from src.gui.widgets.enhanced_features import (
    SearchHistoryManager,
    SearchHistoryDialog,
    MultiLOTComparisonDialog,
    ReferenceTemplateDialog
)
from src.gui.widgets.element_input_widget import ElementInputWidget


# Create QApplication instance for GUI tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestSearchHistoryManager(unittest.TestCase):
    """Test SearchHistoryManager functionality"""
    
    def setUp(self):
        """Create temporary history file for testing"""
        self.temp_dir = Path(__file__).parent / "temp_test_data"
        self.temp_dir.mkdir(exist_ok=True)
        self.history_file = self.temp_dir / "test_history.json"
        self.manager = SearchHistoryManager(history_file=str(self.history_file))
    
    def tearDown(self):
        """Clean up temporary files"""
        if self.history_file.exists():
            self.history_file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()
    
    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsInstance(self.manager, SearchHistoryManager)
        self.assertEqual(self.manager.max_history, 50)
        self.assertIsInstance(self.manager.history, list)
    
    def test_add_search(self):
        """Test adding a search to history"""
        self.manager.add_search(
            client="TEST_CLIENT",
            reference="TEST_REF",
            lot="LOT_001",
            machine="MACHINE_A"
        )
        
        self.assertEqual(len(self.manager.history), 1)
        self.assertEqual(self.manager.history[0]['client'], "TEST_CLIENT")
        self.assertEqual(self.manager.history[0]['reference'], "TEST_REF")
        self.assertEqual(self.manager.history[0]['lot'], "LOT_001")
        self.assertIn('timestamp', self.manager.history[0])
    
    def test_duplicate_removal(self):
        """Test that duplicates are removed"""
        # Add same search twice
        self.manager.add_search("CLIENT", "REF", "LOT", "MACHINE")
        self.manager.add_search("CLIENT", "REF", "LOT2", "MACHINE")
        
        # Should only keep the most recent one
        self.assertEqual(len(self.manager.history), 1)
        self.assertEqual(self.manager.history[0]['lot'], "LOT2")
    
    def test_max_history_limit(self):
        """Test that history respects max limit"""
        # Add more than max_history items
        for i in range(60):
            self.manager.add_search(f"CLIENT_{i}", f"REF_{i}", f"LOT_{i}", "MACHINE")
        
        self.assertLessEqual(len(self.manager.history), self.manager.max_history)
    
    def test_get_recent_searches(self):
        """Test retrieving recent searches"""
        # Add multiple searches
        for i in range(10):
            self.manager.add_search(f"CLIENT_{i}", f"REF_{i}", f"LOT_{i}", "MACHINE")
        
        recent = self.manager.get_recent_searches(limit=5)
        self.assertEqual(len(recent), 5)
        
        # Most recent should be first
        self.assertEqual(recent[0]['client'], "CLIENT_9")
    
    def test_get_suggestions(self):
        """Test autocomplete suggestions"""
        # Add searches with different values
        self.manager.add_search("AUTOLIV", "REF1", "LOT1", "MACHINE_A")
        self.manager.add_search("AUTOLIV", "REF2", "LOT2", "MACHINE_B")
        self.manager.add_search("BROSE", "REF3", "LOT3", "MACHINE_A")
        
        # Get client suggestions
        client_suggestions = self.manager.get_suggestions("client")
        self.assertIn("AUTOLIV", client_suggestions)
        self.assertIn("BROSE", client_suggestions)
        
        # Get machine suggestions
        machine_suggestions = self.manager.get_suggestions("machine")
        self.assertIn("MACHINE_A", machine_suggestions)
        self.assertIn("MACHINE_B", machine_suggestions)
    
    def test_persistence(self):
        """Test that history persists to file"""
        # Add a search
        self.manager.add_search("CLIENT", "REF", "LOT", "MACHINE")
        
        # File should exist
        self.assertTrue(self.history_file.exists())
        
        # Create new manager with same file
        manager2 = SearchHistoryManager(history_file=str(self.history_file))
        
        # Should load the saved history
        self.assertEqual(len(manager2.history), 1)
        self.assertEqual(manager2.history[0]['client'], "CLIENT")
    
    def test_clear_history(self):
        """Test clearing history"""
        # Add searches
        for i in range(5):
            self.manager.add_search(f"CLIENT_{i}", f"REF_{i}", f"LOT_{i}", "MACHINE")
        
        # Clear
        self.manager.clear_history()
        
        self.assertEqual(len(self.manager.history), 0)


class TestSearchHistoryDialog(unittest.TestCase):
    """Test SearchHistoryDialog GUI"""
    
    def setUp(self):
        """Create dialog for testing"""
        self.manager = SearchHistoryManager()
        # Add test data
        self.manager.add_search("AUTOLIV", "665220400", "LOT_001", "MACHINE_A")
        self.manager.add_search("BROSE", "E00104-102", "LOT_002", "MACHINE_B")
        
        self.dialog = SearchHistoryDialog(self.manager, None)
    
    def tearDown(self):
        """Clean up"""
        self.dialog.close()
    
    def test_dialog_creation(self):
        """Test dialog is created properly"""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.history_table.columnCount(), 5)
    
    def test_table_population(self):
        """Test that table is populated with history"""
        # Should have 2 rows from setUp
        self.assertEqual(self.dialog.history_table.rowCount(), 2)
        
        # Check first row data
        client_item = self.dialog.history_table.item(0, 1)
        self.assertIsNotNone(client_item)
    
    def test_filter_functionality(self):
        """Test filtering the history table"""
        # Apply filter
        self.dialog.filter_input.setText("AUTOLIV")
        self.dialog._filter_history()
        
        # Should only show AUTOLIV entry
        visible_rows = sum(
            1 for row in range(self.dialog.history_table.rowCount())
            if not self.dialog.history_table.isRowHidden(row)
        )
        self.assertEqual(visible_rows, 1)


class TestMultiLOTComparisonDialog(unittest.TestCase):
    """Test MultiLOTComparisonDialog"""
    
    @patch('src.gui.widgets.enhanced_features.MeasurementHistoryService')
    def setUp(self, mock_service):
        """Create dialog with mocked service"""
        self.dialog = MultiLOTComparisonDialog(
            client="TEST_CLIENT",
            reference="TEST_REF",
            machine="all",
            parent=None
        )
    
    def tearDown(self):
        """Clean up"""
        self.dialog.close()
    
    def test_dialog_creation(self):
        """Test dialog is created properly"""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.results_table.columnCount(), 8)
        self.assertEqual(self.dialog.client, "TEST_CLIENT")
        self.assertEqual(self.dialog.reference, "TEST_REF")
    
    def test_select_all_lots(self):
        """Test select all LOTs functionality"""
        # Add test items
        self.dialog.lot_list.addItems(["LOT_001", "LOT_002", "LOT_003"])
        
        # Select all
        self.dialog._select_all_lots()
        
        # All items should be selected
        selected = self.dialog.lot_list.selectedItems()
        self.assertEqual(len(selected), 3)


class TestReferenceTemplateDialog(unittest.TestCase):
    """Test ReferenceTemplateDialog"""
    
    def setUp(self):
        """Create dialog"""
        self.dialog = ReferenceTemplateDialog(
            client="TEST_CLIENT",
            reference="TEST_REF",
            parent=None
        )
    
    def tearDown(self):
        """Clean up"""
        self.dialog.close()
    
    def test_dialog_creation(self):
        """Test dialog is created properly"""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.client, "TEST_CLIENT")
        self.assertEqual(self.dialog.reference, "TEST_REF")
    
    def test_machine_combo(self):
        """Test machine selection combo"""
        # Should have default machines
        self.assertGreater(self.dialog.machine_combo.count(), 0)
    
    def test_lot_mode_radio(self):
        """Test LOT mode radio buttons"""
        # Should have both options
        self.assertIsNotNone(self.dialog.all_lots_radio)
        self.assertIsNotNone(self.dialog.specific_lot_radio)


class TestElementInputWidgetIntegration(unittest.TestCase):
    """Test integration with ElementInputWidget"""
    
    def setUp(self):
        """Create widget"""
        self.widget = ElementInputWidget()
    
    def test_search_history_initialized(self):
        """Test that search history is initialized"""
        self.assertIsNotNone(self.widget.search_history)
        self.assertIsInstance(self.widget.search_history, SearchHistoryManager)
    
    def test_buttons_exist(self):
        """Test that enhanced feature buttons exist"""
        self.assertTrue(hasattr(self.widget, 'history_button'))
        self.assertTrue(hasattr(self.widget, 'template_button'))
        self.assertTrue(hasattr(self.widget, 'compare_lots_button'))
    
    def test_advanced_frame_exists(self):
        """Test that advanced buttons frame exists"""
        self.assertTrue(hasattr(self.widget, 'advanced_buttons_frame'))
    
    def test_methods_exist(self):
        """Test that integration methods exist"""
        methods = [
            '_show_search_history',
            '_apply_history_search',
            '_create_reference_template',
            '_apply_template',
            '_compare_multiple_lots',
            '_enable_advanced_features',
            '_save_current_search'
        ]
        
        for method in methods:
            self.assertTrue(
                hasattr(self.widget, method),
                f"Method {method} not found"
            )
    
    def test_enable_advanced_features(self):
        """Test enabling advanced features"""
        # Set required data
        self.widget.client = "TEST_CLIENT"
        self.widget.project_reference = "TEST_REF"
        
        # Enable features
        self.widget._enable_advanced_features()
        
        # Buttons should be enabled
        self.assertTrue(self.widget.template_button.isEnabled())
        self.assertTrue(self.widget.compare_lots_button.isEnabled())
    
    @patch('src.gui.widgets.enhanced_features.SearchHistoryDialog')
    def test_show_search_history(self, mock_dialog):
        """Test showing search history dialog"""
        # Call method
        self.widget._show_search_history()
        
        # Dialog should be created
        mock_dialog.assert_called_once()


class TestPasteableTableWidget(unittest.TestCase):
    """Test Copy/Paste functionality"""
    
    def setUp(self):
        """Create widget with table"""
        self.widget = ElementInputWidget()
        self.table = self.widget.values_table
    
    def test_table_is_pasteable(self):
        """Test that table supports paste"""
        from src.gui.widgets.element_input_widget import PasteableTableWidget
        self.assertIsInstance(self.table, PasteableTableWidget)
    
    def test_keypressevent_exists(self):
        """Test that keyPressEvent handler exists"""
        self.assertTrue(hasattr(self.table, 'keyPressEvent'))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSearchHistoryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchHistoryDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiLOTComparisonDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestReferenceTemplateDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestElementInputWidgetIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPasteableTableWidget))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
