# src/gui/windows/spc_chart_window.py
import os
import subprocess
import platform
import math
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QMessageBox,
    QFrame,
    QSplitter,
    QCheckBox,
    QGroupBox,
    QProgressBar,
    QSpacerItem,
    QSizePolicy,
    QButtonGroup,
    QRadioButton,
    QSlider,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from src.services.spc_chart_service import SPCChartService
from src.gui.windows.components.spc_export_dialog import ExcelExportDialog
from ..logging_config import logger
from ..utils.chart_utils import ChartPathResolver # ,ChartDisplayHelper
from ..utils.styles import global_style, get_color_palette
from ..utils.responsive_utils import ResponsiveWidget
from ..widgets.buttons import ModernButton, ActionButton, CompactButton
from ..widgets.inputs import ModernComboBox, ModernTextEdit


class ChartGenerationWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, client: str, ref_project: str, batch_number: str):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.service = None

    def run(self):
        try:
            study_id = f"{self.ref_project}_{self.batch_number}"
            logger.info(f"Starting chart generation for study: {study_id}")

            self.progress.emit(10)

            # Pass all required params, not study_id string alone
            self.service = SPCChartService(
                self.client, self.ref_project, self.batch_number
            )

            if not self.service.initialize_chart_manager():
                self.error.emit(
                    f"Failed to initialize chart manager for study: {study_id}"
                )
                return

            self.progress.emit(25)

            valid, message = self.service.validate_study_data()
            if not valid:
                self.error.emit(f"Study data validation failed: {message}")
                return

            self.progress.emit(40)

            chart_results = self.service.generate_all_charts(show=False, save=True)

            self.progress.emit(80)

            results = {
                "chart_results": chart_results,
                "elements_summary": self.service.get_elements_summary(),
                "study_statistics": self.service.get_study_statistics(),
                "service": self.service,
            }

            self.progress.emit(100)

            logger.info(
                f"Chart generation completed successfully for {len(chart_results)} elements"
            )
            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Error in chart generation: {str(e)}")
            self.error.emit(f"Error generating charts: {str(e)}")


