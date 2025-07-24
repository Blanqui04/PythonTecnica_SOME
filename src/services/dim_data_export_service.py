# src/services/dim_data_export_service.py
import json
import csv
import os
import logging
from datetime import datetime
from typing import List, Tuple
from src.models.dimensional.dimensional_result import DimensionalResult


class DataExportService:
    """Service for exporting dimensional analysis results"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def save_to_json(results: List[DimensionalResult], filepath: str) -> None:
        """
        Save results to JSON file

        Args:
            results: List of DimensionalResult objects
            filepath: Path to save JSON file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert results to dictionaries with metadata
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_records": len(results),
                    "export_format_version": "1.0",
                },
                "results": [result.to_dict() for result in results],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)

            logging.getLogger(__name__).info(
                f"Successfully exported {len(results)} results to JSON: {filepath}"
            )

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to save JSON file {filepath}: {str(e)}"
            )
            raise

    @staticmethod
    def save_to_csv(results: List[DimensionalResult], filepath: str) -> None:
        """
        Save results to CSV file

        Args:
            results: List of DimensionalResult objects
            filepath: Path to save CSV file
        """
        if not results:
            logging.getLogger(__name__).warning("No results to export to CSV")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert results to dictionaries
            data = []
            for result in results:
                result_dict = result.to_dict()

                # Flatten list fields for CSV compatibility
                if isinstance(result_dict.get("measurements"), list):
                    result_dict["measurements"] = "; ".join(
                        f"{m:.4f}" for m in result_dict["measurements"]
                    )

                if isinstance(result_dict.get("deviation"), list):
                    result_dict["deviation"] = "; ".join(
                        f"{d:.4f}" for d in result_dict["deviation"]
                    )

                if isinstance(result_dict.get("warnings"), list):
                    result_dict["warnings"] = "; ".join(result_dict["warnings"])

                # Handle GDT flags
                if isinstance(result_dict.get("gdt_flags"), dict):
                    active_flags = [k for k, v in result_dict["gdt_flags"].items() if v]
                    result_dict["gdt_flags"] = "; ".join(active_flags)

                data.append(result_dict)

            # Get field names from first result
            fieldnames = list(data[0].keys()) if data else []

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logging.getLogger(__name__).info(
                f"Successfully exported {len(results)} results to CSV: {filepath}"
            )

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to save CSV file {filepath}: {str(e)}"
            )
            raise

    def export_results(
        self, results: List[DimensionalResult], export_dir: str, base_filename: str
    ) -> Tuple[str, str]:
        """
        Export results to both JSON and CSV formats

        Args:
            results: List of DimensionalResult objects
            export_dir: Directory to save files
            base_filename: Base filename without extension

        Returns:
            Tuple of (json_path, csv_path)
        """
        if not results:
            raise ValueError("No results to export")

        # Ensure export directory exists
        os.makedirs(export_dir, exist_ok=True)

        # Generate file paths with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{base_filename}_{timestamp}.json"
        csv_filename = f"{base_filename}_{timestamp}.csv"

        json_path = os.path.join(export_dir, json_filename)
        csv_path = os.path.join(export_dir, csv_filename)

        # Export to both formats
        self.save_to_json(results, json_path)
        self.save_to_csv(results, csv_path)

        # Generate summary report
        summary_path = os.path.join(
            export_dir, f"{base_filename}_{timestamp}_summary.txt"
        )
        self._generate_summary_report(results, summary_path)

        self.logger.info(
            f"Export completed: JSON={json_path}, CSV={csv_path}, Summary={summary_path}"
        )

        return json_path, csv_path

    def _generate_summary_report(
        self, results: List[DimensionalResult], filepath: str
    ) -> None:
        """
        Generate a human-readable summary report

        Args:
            results: List of DimensionalResult objects
            filepath: Path to save summary report
        """
        try:
            total = len(results)
            good = sum(1 for r in results if r.status.value == "GOOD")
            bad = sum(1 for r in results if r.status.value == "BAD")
            warning = sum(1 for r in results if r.status.value == "WARNING")

            # Calculate statistics
            success_rate = (good / total) * 100 if total > 0 else 0.0

            # Get elements with issues
            failed_elements = [r for r in results if r.status.value == "BAD"]
            warning_elements = [r for r in results if r.status.value == "WARNING"]

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("DIMENSIONAL ANALYSIS SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                # Overall statistics
                f.write("OVERALL STATISTICS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Elements Analyzed: {total}\n")
                f.write(f"Passed (GOOD): {good} ({(good / total) * 100:.1f}%)\n")
                f.write(f"Failed (BAD): {bad} ({(bad / total) * 100:.1f}%)\n")
                f.write(f"Warnings: {warning} ({(warning / total) * 100:.1f}%)\n")
                f.write(f"Success Rate: {success_rate:.1f}%\n\n")

                # Failed elements details
                if failed_elements:
                    f.write("FAILED ELEMENTS\n")
                    f.write("-" * 15 + "\n")
                    for elem in failed_elements:
                        f.write(
                            f"- {elem.element_id}: {elem.description}, {elem.classe}\n"
                        )
                        f.write(f"  Batch: {elem.batch}, Cavity: {elem.cavity}\n")
                        f.write(
                            f"  Out of spec measurements: {elem.out_of_spec_count}/{len(elem.measurements)}\n"
                        )
                        if elem.warnings:
                            f.write(f"  Warnings: {'; '.join(elem.warnings)}\n")
                        f.write("\n")

                # Warning elements details
                if warning_elements:
                    f.write("ELEMENTS WITH WARNINGS\n")
                    f.write("-" * 22 + "\n")
                    for elem in warning_elements:
                        f.write(
                            f"- {elem.element_id}: {elem.description}, {elem.classe}\n"
                        )
                        f.write(f"  Batch: {elem.batch}, Cavity: {elem.cavity}\n")
                        if elem.warnings:
                            f.write(f"  Warnings: {'; '.join(elem.warnings)}\n")
                        f.write("\n")

                # Recommendations
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 15 + "\n")
                if bad > 0:
                    f.write("- Review failed elements and investigate root causes\n")
                    f.write(
                        "- Check measurement procedures and equipment calibration\n"
                    )
                    f.write("- Consider process adjustments for out-of-spec elements\n")

                if warning > 0:
                    f.write(
                        "- Address warning conditions to improve measurement reliability\n"
                    )
                    f.write("- Ensure sufficient number of measurements per element\n")

                if success_rate < 95:
                    f.write(
                        "- Overall success rate below 95% - comprehensive review recommended\n"
                    )
                elif success_rate >= 98:
                    f.write("- Excellent success rate - process performing well\n")

            self.logger.info(f"Summary report generated: {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {str(e)}")

    @staticmethod
    def load_from_json(filepath: str) -> List[DimensionalResult]:
        """
        Load results from JSON file

        Args:
            filepath: Path to JSON file

        Returns:
            List of DimensionalResult objects
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle both old and new format
            if isinstance(data, dict) and "results" in data:
                results_data = data["results"]
            else:
                results_data = data

            results = []
            for result_dict in results_data:
                # Reconstruct DimensionalResult from dict
                # Note: This would require implementing a from_dict method in DimensionalResult
                # For now, return the raw data
                results.append(result_dict)

            logging.getLogger(__name__).info(
                f"Successfully loaded {len(results)} results from JSON: {filepath}"
            )
            return results

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to load JSON file {filepath}: {str(e)}"
            )
            raise
