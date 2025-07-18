import os
import subprocess
import platform
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QMessageBox,
    QFrame,
    QSplitter,
    QTextEdit,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from src.services.spc_chart_service import SPCChartService
from ..logging_config import logger
from ..utils.chart_utils import ChartPathResolver, ChartDisplayHelper


class ChartGenerationWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, client: str, ref_project: str):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.service = None

    def run(self):
        try:
            study_id = f"{self.client}_{self.ref_project}"
            logger.info(f"Starting chart generation for study: {study_id}")

            self.service = SPCChartService(study_id)
            if not self.service.initialize_chart_manager():
                self.error.emit(
                    f"Failed to initialize chart manager for study: {study_id}"
                )
                return

            valid, message = self.service.validate_study_data()
            if not valid:
                self.error.emit(f"Study data validation failed: {message}")
                return

            chart_results = self.service.generate_all_charts(show=False, save=True)

            results = {
                "chart_results": chart_results,
                "elements_summary": self.service.get_elements_summary(),
                "study_statistics": self.service.get_study_statistics(),
                "service": self.service,
            }

            logger.info(
                f"Chart generation completed successfully for {len(chart_results)} elements"
            )
            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Error in chart generation: {str(e)}")
            self.error.emit(f"Error generating charts: {str(e)}")


