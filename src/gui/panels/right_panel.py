from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from ..widgets.buttons import ModernButton
from PyQt5.QtCore import pyqtSignal

class RightPanel(QGroupBox):
    action_requested = pyqtSignal(str)  # Signal with action name
    
    def __init__(self, parent=None):
        super().__init__("Edit Actions", parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Edit section
        edit_group = QGroupBox("Edit")
        edit_layout = QVBoxLayout()
        
        self.edit_dim_btn = ModernButton("✏️ Edit Dimensional")
        self.edit_study_btn = ModernButton("✏️ Edit Study")
        
        self.edit_dim_btn.clicked.connect(lambda: self.emit_action("edit_dimensional"))
        self.edit_study_btn.clicked.connect(lambda: self.emit_action("edit_study"))
        
        edit_layout.addWidget(self.edit_dim_btn)
        edit_layout.addWidget(self.edit_study_btn)
        edit_group.setLayout(edit_layout)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        self.open_plan_btn = ModernButton("📂 Open Plan")
        self.open_folder_btn = ModernButton("📁 Open Folder")
        
        self.open_plan_btn.clicked.connect(lambda: self.emit_action("open_plan"))
        self.open_folder_btn.clicked.connect(lambda: self.emit_action("open_folder"))
        
        file_layout.addWidget(self.open_plan_btn)
        file_layout.addWidget(self.open_folder_btn)
        file_group.setLayout(file_layout)
        
        # Additional actions
        additional_group = QGroupBox("Additional")
        additional_layout = QVBoxLayout()
        
        self.export_btn = ModernButton("📤 Export Data")
        self.import_btn = ModernButton("📥 Import Data")
        
        self.export_btn.clicked.connect(lambda: self.emit_action("export_data"))
        self.import_btn.clicked.connect(lambda: self.emit_action("import_data"))
        
        additional_layout.addWidget(self.export_btn)
        additional_layout.addWidget(self.import_btn)
        additional_group.setLayout(additional_layout)
        
        layout.addWidget(edit_group)
        layout.addWidget(file_group)
        layout.addWidget(additional_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def emit_action(self, action_name):
        self.action_requested.emit(action_name)