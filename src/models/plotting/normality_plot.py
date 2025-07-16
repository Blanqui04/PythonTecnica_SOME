# src/statistics/plotting/normality_plot.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats
import seaborn as sns
from pathlib import Path

from base_chart import SPCChartBase


class NormalityAnalysisChart(SPCChartBase):
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None, 
                 element_name=None, **kwargs):
        super().__init__(input_json_path, lang, show, save_path, element_name=element_name, **kwargs)
        
        self.logger.info(f"Initializing NormalityAnalysisChart for element: {self.element_name}")
        
        try:
            # Extract specific data from the selected element
            self.mostra = np.array(self.element_data.get("sample_data", []))
            self.nominal = self.element_data.get("nominal", 0)
            self.tol = self.element_data.get("tolerance", [-1, 1])
            self.element = self.element_data.get("element_name", self.element_name)
            self.std_short = self.element_data.get("std_short_term", None)
            self.pval_ad = self.element_data.get("pval_ad", None)
            self.ad = self.element_data.get("ad", None)
            self.ad_res = self.element_data.get("ad_result", None)
            self.output_dir = Path(self.element_data.get("output_dir", "."))
            
            self.logger.info(f"Loaded {len(self.mostra)} sample points for element {self.element}")
            
            # Validate required data
            if len(self.mostra) == 0:
                raise ValueError(f"No sample data found for element {self.element_name}")
                
        except Exception as e:
            self.logger.error(f"Error initializing NormalityAnalysisChart: {e}", exc_info=True)
            raise

    def plot(self):
        self.logger.info(f"Creating normality analysis chart for {self.element}")
        
        try:
            # Add fallback translations
            fallback_translations = {
                "normality_analysis": "Anàlisi de normalitat - {element}",
                "mean": "Mitjana",
                "p_value": "p-valor", 
                "normality": "Normalitat",
                "yes": "Sí",
                "no": "No",
                "histogram_kde": "Histograma + KDE",
                "value": "Valor",
                "frequency": "Freqüència",
                "qq_plot": "Q-Q plot",
                "theoretical_quantiles": "Quantils teòrics",
                "sample_quantiles": "Quantils mostra",
                "long_term_norm": "Normal llarg termini",
                "short_term_norm": "Normal curt termini"
            }
            
            # Merge with loaded translations, fallback if key missing
            tr = {**fallback_translations, **self.labels}
            
            mean = np.mean(self.mostra)
            std = np.std(self.mostra, ddof=1)
            lsl = self.nominal + self.tol[0]
            usl = self.nominal + self.tol[1]
            
            self.logger.debug(f"Statistics - Mean: {mean:.4f}, Std: {std:.4f}, LSL: {lsl:.4f}, USL: {usl:.4f}")

            fig, axs = plt.subplots(1, 2, figsize=(12, 12 / self.GOLDEN_RATIO))
            fig.subplots_adjust(top=0.85)

            # Main title
            fig.suptitle(
                tr.get("normality_analysis", "Anàlisi de normalitat").format(element=self.element),
                fontsize=16,
                fontname=self.FONT_NAME,
                y=0.94,
            )

            # Subtitle with AD results if available
            subtitle = ""
            if self.pval_ad is not None and self.ad_res is not None:
                subtitle = (
                    f"{tr.get('mean', 'Mitjana')}: {mean:.4f}   "
                    f"AD: {self.ad:.4f}   "
                    f"{tr.get('p_value', 'p-valor')}: {self.pval_ad:.4f}   "
                    f"{tr.get('normality', 'Normalitat')}: {tr.get('yes', 'Sí') if self.ad_res else tr.get('no', 'No')}"
                )
                
            if subtitle:
                fig.text(
                    0.5, 0.87, subtitle,
                    ha="center", va="center",
                    fontsize=11, fontname=self.FONT_NAME,
                    color="#444444",
                )

            # Create plots
            self._plot_histogram_kde(axs[0], mean, std, lsl, usl, tr)
            self._plot_qq(axs[1], tr)

            plt.tight_layout(rect=[0, 0, 1, 0.90])
            
            self.logger.info("Normality analysis chart created successfully")
            self._finalize()
            
        except Exception as e:
            self.logger.error(f"Error creating normality analysis chart: {e}", exc_info=True)
            raise

    def _plot_histogram_kde(self, ax, mean, std, lsl, usl, tr):
        self.logger.debug("Creating histogram + KDE plot")
        
        ax.grid(True, linestyle="--", alpha=0.4, zorder=0)

        data_min = min(np.min(self.mostra), lsl)
        data_max = max(np.max(self.mostra), usl)
        x_range = data_max - data_min

        target_bins = 10
        bin_width = x_range / target_bins if x_range > 0 else 1
        num_bins = int(x_range / bin_width)
        num_bins = max(5, min(num_bins, 20))

        # Create histogram with KDE
        kde_kwargs = {"fill": True, "linewidth": 1, "alpha": 0.7}
        sns.histplot(
            self.mostra,
            kde=True,
            bins=num_bins,
            color=self.COLOR_BLAU,
            edgecolor=self.COLOR_NEGRE,
            ax=ax,
            **kde_kwargs,
        )

        # Format axis ticks
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
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))

        # Find KDE line for scaling normal curves
        kde_line = None
        max_points = 0
        for line in ax.lines:
            ydata = line.get_ydata()
            if len(ydata) > max_points:
                kde_line = line
                max_points = len(ydata)
        kde_ymax = np.max(kde_line.get_ydata()) if kde_line else 1

        # Normal curves: long term and short term
        for std_val, color, ls, label_key in [
            (std, self.COLOR_NEGRE, "-", "long_term_norm"),
            (self.std_short, self.COLOR_TARONJA, "--", "short_term_norm"),
        ]:
            if std_val is None:
                continue
            x_vals = np.linspace(mean - 3 * std_val, mean + 3 * std_val, 100)
            pdf = stats.norm.pdf(x_vals, loc=mean, scale=std_val)
            pdf_scaled = pdf * kde_ymax / np.max(pdf) if np.max(pdf) > 0 else pdf
            ax.plot(
                x_vals, pdf_scaled,
                color=color, linestyle=ls, linewidth=1.2,
                label=tr.get(label_key, label_key),
            )

        # Set appropriate x-axis limits
        normal_max = mean + 3 * std
        normal_min = mean - 3 * std
        
        x_min = min(min(self.mostra), normal_min, lsl)
        x_max = max(max(self.mostra), normal_max, usl)
        x_margin = 0.05 * (x_max - x_min)
        ax.set_xlim(x_min - x_margin, x_max + x_margin)

        # Vertical lines
        ymax = ax.get_ylim()[1]
        
        ax.axvline(lsl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.2, alpha=0.8)
        ax.axvline(usl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.2, alpha=0.8)
        ax.axvline(self.nominal, color=self.COLOR_VERD, linestyle="-", linewidth=1.2, alpha=0.8)
        ax.axvline(mean, color=self.COLOR_NEGRE, linestyle="--", linewidth=1.2, alpha=0.8)

        # Labels for vertical lines
        label_props = dict(fontsize=9, fontname=self.FONT_NAME, ha="center", va="bottom",
                          bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.2", alpha=0.8))
        
        ax.text(lsl, ymax * 0.94, f"LSL ({lsl:.3f})", color=self.COLOR_VERMELL, **label_props)
        ax.text(usl, ymax * 0.94, f"USL ({usl:.3f})", color=self.COLOR_VERMELL, **label_props)
        ax.text(self.nominal, ymax * 0.94, f"$x_{{0}}$ ({self.nominal:.3f})", color=self.COLOR_VERD, **label_props)

        ax.set_title(tr.get("histogram_kde", "Histograma + KDE"), fontsize=13, fontname=self.FONT_NAME)
        ax.set_xlabel(tr.get("value", "Valor"), fontsize=11, fontname=self.FONT_NAME)
        ax.set_ylabel(tr.get("frequency", "Freqüència"), fontsize=11, fontname=self.FONT_NAME)

        ax.legend(fontsize=9, prop={"family": self.FONT_NAME})

    def _plot_qq(self, ax, tr):
        self.logger.debug("Creating Q-Q plot")
        
        ax.grid(True, linestyle="--", alpha=0.4, zorder=0)
        stats.probplot(self.mostra, dist="norm", plot=ax)
        
        # Customize the plot appearance
        lines = ax.get_lines()
        if len(lines) >= 2:
            lines[0].set_markerfacecolor(self.COLOR_BLAU)
            lines[0].set_markeredgecolor(self.COLOR_NEGRE)
            lines[0].set_markersize(6)
            lines[1].set_color(self.COLOR_VERMELL)
            lines[1].set_linewidth(2)
        
        ax.set_title(tr.get("qq_plot", "Q-Q plot"), fontsize=13, fontname=self.FONT_NAME)
        ax.set_xlabel(tr.get("theoretical_quantiles", "Quantils teòrics"), fontsize=11, fontname=self.FONT_NAME)
        ax.set_ylabel(tr.get("sample_quantiles", "Quantils mostra"), fontsize=11, fontname=self.FONT_NAME)

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname(self.FONT_NAME)


if __name__ == "__main__":
    import json
    import tempfile
    import os

    # Test data
    test_data = {
        "TestElement": {
            "sample_data": [10.1, 10.3, 10.2, 10.4, 10.2, 10.5, 10.1, 10.3, 10.2, 10.4],
            "nominal": 10.0,
            "tolerance": [-0.5, 0.5],
            "element_name": "TestElement",
            "std_short_term": 0.1,
            "pval_ad": 0.15,
            "ad": 0.3,
            "ad_result": True,
            "output_dir": "data/charts"
        }
    }

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmpfile:
        json.dump(test_data, tmpfile)
        tmpfile_path = tmpfile.name

    try:
        chart = NormalityAnalysisChart(tmpfile_path, lang="ca", show=True, element_name="TestElement")
        chart.plot()
    finally:
        os.remove(tmpfile_path)