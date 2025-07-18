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
from ..logging_config import logger
from ..utils.chart_utils import ChartPathResolver, ChartDisplayHelper
from ..utils.styles import global_style, get_color_palette
from ..widgets.buttons import ModernButton, ActionButton, CompactButton
from ..widgets.inputs import ModernComboBox, ModernTextEdit


class ChartGenerationWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, client: str, ref_project: str):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.service = None

    def run(self):
        try:
            study_id = f"{self.client}_{self.ref_project}"
            logger.info(f"Starting chart generation for study: {study_id}")
            
            self.progress.emit(10)
            
            self.service = SPCChartService(study_id)
            if not self.service.initialize_chart_manager():
                self.error.emit(f"Failed to initialize chart manager for study: {study_id}")
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
            
            logger.info(f"Chart generation completed successfully for {len(chart_results)} elements")
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
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Control bar
        control_bar = self.create_control_bar()
        self.main_layout.addWidget(control_bar)
        
        # Chart container
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_container.setLayout(self.chart_layout)
        self.main_layout.addWidget(self.chart_container)
        
        self.setLayout(self.main_layout)
    
    def create_control_bar(self):
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout()
        
        # Layout mode selector
        layout_label = QLabel("Layout:")
        layout_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        layout.addWidget(layout_label)
        
        self.layout_group = QButtonGroup()
        
        auto_radio = QRadioButton("Auto")
        auto_radio.setChecked(True)
        auto_radio.toggled.connect(lambda: self.set_layout_mode("auto"))
        self.layout_group.addButton(auto_radio)
        layout.addWidget(auto_radio)
        
        grid_radio = QRadioButton("Grid")
        grid_radio.toggled.connect(lambda: self.set_layout_mode("grid"))
        self.layout_group.addButton(grid_radio)
        layout.addWidget(grid_radio)
        
        vertical_radio = QRadioButton("Vertical")
        vertical_radio.toggled.connect(lambda: self.set_layout_mode("vertical"))
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
        layout.addWidget(self.per_row_spin)
        
        layout.addStretch()
        
        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self.set_zoom_level)
        layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFont(QFont("Segoe UI", 9))
        self.zoom_label.setMinimumWidth(40)
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
    
    def add_chart(self, chart_path, chart_type):
        """Add a chart to the display"""
        if os.path.exists(chart_path):
            chart_info = {
                'path': chart_path,
                'type': chart_type,
                'pixmap': QPixmap(chart_path)
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
                    color: #95a5a6;
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
            row_layout.setSpacing(15)
            
            for col in range(charts_per_row):
                chart_idx = row * charts_per_row + col
                if chart_idx < len(self.charts):
                    chart_info = self.charts[chart_idx]
                    chart_widget = self.create_chart_widget(chart_info, zoom_factor, True)
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
        """Create a widget for displaying a single chart"""
        chart_widget = QFrame()
        chart_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Chart title
        title_label = QLabel(chart_info['type'].replace('_', ' ').title())
        title_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Chart image
        chart_label = QLabel()
        pixmap = chart_info['pixmap']
        
        if not pixmap.isNull():
            # Calculate size based on zoom and layout mode
            if is_grid:
                target_width = int(400 * zoom_factor)
                target_height = int(300 * zoom_factor)
            else:
                target_width = int(800 * zoom_factor)
                target_height = int(600 * zoom_factor)
            
            scaled_pixmap = pixmap.scaled(
                target_width, 
                target_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            chart_label.setPixmap(scaled_pixmap)
        
        chart_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart_label)
        
        chart_widget.setLayout(layout)
        return chart_widget


class ModernSPCChartWindow(QDialog):
    def __init__(self, client: str, ref_project: str, parent=None):
        super().__init__(parent)
        self.client = client
        self.ref_project = ref_project
        self.study_id = f"{client}_{ref_project}"
        self.chart_service = None
        self.elements_data = {}
        self.current_element = None
        self.colors = get_color_palette()
        
        self.setup_ui()
        self.apply_styles()
        self.start_chart_generation()

    def setup_ui(self):
        self.setWindowTitle(f"SPC Charts - {self.client} - {self.ref_project}")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 900)
        
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
        content_splitter.setSizes([350, 1250])
        main_layout.addWidget(content_splitter)
        
        # Footer
        footer_widget = self.create_footer_section()
        main_layout.addWidget(footer_widget)
        
        self.setLayout(main_layout)

    def create_header_section(self):
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['secondary']}, stop:1 {self.colors['secondary_dark']});
                border: none;
                padding: 20px;
            }}
        """)
        header_frame.setFixedHeight(120)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("📊 Anàlisi de Capacitat SPC")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel(f"Client: {self.client} | Projecte: {self.ref_project}")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setStyleSheet("color: #ecf0f1; margin-bottom: 10px;")
        layout.addWidget(subtitle_label)
        
        # Status and progress
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("⏳ Inicialitzant generació de gràfics...")
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        self.status_label.setStyleSheet("color: #ffffff;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.colors['primary']};
                border-radius: 3px;
            }}
        """)
        status_layout.addWidget(self.progress_bar)
        
        layout.addLayout(status_layout)
        header_frame.setLayout(layout)
        
        return header_frame

    def create_control_panel(self):
        control_widget = QWidget()
        control_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['surface']};
                border-right: 1px solid {self.colors['border']};
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
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
        layout = QVBoxLayout()
        
        # Element selector
        self.element_combo = ModernComboBox()
        self.element_combo.setEnabled(False)
        self.element_combo.currentTextChanged.connect(self.on_element_changed)
        layout.addWidget(self.element_combo)
        
        # Element information
        self.element_info = ModernTextEdit()
        self.element_info.setMaximumHeight(120)
        self.element_info.setReadOnly(True)
        self.element_info.setPlainText("Carregant informació dels elements...")
        layout.addWidget(self.element_info)
        
        group.setLayout(layout)
        return group

    def create_chart_type_group(self):
        group = QGroupBox("📈 Tipus de Gràfics")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        layout = QVBoxLayout()
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = CompactButton("Tots")
        self.select_all_btn.clicked.connect(self.select_all_charts)
        self.select_all_btn.setEnabled(False)
        button_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = CompactButton("Cap")
        self.select_none_btn.clicked.connect(self.select_no_charts)
        self.select_none_btn.setEnabled(False)
        button_layout.addWidget(self.select_none_btn)
        
        layout.addLayout(button_layout)
        
        # Chart type checkboxes
        self.chart_type_checkboxes = {}
        chart_types = [
            ("capability", "📊 Capacitat"),
            ("normality", "📈 Normalitat"),
            ("extrapolation", "🔮 Extrapolació"),
            ("individuals", "👤 Individuals"),
            ("moving_range", "📉 Rang Mòbil"),
        ]
        
        for chart_type, display_name in chart_types:
            checkbox = QCheckBox(display_name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setEnabled(False)
            checkbox.stateChanged.connect(self.on_chart_selection_changed)
            layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type] = checkbox
        
        group.setLayout(layout)
        return group

    def create_statistics_group(self):
        group = QGroupBox("📊 Estadístiques")
        group.setFont(QFont("Segoe UI", 11, QFont.Medium))
        layout = QVBoxLayout()
        
        self.stats_info = ModernTextEdit()
        self.stats_info.setMaximumHeight(100)
        self.stats_info.setReadOnly(True)
        self.stats_info.setPlainText("Estadístiques no disponibles...")
        layout.addWidget(self.stats_info)
        
        group.setLayout(layout)
        return group

    def create_chart_display_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.colors['background']};
                border: none;
            }}
        """)
        
        self.chart_display = ChartDisplayWidget()
        scroll_area.setWidget(self.chart_display)
        
        return scroll_area

    def create_footer_section(self):
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border-top: 1px solid {self.colors['border']};
                padding: 15px 20px;
            }}
        """)
        footer_frame.setFixedHeight(80)
        
        layout = QHBoxLayout()
        
        # Action buttons
        self.open_folder_btn = ActionButton("📁 Obrir Carpeta")
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)
        
        self.export_btn = ActionButton("📤 Exportar Gràfics")
        self.export_btn.clicked.connect(self.export_charts)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        layout.addStretch()
        
        # Close button
        close_btn = ModernButton("❌ Tancar", primary=True)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        footer_frame.setLayout(layout)
        return footer_frame

    def apply_styles(self):
        """Apply the global styles to the window"""
        self.setStyleSheet(global_style())

    def start_chart_generation(self):
        self.chart_worker = ChartGenerationWorker(self.client, self.ref_project)
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
        self.status_label.setStyleSheet(f"color: {self.colors['success']}; font-weight: bold;")
        self.progress_bar.setValue(100)
        
        # Enable controls
        self.element_combo.clear()
        element_names = list(self.elements_data.keys())
        self.element_combo.addItems(element_names)
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
        if element_names:
            self.current_element = element_names[0]
            self.load_element_charts(self.current_element)

    def on_chart_generation_error(self, error_msg):
        logger.error(f"Chart generation failed: {error_msg}")
        self.status_label.setText("❌ Error generant gràfics")
        self.status_label.setStyleSheet(f"color: {self.colors['danger']}; font-weight: bold;")
        self.progress_bar.setValue(0)
        
        QMessageBox.critical(
            self, 
            "Error de Generació", 
            f"No s'han pogut generar els gràfics:\n\n{error_msg}"
        )

    def on_element_changed(self, element_name):
        if element_name and element_name != self.current_element:
            self.current_element = element_name
            self.load_element_charts(element_name)

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
        if not self.chart_service or element_name not in self.elements_data:
            return
        
        logger.info(f"Loading charts for element: {element_name}")
        
        # Update element info
        element_data = self.elements_data[element_name]
        element_data["element_name"] = element_name
        info_text = ChartDisplayHelper.format_element_info(element_data)
        self.element_info.setPlainText(info_text)
        
        # Clear and load charts
        self.chart_display.clear_charts()
        
        for chart_type, checkbox in self.chart_type_checkboxes.items():
            if checkbox.isChecked():
                chart_path = self.chart_service.get_chart_file_path(element_name, chart_type)
                if os.path.exists(chart_path):
                    self.chart_display.add_chart(chart_path, chart_type)
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
        folder_path = ChartPathResolver.get_study_directory(self.client, self.ref_project)
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
                QMessageBox.warning(self, "Error", f"No s'ha pogut obrir la carpeta:\n{e}")
        else:
            QMessageBox.warning(self, "Error", "La carpeta de resultats no existeix.")

    def export_charts(self):
        QMessageBox.information(
            self, 
            "Exportació", 
            "Funcionalitat d'exportació pendent d'implementar.\n\n"
            "Aquesta funcionalitat permetrà exportar els gràfics "
            "en diferents formats (PDF, PNG, SVG)."
        )

    def closeEvent(self, event):
        if hasattr(self, "chart_worker") and self.chart_worker.isRunning():
            self.chart_worker.quit()
            self.chart_worker.wait()
        event.accept()


# Alias for backward compatibility
SPCChartWindow = ModernSPCChartWindow