class SPCChartWindow(QDialog):
    def __init__(self, client: str, ref_project: str, parent=None):
        super().__init__(parent)
        self.client = client
        self.ref_project = ref_project
        self.study_id = f"{client}_{ref_project}"
        self.chart_service = None
        self.elements_data = {}
        self.current_element = None

        self.setup_ui()
        self.start_chart_generation()

    def setup_ui(self):
        self.setWindowTitle(f"SPC Charts - {self.client} - {self.ref_project}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_header_section())

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(self.create_control_panel())
        content_splitter.addWidget(self.create_chart_display_area())
        content_splitter.setSizes([300, 1100])
        main_layout.addWidget(content_splitter)

        main_layout.addWidget(self.create_footer_section())
        self.setLayout(main_layout)

    def create_header_section(self):
        header_frame = QFrame()
        header_frame.setMaximumHeight(80)
        layout = QVBoxLayout()

        title_label = QLabel(f"📊 Analisi de Capacitat - {self.client}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QLabel(
            f"Projecte: {self.ref_project} | ID Estudi: {self.study_id}"
        )
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        layout.addWidget(subtitle_label)

        self.status_label = QLabel("⏳ Generant gràfics...")
        self.status_label.setStyleSheet("color: #007acc; font-weight: bold;")
        layout.addWidget(self.status_label)

        header_frame.setLayout(layout)
        return header_frame

    def create_control_panel(self):
        control_widget = QWidget()
        control_widget.setMaximumWidth(280)
        layout = QVBoxLayout()

        element_group = QFrame()
        element_layout = QVBoxLayout()
        element_layout.addWidget(QLabel("🔍 Selecciona Element:"))

        self.element_combo = QComboBox()
        self.element_combo.setEnabled(False)
        self.element_combo.currentTextChanged.connect(self.on_element_changed)
        element_layout.addWidget(self.element_combo)

        self.element_info = QTextEdit()
        self.element_info.setMaximumHeight(150)
        self.element_info.setReadOnly(True)
        self.element_info.setPlainText("Carregant informació dels elements...")
        element_layout.addWidget(self.element_info)
        element_group.setLayout(element_layout)
        layout.addWidget(element_group)

        chart_group = QFrame()
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(QLabel("📈 Tipus de Gràfic:"))

        self.chart_type_checkboxes = {}
        for chart_type in [
            "capability",
            "normality",
            "extrapolation",
            "individuals",
            "moving_range",
        ]:
            checkbox = QCheckBox(chart_type.capitalize())
            checkbox.setEnabled(False)
            checkbox.stateChanged.connect(self.on_chart_selection_changed)
            chart_layout.addWidget(checkbox)
            self.chart_type_checkboxes[chart_type] = checkbox

        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        layout.addStretch()
        control_widget.setLayout(layout)
        return control_widget

    def create_chart_display_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.chart_content = QWidget()
        self.chart_layout = QVBoxLayout()
        loading_label = QLabel("⏳ Generant gràfics SPC...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("font-size: 18px; color: #666; padding: 50px;")
        self.chart_layout.addWidget(loading_label)

        self.chart_content.setLayout(self.chart_layout)
        scroll_area.setWidget(self.chart_content)
        return scroll_area

    def create_footer_section(self):
        footer_frame = QFrame()
        footer_frame.setMaximumHeight(60)
        layout = QHBoxLayout()

        self.open_folder_btn = QPushButton("📁 Obrir Carpeta")
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)

        self.export_btn = QPushButton("📤 Exportar Gràfics")
        self.export_btn.clicked.connect(self.export_charts)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        layout.addStretch()

        close_btn = QPushButton("❌ Tancar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        footer_frame.setLayout(layout)
        return footer_frame

    def start_chart_generation(self):
        self.chart_worker = ChartGenerationWorker(self.client, self.ref_project)
        self.chart_worker.finished.connect(self.on_charts_generated)
        self.chart_worker.error.connect(self.on_chart_generation_error)
        self.chart_worker.start()

    def on_charts_generated(self, results):
        logger.info("Charts generated successfully, updating UI")

        self.chart_service = results["service"]
        self.elements_data = results["elements_summary"]

        self.status_label.setText("✅ Gràfics generats correctament!")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")

        self.element_combo.clear()
        element_names = list(self.elements_data.keys())
        self.element_combo.addItems(element_names)
        self.element_combo.setEnabled(True)

        for checkbox in self.chart_type_checkboxes.values():
            checkbox.setEnabled(True)

        self.open_folder_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        if element_names:
            self.current_element = element_names[0]
            self.load_element_charts(self.current_element)

    def on_chart_generation_error(self, error_msg):
        logger.error(f"Chart generation failed: {error_msg}")
        self.status_label.setText("❌ Error generant gràfics")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        QMessageBox.critical(
            self, "Error", f"No s'han pogut generar els gràfics:\n\n{error_msg}"
        )

    def on_element_changed(self, element_name):
        if element_name and element_name != self.current_element:
            self.current_element = element_name
            self.load_element_charts(element_name)

    def on_chart_selection_changed(self):
        self.load_element_charts(self.current_element)

    def load_element_charts(self, element_name):
        if not self.chart_service or element_name not in self.elements_data:
            return

        logger.info(f"Loading charts for element: {element_name}")

        element_data = self.elements_data[element_name]
        element_data["element_name"] = element_name
        info_text = ChartDisplayHelper.format_element_info(element_data)
        self.element_info.setPlainText(info_text)

        for i in reversed(range(self.chart_layout.count())):
            widget = self.chart_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for chart_type, checkbox in self.chart_type_checkboxes.items():
            if checkbox.isChecked():
                chart_path = self.chart_service.get_chart_file_path(
                    element_name, chart_type
                )
                if os.path.exists(chart_path):
                    pixmap = QPixmap(chart_path)
                    if not pixmap.isNull():
                        chart_label = QLabel()
                        chart_label.setPixmap(pixmap)
                        chart_label.setAlignment(Qt.AlignCenter)
                        chart_label.setScaledContents(True)
                        chart_label.setMinimumSize(600, 400)
                        self.chart_layout.addWidget(chart_label)
                else:
                    logger.warning(f"Chart not found: {chart_path}")

    def open_results_folder(self):
        folder_path = ChartPathResolver.get_study_directory(
            self.client, self.ref_project
        )
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
        QMessageBox.information(
            self, "Info", "Funcionalitat d'exportació pendent d'implementar."
        )

    def closeEvent(self, event):
        if hasattr(self, "chart_worker") and self.chart_worker.isRunning():
            self.chart_worker.quit()
            self.chart_worker.wait()
        event.accept()
