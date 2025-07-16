# src/models/capability/capability_study_manager.py
"""
Capability Study Manager - Main orchestrator for capability studies
"""

import os
import json
import pandas as pd
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from .extrapolation_manager import ExtrapolationManager, ExtrapolationConfig
from .sample_data_manager import SampleDataManager
from .capability_analyzer import CapabilityAnalyzer, ElementData, ElementType  # noqa: F401
from ...exceptions.sample_errors import SampleErrors

# Configuració del logger
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "capability_study.log")

logging.basicConfig(
    filename=log_path,
    filemode="a",  # append mode
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@dataclass
class StudyConfig:
    """Configuration for capability study"""

    min_sample_size: int = 5
    output_directory: str = "data/spc"
    include_extrapolation: bool = True
    extrapolation_config: Optional[ExtrapolationConfig] = field(
        default_factory=ExtrapolationConfig
    )
    export_detailed_results: bool = True
    export_summary: bool = True

    def __post_init__(self):
        if self.min_sample_size < 5:
            raise ValueError("min_sample_size must be greater than 0")


@dataclass
class StudyResults:
    """Complete results from capability study"""

    study_id: str
    timestamp: datetime
    config: StudyConfig
    elements_analyzed: int
    successful_analyses: int
    failed_analyses: int
    analysis_results: List[Dict]
    extrapolation_results: List[Dict]
    summary_statistics: Dict
    output_files: List[str]


class CapabilityStudyManager:
    """
    Main manager for capability studies - orchestrates the entire process
    """

    def __init__(self, config: Optional[StudyConfig] = None):
        """
        Initialize the capability study manager

        Args:
            config: Configuration for the study
        """
        self.config = config or StudyConfig()
        self.analyzer = CapabilityAnalyzer(min_sample_size=self.config.min_sample_size)
        self.extrapolation_manager = ExtrapolationManager(
            self.config.extrapolation_config
        )
        self.data_manager = SampleDataManager()

        # Ensure output directory exists
        os.makedirs(self.config.output_directory, exist_ok=True)

        # Setup logger for the class
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)  # You can adjust the level here

        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)  # Default output level, can be DEBUG for more details

        # Create formatter and add it to the handlers
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)

        # Add the handlers to logger if not already added
        if not self.logger.hasHandlers():
            self.logger.addHandler(ch)

    def load_data_from_source(
        self, source: Union[str, List[Dict], pd.DataFrame]
    ) -> List[ElementData]:
        """
        Load data from various sources

        Args:
            source: Data source (file path, list of dicts, or DataFrame)

        Returns:
            List[ElementData]: Loaded element data
        """
        self.logger.debug(f"Loading data from source of type {type(source)}")
        if isinstance(source, str):
            # File path
            if source.endswith(".csv"):
                self.logger.info(f"Loading CSV data from {source}")
                return self.data_manager.load_sample_data_from_csv(source)
            elif source.endswith(".json"):
                self.logger.info(f"Loading JSON data from {source}")
                return self.data_manager.load_sample_data_from_json(source)
            else:
                msg = f"Unsupported file format: {source}"
                self.logger.error(msg)
                raise SampleErrors(msg)
        elif isinstance(source, list):
            # List can be dicts or ElementData objects
            if source and isinstance(source[0], ElementData):
                self.logger.info(
                    "Data source is a list of ElementData objects, returning as is"
                )
                return source
            else:
                self.logger.info("Loading data from list of dictionaries")
                return self.data_manager.load_sample_data_from_dict(source)
        elif isinstance(source, pd.DataFrame):
            # DataFrame
            self.logger.info("Loading data from pandas DataFrame")
            return self.data_manager.load_sample_data_from_dataframe(source)
        else:
            msg = f"Unsupported data source type: {type(source)}"
            self.logger.error(msg)
            raise SampleErrors(msg)

    def validate_study_data(self, elements_data: List[ElementData]) -> List[str]:
        """
        Validate data for capability study

        Args:
            elements_data: Elements to validate

        Returns:
            List[str]: Validation errors
        """
        self.logger.debug(f"Validating {len(elements_data)} elements")
        errors = []

        # Load data into manager for validation
        self.data_manager.sample_data = elements_data
        validation_errors = self.data_manager.validate_sample_data(
            self.config.min_sample_size
        )
        errors.extend(validation_errors)

        # Check if we have any data
        if not elements_data:
            errors.append("No elements provided for analysis")

        if errors:
            self.logger.warning(f"Validation errors found: {errors}")
        else:
            self.logger.info("Validation successful - no errors found")

        return errors

    def run_capability_study(
        self,
        data_source: Union[str, List[Dict], pd.DataFrame],
        study_id: Optional[str] = None,
        interactive_extrapolation: bool = True,
    ) -> StudyResults:
        """
        Run complete capability study

        Args:
            data_source: Data source for the study
            study_id: Unique identifier for the study
            interactive_extrapolation: Whether to use interactive extrapolation

        Returns:
            StudyResults: Complete study results
        """
        if study_id is None:
            study_id = f"study_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        timestamp = datetime.now()

        try:
            # Load data
            self.logger.info("Loading data...")
            elements_data = self.load_data_from_source(data_source)
            self.logger.info(f"Loaded {len(elements_data)} elements")

            # Validate data
            self.logger.info("Validating data...")
            validation_errors = self.validate_study_data(elements_data)
            if validation_errors:
                self.logger.error("Validation errors found")
                for error in validation_errors:
                    self.logger.error(f"  - {error}")
                raise SampleErrors(f"Data validation failed: {validation_errors}")

            # Perform capability analysis
            self.logger.info("Performing capability analysis...")
            analysis_results = self.analyzer.analyze_multiple_elements(elements_data)

            # Count successful and failed analyses
            successful_analyses = sum(
                1 for r in analysis_results if "analysis_failed" not in r
            )
            failed_analyses = len(analysis_results) - successful_analyses

            self.logger.info(
                f"Analysis complete: {successful_analyses} successful, {failed_analyses} failed"
            )

            # Perform extrapolation if enabled
            extrapolation_results = []
            if self.config.include_extrapolation and successful_analyses > 0:
                self.logger.info("Performing extrapolation analysis...")

                # Prepare data for extrapolation
                extrapolation_data = []
                for element, result in zip(elements_data, analysis_results):
                    if "analysis_failed" not in result:
                        extrapolation_data.append(
                            {
                                "element_name": element.name,
                                "values": element.values,
                                "nominal": element.nominal,
                                "tol_minus": element.tol_minus,
                            }
                        )

                if interactive_extrapolation:
                    extrap_results = (
                        self.extrapolation_manager.extrapolate_multiple_samples(
                            extrapolation_data, interactive=True
                        )
                    )
                else:
                    # Use default target size for batch processing
                    self.logger.info(
                        "Running batch extrapolation with default target size 50"
                    )
                    extrap_results = self.extrapolation_manager.batch_extrapolate(
                        extrapolation_data, target_size=50
                    )

                # Convert to dictionaries for storage
                for i, extrap_result in enumerate(extrap_results):
                    extrapolation_results.append(
                        {
                            "element_name": extrapolation_data[i]["element_name"],
                            "extrapolated_values": extrap_result.extrapolated_values,
                            "ad_statistic": extrap_result.ad_statistic,
                            "p_value": extrap_result.p_value,
                            "was_extrapolated": extrap_result.was_extrapolated,
                        }
                    )
                self.logger.info(
                    f"Extrapolation completed for {len(extrapolation_results)} elements"
                )

            # Generate summary statistics
            self.logger.info("Generating summary statistics...")
            summary_stats = self._generate_summary_statistics(
                analysis_results, elements_data
            )

            # Export results
            self.logger.info("Exporting results...")
            output_files = self._export_results(
                study_id,
                analysis_results,
                extrapolation_results,
                elements_data,
                summary_stats,
            )

            # Create study results
            self.logger.info(
                f"Study completed successfully. Results saved to: {output_files}"
            )
            study_results = StudyResults(
                study_id=study_id,
                timestamp=timestamp,
                config=self.config,
                elements_analyzed=len(elements_data),
                successful_analyses=successful_analyses,
                failed_analyses=failed_analyses,
                analysis_results=analysis_results,
                extrapolation_results=extrapolation_results,
                summary_statistics=summary_stats,
                output_files=output_files,
            )

            return study_results

        except Exception as e:
            self.logger.error(f"Study failed: {e}", exc_info=True)
            raise SampleErrors(f"Capability study failed: {e}")

    def _generate_summary_statistics(
        self, analysis_results: List[Dict], elements_data: List[ElementData]
    ) -> Dict:
        """
        Generate summary statistics for the study

        Args:
            analysis_results: Results from capability analysis
            elements_data: Original element data

        Returns:
            Dict: Summary statistics
        """
        self.logger.debug("Generating summary statistics")
        successful_results = [r for r in analysis_results if "analysis_failed" not in r]

        if not successful_results:
            self.logger.warning("No successful analyses to summarize")
            return {"error": "No successful analyses to summarize"}

        # Extract capability indices
        cp_values = [r["capability"]["cp"] for r in successful_results]
        cpk_values = [r["capability"]["cpk"] for r in successful_results]
        pp_values = [r["capability"]["pp"] for r in successful_results]
        ppk_values = [r["capability"]["ppk"] for r in successful_results]

        # Count elements by type
        element_types = {}
        for element in elements_data:
            element_type = element.element_type.value
            element_types[element_type] = element_types.get(element_type, 0) + 1

        # Normality statistics
        normal_count = sum(
            1 for r in successful_results if r["statistics"]["is_normal"]
        )

        summary = {
            "total_elements": len(elements_data),
            "successful_analyses": len(successful_results),
            "failed_analyses": len(analysis_results) - len(successful_results),
            "element_types": element_types,
            "normality": {
                "normal_distributions": normal_count,
                "non_normal_distributions": len(successful_results) - normal_count,
                "normality_percentage": (normal_count / len(successful_results)) * 100,
            },
            "capability_indices": {
                "cp": {
                    "mean": sum(cp_values) / len(cp_values),
                    "min": min(cp_values),
                    "max": max(cp_values),
                    "acceptable_count": sum(1 for cp in cp_values if cp >= 1.33),
                },
                "cpk": {
                    "mean": sum(cpk_values) / len(cpk_values),
                    "min": min(cpk_values),
                    "max": max(cpk_values),
                    "acceptable_count": sum(1 for cpk in cpk_values if cpk >= 1.33),
                },
                "pp": {
                    "mean": sum(pp_values) / len(pp_values),
                    "min": min(pp_values),
                    "max": max(pp_values),
                },
                "ppk": {
                    "mean": sum(ppk_values) / len(ppk_values),
                    "min": min(ppk_values),
                    "max": max(ppk_values),
                },
            },
        }

        self.logger.debug(f"Summary statistics generated: {summary}")
        return summary

    def _export_results(
        self,
        study_id: str,
        analysis_results: List[Dict],
        extrapolation_results: List[Dict],
        elements_data: List[ElementData],
        summary_stats: Dict,
    ) -> List[str]:
        """
        Export results to files

        Args:
            study_id: Study identifier
            analysis_results: Analysis results
            extrapolation_results: Extrapolation results
            elements_data: Original element data
            summary_stats: Summary statistics

        Returns:
            List[str]: List of output file paths
        """
        self.logger.debug(f"Starting export of study results for study_id={study_id}")
        output_files = []

        # Export detailed results to CSV
        if self.config.export_detailed_results:
            csv_path = os.path.join(
                self.config.output_directory, f"{study_id}_detailed_results.csv"
            )
            self.logger.debug(f"Exporting detailed results to CSV at {csv_path}")
            self.analyzer.export_results_to_csv(analysis_results, csv_path)
            output_files.append(csv_path)
            self.logger.info(f"Detailed results exported: {csv_path}")

        # Export summary to JSON
        if self.config.export_summary:
            summary_path = os.path.join(
                self.config.output_directory, f"{study_id}_summary.json"
            )
            self.logger.debug(f"Exporting summary statistics to JSON at {summary_path}")
            with open(summary_path, "w") as f:
                json.dump(summary_stats, f, indent=2, default=str)
            output_files.append(summary_path)
            self.logger.info(f"Summary statistics exported: {summary_path}")

        # Export extrapolation results if available
        if extrapolation_results:
            extrap_path = os.path.join(
                self.config.output_directory, f"{study_id}_extrapolation.json"
            )
            self.logger.debug(
                f"Exporting extrapolation results to JSON at {extrap_path}"
            )
            with open(extrap_path, "w") as f:
                json.dump(extrapolation_results, f, indent=2, default=str)
            output_files.append(extrap_path)
            self.logger.info(f"Extrapolation results exported: {extrap_path}")

        # Export complete study report
        report_path = os.path.join(
            self.config.output_directory, f"{study_id}_complete_report.json"
        )
        complete_report = {
            "study_id": study_id,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "min_sample_size": self.config.min_sample_size,
                "include_extrapolation": self.config.include_extrapolation,
            },
            "summary_statistics": summary_stats,
            "detailed_results": analysis_results,
            "extrapolation_results": extrapolation_results,
        }
        self.logger.debug(f"Exporting complete report to JSON at {report_path}")

        with open(report_path, "w") as f:
            json.dump(complete_report, f, indent=2, default=str)
        output_files.append(report_path)
        self.logger.info(f"Complete report exported: {report_path}")

        return output_files

    def run_quick_study(
        self, data_source: Union[str, List[Dict], pd.DataFrame]
    ) -> Dict:
        """
        Run a quick capability study without extrapolation

        Args:
            data_source: Data source for the study

        Returns:
            Dict: Quick study results
        """
        self.logger.info("Running quick capability study")
        # Create a minimal config for quick study
        quick_config = StudyConfig(
            include_extrapolation=False,
            export_detailed_results=False,
            export_summary=False,
        )

        # Temporarily use quick config
        original_config = self.config
        self.config = quick_config

        try:
            # Load and analyze data
            self.logger.debug("Loading data from source for quick study")
            elements_data = self.load_data_from_source(data_source)
            self.logger.info(f"Loaded {len(elements_data)} elements for analysis")
            # Convert all dictionaries to ElementData objects if needed
            # elements_data = [
            #    ElementData(**e) if isinstance(e, dict) else e
            #    for e in elements_data]
            self.logger.debug("Validating study data for quick study")
            validation_errors = self.validate_study_data(elements_data)

            if validation_errors:
                self.logger.warning(
                    f"Data validation failed with errors: {validation_errors}"
                )
                return {"error": "Data validation failed", "errors": validation_errors}

            self.logger.debug("Running analysis on elements")
            analysis_results = self.analyzer.analyze_multiple_elements(elements_data)

            self.logger.debug("Generating summary statistics for quick study")
            summary_stats = self._generate_summary_statistics(
                analysis_results, elements_data
            )

            self.logger.info("Quick capability study completed successfully")
            return {
                "success": True,
                "elements_analyzed": len(elements_data),
                "summary_statistics": summary_stats,
                "analysis_results": analysis_results,
            }

        except Exception as e:
            self.logger.error(
                f"Exception occurred during quick study: {e}", exc_info=True
            )
            return {"error": str(e)}
        finally:
            # Restore original config
            self.config = original_config
            self.logger.debug("Restored original configuration after quick study")

    def get_study_recommendations(self, study_results: StudyResults) -> List[str]:
        """
        Generate recommendations based on study results

        Args:
            study_results: Results from capability study

        Returns:
            List[str]: List of recommendations
        """
        recommendations = []

        if study_results.failed_analyses > 0:
            recommendations.append(
                f"Review {study_results.failed_analyses} failed analyses for data quality issues"
            )

        summary = study_results.summary_statistics

        if "capability_indices" in summary:
            cp_acceptable = summary["capability_indices"]["cp"]["acceptable_count"]
            cpk_acceptable = summary["capability_indices"]["cpk"]["acceptable_count"]
            total_successful = study_results.successful_analyses

            if cp_acceptable < total_successful:
                recommendations.append(
                    f"Process capability (CP): {cp_acceptable}/{total_successful} elements meet minimum requirements (≥1.33)"
                )

            if cpk_acceptable < total_successful:
                recommendations.append(
                    f"Process capability (CPK): {cpk_acceptable}/{total_successful} elements meet minimum requirements (≥1.33)"
                )

        if "normality" in summary:
            normal_pct = summary["normality"]["normality_percentage"]
            if normal_pct < 80:
                recommendations.append(
                    f"Only {normal_pct:.1f}% of samples follow normal distribution. Consider process improvement or different statistical methods"
                )

        return recommendations
