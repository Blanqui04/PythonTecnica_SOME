# src/gui/workers/capability_study_worker.py
from PyQt5.QtCore import QObject, pyqtSignal
from src.services.capacity_study_service import perform_capability_study


class CapabilityStudyWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, client, ref_project, elements):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.elements = elements

    def run(self):
        try:
            # Call the service function with the elements
            result = perform_capability_study(
                self.client, self.ref_project, self.elements
            )
            self.finished.emit(str(result))
        except Exception as e:
            self.finished.emit(f"Error during capacity study: {e}")
