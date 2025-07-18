import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase


class IChart(SPCChartBase):
    """
    Individual Chart (I-Chart) for Statistical Process Control.
    
    This class creates an I-Chart with control limits, center line, and tolerance limits.
    It handles both provided control limits and calculates them from moving ranges when needed.
    """
    
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None, 
                 i18n_folder=None, extra_rcparams=None, logger=None, element_name=None):
        """
        Initialize the IChart with data from JSON file.
        
        Expected JSON structure for each element:
        {
            "element_name": {
                "sample_data": [list of measurements],
                "nominal": float (target value),
                "tolerance": [lower_tol, upper_tol] (relative to nominal),
                "mean": float (optional, will be calculated if not provided),
                "moving_range": float (optional, will be calculated if not provided),
                "ucl": float (optional, will be calculated if not provided),
                "lcl": float (optional, will be calculated if not provided),
                "cp": float (optional, process capability),
                "cpk": float (optional, process capability index)
            }
        }
        """
        super().__init__(
            input_json_path=input_json_path,
            lang=lang,
            show=show,
            save_path=save_path,
            i18n_folder=i18n_folder,
            extra_rcparams=extra_rcparams,
            logger=logger,
            element_name=element_name
        )
        
        # Parse and validate element data
        self._parse_element_data()
        
        # Calculate missing values
        self._calculate_control_limits()
        self._calculate_process_capability()
        
        self.logger.info(f"IChart initialized for element: {self.element}")

    def _parse_element_data(self):
        """Parse and validate the element data from JSON."""
        try:
            # Required fields
            self.sample_data = np.array(self.element_data.get("sample_data", []))
            if len(self.sample_data) == 0:
                raise ValueError("sample_data is required and cannot be empty")
            
            self.nominal = self.element_data.get("nominal", 0)
            self.tolerance = self.element_data.get("tolerance", [-1, 1])
            
            if len(self.tolerance) != 2:
                raise ValueError("tolerance must be a list of [lower_tolerance, upper_tolerance]")
            
            # Optional fields
            self.element = self.element_data.get("element_name", self.element_name)
            self.mean = self.element_data.get("mean", None)
            self.moving_range = self.element_data.get("moving_range", None)
            self.ucl = self.element_data.get("ucl", None)
            self.lcl = self.element_data.get("lcl", None)
            self.cp = self.element_data.get("cp", None)
            self.cpk = self.element_data.get("cpk", None)
            
            # Calculate tolerance limits
            self.lsl = self.nominal + self.tolerance[0]  # Lower Specification Limit
            self.usl = self.nominal + self.tolerance[1]  # Upper Specification Limit
            
            self.logger.debug(f"Parsed data: n={len(self.sample_data)}, nominal={self.nominal}, LSL={self.lsl}, USL={self.usl}")
            
        except Exception as e:
            self.logger.error(f"Error parsing element data: {e}")
            raise

    def _calculate_control_limits(self):
        """Calculate control limits if not provided."""
        try:
            # Calculate mean if not provided
            if self.mean is None:
                self.mean = np.mean(self.sample_data)
                self.logger.debug(f"Calculated mean: {self.mean:.4f}")
            
            # Calculate moving range if not provided
            if self.moving_range is None:
                if len(self.sample_data) < 2:
                    raise ValueError("Need at least 2 data points to calculate moving range")
                
                moving_ranges = np.abs(np.diff(self.sample_data))
                self.moving_range = np.mean(moving_ranges)
                self.logger.debug(f"Calculated moving range: {self.moving_range:.4f}")
            
            # Calculate control limits if not provided
            if self.ucl is None or self.lcl is None:
                # Constants for Individual charts (n=1)
                # For moving range of 2: D4 = 3.267, D3 = 0
                # For control limits: A2 = 2.659 (approximate)
                A2 = 2.659  # Constant for individual measurements
                
                self.ucl = self.mean + A2 * self.moving_range
                self.lcl = self.mean - A2 * self.moving_range
                
                self.logger.debug(f"Calculated control limits: UCL={self.ucl:.4f}, LCL={self.lcl:.4f}")
                
        except Exception as e:
            self.logger.error(f"Error calculating control limits: {e}")
            raise

    def _calculate_process_capability(self):
        """Calculate process capability indices if not provided."""
        try:
            if self.cp is None or self.cpk is None:
                if len(self.sample_data) < 2:
                    self.logger.warning("Need at least 2 data points for process capability calculation")
                    return
                
                # Calculate standard deviation
                # For Individual charts, we estimate sigma from moving range
                # sigma = MR / d2, where d2 = 1.128 for n=2
                d2 = 1.128
                sigma = self.moving_range / d2
                
                # Calculate Cp (process capability)
                if self.cp is None:
                    self.cp = (self.usl - self.lsl) / (6 * sigma)
                
                # Calculate Cpk (process capability index)
                if self.cpk is None:
                    cpu = (self.usl - self.mean) / (3 * sigma)
                    cpl = (self.mean - self.lsl) / (3 * sigma)
                    self.cpk = min(cpu, cpl)
                
                self.logger.debug(f"Calculated process capability: Cp={self.cp:.4f}, Cpk={self.cpk:.4f}")
                
        except Exception as e:
            self.logger.error(f"Error calculating process capability: {e}")
            # Set to None if calculation fails
            self.cp = None
            self.cpk = None

    def _get_point_colors(self):
        """Determine point colors based on whether they're within specification limits."""
        colors = []
        for value in self.sample_data:
            if self.lsl <= value <= self.usl:
                colors.append(self.COLOR_BLAU)
            else:
                colors.append(self.COLOR_VERMELL)
        return colors

    def plot(self):
        """Create and display/save the I-Chart."""
        try:
            self.logger.info(f"Creating I-Chart for element: {self.element}")
            
            # Create figure
            fig, ax = self._create_figure()
            
            # Prepare data
            indices = np.arange(1, len(self.sample_data) + 1)
            point_colors = self._get_point_colors()
            
            # Plot data points and line
            ax.plot(indices, self.sample_data, color=self.COLOR_BLAU, 
                   linewidth=1, zorder=3, alpha=0.7)
            ax.scatter(indices, self.sample_data, c=point_colors, 
                      edgecolor=self.COLOR_NEGRE, s=60, zorder=4)
            
            # Plot control limits
            ax.axhline(self.ucl, color=self.COLOR_VERMELL, linestyle="-", 
                      linewidth=1.5, zorder=2, 
                      label=self.labels.get("ucl_label", "UCL = {ucl:.3f}").format(ucl=self.ucl))
            ax.axhline(self.mean, color=self.COLOR_NEGRE, linestyle="-", 
                      linewidth=1.5, zorder=2,
                      label=self.labels.get("cl_label", "CL = {cl:.3f}").format(cl=self.mean))
            ax.axhline(self.lcl, color=self.COLOR_VERMELL, linestyle="-", 
                      linewidth=1.5, zorder=2,
                      label=self.labels.get("lcl_label", "LCL = {lcl:.3f}").format(lcl=self.lcl))
            
            # Plot specification limits (optional, as dashed lines)
            ax.axhline(self.usl, color=self.COLOR_TARONJA, linestyle="--", 
                      linewidth=1, alpha=0.8, zorder=1,
                      label=self.labels.get("usl_label", "USL = {usl:.3f}").format(usl=self.usl))
            ax.axhline(self.lsl, color=self.COLOR_TARONJA, linestyle="--", 
                      linewidth=1, alpha=0.8, zorder=1,
                      label=self.labels.get("lsl_label", "LSL = {lsl:.3f}").format(lsl=self.lsl))
            
            # Set titles and labels
            chart_title = self.labels.get("individual_chart", "Individual Chart for {element}").format(element=self.element)
            
            # Add process capability to title if available
            if self.cp is not None and self.cpk is not None:
                capability_text = self.labels.get("process_capability", "Process Capability: Cp = {cp:.2f}, Cpk = {cpk:.2f}").format(cp=self.cp, cpk=self.cpk)
                chart_title += f"\n{capability_text}"
            
            self._set_titles_and_labels(
                ax,
                title=chart_title,
                xlabel=self.labels.get("index_piece", "Sample Number"),
                ylabel=self.labels.get("value_measured", "Measured Value")
            )
            
            # Configure x-axis
            ax.set_xticks(indices)
            ax.set_xticklabels(indices)
            
            # Set legend
            self._set_legend(ax)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save and/or show
            self._finalize()
            
            self.logger.info("I-Chart created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating I-Chart: {e}", exc_info=True)
            raise


# Example usage and testing
if __name__ == "__main__":
    import json
    import tempfile
    
    # Test data structure
    test_data = {
        "test_element": {
            "sample_data": [9.4, 10.1, 9.8, 10.2, 9.7, 10.3, 9.6, 9.9, 10.0, 9.5],
            "nominal": 10.0,
            "tolerance": [-0.5, 0.5],
            "element_name": "Test Measurement"
        }
    }
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(test_data, tmp)
        tmp_path = tmp.name
    
    try:
        # Create and test the chart
        chart = IChart(
            input_json_path=tmp_path,
            lang="ca",
            show=True,
            element_name="test_element"
        )
        chart.plot()
        
        print("I-Chart created successfully!")
        print(f"Control limits: UCL={chart.ucl:.3f}, CL={chart.mean:.3f}, LCL={chart.lcl:.3f}")
        print(f"Process capability: Cp={chart.cp:.3f}, Cpk={chart.cpk:.3f}")
        
    finally:
        # Clean up
        import os
        os.unlink(tmp_path)