# src/models/plotting/x_chart.py
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class XBarChart(SPCChartBase):
    """
    X-bar Chart (Average Chart) for Statistical Process Control.
    Used for monitoring process mean with subgrouped data.
    """

    def __init__(
        self,
        input_json_path,
        lang="ca",
        show=False,
        save_path=None,
        i18n_folder=None,
        extra_rcparams=None,
        logger=None,
        element_name=None,
        subgroup_size=5,
    ):
        """Initialize X-bar Chart"""
        self.subgroup_size = subgroup_size
        super().__init__(
            input_json_path=input_json_path,
            lang=lang,
            show=show,
            save_path=save_path,
            i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger or base_logger.getChild(self.__class__.__name__),
            element_name=element_name,
        )

        self._parse_element_data()
        self._calculate_subgroups()
        self._calculate_control_limits()

        self.logger.info(f"XBarChart initialized for element: {self.element}")

    def _parse_element_data(self):
        """Parse element data"""
        try:
            self.sample_data = np.array(self.element_data.get("sample_data", []))
            if len(self.sample_data) < self.subgroup_size:
                raise ValueError(f"Need at least {self.subgroup_size} data points")

            self.element = self.element_data.get("element_name", self.element_name)
            self.nominal = self.element_data.get("nominal", 0)
            self.tolerance = self.element_data.get("tolerance", [-1, 1])

            self.lsl = self.nominal + self.tolerance[0]
            self.usl = self.nominal + self.tolerance[1]

            self.logger.debug(f"Parsed data: n={len(self.sample_data)}, subgroup_size={self.subgroup_size}")

        except Exception as e:
            self.logger.error(f"Error parsing element data: {e}")
            raise

    def _calculate_subgroups(self):
        """Calculate subgroup averages"""
        try:
            # Calculate number of complete subgroups
            n_subgroups = len(self.sample_data) // self.subgroup_size
            
            # Truncate data to complete subgroups
            data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
            
            # Reshape into subgroups and calculate means
            subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
            self.subgroup_means = np.mean(subgroups, axis=1)
            
            # Calculate grand mean
            self.grand_mean = np.mean(self.subgroup_means)
            
            self.logger.debug(f"Calculated {n_subgroups} subgroups, grand mean: {self.grand_mean:.4f}")

        except Exception as e:
            self.logger.error(f"Error calculating subgroups: {e}")
            raise

    def _calculate_control_limits(self):
        """Calculate control limits using A2 constant"""
        try:
            # A2 constants for different subgroup sizes
            A2_constants = {
                2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577,
                6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308
            }
            
            A2 = A2_constants.get(self.subgroup_size, 0.577)  # Default to n=5
            
            # Calculate average range
            n_subgroups = len(self.sample_data) // self.subgroup_size
            data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
            subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
            ranges = np.ptp(subgroups, axis=1)  # Range for each subgroup
            avg_range = np.mean(ranges)
            
            self.ucl = self.grand_mean + A2 * avg_range
            self.lcl = self.grand_mean - A2 * avg_range
            
            self.logger.debug(f"Control limits: UCL={self.ucl:.4f}, CL={self.grand_mean:.4f}, LCL={self.lcl:.4f}")

        except Exception as e:
            self.logger.error(f"Error calculating control limits: {e}")
            raise

    def _get_point_colors(self):
        """Determine point colors based on control limits"""
        colors = []
        for value in self.subgroup_means:
            if self.lcl <= value <= self.ucl:
                colors.append(self.COLOR_BLAU)
            else:
                colors.append(self.COLOR_VERMELL)
        return colors

    def plot(self):
        """Create X-bar chart"""
        try:
            self.logger.info(f"Creating X-bar Chart for element: {self.element}")

            fig, ax = self._create_figure()

            indices = np.arange(1, len(self.subgroup_means) + 1)
            point_colors = self._get_point_colors()

            # Plot data
            ax.plot(indices, self.subgroup_means, color=self.COLOR_BLAU, linewidth=1, zorder=3, alpha=0.7)
            ax.scatter(indices, self.subgroup_means, c=point_colors, edgecolor=self.COLOR_NEGRE, s=60, zorder=4)

            # Plot control limits
            ax.axhline(self.ucl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"UCL = {self.ucl:.3f}")
            ax.axhline(self.grand_mean, color=self.COLOR_NEGRE, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"X̄̄ = {self.grand_mean:.3f}")
            ax.axhline(self.lcl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"LCL = {self.lcl:.3f}")

            # Plot specification limits
            ax.axhline(self.usl, color=self.COLOR_TARONJA, linestyle="--", linewidth=1, alpha=0.8, zorder=1,
                      label=f"USL = {self.usl:.3f}")
            ax.axhline(self.lsl, color=self.COLOR_TARONJA, linestyle="--", linewidth=1, alpha=0.8, zorder=1,
                      label=f"LSL = {self.lsl:.3f}")

            chart_title = f"X-bar Chart for {self.element}\n(Subgroup size: {self.subgroup_size})"
            self._set_titles_and_labels(ax, title=chart_title,
                                       xlabel="Subgroup Number",
                                       ylabel="Subgroup Average")

            ax.set_xticks(indices)
            ax.set_xticklabels(indices)
            self._set_legend(ax)
            plt.tight_layout()

            self._finalize()
            self.logger.info("X-bar Chart created successfully")

        except Exception as e:
            self.logger.error(f"Error creating X-bar Chart: {e}", exc_info=True)
            raise