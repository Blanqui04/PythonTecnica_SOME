# src/models/capability/extrapolation_manager.py
"""
Extrapolation Manager - Handles data extrapolation for normality improvement
"""

import numpy as np
import scipy.stats as stats
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .capability_analyzer import ExtrapolationResults
from ...exceptions.sample_errors import SampleErrors

from .logging_config import logger # Configured logger for calculations

@dataclass
class ExtrapolationConfig:
    """Configuration for extrapolation process"""

    target_p_value: float = 0.05
    max_attempts: int = 100
    available_sizes: List[int] = None

    def __post_init__(self):
        if self.available_sizes is None:
            self.available_sizes = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150]


class ExtrapolationManager:
    """
    Manages data extrapolation to improve normality of samples
    """

    def __init__(self, config: Optional[ExtrapolationConfig] = None):
        """
        Initialize extrapolation manager

        Args:
            config: Configuration for extrapolation process
        """
        self.config = config or ExtrapolationConfig()
        logger.debug(f"ExtrapolationManager initialized with config: {self.config}")

    def _calculate_p_value_approximation(self, ad_stat: float) -> float:
        """
        Calculate approximate p-value for Anderson-Darling test

        Args:
            ad_stat: Anderson-Darling statistic

        Returns:
            float: Approximate p-value
        """
        if ad_stat >= 0.6:
            return np.exp(1.2937 - 5.709 * ad_stat + 0.0186 * ad_stat**2)
        elif 0.34 < ad_stat < 0.6:
            return np.exp(0.9177 - 4.279 * ad_stat - 1.38 * ad_stat**2)
        elif 0.2 < ad_stat <= 0.34:
            return 1 - np.exp(-8.318 + 42.796 * ad_stat - 59.938 * ad_stat**2)
        else:  # ad_stat <= 0.2
            return 1 - np.exp(-13.436 + 101.14 * ad_stat - 223.73 * ad_stat**2)

    def _calculate_anderson_darling_manual(
        self, sample: np.ndarray, mean: float, std: float
    ) -> float:
        """
        Manual calculation of Anderson-Darling A² statistic

        Args:
            sample: Sample data
            mean: Mean of the sample
            std: Standard deviation of the sample

        Returns:
            float: A² statistic
        """
        n = len(sample)
        sorted_sample = np.sort(sample)

        # Calculate CDF values
        cdf_vals = stats.norm.cdf(sorted_sample, loc=mean, scale=std)
        cdf_vals = np.clip(cdf_vals, 1e-10, 1 - 1e-10)

        i = np.arange(1, n + 1)
        one_minus_cdf_reverse = 1 - cdf_vals[::-1]

        s = (2 * i - 1) * (np.log(cdf_vals) + np.log(one_minus_cdf_reverse))
        A_2 = -n - np.sum(s) / n
        A2_corrected = A_2 * (1 + 0.75 / n + 2.25 / (n**2))

        return A2_corrected

    def get_extrapolation_choice(self) -> Tuple[bool, Optional[int]]:
        """
        Get user choice for extrapolation (interactive mode)

        Returns:
            Tuple[bool, Optional[int]]: (extrapolate, target_size)
        """
        try:
            extrap_choice = input("Do you want to extrapolate? (y/n): ").strip().lower()
            extrapolate = extrap_choice in ["y", "yes", "s", "sí", "si"]

            if not extrapolate:
                return False, None

            print("Select the number of values to extrapolate:")
            for idx, val in enumerate(self.config.available_sizes):
                print(f"{idx + 1}. {val}")

            while True:
                try:
                    sel = int(input(f"Option (1-{len(self.config.available_sizes)}): "))
                    if 1 <= sel <= len(self.config.available_sizes):
                        return True, self.config.available_sizes[sel - 1]
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

        except KeyboardInterrupt:
            logger.warning("Extrapolation input interrupted by user.")
            return False, None

    def extrapolate_sample(
        self,
        original_sample: List[float],
        nominal: float,
        tol_minus: float,
        target_size: Optional[int] = None,
        interactive: bool = True,
    ) -> ExtrapolationResults:
        """
        Extrapolate sample data to improve normality

        Args:
            original_sample: Original sample data
            nominal: Nominal value
            tol_minus: Lower tolerance (used to detect if negatives should be avoided)
            target_size: Target sample size (if None, will prompt user)
            interactive: Whether to use interactive mode

        Returns:
            ExtrapolationResults: Results of extrapolation
        """
        original_sample = np.array(original_sample)
        n_orig = len(original_sample)
        mu = np.mean(original_sample)
        std = np.std(original_sample, ddof=1)

        # Check if we should avoid negative values
        avoid_negatives = nominal == 0 and tol_minus == 0

        logger.debug(f"Starting extrapolation for sample with n={n_orig}, mu={mu:.4f}, std={std:.4f}")

        if std == 0:
            logger.error("Standard deviation is zero, cannot extrapolate.")
            raise SampleErrors("Standard deviation is zero, cannot extrapolate")

        # Get extrapolation choice
        if interactive:
            extrapolate, target_size = self.get_extrapolation_choice()
        else:
            extrapolate = target_size is not None

        if not extrapolate or target_size is None:
            logger.info("No extrapolation selected or target size not provided.")
            return ExtrapolationResults(
                extrapolated_values=[],
                ad_statistic=0.0,
                p_value=0.0,
                was_extrapolated=False,
            )

        if target_size <= n_orig:
            logger.warning("Target size is not larger than original sample. No extrapolation performed.")
            return ExtrapolationResults(
                extrapolated_values=original_sample.tolist(),
                ad_statistic=0.0,
                p_value=0.0,
                was_extrapolated=False,
            )

        logger.info(f"Attempting extrapolation to {target_size} values...")
        # Perform extrapolation attempts
        attempt = 0
        best_sample = None
        best_p_value = 0.0
        best_ad_stat = float("inf")

        print(f"Starting extrapolation to {target_size} values...")

        while attempt < self.config.max_attempts:
            # Generate additional values
            n_extra = target_size - n_orig

            if avoid_negatives:
                # Generate positive values only
                new_vals = np.abs(np.random.normal(mu, std, n_extra))
            else:
                new_vals = np.random.normal(mu, std, n_extra)

            # Combine with original sample
            extended_sample = np.concatenate([original_sample, new_vals])

            # Calculate Anderson-Darling statistics
            ad_stat = self._calculate_anderson_darling_manual(extended_sample, mu, std)
            p_value = self._calculate_p_value_approximation(ad_stat)

            logger.debug(f"Attempt {attempt + 1}: A² = {ad_stat:.4f}, p ≈ {p_value:.4f}")

            # Keep track of best result
            if p_value > best_p_value:
                best_sample = extended_sample.copy()
                best_p_value = p_value
                best_ad_stat = ad_stat

            # Check if we achieved target p-value
            if p_value >= self.config.target_p_value:
                print(
                    f"Success! Sample is probably normal (p = {p_value:.4f} >= {self.config.target_p_value})"
                )
                return ExtrapolationResults(
                    extrapolated_values=extended_sample.tolist(),
                    ad_statistic=ad_stat,
                    p_value=p_value,
                    was_extrapolated=True,
                )

            attempt += 1

        # If we couldn't achieve target p-value, return best attempt
        logger.warning(f"Failed to reach target p >= {self.config.target_p_value} after {self.config.max_attempts} attempts.")
        logger.info(f"Best result: A² = {best_ad_stat:.4f}, p ≈ {best_p_value:.4f}")

        return ExtrapolationResults(
            extrapolated_values=best_sample.tolist()
            if best_sample is not None
            else original_sample.tolist(),
            ad_statistic=best_ad_stat,
            p_value=best_p_value,
            was_extrapolated=True,
        )

    def extrapolate_multiple_samples(
        self, samples_data: List[dict], interactive: bool = True
    ) -> List[ExtrapolationResults]:
        """
        Extrapolate multiple samples

        Args:
            samples_data: List of sample data dictionaries
            interactive: Whether to use interactive mode

        Returns:
            List[ExtrapolationResults]: Results for each sample
        """
        results = []

        for sample_data in samples_data:
            element = sample_data.get("element_name", "Unknown")
            logger.info(f"Processing element: {element}")
            try:
                print(f"\nProcessing element: {sample_data['element_name']}")

                result = self.extrapolate_sample(
                    original_sample=sample_data["values"],
                    nominal=sample_data["nominal"],
                    tol_minus=sample_data["tol_minus"],
                    interactive=interactive,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error extrapolating {element}: {e}")
                results.append(
                    ExtrapolationResults(
                        extrapolated_values=[],
                        ad_statistic=0.0,
                        p_value=0.0,
                        was_extrapolated=False,
                    )
                )

        return results

    def batch_extrapolate(
        self, samples_data: List[dict], target_size: int
    ) -> List[ExtrapolationResults]:
        """
        Batch extrapolate multiple samples with same target size

        Args:
            samples_data: List of sample data dictionaries
            target_size: Target sample size for all samples

        Returns:
            List[ExtrapolationResults]: Results for each sample
        """
        results = []

        for sample_data in samples_data:
            element = sample_data.get("element_name", "Unknown")
            logger.info(f"Processing element: {element}")
            try:
                print(f"Processing element: {sample_data['element_name']}")

                result = self.extrapolate_sample(
                    original_sample=sample_data["values"],
                    nominal=sample_data["nominal"],
                    tol_minus=sample_data["tol_minus"],
                    target_size=target_size,
                    interactive=False,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error extrapolating {element}: {e}")
                results.append(
                    ExtrapolationResults(
                        extrapolated_values=[],
                        ad_statistic=0.0,
                        p_value=0.0,
                        was_extrapolated=False,
                    )
                )

        return results
