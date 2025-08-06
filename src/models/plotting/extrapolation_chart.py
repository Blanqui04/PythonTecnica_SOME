# src/models/plotting/extrapolation_chart.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from matplotlib.ticker import FuncFormatter
from pathlib import Path
from .logging_config import logger as base_logger
from typing import Dict, Any

from .base_chart import SPCChartBase


class ExtrapolatedSPCChart(SPCChartBase):
    """
    Extrapolated SPC Chart implementation based on SPCChartBase.

    This chart displays the distribution of measured values with extrapolated normal curve,
    showing control limits, nominal values, and statistical indicators.
    """

    COLOR_VERMELL_CLAR = "#FFE6E6"  # Light red for rejection zones

    def __init__(
        self,
        input_json_path: str | Path,
        lang: str = "ca",
        show: bool = False,
        save_path: str | Path = None,
        i18n_folder: str | Path = None,
        extra_rcparams: dict = None,
        logger=None,
        element_name: str = None,
        bins: int = 30,
    ):
        """
        Initialize the ExtrapolatedSPCChart.

        Args:
            input_json_path: Path to JSON file containing SPC data
            lang: Language code for translations
            show: Whether to display the chart
            save_path: Path to save the chart
            i18n_folder: Path to i18n folder
            extra_rcparams: Additional matplotlib rcParams
            logger: Logger instance
            element_name: Name of the element to plot
            bins: Number of bins for histogram
        """
        self.bins = bins
        super().__init__(
            input_json_path=input_json_path,
            lang=lang,
            show=show,
            save_path=save_path,
            i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger or base_logger.getChild(self.__class__.__name__),
            element_name=element_name,
        )

        self.logger.info(
            f"ExtrapolatedSPCChart initialized for element: {self.element_name}"
        )

    def _validate_data(self) -> None:
        """Validate that the element data contains required fields for extrapolated chart."""
        self.logger.debug("Validating element data for extrapolated chart")

        required_fields = [
            "nominal",
            "tolerance", 
            "mean",
            "std_long",
        ]
        
        # Check for either extrapolated_values OR original_values (for real data > 10)
        has_extrapolated = "extrapolated_values" in self.element_data and \
                        isinstance(self.element_data["extrapolated_values"], list) and \
                        len(self.element_data["extrapolated_values"]) > 0
                        
        has_real_values = "original_values" in self.element_data and \
                        isinstance(self.element_data["original_values"], list) and \
                        len(self.element_data["original_values"]) > 10
        
        if not (has_extrapolated or has_real_values):
            error_msg = (
                "Element must have either 'extrapolated_values' or 'original_values' with > 10 samples "
                "for extrapolation chart"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        missing_fields = [
            field for field in required_fields if field not in self.element_data
        ]

        if missing_fields:
            error_msg = f"Missing required fields in element data: {missing_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate data types and values
        if (
            not isinstance(self.element_data["tolerance"], list)
            or len(self.element_data["tolerance"]) != 2
        ):
            error_msg = "Field 'tolerance' must be a list with exactly 2 tolerance values [lower, upper]"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        for field in ["nominal", "mean", "std_long"]:
            if not isinstance(self.element_data[field], (int, float)):
                error_msg = f"Field '{field}' must be a numeric value"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

        if self.element_data["std_long"] <= 0:
            error_msg = "Standard deviation must be positive"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("Element data validation passed")

    def _extract_data(self) -> Dict[str, Any]:
        """Extract and prepare data for plotting."""
        self.logger.debug("Extracting data for extrapolated chart")

        # Determine which values to use - extrapolated or real values > 10
        values_to_use = []
        data_type = "unknown"
        
        if "extrapolated_values" in self.element_data and \
        isinstance(self.element_data["extrapolated_values"], list) and \
        len(self.element_data["extrapolated_values"]) > 0:
            values_to_use = self.element_data["extrapolated_values"]
            data_type = "extrapolated"
            self.logger.info(f"Using extrapolated values: {len(values_to_use)} samples")
        elif "original_values" in self.element_data and \
            isinstance(self.element_data["original_values"], list) and \
            len(self.element_data["original_values"]) > 10:
            values_to_use = self.element_data["original_values"]
            data_type = "real"
            self.logger.info(f"Using real values: {len(values_to_use)} samples")
        else:
            raise ValueError("No suitable data found for extrapolation chart")

        data = {
            "extrapolated_values": np.array(values_to_use),
            "nominal": float(self.element_data["nominal"]),
            "tolerance": self.element_data["tolerance"], 
            "mean": float(self.element_data["mean"]),
            "std_long": float(self.element_data["std_long"]),
            "data_type": data_type,  # Track what type of data we're using
        }

        # Calculate control limits
        data["lsl"] = (
            data["nominal"] + data["tolerance"][0]
        )  # Lower Specification Limit
        data["usl"] = (
            data["nominal"] + data["tolerance"][1]
        )  # Upper Specification Limit

        # Optional statistical indicators - handle both extrapolated and real data
        if data_type == "extrapolated":
            data["pp"] = self.element_data.get("extrapolated_pp") or self.element_data.get("pp")
            data["ppk"] = self.element_data.get("extrapolated_ppk") or self.element_data.get("ppk") 
            data["pval"] = self.element_data.get("extrapolated_p_value") or self.element_data.get("pval")
            data["is_normal"] = (data["pval"] > 0.05) if data["pval"] is not None else None
        else:  # real data
            data["pp"] = self.element_data.get("pp")
            data["ppk"] = self.element_data.get("ppk")
            data["pval"] = self.element_data.get("p_value") or self.element_data.get("pval")
            data["is_normal"] = (data["pval"] > 0.05) if data["pval"] is not None else None

        self.logger.info(
            f"Data extracted ({data_type}): {len(data['extrapolated_values'])} measurements, "
            f"nominal={data['nominal']:.4f}, mean={data['mean']:.4f}, "
            f"std={data['std_long']:.4f}, LSL={data['lsl']:.4f}, USL={data['usl']:.4f}"
        )

        return data

    def _create_normal_curve(self, data: Dict[str, Any]) -> tuple:
        """Create normal distribution curve data."""
        self.logger.debug("Creating normal distribution curve")

        # Generate x values for normal curve (±3 sigma range)
        x_min = data["mean"] - 3 * data["std_long"]
        x_max = data["mean"] + 3 * data["std_long"]
        x = np.linspace(x_min, x_max, 200)

        # Calculate probability density
        p = stats.norm.pdf(x, data["mean"], data["std_long"])

        # Scale to match histogram frequency
        bin_width = (
            max(data["extrapolated_values"]) - min(data["extrapolated_values"])
        ) / self.bins
        normal_scaled = p * len(data["extrapolated_values"]) * bin_width

        self.logger.debug(
            f"Normal curve created: x range [{x_min:.4f}, {x_max:.4f}], "
            f"max density: {max(normal_scaled):.4f}"
        )

        return x, normal_scaled

    def _plot_histogram_and_kde(self, ax, data: Dict[str, Any]) -> None:
        """Plot histogram and KDE."""
        self.logger.debug("Plotting histogram and KDE")

        histogram_label = self.labels.get("histogram_kde", "Histogram and KDE")

        sns.histplot(
            data["extrapolated_values"],
            bins=self.bins,
            kde=True,
            stat="count",
            alpha=0.6,
            color=self.COLOR_BLAU,
            edgecolor="k",
            label=histogram_label,
            ax=ax,
        )

        self.logger.debug(f"Histogram plotted with {self.bins} bins")

    def _plot_normal_curve(
        self, ax, x: np.ndarray, normal_scaled: np.ndarray, data: Dict[str, Any]
    ) -> None:
        """Plot the normal distribution curve."""
        self.logger.debug("Plotting normal distribution curve")

        curve_label = (
            f"$\\bar{{x}}$ = {data['mean']:.4f}, $\\sigma$ = {data['std_long']:.4f}"
        )

        ax.plot(
            x, normal_scaled, color=self.COLOR_NEGRE, linewidth=1, label=curve_label
        )

        self.logger.debug("Normal curve plotted")

    def _plot_control_limits(self, ax, data: Dict[str, Any]) -> None:
        """Plot control limits and nominal value."""
        self.logger.debug("Plotting control limits and nominal value")

        ymax = ax.get_ylim()[1]

        # LSL (Lower Specification Limit)
        if data["lsl"] != data["nominal"]:
            ax.axvline(
                data["lsl"], color=self.COLOR_VERMELL, linestyle="-", linewidth=0.75
            )
            ax.text(
                data["lsl"],
                ymax * 0.94,
                f"LSL ({data['lsl']:.2f})",
                color=self.COLOR_VERMELL,
                fontsize=9,
                fontname=self.FONT_NAME,
                ha="center",
                va="bottom",
                bbox=dict(
                    facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"
                ),
            )
            self.logger.debug(f"LSL plotted at {data['lsl']:.4f}")

        # Nominal value
        ax.axvline(
            data["nominal"], color=self.COLOR_VERD, linestyle="-", linewidth=0.75
        )
        ax.text(
            data["nominal"],
            ymax * 0.95,
            f"$x_{{0}}$ ({data['nominal']:.2f})",
            color=self.COLOR_VERD,
            fontsize=9,
            fontname=self.FONT_NAME,
            ha="center",
            va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"),
        )
        self.logger.debug(f"Nominal value plotted at {data['nominal']:.4f}")

        # Mean value (mu)
        ax.axvline(data["mean"], color=self.COLOR_NEGRE, linestyle="--", linewidth=0.75)
        self.logger.debug(f"Mean value plotted at {data['mean']:.4f}")

        # USL (Upper Specification Limit)
        if data["usl"] != data["nominal"]:
            ax.axvline(
                data["usl"], color=self.COLOR_VERMELL, linestyle="-", linewidth=0.75
            )
            ax.text(
                data["usl"],
                ymax * 0.95,
                f"USL ({data['usl']:.2f})",
                color=self.COLOR_VERMELL,
                fontsize=9,
                fontname=self.FONT_NAME,
                ha="center",
                va="bottom",
                bbox=dict(
                    facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"
                ),
            )
            self.logger.debug(f"USL plotted at {data['usl']:.4f}")

    def _plot_rejection_zones(
        self, ax, x: np.ndarray, normal_scaled: np.ndarray, data: Dict[str, Any]
    ) -> None:
        """Plot shaded rejection zones."""
        self.logger.debug("Plotting rejection zones")

        # Shade areas outside specification limits
        ax.fill_between(
            x,
            0,
            normal_scaled,
            where=(x < data["lsl"]) | (x > data["usl"]),
            color=self.COLOR_VERMELL_CLAR,
            alpha=0.4,
        )

        self.logger.debug("Rejection zones plotted")

    def _set_axis_limits(self, ax, x: np.ndarray, data: Dict[str, Any]) -> None:
        """Set appropriate axis limits."""
        self.logger.debug("Setting axis limits")

        x_min_val = min(
            min(data["extrapolated_values"]), min(x), data["lsl"], data["nominal"]
        )
        x_max_val = max(
            max(data["extrapolated_values"]), max(x), data["usl"], data["nominal"]
        )
        x_margin = 0.02 * (x_max_val - x_min_val)

        ax.set_xlim(x_min_val - x_margin, x_max_val + x_margin)

        self.logger.debug(
            f"X-axis limits set: [{x_min_val - x_margin:.4f}, {x_max_val + x_margin:.4f}]"
        )

    def _format_axes(self, ax) -> None:
        """Format axis ticks and labels."""
        self.logger.debug("Formatting axes")

        # Format tick labels
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))
        ax.tick_params(axis="x", labelsize=10)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))
        ax.tick_params(axis="y", labelsize=10)

        # Set font for tick labels
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname(self.FONT_NAME)

        self.logger.debug("Axis formatting completed")

    def _create_subtitle(self, data: Dict[str, Any]) -> str:
        """Create subtitle with statistical indicators and data type."""
        self.logger.debug("Creating subtitle with statistical indicators")

        subtitle_parts = []
        
        # Add data type indicator
        data_type = data.get("data_type", "unknown")
        if data_type == "extrapolated":
            data_type_text = self.labels.get("subtitle_extrapolated", "Extrapolated Data")
        elif data_type == "real":
            data_type_text = self.labels.get("subtitle_real", f"Real Data (n={len(data['extrapolated_values'])})")
        else:
            data_type_text = "Unknown Data Type"
        
        subtitle_parts.append(data_type_text)

        # Pp and Ppk values
        if data["pp"] is not None and data["ppk"] is not None:
            pp_ppk_text = self.labels.get(
                "subtitle_pp_ppk", "Pp = {pp:.2f}, Ppk = {ppk:.2f}"
            )
            subtitle_parts.append(pp_ppk_text.format(pp=data["pp"], ppk=data["ppk"]))

        # P-value
        if data["pval"] is not None:
            pval_text = self.labels.get("subtitle_pval", "p-value = {pval:.4f}")
            subtitle_parts.append(pval_text.format(pval=data["pval"]))

        # Normality test result
        if data["is_normal"] is not None:
            yes_text = self.labels.get("yes", "Yes")
            no_text = self.labels.get("no", "No")
            normal_text = self.labels.get("subtitle_normal", "Normal: {normal}")
            subtitle_parts.append(
                normal_text.format(normal=yes_text if data["is_normal"] else no_text)
            )

        subtitle = "   ".join(subtitle_parts)
        self.logger.debug(f"Subtitle created: {subtitle}")

        return subtitle

    def plot(self) -> None:
        """Create the extrapolated SPC chart."""
        self.logger.info("Starting extrapolated SPC chart creation")

        try:
            # Validate data
            self._validate_data()

            # Extract data
            data = self._extract_data()

            # Create figure
            fig, ax = self._create_figure(figsize=(10, 10 / self.GOLDEN_RATIO))

            # Create normal distribution curve
            x, normal_scaled = self._create_normal_curve(data)

            # Plot histogram and KDE
            self._plot_histogram_and_kde(ax, data)

            # Plot normal curve
            self._plot_normal_curve(ax, x, normal_scaled, data)

            # Plot control limits
            self._plot_control_limits(ax, data)

            # Plot rejection zones
            self._plot_rejection_zones(ax, x, normal_scaled, data)

            # Set axis limits
            self._set_axis_limits(ax, x, data)

            # Format axes
            self._format_axes(ax)

            # Set labels and title
            xlabel = self.labels.get("distribution_xlabel", "Measured Values")
            ylabel = self.labels.get("distribution_ylabel", "Frequency")
            title = self.labels.get(
                "distribution_title", "Measurement Distribution - {element}"
            ).format(element=self.element_name)

            self._set_titles_and_labels(ax, title=title, xlabel=xlabel, ylabel=ylabel)

            # Add subtitle with statistical indicators
            subtitle = self._create_subtitle(data)
            if subtitle.strip():
                ax.text(
                    0.5,
                    1.01,
                    subtitle.strip(),
                    fontsize=11,
                    fontname=self.FONT_NAME,
                    color="#444444",
                    ha="center",
                    va="bottom",
                    transform=ax.transAxes,
                )

            # Set legend
            self._set_legend(ax)

            # Apply tight layout
            plt.tight_layout()

            self.logger.info("Extrapolated SPC chart created successfully")

        except Exception as e:
            self.logger.error(
                f"Error creating extrapolated SPC chart: {e}", exc_info=True
            )
            raise
        finally:
            # Finalize (save/show/close)
            self._finalize()
