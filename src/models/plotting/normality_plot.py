# src/models/plotting/normality_plot.py - PROFESSIONAL PPAP AESTHETIC
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats
import seaborn as sns
from pathlib import Path
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class NormalityAnalysisChart(SPCChartBase):
    """Professional Normality Analysis Chart with PPAP-compliant styling"""

    def __init__(self, input_json_path, lang="ca", show=False, save_path=None,
                 element_name=None, **kwargs):
        logger = kwargs.pop("logger", base_logger.getChild(self.__class__.__name__))

        super().__init__(
            input_json_path=input_json_path, lang=lang, show=show,
            save_path=save_path, element_name=element_name,
            logger=logger, **kwargs
        )

        self.mostra = np.array(self.element_data.get("sample_data", []))
        self.nominal = self.element_data.get("nominal", 0)
        self.tol = self.element_data.get("tolerance", [-1, 1])
        self.element = self.element_data.get("element_name", self.element_name)
        self.std_short = self.element_data.get("std_short_term", None)
        self.pval_ad = self.element_data.get("pval_ad", None)
        self.ad = self.element_data.get("ad", None)
        self.ad_res = self.element_data.get("ad_result", None)

    def plot(self):
        try:
            mean = np.mean(self.mostra)
            std = np.std(self.mostra, ddof=1)
            lsl = self.nominal + self.tol[0]
            usl = self.nominal + self.tol[1]

            # Create figure with professional layout
            fig, axs = plt.subplots(1, 2, figsize=(12, 12 / self.GOLDEN_RATIO))
            fig.patch.set_facecolor(self.FIGURE_FACECOLOR)

            # Main title with professional styling
            fig.suptitle(f"Normality Analysis: {self.element}",
                        fontsize=self.FONT_SIZE_TITLE + 2,
                        fontweight='bold',
                        color=self.COLOR_PRIMARY_BLUE,
                        y=0.98)

            # Create plots
            self._plot_histogram_kde(axs[0], mean, std, lsl, usl)
            self._plot_qq(axs[1])

            plt.tight_layout(rect=[0, 0, 1, 0.95])
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating normality analysis: {e}", exc_info=True)
            raise

    def _plot_histogram_kde(self, ax, mean, std, lsl, usl):
        """Plot histogram with KDE and normal distributions"""
        
        # Set professional background
        ax.set_facecolor(self.AXES_FACECOLOR)
        
        # Calculate bins
        data_min = min(np.min(self.mostra), lsl)
        data_max = max(np.max(self.mostra), usl)
        x_range = data_max - data_min
        bin_width = x_range / 10 if x_range > 0 else 1
        num_bins = max(5, min(int(x_range / bin_width), 20))

        # Histogram with KDE using professional colors
        sns.histplot(
            self.mostra, kde=True, bins=num_bins,
            color=self.COLOR_ACCENT_BLUE, edgecolor=self.COLOR_DARK_GRAY,
            alpha=0.6, linewidth=0.8, ax=ax, stat='count'
        )

        # Format axes
        x_min, x_max = ax.get_xlim()
        x_range = abs(x_max - x_min)
        
        if x_range < 0.001:
            fmt = "{x:.4f}"
        elif x_range < 0.1:
            fmt = "{x:.3f}"
        elif x_range < 1:
            fmt = "{x:.2f}"
        else:
            fmt = "{x:.1f}"

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt.format(x=x)))

        # Get KDE line for scaling
        kde_line = None
        max_points = 0
        for line in ax.lines:
            ydata = line.get_ydata()
            if len(ydata) > max_points:
                kde_line = line
                max_points = len(ydata)
        kde_ymax = np.max(kde_line.get_ydata()) if kde_line else 1

        # Plot normal curves with professional styling
        curves = [
            (std, self.COLOR_DARK_GRAY, '-', 'Long-term Normal', 1.5),
            (self.std_short, self.COLOR_WARNING_ORANGE, '--', 'Short-term Normal', 1.2)
        ]
        
        for std_val, color, ls, label, lw in curves:
            if std_val is None:
                continue
            x_vals = np.linspace(mean - 3 * std_val, mean + 3 * std_val, 100)
            pdf = stats.norm.pdf(x_vals, loc=mean, scale=std_val)
            pdf_scaled = pdf * kde_ymax / np.max(pdf) if np.max(pdf) > 0 else pdf
            ax.plot(x_vals, pdf_scaled, color=color, linestyle=ls,
                   linewidth=lw, label=label, alpha=0.9)

        # Set x-limits
        normal_max = mean + 3 * std
        normal_min = mean - 3 * std
        x_min = min(min(self.mostra), normal_min, lsl)
        x_max = max(max(self.mostra), normal_max, usl)
        x_margin = 0.05 * (x_max - x_min)
        ax.set_xlim(x_min - x_margin, x_max + x_margin)

        # Vertical lines with professional styling
        ymax = ax.get_ylim()[1]
        
        line_specs = [
            (lsl, self.COLOR_DANGER_RED, f'LSL\n{lsl:.3f}', 1.2),
            (usl, self.COLOR_DANGER_RED, f'USL\n{usl:.3f}', 1.2),
            (self.nominal, self.COLOR_SUCCESS_GREEN, f'Target\n{self.nominal:.3f}', 1.2),
            (mean, self.COLOR_PRIMARY_BLUE, f'Mean\n{mean:.3f}', 1.0)
        ]
        
        for x_pos, color, label_text, lw in line_specs:
            ax.axvline(x_pos, color=color, linestyle='-' if 'Mean' not in label_text else '--',
                      linewidth=lw, alpha=0.8, zorder=3)
            ax.text(x_pos, ymax * 0.92, label_text,
                   color=color, fontsize=self.FONT_SIZE_ANNOTATION,
                   ha='center', va='top', weight='bold',
                   bbox=dict(facecolor='white', edgecolor=color,
                           boxstyle='round,pad=0.4', alpha=0.95, linewidth=0.8))

        # Labels and styling
        ax.set_title('Histogram & Kernel Density Estimate',
                    fontsize=self.FONT_SIZE_SUBTITLE,
                    fontweight='bold', color=self.COLOR_SECONDARY_BLUE, pad=10)
        ax.set_xlabel('Measured Value', fontsize=self.FONT_SIZE_LABEL,
                     color=self.COLOR_DARK_GRAY)
        ax.set_ylabel('Frequency', fontsize=self.FONT_SIZE_LABEL,
                     color=self.COLOR_DARK_GRAY)
        
        ax.legend(fontsize=self.FONT_SIZE_LEGEND, loc='upper left',
                 framealpha=0.95, edgecolor=self.COLOR_MEDIUM_GRAY)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)

    def _plot_qq(self, ax):
        """Plot Q-Q plot with professional styling"""
        
        ax.set_facecolor(self.AXES_FACECOLOR)
        
        # Create Q-Q plot
        stats.probplot(self.mostra, dist="norm", plot=ax)

        # Customize appearance with professional colors
        lines = ax.get_lines()
        if len(lines) >= 2:
            # Data points
            lines[0].set_markerfacecolor(self.COLOR_ACCENT_BLUE)
            lines[0].set_markeredgecolor(self.COLOR_DARK_GRAY)
            lines[0].set_markersize(self.MARKERSIZE)
            lines[0].set_markeredgewidth(self.MARKER_EDGEWIDTH)
            
            # Reference line
            lines[1].set_color(self.COLOR_DANGER_RED)
            lines[1].set_linewidth(self.LINEWIDTH_CONTROL)
            lines[1].set_label('Theoretical Normal')

        ax.set_title('Q-Q Plot (Quantile-Quantile)',
                    fontsize=self.FONT_SIZE_SUBTITLE,
                    fontweight='bold', color=self.COLOR_SECONDARY_BLUE, pad=10)
        ax.set_xlabel('Theoretical Quantiles', fontsize=self.FONT_SIZE_LABEL,
                     color=self.COLOR_DARK_GRAY)
        ax.set_ylabel('Sample Quantiles', fontsize=self.FONT_SIZE_LABEL,
                     color=self.COLOR_DARK_GRAY)
        
        ax.legend(fontsize=self.FONT_SIZE_LEGEND, loc='lower right',
                 framealpha=0.95, edgecolor=self.COLOR_MEDIUM_GRAY)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)