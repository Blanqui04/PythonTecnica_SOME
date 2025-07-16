from PyQt5.QtCore import QObject, pyqtSignal
from src.services.capacity_study_service import perform_capability_study

class CapabilityStudyWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, client, ref_project, min_samples, extrapolate):
        super().__init__()
        self.client = client
        self.ref_project = ref_project
        self.min_samples = min_samples
        self.extrapolate = extrapolate

    def run(self):
        try:
            result = perform_capability_study(
                self.client,
                self.ref_project,
                self.min_samples,
                self.extrapolate
            )
            self.finished.emit(str(result))
        except Exception as e:
            self.finished.emit(f"Error during capacity study: {e}")
