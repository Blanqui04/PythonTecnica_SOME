# src/models/plotting/x_chart.py - PROFESSIONAL PPAP AESTHETIC
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class XBarChart(SPCChartBase):
    """Professional X̄-Chart with PPAP-compliant styling"""

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
        self._calculate_subgroups()
        self._calculate_control_limits()

    def _parse_element_data(self):
        """Parse element data"""
        self.sample_data = np.array(self.element_data.get("sample_data", []))
        if len(self.sample_data) < self.subgroup_size:
            raise ValueError(f"Need at least {self.subgroup_size} data points")

        self.element = self.element_data.get("element_name", self.element_name)
        self.nominal = self.element_data.get("nominal", 0)
        self.tolerance = self.element_data.get("tolerance", [-1, 1])
        self.lsl = self.nominal + self.tolerance[0]
        self.usl = self.nominal + self.tolerance[1]

    def _calculate_subgroups(self):
        """Calculate subgroup averages"""
        n_subgroups = len(self.sample_data) // self.subgroup_size
        data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
        subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
        self.subgroup_means = np.mean(subgroups, axis=1)
        self.grand_mean = np.mean(self.subgroup_means)

    def _calculate_control_limits(self):
        """Calculate control limits using A2 constant"""
        A2_constants = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577,
                       6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
        A2 = A2_constants.get(self.subgroup_size, 0.577)
        
        n_subgroups = len(self.sample_data) // self.subgroup_size
        data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
        subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
        ranges = np.ptp(subgroups, axis=1)
        avg_range = np.mean(ranges)
        
        self.ucl = self.grand_mean + A2 * avg_range
        self.lcl = self.grand_mean - A2 * avg_range

    def _get_point_colors(self):
        """Determine point colors based on control limits"""
        colors = []
        for value in self.subgroup_means:
            if self.lcl <= value <= self.ucl:
                colors.append(self.COLOR_ACCENT_BLUE)
            else:
                colors.append(self.COLOR_DANGER_RED)
        return colors

    # x_chart.py - Updated plot method
    def plot(self):
        """Create professional X̄-Chart"""
        try:
            fig, ax = self._create_figure()
            indices = np.arange(1, len(self.subgroup_means) + 1)
            point_colors = self._get_point_colors()

            # Plot data line with professional styling
            ax.plot(indices, self.subgroup_means, color=self.COLOR_ACCENT_BLUE,
                linewidth=self.LINEWIDTH_DATA, zorder=3, alpha=0.8, 
                label=f'Subgroup Average (n={self.subgroup_size})')

            # Plot data points
            ax.scatter(indices, self.subgroup_means, c=point_colors,
                    edgecolor=self.COLOR_DARK_GRAY, s=self.MARKERSIZE**2,
                    linewidth=self.MARKER_EDGEWIDTH, zorder=4)

            # Control limits with professional styling
            ax.axhline(self.ucl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'UCL = {self.ucl:.4f}')
            ax.axhline(self.grand_mean, color=self.COLOR_PRIMARY_BLUE, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'X̄̄ = {self.grand_mean:.4f}')
            ax.axhline(self.lcl, color=self.COLOR_DANGER_RED, linestyle='-',
                    linewidth=self.LINEWIDTH_CONTROL, zorder=2,
                    label=f'LCL = {self.lcl:.4f}')

            # Specification limits (dashed)
            ax.axhline(self.usl, color=self.COLOR_WARNING_ORANGE, linestyle='--',
                    linewidth=self.LINEWIDTH_SPEC, alpha=0.7, zorder=1,
                    label=f'USL = {self.usl:.4f}')
            ax.axhline(self.lsl, color=self.COLOR_WARNING_ORANGE, linestyle='--',
                    linewidth=self.LINEWIDTH_SPEC, alpha=0.7, zorder=1,
                    label=f'LSL = {self.lsl:.4f}')

            # Title without subtitle
            title = f"X̄-Chart: {self.element}"
            self._set_titles_and_labels(ax, title=title,
                                    xlabel="Subgroup Number",
                                    ylabel="Subgroup Average")

            # Configure axes
            ax.set_xticks(indices[::max(1, len(indices)//20)])
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=self.LINEWIDTH_GRID)
            
            # Professional legend
            self._set_legend(ax, loc='upper right', ncol=1)
            
            plt.tight_layout()
            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating X̄-Chart: {e}", exc_info=True)
            raise