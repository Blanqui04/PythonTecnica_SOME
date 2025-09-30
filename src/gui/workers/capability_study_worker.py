# src/gui/workers/capability_study_worker.py
from PyQt5.QtCore import QObject, pyqtSignal
from src.services.capacity_study_service import perform_capability_study
import logging

logger = logging.getLogger(__name__)


class CapabilityStudyWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(
        self, client, ref_project, elements, extrap_config=None, batch_number=None
    ):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.elements = elements
        self.extrap_config = extrap_config
        self.batch_number = batch_number

    def run(self):
        try:
            logger.info(f"Starting capability study for {self.client} - {self.ref_project} - Batch: {self.batch_number}")
            logger.info(f"Processing {len(self.elements)} elements with cavity information")
            
            # Log element details for debugging (including cavity information)
            for i, element in enumerate(self.elements):
                element_id = element.get('element_id', 'Unknown')
                cavity = element.get('cavity', 'N/A')
                logger.info(f"Element {i+1}: {element_id} - Cavity: {cavity}")
            
            # Validate that all elements have cavity information
            missing_cavity_elements = []
            for element in self.elements:
                if not element.get('cavity'):
                    missing_cavity_elements.append(element.get('element_id', 'Unknown'))
            
            if missing_cavity_elements:
                error_msg = f"The following elements are missing cavity information: {', '.join(missing_cavity_elements)}. Cavity is required to properly identify dimensions."
                logger.error(error_msg)
                self.finished.emit(f"Error: {error_msg}")
                return
            
            # Perform the capability study with enhanced element identification
            result = perform_capability_study(
                self.client,
                self.ref_project,
                self.elements,
                self.extrap_config,
                batch_number=self.batch_number,
            )
            
            # Use thread-safe chart generation
            chart_results = self.service.generate_all_charts_threadsafe(show=False, save=True)

            results = {
                "chart_results": chart_results,
                "elements_summary": self.service.get_elements_summary(),
                "study_statistics": self.service.get_study_statistics(),
                "chart_service": self.service,
            }

            self.finished.emit(results)
            
            logger.info("Capability study completed successfully")
            
        except Exception as e:
            error_msg = f"Error during capacity study: {e}"
            logger.error(error_msg)
            logger.error("Exception details:", exc_info=True)
            
            # Enhanced error message with context
            detailed_error = "Capability Study failed!\n\n"
            detailed_error += f"Client: {self.client}\n"
            detailed_error += f"Project: {self.ref_project}\n"
            detailed_error += f"Batch: {self.batch_number}\n\n"
            detailed_error += f"Error: {str(e)}\n\n"
            detailed_error += "Please check that:\n"
            detailed_error += "• All elements have valid cavity information\n"
            detailed_error += "• Database connection is available\n"
            detailed_error += "• All measurement data is properly formatted\n"
            
            self.finished.emit(detailed_error)