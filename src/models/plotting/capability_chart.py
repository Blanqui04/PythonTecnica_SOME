# src/models/plotting/capability_chart.py - PROFESSIONAL PPAP AESTHETIC
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
from matplotlib.patches import Rectangle
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger


class CapabilityChart(SPCChartBase):
    """Professional Process Capability Chart with PPAP-compliant styling"""

    def __init__(self, input_json_path, element_name=None, **kwargs):
        super().__init__(input_json_path, element_name=element_name, **kwargs)
        self.logger = base_logger.getChild(self.__class__.__name__)
        self._validate_data()


    def _validate_data(self):
        """Validate required data fields"""
        required_fields = [
            "mean", "std_short", "std_long", "tolerance", "cp", "cpk",
            "pp", "ppk", "ppm_short", "ppm_long", "nominal"
        ]

        missing = [f for f in required_fields 
                  if f not in self.element_data or self.element_data[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        tolerance = self.element_data["tolerance"]
        nominal = self.element_data["nominal"]
        
        self.lsl = nominal + tolerance[0]
        self.usl = nominal + tolerance[1]


    def _get_chart_data(self):
        """Extract chart data"""
        return {
            "mean": self.element_data["mean"],
            "std_short": self.element_data["std_short"],
            "std_long": self.element_data["std_long"],
            "cp": self.element_data["cp"],
            "cpk": self.element_data["cpk"],
            "pp": self.element_data["pp"],
            "ppk": self.element_data["ppk"],
            "ppm_short": self.element_data["ppm_short"],
            "ppm_long": self.element_data["ppm_long"],
            "lsl": self.lsl,
            "usl": self.usl,
        }


    def plot(self):
        """Create professional capability chart"""
        try:
            data = self._get_chart_data()

            # Create figure with professional layout
            fig = plt.figure(figsize=(10, 6.5))
            fig.patch.set_facecolor(self.FIGURE_FACECOLOR)
            gs = gridspec.GridSpec(1, 2, width_ratios=[2.2, 1], 
                                  left=0.08, right=0.98, top=0.92, bottom=0.08)

            # Main chart
            ax = fig.add_subplot(gs[0])
            self._draw_main_chart(ax, data)

            # Tables
            axbox = fig.add_subplot(gs[1])
            axbox.axis('off')
            self._create_capability_tables(axbox, data)

            # Main title
            fig.suptitle(f"Process Capability Analysis: {self.element_name}",
                        fontsize=self.FONT_SIZE_TITLE + 2,
                        fontweight='bold',
                        color=self.COLOR_PRIMARY_BLUE,
                        y=0.97)

            self._finalize()

        except Exception as e:
            self.logger.error(f"Error creating capability chart: {e}", exc_info=True)
            raise


    def _draw_main_chart(self, ax, data):
        """Draw the main capability visualization"""
        
        ax.set_facecolor(self.AXES_FACECOLOR)
        
        # Calculate scale
        x_points = [
            data["lsl"], data["usl"], data["mean"],
            data["mean"] - 3 * data["std_short"],
            data["mean"] + 3 * data["std_short"],
            data["mean"] - 3 * data["std_long"],
            data["mean"] + 3 * data["std_long"]
        ]
        
        x_min, x_max = min(x_points), max(x_points)
        x_margin = 0.05 * (x_max - x_min) if x_max > x_min else 1
        scale_min = x_min - x_margin
        scale_max = x_max + x_margin

        # Row labels with professional styling
        row_labels = ["Long-term", "Short-term", "Specifications"]
        row_colors = [self.COLOR_SECONDARY_BLUE, self.COLOR_ACCENT_BLUE, self.COLOR_DANGER_RED]
        
        for y_pos, label, color in zip([2, 1, 0], row_labels, row_colors):
            ax.text(scale_min - 0.02 * abs(scale_max - scale_min), y_pos, label,
                   verticalalignment='center', fontsize=self.FONT_SIZE_LABEL,
                   fontweight='bold', rotation=90, ha='right',
                   color=color, fontname=self.FONT_NAME)

        # Draw horizontal capability bars
        bars = [
            (0, data["lsl"], data["usl"], self.COLOR_DANGER_RED, 2.5),
            (1, data["mean"] - 3 * data["std_short"], 
             data["mean"] + 3 * data["std_short"], self.COLOR_ACCENT_BLUE, 2.0),
            (2, data["mean"] - 3 * data["std_long"], 
             data["mean"] + 3 * data["std_long"], self.COLOR_SECONDARY_BLUE, 2.0)
        ]
        
        for y, x_min_bar, x_max_bar, color, lw in bars:
            ax.hlines(y=y, xmin=x_min_bar, xmax=x_max_bar,
                     color=color, linestyle='-', linewidth=lw, alpha=0.9)
            
            # End markers
            marker = 's' if y == 0 else 'D'
            ax.plot([x_min_bar, x_max_bar], [y, y], marker,
                   color=color, markersize=6, zorder=6,
                   markeredgecolor=self.COLOR_DARK_GRAY, markeredgewidth=0.8)

        # Mean markers
        ax.plot(data["mean"], 1, 'o', color=self.COLOR_PRIMARY_BLUE,
               markersize=7, zorder=7, markeredgecolor=self.COLOR_DARK_GRAY,
               markeredgewidth=1.2, label='Process Mean')
        ax.plot(data["mean"], 2, 'o', color=self.COLOR_PRIMARY_BLUE,
               markersize=7, zorder=7, markeredgecolor=self.COLOR_DARK_GRAY,
               markeredgewidth=1.2)

        # Vertical reference lines
        ax.vlines(data["mean"], -0.3, 2.7, color=self.COLOR_PRIMARY_BLUE,
                 linestyle='-.', linewidth=1.2, alpha=0.7, zorder=5)
        ax.vlines(data["usl"], -0.5, 2.7, color=self.COLOR_DANGER_RED,
                 linestyle='--', linewidth=1.0, alpha=0.6)
        ax.vlines(data["lsl"], -0.5, 2.7, color=self.COLOR_DANGER_RED,
                 linestyle='--', linewidth=1.0, alpha=0.6)

        # Limit labels
        ax.text(data["usl"], 2.55, f'USL = {data["usl"]:.2f}',
               color=self.COLOR_DANGER_RED, fontsize=self.FONT_SIZE_ANNOTATION,
               ha='center', va='bottom', weight='bold',
               bbox=dict(facecolor='white', edgecolor=self.COLOR_DANGER_RED,
                        boxstyle='round,pad=0.4', alpha=0.95, linewidth=0.8))
        
        ax.text(data["lsl"], 2.55, f'LSL = {data["lsl"]:.2f}',
               color=self.COLOR_DANGER_RED, fontsize=self.FONT_SIZE_ANNOTATION,
               ha='center', va='bottom', weight='bold',
               bbox=dict(facecolor='white', edgecolor=self.COLOR_DANGER_RED,
                        boxstyle='round,pad=0.4', alpha=0.95, linewidth=0.8))

        # Axis properties
        ax.set_ylim(-0.3, 2.8)
        ax.set_xlim(scale_min, scale_max)
        ax.set_yticks([])
        ax.set_xlabel('Measured Value', fontsize=self.FONT_SIZE_LABEL,
                     color=self.COLOR_DARK_GRAY, fontweight='normal')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--',
               linewidth=self.LINEWIDTH_GRID)
        
        # Professional border
        for spine in ax.spines.values():
            spine.set_edgecolor(self.COLOR_DARK_GRAY)
            spine.set_linewidth(1.2)


    def _create_capability_tables(self, axbox, data):
        """Create capability information tables with improved styling"""
        # Create tables with better spacing - reduced height for tighter rows
        self._create_single_table(axbox, data, "short", 0.56, 0.3)
        self._create_single_table(axbox, data, "long", 0.08, 0.3)


    def _create_single_table(self, axbox, data, term_type, y_pos, height):
        """Create a single capability table with professional styling"""
        is_short = (term_type == "short")
        
        # Configuration
        header_text = "Short-term Capability" if is_short else "Long-term Capability"
        header_color = self.COLOR_ACCENT_BLUE if is_short else self.COLOR_SECONDARY_BLUE
        
        # Data selection
        if is_short:
            params = [
                ("Cp", data["cp"]),
                ("Cpk", data["cpk"]),
                ("PPM Defective", data["ppm_short"]),
                ("Std Dev (σ)", data["std_short"])
            ]
        else:
            params = [
                ("Pp", data["pp"]),
                ("Ppk", data["ppk"]),
                ("PPM Defective", data["ppm_long"]),
                ("Std Dev (σ)", data["std_long"])
            ]

        # Add header as text with rectangular box (matches table aesthetic)
        axbox.text(0.5, y_pos + height + 0.02, header_text,
                transform=axbox.transAxes,
                fontsize=self.FONT_SIZE_SUBTITLE + 1,
                fontweight='bold',
                color='white',
                ha='center',
                va='bottom',
                bbox=dict(boxstyle='square,pad=0.5',  # Square instead of round
                        facecolor=header_color,
                        edgecolor=self.COLOR_DARK_GRAY,
                        linewidth=1.2))

        # Create table without header row
        n_rows = len(params)
        table = Table(axbox, bbox=[0.05, y_pos, 0.9, height])
        
        # Data rows with improved sizing
        row_height = 1.0 / n_rows
        for i, (label, value) in enumerate(params):
            # Alternate row colors for better readability
            row_bg = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
            
            # Label cell (left column)
            label_cell = table.add_cell(i, 0, width=0.55, height=row_height,
                                    text=label, loc='left',
                                    facecolor=row_bg)
            label_cell.get_text().set_fontsize(self.FONT_SIZE_LABEL + 2)
            label_cell.get_text().set_fontname(self.FONT_NAME)
            label_cell.get_text().set_color(self.COLOR_DARK_GRAY)
            label_cell.get_text().set_weight('normal')
            label_cell.set_edgecolor(self.COLOR_MEDIUM_GRAY)
            label_cell.set_linewidth(0.8)
            label_cell.PAD = 0.08
            
            # Format value based on type
            if isinstance(value, float):
                if "PPM" in label:
                    formatted_value = f"{value:.1f}"
                elif "Std Dev" in label:
                    formatted_value = f"{value:.4f}"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            # Value cell (right column)
            value_cell = table.add_cell(i, 1, width=0.45, height=row_height,
                                    text=formatted_value, loc='right',
                                    facecolor=row_bg)
            value_cell.get_text().set_fontsize(self.FONT_SIZE_LABEL + 2)
            value_cell.get_text().set_fontname(self.FONT_NAME)
            value_cell.get_text().set_weight('bold')
            value_cell.get_text().set_color(self.COLOR_PRIMARY_BLUE)
            value_cell.set_edgecolor(self.COLOR_MEDIUM_GRAY)
            value_cell.set_linewidth(0.8)
            value_cell.PAD = 0.08

        axbox.add_table(table)