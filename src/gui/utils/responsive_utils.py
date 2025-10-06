#!/usr/bin/env python3
"""
Responsive UI Utilities for PythonTecnica_SOME Application
=========================================================

This module provides utilities to make the application responsive across different screen resolutions.
It includes automatic scaling, adaptive layouts, and responsive sizing calculations.
"""

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QRect
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ScreenUtils:
    """Utility class for screen resolution and scaling management"""
    
    # Reference resolution (development baseline)
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080
    
    # Screen categories based on width
    SCREEN_CATEGORIES = {
        'small': 1366,      # Small laptops
        'medium': 1600,     # Medium laptops/tablets
        'large': 1920,      # Standard desktop
        'xlarge': 2560,     # High-res monitors
        'ultra': 3840       # 4K monitors
    }
    
    def __init__(self):
        self.app = QApplication.instance()
        self.desktop = QDesktopWidget() if self.app else None
        self.current_screen = self._get_current_screen_info()
        self.scale_factor = self._calculate_scale_factor()
        
        logger.info(f"Screen initialized: {self.current_screen['width']}x{self.current_screen['height']}, "
                   f"Scale factor: {self.scale_factor}")
    
    def _get_current_screen_info(self) -> Dict[str, Any]:
        """Get current screen information"""
        if not self.desktop:
            # Fallback values
            return {
                'width': 1366,
                'height': 768,
                'category': 'small',
                'dpi': 96
            }
        
        # Get primary screen geometry
        screen_rect = self.desktop.screenGeometry()
        
        # Get screen category
        category = self._get_screen_category(screen_rect.width())
        
        return {
            'width': screen_rect.width(),
            'height': screen_rect.height(),
            'category': category,
            'dpi': self.desktop.physicalDpiX(),
            'geometry': screen_rect
        }
    
    def _get_screen_category(self, width: int) -> str:
        """Determine screen category based on width"""
        for category, min_width in sorted(self.SCREEN_CATEGORIES.items(), 
                                        key=lambda x: x[1], reverse=True):
            if width >= min_width:
                return category
        return 'small'
    
    def _calculate_scale_factor(self) -> float:
        """Calculate scaling factor based on current vs reference resolution"""
        current_width = self.current_screen['width']
        current_height = self.current_screen['height']
        
        # Calculate scale factors for width and height
        width_scale = current_width / self.REFERENCE_WIDTH
        height_scale = current_height / self.REFERENCE_HEIGHT
        
        # Use the smaller scale factor to ensure everything fits
        scale_factor = min(width_scale, height_scale)
        
        # Clamp scale factor to reasonable bounds
        scale_factor = max(0.7, min(scale_factor, 2.0))
        
        return scale_factor
    
    def scale_size(self, width: int, height: int) -> Tuple[int, int]:
        """Scale width and height according to current screen"""
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)
        return scaled_width, scaled_height
    
    def scale_font_size(self, base_size: int) -> int:
        """Scale font size according to current screen"""
        scaled_size = int(base_size * self.scale_factor)
        return max(8, scaled_size)  # Minimum font size of 8
    
    def get_adaptive_spacing(self) -> Dict[str, int]:
        """Get adaptive spacing values based on screen size"""
        base_spacing = {
            'small': 4,
            'medium': 6,
            'large': 8,
            'content': 10,
            'section': 15,
            'page': 20
        }
        
        category = self.current_screen['category']
        
        # Adjust spacing based on screen category
        multiplier = {
            'small': 0.8,
            'medium': 0.9,
            'large': 1.0,
            'xlarge': 1.1,
            'ultra': 1.2
        }.get(category, 1.0)
        
        return {key: int(value * multiplier) for key, value in base_spacing.items()}
    
    def get_adaptive_margins(self) -> Dict[str, int]:
        """Get adaptive margin values based on screen size"""
        base_margins = {
            'tiny': 2,
            'small': 5,
            'medium': 10,
            'large': 15,
            'xlarge': 20
        }
        
        return {key: int(value * self.scale_factor) for key, value in base_margins.items()}
    
    def get_window_size_for_content(self, content_width: int, content_height: int) -> Tuple[int, int]:
        """Calculate optimal window size for given content"""
        # Add margins and chrome
        margin_values = self.get_adaptive_margins()
        chrome_width = margin_values['medium'] * 4  # Left/right margins + some chrome
        chrome_height = margin_values['large'] * 4  # Top/bottom margins + title bar
        
        total_width = content_width + chrome_width
        total_height = content_height + chrome_height
        
        # Ensure it fits on screen (leave some margin)
        max_width = int(self.current_screen['width'] * 0.95)
        max_height = int(self.current_screen['height'] * 0.90)
        
        final_width = min(total_width, max_width)
        final_height = min(total_height, max_height)
        
        return final_width, final_height
    
    def center_window(self, window_width: int, window_height: int) -> Tuple[int, int]:
        """Calculate position to center window on screen"""
        screen_width = self.current_screen['width']
        screen_height = self.current_screen['height']
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Ensure window is not off-screen
        x = max(0, x)
        y = max(0, y)
        
        return x, y


