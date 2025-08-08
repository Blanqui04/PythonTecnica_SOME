# src/gui/windows/components/helpers/summary_circular_progress.py
from PyQt5.QtWidgets import (QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QPen


class CircularProgressWidget(QWidget):
    """Custom circular progress widget for better visualization"""
    
    def __init__(self, value: float, max_value: float = 100, color: QColor = QColor("#3498db"), 
                 text: str = "", size: int = 80):
        super().__init__()
        self.value = value
        self.max_value = max_value
        self.color = color
        self.text = text
        self.setFixedSize(size, size)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background circle
        pen = QPen(QColor("#ecf0f1"), 8)
        painter.setPen(pen)
        painter.drawEllipse(10, 10, self.width() - 20, self.height() - 20)
        
        # Progress arc
        progress_pen = QPen(self.color, 8)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        
        angle = int((self.value / self.max_value) * 360 * 16)  # 16ths of a degree
        painter.drawArc(10, 10, self.width() - 20, self.height() - 20, 90 * 16, -angle)
        
        # Center text
        painter.setPen(QPen(QColor("#2c3e50"), 2))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)
    
    def update_value(self, value: float, text: str = ""):
        self.value = value
        if text:
            self.text = text
        self.update()