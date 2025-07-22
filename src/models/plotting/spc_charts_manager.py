# src/statistics/plotting/spc_chart_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import os

from .logging_config import logger as base_logger

from .spc_data_loader import SPCDataLoader
from .i_chart import IChart
from .mr_chart import MRChart
from .capability_chart import CapabilityChart
from .extrapolation_chart import ExtrapolatedSPCChart
from .normality_plot import NormalityAnalysisChart


class SPCChartManager:
    """
    Manager class for creating SPC charts from loaded data.
    Handles multiple chart types and elements.
    """

    CHART_TYPES = {
        "normality": NormalityAnalysisChart,
        # Add more chart types here as they are implemented
        "individuals": IChart,
        "moving_range": MRChart,
        "capability": CapabilityChart,
        "extrapolation": ExtrapolatedSPCChart,
    }

    def __init__(
        self,
        study_id: str,
        base_path: str = "./data/spc",
        output_dir: str = "./data/reports/charts",
        lang: str = "ca",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SPC Chart Manager.

        Args:
            study_id: Study identifier
            base_path: Base path for data files
            output_dir: Output directory for charts
            lang: Language for chart labels
            logger: Optional logger instance
        """
        self.study_id = study_id
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.lang = lang
        self.logger = logger or base_logger.getChild(self.__class__.__name__)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data loader
        self.data_loader = SPCDataLoader(study_id, base_path)
        self.elements_data = {}

        self.logger.info(f"Initialized SPCChartManager for study '{study_id}'")

    def load_data(self) -> bool:
        """
        Load SPC data from the complete report.

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        self.logger.info(f"Loading data for study: '{self.study_id}'")
        report_path = (
            self.base_path / self.study_id / f"{self.study_id}_complete_report.json"
        )
        print(report_path)
        if not report_path.exists():
            legacy_path = self.base_path / f"{self.study_id}_complete_report.json"
            if legacy_path.exists():
                self.logger.warning(f"Using legacy report path: {legacy_path}")
                report_path = legacy_path
            else:
                self.logger.error(
                    f"SPC report not found in either path:\n  - {report_path}\n  - {legacy_path}"
                )
                return False  # no exception, just return False

        # Try loading the data with the chosen report_path
        try:
            self.elements_data = SPCDataLoader(
                self.study_id, self.base_path
            ).load_complete_report(report_path)
            # You can check if elements_data is empty or None here and return False if needed
            if not self.elements_data:
                self.logger.error(f"No data loaded from report: {report_path}")
                return False
        except Exception as e:
            self.logger.error(f"Exception loading report: {e}", exc_info=True)
            return False

        return True

    def _convert_element_data_for_chart(
        self, element_name: str, element_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert loaded element data to the format expected by chart classes.

        Args:
            element_name: Name of the element
            element_data: Raw element data from loader

        Returns:
            Dict containing data formatted for chart classes
        """
        self.logger.debug(f"Converting data for element '{element_name}'")

        # Map the loaded data to the format expected by NormalityAnalysisChart
        chart_data = {
            "element_name": element_name,
            "sample_data": element_data.get("original_values", []),
            "nominal": element_data.get("nominal", 0),
            "tolerance": element_data.get("tolerance", [-1, 1]),
            "std_short": element_data.get("std_short"),
            "std_long": element_data.get("std_long"),
            "pval_ad": element_data.get("p_value"),
            "ad": element_data.get("ad_value"),
            "ad_result": element_data.get("p_value", 0) > 0.05
            if element_data.get("p_value") is not None
            else None,
            "output_dir": str(self.output_dir),
            "mean": element_data.get("mean"),
            "sample_size": element_data.get("sample_size"),
            "cp": element_data.get("cp"),
            "cpk": element_data.get("cpk"),
            "pp": element_data.get("pp"),
            "ppk": element_data.get("ppk"),
            "ppm_short": element_data.get("ppm_short"),
            "ppm_long": element_data.get("ppm_long"),
        }

        # Add extrapolation data if available
        extrapolated_values = element_data.get("extrapolated_values", [])
        if extrapolated_values:
            chart_data["extrapolated_values"] = extrapolated_values
            chart_data["extrapolated_ad_value"] = element_data.get(
                "extrapolated_ad_value"
            )
            chart_data["extrapolated_p_value"] = element_data.get(
                "extrapolated_p_value"
            )
            print(chart_data)

        return chart_data

    def create_chart(
        self, element_name: str, chart_type: str, show: bool = False, save: bool = True
    ) -> bool:
        """
        Create a single chart for a specific element and chart type.

        Args:
            element_name: Name of the element
            chart_type: Type of chart to create
            show: Whether to display the chart
            save: Whether to save the chart

        Returns:
            bool: True if chart created successfully, False otherwise
        """
        self.logger.info(f"Creating {chart_type} chart for element '{element_name}'")

        if chart_type not in self.CHART_TYPES:
            self.logger.error(f"Unknown chart type: {chart_type}")
            return False

        if element_name not in self.elements_data:
            self.logger.error(f"Element '{element_name}' not found in loaded data")
            return False

        try:
            # Get the chart class
            chart_class = self.CHART_TYPES[chart_type]

            # Convert element data to chart format
            element_data = self.elements_data[element_name]
            chart_data = self._convert_element_data_for_chart(
                element_name, element_data
            )

            # Create temporary JSON file with chart data
            temp_data = {element_name: chart_data}

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as temp_file:
                json.dump(temp_data, temp_file, indent=2)
                temp_file_path = temp_file.name

            try:
                # Determine save path
                save_path = None
                if save:
                    save_path = (
                        self.output_dir
                        / f"{self.study_id}_{element_name}_{chart_type}.png"
                    )

                # Create chart instance
                chart = chart_class(
                    input_json_path=temp_file_path,
                    lang=self.lang,
                    show=show,
                    save_path=save_path,
                    element_name=element_name,
                    logger=self.logger,
                )

                # Generate the chart
                chart.plot()

                self.logger.info(
                    f"Successfully created {chart_type} chart for '{element_name}'"
                )
                if save_path:
                    self.logger.info(f"Chart saved to: {save_path}")

                return True

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to delete temporary file {temp_file_path}: {e}"
                    )

        except Exception as e:
            self.logger.error(
                f"Failed to create {chart_type} chart for '{element_name}': {e}",
                exc_info=True,
            )
            return False

    def create_all_charts(
        self,
        chart_types: Optional[List[str]] = None,
        elements: Optional[List[str]] = None,
        show: bool = False,
        save: bool = True,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Create all charts for specified elements and chart types.

        Args:
            chart_types: List of chart types to create (default: all available)
            elements: List of elements to process (default: all loaded elements)
            show: Whether to display charts
            save: Whether to save charts

        Returns:
            Dict mapping element names to chart creation results
        """
        if not self.elements_data:
            self.logger.error("No elements data loaded. Call load_data() first.")
            return {}

        # Use defaults if not specified
        chart_types = chart_types or list(self.CHART_TYPES.keys())
        elements = elements or list(self.elements_data.keys())

        self.logger.info(
            f"Creating charts for {len(elements)} elements and {len(chart_types)} chart types"
        )
        self.logger.info(f"Elements: {elements}")
        self.logger.info(f"Chart types: {chart_types}")

        results = {}

        for element_name in elements:
            if element_name not in self.elements_data:
                self.logger.warning(
                    f"Element '{element_name}' not found in loaded data. Skipping."
                )
                continue

            element_results = {}

            for chart_type in chart_types:
                # Skip extrapolation charts if no extrapolated data
                if chart_type == "extrapolation":
                    extrapolated_values = self.elements_data[element_name].get(
                        "extrapolated_values", []
                    )
                    if not extrapolated_values:
                        self.logger.info(
                            f"No extrapolated values for '{element_name}'. Skipping extrapolation chart."
                        )
                        element_results[chart_type] = False
                        continue

                # Create the chart
                success = self.create_chart(
                    element_name, chart_type, show=show, save=save
                )
                element_results[chart_type] = success

            results[element_name] = element_results

        # Log summary
        total_charts = sum(len(elem_results) for elem_results in results.values())
        successful_charts = sum(
            sum(elem_results.values()) for elem_results in results.values()
        )

        self.logger.info(
            f"Chart creation complete: {successful_charts}/{total_charts} charts created successfully"
        )

        return results

    def get_elements_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all loaded elements and their available data.

        Returns:
            Dict containing summary information for each element
        """
        if not self.elements_data:
            return {}

        summary = {}

        for element_name, element_data in self.elements_data.items():
            summary[element_name] = {
                "sample_size": len(element_data.get("original_values", [])),
                "has_extrapolation": bool(element_data.get("extrapolated_values", [])),
                "has_normality_test": element_data.get("p_value") is not None,
                "nominal": element_data.get("nominal"),
                "tolerance": element_data.get("tolerance"),
                "mean": element_data.get("mean"),
                "cp": element_data.get("cp"),
                "cpk": element_data.get("cpk"),
            }

        return summary


if __name__ == "__main__":
    study_id = "test_study"
    logger = base_logger.getChild("SPCChartManager")
    manager = SPCChartManager(study_id, logger=logger)

    if manager.load_data():
        print("Data loaded successfully")
        summary = manager.get_elements_summary()
        print(f"Elements summary: {summary}")

        # Create all available charts
        results = manager.create_all_charts(show=True, save=True)
        print(f"Chart creation results: {results}")
    else:
        print("Failed to load data")
