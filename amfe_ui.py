import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem, QSizePolicy,
                             QFrame, QGroupBox, QTextEdit, QScrollArea, QMessageBox, QFileDialog,
                             QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, 
                             QProgressBar, QAbstractItemView, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QImage, QPalette, QColor, QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from amfe import AmfeManager  # Our backend module

class AmfeCombinerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMFE Combiner")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create backend instance
        self.amfe_manager = AmfeManager()
        
        # Create UI elements
        self.init_ui()
        
        # Load available processes
        self.load_processes()

    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Process selection
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Preview and actions
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set application style
        self.setStyle()
    
    def setStyle(self):
        # Set a modern style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F0F0;
            }
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3A7BC8;
            }
            QPushButton:pressed {
                background-color: #2A6AB0;
            }
            QPushButton#combineButton {
                background-color: #4A90E2;
                font-weight: bold;
            }
            QPushButton#combineButton:hover {
                background-color: #3A7BC8;
            }
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                text-align: center;
                background-color: #F0F0F0;
            }
            QProgressBar::chunk {
                background-color: #5CB85C;
                width: 10px;
            }
        """)
    
    def create_left_panel(self):
        # Left panel container
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Available Processes")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter processes...")
        self.search_input.textChanged.connect(self.filter_processes)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Process list
        self.process_list = QListWidget()
        self.process_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.process_list.itemSelectionChanged.connect(self.update_selected_list)
        layout.addWidget(self.process_list, 1)  # Stretch factor 1
        
        # Selection buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def create_right_panel(self):
        # Right panel container
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Selected processes group
        selected_group = QGroupBox("Selected Processes")
        selected_layout = QVBoxLayout(selected_group)
        
        # Tree widget for selected processes
        self.selected_tree = QTreeWidget()
        self.selected_tree.setHeaderLabels(["Process", "Status", "Files"])
        self.selected_tree.setColumnWidth(0, 250)
        self.selected_tree.setColumnWidth(1, 100)
        self.selected_tree.setColumnWidth(2, 80)
        
        selected_layout.addWidget(self.selected_tree)
        layout.addWidget(selected_group)
        
        # Output group
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)
        
        # Output file selection
        file_layout = QHBoxLayout()
        file_layout.setSpacing(5)
        
        file_label = QLabel("Output File:")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output file location...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.output_path, 1)  # Stretch factor 1
        file_layout.addWidget(browse_btn)
        
        output_layout.addLayout(file_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        output_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        output_layout.addWidget(self.status_label)
        
        # Combine button
        self.combine_btn = QPushButton("Combine AMFEs")
        self.combine_btn.setObjectName("combineButton")
        self.combine_btn.clicked.connect(self.combine_amfes)
        output_layout.addWidget(self.combine_btn)
        
        layout.addWidget(output_group)
          
        # Graph group
        graph_group = QGroupBox("Graph Generation")
        self.graph_layout = QVBoxLayout(graph_group)

        # Inicialment no hi ha gràfic
        self.canvas = None
        placeholder = QLabel("No graph available. Combine AMFEs to generate one.")
        placeholder.setAlignment(Qt.AlignCenter)
        self.graph_layout.addWidget(placeholder)

        layout.addWidget(graph_group, 1)  # Stretch factor 1
        
        return panel
    
    def load_processes(self):
        """Load available processes into the list"""
        self.process_list.clear()
        for process in self.amfe_manager.available_processes:
            item = QListWidgetItem(process)
            self.process_list.addItem(item)
    
    def filter_processes(self):
        """Filter processes based on search text"""
        search_text = self.search_input.text().lower()
        
        # Show all items if search is empty
        if not search_text:
            for i in range(self.process_list.count()):
                self.process_list.item(i).setHidden(False)
            return
        
        # Filter items
        for i in range(self.process_list.count()):
            item = self.process_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_text not in item_text)
    
    def select_all(self):
        """Select all visible processes"""
        for i in range(self.process_list.count()):
            if not self.process_list.item(i).isHidden():
                self.process_list.item(i).setSelected(True)
    
    def deselect_all(self):
        """Deselect all processes"""
        self.process_list.clearSelection()
    
    def update_selected_list(self):
        """Update the selected processes tree"""
        self.selected_tree.clear()
        
        # Get selected processes
        selected_items = self.process_list.selectedItems()
        selected_processes = [item.text() for item in selected_items]
        
        # Add to treeview with status
        for process in selected_processes:
            # Get AMFE files for this process
            amfe_paths = self.amfe_manager.get_amfe_paths([process])
            files = self.amfe_manager.get_amfe_excels(amfe_paths)
            
            # Check if files are valid
            status = "Valid" if files and self.amfe_manager.is_valid_excel(files[0]) else "Invalid"
            
            # Create tree item
            item = QTreeWidgetItem([process, status, str(len(files))])
            self.selected_tree.addTopLevelItem(item)
    
    def browse_output(self):
        """Open file dialog to choose output path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Combined AMFE File",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.output_path.setText(file_path)
    
    def combine_amfes(self):
        """Combine selected AMFEs into one file"""
        # Get selected processes
        selected_items = self.process_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one process")
            return
        
        # Get output path
        output_file = self.output_path.text()
        if not output_file:
            QMessageBox.warning(self, "Warning", "Please specify an output file")
            return
        
        # Get selected processes
        selected_processes = [item.text() for item in selected_items]
        
        # Get AMFE paths
        amfe_paths = self.amfe_manager.get_amfe_paths(selected_processes)
        
        # Update UI
        self.status_label.setText("Combining AMFEs...")
        self.progress_bar.setValue(0)
        self.combine_btn.setEnabled(False)
        QApplication.processEvents()  # Update UI
        
        # Create worker thread
        self.worker = AmfeWorker(self.amfe_manager, amfe_paths, output_file)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.combine_finished)
        self.worker.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def combine_finished(self, success, message):
        """Handle completion of combine operation"""
        self.combine_btn.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(f"Success! File saved to: {message}")
            QMessageBox.information(self, "Success", "AMFEs combined successfully!")
            self.show_graph()
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Error occurred during combination")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{message}")
        
    
    def show_graph(self):
        """Display risk distribution charts in the UI"""
        # Clear previous widgets
        self.clear_graph_layout()
        
        try:
            # Get risk data
            risk_before = self.amfe_manager.get_risk_summary_data(
                self.output_path.text(), show='before'
            )
            risk_after = self.amfe_manager.get_risk_summary_data(
                self.output_path.text(), show='after'
            )
            
            # Create container for charts
            chart_container = QWidget()
            chart_layout = QHBoxLayout(chart_container)
            chart_layout.setSpacing(20)
            
            # Create before chart
            fig_before = self.amfe_manager.display_risk_pie_chart(
                risk_before, 
                "Initial Risk (Before Actions)"
            )
            canvas_before = FigureCanvas(fig_before)
            canvas_before.setMinimumSize(400, 400)
            chart_layout.addWidget(canvas_before)
            
            # Create after chart
            fig_after = self.amfe_manager.display_risk_pie_chart(
                risk_after, 
                "Residual Risk (After Actions)"
            )
            canvas_after = FigureCanvas(fig_after)
            canvas_after.setMinimumSize(400, 400)
            chart_layout.addWidget(canvas_after)
            
            # Add to main layout
            self.graph_layout.addWidget(chart_container)
            
        except Exception as e:
            error_label = QLabel(f"Could not generate graph: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            self.graph_layout.addWidget(error_label)
            

    def clear_graph_layout(self):
        """Clear all widgets from the graph layout"""
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


class AmfeWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, amfe_manager, amfe_paths, output_file):
        super().__init__()
        self.amfe_manager = amfe_manager
        self.amfe_paths = amfe_paths
        self.output_file = output_file
    
    def run(self):
        try:
            # Combine AMFEs
            self.progress_signal.emit(30)
            result = self.amfe_manager.combine_amfe_data(self.amfe_paths, self.output_file)
            self.progress_signal.emit(80)
            
            if result:
                self.finished_signal.emit(True, self.output_file)
            else:
                self.finished_signal.emit(False, "Failed to create combined file")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            self.progress_signal.emit(100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AmfeCombinerApp()
    window.show()
    sys.exit(app.exec_())