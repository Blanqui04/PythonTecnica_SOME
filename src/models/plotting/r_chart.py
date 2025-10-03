# src/models/plotting/r_chart.py
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class RChart(SPCChartBase):
    """Professional R-Chart (Range) with PPAP-compliant styling"""

    def __init__(self, input_json_path, lang="ca", show=False, save_path=None,
                 i18n_folder=None, extra_rcparams=None, logger=None,
                 element_name=None, subgroup_size=5):
        self.subgroup_size = subgroup_size
        super().__init__(
            input_json_path=input_json_path, lang=lang, show=show,
            save_path=save_path, i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger or base_logger.getChild(self.__class__.__name__),
            element_name=element_name,
        )
        self._parse_element_data()
        self._calculate_ranges()
        self._calculate_control_limits()

    def _parse_element_data(self):
        self.sample_data = np.array(self.element_data.get("sample_data", []))
        if len(self.sample_data) < self.subgroup_size:
            raise ValueError(f"Need at least {self.subgroup_size} data points")
        self.element = self.element_data.get("element_name", self.element_name)

    def _calculate_ranges(self):
        n_subgroups = len(self.sample_data) // self.subgroup_size
        data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
        subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
        self.ranges = np.ptp(subgroups, axis=1)
        self.avg_range = np.mean(self.ranges)

    def _calculate_control_limits(self):
        D3_constants = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
        D4_constants = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114, 6: 2.004,
                       7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
        
        D3 = D3_constants.get(self.subgroup_size, 0)
        D4 = D4_constants.get(self.subgroup_size, 2.114)
        
        self.ucl = D4 * self.avg_range
        self.lcl = D3 * self.avg_range

    def _get_point_colors(self):
        colors = []
        for value in self.ranges:
            if self.lcl <= value <= self.ucl:
                colors.append(self.COLOR_ACCENT_BLUE)
            else:
                colors.append(self.COLOR_DANGER_RED)
        return colors

    # r_chart.py - Updated plot method
    def plot(self):
        try:
            fig, ax = self._create_figure()
            indices = np.arange(1, len(self.ranges) + 1)
            point_colors = self._get_point_colors()

            # Plot data
            ax.plot(indices, self.ranges, color=self.COLOR_ACCENT_BLUE,
                linewidth=self.LINEWIDTH_DATA, zorder=3, alpha=0.8, 
                label=f'Subgroup Range (n={self.subgroup_size})')
            ax.scatter(indices, self.ranges, c=point_colors,
                    edgecolor=self.COLOR_DARK_GRAY, s=self.MARKERSIZE**2,
                    linewidth=self.MARKER_EDGEWIDTH, zorder=4)

            # Control limits
            ax.axhline(self.ucl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'UCL = {self.ucl:.4f}')
            ax.axhline(self.avg_range, color=self.COLOR_PRIMARY_BLUE, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'R̄ = {self.avg_range:.4f}')
            ax.axhline(self.lcl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'LCL = {self.lcl:.4f}')

            # Title without subtitle
            title = f"R-Chart: {self.element}"
            self._set_titles_and_labels(ax, title=title,
                                    xlabel="Subgroup Number", ylabel="Range")

            ax.set_xticks(indices[::max(1, len(indices)//20)])
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)
            self._set_legend(ax, loc='upper right')
            
            plt.tight_layout()
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating R-Chart: {e}", exc_info=True)
        raise