# src/gui/workers/dimensional_processing_thread.py
from PyQt5.QtWidgets import (
    QMessageBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import logging

from src.services.dimensional_service import DimensionalService
#from src.models.dimensional.gdt_interpreter import GDTInterpreter

class ProcessingThread(QThread):
    """Thread for processing dimensional analysis to prevent UI freezing"""

    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df

    def run(self):
        try:            
            service = DimensionalService()
            results = service.process_dataframe(
                self.df, progress_callback=self.progress_updated.emit
            )
            self.processing_finished.emit(results)
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _handle_gdt_input(self, description: str) -> str:
        """
        Handle GD&T input in description field

        Args:
            description: Raw description text

        Returns:
            Processed description with GD&T symbols preserved
        """
        # Define GD&T symbol mappings
        gdt_mappings = {
            # Geometric symbols
            "position": "⌖",
            "concentricity": "◎",
            "symmetry": "≡",
            "parallelism": "∥",
            "perpendicularity": "⊥",
            "angularity": "∠",
            "profile line": "⌒",
            "profile surface": "⌓",
            "circularity": "○",
            "cylindricity": "⌭",
            "flatness": "⏥",
            "straightness": "⏤",
            "runout": "↗",
            "total runout": "↗↗",
            # Material condition modifiers
            "(M)": "Ⓜ",
            "(L)": "Ⓛ",
            "(S)": "Ⓢ",
            # Diameter symbol
            "diameter": "Ø",
            "dia": "Ø",
            "diam": "Ø",
            "ø": "Ø",
        }

        processed_description = description

        # Apply mappings (case insensitive)
        for text, symbol in gdt_mappings.items():
            processed_description = processed_description.replace(text.lower(), symbol)
            processed_description = processed_description.replace(text.upper(), symbol)
            processed_description = processed_description.replace(text.title(), symbol)

        return processed_description

    def _validate_gdt_description(self, description: str) -> tuple[bool, list[str]]:
        """
        Validate GD&T description format

        Args:
            description: Description text to validate

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []

        # Check for common GD&T patterns
        gdt_patterns = [
            r"position\s+[\d.,]+\s*\([MLS]\)",  # position 0.5(M)
            r"parallelism\s+[\d.,]+",  # parallelism 0.1
            r"perpendicularity\s+[\d.,]+",  # perpendicularity 0.05
            r"profile\s+[\d.,]+",  # profile 0.2
            r"flatness\s+[\d.,]+",  # flatness 0.01
            r"circularity\s+[\d.,]+",  # circularity 0.05
        ]

        import re

        # Check if description contains GD&T elements
        has_gdt = any(
            re.search(pattern, description.lower()) for pattern in gdt_patterns
        )

        if has_gdt:
            # Validate datum references
            datum_pattern = r"[A-Z]\s*[A-Z]?\s*[A-Z]?"
            datums = re.findall(datum_pattern, description.upper())

            if len(datums) > 3:
                warnings.append(
                    "More than 3 datum references found - verify correctness"
                )

            # Check for material condition without tolerance
            if re.search(r"\([MLS]\)", description) and not re.search(
                r"[\d.,]+", description
            ):
                warnings.append(
                    "Material condition modifier found without tolerance value"
                )

        return True, warnings  # Always valid, but may have warnings

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            if self.unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before closing?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )

                if reply == QMessageBox.Yes:
                    if self.session_file:
                        self._save_session_to_file(self.session_file)
                    else:
                        self._save_session()
                    event.accept()
                elif reply == QMessageBox.No:
                    event.accept()
                else:
                    event.ignore()
                    return

            if self.processing_thread and self.processing_thread.isRunning():
                reply = QMessageBox.question(
                    self,
                    "Processing in Progress",
                    "Analysis is still running. Are you sure you want to close?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                else:
                    self.processing_thread.terminate()
                    self.processing_thread.wait()

            # Stop auto-save timer
            self.auto_save_timer.stop()

            self._log_message("Enhanced Dimensional Study window closed")
            event.accept()

        except Exception as e:
            logging.error(f"Processing thread error: {str(e)}")
            self.error_occurred.emit(str(e))