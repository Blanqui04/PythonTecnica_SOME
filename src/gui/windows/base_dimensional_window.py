# src/gui/windows/base_dimensional_window.py
from PyQt5.QtWidgets import QMainWindow
import logging
from pathlib import Path
from datetime import datetime  # Correct import for datetime.now()
import os

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
        """Setup comprehensive logging for the dimensional study"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create a logger with client/project name
        logger_name = f"DimensionalStudy.{self.client_name}.{self.project_ref}.{self.batch_number}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Only add handlers if they haven't been added before
        if not logger.handlers:
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            
            # File handler for dimensional.log
            file_handler = logging.FileHandler(
                logs_dir / "dimensional.log",
                mode='a',  # Append mode
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            logger.addHandler(file_handler)
            
            # Stream handler for console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)  # Only show INFO+ in console
            logger.addHandler(console_handler)
            
            # Add process ID and thread info
            old_factory = logging.getLogRecordFactory()
            
            def record_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                record.pid = os.getpid()
                return record
                
            logging.setLogRecordFactory(record_factory)
            
            logger.debug("Logger initialized for %s/%s (Batch %s)", 
                        self.client_name, self.project_ref, self.batch_number)
            
        return logger
    
    def _log_message(self, message: str, level: str = "INFO"):
        """
        Add message to log area and logger with enhanced tracking.
        Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Log to GUI if available
        if hasattr(self, 'log_area'):
            try:
                self.log_area.append(f"[{timestamp}] [{level}] {message}")
                # Auto-scroll to bottom
                self.log_area.verticalScrollBar().setValue(
                    self.log_area.verticalScrollBar().maximum()
                )
            except Exception as e:
                print(f"Failed to log to GUI: {str(e)}")
        
        # Log to file and console using the logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        # Include caller information for debugging
        try:
            import inspect
            frame = inspect.currentframe().f_back
            caller_info = f" (Called from {frame.f_code.co_filename}:{frame.f_lineno})"
            full_message = f"{message}{caller_info}"
        except Exception:
            full_message = message
            
        log_method(full_message)
        
        # For errors, also log stack trace
        if level in ("ERROR", "CRITICAL"):
            self.logger.debug("Stack trace:", exc_info=True)
    
    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes and log the action"""
        if not self.unsaved_changes:
            self.logger.debug("Marking document as having unsaved changes")
            self.unsaved_changes = True
            if not self.windowTitle().endswith("*"):
                self.setWindowTitle(self.windowTitle() + " *")
    
    def _clear_unsaved_changes(self):
        """Clear the unsaved changes flag and log the action"""
        if self.unsaved_changes:
            self.logger.debug("Clearing unsaved changes flag")
            self.unsaved_changes = False
            title = self.windowTitle()
            if title.endswith(" *"):
                self.setWindowTitle(title[:-2])
    
    def closeEvent(self, event):
        """Handle window close event with proper logging"""
        self.logger.info("Window closing - client: %s, project: %s, batch: %s",
                        self.client_name, self.project_ref, self.batch_number)
        
        # Clean up logging handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
            
        super().closeEvent(event)