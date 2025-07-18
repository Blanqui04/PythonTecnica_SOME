import numpy as np
import matplotlib.pyplot as plt
from .base_chart import SPCChartBase


class MRChart(SPCChartBase):
    """
    Moving Range Chart (MR-Chart) for Statistical Process Control.
    
    This class creates an MR-Chart with control limits and center line.
    It's typically used in conjunction with Individual charts (I-Chart) to monitor process variability.
    """
    
    def __init__(self, input_json_path, lang="ca", show=False, save_path=None, 
                 i18n_folder=None, extra_rcparams=None, logger=None, element_name=None):
        """
        Initialize the MRChart with data from JSON file.
        
        Expected JSON structure for each element:
        {
            "element_name": {
                "sample_data": [list of measurements],
                "element_name": "Display name for element",
                "moving_ranges": [list of moving ranges] (optional, will be calculated if not provided),
                "mr_mean": float (optional, will be calculated if not provided),
                "mr_ucl": float (optional, will be calculated if not provided),
                "mr_lcl": float (optional, will be calculated if not provided),
                "estimated_sigma": float (optional, will be calculated if not provided)
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
        self._calculate_moving_ranges()
        self._calculate_control_limits()
        self._calculate_estimated_sigma()
        
        self.logger.info(f"MRChart initialized for element: {self.element}")

    def _parse_element_data(self):
        """Parse and validate the element data from JSON."""
        try:
            # Required fields
            self.sample_data = np.array(self.element_data.get("sample_data", []))
            if len(self.sample_data) < 2:
                raise ValueError("At least 2 data points are required for Moving Range chart")
            
            # Optional fields
            self.element = self.element_data.get("element_name", self.element_name)
            self.moving_ranges = self.element_data.get("moving_ranges", None)
            self.mr_mean = self.element_data.get("mr_mean", None)
            self.mr_ucl = self.element_data.get("mr_ucl", None)
            self.mr_lcl = self.element_data.get("mr_lcl", None)
            self.estimated_sigma = self.element_data.get("estimated_sigma", None)
            
            self.logger.debug(f"Parsed data: n={len(self.sample_data)}, element={self.element}")
            
        except Exception as e:
            self.logger.error(f"Error parsing element data: {e}")
            raise

    def _calculate_moving_ranges(self):
        """Calculate moving ranges if not provided."""
        try:
            if self.moving_ranges is None:
                # Calculate moving ranges as absolute differences between consecutive values
                self.moving_ranges = np.abs(np.diff(self.sample_data))
                self.logger.debug(f"Calculated {len(self.moving_ranges)} moving ranges")
            else:
                self.moving_ranges = np.array(self.moving_ranges)
                
            # Indices for plotting (MR is defined from second observation)
            self.indices = np.arange(2, len(self.sample_data) + 1)
            
            if len(self.moving_ranges) != len(self.indices):
                raise ValueError(f"Moving ranges length ({len(self.moving_ranges)}) must match indices length ({len(self.indices)})")
                
        except Exception as e:
            self.logger.error(f"Error calculating moving ranges: {e}")
            raise

    def _calculate_control_limits(self):
        """Calculate control limits if not provided."""
        try:
            # Calculate mean of moving ranges if not provided
            if self.mr_mean is None:
                self.mr_mean = np.mean(self.moving_ranges)
                self.logger.debug(f"Calculated MR mean: {self.mr_mean:.4f}")
            
            # Calculate control limits if not provided
            if self.mr_ucl is None or self.mr_lcl is None:
                # Constants for Moving Range charts (subgroup size = 2)
                D4 = 3.267  # Upper control limit factor
                D3 = 0      # Lower control limit factor (always 0 for n=2)
                
                self.mr_ucl = D4 * self.mr_mean
                self.mr_lcl = D3 * self.mr_mean  # Always 0
                
                self.logger.debug(f"Calculated MR control limits: UCL={self.mr_ucl:.4f}, LCL={self.mr_lcl:.4f}")
                
        except Exception as e:
            self.logger.error(f"Error calculating control limits: {e}")
            raise

    def _calculate_estimated_sigma(self):
        """Calculate estimated sigma if not provided."""
        try:
            if self.estimated_sigma is None:
                # Estimate sigma from moving range
                # sigma = MR_bar / d2, where d2 = 1.128 for n=2
                d2 = 1.128
                self.estimated_sigma = self.mr_mean / d2
                
                self.logger.debug(f"Calculated estimated sigma: {self.estimated_sigma:.4f}")
                
        except Exception as e:
            self.logger.error(f"Error calculating estimated sigma: {e}")
            raise

    def _get_point_colors(self):
        """Determine point colors based on control limits."""
        colors = []
        for value in self.moving_ranges:
            if self.mr_lcl <= value <= self.mr_ucl:
                colors.append(self.COLOR_BLAU)
            else:
                colors.append(self.COLOR_VERMELL)
        return colors

    def _detect_out_of_control_points(self):
        """Detect points that are out of control."""
        out_of_control = []
        for i, value in enumerate(self.moving_ranges):
            if value > self.mr_ucl or value < self.mr_lcl:
                out_of_control.append(i)
        return out_of_control

    def plot(self):
        """Create and display/save the MR-Chart."""
        try:
            self.logger.info(f"Creating MR-Chart for element: {self.element}")
            
            # Create figure
            fig, ax = self._create_figure()
            
            # Get point colors
            point_colors = self._get_point_colors()
            
            # Plot moving ranges
            ax.plot(self.indices, self.moving_ranges, color=self.COLOR_BLAU, 
                   linewidth=1, zorder=3, alpha=0.7)
            ax.scatter(self.indices, self.moving_ranges, c=point_colors, 
                      edgecolor=self.COLOR_NEGRE, s=60, zorder=4)
            
            # Plot control limits
            ax.axhline(self.mr_ucl, color=self.COLOR_VERMELL, linestyle="-", 
                      linewidth=1.5, zorder=2, 
                      label=self.labels.get("ucl_label", "UCL = {ucl:.3f}").format(ucl=self.mr_ucl))
            ax.axhline(self.mr_mean, color=self.COLOR_NEGRE, linestyle="-", 
                      linewidth=1.5, zorder=2,
                      label=self.labels.get("cl_label", "CL = {cl:.3f}").format(cl=self.mr_mean))
            ax.axhline(self.mr_lcl, color=self.COLOR_VERMELL, linestyle="-", 
                      linewidth=1.5, zorder=2,
                      label=self.labels.get("lcl_label", "LCL = {lcl:.3f}").format(lcl=self.mr_lcl))
            
            # Set titles and labels
            chart_title = self.labels.get("moving_range_chart", "Moving Range Chart for {element}").format(element=self.element)
            
            # Add estimated sigma to title
            if self.estimated_sigma is not None:
                sigma_text = self.labels.get("estimated_sigma", "Estimated Sigma = {sigma:.4f}").format(sigma=self.estimated_sigma)
                chart_title += f"\n{sigma_text}"
            
            self._set_titles_and_labels(
                ax,
                title=chart_title,
                xlabel=self.labels.get("index_piece", "Sample Number"),
                ylabel=self.labels.get("mobile_range", "Moving Range")
            )
            
            # Configure x-axis
            ax.set_xticks(self.indices)
            ax.set_xticklabels(self.indices)
            
            # Set y-axis to start from 0 (moving ranges are always positive)
            ax.set_ylim(bottom=0)
            
            # Highlight out-of-control points
            out_of_control = self._detect_out_of_control_points()
            if out_of_control:
                for idx in out_of_control:
                    ax.annotate('!', xy=(self.indices[idx], self.moving_ranges[idx]), 
                               xytext=(5, 5), textcoords='offset points',
                               fontsize=12, color=self.COLOR_VERMELL, weight='bold')
                self.logger.warning(f"Found {len(out_of_control)} out-of-control points")
            
            # Set legend
            self._set_legend(ax)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save and/or show
            self._finalize()
            
            self.logger.info("MR-Chart created successfully")
            
            # Return statistics for potential use
            return {
                'mr_mean': self.mr_mean,
                'mr_ucl': self.mr_ucl,
                'mr_lcl': self.mr_lcl,
                'estimated_sigma': self.estimated_sigma,
                'out_of_control_points': len(out_of_control)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating MR-Chart: {e}", exc_info=True)
            raise

    def get_statistics(self):
        """Return calculated statistics for the MR chart."""
        return {
            'sample_count': len(self.sample_data),
            'moving_range_count': len(self.moving_ranges),
            'mr_mean': self.mr_mean,
            'mr_ucl': self.mr_ucl,
            'mr_lcl': self.mr_lcl,
            'estimated_sigma': self.estimated_sigma,
            'min_moving_range': np.min(self.moving_ranges),
            'max_moving_range': np.max(self.moving_ranges),
            'out_of_control_points': len(self._detect_out_of_control_points())
        }


# Example usage and testing
if __name__ == "__main__":
    import json
    import tempfile
    
    # Test data structure
    test_data = {
        "test_element": {
            "sample_data": [9.5, 10.1, 9.8, 10.2, 9.7, 10.3, 9.6, 9.9, 10.0, 9.5, 10.4],
            "element_name": "Test Measurement"
        }
    }
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(test_data, tmp)
        tmp_path = tmp.name
    
    try:
        # Create and test the chart
        chart = MRChart(
            input_json_path=tmp_path,
            lang="ca",
            show=True,
            element_name="test_element"
        )
        
        # Plot the chart and get statistics
        stats = chart.plot()
        
        print("MR-Chart created successfully!")
        print("Moving Range statistics:")
        print(f"  Mean: {stats['mr_mean']:.4f}")
        print(f"  UCL: {stats['mr_ucl']:.4f}")
        print(f"  LCL: {stats['mr_lcl']:.4f}")
        print(f"  Estimated Sigma: {stats['estimated_sigma']:.4f}")
        print(f"  Out-of-control points: {stats['out_of_control_points']}")
        
        # Get detailed statistics
        detailed_stats = chart.get_statistics()
        print(f"\nDetailed statistics: {detailed_stats}")
        
    finally:
        # Clean up
        import os
        os.unlink(tmp_path)