class ResponsiveWidget:
    """Mixin class to make widgets responsive"""
    
    def __init__(self):
        self.screen_utils = ScreenUtils()
    
    def set_responsive_size(self, base_width: int, base_height: int):
        """Set widget size responsively"""
        scaled_width, scaled_height = self.screen_utils.scale_size(base_width, base_height)
        if hasattr(self, 'resize'):
            self.resize(scaled_width, scaled_height)
        elif hasattr(self, 'setFixedSize'):
            self.setFixedSize(scaled_width, scaled_height)
    
    def set_responsive_minimum_size(self, base_width: int, base_height: int):
        """Set minimum size responsively"""
        scaled_width, scaled_height = self.screen_utils.scale_size(base_width, base_height)
        if hasattr(self, 'setMinimumSize'):
            self.setMinimumSize(scaled_width, scaled_height)
    
    def get_responsive_font_size(self, base_size: int) -> int:
        """Get responsive font size"""
        return self.screen_utils.scale_font_size(base_size)
    
    def get_responsive_spacing(self) -> Dict[str, int]:
        """Get responsive spacing values"""
        return self.screen_utils.get_adaptive_spacing()
    
    def get_responsive_margins(self) -> Dict[str, int]:
        """Get responsive margin values"""
        return self.screen_utils.get_adaptive_margins()


def get_screen_utils() -> ScreenUtils:
    """Get global screen utils instance"""
    if not hasattr(get_screen_utils, '_instance'):
        get_screen_utils._instance = ScreenUtils()
    return get_screen_utils._instance


def make_window_responsive(window, base_width: int = None, base_height: int = None):
    """Make a window responsive with proper sizing and positioning"""
    screen_utils = get_screen_utils()
    
    if base_width and base_height:
        # Calculate responsive size
        window_width, window_height = screen_utils.get_window_size_for_content(base_width, base_height)
        
        # Set minimum size
        min_width = int(base_width * 0.7)
        min_height = int(base_height * 0.7) 
        scaled_min_width, scaled_min_height = screen_utils.scale_size(min_width, min_height)
        
        window.setMinimumSize(scaled_min_width, scaled_min_height)
        
        # Resize window
        window.resize(window_width, window_height)
        
        # Center window
        x, y = screen_utils.center_window(window_width, window_height)
        window.move(x, y)
    else:
        # Just set minimum size and maximize
        window.setMinimumSize(800, 600)
        if hasattr(window, 'showMaximized'):
            window.showMaximized()


def create_responsive_stylesheet(base_font_size: int = 10) -> str:
    """Create a responsive stylesheet with proper font sizes"""
    screen_utils = get_screen_utils()
    
    # Calculate responsive sizes
    font_size = screen_utils.scale_font_size(base_font_size)
    small_font = screen_utils.scale_font_size(base_font_size - 1)
    large_font = screen_utils.scale_font_size(base_font_size + 2)
    
    spacing = screen_utils.get_adaptive_spacing()
    margins = screen_utils.get_adaptive_margins()
    
    stylesheet = f"""
    QWidget {{
        font-size: {font_size}px;
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    
    QMainWindow {{
        background-color: #f5f5f5;
    }}
    
    QPushButton {{
        font-size: {font_size}px;
        padding: {spacing['medium']}px {spacing['large']}px;
        margin: {margins['small']}px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background-color: #ffffff;
        min-height: {int(20 * screen_utils.scale_factor)}px;
    }}
    
    QPushButton:hover {{
        background-color: #e3f2fd;
        border-color: #2196f3;
    }}
    
    QLabel {{
        font-size: {font_size}px;
        margin: {margins['tiny']}px;
    }}
    
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        font-size: {font_size}px;
        padding: {spacing['small']}px;
        border: 1px solid #ddd;
        border-radius: 4px;
        min-height: {int(16 * screen_utils.scale_factor)}px;
    }}
    
    QTableWidget {{
        font-size: {small_font}px;
        gridline-color: #e0e0e0;
        selection-background-color: #e3f2fd;
    }}
    
    QTableWidget::item {{
        padding: {spacing['small']}px;
    }}
    
    QHeaderView::section {{
        font-size: {font_size}px;
        font-weight: bold;
        padding: {spacing['medium']}px;
        background-color: #f0f0f0;
        border: 1px solid #ddd;
    }}
    
    QGroupBox {{
        font-size: {font_size}px;
        font-weight: bold;
        margin: {margins['medium']}px;
        padding-top: {spacing['large']}px;
    }}
    
    QTabWidget::pane {{
        border: 1px solid #ddd;
    }}
    
    QTabBar::tab {{
        font-size: {font_size}px;
        padding: {spacing['medium']}px {spacing['large']}px;
        margin: {margins['tiny']}px;
    }}
    
    QScrollBar:vertical {{
        width: {int(12 * screen_utils.scale_factor)}px;
    }}
    
    QScrollBar:horizontal {{
        height: {int(12 * screen_utils.scale_factor)}px;
    }}
    
    QToolTip {{
        font-size: {small_font}px;
        background-color: #ffffcc;
        border: 1px solid #999;
        padding: {spacing['small']}px;
    }}
    """
    
    return stylesheet


def log_screen_info():
    """Log current screen information for debugging"""
    screen_utils = get_screen_utils()
    logger.info("=== SCREEN INFORMATION ===")
    logger.info(f"Resolution: {screen_utils.current_screen['width']}x{screen_utils.current_screen['height']}")
    logger.info(f"Category: {screen_utils.current_screen['category']}")
    logger.info(f"Scale Factor: {screen_utils.scale_factor}")
    logger.info(f"DPI: {screen_utils.current_screen['dpi']}")
    logger.info(f"Adaptive Spacing: {screen_utils.get_adaptive_spacing()}")
    logger.info(f"Adaptive Margins: {screen_utils.get_adaptive_margins()}")
    logger.info("=========================")


if __name__ == "__main__":
    # Test the responsive utilities
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    log_screen_info()
    app.quit()