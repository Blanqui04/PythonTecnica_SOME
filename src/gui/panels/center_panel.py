from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QTextEdit, QScrollArea, 
                             QTabWidget, QWidget, QHBoxLayout, QPushButton, 
                             QLabel, QStackedLayout, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
import platform
import subprocess

# Import shared logger
from src.gui.logging_config import logger
from src.database.database_uploader import DatabaseUploader

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not available. PDF preview functionality will be limited.")


class PDFViewer(QLabel):
    """Custom PDF viewer widget"""
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px dashed #ccc;
                border-radius: 8px;
                color: #666;
                font-size: 14px;
            }
        """)
        self.setText("PDF Preview\n\nClick 'View PDF Plan' to load and preview a PDF")
        self.setMinimumSize(400, 500)
        self.current_pdf_doc = None
        self.current_page = 0
        self.zoom_factor = 1.0
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def load_pdf_from_data(self, pdf_data, filename):
        """Load PDF from binary data"""
        if not FITZ_AVAILABLE:
            self.setText(f"PDF: {filename}\n\nPyMuPDF not available for preview.\nClick 'Open External' to view the PDF.")
            return False
            
        try:
            # Create a PDF document from binary data
            self.current_pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
            self.current_page = 0
            self.zoom_factor = 1.0
            self.display_current_page()
            return True
        except Exception as e:
            self.setText(f"Error loading PDF:\n{str(e)}")
            logger.error(f"Error loading PDF: {e}")
            return False
            
    def display_current_page(self):
        """Display the current page of the PDF"""
        if not self.current_pdf_doc or not FITZ_AVAILABLE:
            return
            
        try:
            # Get the page
            page = self.current_pdf_doc[self.current_page]
            
            # Create a matrix for zoom
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            
            # Render page to image
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimg = QPixmap()
            qimg.loadFromData(img_data)
            
            # Scale to fit the widget while maintaining aspect ratio
            scaled_pixmap = qimg.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
                
        except Exception as e:
            self.setText(f"Error displaying PDF page:\n{str(e)}")
            logger.error(f"Error displaying PDF page: {e}")
            
    def zoom_in(self):
        """Zoom in"""
        if not FITZ_AVAILABLE:
            return
        self.zoom_factor = min(self.zoom_factor * 1.2, 3.0)
        self.display_current_page()
        
    def zoom_out(self):
        """Zoom out"""
        if not FITZ_AVAILABLE:
            return
        self.zoom_factor = max(self.zoom_factor / 1.2, 0.3)
        self.display_current_page()
        
    def reset_zoom(self):
        """Reset zoom to fit"""
        if not FITZ_AVAILABLE:
            return
        self.zoom_factor = 1.0
        self.display_current_page()
        
    def clear_pdf(self):
        """Clear the current PDF"""
        if self.current_pdf_doc:
            self.current_pdf_doc.close()
            self.current_pdf_doc = None
        self.clear()
        self.setText("PDF Preview\n\nClick 'View PDF Plan' to load and preview a PDF")
    
    def resizeEvent(self, event):
        """Handle resize events to update PDF display"""
        super().resizeEvent(event)
        if self.current_pdf_doc and FITZ_AVAILABLE:
            # Redisplay current page with new size
            self.display_current_page()


class PDFLoadThread(QThread):
    """Thread for loading PDF data"""
    pdf_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client, ref_project, ref_client):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.ref_client = ref_client
        
    def run(self):
        try:
            uploader = DatabaseUploader(self.client, self.ref_project)
            result = uploader.get_planol_pdf(self.ref_client)
            self.pdf_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class CenterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Visualizer & PDF Viewer", parent)
        logger.debug("Initializing [CenterPanel]")
        self.current_pdf_path = None
        self.current_pdf_data = None
        self.setup_ui()
        logger.info("[CenterPanel] initialized successfully")

    def setup_ui(self):
        logger.debug("Setting up UI for [CenterPanel]")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget for different view modes
        self.tab_widget = QTabWidget()
        
        # Text tab - for text content and visualizations
        text_tab = QWidget()
        text_layout = QVBoxLayout()
        
        # Create text widget (visualizer)
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.text_widget.setPlainText("Welcome to Database Management System\n\n"
                                      "Use the search fields above to find data.\n"
                                      "Select actions from the side panels to process data.\n\n"
                                      "Results and visualizations will appear here.")
        self.text_widget.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                color: #495057;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        
        # Create scroll area for text widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        scroll_area.setWidget(self.text_widget)
        
        text_layout.addWidget(scroll_area)
        text_tab.setLayout(text_layout)
        
        # PDF tab - for PDF viewing
        pdf_tab = QWidget()
        pdf_layout = QVBoxLayout()
        
        # PDF controls
        controls_layout = QHBoxLayout()
        
        self.view_pdf_btn = QPushButton("View PDF Plan")
        self.view_pdf_btn.clicked.connect(self.view_pdf_plan)
        
        self.open_external_btn = QPushButton("Open External")
        self.open_external_btn.clicked.connect(self.open_external_pdf)
        self.open_external_btn.setEnabled(False)
        
        if FITZ_AVAILABLE:
            self.zoom_in_btn = QPushButton("Zoom In")
            self.zoom_in_btn.clicked.connect(self.zoom_in)
            
            self.zoom_out_btn = QPushButton("Zoom Out")
            self.zoom_out_btn.clicked.connect(self.zoom_out)
            
            self.reset_zoom_btn = QPushButton("Reset Zoom")
            self.reset_zoom_btn.clicked.connect(self.reset_zoom)
            
            controls_layout.addWidget(self.zoom_in_btn)
            controls_layout.addWidget(self.zoom_out_btn)
            controls_layout.addWidget(self.reset_zoom_btn)
        
        controls_layout.addWidget(self.view_pdf_btn)
        controls_layout.addWidget(self.open_external_btn)
        controls_layout.addStretch()
        
        # PDF info label
        self.pdf_info_label = QLabel("No PDF loaded")
        self.pdf_info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        
        # PDF viewer
        self.pdf_viewer = PDFViewer()
        
        pdf_layout.addLayout(controls_layout)
        pdf_layout.addWidget(self.pdf_info_label)
        pdf_layout.addWidget(self.pdf_viewer)
        pdf_tab.setLayout(pdf_layout)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(text_tab, "Text Viewer")
        self.tab_widget.addTab(pdf_tab, "PDF Viewer")
        
        # Create stacked layout for backwards compatibility
        self.stacked_layout = QStackedLayout()
        
        # Mode 2: Custom widget view (e.g., interactive form or preview)
        self.custom_widget_container = QWidget()  # Placeholder, can be replaced dynamically
        
        # Add tab widget as the primary view (index 0)
        # Add custom widget container for special cases (index 1)
        self.stacked_layout.addWidget(self.tab_widget)
        self.stacked_layout.addWidget(self.custom_widget_container)
        
        # Set default to tab widget view
        self.stacked_layout.setCurrentIndex(0)
        
        layout.addLayout(self.stacked_layout)
        self.setLayout(layout)

        # Create alias for backward compatibility
        self.visualizer = self.text_widget

    def update_content(self, content: str):
        """Update visualizer text content and switch to text mode."""
        logger.debug(f"Updating content in [CenterPanel]: {content[:60]}{'...' if len(content) > 60 else ''}")
        self.text_widget.setPlainText(content)
        # Ensure we're showing the tab widget and switch to text tab
        self.stacked_layout.setCurrentIndex(0)
        self.tab_widget.setCurrentIndex(0)
        logger.info("Visualizer content updated")

    def set_custom_widget(self, widget):
        """Set a custom widget and switch to custom view mode"""
        # Remove old widget if exists
        old_widget = self.stacked_layout.widget(1)
        if old_widget:
            self.stacked_layout.removeWidget(old_widget)
            old_widget.deleteLater()
        
        # Add new custom widget
        self.stacked_layout.addWidget(widget)
        self.custom_widget_container = widget
        
        # Switch to custom widget view
        self.stacked_layout.setCurrentIndex(1)
        logger.info("Switched to custom widget view")

    def show_custom_widget(self, widget):
        """Show a custom widget (alias for set_custom_widget for backward compatibility)"""
        self.set_custom_widget(widget)

    def reset_to_text_view(self):
        """Reset to text view mode (switch back from custom widget to tab widget and text tab)"""
        # Switch back to tab widget view
        self.stacked_layout.setCurrentIndex(0)
        # Switch to text tab
        self.tab_widget.setCurrentIndex(0)
        logger.info("Reset to text view mode")

    def update_pdf_info(self, info):
        """Update PDF info label"""
        self.pdf_info_label.setText(info)

    def view_pdf_plan(self):
        """View PDF plan from database"""
        try:
            # Get parent window to access header panel
            parent_window = self.parent()
            while parent_window and not hasattr(parent_window, 'header'):
                parent_window = parent_window.parent()
            
            if not parent_window:
                self.update_content("Error: Could not find parent window with header panel")
                return
                
            # Get project reference (primary requirement)
            ref_project = parent_window.header.ref_project_edit.text().strip()
            ref_client = parent_window.header.ref_client_edit.text().strip()
            
            # Only project reference is required now
            if not ref_project:
                self.update_content("Please enter Project Reference to view PDF plans.")
                return
                
            # Use client reference as the search key (or project reference if client not available)
            search_key = ref_client if ref_client else ref_project
                
            # Switch to tab widget view and PDF tab
            self.stacked_layout.setCurrentIndex(0)
            self.tab_widget.setCurrentIndex(1)
            self.update_pdf_info("Loading PDF...")
            
            # Start PDF loading in thread using search_key as the client reference
            self.pdf_thread = PDFLoadThread(search_key, ref_project, search_key)
            self.pdf_thread.pdf_loaded.connect(self.on_pdf_loaded)
            self.pdf_thread.error_occurred.connect(self.on_pdf_error)
            self.pdf_thread.start()
            
        except Exception as e:
            logger.error(f"Error in view_pdf_plan: {e}")
            self.update_content(f"Error viewing PDF plan: {str(e)}")

    def on_pdf_loaded(self, pdf_result):
        """Handle PDF loaded from thread"""
        try:
            if pdf_result['success']:
                # Save PDF to temporary file
                uploader = DatabaseUploader("", "")  # We just need the save method
                temp_path = uploader.save_temp_pdf(pdf_result['pdf_data'], pdf_result['filename'])
                
                if temp_path:
                    # Load PDF preview
                    preview_success = self.load_pdf_preview(
                        pdf_result['pdf_data'], 
                        pdf_result['filename'], 
                        temp_path
                    )
                    
                    if preview_success:
                        self.update_pdf_info(f"Loaded: {pdf_result['filename']} (Plan: {pdf_result['num_planol']})")
                        self.open_external_btn.setEnabled(True)
                    else:
                        self.update_pdf_info(f"Error loading preview: {pdf_result['filename']}")
                        # Still enable external opening
                        self.open_external_btn.setEnabled(True)
                        
                else:
                    self.update_pdf_info("Error saving PDF to temporary file")
            else:
                self.update_pdf_info(f"No PDF found: {pdf_result['error']}")
                self.pdf_viewer.setText(f"No PDF Plan Found\n\n{pdf_result['error']}")
                
        except Exception as e:
            logger.error(f"Error handling PDF load: {e}")
            self.update_pdf_info(f"Error: {str(e)}")

    def on_pdf_error(self, error_message):
        """Handle PDF loading error"""
        logger.error(f"PDF loading error: {error_message}")
        self.update_pdf_info(f"Error: {error_message}")
        self.pdf_viewer.setText(f"Error Loading PDF\n\n{error_message}")

    def load_pdf_preview(self, pdf_data, filename, temp_path):
        """Load PDF preview in the viewer"""
        try:
            # Load PDF in viewer
            success = self.pdf_viewer.load_pdf_from_data(pdf_data, filename)
            
            if success:
                self.current_pdf_path = temp_path
                self.current_pdf_data = pdf_data
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading PDF preview: {e}")
            return False

    def open_external_pdf(self):
        """Open PDF in external viewer"""
        if not self.current_pdf_path:
            self.update_pdf_info("No PDF loaded to open externally")
            return
            
        try:
            if platform.system() == 'Windows':
                os.startfile(self.current_pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', self.current_pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', self.current_pdf_path])
            
            self.update_pdf_info("PDF opened in external viewer")
            
        except Exception as e:
            logger.error(f"Error opening PDF externally: {e}")
            self.update_pdf_info(f"Error opening externally: {str(e)}")

    def zoom_in(self):
        """Zoom in PDF"""
        if FITZ_AVAILABLE:
            self.pdf_viewer.zoom_in()

    def zoom_out(self):
        """Zoom out PDF"""
        if FITZ_AVAILABLE:
            self.pdf_viewer.zoom_out()

    def reset_zoom(self):
        """Reset PDF zoom"""
        if FITZ_AVAILABLE:
            self.pdf_viewer.reset_zoom()

    def toggle_view_mode(self):
        """Toggle between text and PDF view modes"""
        # Ensure we're in tab widget view
        self.stacked_layout.setCurrentIndex(0)
        
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # Currently on text tab
            # Switch to PDF tab and load PDF
            self.switch_to_pdf_and_load()
        else:  # Currently on PDF tab
            # Switch to text tab
            self.tab_widget.setCurrentIndex(0)
            logger.info("Switched to text view mode")

    def switch_to_pdf_and_load(self):
        """Switch to PDF tab and automatically load PDF if project reference is available"""
        try:
            # Ensure we're in tab widget view and switch to PDF tab
            self.stacked_layout.setCurrentIndex(0)
            self.tab_widget.setCurrentIndex(1)
            logger.info("Switched to PDF view mode")
            
            # Get parent window to access header panel
            parent_window = self.parent()
            while parent_window and not hasattr(parent_window, 'header'):
                parent_window = parent_window.parent()
            
            if not parent_window:
                self.update_pdf_info("Error: Could not find parent window with header panel")
                return
                
            # Get project reference (primary requirement)
            ref_project = parent_window.header.ref_project_edit.text().strip()
            ref_client = parent_window.header.ref_client_edit.text().strip()
            
            # Only project reference is required now
            if not ref_project:
                self.update_pdf_info("Please enter Project Reference to view PDF plans.")
                self.pdf_viewer.setText("PDF Viewer\n\nPlease enter Project Reference\nin the header field above to view PDF plans.")
                return
                
            # Use client reference as the search key (or project reference if client not available)
            search_key = ref_client if ref_client else ref_project  # noqa: F841
            
        except Exception as e:
            logger.error(f"Error in switch_to_pdf_and_load: {e}")
            self.update_pdf_info(f"Error: {str(e)}")

    def switch_to_text(self):
        """Switch to text tab"""
        self.stacked_layout.setCurrentIndex(0)
        self.tab_widget.setCurrentIndex(0)
        logger.info("Switched to text view mode")