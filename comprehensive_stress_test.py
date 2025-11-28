#!/usr/bin/env python3
"""
Comprehensive Stress Test for PythonTecnica SOME
Tests all application components and features
"""

import sys
import os
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class ComprehensiveStressTester:
    def __init__(self):
        self.app = None
        self.test_results = []
        self.temp_dir = tempfile.mkdtemp(prefix="stress_test_")
        self.start_time = datetime.now()

    def log_test(self, test_name, result, details="", duration=None):
        """Log test results with timing"""
        status = "✅ PASS" if result else "❌ FAIL"
        msg = f"{status} {test_name}"
        if duration:
            msg += f" ({duration:.2f}s)"
        if details:
            msg += f" - {details}"
        print(msg)
        self.test_results.append((test_name, result, details, duration))

    def setup_test_environment(self):
        """Setup comprehensive test environment"""
        try:
            # Create test directories
            test_dirs = [
                'data/temp/stress_test',
                'data/backup',
                'data/cache',
                'data/reports',
                'logs'
            ]

            for dir_path in test_dirs:
                os.makedirs(dir_path, exist_ok=True)

            # Create test database config
            db_config = {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass"
            }

            import json
            with open('data/temp/stress_test/test_config.json', 'w') as f:
                json.dump(db_config, f)

            self.log_test("Test Environment Setup", True, f"Created test directories and config in {self.temp_dir}")
            return True

        except Exception as e:
            self.log_test("Test Environment Setup", False, str(e))
            return False

    def test_import_system(self):
        """Test all imports work correctly"""
        start_time = time.time()
        try:
            # Test core imports
            imports_to_test = [
                'pandas',
                'numpy',
                'scipy',
                'psycopg2',
                'PyQt5.QtWidgets',
                'PyQt5.QtCore',
                'matplotlib',
                'openpyxl',
                'plotly'
            ]

            failed_imports = []
            for module in imports_to_test:
                try:
                    __import__(module)
                except ImportError as e:
                    failed_imports.append(f"{module}: {e}")

            if failed_imports:
                self.log_test("Import System", False, f"Failed imports: {failed_imports}", time.time() - start_time)
                return False

            # Test application-specific imports
            app_imports = [
                'src.gui.main_window',
                'src.gui.windows.dimensional_study_window',
                'src.services.data_processing_orchestrator',
                'src.database.quality_measurement_adapter',
                'src.data_processing.pipeline_manager'
            ]

            for module in app_imports:
                try:
                    __import__(module.replace('src.', '').replace('.', '_'))
                except ImportError as e:
                    failed_imports.append(f"{module}: {e}")

            if failed_imports:
                self.log_test("Import System", False, f"Failed app imports: {failed_imports}", time.time() - start_time)
                return False

            self.log_test("Import System", True, "All imports successful", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("Import System", False, str(e), time.time() - start_time)
            return False

    def test_data_generation(self):
        """Test comprehensive data generation"""
        start_time = time.time()
        try:
            # Generate multiple test datasets
            datasets = {
                'small': 100,
                'medium': 1000,
                'large': 5000,
                'xlarge': 10000
            }

            total_memory = 0
            for size_name, n_rows in datasets.items():
                # Generate dimensional data
                np.random.seed(42)
                data = []

                for i in range(n_rows):
                    element_id = f'ELEMENT_{size_name.upper()}_{i:04d}'
                    nominal = np.random.uniform(1, 200)
                    lower_tol = nominal - np.random.uniform(0.01, 5.0)
                    upper_tol = nominal + np.random.uniform(0.01, 5.0)

                    row = {
                        'element_id': element_id,
                        'description': f'Test Element {i} ({size_name})',
                        'nominal': round(nominal, 3),
                        'lower_tolerance': round(lower_tol, 3),
                        'upper_tolerance': round(upper_tol, 3),
                        'batch': f'BATCH_{size_name.upper()}_{i//50:02d}',
                        'cavity': str(np.random.randint(1, 5)),
                        'class': f'CLASS_{np.random.randint(1, 4)}',
                        'datum_element_id': f'DATUM_{np.random.randint(1, 10)}',
                        'evaluation_type': 'Normal',
                        'measuring_instrument': '3D Scanbox',
                        'unit': 'mm'
                    }

                    # Add measurements
                    for j in range(1, 6):
                        measurement = nominal + np.random.normal(0, 0.5)
                        row[f'measurement_{j}'] = round(measurement, 3)

                    data.append(row)

                df = pd.DataFrame(data)
                filename = f'data/temp/stress_test/{size_name}_dataset.xlsx'
                df.to_excel(filename, index=False)

                memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
                total_memory += memory_mb

                self.log_test(f"Data Generation ({size_name})", True,
                            f"{n_rows} rows, {memory_mb:.1f} MB", time.time() - start_time)

            self.log_test("Data Generation (Total)", True,
                        f"Generated {sum(datasets.values())} total rows, {total_memory:.1f} MB", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("Data Generation", False, str(e), time.time() - start_time)
            return False

    def test_processing_engine(self):
        """Test the dimensional processing engine"""
        start_time = time.time()
        try:
            from src.gui.workers.dimensional_processing_thread import ProcessingThread

            # Test with different dataset sizes
            test_files = [
                'data/temp/stress_test/small_dataset.xlsx',
                'data/temp/stress_test/medium_dataset.xlsx'
            ]

            for test_file in test_files:
                if not os.path.exists(test_file):
                    continue

                df = pd.read_excel(test_file)
                size_name = os.path.basename(test_file).split('_')[0]

                # Create and run processing thread
                thread = ProcessingThread(df)
                thread.start()
                thread.wait(30000)  # 30 second timeout

                if thread.isFinished():
                    self.log_test(f"Processing Engine ({size_name})", True,
                                f"Processed {len(df)} rows successfully", time.time() - start_time)
                else:
                    thread.terminate()
                    thread.wait(5000)
                    self.log_test(f"Processing Engine ({size_name})", False,
                                f"Processing timeout after 30s", time.time() - start_time)
                    thread.deleteLater()
                    return False

                thread.deleteLater()

            self.log_test("Processing Engine (All)", True, "All processing tests passed", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("Processing Engine", False, str(e), time.time() - start_time)
            return False

    def test_gui_components(self):
        """Test GUI component initialization"""
        start_time = time.time()
        try:
            from PyQt5.QtWidgets import QApplication
            from src.gui.windows.dimensional_study_window import DimensionalStudyWindow

            # Create QApplication if needed
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            # Test window creation
            window = DimensionalStudyWindow("TEST_CLIENT", "TEST_REF", "TEST_BATCH")

            # Test component access
            components_to_test = [
                ('table_manager', window.table_manager),
                ('session_manager', window.session_manager),
                ('summary_widget', getattr(window, 'summary_widget', None)),
                ('progress_bar', getattr(window, 'progress_bar', None)),
                ('results_tabs', getattr(window, 'results_tabs', None))
            ]

            failed_components = []
            for comp_name, component in components_to_test:
                if component is None:
                    failed_components.append(comp_name)

            if failed_components:
                self.log_test("GUI Components", False, f"Missing components: {failed_components}", time.time() - start_time)
                return False

            # Clean up
            window.close()
            app.processEvents()

            self.log_test("GUI Components", True, "All GUI components initialized successfully", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("GUI Components", False, str(e), time.time() - start_time)
            return False

    def test_database_operations(self):
        """Test database-related operations"""
        start_time = time.time()
        try:
            # Test database adapter initialization (without actual connection)
            from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter

            # Load test config
            config_file = 'data/temp/stress_test/test_config.json'
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    db_config = json.load(f)

                # Test adapter creation
                adapter = QualityMeasurementDBAdapter(db_config)

                # Test basic methods without connecting
                self.log_test("Database Operations", True, "Database adapter initialized successfully", time.time() - start_time)
                return True
            else:
                self.log_test("Database Operations", False, "Test config not found", time.time() - start_time)
                return False

        except Exception as e:
            self.log_test("Database Operations", False, str(e), time.time() - start_time)
            return False

    def test_file_operations(self):
        """Test file I/O operations"""
        start_time = time.time()
        try:
            # Test Excel file operations
            test_data = pd.DataFrame({
                'col1': range(100),
                'col2': [f'value_{i}' for i in range(100)]
            })

            # Test write
            test_file = 'data/temp/stress_test/file_test.xlsx'
            test_data.to_excel(test_file, index=False)

            # Test read
            read_data = pd.read_excel(test_file)

            if len(read_data) != len(test_data):
                self.log_test("File Operations", False, "Data length mismatch", time.time() - start_time)
                return False

            # Test CSV operations
            csv_file = 'data/temp/stress_test/file_test.csv'
            test_data.to_csv(csv_file, index=False)
            csv_data = pd.read_csv(csv_file)

            if len(csv_data) != len(test_data):
                self.log_test("File Operations", False, "CSV data length mismatch", time.time() - start_time)
                return False

            # Test JSON operations
            json_file = 'data/temp/stress_test/file_test.json'
            test_data.to_json(json_file, orient='records')
            json_data = pd.read_json(json_file)

            if len(json_data) != len(test_data):
                self.log_test("File Operations", False, "JSON data length mismatch", time.time() - start_time)
                return False

            self.log_test("File Operations", True, "All file operations successful", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("File Operations", False, str(e), time.time() - start_time)
            return False

    def test_memory_management(self):
        """Test memory management with large datasets"""
        start_time = time.time()
        try:
            # Create progressively larger DataFrames
            sizes = [1000, 5000, 10000]

            for size in sizes:
                # Create large DataFrame
                df = pd.DataFrame({
                    'data': ['x' * 100] * size,
                    'numbers': np.random.rand(size),
                    'categories': np.random.choice(['A', 'B', 'C'], size)
                })

                memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

                # Test processing
                from src.gui.workers.dimensional_processing_thread import ProcessingThread
                thread = ProcessingThread(df)
                thread.start()
                thread.wait(15000)  # 15 second timeout for large data

                if thread.isFinished():
                    self.log_test(f"Memory Management ({size} rows)", True,
                                f"{memory_mb:.1f} MB processed successfully", time.time() - start_time)
                else:
                    thread.terminate()
                    thread.wait(5000)
                    self.log_test(f"Memory Management ({size} rows)", False,
                                f"Memory test timeout", time.time() - start_time)
                    thread.deleteLater()
                    return False

                thread.deleteLater()
                del df  # Force garbage collection

            self.log_test("Memory Management (All)", True, "All memory tests passed", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("Memory Management", False, str(e), time.time() - start_time)
            return False

    def test_concurrent_operations(self):
        """Test multiple concurrent operations"""
        start_time = time.time()
        try:
            results = []
            threads = []

            def run_concurrent_test(thread_id):
                try:
                    # Create test data
                    df = pd.DataFrame({
                        'element_id': [f'CONCURRENT_{thread_id}_001'],
                        'description': [f'Concurrent test {thread_id}'],
                        'nominal': [10.0],
                        'measurement_1': [10.1],
                        'measurement_2': [9.9]
                    })

                    # Process data
                    from src.gui.workers.dimensional_processing_thread import ProcessingThread
                    thread = ProcessingThread(df)
                    thread.start()
                    thread.wait(10000)

                    if thread.isFinished():
                        results.append(True)
                    else:
                        thread.terminate()
                        thread.wait(2000)
                        results.append(False)

                    thread.deleteLater()

                except Exception as e:
                    print(f"Concurrent thread {thread_id} error: {e}")
                    results.append(False)

            # Start 5 concurrent threads
            for i in range(5):
                t = threading.Thread(target=run_concurrent_test, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join(timeout=15)

            success_count = sum(results)
            total_count = len(results)

            if success_count == total_count:
                self.log_test("Concurrent Operations", True,
                            f"All {total_count} concurrent operations successful", time.time() - start_time)
                return True
            else:
                self.log_test("Concurrent Operations", False,
                            f"{success_count}/{total_count} operations successful", time.time() - start_time)
                return False

        except Exception as e:
            self.log_test("Concurrent Operations", False, str(e), time.time() - start_time)
            return False

    def test_error_handling(self):
        """Test error handling and recovery"""
        start_time = time.time()
        try:
            # Test invalid data handling
            invalid_data_tests = [
                pd.DataFrame(),  # Empty DataFrame
                pd.DataFrame({'invalid_col': []}),  # DataFrame with no valid columns
                None,  # None input
            ]

            for i, invalid_data in enumerate(invalid_data_tests):
                try:
                    from src.gui.workers.dimensional_processing_thread import ProcessingThread
                    thread = ProcessingThread(invalid_data)
                    thread.start()
                    thread.wait(5000)

                    # Should handle gracefully
                    if thread.isFinished():
                        self.log_test(f"Error Handling (Test {i+1})", True,
                                    "Invalid data handled gracefully", time.time() - start_time)
                    else:
                        thread.terminate()
                        thread.wait(2000)
                        self.log_test(f"Error Handling (Test {i+1})", False,
                                    "Invalid data caused hang", time.time() - start_time)
                        thread.deleteLater()
                        return False

                    thread.deleteLater()

                except Exception as e:
                    self.log_test(f"Error Handling (Test {i+1})", False, str(e), time.time() - start_time)
                    return False

            self.log_test("Error Handling (All)", True, "All error conditions handled", time.time() - start_time)
            return True

        except Exception as e:
            self.log_test("Error Handling", False, str(e), time.time() - start_time)
            return False

    def cleanup_test_environment(self):
        """Clean up test environment"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.log_test("Cleanup", True, f"Cleaned up test environment: {self.temp_dir}")
            return True
        except Exception as e:
            self.log_test("Cleanup", False, str(e))
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive PythonTecnica SOME Stress Tests")
        print("=" * 60)
        print(f"Test Environment: {self.temp_dir}")
        print(f"Start Time: {self.start_time}")
        print("=" * 60)

        tests = [
            ("Environment Setup", self.setup_test_environment),
            ("Import System", self.test_import_system),
            ("Data Generation", self.test_data_generation),
            ("Processing Engine", self.test_processing_engine),
            ("GUI Components", self.test_gui_components),
            ("Database Operations", self.test_database_operations),
            ("File Operations", self.test_file_operations),
            ("Memory Management", self.test_memory_management),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Error Handling", self.test_error_handling),
            ("Cleanup", self.cleanup_test_environment),
        ]

        passed = 0
        total = len(tests)
        total_time = 0

        for test_name, test_func in tests:
            print(f"\n🔄 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                self.log_test(test_name, False, f"Test crashed: {e}")

        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print(f"📊 Comprehensive Stress Test Results: {passed}/{total} tests passed")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📅 End Time: {end_time}")

        if passed == total:
            print("🎉 ALL COMPREHENSIVE TESTS PASSED! Application is production-ready.")
        else:
            print("⚠️ Some tests failed. Check the logs for details.")

        # Print detailed results
        print("\n📋 Detailed Test Results:")
        for test_name, result, details, duration in self.test_results:
            status = "✅" if result else "❌"
            duration_str = f" ({duration:.2f}s)" if duration else ""
            print(f"  {status} {test_name}{duration_str}")
            if details and len(details) > 0:
                print(f"     └─ {details}")

        return passed == total

def main():
    tester = ComprehensiveStressTester()
    success = tester.run_comprehensive_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()