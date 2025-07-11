"""
Sample Data Manager - Handles sample data loading, validation, and management
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union  # noqa: F401
import json
import os

from src.models.capability.capability_analyzer import ElementData, ElementType
from ...exceptions.sample_errors import SampleErrors

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),    # Save logs to file
        logging.StreamHandler()            # Also print logs to console
    ]
)

logger = logging.getLogger(__name__)


class SampleDataManager:
    """
    Manages sample data for capability studies
    """

    def __init__(self):
        """Initialize the sample data manager"""
        logger.info("Inicialitzant SampleDataManager")
        self.sample_data: List[ElementData] = []

    def load_sample_data_from_dict(self, data: List[Dict]) -> List[ElementData]:
        """
        Load sample data from dictionary format

        Args:
            data: List of dictionaries with sample data

        Returns:
            List[ElementData]: List of element data objects
        """
        logger.info(f"Iniciant càrrega de dades des de dict amb {len(data)} elements")
        elements = []

        for item in data:
            try:
                element_data = ElementData(
                    name=str(item["Element"]),
                    nominal=float(item["Nominal"]),
                    tol_minus=float(item["Tol-"]),
                    tol_plus=float(item["Tol+"]),
                    values=[float(v) for v in item["Values"]],
                )

                # Detect element type
                from .capability_analyzer import CapabilityAnalyzer

                analyzer = CapabilityAnalyzer()
                element_data.element_type = analyzer.detect_element_type(
                    element_data.name
                )

                elements.append(element_data)
                logger.debug(
                    f"Afegit element: {element_data.name} tipus: {element_data.element_type}"
                )

            except (KeyError, ValueError, TypeError) as e:
                logger.error(
                    f"Error processant element {item.get('Element', 'unknown')}: {e}"
                )
                raise SampleErrors(
                    f"Error processing element {item.get('Element', 'unknown')}: {e}"
                )

        self.sample_data = elements
        logger.info(
            f"Càrrega de dades des de dict finalitzada amb {len(elements)} elements"
        )
        return elements

    def load_sample_data_from_dataframe(self, df: pd.DataFrame) -> List[ElementData]:
        """
        Load sample data from DataFrame

        Args:
            df: DataFrame with sample data

        Returns:
            List[ElementData]: List of element data objects
        """
        logger.info(f"Iniciant càrrega de dades des de DataFrame amb {len(df)} files")
        elements = []

        for _, row in df.iterrows():
            try:
                element_data = ElementData(
                    name=str(row["Element"]),
                    nominal=float(row["Nominal"]),
                    tol_minus=float(row["Tol-"]),
                    tol_plus=float(row["Tol+"]),
                    values=[float(v) for v in row["Values"]],
                )

                # Detect element type
                from .capability_analyzer import CapabilityAnalyzer

                analyzer = CapabilityAnalyzer()
                element_data.element_type = analyzer.detect_element_type(
                    element_data.name
                )

                elements.append(element_data)
                logger.debug(
                    f"Afegit element: {element_data.name} tipus: {element_data.element_type}"
                )

            except (KeyError, ValueError, TypeError) as e:
                logger.error(
                    f"Error processant fila {row.get('Element', 'unknown')}: {e}"
                )
                raise SampleErrors(
                    f"Error processing row {row.get('Element', 'unknown')}: {e}"
                )

        self.sample_data = elements
        logger.info(
            f"Càrrega de dades des de DataFrame finalitzada amb {len(elements)} elements"
        )
        return elements

    def load_sample_data_from_csv(self, filepath: str) -> List[ElementData]:
        """
        Load sample data from CSV file

        Args:
            filepath: Path to CSV file

        Returns:
            List[ElementData]: List of element data objects
        """
        logger.info(f"Carregant dades des de fitxer CSV: {filepath}")
        if not os.path.exists(filepath):
            logger.error(f"Fitxer no trobat: {filepath}")
            raise SampleErrors(f"File not found: {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.debug(f"CSV llegit correctament, {len(df)} files")
            return self.load_sample_data_from_dataframe(df)
        except Exception as e:
            logger.error(f"Error carregant fitxer CSV: {e}")
            raise SampleErrors(f"Error loading CSV file: {e}")

    def load_sample_data_from_json(self, filepath: str) -> List[ElementData]:
        """
        Load sample data from JSON file

        Args:
            filepath: Path to JSON file

        Returns:
            List[ElementData]: List of element data objects
        """
        logger.info(f"Carregant dades des de fitxer JSON: {filepath}")
        if not os.path.exists(filepath):
            logger.error(f"Fitxer no trobat: {filepath}")
            raise SampleErrors(f"File not found: {filepath}")

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            logger.debug(f"JSON llegit correctament, {len(data)} elements")
            return self.load_sample_data_from_dict(data)
        except Exception as e:
            logger.error(f"Error carregant fitxer JSON: {e}")
            raise SampleErrors(f"Error loading JSON file: {e}")

    def create_sample_element(
        self,
        name: str,
        nominal: float,
        tol_minus: float,
        tol_plus: float,
        values: List[float],
    ) -> ElementData:
        """
        Create a single element data object

        Args:
            name: Element name
            nominal: Nominal value
            tol_minus: Lower tolerance
            tol_plus: Upper tolerance
            values: Sample values

        Returns:
            ElementData: Element data object
        """
        element_data = ElementData(
            name=name,
            nominal=nominal,
            tol_minus=tol_minus,
            tol_plus=tol_plus,
            values=values,
        )

        # Detect element type
        from .capability_analyzer import CapabilityAnalyzer

        analyzer = CapabilityAnalyzer()
        element_data.element_type = analyzer.detect_element_type(element_data.name)

        return element_data

    def add_sample_element(self, element_data: ElementData) -> None:
        """
        Add element to sample data collection

        Args:
            element_data: Element data to add
        """
        self.sample_data.append(element_data)

    def get_sample_data(self) -> List[ElementData]:
        """
        Get current sample data

        Returns:
            List[ElementData]: Current sample data
        """
        return self.sample_data

    def clear_sample_data(self) -> None:
        """Clear all sample data"""
        self.sample_data.clear()

    def validate_sample_data(self, min_sample_size: int = 5) -> List[str]:
        """
        Validate all sample data

        Args:
            min_sample_size: Minimum required sample size

        Returns:
            List[str]: List of validation errors
        """
        logger.info(f"Iniciant validació de dades amb mida mínima {min_sample_size}")
        errors = []

        for element in self.sample_data:
            # Check sample size
            if len(element.values) < min_sample_size:
                errors.append(
                    f"{element.name}: Sample size {len(element.values)} < {min_sample_size}"
                )
                error_msg = f"{element.name}: Sample size {len(element.values)} < {min_sample_size}"
                logger.warning(error_msg)
                errors.append(error_msg)
            # Check for numeric values
            if not all(isinstance(v, (int, float)) for v in element.values):
                errors.append(f"{element.name}: Non-numeric values found")
                error_msg = f"{element.name}: Non-numeric values found"
                logger.warning(error_msg)
                errors.append(error_msg)
            # Check for NaN or infinite values
            if any(np.isnan(v) or np.isinf(v) for v in element.values):
                errors.append(f"{element.name}: NaN or infinite values found")
                error_msg = f"{element.name}: NaN or infinite values found"
                logger.warning(error_msg)
                errors.append(error_msg)
            # Check tolerance values
            if element.tol_minus > element.tol_plus:
                errors.append(f"{element.name}: Lower tolerance > upper tolerance")
                error_msg = f"{element.name}: Lower tolerance > upper tolerance"
                logger.warning(error_msg)
                errors.append(error_msg)
        logger.info(f"Validació finalitzada amb {len(errors)} errors trobats")
        return errors

    def get_element_by_name(self, name: str) -> Optional[ElementData]:
        """
        Get element by name

        Args:
            name: Element name

        Returns:
            Optional[ElementData]: Element data if found
        """
        for element in self.sample_data:
            if element.name == name:
                return element
        return None

    def remove_element_by_name(self, name: str) -> bool:
        """
        Remove element by name

        Args:
            name: Element name

        Returns:
            bool: True if element was removed
        """
        for i, element in enumerate(self.sample_data):
            if element.name == name:
                del self.sample_data[i]
                return True
        return False

    def get_elements_by_type(self, element_type: ElementType) -> List[ElementData]:
        """
        Get elements by type

        Args:
            element_type: Type of elements to retrieve

        Returns:
            List[ElementData]: Elements of specified type
        """
        return [
            element
            for element in self.sample_data
            if element.element_type == element_type
        ]

    def get_sample_summary(self) -> Dict:
        """
        Get summary of sample data

        Returns:
            Dict: Summary statistics
        """
        if not self.sample_data:
            return {"total_elements": 0}

        summary = {
            "total_elements": len(self.sample_data),
            "elements_by_type": {
                "dimensional": len(self.get_elements_by_type(ElementType.DIMENSIONAL)),
                "gdt": len(self.get_elements_by_type(ElementType.GDT)),
                "traction": len(self.get_elements_by_type(ElementType.TRACTION)),
            },
            "sample_sizes": {
                "min": min(len(element.values) for element in self.sample_data),
                "max": max(len(element.values) for element in self.sample_data),
                "avg": sum(len(element.values) for element in self.sample_data)
                / len(self.sample_data),
            },
        }

        return summary

    def export_sample_data_to_csv(self, filepath: str) -> None:
        """
        Export sample data to CSV

        Args:
            filepath: Path to save CSV file
        """
        data_for_export = []

        for element in self.sample_data:
            data_for_export.append(
                {
                    "Element": element.name,
                    "Nominal": element.nominal,
                    "Tol-": element.tol_minus,
                    "Tol+": element.tol_plus,
                    "Values": json.dumps(element.values),
                    "Element_Type": element.element_type.value,
                }
            )

        df = pd.DataFrame(data_for_export)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)

    def export_sample_data_to_json(self, filepath: str) -> None:
        """
        Export sample data to JSON

        Args:
            filepath: Path to save JSON file
        """
        data_for_export = []

        for element in self.sample_data:
            data_for_export.append(
                {
                    "Element": element.name,
                    "Nominal": element.nominal,
                    "Tol-": element.tol_minus,
                    "Tol+": element.tol_plus,
                    "Values": element.values,
                    "Element_Type": element.element_type.value,
                }
            )

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data_for_export, f, indent=2)

    @staticmethod
    def get_default_sample_data() -> List[ElementData]:
        """Get default sample data for testing"""
        default_data = [
            ElementData(
                name="Diameter_1",
                nominal=12.5,
                tol_minus=-0.05,
                tol_plus=0.05,
                values=[
                    12.41,
                    12.46,
                    12.43,
                    12.47,
                    12.50,
                    12.49,
                    12.44,
                    12.46,
                    12.48,
                    12.48,
                ],
                element_type=ElementType.DIMENSIONAL,
            ),
            ElementData(
                name="Dimensio_Anomaly",
                nominal=30.0,
                tol_minus=-0.2,
                tol_plus=0.2,
                values=[
                    29.85,
                    29.87,
                    29.86,
                    30.15,
                    30.18,
                    30.17,
                    30.16,
                    29.84,
                    29.88,
                    30.19,
                ],
                #element_type=ElementType.DIMENSIONAL,
            ),
            ElementData(
                name="Dimensio_1",
                nominal=25.0,
                tol_minus=-0.25,
                tol_plus=0.25,
                values=[
                    25.021,
                    24.983,
                    25.015,
                    24.992,
                    25.027,
                    25.031,
                    24.986,
                    25.012,
                    24.979,
                    25.022,
                ],
                #element_type=ElementType.DIMENSIONAL,
            ),
            ElementData(
                name="Traccio_1",
                nominal=17500,
                tol_minus=0.0,
                tol_plus=1000.0,
                values=[
                    17550,
                    17600,
                    17480,
                    17520,
                    17590,
                    17495,
                    17505,
                    17610,
                    17570,
                    17585,
                ],
                element_type=ElementType.TRACTION,
            ),
        ]
        return default_data
