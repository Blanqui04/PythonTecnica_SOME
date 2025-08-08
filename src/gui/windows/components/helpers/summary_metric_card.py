# src/gui/windows/components/dimensional_summary_widget.py - ENHANCED SOPHISTICATED VERSION
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class CompactMetricCard(QFrame):
    """Compact metric card with better space utilization"""
    
    def __init__(self, title: str, value: str, icon: str = "📊", color: str = "#3498db"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(60)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {color}15, stop:1 {color}08);
                border: 2px solid {color};
                border-radius: 6px;
                margin: 1px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {color}25, stop:1 {color}10);
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # Title
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {color}; border: none;")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {color}; border: none;")
        self.value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def update_value(self, value: str):
        self.value_label.setText(str(value))