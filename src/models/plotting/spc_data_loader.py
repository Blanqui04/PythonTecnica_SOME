# src/models/plotting/spc_data_loader.py
import os
import json
from .logging_config import logger as base_logger


class SPCDataLoader:
    def __init__(self, study_id, base_path="./data/spc"):
        self.study_id = study_id
        self.base_path = base_path
        self.elements_data = {}
        self.logger = base_logger.getChild(self.__class__.__name__)


    def load_complete_report(self, report_path: str = None):
        # If no path is passed, try to find one as before (legacy behavior)
        if report_path is None:
            nested_path = (
                f"{self.base_path}/{self.study_id}/{self.study_id}_complete_report.json"
            )
            flat_path = f"{self.base_path}/{self.study_id}_complete_report.json"

            if os.path.exists(nested_path):
                report_path = nested_path
            elif os.path.exists(flat_path):
                report_path = flat_path
            else:
                self.logger.error(
                    f"Report not found in either location:\n{nested_path}\n{flat_path}"
                )
                return None

        try:
            print(f"Trying to load: {report_path}")
            print("File exists:", os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            self.logger.info(f"Loaded JSON report from {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to load JSON report: {e}")
            return None

        detailed_results = report.get("detailed_results", [])
        extrapolation_results = report.get("extrapolation_results", [])

        if not detailed_results:
            self.logger.warning("No detailed_results found in JSON report.")
            return None

        # Build a lookup dict for extrapolation results by element_name
        extrapolation_lookup = {
            item["element_name"]: item
            for item in extrapolation_results
            if "element_name" in item
        }

        self.elements_data = {}

        for element_info in detailed_results:
            element_name = element_info.get("element_name")
            if not element_name:
                continue

            extrapolated = extrapolation_lookup.get(element_name, {})

            self.elements_data[element_name] = {
                "nominal": element_info.get("nominal"),
                "batch": element_info.get("batch_number"),
                "cavity": element_info.get("cavity"),
                "tolerance": element_info.get("tolerance"),
                "mean": element_info.get("statistics", {}).get("mean"),
                "sample_size": element_info.get("statistics", {}).get("sample_size"),
                "original_values": element_info.get("original_values", []),
                "std_short": element_info.get("statistics", {}).get("std_short"),
                "std_long": element_info.get("statistics", {}).get("std_long"),
                "cp": element_info.get("capability", {}).get("cp"),
                "cpk": element_info.get("capability", {}).get("cpk"),
                "pp": element_info.get("capability", {}).get("pp"),
                "ppk": element_info.get("capability", {}).get("ppk"),
                "ppm_short": element_info.get("capability", {}).get("ppm_short"),
                "ppm_long": element_info.get("capability", {}).get("ppm_long"),
                "ad_value": element_info.get("statistics", {}).get("ad_statistic"),
                "p_value": element_info.get("statistics", {}).get("p_value"),
                "extrapolated_values": extrapolated.get("extrapolated_values", []),
                "extrapolated_ad_value": extrapolated.get("ad_statistic"),
                "extrapolated_p_value": extrapolated.get("p_value"),
            }

        return self.elements_data

    def get_element_data(self, element_name):
        return self.elements_data.get(element_name)


if __name__ == "__main__":
    import sys
    import pprint

    from .logging_config import logger as base_logger
    logger = base_logger.getChild("SPCDataLoader")


    study_id = "test_study"  # Per defecte, el teu estudi
    loader = SPCDataLoader(study_id)
    loader.load_complete_report()

    if not loader.elements_data:
        print("No s'han carregat dades. Comprova el fitxer JSON i la seva estructura.")
        sys.exit(1)

    print(f"Dades carregades per l'estudi '{study_id}':")
    for elem, data in loader.elements_data.items():
        print(f"\nElement: {elem}")
        pprint.pprint(data)
