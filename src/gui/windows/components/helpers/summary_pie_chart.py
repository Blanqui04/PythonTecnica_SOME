# src/gui/windows/components/dimensional_summary_widget.py - ENHANCED SOPHISTICATED VERSION
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QPen


class StatusPieChart(QWidget):
    """Custom pie chart for status visualization"""
    
    def __init__(self, data: dict, size: int = 120):
        super().__init__()
        self.data = data
        self.colors = {
            "GOOD": QColor("#27ae60"),
            "BAD": QColor("#e74c3c"),
            "WARNING": QColor("#f39c12"),
            "TED": QColor("#3498db"),
            "TO_CHECK": QColor("#f39c12")
        }
        self.setFixedSize(size, size)
    
    def paintEvent(self, event):
        if not self.data or sum(self.data.values()) == 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        total = sum(self.data.values())
        current_angle = 0
        
        for status, count in self.data.items():
            if count > 0:
                angle = int((count / total) * 360 * 16)
                color = self.colors.get(status, QColor("#95a5a6"))
                
                painter.setBrush(color)
                painter.setPen(QPen(QColor("white"), 2))
                painter.drawPie(5, 5, self.width() - 10, self.height() - 10, 
                              current_angle, angle)
                current_angle += angle
    
    def update_data(self, data: dict):
        self.data = data
        self.update()
