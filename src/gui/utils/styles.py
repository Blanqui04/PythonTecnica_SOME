# src/gui/utils/styles.py
"""
Global styles for the Database Management System
Professional, serene, and beautiful theme
"""

def global_style():
    return """
    /* Main Application Styling */
    QMainWindow {
        background-color: #f5f6fa;
        color: #2c3e50;
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    }
    
    /* Central Widget */
    QWidget {
        background-color: #f5f6fa;
        color: #2c3e50;
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    }
    
    /* Scroll Areas */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QScrollBar:vertical {
        background-color: #ecf0f1;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:vertical {
        background-color: #bdc3c7;
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #95a5a6;
    }
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        background: none;
        border: none;
    }
    
    QScrollBar:horizontal {
        background-color: #ecf0f1;
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #bdc3c7;
        border-radius: 6px;
        min-width: 20px;
        margin: 2px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #95a5a6;
    }
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        background: none;
        border: none;
    }
    
    /* Table Styling */
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f8f9fa;
        gridline-color: #ecf0f1;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
    }
    
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #ecf0f1;
    }
    
    QTableWidget::item:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    
    QHeaderView::section {
        background-color: #34495e;
        color: #ffffff;
        padding: 12px 8px;
        border: none;
        border-right: 1px solid #2c3e50;
        font-weight: 600;
        font-size: 11px;
    }
    
    QHeaderView::section:hover {
        background-color: #2c3e50;
    }
    
    /* Tree Widget */
    QTreeWidget {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
        outline: none;
    }
    
    QTreeWidget::item {
        padding: 6px;
        border-bottom: 1px solid #f8f9fa;
    }
    
    QTreeWidget::item:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    
    QTreeWidget::item:hover {
        background-color: #e3f2fd;
    }
    
    /* List Widget */
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        color: #2c3e50;
        outline: none;
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #f8f9fa;
    }
    
    QListWidget::item:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    
    QListWidget::item:hover {
        background-color: #e3f2fd;
    }
    
    /* Menu Bar */
    QMenuBar {
        background-color: #34495e;
        color: #ffffff;
        border: none;
        padding: 4px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 2px;
    }
    
    QMenuBar::item:selected {
        background-color: #3498db;
    }
    
    QMenuBar::item:pressed {
        background-color: #2980b9;
    }
    
    /* Menu */
    QMenu {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 4px;
        color: #2c3e50;
    }
    
    QMenu::item {
        padding: 8px 16px;
        border-radius: 4px;
        margin: 1px;
    }
    
    QMenu::item:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    
    QMenu::separator {
        height: 1px;
        background-color: #ecf0f1;
        margin: 4px 8px;
    }
    
    /* Status Bar */
    QStatusBar {
        background-color: #34495e;
        color: #ffffff;
        border: none;
        padding: 4px;
    }
    
    QStatusBar::item {
        border: none;
    }
    
    /* Tool Tip */
    QToolTip {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #34495e;
        border-radius: 4px;
        padding: 6px;
        font-size: 11px;
    }
    
    /* Progress Bar */
    QProgressBar {
        background-color: #ecf0f1;
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        text-align: center;
        color: #2c3e50;
        font-weight: 600;
    }
    
    QProgressBar::chunk {
        background-color: #3498db;
        border-radius: 3px;
        margin: 1px;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: #bdc3c7;
        margin: 2px;
    }
    
    QSplitter::handle:horizontal {
        width: 4px;
    }
    
    QSplitter::handle:vertical {
        height: 4px;
    }
    
    QSplitter::handle:hover {
        background-color: #95a5a6;
    }
    
    /* Tab Widget */
    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        top: -1px;
    }
    
    QTabBar::tab {
        background-color: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
        border-bottom: none;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #2c3e50;
        border-bottom: 1px solid #ffffff;
    }
    
    QTabBar::tab:hover {
        background-color: #e9ecef;
    }
    
    /* Slider */
    QSlider::groove:horizontal {
        border: 1px solid #bdc3c7;
        height: 6px;
        background: #ecf0f1;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background: #3498db;
        border: 1px solid #2980b9;
        width: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }
    
    QSlider::handle:horizontal:hover {
        background: #2980b9;
    }
    
    /* Spin Box - FIXED: Removed box-shadow and replaced with enhanced border */
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 2px solid #ecf0f1;
        border-radius: 6px;
        padding: 6px 8px;
        color: #2c3e50;
        min-height: 32px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #3498db;
        background-color: #f8feff;
        /* Removed box-shadow - not supported in PyQt5 */
        /* Alternative: Use a thicker border or background gradient to indicate focus */
        border-width: 3px;
    }
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #bdc3c7;
        border-bottom: 1px solid #bdc3c7;
        border-top-right-radius: 6px;
        background-color: #f8f9fa;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        border-left: 1px solid #bdc3c7;
        border-bottom-right-radius: 6px;
        background-color: #f8f9fa;
    }
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
        background-color: #e9ecef;
    }
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