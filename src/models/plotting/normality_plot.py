# src/statistics/plotting/normality_plot.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats
import seaborn as sns
from pathlib import Path

from base_chart import SPCChartBase
from spc_data_loader import SPCDataLoader


class NormalityAnalysisChart(SPCChartBase):
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None):
        super().__init__(input_json_path, lang, show, save_path)
        # Extreure dades específiques del JSON
        self.mostra = np.array(self.data.get("sample_data", []))
        self.nominal = self.data.get("nominal", 0)
        self.tol = self.data.get("tolerance", [-1, 1])
        self.element = self.data.get("element_name", "Element")
        self.std_short = self.data.get("std_short_term", None)
        self.pval_ad = self.data.get("pval_ad", None)
        self.ad = self.data.get("ad", None)
        self.ad_res = self.data.get("ad_result", None)
        self.output_dir = Path(self.data.get("output_dir", "."))

    def plot(self):
        tr = self.labels
        mean = np.mean(self.mostra)
        std = np.std(self.mostra, ddof=1)
        lsl = self.nominal + self.tol[0]
        usl = self.nominal + self.tol[1]

        fig, axs = plt.subplots(1, 2, figsize=(10, 10 / self.GOLDEN_RATIO))
        fig.subplots_adjust(top=0.70)

        # Títol principal
        fig.suptitle(
            tr.get("normality_analysis", "Anàlisi de normalitat").format(
                element=self.element
            ),
            fontsize=16,
            fontname=self.FONT_NAME,
            y=0.94,
        )

        # Subtítol amb resultats AD si disponibles
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
                0.5,
                0.87,
                subtitle,
                ha="center",
                va="center",
                fontsize=11,
                fontname=self.FONT_NAME,
                color="#444444",
            )

        # --- Histograma + KDE ---
        self._plot_histogram_kde(axs[0], mean, std, lsl, usl, tr)

        # --- Q-Q plot ---
        self._plot_qq(axs[1], tr)

        plt.tight_layout(rect=[0, 0, 1, 0.90])

        self._finalize()

    def _plot_histogram_kde(self, ax, mean, std, lsl, usl, tr):
        ax.grid(True, linestyle="--", alpha=0.4, zorder=0)

        data_min = min(np.min(self.mostra), lsl)
        data_max = max(np.max(self.mostra), usl)
        x_range = data_max - data_min

        target_bins = 10
        bin_width = x_range / target_bins if x_range > 0 else 1
        num_bins = int(x_range / bin_width)
        num_bins = max(5, min(num_bins, 20))

        kde_kwargs = {"fill": True, "linewidth": 1}
        sns.histplot(
            self.mostra,
            kde=True,
            bins=num_bins,
            color=self.COLOR_BLAU,
            edgecolor=self.COLOR_NEGRE,
            ax=ax,
            **kde_kwargs,
        )

        x_min, x_max = ax.get_xlim()
        x_range = abs(x_max - x_min)

        # Format ticks
        if x_range < 0.001:
            fmt = "{x:.4f}"
        elif x_range < 0.1:
            fmt = "{x:.3f}"
        elif x_range < 0.11:
            fmt = "{x:.2f}"
        elif x_range < 1:
            fmt = "{x:.1f}"
        else:
            fmt = "{x:.0f}"
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt.format(x=x)))
        ax.tick_params(axis="x", labelsize=9, rotation=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))
        ax.tick_params(axis="y", labelsize=9, rotation=0)

        for label in ax.get_xticklabels():
            label.set_fontname(self.FONT_NAME)
        for label in ax.get_yticklabels():
            label.set_fontname(self.FONT_NAME)

        # Trobar línia KDE per escalar les corbes normals
        kde_line = None
        max_points = 0
        for line in ax.lines:
            ydata = line.get_ydata()
            if len(ydata) > max_points:
                kde_line = line
                max_points = len(ydata)
        kde_ymax = np.max(kde_line.get_ydata()) if kde_line else 1

        # Corbes normals: llarg termini i curt termini
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
                x_vals,
                pdf_scaled,
                color=color,
                linestyle=ls,
                linewidth=0.8,
                label=tr.get(label_key, label_key),
            )

        normal_max = mean + 3 * std
        normal_min = mean - 3 * std

        # Decide show USL
        show_usl = True
        if (abs(usl - normal_max) - abs(normal_max)) > 1 * abs(normal_max):
            x_min = min(min(self.mostra), normal_min, lsl)
            x_max = normal_max
            show_usl = False
        else:
            x_min = min(min(self.mostra), normal_min, lsl)
            x_max = max(max(self.mostra), normal_max, usl)
            show_usl = True

        x_margin = 0.02 * (x_max - x_min)
        ax.set_xlim(x_min - x_margin, x_max + x_margin)

        # Línies verticals
        ax.axvline(lsl, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.8)
        if show_usl:
            ax.axvline(usl, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.8)
        ax.axvline(self.nominal, color=self.COLOR_VERD, linestyle="-", linewidth=0.8)
        ax.axvline(mean, color=self.COLOR_NEGRE, linestyle="--", linewidth=0.8)

        ymax = ax.get_ylim()[1]
        ax.text(
            lsl,
            ymax * 0.94,
            f"LSL ({lsl:.2f})",
            color=self.COLOR_VERMELL,
            fontsize=9,
            fontname=self.FONT_NAME,
            ha="center",
            va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"),
        )
        if show_usl:
            ax.text(
                usl,
                ymax * 0.94,
                f"USL ({usl:.2f})",
                color=self.COLOR_VERMELL,
                fontsize=9,
                fontname=self.FONT_NAME,
                ha="center",
                va="bottom",
                bbox=dict(
                    facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"
                ),
            )
        ax.text(
            self.nominal,
            ymax * 0.94,
            f"$x_{{0}}$ ({self.nominal:.3f})",
            color=self.COLOR_VERD,
            fontsize=9,
            fontname=self.FONT_NAME,
            ha="center",
            va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"),
        )

        ax.set_title(
            tr.get("histogram_kde", "Histograma + KDE"),
            fontsize=13,
            fontname=self.FONT_NAME,
        )
        ax.set_xlabel(tr.get("value", "Valor"), fontsize=11, fontname=self.FONT_NAME)
        ax.set_ylabel(
            tr.get("frequency", "Freqüència"), fontsize=11, fontname=self.FONT_NAME
        )

        ax.legend(fontsize=8, prop={"family": self.FONT_NAME}, markerscale=0.7)

    def _plot_qq(self, ax, tr):
        ax.grid(True, linestyle="--", alpha=0.4, zorder=0)
        stats.probplot(self.mostra, dist="norm", plot=ax)
        ax.set_title(
            tr.get("qq_plot", "Q-Q plot"), fontsize=13, fontname=self.FONT_NAME
        )
        ax.set_xlabel(
            tr.get("theoretical_quantiles", "Quantils teòrics"),
            fontsize=11,
            fontname=self.FONT_NAME,
        )
        ax.set_ylabel(
            tr.get("sample_quantiles", "Quantils mostra"),
            fontsize=11,
            fontname=self.FONT_NAME,
        )

        for label in ax.get_xticklabels():
            label.set_fontname(self.FONT_NAME)
        for label in ax.get_yticklabels():
            label.set_fontname(self.FONT_NAME)

if __name__ == "__main__":
    import json
    import tempfile
    import os

    # Dades mínimes de prova
    test_data = {
        "sample_data": [10.1, 10.3, 10.2, 10.4, 10.2, 10.5],
        "nominal": 10.0,
        "tolerance": [-0.5, 0.5],
        "element_name": "TestElement",
        "std_short_term": 0.1,
        "pval_ad": 0.15,
        "ad": 0.3,
        "ad_result": True,
        "output_dir": "."
    }

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmpfile:
        json.dump(test_data, tmpfile)
        tmpfile_path = tmpfile.name

    try:
        chart = NormalityAnalysisChart(tmpfile_path, lang="ca", show=True)
        chart.plot()
    finally:
        os.remove(tmpfile_path)
