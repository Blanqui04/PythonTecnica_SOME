from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from ..widgets.buttons import ModernButton

class LeftPanel(QGroupBox):
    action_requested = pyqtSignal(str)  # Signal with action name
    
    def __init__(self, parent=None):
        super().__init__("Main Actions", parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Analysis section
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout()
        
        self.dimensional_btn = ModernButton("📊 Dimensional Study")
        self.capacity_btn = ModernButton("📈 Capacity Study")
        
        self.dimensional_btn.clicked.connect(lambda: self.emit_action("dimensional"))
        self.capacity_btn.clicked.connect(lambda: self.emit_action("capacity"))
        
        analysis_layout.addWidget(self.dimensional_btn)
        analysis_layout.addWidget(self.capacity_btn)
        analysis_group.setLayout(analysis_layout)
        
        # View section
        view_group = QGroupBox("View")
        view_layout = QVBoxLayout()
        
        self.plan_btn = ModernButton("🗺️ View Plan")
        self.matrix_btn = ModernButton("🔢 View Matrix")
        
        self.plan_btn.clicked.connect(lambda: self.emit_action("view_plan"))
        self.matrix_btn.clicked.connect(lambda: self.emit_action("view_matrix"))
        
        view_layout.addWidget(self.plan_btn)
        view_layout.addWidget(self.matrix_btn)
        view_group.setLayout(view_layout)
        
        # Data processing
        data_group = QGroupBox("Data Processing")
        data_layout = QVBoxLayout()
        
        self.kop_btn = ModernButton("📋 Read KOP")
        self.csv_btn = ModernButton("📄 Process CSV")
        self.update_btn = ModernButton("🔄 Update Database")
        
        self.kop_btn.clicked.connect(lambda: self.emit_action("read_kop"))
        self.csv_btn.clicked.connect(lambda: self.emit_action("process_csv"))
        self.update_btn.clicked.connect(lambda: self.emit_action("update_db"))
        
        data_layout.addWidget(self.kop_btn)
        data_layout.addWidget(self.csv_btn)
        data_layout.addWidget(self.update_btn)
        data_group.setLayout(data_layout)
        
        layout.addWidget(analysis_group)
        layout.addWidget(view_group)
        layout.addWidget(data_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def emit_action(self, action_name):
        self.action_requested.emit(action_name)