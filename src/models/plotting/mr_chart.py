# src/statistics/plotting/mr_chart.py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from base_chart import SPCChartBase

# Traduccions mínimes per a MR chart
translations = {
    "ca": {
        "ucl_label": "Lím. Sup. Control = {ucl:.2f}",
        "cl_label": "Mitjana = {cl:.2f}",
        "lcl_label": "Lím. Inf. Control = {lcl:.2f}",
        "moving_range_chart": "Diagrama MR per a {element}",
        "estimated_sigma": "Sigma estimat = {sigma:.3f}",
        "index_piece": "Índex de peça",
        "mobile_range": "Rang mòbil"
    },
    "en": {
        "ucl_label": "Upper Control Limit = {ucl:.2f}",
        "cl_label": "Center Line = {cl:.2f}",
        "lcl_label": "Lower Control Limit = {lcl:.2f}",
        "moving_range_chart": "Moving Range Chart for {element}",
        "estimated_sigma": "Estimated Sigma = {sigma:.3f}",
        "index_piece": "Piece Index",
        "mobile_range": "Moving Range"
    }
}


class MRChart(SPCChartBase):
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None):
        super().__init__(input_json_path, lang, show, save_path)
        self.mostra = np.array(self.data.get("sample_data", []))
        self.element = self.data.get("element_name", "Element")
        self.output_dir = Path(self.data.get("output_dir", "."))

    def plot(self):
        tr = translations.get(self.lang, translations["ca"])

        if len(self.mostra) < 2:
            raise ValueError("At least two data points required for Moving Range chart")

        mr = np.abs(np.diff(self.mostra))
        indices = np.arange(2, len(self.mostra) + 1)  # MR defined from second observation

        MR_bar = np.mean(mr)
        d2 = 1.128
        sigma_est = MR_bar / d2
        D_4 = 3.267
        D_3 = 0

        UCL = D_4 * MR_bar
        LCL = D_3 * MR_bar  # always 0

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.grid(True, linestyle=":", alpha=0.4, zorder=0)

        ax.plot(indices, mr, marker='o', color=self.COLOR_BLAU, linewidth=1, zorder=3)
        ax.scatter(indices, mr, color=self.COLOR_BLAU, edgecolor=self.COLOR_NEGRE, s=60, zorder=4)

        ax.axhline(UCL, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.75, zorder=2, label=tr['ucl_label'].format(ucl=UCL))
        ax.axhline(MR_bar, color=self.COLOR_NEGRE, linestyle="-", linewidth=0.75, zorder=2, label=tr['cl_label'].format(cl=MR_bar))
        ax.axhline(LCL, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.75, zorder=2, label=tr['lcl_label'].format(lcl=LCL))

        ax.set_title(tr['moving_range_chart'].format(element=self.element),
                     fontsize=15, fontname="Times New Roman", pad=30)

        subtitle = tr['estimated_sigma'].format(sigma=sigma_est)
        if subtitle:
            ax.text(
                0.5, 1.03, subtitle,
                fontsize=11,
                fontname="Times New Roman",
                color="#444444",
                ha='center',
                va='bottom',
                transform=ax.transAxes
            )

        ax.set_xlabel(tr['index_piece'], fontsize=12, fontname="Times New Roman")
        ax.set_ylabel(tr['mobile_range'], fontsize=12, fontname="Times New Roman")
        ax.set_xticks(indices)
        ax.set_xticklabels(indices, fontname="Times New Roman")
        ax.tick_params(axis='y', labelsize=10)
        for label in ax.get_yticklabels():
            label.set_fontname("Times New Roman")

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        ax.legend(
            fontsize=7,
            prop={"family": "Times New Roman"},
            loc="upper right",
            frameon=True,
            framealpha=0.95,
            borderpad=0.3,
            labelspacing=0.2,
            handlelength=0.7,
            handletextpad=0.3,
            markerscale=0.7
        )

        if self.save_path:
            filename = self.save_path
        else:
            filename = self.output_dir / f"4 - {self.element} - Diagrama_MR - {self.lang}.png"

        plt.savefig(filename, format="png", dpi=300, bbox_inches="tight")

        if self.show:
            plt.show()

        plt.close()


# --- TEST senzill per provar la classe sense fitxer extern ---

if __name__ == "__main__":
    import json
    import tempfile

    # Dades fictícies per provar
    test_data = {
        "sample_data": [9.5, 10.1, 9.8, 10.2, 9.7, 10.3, 9.6],
        "element_name": "Test Element",
        "output_dir": tempfile.gettempdir()
    }

    # Escriure temporalment json per simular entrada
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmpfile:
        json.dump(test_data, tmpfile)
        tmpfile.flush()

        # Crear i executar gràfic
        chart = MRChart(tmpfile.name, lang="ca", show=True)
        chart.plot()

    print("Gràfic MRChart creat i mostrat amb èxit.")
