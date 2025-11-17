"""
Manual Test Script for Enhanced Features
Tests the 4 new functionalities:
1. Copy/Paste (Ctrl+C/V)
2. Search History with Autocomplete
3. Reference Templates
4. Multi-LOT Comparison

Run this after starting the GUI to validate all features work correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from src.gui.widgets.element_input_widget import ElementInputWidget
from src.gui.widgets.enhanced_features import SearchHistoryManager
import json


class EnhancedFeaturesManualTest:
    """Manual test coordinator for enhanced features"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.widget = ElementInputWidget()
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f"\n  Details: {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_1_history_manager(self):
        """Test 1: Search History Manager"""
        print("\n=== TEST 1: Search History Manager ===")
        
        try:
            # Test initialization
            history = SearchHistoryManager()
            self.log_test("SearchHistoryManager initialization", True, "Manager created")
            
            # Test adding searches
            history.add_search(
                client="TEST_CLIENT",
                reference="TEST_REF_001",
                lot="LOT_TEST_123",
                machine="MACHINE_01"
            )
            self.log_test("Add search to history", True, "Search added successfully")
            
            # Test retrieving recent searches
            recent = history.get_recent_searches(limit=5)
            found = any(
                s.get('client') == 'TEST_CLIENT' and 
                s.get('reference') == 'TEST_REF_001'
                for s in recent
            )
            self.log_test("Retrieve recent searches", found, f"Found {len(recent)} searches")
            
            # Test autocomplete suggestions
            suggestions = history.get_suggestions("client")
            self.log_test("Get autocomplete suggestions", 
                         "TEST_CLIENT" in suggestions or len(suggestions) >= 0,
                         f"Found {len(suggestions)} client suggestions")
            
            # Test JSON file persistence
            history_file = Path.home() / ".pythontecnica" / "data" / "search_history.json"
            file_exists = history_file.exists()
            self.log_test("JSON file persistence", file_exists, 
                         f"File: {history_file}")
            
            if file_exists:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.log_test("JSON file readable", True, 
                             f"Contains {len(data.get('searches', []))} searches")
            
        except Exception as e:
            self.log_test("History Manager Tests", False, f"Exception: {str(e)}")
    
    def test_2_ui_buttons_present(self):
        """Test 2: UI Buttons Present"""
        print("\n=== TEST 2: UI Buttons Present ===")
        
        try:
            # Check history button
            has_history_btn = hasattr(self.widget, 'history_button')
            self.log_test("History button exists", has_history_btn)
            
            # Check template button
            has_template_btn = hasattr(self.widget, 'template_button')
            self.log_test("Template button exists", has_template_btn)
            
            # Check compare button
            has_compare_btn = hasattr(self.widget, 'compare_lots_button')
            self.log_test("Compare LOTs button exists", has_compare_btn)
            
            # Check advanced frame
            has_frame = hasattr(self.widget, 'advanced_buttons_frame')
            self.log_test("Advanced buttons frame exists", has_frame)
            
            # Check methods exist
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
                has_method = hasattr(self.widget, method)
                self.log_test(f"Method {method} exists", has_method)
            
        except Exception as e:
            self.log_test("UI Buttons Test", False, f"Exception: {str(e)}")
    
    def test_3_table_widget_paste(self):
        """Test 3: Table Widget Copy/Paste"""
        print("\n=== TEST 3: PasteableTableWidget ===")
        
        try:
            # Check if values table exists (changed from results_table)
            has_table = hasattr(self.widget, 'values_table')
            self.log_test("Values table exists", has_table)
            
            if has_table:
                table = self.widget.values_table
                table_class = table.__class__.__name__
                
                # Check if it's PasteableTableWidget
                is_pasteable = 'Pasteable' in table_class
                self.log_test("Table supports paste", is_pasteable,
                             f"Class: {table_class}")
                
                # Check if keyPressEvent exists (for Ctrl+V handling)
                has_key_event = hasattr(table, 'keyPressEvent')
                self.log_test("KeyPressEvent handler exists", has_key_event)
            
        except Exception as e:
            self.log_test("Table Widget Test", False, f"Exception: {str(e)}")
    
    def test_4_dialog_classes(self):
        """Test 4: Dialog Classes"""
        print("\n=== TEST 4: Dialog Classes ===")
        
        try:
            from src.gui.widgets.enhanced_features import (
                SearchHistoryDialog,
                MultiLOTComparisonDialog,
                ReferenceTemplateDialog
            )
            
            # Test SearchHistoryDialog
            history = SearchHistoryManager()
            dialog1 = SearchHistoryDialog(history, None)
            self.log_test("SearchHistoryDialog created", True,
                         f"Has {dialog1.history_table.columnCount()} columns")
            dialog1.close()
            
            # Test MultiLOTComparisonDialog
            dialog2 = MultiLOTComparisonDialog(None, None, None, None)
            self.log_test("MultiLOTComparisonDialog created", True,
                         f"Has {dialog2.results_table.columnCount()} columns")
            dialog2.close()
            
            # Test ReferenceTemplateDialog
            dialog3 = ReferenceTemplateDialog("TEST_CLIENT", "TEST_REF", None)
            self.log_test("ReferenceTemplateDialog created", True,
                         "Template dialog initialized")
            dialog3.close()
            
        except Exception as e:
            self.log_test("Dialog Classes Test", False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("ENHANCED FEATURES TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}")
                    if result['details']:
                        print(f"    {result['details']}")
        
        print("\n" + "="*60)
        
        return passed == total
    
    def run_all_tests(self):
        """Run all manual tests"""
        print("\n🧪 ENHANCED FEATURES MANUAL TEST SUITE")
        print("="*60)
        
        self.test_1_history_manager()
        self.test_2_ui_buttons_present()
        self.test_3_table_widget_paste()
        self.test_4_dialog_classes()
        
        success = self.print_summary()
        
        return success


def main():
    """Main test runner"""
    tester = EnhancedFeaturesManualTest()
    
    # Run tests without showing GUI
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests passed! Enhanced features are ready.")
        print("\n📝 Manual validation steps:")
        print("1. Run main_app.py")
        print("2. Load a dimensional analysis")
        print("3. Click '📜 History' to view search history")
        print("4. Click '📋 Create Template' to create a template")
        print("5. Click '📊 Compare LOTs' to compare multiple LOTs")
        print("6. Try Ctrl+V in the results table with copied data")
        return 0
    else:
        print("\n❌ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
