import json
import logging

class SPCDataLoader:
    def __init__(self, study_id, base_path="./data/spc"):
        self.study_id = study_id
        self.base_path = base_path
        self.elements_data = {}

    def load_complete_report(self):
        path = f"{self.base_path}/{self.study_id}_complete_report.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                report = json.load(f)
            logging.info(f"Loaded JSON report from {path}")
        except Exception as e:
            logging.error(f"Failed to load JSON report: {e}")
            return

        detailed_results = report.get("detailed_results", [])
        extrapolation_results = report.get("extrapolation_results", [])

        if not detailed_results:
            logging.warning("No detailed_results found in JSON report.")
            return

        # Build a lookup dict for extrapolation results by element_name
        extrapolation_lookup = {
            item["element_name"]: item for item in extrapolation_results if "element_name" in item
        }

        for element_info in detailed_results:
            element_name = element_info.get("element_name")
            if not element_name:
                continue

            extrapolated = extrapolation_lookup.get(element_name, {})

            self.elements_data[element_name] = {
                "nominal": element_info.get("nominal"),
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

    logging.basicConfig(level=logging.INFO)

    study_id = 'prova'  # Per defecte, el teu estudi
    loader = SPCDataLoader(study_id)
    loader.load_complete_report()

    if not loader.elements_data:
        print("No s'han carregat dades. Comprova el fitxer JSON i la seva estructura.")
        sys.exit(1)

    print(f"Dades carregades per l'estudi '{study_id}':")
    for elem, data in loader.elements_data.items():
        print(f"\nElement: {elem}")
        pprint.pprint(data)
