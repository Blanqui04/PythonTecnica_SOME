"""
Capability Analyzer - Main class for statistical analysis and capability studies
"""

import os
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import logging
from typing import Dict, List, Tuple, Optional, Union  # noqa: F401
from dataclasses import dataclass
from enum import Enum

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


class ElementType(Enum):
    """Element type classification"""

    DIMENSIONAL = "dimensional"
    GDT = "gdt"
    TRACTION = "traction"


@dataclass
class ElementData:
    """Data structure for element information"""

    name: str
    nominal: float
    tol_minus: float
    tol_plus: float
    values: List[float]
    element_type: ElementType = ElementType.DIMENSIONAL


@dataclass
class StatisticalResults:
    """Results from statistical analysis"""

    mean: float
    std_long: float
    std_short: float
    is_normal: bool
    ad_statistic: float
    p_value: float
    sample_size: int


@dataclass
class CapabilityResults:
    """Results from capability analysis"""

    cp: float
    cpk: float
    pp: float
    ppk: float
    ppm_short: float
    ppm_long: float


@dataclass
class ExtrapolationResults:
    """Results from extrapolation process"""

    extrapolated_values: List[float]
    ad_statistic: float
    p_value: float
    was_extrapolated: bool


class CapabilityAnalyzer:
    """
    Main class for capability analysis with statistical testing and extrapolation
    """

    def __init__(self, min_sample_size: int = 5):
        """
        Initialize the capability analyzer

        Args:
            min_sample_size: Minimum required sample size for analysis
        """
        self.min_sample_size = min_sample_size
        self.d2_constant = 1.128  # For moving range calculation
        logger.info(f"CapabilityAnalyzer initialized with min_sample_size={min_sample_size}")

    def detect_element_type(self, element_name: str) -> ElementType:
        """
        Detect element type based on name

        Args:
            element_name: Name of the element to classify

        Returns:
            ElementType: Classification of the element
        """
        logger.debug(f"Detecting element type for '{element_name}'")
        name = element_name.lower()

        gdt_keywords = [
            "flatness",
            "position",
            "parallelism",
            "perpendicularity",
            "cylindricity",
            "concentricity",
            "symmetry",
            "profile",
            "runout",
        ]
        traction_keywords = [
            "force",
            "traction",
            "compression",
            "hysteresi",
            "hysteresis",
            "f",
            "traccio",
        ]

        if any(kw in name for kw in gdt_keywords):
            element_type = ElementType.GDT
        elif any(kw in name for kw in traction_keywords):
            element_type = ElementType.TRACTION
        else:
            element_type = ElementType.DIMENSIONAL
        
        logger.debug(f"Detected element type: {element_type.value}")
        return element_type

    def validate_sample(self, values: List[float]) -> None:
        """
        Validate sample data

        Args:
            values: Sample values to validate

        Raises:
            SampleErrors: If sample is invalid
        """
        logger.debug(f"Validating sample with {len(values)} values")
        if len(values) < self.min_sample_size:
            logger.error(f"Sample size {len(values)} below minimum {self.min_sample_size}")
            raise SampleErrors(
                f"Sample size {len(values)} is below minimum required {self.min_sample_size}"
            )

        if not all(isinstance(v, (int, float)) for v in values):
            logger.error("Non-numeric values found in sample")
            raise SampleErrors("All sample values must be numeric")
        logger.debug("Sample validation passed")


    def analyze_sample(self, values: List[float]) -> StatisticalResults:
        """
        Perform statistical analysis on sample data

        Args:
            values: Sample values to analyze

        Returns:
            StatisticalResults: Statistical analysis results
        """
        logger.info("Starting statistical analysis of sample")
        self.validate_sample(values)

        sample = np.asarray(values)
        n = len(sample)

        # Calculate basic statistics
        mean = np.mean(sample)
        std_long = np.std(sample, ddof=1)

        # Short-term standard deviation from moving range
        moving_ranges = np.abs(np.diff(sample))
        mr_bar = np.mean(moving_ranges)
        std_short = mr_bar / self.d2_constant

        # Anderson-Darling test for normality
        ad_test = stats.anderson(sample, dist="norm")
        ad_statistic = ad_test.statistic

        try:
            ad_critical = ad_test.critical_values[
                list(ad_test.significance_level).index(5.0)
            ]
        except (AttributeError, ValueError):
            ad_critical = ad_test.critical_values[2]  # fallback

        is_normal = ad_statistic < ad_critical
        p_value = self._calculate_p_value_approximation(ad_statistic)

        logger.info(f"Statistical analysis completed: mean={mean:.4f}, std_long={std_long:.4f}, std_short={std_short:.4f}, is_normal={is_normal}")

        return StatisticalResults(
            mean=mean,
            std_long=std_long,
            std_short=std_short,
            is_normal=is_normal,
            ad_statistic=ad_statistic,
            p_value=p_value,
            sample_size=n,
        )

    def _calculate_p_value_approximation(self, ad_stat: float) -> float:
        """
        Calculate approximate p-value for Anderson-Darling test

        Args:
            ad_stat: Anderson-Darling statistic

        Returns:
            float: Approximate p-value
        """
        logger.debug(f"Calculating p-value approximation for AD stat: {ad_stat}")
        if ad_stat >= 0.6:
            p_val = np.exp(1.2937 - 5.709 * ad_stat + 0.0186 * ad_stat**2)
        elif 0.34 < ad_stat < 0.6:
            p_val = np.exp(0.9177 - 4.279 * ad_stat - 1.38 * ad_stat**2)
        elif 0.2 < ad_stat <= 0.34:
            p_val = 1 - np.exp(-8.318 + 42.796 * ad_stat - 59.938 * ad_stat**2)
        else:  # ad_stat <= 0.2
            p_val = 1 - np.exp(-13.436 + 101.14 * ad_stat - 223.73 * ad_stat**2)
        logger.debug(f"Approximated p-value: {p_val}")
        return p_val

    def calculate_anderson_darling_manual(
        self,
        sample: List[float],
        mean: Optional[float] = None,
        std: Optional[float] = None,
    ) -> Tuple[float, pd.DataFrame]:
        """
        Manual calculation of Anderson-Darling A² statistic

        Args:
            sample: Sample data
            mean: Mean of the sample (calculated if None)
            std: Standard deviation of the sample (calculated if None)

        Returns:
            Tuple[float, pd.DataFrame]: A² statistic and calculation details
        """
        logger.info("Calculating Anderson-Darling statistic manually")
        sample = np.asarray(sample)
        n = len(sample)

        if n < self.min_sample_size:
            logger.error(f"Sample too small for AD calculation: {n} < {self.min_sample_size}")
            raise SampleErrors(f"Sample too small: {n} < {self.min_sample_size}")

        sorted_sample = np.sort(sample)

        if mean is None:
            mean = np.mean(sample)
        if std is None:
            std = np.std(sample, ddof=1)

        # Calculate CDF values
        cdf_vals = stats.norm.cdf(sorted_sample, loc=mean, scale=std)
        cdf_vals = np.clip(cdf_vals, 1e-10, 1 - 1e-10)

        i = np.arange(1, n + 1)
        one_minus_cdf = 1 - cdf_vals
        one_minus_cdf_reverse = 1 - cdf_vals[::-1]

        s = (2 * i - 1) * (np.log(cdf_vals) + np.log(one_minus_cdf_reverse))
        A_2 = -n - np.sum(s) / n
        A2_corrected = A_2 * (1 + 0.75 / n + 2.25 / (n**2))

        # Create calculation DataFrame
        df = pd.DataFrame(
            {
                "i": i,
                "sorted": sorted_sample,
                "F(Xi)": cdf_vals,
                "1-F(Xi)": one_minus_cdf,
                "1-F(Xn-i+1)": one_minus_cdf_reverse,
                "S": s,
            }
        )

        logger.debug("Manual Anderson-Darling calculation complete")
        return A2_corrected, df

    def calculate_capability_indices(
        self, element_data: ElementData, stats_results: StatisticalResults
    ) -> CapabilityResults:
        """
        Calculate capability indices (CP, CPK, PP, PPK)

        Args:
            element_data: Element information
            stats_results: Statistical analysis results

        Returns:
            CapabilityResults: Capability indices and PPM values
        """
        logger.info(f"Calculating capability indices for element '{element_data.name}'")
        nominal = element_data.nominal
        tolerance = [element_data.tol_minus, element_data.tol_plus]
        mean = stats_results.mean
        std_short = stats_results.std_short
        std_long = stats_results.std_long
        element_type = element_data.element_type

        # Calculate indices for short-term (CP, CPK)
        cp, cpk = self._calculate_process_indices(
            element_type, nominal, mean, std_short, tolerance
        )

        # Calculate indices for long-term (PP, PPK)
        pp, ppk = self._calculate_process_indices(
            element_type, nominal, mean, std_long, tolerance
        )

        # Calculate PPM
        ppm_short = self._calculate_ppm(nominal, tolerance, mean, std_short)
        ppm_long = self._calculate_ppm(nominal, tolerance, mean, std_long)

        logger.info(f"Capability indices calculated: Cp={cp:.4f}, Cpk={cpk:.4f}, Pp={pp:.4f}, Ppk={ppk:.4f}, ppm_short={ppm_short:.0f}, ppm_long={ppm_long:.0f}")
        return CapabilityResults(cp=cp, cpk=cpk, pp=pp, ppk=ppk, ppm_short=ppm_short, ppm_long=ppm_long)

    def _calculate_process_indices(
        self,
        element_type: ElementType,
        nominal: float,
        mean: float,
        std: float,
        tolerance: List[float],
    ) -> Tuple[float, float]:
        """
        Calculate process capability indices

        Args:
            element_type: Type of element
            nominal: Nominal value
            mean: Sample mean
            std: Standard deviation
            tolerance: Tolerance limits [lower, upper]

        Returns:
            Tuple[float, float]: Process capability indices (P, Pk)
        """
        pk_inf = (mean - (nominal + tolerance[0])) / (3 * std)
        pk_sup = (nominal + tolerance[1] - mean) / (3 * std)
        p = (nominal + tolerance[1] - (nominal + tolerance[0])) / (6 * std)

        if element_type == ElementType.TRACTION:
            pk = pk_inf
        elif element_type == ElementType.GDT:
            pk = pk_sup
        else:  # DIMENSIONAL
            pk = min(pk_sup, pk_inf)

        logger.debug(f"Process indices: p={p}, pk={pk}")
        return p, pk

    def _calculate_ppm(
        self, nominal: float, tolerance: List[float], mean: float, std: float
    ) -> float:
        """
        Calculate parts per million (PPM) defect rate

        Args:
            nominal: Nominal value
            tolerance: Tolerance limits [lower, upper]
            mean: Sample mean
            std: Standard deviation

        Returns:
            float: PPM value
        """
        lsl = nominal + tolerance[0]
        usl = nominal + tolerance[1]

        z_lower = (lsl - mean) / std
        z_upper = (usl - mean) / std

        ppm_lower = stats.norm.cdf(z_lower) * 1e6
        ppm_upper = (1 - stats.norm.cdf(z_upper)) * 1e6

        logger.debug(f"Calculated ppm: {ppm_lower + ppm_upper}")
        return ppm_lower + ppm_upper

    def analyze_element(self, element_data: ElementData) -> Dict:
        """
        Perform complete capability analysis for a single element

        Args:
            element_data: Element data to analyze

        Returns:
            Dict: Complete analysis results
        """
        logger.info(f"Starting analysis for element: {element_data.name}")
        if not isinstance(element_data, ElementData):
            logger.error(f"Invalid type for element_data: expected ElementData, got {type(element_data)}")
            raise TypeError(f"Expected ElementData, got {type(element_data)}")
        # Perform statistical analysis
        stats_results = self.analyze_sample(element_data.values)
        logger.debug(f"Statistical results for {element_data.name}: mean={stats_results.mean}, std_short={stats_results.std_short}, std_long={stats_results.std_long}")

        # Calculate capability indices
        capability_results = self.calculate_capability_indices(element_data, stats_results)
        logger.debug(f"Capability indices for {element_data.name}: Cp={capability_results.cp}, Cpk={capability_results.cpk}, Pp={capability_results.pp}, Ppk={capability_results.ppk}")

        # Prepare results dictionary
        results = {
            "element_name": element_data.name,
            "nominal": element_data.nominal,
            "tolerance": [element_data.tol_minus, element_data.tol_plus],
            "original_values": element_data.values,
            "element_type": element_data.element_type.value,
            "statistics": {
                "mean": stats_results.mean,
                "std_short": stats_results.std_short,
                "std_long": stats_results.std_long,
                "is_normal": stats_results.is_normal,
                "ad_statistic": stats_results.ad_statistic,
                "p_value": stats_results.p_value,
                "sample_size": stats_results.sample_size,
            },
            "capability": {
                "cp": capability_results.cp,
                "cpk": capability_results.cpk,
                "pp": capability_results.pp,
                "ppk": capability_results.ppk,
                "ppm_short": capability_results.ppm_short,
                "ppm_long": capability_results.ppm_long,
            },
        }

        logger.info(f"Completed analysis for element: {element_data.name}")
        return results

    def analyze_multiple_elements(self, elements_data: List[ElementData]) -> List[Dict]:
        """
        Analyze multiple elements

        Args:
            elements_data: List of element data to analyze

        Returns:
            List[Dict]: List of analysis results
        """
        logger.info(f"Starting analysis of {len(elements_data)} elements")
        results = []

        for element_data in elements_data:
            try:
                result = self.analyze_element(element_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing element {element_data.name}: {e}", exc_info=True)
                error_result = {
                    "element_name": element_data.name,
                    "error": str(e),
                    "analysis_failed": True,
                }
                results.append(error_result)

        logger.info("Completed analysis of multiple elements")
        return results

    def export_results_to_csv(self, results: List[Dict], output_path: str) -> None:
        """
        Export analysis results to CSV

        Args:
            results: Analysis results
            output_path: Path to save CSV file
        """
        logger.info(f"Starting export of results to CSV at '{output_path}'")
        flattened_data = []

        for result in results:
            if "analysis_failed" in result:
                logger.warning(f"Skipping element '{result['element_name']}' due to analysis failure: {result['error']}")
                flattened_data.append(
                    {"Element": result["element_name"], "Error": result["error"]}
                )
                continue

            flattened_result = {
                "Element": result["element_name"],
                "Nominal": result["nominal"],
                "Tolerance": json.dumps(result["tolerance"]),
                "Original_Values": json.dumps(result["original_values"]),
                "Element_Type": result["element_type"],
                "Mean": result["statistics"]["mean"],
                "Std_Short": result["statistics"]["std_short"],
                "Std_Long": result["statistics"]["std_long"],
                "Is_Normal": result["statistics"]["is_normal"],
                "AD_Statistic": result["statistics"]["ad_statistic"],
                "P_Value": result["statistics"]["p_value"],
                "Sample_Size": result["statistics"]["sample_size"],
                "CP": result["capability"]["cp"],
                "CPK": result["capability"]["cpk"],
                "PP": result["capability"]["pp"],
                "PPK": result["capability"]["ppk"],
                "PPM_Short": result["capability"]["ppm_short"],
                "PPM_Long": result["capability"]["ppm_long"],
            }

            flattened_data.append(flattened_result)

        try:
            df = pd.DataFrame(flattened_data)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Successfully exported results to CSV at '{output_path}'")
        except Exception as e:
            logger.error(f"Failed to export results to CSV at '{output_path}': {e}", exc_info=True)
            raise
