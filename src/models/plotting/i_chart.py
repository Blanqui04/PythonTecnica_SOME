# src/models/plotting/i_chart.py
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class IChart(SPCChartBase):
    """Professional I-Chart (Individuals) with PPAP-compliant styling"""

    def __init__(self, input_json_path, lang="ca", show=False, save_path=None,
                 i18n_folder=None, extra_rcparams=None, logger=None, element_name=None):
        super().__init__(
            input_json_path=input_json_path, lang=lang, show=show,
            save_path=save_path, i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger or base_logger.getChild(self.__class__.__name__),
            element_name=element_name,
        )
        self._parse_element_data()
        self._calculate_control_limits()

    def _parse_element_data(self):
        self.sample_data = np.array(self.element_data.get("sample_data", []))
        if len(self.sample_data) == 0:
            raise ValueError("sample_data is required and cannot be empty")

        self.nominal = self.element_data.get("nominal", 0)
        self.tolerance = self.element_data.get("tolerance", [-1, 1])
        self.element = self.element_data.get("element_name", self.element_name)
        
        self.mean = self.element_data.get("mean", None)
        self.moving_range = self.element_data.get("moving_range", None)
        self.ucl = self.element_data.get("ucl", None)
        self.lcl = self.element_data.get("lcl", None)
        
        self.lsl = self.nominal + self.tolerance[0]
        self.usl = self.nominal + self.tolerance[1]

    def _calculate_control_limits(self):
        if self.mean is None:
            self.mean = np.mean(self.sample_data)

        if self.moving_range is None:
            if len(self.sample_data) < 2:
                raise ValueError("Need at least 2 data points to calculate moving range")
            moving_ranges = np.abs(np.diff(self.sample_data))
            self.moving_range = np.mean(moving_ranges)

        if self.ucl is None or self.lcl is None:
            A2 = 2.659  # Constant for individual measurements
            self.ucl = self.mean + A2 * self.moving_range
            self.lcl = self.mean - A2 * self.moving_range

    def _get_point_colors(self):
        colors = []
        for value in self.sample_data:
            if self.lcl <= value <= self.ucl:
                colors.append(self.COLOR_ACCENT_BLUE)
            else:
                colors.append(self.COLOR_DANGER_RED)
        return colors

    # i_chart.py - Updated plot method
    def plot(self):
        try:
            fig, ax = self._create_figure()
            indices = np.arange(1, len(self.sample_data) + 1)
            point_colors = self._get_point_colors()

            # Plot data
            ax.plot(indices, self.sample_data, color=self.COLOR_ACCENT_BLUE,
                linewidth=self.LINEWIDTH_DATA, zorder=3, alpha=0.8,
                label='Individual Values')
            ax.scatter(indices, self.sample_data, c=point_colors,
                    edgecolor=self.COLOR_DARK_GRAY, s=self.MARKERSIZE**2,
                    linewidth=self.MARKER_EDGEWIDTH, zorder=4)

            # Control limits
            ax.axhline(self.ucl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'UCL = {self.ucl:.4f}')
            ax.axhline(self.mean, color=self.COLOR_PRIMARY_BLUE, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'X̄ = {self.mean:.4f}')
            ax.axhline(self.lcl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'LCL = {self.lcl:.4f}')

            # Specification limits
            ax.axhline(self.usl, color=self.COLOR_WARNING_ORANGE, linestyle='--',
                    linewidth=self.LINEWIDTH_SPEC, alpha=0.7, zorder=1,
                    label=f'USL = {self.usl:.4f}')
            ax.axhline(self.lsl, color=self.COLOR_WARNING_ORANGE, linestyle='--',
                    linewidth=self.LINEWIDTH_SPEC, alpha=0.7, zorder=1,
                    label=f'LSL = {self.lsl:.4f}')

            # Nominal value
            ax.axhline(self.nominal, color=self.COLOR_SUCCESS_GREEN, linestyle=':',
                    linewidth=self.LINEWIDTH_SPEC, alpha=0.8, zorder=1,
                    label=f'Nominal = {self.nominal:.4f}')

            # Title without subtitle
            title = f"I-Chart: {self.element}"
            self._set_titles_and_labels(ax, title=title,
                                    xlabel="Sample Number",
                                    ylabel="Individual Value")

            ax.set_xticks(indices[::max(1, len(indices)//20)])
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)
            self._set_legend(ax, loc='best', ncol=2)
            
            plt.tight_layout()
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating I-Chart: {e}", exc_info=True)
            raise