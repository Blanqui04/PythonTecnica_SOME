# src/models/plotting/mr_chart.py
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class MRChart(SPCChartBase):
    """Professional MR-Chart (Moving Range) with PPAP-compliant styling"""

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
        self._calculate_moving_ranges()
        self._calculate_control_limits()

    def _parse_element_data(self):
        self.sample_data = np.array(self.element_data.get("sample_data", []))
        if len(self.sample_data) < 2:
            raise ValueError("At least 2 data points required for Moving Range chart")

        self.element = self.element_data.get("element_name", self.element_name)
        self.moving_ranges = self.element_data.get("moving_ranges", None)
        self.mr_mean = self.element_data.get("mr_mean", None)
        self.mr_ucl = self.element_data.get("mr_ucl", None)
        self.mr_lcl = self.element_data.get("mr_lcl", None)

    def _calculate_moving_ranges(self):
        if self.moving_ranges is None:
            self.moving_ranges = np.abs(np.diff(self.sample_data))
        else:
            self.moving_ranges = np.array(self.moving_ranges)

        self.indices = np.arange(2, len(self.sample_data) + 1)

    def _calculate_control_limits(self):
        if self.mr_mean is None:
            self.mr_mean = np.mean(self.moving_ranges)

        if self.mr_ucl is None or self.mr_lcl is None:
            D4 = 3.267  # Upper control limit factor for n=2
            D3 = 0      # Lower control limit factor (always 0 for n=2)
            
            self.mr_ucl = D4 * self.mr_mean
            self.mr_lcl = D3 * self.mr_mean

    def _get_point_colors(self):
        colors = []
        for value in self.moving_ranges:
            if self.mr_lcl <= value <= self.mr_ucl:
                colors.append(self.COLOR_ACCENT_BLUE)
            else:
                colors.append(self.COLOR_DANGER_RED)
        return colors

    # mr_chart.py - Updated plot method
    def plot(self):
        try:
            fig, ax = self._create_figure()
            point_colors = self._get_point_colors()

            # Plot data
            ax.plot(self.indices, self.moving_ranges, color=self.COLOR_ACCENT_BLUE,
                linewidth=self.LINEWIDTH_DATA, zorder=3, alpha=0.8,
                label='Moving Range')
            ax.scatter(self.indices, self.moving_ranges, c=point_colors,
                    edgecolor=self.COLOR_DARK_GRAY, s=self.MARKERSIZE**2,
                    linewidth=self.MARKER_EDGEWIDTH, zorder=4)

            # Control limits
            ax.axhline(self.mr_ucl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'UCL = {self.mr_ucl:.4f}')
            ax.axhline(self.mr_mean, color=self.COLOR_PRIMARY_BLUE, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'MR̄ = {self.mr_mean:.4f}')
            ax.axhline(self.mr_lcl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'LCL = {self.mr_lcl:.4f}')

            # Title without subtitle
            title = f"MR-Chart: {self.element}"
            self._set_titles_and_labels(ax, title=title,
                                    xlabel="Sample Number",
                                    ylabel="Moving Range")

            ax.set_xticks(self.indices[::max(1, len(self.indices)//20)])
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)
            self._set_legend(ax, loc='upper right')
            
            plt.tight_layout()
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating MR-Chart: {e}", exc_info=True)
            raise