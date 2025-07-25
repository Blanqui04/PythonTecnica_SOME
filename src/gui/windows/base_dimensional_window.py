# src/gui/windows/base_dimensional_window.py
from PyQt5.QtWidgets import (QMainWindow)
import logging

from datetime import datetime


class BaseDimensionalWindow(QMainWindow):
    """Base class for dimensional study windows with common functionality"""
    
    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__()
        self.client_name = client
        self.project_ref = ref_project
        self.batch_number = batch_number
        self.unsaved_changes = False
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for the dimensional study"""
        logger = logging.getLogger(
            f"DimensionalStudy_{self.client_name}_{self.project_ref}"
        )
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _log_message(self, message: str, level: str = "INFO"):
        """Add message to log area and logger"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, 'log_area'):
            self.log_area.append(f"[{timestamp}] [{level}] {message}")
        getattr(self.logger, level.lower())(message)
    
    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + " *")
    
    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.unsaved_changes = False
        title = self.windowTitle()
        if title.endswith(" *"):
            self.setWindowTitle(title[:-2])