class ChartDisplayWidget(QWidget):
    """Custom widget for displaying charts with proper scaling and layout"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts = []
        self.layout_mode = "auto"  # auto, grid, vertical
        self.max_charts_per_row = 2
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main container that will hold both the controls and charts
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # Create floating control bar (positioned over the chart area)
        control_bar = self.create_floating_control_bar()
        self.container_layout.addWidget(control_bar)

        # Chart container
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_layout.setContentsMargins(
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor)
        )
        self.chart_layout.setSpacing(int(20 * self.screen_utils.scale_factor))
        self.chart_container.setLayout(self.chart_layout)
        self.container_layout.addWidget(self.chart_container)

        self.container.setLayout(self.container_layout)
        self.main_layout.addWidget(self.container)
        self.setLayout(self.main_layout)

    def create_floating_control_bar(self):
        """Create a floating control bar that overlays the chart area"""
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(248, 249, 250, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 10px;
            }
            QLabel {
                color: #495057;
                font-weight: 500;
            }
            QRadioButton {
                color: #495057;
                font-size: 9pt;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
            }
            QSpinBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 9pt;
                min-height: 16px;
            }
            QSlider::groove:horizontal {
                background-color: #dee2e6;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #007bff;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
        """)
        control_frame.setFixedHeight(int(50 * self.screen_utils.scale_factor))
        control_frame.setContentsMargins(5, 5, 5, 5)

        layout = QHBoxLayout()
        layout.setSpacing(int(12 * self.screen_utils.scale_factor))
        layout.setContentsMargins(
            int(10 * self.screen_utils.scale_factor),
            int(8 * self.screen_utils.scale_factor),
            int(10 * self.screen_utils.scale_factor),
            int(8 * self.screen_utils.scale_factor)
        )

        # Layout mode selector
        layout_label = QLabel("Layout:")
        layout_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        layout.addWidget(layout_label)

        self.layout_group = QButtonGroup()

        auto_radio = QRadioButton("Auto")
        auto_radio.setChecked(True)
        auto_radio.toggled.connect(lambda: self.set_layout_mode("auto"))
        auto_radio.setFont(QFont("Segoe UI", 9))
        self.layout_group.addButton(auto_radio)
        layout.addWidget(auto_radio)

        grid_radio = QRadioButton("Grid")
        grid_radio.toggled.connect(lambda: self.set_layout_mode("grid"))
        grid_radio.setFont(QFont("Segoe UI", 9))
        self.layout_group.addButton(grid_radio)
        layout.addWidget(grid_radio)

        vertical_radio = QRadioButton("Vertical")
        vertical_radio.toggled.connect(lambda: self.set_layout_mode("vertical"))
        vertical_radio.setFont(QFont("Segoe UI", 9))
        self.layout_group.addButton(vertical_radio)
        layout.addWidget(vertical_radio)

        # Spacing
        layout.addItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # Charts per row (for grid mode)
        per_row_label = QLabel("Per Row:")
        per_row_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        layout.addWidget(per_row_label)

        self.per_row_spin = QSpinBox()
        self.per_row_spin.setRange(1, 4)
        self.per_row_spin.setValue(2)
        self.per_row_spin.valueChanged.connect(self.set_charts_per_row)
        self.per_row_spin.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.per_row_spin)

        layout.addStretch()

        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        layout.addWidget(zoom_label)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(int(100 * self.screen_utils.scale_factor))
        self.zoom_slider.valueChanged.connect(self.set_zoom_level)
        layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFont(QFont("Segoe UI", 9))
        self.zoom_label.setMinimumWidth(int(35 * self.screen_utils.scale_factor))
        layout.addWidget(self.zoom_label)

        control_frame.setLayout(layout)
        return control_frame

    def set_layout_mode(self, mode):
        self.layout_mode = mode
        self.update_chart_layout()

    def set_charts_per_row(self, value):
        self.max_charts_per_row = value
        self.update_chart_layout()

    def set_zoom_level(self, value):
        self.zoom_label.setText(f"{value}%")
        self.update_chart_layout()

    def add_chart(self, chart_path, chart_type, element_id=None, cavity=None):
        """Add a chart to the display - Updated to include element_id and cavity"""
        if os.path.exists(chart_path):
            chart_info = {
                "path": chart_path,
                "type": chart_type,
                "element_id": element_id,
                "cavity": cavity,
                "pixmap": QPixmap(chart_path),
            }
            self.charts.append(chart_info)
            self.update_chart_layout()

    def clear_charts(self):
        """Clear all charts"""
        self.charts.clear()
        self.clear_layout()

    def clear_layout(self):
        """Clear the chart layout"""
        while self.chart_layout.count():
            child = self.chart_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_chart_layout(self):
        """Update the chart layout based on current settings"""
        self.clear_layout()

        if not self.charts:
            empty_label = QLabel("No charts to display")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 16px;
                    font-style: italic;
                    padding: 50px;
                }
            """)
            self.chart_layout.addWidget(empty_label)
            return

        zoom_factor = self.zoom_slider.value() / 100.0

        if self.layout_mode == "vertical":
            self.create_vertical_layout(zoom_factor)
        elif self.layout_mode == "grid":
            self.create_grid_layout(zoom_factor)
        else:  # auto
            self.create_auto_layout(zoom_factor)

    def create_vertical_layout(self, zoom_factor):
        """Create vertical layout"""
        for chart_info in self.charts:
            chart_widget = self.create_chart_widget(chart_info, zoom_factor)
            self.chart_layout.addWidget(chart_widget)

    def create_grid_layout(self, zoom_factor):
        """Create grid layout"""
        charts_per_row = self.max_charts_per_row
        rows = math.ceil(len(self.charts) / charts_per_row)

        for row in range(rows):
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setSpacing(int(15 * self.screen_utils.scale_factor))

            for col in range(charts_per_row):
                chart_idx = row * charts_per_row + col
                if chart_idx < len(self.charts):
                    chart_info = self.charts[chart_idx]
                    chart_widget = self.create_chart_widget(
                        chart_info, zoom_factor, True
                    )
                    row_layout.addWidget(chart_widget)
                else:
                    row_layout.addStretch()

            row_widget.setLayout(row_layout)
            self.chart_layout.addWidget(row_widget)

    def create_auto_layout(self, zoom_factor):
        """Create automatic layout based on number of charts"""
        if len(self.charts) == 1:
            self.create_vertical_layout(zoom_factor)
        elif len(self.charts) <= 4:
            self.create_grid_layout(zoom_factor)
        else:
            self.create_vertical_layout(zoom_factor)

    def create_chart_widget(self, chart_info, zoom_factor, is_grid=False):
        """Create a widget for displaying a single chart - Updated to show element and cavity info"""
        chart_widget = QFrame()
        chart_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: {self.screen_utils.scale_size(1)}px solid #dee2e6;
                border-radius: {self.screen_utils.scale_size(6)}px;
                padding: {self.screen_utils.scale_size(10)}px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(int(12 * self.screen_utils.scale_factor))

        # Chart title - enhanced with element and cavity info
        title_text = chart_info["type"].replace("_", " ").title()
        if chart_info.get("element_id") and chart_info.get("cavity"):
            title_text = f"{chart_info['element_id']} - Cavity {chart_info['cavity']} - {title_text}"
        elif chart_info.get("element_id"):
            title_text = f"{chart_info['element_id']} - {title_text}"
            
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        title_label.setStyleSheet("""
            QLabel {
                color: #343a40;
                background-color: transparent;
                margin-bottom: {self.screen_utils.scale_size(8)}px;
                padding: 0;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Chart image - better proportions
        chart_label = QLabel()
        pixmap = chart_info["pixmap"]

        if not pixmap.isNull():
            # Better size calculations for more balanced display
            if is_grid:
                target_width = int(520 * zoom_factor * self.screen_utils.scale_factor)
                target_height = int(380 * zoom_factor * self.screen_utils.scale_factor)
            else:
                target_width = int(950 * zoom_factor * self.screen_utils.scale_factor)
                target_height = int(700 * zoom_factor * self.screen_utils.scale_factor)

            scaled_pixmap = pixmap.scaled(
                target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            chart_label.setPixmap(scaled_pixmap)

        chart_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart_label)

        chart_widget.setLayout(layout)
        return chart_widget


class ModernSPCChartWindow(QDialog, ResponsiveWidget):
    def __init__(self, client: str, ref_project: str, batch_number: str, parent=None):
        super().__init__(parent)
        ResponsiveWidget.__init__(self)
        self.client = client
        self.ref_project = ref_project
        self.batch_number = batch_number
        self.study_id = f"{client}_{ref_project}"
        self.chart_service = None
        self.elements_data = {}
        self.current_element = None
        self.current_element_cavity_key = None  # New: track element+cavity combination
        self.colors = get_color_palette()

        self.setup_ui()
        self.apply_styles()
        self.start_chart_generation()

    def setup_ui(self):
        self.setWindowTitle(f"SPC Charts - {self.client} - {self.ref_project} - Batch: {self.batch_number}")

        # Enable window controls (minimize, maximize, close)
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )

        # Set initial size and show maximized
        self.resize(
            int(1400 * self.screen_utils.scale_factor),
            int(900 * self.screen_utils.scale_factor)
        )
        self.showMaximized()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_widget = self.create_header_section()
        main_layout.addWidget(header_widget)

        # Content area
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(self.create_control_panel())
        content_splitter.addWidget(self.create_chart_display_area())

        # Better splitter proportions
        content_splitter.setSizes([
            int(350 * self.screen_utils.scale_factor),
            int(1050 * self.screen_utils.scale_factor)
        ])
        main_layout.addWidget(content_splitter)

        # Footer
        footer_widget = self.create_footer_section()
        main_layout.addWidget(footer_widget)

        self.setLayout(main_layout)

    def create_header_section(self):
        """Create an improved header with proper spacing and logo"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border: none;
            }
        """)
        header_frame.setFixedHeight(int(140 * self.screen_utils.scale_factor))

        # Main layout with proper margins
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(
            int(30 * self.screen_utils.scale_factor),
            int(25 * self.screen_utils.scale_factor),
            int(30 * self.screen_utils.scale_factor),
            int(25 * self.screen_utils.scale_factor)
        )
        main_layout.setSpacing(int(20 * self.screen_utils.scale_factor))

        # Left side - Text content
        text_widget = QWidget()
        text_widget.setStyleSheet("QWidget { background: transparent; }")  # Ensure transparent background
        text_layout = QVBoxLayout()
        text_layout.setSpacing(12)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Title with improved typography - NO background color to avoid covering text
        title_label = QLabel("Anàlisi de Capacitat SPC")
        title_label.setFont(QFont("Segoe UI", int(20 * self.screen_utils.scale_factor), QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                padding: 5px 0px 10px 0px;
                margin: 0;
                letter-spacing: 0.5px;
            }
        """)
        title_label.setMinimumHeight(35)  # Ensure enough height for the text
        text_layout.addWidget(title_label)

        # Subtitle with better spacing - NO background color - Updated to include batch
        subtitle_label = QLabel(f"Client: {self.client} | Projecte: {self.ref_project} | Batch: {self.batch_number}")
        subtitle_label.setFont(QFont("Segoe UI", int(12 * self.screen_utils.scale_factor), QFont.Normal))
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                background: transparent;
                padding: 0;
                margin: 0;
            }
        """)
        text_layout.addWidget(subtitle_label)

        # Status and progress section
        status_widget = QWidget()
        status_widget.setStyleSheet("QWidget { background: transparent; }")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 8, 0, 0)
        status_layout.setSpacing(15)

        self.status_label = QLabel("⏳ Inicialitzant generació de gràfics...")
        self.status_label.setFont(QFont("Segoe UI", int(11 * self.screen_utils.scale_factor), QFont.Medium))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                background: transparent;
                padding: 0;
                margin: 0;
            }
        """)
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(
            int(220 * self.screen_utils.scale_factor),
            int(8 * self.screen_utils.scale_factor)
        )
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(189, 195, 199, 0.3);
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(self.progress_bar)

        status_layout.addStretch()
        status_widget.setLayout(status_layout)
        text_layout.addWidget(status_widget)

        text_widget.setLayout(text_layout)
        main_layout.addWidget(text_widget)

        # Right side - Logo
        logo_widget = self.create_logo_widget()
        main_layout.addWidget(logo_widget)

        header_frame.setLayout(main_layout)
        return header_frame

    def create_logo_widget(self):
        """Create the logo widget for the header"""
        logo_widget = QWidget()
        logo_widget.setFixedSize(
            int(120 * self.screen_utils.scale_factor),
            int(90 * self.screen_utils.scale_factor)
        )
        logo_widget.setStyleSheet("QWidget { background: transparent; }")  # Transparent background
        
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("QLabel { background: transparent; }")  # Transparent background
        
        # Try to load the logo
        logo_path = "./assets/images/gui/logo_some.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Scale the logo to fit properly within the widget size
                scaled_pixmap = pixmap.scaled(
                    300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                logo_label.setPixmap(scaled_pixmap)
            else:
                # Fallback if image can't be loaded - cleaner fallback design
                logo_label.setText("LOGO")
                logo_label.setStyleSheet("""
                    QLabel {
                        color: #ecf0f1;
                        background: transparent;
                        border: 2px solid rgba(236, 240, 241, 0.3);
                        border-radius: 8px;
                        padding: 15px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
        else:
            # Fallback if file doesn't exist - cleaner fallback design
            logo_label.setText("LOGO")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #ecf0f1;
                    background: transparent;
                    border: 2px solid rgba(236, 240, 241, 0.3);
                    border-radius: 8px;
                    padding: 15px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

        logo_layout.addWidget(logo_label)
        logo_widget.setLayout(logo_layout)
        return logo_widget

    def create_control_panel(self):
        control_widget = QWidget()
        control_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        control_widget.setMinimumWidth(int(320 * self.screen_utils.scale_factor))
        control_widget.setMaximumWidth(int(400 * self.screen_utils.scale_factor))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor),
            int(20 * self.screen_utils.scale_factor)
        )
        main_layout.setSpacing(int(20 * self.screen_utils.scale_factor))

        # Element selection group
        element_group = self.create_element_group()
        main_layout.addWidget(element_group)

        # Chart type selection group
        chart_group = self.create_chart_type_group()
        main_layout.addWidget(chart_group)

        # Statistics group
        stats_group = self.create_statistics_group()
        main_layout.addWidget(stats_group)

        main_layout.addStretch()
        control_widget.setLayout(main_layout)

        return control_widget

    def create_element_group(self):
        group = QGroupBox("🔍 Selecció d'Element")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Element selector - Updated to show element+cavity combinations
        self.element_combo = ModernComboBox()
        self.element_combo.setEnabled(False)
        self.element_combo.setMinimumHeight(int(32 * self.screen_utils.scale_factor))
        self.element_combo.currentTextChanged.connect(self.on_element_changed)
        layout.addWidget(self.element_combo)

        # Element information
        self.element_info = ModernTextEdit()
        self.element_info.setMaximumHeight(int(100 * self.screen_utils.scale_factor))
        self.element_info.setMinimumHeight(int(80 * self.screen_utils.scale_factor))
        self.element_info.setReadOnly(True)
        self.element_info.setPlainText("Carregant informació dels elements...")
        self.element_info.setWordWrapMode(True)
        layout.addWidget(self.element_info)

        group.setLayout(layout)
        return group

    def create_chart_type_group(self):
        group = QGroupBox("📈 Tipus de Gràfics")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
            QCheckBox {
                color: #495057;
                font-size: 10pt;
                spacing: 5px;
                background-color: transparent;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Select all/none buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = CompactButton("Tots")
        self.select_all_btn.clicked.connect(self.select_all_charts)
        self.select_all_btn.setEnabled(False)
        self.select_all_btn.setMinimumHeight(int(28 * self.screen_utils.scale_factor))
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        button_layout.addWidget(self.select_all_btn)

        self.select_none_btn = CompactButton("Cap")
        self.select_none_btn.clicked.connect(self.select_no_charts)
        self.select_none_btn.setEnabled(False)
        self.select_none_btn.setMinimumHeight(int(28 * self.screen_utils.scale_factor))
        self.select_none_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        button_layout.addWidget(self.select_none_btn)

        layout.addLayout(button_layout)

        # Chart type checkboxes
        self.chart_type_checkboxes = {}
        chart_types = [
            ("capability", "Capacitat"),
            ("normality", "Normalitat"),
            ("extrapolation", "Extrapolació"),
            ("individuals", "Individuals"),
            ("moving_range", "Rang Mòbil"),
        ]

        for chart_type, display_name in chart_types:
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setMinimumHeight(int(22 * self.screen_utils.scale_factor))
            checkbox.setEnabled(False)
            checkbox.stateChanged.connect(self.on_chart_selection_changed)
            layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type] = checkbox

        group.setLayout(layout)
        return group

    def create_statistics_group(self):
        group = QGroupBox("📊 Estadístiques")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        group.setStyleSheet("""
            QGroupBox {
                color: #495057;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: transparent;
            }
        """)

        layout = QVBoxLayout()

        self.stats_info = ModernTextEdit()
        self.stats_info.setMaximumHeight(int(100 * self.screen_utils.scale_factor))
        self.stats_info.setMinimumHeight(int(80 * self.screen_utils.scale_factor))
        self.stats_info.setReadOnly(True)
        self.stats_info.setPlainText("Estadístiques no disponibles...")
        self.stats_info.setWordWrapMode(True)
        layout.addWidget(self.stats_info)

        group.setLayout(layout)
        return group

    def create_chart_display_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
        """)

        self.chart_display = ChartDisplayWidget()
        scroll_area.setWidget(self.chart_display)

        return scroll_area

    def create_footer_section(self):
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: {int(15 * self.screen_utils.scale_factor)}px {int(20 * self.screen_utils.scale_factor)}px;
            }
        """)
        footer_frame.setFixedHeight(int(70 * self.screen_utils.scale_factor))

        layout = QHBoxLayout()

        # Action buttons with better styling
        self.open_folder_btn = ActionButton("📁 Obrir Carpeta")
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.setMinimumHeight(int(36 * self.screen_utils.scale_factor))
        self.open_folder_btn.setFont(QFont("Segoe UI", 10))
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        layout.addWidget(self.open_folder_btn)

        self.export_btn = ActionButton("📤 Exportar Gràfics")
        self.export_btn.clicked.connect(self.export_charts)
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(int(36 * self.screen_utils.scale_factor))
        self.export_btn.setFont(QFont("Segoe UI", 10))
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        layout.addWidget(self.export_btn)

        layout.addStretch()

        # Close button
        close_btn = ModernButton("Tancar", primary=True)
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumHeight(int(36 * self.screen_utils.scale_factor))
        close_btn.setFont(QFont("Segoe UI", 10))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        layout.addWidget(close_btn)

        footer_frame.setLayout(layout)
        return footer_frame

    def apply_styles(self):
        """Apply the global styles to the window"""
        self.setStyleSheet(global_style())

    def start_chart_generation(self):
        self.chart_worker = ChartGenerationWorker(
            self.client, self.ref_project, self.batch_number
        )
        self.chart_worker.finished.connect(self.on_charts_generated)
        self.chart_worker.error.connect(self.on_chart_generation_error)
        self.chart_worker.progress.connect(self.on_progress_update)
        self.chart_worker.start()

    def on_progress_update(self, progress):
        self.progress_bar.setValue(progress)
        if progress < 100:
            self.status_label.setText(f"⏳ Generant gràfics... {progress}%")

    def on_charts_generated(self, results):
        logger.info("Charts generated successfully, updating UI")

        self.chart_service = results["service"]
        self.elements_data = results["elements_summary"]

        # Update status
        self.status_label.setText("✅ Gràfics generats correctament!")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        self.progress_bar.setValue(100)

        # Enable controls and populate element selector with element+cavity combinations
        self.element_combo.clear()
        element_cavity_keys = []
        
        for element_key, element_data in self.elements_data.items():
            # Create display format: "ElementID - Cavity X" or just "ElementID" if no cavity info
            if 'cavity' in element_data and element_data['cavity']:
                display_name = f"{element_key} - Cavity {element_data['cavity']}"
                element_cavity_key = f"{element_key}_{element_data['cavity']}"
            else:
                display_name = element_key
                element_cavity_key = element_key
            
            self.element_combo.addItem(display_name, element_cavity_key)
            element_cavity_keys.append(element_cavity_key)
        
        self.element_combo.setEnabled(True)

        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setEnabled(True)
            checkbox.setChecked(True)  # Check all by default

        self.select_all_btn.setEnabled(True)
        self.select_none_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Update statistics
        stats = results.get("study_statistics", {})
        stats_text = self.format_statistics(stats)
        self.stats_info.setPlainText(stats_text)

        # Load first element
        if element_cavity_keys:
            self.current_element_cavity_key = element_cavity_keys[0]
            # Find the original element key for the first entry
            first_element_key = list(self.elements_data.keys())[0]
            self.current_element = first_element_key
            self.load_element_charts(first_element_key)

    def on_chart_generation_error(self, error_msg):
        logger.error(f"Chart generation failed: {error_msg}")
        self.status_label.setText("❌ Error generant gràfics")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.progress_bar.setValue(0)

        QMessageBox.critical(
            self,
            "Error de Generació",
            f"No s'han pogut generar els gràfics:\n\n{error_msg}",
        )

    def on_element_changed(self, display_name):
        """Handle element selection change - Updated for element+cavity combinations"""
        if not display_name:
            return
            
        # Get the element_cavity_key from the combo box data
        current_index = self.element_combo.currentIndex()
        if current_index >= 0:
            element_cavity_key = self.element_combo.itemData(current_index)
            if element_cavity_key and element_cavity_key != self.current_element_cavity_key:
                self.current_element_cavity_key = element_cavity_key
                
                # Extract the original element key to find in elements_data
                # For keys like "Element1_CavityA", we need to find the matching element
                matching_element_key = None
                for element_key, element_data in self.elements_data.items():
                    if 'cavity' in element_data and element_data['cavity']:
                        if f"{element_key}_{element_data['cavity']}" == element_cavity_key:
                            matching_element_key = element_key
                            break
                    else:
                        if element_key == element_cavity_key:
                            matching_element_key = element_key
                            break
                
                if matching_element_key:
                    self.current_element = matching_element_key
                    self.load_element_charts(matching_element_key)

    def on_chart_selection_changed(self):
        if self.current_element:
            self.load_element_charts(self.current_element)

    def select_all_charts(self):
        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setChecked(True)

    def select_no_charts(self):
        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setChecked(False)

    def load_element_charts(self, element_name):
        """Load charts for the selected element - UPDATED to handle cavity properly"""
        if not self.chart_service or element_name not in self.elements_data:
            return

        logger.info(f"Loading charts for element: {element_name}")

        # Update element info - Enhanced to show cavity information
        element_data = self.elements_data[element_name]
        element_data["element_name"] = element_name
        
        # Get cavity info
        cavity_info = element_data.get('cavity', '')
        
        # Enhanced info formatting to include cavity
        info_parts = [f"Element: {element_name}"]
        if cavity_info:
            info_parts.append(f"Cavity: {cavity_info}")
        if 'nominal' in element_data:
            info_parts.append(f"Nominal: {element_data['nominal']:.3f}")
        if 'tolerance' in element_data and isinstance(element_data['tolerance'], list):
            tol_minus, tol_plus = element_data['tolerance']
            info_parts.append(f"Tolerance: {tol_minus:.3f} / +{tol_plus:.3f}")
        
        info_text = "\n".join(info_parts)
        self.element_info.setPlainText(info_text)

        # Clear and load charts
        self.chart_display.clear_charts()

        for chart_type, checkbox in self.chart_type_checkboxes.items():
            if checkbox.isChecked():
                # UPDATED: Pass cavity parameter to get_chart_file_path
                chart_path = self.chart_service.get_chart_file_path(
                    element_name, chart_type, cavity_info
                )
                
                if os.path.exists(chart_path):
                    self.chart_display.add_chart(
                        chart_path, 
                        chart_type, 
                        element_id=element_name,
                        cavity=cavity_info
                    )
                else:
                    logger.warning(f"Chart not found: {chart_path}")

    def format_statistics(self, stats):
        if not stats:
            return "No hi ha estadístiques disponibles"

        formatted = []
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                formatted.append(f"{key}: {value:.2f}")
            else:
                formatted.append(f"{key}: {value}")

        return "\n".join(formatted)

    def open_results_folder(self):
        """UPDATED: Open the new charts directory structure"""
        folder_path = ChartPathResolver.get_charts_directory(self.ref_project)
        if os.path.exists(folder_path):
            try:
                if platform.system() == "Windows":
                    os.startfile(folder_path)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", folder_path])
                else:
                    subprocess.run(["xdg-open", folder_path])
                logger.info(f"Opened folder: {folder_path}")
            except Exception as e:
                logger.error(f"Failed to open folder: {e}")
                QMessageBox.warning(
                    self, "Error", f"No s'ha pogut obrir la carpeta:\n{e}"
                )
        else:
            QMessageBox.warning(self, "Error", "La carpeta de resultats no existeix.")

    def export_charts(self):
        dialog = ExcelExportDialog(
            client=self.client,
            ref_project=self.ref_project,
            batch_number=self.batch_number,
            parent=self
        )
        dialog.exec_()

    # Add methods to expose raw/extrapolated data and allow recalculation
    def set_raw_data(self, raw_data):
        """Set raw data for charts (for session restore/edit)"""
        self.raw_data = raw_data

    def set_extrapolated_data(self, extrapolated_data):
        """Set extrapolated data for charts (for session restore/edit)"""
        self.extrapolated_data = extrapolated_data

    def recalculate_charts(self, new_values=None, new_deviation=None):
        """Recalculate charts/statistics with edited values/deviation"""
        # Use new_values or new_deviation to update stats and regenerate charts
        # Call SPCChartService or underlying manager to update
        pass

    def closeEvent(self, event):
        if hasattr(self, "chart_worker") and self.chart_worker.isRunning():
            self.chart_worker.quit()
            self.chart_worker.wait()
        event.accept()


# Alias for backward compatibility
SPCChartWindow = ModernSPCChartWindow