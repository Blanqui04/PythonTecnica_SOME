# src/gui/utils/styles.py
"""
Global styles for the Database Management System
Professional, serene, and beautiful theme
"""

from src.gui.utils.responsive_utils import get_screen_utils

def global_style():
    """Return responsive global stylesheet"""
    screen_utils = get_screen_utils()
    
    # Get responsive values
    spacing = screen_utils.get_adaptive_spacing()
    margins = screen_utils.get_adaptive_margins()
    font_size = screen_utils.scale_font_size(10)
    small_font = screen_utils.scale_font_size(9)
    large_font = screen_utils.scale_font_size(12)
    
    # Scale other values
    scrollbar_width = int(12 * screen_utils.scale_factor)
    scrollbar_height = int(12 * screen_utils.scale_factor)
    scrollbar_handle_min = int(20 * screen_utils.scale_factor)
    scrollbar_margin = int(2 * screen_utils.scale_factor)
    border_radius = int(6 * screen_utils.scale_factor)
    small_border_radius = int(4 * screen_utils.scale_factor)
    padding_small = spacing['small']
    padding_medium = spacing['medium']
    padding_large = spacing['large']
    margin_small = margins['small']
    margin_tiny = margins['tiny']
    
    return f"""
    /* Main Application Styling */
    QMainWindow {{
        background-color: #f5f6fa;
        color: #2c3e50;
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
        font-size: {font_size}px;
    }}
    
    /* Central Widget */
    QWidget {{
        background-color: #f5f6fa;
        color: #2c3e50;
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
        font-size: {font_size}px;
    }}
    
    /* Scroll Areas */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    
    QScrollBar:vertical {{
        background-color: #ecf0f1;
        width: {scrollbar_width}px;
        border-radius: {int(scrollbar_width/2)}px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: #bdc3c7;
        border-radius: {int(scrollbar_width/2)}px;
        min-height: {scrollbar_handle_min}px;
        margin: {scrollbar_margin}px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #95a5a6;
    }}
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        background: none;
        border: none;
    }}
    
    QScrollBar:horizontal {{
        background-color: #ecf0f1;
        height: {scrollbar_height}px;
        border-radius: {int(scrollbar_height/2)}px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: #bdc3c7;
        border-radius: {int(scrollbar_height/2)}px;
        min-width: {scrollbar_handle_min}px;
        margin: {scrollbar_margin}px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: #95a5a6;
    }}
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        background: none;
        border: none;
    }}
    
    /* Table Styling */
    QTableWidget {{
        background-color: #ffffff;
        alternate-background-color: #f8f9fa;
        gridline-color: #ecf0f1;
        border: 1px solid #dee2e6;
        border-radius: {border_radius}px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
        font-size: {font_size}px;
    }}
    
    QTableWidget::item {{
        padding: {padding_small}px;
        border-bottom: 1px solid #ecf0f1;
    }}
    
    QTableWidget::item:selected {{
        background-color: #3498db;
        color: #ffffff;
    }}
    
    QHeaderView::section {{
        background-color: #34495e;
        color: #ffffff;
        padding: {padding_medium}px {padding_small}px;
        border: none;
        border-right: 1px solid #2c3e50;
        font-weight: 600;
        font-size: {small_font}px;
    }}
    
    QHeaderView::section:hover {{
        background-color: #2c3e50;
    }}
    
    /* Tree Widget */
    QTreeWidget {{
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: {border_radius}px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
        outline: none;
        font-size: {font_size}px;
    }}
    
    QTreeWidget::item {{
        padding: {padding_small}px;
        border-bottom: 1px solid #f8f9fa;
    }}
    
    QTreeWidget::item:selected {{
        background-color: #3498db;
        color: #ffffff;
    }}
    
    QTreeWidget::item:hover {{
        background-color: #e3f2fd;
    }}
    
    /* List Widget */
    QListWidget {{
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: {border_radius}px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
        outline: none;
        font-size: {font_size}px;
    }}
    
    QListWidget::item {{
        padding: {padding_small}px;
        border-bottom: 1px solid #f8f9fa;
    }}
    
    QListWidget::item:selected {{
        background-color: #3498db;
        color: #ffffff;
    }}
    
    QListWidget::item:hover {{
        background-color: #e3f2fd;
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: #34495e;
        color: #ffffff;
        border: none;
        padding: {padding_small}px;
        font-size: {font_size}px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: {padding_small}px {padding_medium}px;
        border-radius: {small_border_radius}px;
        margin: {margin_tiny}px;
    }}
    
    QMenuBar::item:selected {{
        background-color: #3498db;
    }}
    
    QMenuBar::item:pressed {{
        background-color: #2980b9;
    }}
    
    /* Menu */
    QMenu {{
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: {border_radius}px;
        padding: {padding_small}px;
        color: #2c3e50;
        font-size: {font_size}px;
    }}
    
    QMenu::item {{
        padding: {padding_small}px {padding_medium}px;
        border-radius: {small_border_radius}px;
        margin: 1px;
    }}
    
    QMenu::item:selected {{
        background-color: #3498db;
        color: #ffffff;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: #ecf0f1;
        margin: {padding_small}px {padding_small}px;
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: #34495e;
        color: #ffffff;
        border: none;
        padding: {padding_small}px;
        font-size: {font_size}px;
    }}
    
    QStatusBar::item {{
        border: none;
    }}
    
    /* Tool Tip */
    QToolTip {{
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #34495e;
        border-radius: {small_border_radius}px;
        padding: {padding_small}px;
        font-size: {small_font}px;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: #ecf0f1;
        border: 1px solid #bdc3c7;
        border-radius: {small_border_radius}px;
        text-align: center;
        color: #2c3e50;
        font-weight: 600;
        font-size: {font_size}px;
    }}
    
    QProgressBar::chunk {{
        background-color: #3498db;
        border-radius: 3px;
        margin: 1px;
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: #bdc3c7;
        margin: {margin_tiny}px;
    }}
    
    QSplitter::handle:horizontal {{
        width: {int(4 * screen_utils.scale_factor)}px;
    }}
    
    QSplitter::handle:vertical {{
        height: {int(4 * screen_utils.scale_factor)}px;
    }}
    
    QSplitter::handle:hover {{
        background-color: #95a5a6;
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: {border_radius}px;
        top: -1px;
    }}
    
    QTabBar::tab {{
        background-color: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
        border-bottom: none;
        padding: {padding_small}px {padding_medium}px;
        margin-right: {margin_tiny}px;
        border-top-left-radius: {border_radius}px;
        border-top-right-radius: {border_radius}px;
        font-size: {font_size}px;
    }}
    
    QTabBar::tab:selected {{
        background-color: #ffffff;
        color: #2c3e50;
        border-bottom: 1px solid #ffffff;
    }}
    
    QTabBar::tab:hover {{
        background-color: #e9ecef;
    }}
    
    /* Slider */
    QSlider::groove:horizontal {{
        border: 1px solid #bdc3c7;
        height: {int(6 * screen_utils.scale_factor)}px;
        background: #ecf0f1;
        border-radius: {int(3 * screen_utils.scale_factor)}px;
    }}
    
    QSlider::handle:horizontal {{
        background: #3498db;
        border: 1px solid #2980b9;
        width: {int(18 * screen_utils.scale_factor)}px;
        margin: {int(-6 * screen_utils.scale_factor)}px 0;
        border-radius: {int(9 * screen_utils.scale_factor)}px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: #2980b9;
    }}
    
    /* Spin Box - FIXED: Removed box-shadow and replaced with enhanced border */
    QSpinBox, QDoubleSpinBox {{
        background-color: #ffffff;
        border: 2px solid #ecf0f1;
        border-radius: {border_radius}px;
        padding: {padding_small}px {padding_small}px;
        color: #2c3e50;
        min-height: {int(32 * screen_utils.scale_factor)}px;
        font-size: {font_size}px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: #3498db;
        background-color: #f8feff;
        /* Removed box-shadow - not supported in PyQt5 */
        /* Alternative: Use a thicker border or background gradient to indicate focus */
        border-width: 3px;
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: {int(20 * screen_utils.scale_factor)}px;
        border-left: 1px solid #bdc3c7;
        border-bottom: 1px solid #bdc3c7;
        border-top-right-radius: {border_radius}px;
        background-color: #f8f9fa;
    }}
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: {int(20 * screen_utils.scale_factor)}px;
        border-left: 1px solid #bdc3c7;
        border-bottom-right-radius: {border_radius}px;
        background-color: #f8f9fa;
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: #e9ecef;
    }}
    """

def get_color_palette():
    """Return the color palette used in the application"""
    return {
        'primary': '#3498db',
        'primary_dark': '#2980b9',
        'secondary': '#34495e',
        'secondary_dark': '#2c3e50',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'info': '#3498db',
        'light': '#ecf0f1',
        'dark': '#2c3e50',
        'white': '#ffffff',
        'gray_100': '#f8f9fa',
        'gray_200': '#e9ecef',
        'gray_300': '#dee2e6',
        'gray_400': '#ced4da',
        'gray_500': '#adb5bd',
        'gray_600': '#6c757d',
        'gray_700': '#495057',
        'gray_800': '#343a40',
        'gray_900': '#212529',
        'background': '#f5f6fa',
        'surface': '#ffffff',
        'border': '#ecf0f1',
        'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'text_muted': '#95a5a6'
    }