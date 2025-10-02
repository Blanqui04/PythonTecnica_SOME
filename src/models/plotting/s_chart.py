# src/models/plotting/s_chart.py
import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class SChart(SPCChartBase):
    """
    S Chart (Standard Deviation Chart) for Statistical Process Control.
    Used for monitoring process variability with subgrouped data.
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
        """Initialize S Chart"""
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
        self._calculate_std_devs()
        self._calculate_control_limits()

        self.logger.info(f"SChart initialized for element: {self.element}")

    def _parse_element_data(self):
        """Parse element data"""
        try:
            self.sample_data = np.array(self.element_data.get("sample_data", []))
            if len(self.sample_data) < self.subgroup_size:
                raise ValueError(f"Need at least {self.subgroup_size} data points")

            self.element = self.element_data.get("element_name", self.element_name)
            self.logger.debug(f"Parsed data: n={len(self.sample_data)}")

        except Exception as e:
            self.logger.error(f"Error parsing element data: {e}")
            raise

    def _calculate_std_devs(self):
        """Calculate subgroup standard deviations"""
        try:
            n_subgroups = len(self.sample_data) // self.subgroup_size
            data_to_use = self.sample_data[:n_subgroups * self.subgroup_size]
            subgroups = data_to_use.reshape(n_subgroups, self.subgroup_size)
            self.std_devs = np.std(subgroups, axis=1, ddof=1)  # Sample std dev
            self.avg_std = np.mean(self.std_devs)
            
            self.logger.debug(f"Calculated {n_subgroups} std devs, avg std: {self.avg_std:.4f}")

        except Exception as e:
            self.logger.error(f"Error calculating std devs: {e}")
            raise

    def _calculate_control_limits(self):
        """Calculate control limits using B3 and B4 constants"""
        try:
            # B3 and B4 constants for different subgroup sizes
            B3_constants = {
                2: 0, 3: 0, 4: 0, 5: 0, 6: 0.029, 7: 0.113, 8: 0.179, 9: 0.232, 10: 0.276
            }
            B4_constants = {
                2: 3.267, 3: 2.568, 4: 2.266, 5: 2.089, 6: 1.970,
                7: 1.882, 8: 1.815, 9: 1.761, 10: 1.716
            }
            
            B3 = B3_constants.get(self.subgroup_size, 0)
            B4 = B4_constants.get(self.subgroup_size, 2.089)
            
            self.ucl = B4 * self.avg_std
            self.lcl = B3 * self.avg_std
            
            self.logger.debug(f"Control limits: UCL={self.ucl:.4f}, S̄={self.avg_std:.4f}, LCL={self.lcl:.4f}")

        except Exception as e:
            self.logger.error(f"Error calculating control limits: {e}")
            raise

    def _get_point_colors(self):
        """Determine point colors based on control limits"""
        colors = []
        for value in self.std_devs:
            if self.lcl <= value <= self.ucl:
                colors.append(self.COLOR_BLAU)
            else:
                colors.append(self.COLOR_VERMELL)
        return colors

    def plot(self):
        """Create S chart"""
        try:
            self.logger.info(f"Creating S Chart for element: {self.element}")

            fig, ax = self._create_figure()

            indices = np.arange(1, len(self.std_devs) + 1)
            point_colors = self._get_point_colors()

            # Plot data
            ax.plot(indices, self.std_devs, color=self.COLOR_BLAU, linewidth=1, zorder=3, alpha=0.7)
            ax.scatter(indices, self.std_devs, c=point_colors, edgecolor=self.COLOR_NEGRE, s=60, zorder=4)

            # Plot control limits
            ax.axhline(self.ucl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"UCL = {self.ucl:.3f}")
            ax.axhline(self.avg_std, color=self.COLOR_NEGRE, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"S̄ = {self.avg_std:.3f}")
            ax.axhline(self.lcl, color=self.COLOR_VERMELL, linestyle="-", linewidth=1.5, zorder=2,
                      label=f"LCL = {self.lcl:.3f}")

            chart_title = f"S Chart for {self.element}\n(Subgroup size: {self.subgroup_size})"
            self._set_titles_and_labels(ax, title=chart_title,
                                       xlabel="Subgroup Number",
                                       ylabel="Standard Deviation")

            ax.set_xticks(indices)
            ax.set_xticklabels(indices)
            ax.set_ylim(bottom=0)
            self._set_legend(ax)
            plt.tight_layout()

            self._finalize()
            self.logger.info("S Chart created successfully")

        except Exception as e:
            self.logger.error(f"Error creating S Chart: {e}", exc_info=True)
            raise