# src/gui/workers/dimensional_processing_thread.py
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import logging
from typing import List #Dict, Any

from src.services.dimensional_service import DimensionalService
#from src.models.dimensional.gdt_interpreter import GDTInterpreter


class ProcessingThread(QThread):
    """Thread for processing dimensional analysis with EXHAUSTIVE LOGGING"""

    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df
        self.logger = logging.getLogger(__name__)
        
        # Configure logger for detailed output
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def run(self):
        """ENHANCED run method with EXHAUSTIVE LOGGING"""
        try:
            self.logger.info("🚀 " + "="*80)
            self.logger.info("🚀 PROCESSING THREAD STARTED - EXHAUSTIVE LOGGING MODE")
            self.logger.info("🚀 " + "="*80)
            self.logger.info(f"📊 Input DataFrame shape: {self.df.shape}")
            self.logger.info(f"📊 Input DataFrame columns: {list(self.df.columns)}")
            
            # STEP 1: Exhaustive input data analysis
            self._log_exhaustive_input_analysis()
            
            # STEP 2: Separate data types with detailed logging
            notes_df, regular_df = self._separate_data_with_logging()
            
            # STEP 3: Initialize service and process data
            all_results = []
            
            # Process regular measurements
            if not regular_df.empty:
                self.logger.info("🔬 " + "="*60)
                self.logger.info("🔬 PROCESSING REGULAR MEASUREMENTS")
                self.logger.info("🔬 " + "="*60)
                regular_results = self._process_regular_measurements(regular_df)
                all_results.extend(regular_results)
                self.logger.info(f"✅ Regular processing completed: {len(regular_results)} results")
            else:
                self.logger.warning("⚠️ No regular measurements to process")
            
            # Process Notes
            if not notes_df.empty:
                self.logger.info("📝 " + "="*60)
                self.logger.info("📝 PROCESSING NOTE ENTRIES")
                self.logger.info("📝 " + "="*60)
                note_results = self._process_notes_with_logging(notes_df)
                all_results.extend(note_results)
                self.logger.info(f"✅ Note processing completed: {len(note_results)} results")
            else:
                self.logger.info("ℹ️ No Note entries to process")
            
            # STEP 4: Final validation and summary
            self._log_final_processing_summary(all_results)
            
            self.logger.info("🎉 " + "="*80)
            self.logger.info(f"🎉 TOTAL PROCESSING COMPLETED: {len(all_results)} results")
            self.logger.info("🎉 " + "="*80)
            
            self.processing_finished.emit(all_results)
            
        except Exception as e:
            error_msg = f"CRITICAL PROCESSING FAILURE: {str(e)}"
            self.logger.error("❌ " + "="*80)
            self.logger.error(f"❌ {error_msg}")
            self.logger.error("❌ FULL EXCEPTION DETAILS:")
            self.logger.error("❌ " + "="*80, exc_info=True)
            self.error_occurred.emit(error_msg)

    def _log_exhaustive_input_analysis(self):
        """EXHAUSTIVE analysis of input data"""
        self.logger.info("🔍 " + "="*60)
        self.logger.info("🔍 EXHAUSTIVE INPUT DATA ANALYSIS")
        self.logger.info("🔍 " + "="*60)
        
        # Log DataFrame info
        self.logger.info("📋 DataFrame Info:")
        self.logger.info(f"   - Shape: {self.df.shape}")
        self.logger.info(f"   - Memory usage: {self.df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        self.logger.info(f"   - Index: {self.df.index.name if self.df.index.name else 'Default'}")
        
        # Log columns with detailed analysis
        self.logger.info("📋 Column Analysis:")
        for col in self.df.columns:
            non_null_count = self.df[col].notna().sum()
            null_count = len(self.df) - non_null_count
            unique_count = self.df[col].nunique()
            dtype = self.df[col].dtype
            
            self.logger.info(f"   {col}:")
            self.logger.info(f"     - Type: {dtype}")
            self.logger.info(f"     - Non-null: {non_null_count}/{len(self.df)} ({non_null_count/len(self.df)*100:.1f}%)")
            self.logger.info(f"     - Null: {null_count}")
            self.logger.info(f"     - Unique values: {unique_count}")
            
            # Log sample values for critical columns
            if col in ['element_id', 'description', 'nominal', 'evaluation_type', 'force_status']:
                sample_values = self.df[col].dropna().head(3).tolist()
                self.logger.info(f"     - Sample values: {sample_values}")
        
        # Log evaluation types breakdown
        if 'evaluation_type' in self.df.columns:
            eval_types = self.df['evaluation_type'].value_counts(dropna=False)
            self.logger.info("📌 Evaluation Types Breakdown:")
            for eval_type, count in eval_types.items():
                percentage = (count / len(self.df)) * 100
                self.logger.info(f"   {eval_type}: {count} ({percentage:.1f}%)")
        
        # Log force status breakdown
        if 'force_status' in self.df.columns:
            force_status = self.df['force_status'].value_counts(dropna=False)
            self.logger.info("🔧 Force Status Breakdown:")
            for status, count in force_status.items():
                percentage = (count / len(self.df)) * 100
                self.logger.info(f"   {status}: {count} ({percentage:.1f}%)")
        
        # Log measurement columns analysis
        measurement_cols = [f'measurement_{i}' for i in range(1, 6)]
        available_measurement_cols = [col for col in measurement_cols if col in self.df.columns]
        
        self.logger.info("📏 Measurement Columns Analysis:")
        for col in available_measurement_cols:
            non_null = self.df[col].notna().sum()
            self.logger.info(f"   {col}: {non_null} measurements available")
        
        # Check for rows with zero measurements
        rows_with_no_measurements = 0
        for idx, row in self.df.iterrows():
            has_measurement = any(pd.notna(row.get(col)) for col in available_measurement_cols)
            if not has_measurement:
                rows_with_no_measurements += 1
        
        self.logger.info(f"⚠️ Rows with NO measurements: {rows_with_no_measurements}")
        
        # Log nominal values analysis
        if 'nominal' in self.df.columns:
            nominal_analysis = self.df['nominal'].describe()
            zero_nominals = (self.df['nominal'] == 0).sum()
            null_nominals = self.df['nominal'].isna().sum()
            
            self.logger.info("📐 Nominal Values Analysis:")
            self.logger.info(f"   - Zero nominals: {zero_nominals}")
            self.logger.info(f"   - Null nominals: {null_nominals}")
            self.logger.info(f"   - Min: {nominal_analysis['min']}")
            self.logger.info(f"   - Max: {nominal_analysis['max']}")
            self.logger.info(f"   - Mean: {nominal_analysis['mean']:.3f}")

    def _separate_data_with_logging(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Separate data with detailed logging"""
        self.logger.info("📊 " + "="*60)
        self.logger.info("📊 DATA SEPARATION PROCESS")
        self.logger.info("📊 " + "="*60)
        
        if 'evaluation_type' not in self.df.columns:
            self.logger.warning("⚠️ No 'evaluation_type' column found - treating all as regular measurements")
            notes_df = pd.DataFrame()
            regular_df = self.df.copy()
        else:
            # Separate by evaluation type
            notes_df = self.df[self.df['evaluation_type'] == 'Note'].copy()
            regular_df = self.df[self.df['evaluation_type'] != 'Note'].copy()
        
        self.logger.info("📋 Separation Results:")
        self.logger.info(f"   - Notes: {len(notes_df)} records")
        self.logger.info(f"   - Regular measurements: {len(regular_df)} records")
        self.logger.info(f"   - Total: {len(notes_df) + len(regular_df)} records")
        
        # Validate separation
        if len(notes_df) + len(regular_df) != len(self.df):
            self.logger.error("❌ DATA SEPARATION ERROR: Row count mismatch!")
            self.logger.error(f"   Original: {len(self.df)}")
            self.logger.error(f"   Notes + Regular: {len(notes_df) + len(regular_df)}")
        
        # Log sample element_ids for each type
        if not notes_df.empty and 'element_id' in notes_df.columns:
            sample_note_ids = notes_df['element_id'].head(3).tolist()
            self.logger.info(f"   - Sample Note IDs: {sample_note_ids}")
        
        if not regular_df.empty and 'element_id' in regular_df.columns:
            sample_regular_ids = regular_df['element_id'].head(3).tolist()
            self.logger.info(f"   - Sample Regular IDs: {sample_regular_ids}")
        
        return notes_df, regular_df

    def _process_regular_measurements(self, regular_df: pd.DataFrame) -> List:
        """Process regular measurements with exhaustive logging"""
        self.logger.info(f"🔬 Processing {len(regular_df)} regular measurement records")
        
        try:
            service = DimensionalService()
            self.logger.info("✅ DimensionalService initialized successfully")
            
            # Process with progress callback
            results = service.process_dataframe(
                regular_df, 
                progress_callback=self._emit_progress_with_logging
            )
            
            self.logger.info(f"✅ Service returned {len(results)} results")
            
            # Log results breakdown
            self._log_results_breakdown(results, "REGULAR")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ ERROR in regular measurements processing: {str(e)}")
            self.logger.error("❌ Regular measurements processing FAILED", exc_info=True)
            raise

    def _process_notes_with_logging(self, notes_df: pd.DataFrame) -> List:
        """Process Note entries with detailed logging"""
        self.logger.info(f"📝 Processing {len(notes_df)} Note records")
        
        results = []
        
        for idx, row in notes_df.iterrows():
            try:
                element_id = row.get('element_id', f'Note_{idx}')
                force_status = row.get('force_status', 'AUTO')
                description = row.get('description', '')
                
                self.logger.debug(f"📝 Processing Note: {element_id}")
                self.logger.debug(f"   - Force Status: {force_status}")
                self.logger.debug(f"   - Description: {description[:50]}...")
                
                # Create a simplified result for Notes
                # Notes should use force_status to determine GOOD/BAD
                from src.models.dimensional.dimensional_result import DimensionalResult, DimensionalStatus
                
                # Determine status based on force_status
                if force_status == 'GOOD':
                    status = DimensionalStatus.GOOD
                    warnings = ["Note entry - Status set to GOOD by user"]
                elif force_status == 'BAD':
                    status = DimensionalStatus.BAD
                    warnings = ["Note entry - Status set to BAD by user"]
                else:  # AUTO or any other value
                    status = DimensionalStatus.GOOD  # Default for notes
                    warnings = ["Note entry - Defaulted to GOOD (use force_status to override)"]
                
                result = DimensionalResult(
                    element_id=str(element_id),
                    batch=str(row.get('batch', 'Unknown')),
                    cavity=str(row.get('cavity', 'Unknown')),
                    classe=str(row.get('class', 'Unknown')),
                    description=str(description),
                    nominal=0.0,  # Notes don't have meaningful nominals
                    lower_tolerance=None,
                    upper_tolerance=None,
                    measurements=[],  # Notes don't have measurements
                    deviation=[],
                    mean=0.0,
                    std_dev=0.0,
                    out_of_spec_count=0,
                    status=status,
                    gdt_flags={'IS_NOTE': True},
                    datum_element_id=row.get('datum_element_id'),
                    effective_tolerance_upper=None,
                    effective_tolerance_lower=None,
                    feature_type='note',
                    warnings=warnings,
                )
                
                results.append(result)
                self.logger.debug(f"✅ Note {element_id} processed successfully - Status: {status.value}")
                
            except Exception as e:
                element_id = row.get('element_id', f'Note_{idx}')
                self.logger.error(f"❌ Error processing Note {element_id}: {str(e)}")
                continue
        
        self.logger.info(f"✅ Note processing completed: {len(results)} results")
        self._log_results_breakdown(results, "NOTES")
        
        return results

    def _emit_progress_with_logging(self, progress: int):
        """Emit progress with logging"""
        if progress % 10 == 0:  # Log every 10%
            self.logger.info(f"📈 Progress: {progress}%")
        self.progress_updated.emit(progress)

    def _log_results_breakdown(self, results: List, category: str):
        """Log detailed breakdown of results"""
        if not results:
            self.logger.warning(f"⚠️ No results to analyze for {category}")
            return
        
        self.logger.info(f"📊 {category} RESULTS BREAKDOWN:")
        
        # Status breakdown
        status_counts = {}
        for result in results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            percentage = (count / len(results)) * 100
            self.logger.info(f"   {status}: {count} ({percentage:.1f}%)")
        
        # Warning analysis
        total_warnings = sum(len(result.warnings) for result in results)
        results_with_warnings = sum(1 for result in results if result.warnings)
        
        self.logger.info("⚠️ Warnings Analysis:")
        self.logger.info(f"   - Total warnings: {total_warnings}")
        self.logger.info(f"   - Results with warnings: {results_with_warnings}/{len(results)}")
        
        # Feature type breakdown for regular measurements
        if category == "REGULAR":
            feature_types = {}
            for result in results:
                ft = result.feature_type
                feature_types[ft] = feature_types.get(ft, 0) + 1
            
            self.logger.info("Feature Types:")
            for ft, count in feature_types.items():
                self.logger.info(f"   {ft}: {count}")

    def _log_final_processing_summary(self, all_results: List):
        """Log comprehensive final summary"""
        self.logger.info("📋 " + "="*60)
        self.logger.info("📋 FINAL PROCESSING SUMMARY")
        self.logger.info("📋 " + "="*60)
        
        if not all_results:
            self.logger.error("❌ NO RESULTS GENERATED!")
            return
        
        # Overall statistics
        total = len(all_results)
        good_count = sum(1 for r in all_results if r.status.value == "GOOD")
        bad_count = sum(1 for r in all_results if r.status.value == "BAD")
        warning_count = sum(1 for r in all_results if r.status.value == "WARNING")
        
        self.logger.info("📊 Overall Statistics:")
        self.logger.info(f" - Total processed: {total}")
        self.logger.info(f" - GOOD: {good_count} ({good_count/total*100:.1f}%)")
        self.logger.info(f" - BAD: {bad_count} ({bad_count/total*100:.1f}%)")
        self.logger.info(f" - WARNING: {warning_count} ({warning_count/total*100:.1f}%)")
        
        # Success rate
        success_rate = (good_count / total) * 100 if total > 0 else 0
        self.logger.info(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Notes vs Regular breakdown
        notes = sum(1 for r in all_results if r.feature_type == 'note')
        regular = total - notes
        
        self.logger.info("📝 Composition:")
        self.logger.info(f"   - Notes: {notes}")
        self.logger.info(f"   - Regular measurements: {regular}")
        
        # Error analysis
        results_with_errors = sum(1 for r in all_results if any('error' in w.lower() for w in r.warnings))
        self.logger.info(f"❌ Results with errors: {results_with_errors}")
        
        # Sample problematic results
        bad_results = [r for r in all_results if r.status.value == "BAD"]
        if bad_results:
            self.logger.info("Sample BAD results:")
            for i, result in enumerate(bad_results[:3]):  # Show first 3
                self.logger.info(f"   {i+1}. {result.element_id}: {result.warnings}")

    def _emit_progress(self, progress: int):
        """Simple progress emission"""
        self.progress_updated.emit(progress)

    def closeEvent(self, event):
        """Handle window close event - FIXED"""
        try:
            # This method seems to be misplaced - it should be in the main window, not the thread
            # For now, just pass
            pass
        except Exception as e:
            self.logger.error(f"Processing thread closeEvent error: {str(e)}")