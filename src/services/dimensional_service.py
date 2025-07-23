# services/dimensional_service.py
import pandas as pd
from typing import List
from models.dimensional.dimensional_analyzer import DimensionalAnalyzer
from models.dimensional.measurement_validator import validate_measurements
from models.dimensional.dimensional_result import DimensionalResult
from services.data_export_service import DataExportService


class DimensionalService:
    def __init__(self):
        self.analyzer = DimensionalAnalyzer()

    def process_dataframe(self, df: pd.DataFrame) -> List[DimensionalResult]:
        results = []
        for _, row in df.iterrows():
            record = row.to_dict()
            if validate_measurements(record):
                result = self.analyzer.analyze_row(record)
                results.append(result)
            else:
                # Could log or warn here about invalid measurements
                pass
        return results

    def export_results(self, results: List[DimensionalResult], out_path: str):
        DataExportService.save_to_json(results, out_path + ".json")
        DataExportService.save_to_csv(results, out_path + ".csv")
