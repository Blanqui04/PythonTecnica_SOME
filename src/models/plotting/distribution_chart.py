# src/models/plotting/distribution_chart.py - PROFESSIONAL PPAP AESTHETIC
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Polygon
from pathlib import Path
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger
from typing import Dict, Any


class DistributionSPCChart(SPCChartBase):
    """Professional Distribution Chart with PPAP-compliant styling"""

    def __init__(self, input_json_path, lang="ca", show=False, save_path=None,
                 i18n_folder=None, extra_rcparams=None, logger=None,
                 element_name=None, bins=30):
        self.bins = bins
        super().__init__(
            input_json_path=input_json_path, lang=lang, show=show,
            save_path=save_path, i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger or base_logger.getChild(self.__class__.__name__),
            element_name=element_name,
        )

    def _validate_data(self):
        """Validate data availability"""
        has_extrapolated = ("extrapolated_values" in self.element_data and 
                           len(self.element_data.get("extrapolated_values", [])) > 0)
        has_original = ("original_values" in self.element_data and 
                       len(self.element_data.get("original_values", [])) >= 5)
        
        if not (has_extrapolated or has_original):
            raise ValueError("Need either extrapolated or ≥5 original values")

        required_fields = ["nominal", "tolerance", "mean", "std_long"]
        missing = [f for f in required_fields if f not in self.element_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

    def _extract_data(self) -> Dict[str, Any]:
        """Extract data for plotting"""
        if ("extrapolated_values" in self.element_data and 
            len(self.element_data.get("extrapolated_values", [])) > 0):
            values = self.element_data["extrapolated_values"]
            data_type = "extrapolated"
        else:
            values = self.element_data.get("original_values", [])
            data_type = "original"

        data = {
            "values": np.array(values),
            "nominal": float(self.element_data["nominal"]),
            "tolerance": self.element_data["tolerance"],
            "mean": float(self.element_data["mean"]),
            "std_long": float(self.element_data["std_long"]),
            "data_type": data_type,
        }

        data["lsl"] = data["nominal"] + data["tolerance"][0]
        data["usl"] = data["nominal"] + data["tolerance"][1]
        data["pp"] = self.element_data.get("pp")
        data["ppk"] = self.element_data.get("ppk")

        return data

    def plot(self):
        """Create professional distribution chart"""
        try:
            self._validate_data()
            data = self._extract_data()

            fig, ax = self._create_figure(figsize=(10, 10 / self.GOLDEN_RATIO))
            
            # Create normal distribution
            x_min = data["mean"] - 4 * data["std_long"]
            x_max = data["mean"] + 4 * data["std_long"]
            x = np.linspace(x_min, x_max, 300)
            pdf = stats.norm.pdf(x, data["mean"], data["std_long"])

            # Scale PDF to histogram
            bin_width = (max(data["values"]) - min(data["values"])) / self.bins
            normal_scaled = pdf * len(data["values"]) * bin_width

            # Plot histogram with professional styling
            sns.histplot(
                data["values"], bins=self.bins, kde=False, stat="count",
                alpha=0.6, color=self.COLOR_ACCENT_BLUE,
                edgecolor=self.COLOR_DARK_GRAY, linewidth=0.8,
                ax=ax, label='Measured Distribution'
            )

            # Plot normal curve
            ax.plot(x, normal_scaled, color=self.COLOR_PRIMARY_BLUE,
                   linewidth=self.LINEWIDTH_CONTROL, alpha=0.9,
                   label=f'Normal: μ={data["mean"]:.4f}, σ={data["std_long"]:.4f}')

            # Shade rejection zones with professional colors
            ax.fill_between(x, 0, normal_scaled,
                           where=(x < data["lsl"]) | (x > data["usl"]),
                           color=self.COLOR_DANGER_RED, alpha=0.15,
                           label='Rejection Zones')

            # Vertical lines for limits
            ymax = ax.get_ylim()[1]
            
            limit_specs = [
                (data["lsl"], self.COLOR_DANGER_RED, f'LSL\n{data["lsl"]:.3f}', '-', 1.2),
                (data["usl"], self.COLOR_DANGER_RED, f'USL\n{data["usl"]:.3f}', '-', 1.2),
                (data["nominal"], self.COLOR_SUCCESS_GREEN, f'Target\n{data["nominal"]:.3f}', ':', 1.2),
                (data["mean"], self.COLOR_PRIMARY_BLUE, f'Mean\n{data["mean"]:.3f}', '--', 1.0)
            ]
            
            for x_pos, color, label_text, ls, lw in limit_specs:
                ax.axvline(x_pos, color=color, linestyle=ls,
                          linewidth=lw, alpha=0.8, zorder=3)
                ax.text(x_pos, ymax * 0.92, label_text,
                       color=color, fontsize=self.FONT_SIZE_ANNOTATION,
                       ha='center', va='top', weight='bold',
                       bbox=dict(facecolor='white', edgecolor=color,
                               boxstyle='round,pad=0.4', alpha=0.95, linewidth=0.8))

            # Set axis limits
            x_min_val = min(min(data["values"]), data["lsl"], x_min)
            x_max_val = max(max(data["values"]), data["usl"], x_max)
            x_margin = 0.02 * (x_max_val - x_min_val)
            ax.set_xlim(x_min_val - x_margin, x_max_val + x_margin)

            # Format axes
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.3f}"))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}"))

            # Title and labels without subtitle
            title = f"Distribution Analysis: {self.element_name}"
            
            self._set_titles_and_labels(ax, title=title,
                                       xlabel="Measured Value",
                                       ylabel="Frequency")

            # Professional legend
            self._set_legend(ax, loc='upper left', ncol=1)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)

            plt.tight_layout()
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating distribution chart: {e}", exc_info=True)
            raise