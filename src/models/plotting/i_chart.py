# src/statistics/plotting/i_chart.py

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from base_chart import SPCChartBase


# Dummy translations per provar sense fitxer extern
translations = {
    "ca": {
        "ucl_label": "Lím. Sup. Control = {ucl:.2f}",
        "cl_label": "Mitjana = {cl:.2f}",
        "lcl_label": "Lím. Inf. Control = {lcl:.2f}",
        "individual_chart": "Diagrama I per a {element}",
        "process capability": "Capacitat del procés",
        "index_piece": "Índex de peça",
        "value_measured": "Valor mesurat"
    },
    "en": {
        "ucl_label": "Upper Control Limit = {ucl:.2f}",
        "cl_label": "Center Line = {cl:.2f}",
        "lcl_label": "Lower Control Limit = {lcl:.2f}",
        "individual_chart": "Individual Chart for {element}",
        "process capability": "Process Capability",
        "index_piece": "Piece Index",
        "value_measured": "Measured Value"
    }
}


class IChart(SPCChartBase):
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None):
        super().__init__(input_json_path, lang, show, save_path)
        self.mostra = np.array(self.data.get("sample_data", []))
        self.nominal = self.data.get("nominal", 0)
        self.tol = self.data.get("tolerance", [-1, 1])
        self.mu = self.data.get("mean", None)
        self.mr = self.data.get("moving_range", None)
        self.element = self.data.get("element_name", "Element")
        self.cp = self.data.get("cp", None)
        self.cpk = self.data.get("cpk", None)
        self.output_dir = Path(self.data.get("output_dir", "."))

    def plot(self):
        tr = translations.get(self.lang, translations["ca"])
        indices = np.arange(1, len(self.mostra) + 1)
        LSL = self.nominal + self.tol[0]
        USL = self.nominal + self.tol[1]
        D4 = 2.659816
        if self.mu is None or self.mr is None:
            raise ValueError("Mean (mu) and Moving Range (mr) must be provided for I-Chart")

        UCL = self.mu + D4 * self.mr
        LCL = self.mu - D4 * self.mr

        point_colors = [self.COLOR_BLAU if (LSL <= v <= USL) else self.COLOR_VERMELL for v in self.mostra]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.grid(True, linestyle=":", alpha=0.4, zorder=0)

        ax.plot(indices, self.mostra, color=self.COLOR_BLAU, linewidth=1, zorder=3)
        ax.scatter(indices, self.mostra, color=point_colors, edgecolor=self.COLOR_NEGRE, s=60, zorder=4)

        ax.axhline(UCL, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.8, zorder=2, label=tr['ucl_label'].format(ucl=UCL))
        ax.axhline(self.mu, color=self.COLOR_NEGRE, linestyle="-", linewidth=0.8, zorder=2, label=tr['cl_label'].format(cl=self.mu))
        ax.axhline(LCL, color=self.COLOR_VERMELL, linestyle="-", linewidth=0.8, zorder=2, label=tr['lcl_label'].format(lcl=LCL))

        ax.set_title(tr['individual_chart'].format(element=self.element), fontsize=15, fontname="Times New Roman", pad=30)

        subtitle = ""
        if self.cp is not None and self.cpk is not None:
            subtitle = f"{tr['process capability']}: Cp = {self.cp:.2f}, Cpk = {self.cpk:.2f}"
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
        ax.set_ylabel(tr['value_measured'], fontsize=12, fontname="Times New Roman")
        ax.set_xticks(indices)
        ax.set_xticklabels(indices, fontname="Times New Roman")
        ax.tick_params(axis='y', labelsize=10)
        for label in ax.get_yticklabels():
            label.set_fontname("Times New Roman")

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        ax.legend(
            fontsize=6,
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
            filename = self.output_dir / f"3 - {self.element} - Diagrama_I - {self.lang}.png"

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
        "sample_data": [9.4, 10.1, 9.8, 10.2, 9.7, 10.3, 9.6],
        "nominal": 10,
        "tolerance": [-0.5, 0.5],
        "mean": 9.9,
        "moving_range": 0.25,
        "element_name": "Test Element",
        "cp": 1.33,
        "cpk": 1.2,
        "output_dir": tempfile.gettempdir()
    }

    # Escriure temporalment json per simular entrada
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmpfile:
        json.dump(test_data, tmpfile)
        tmpfile.flush()

        # Crear i executar gràfic
        chart = IChart(tmpfile.name, lang="ca", show=True)
        chart.plot()

    print("Gràfic IChart creat i mostrat amb èxit.")
