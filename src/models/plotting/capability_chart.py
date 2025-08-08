# src/models/plotting/capability_chart.py - FIXED VERSION
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
from .base_chart import SPCChartBase
from .logging_config import logger as base_logger

class CapabilityChart(SPCChartBase):
    """
    Creates a process capability chart showing short-term and long-term capability indices
    with specification limits and statistical tables.
    """

    def __init__(self, input_json_path, element_name=None, **kwargs):
        """
        Initialize the capability chart.

        Args:
            input_json_path: Path to JSON file containing SPC data
            element_name: Specific element to chart (if None, uses first element)
            **kwargs: Additional arguments passed to SPCChartBase
        """
        super().__init__(input_json_path, element_name=element_name, **kwargs)
        self.logger = base_logger.getChild(self.__class__.__name__)
        self.logger.info(
            f"🔄 Initialized CapabilityChart for element: {self.element_name}"
        )

        # Validate required data fields
        self._validate_data()

    def _validate_data(self):
        """Validate that all required data fields are present."""
        self.logger.info(f"🔍 Validating data for element: {self.element_name}")
        self.logger.info(f"📊 Available data keys: {list(self.element_data.keys())}")
        
        required_fields = [
            "mean",
            "std_short",
            "std_long",
            "tolerance",
            "cp",
            "cpk",
            "pp",
            "ppk",
            "ppm_short",
            "ppm_long",
            "nominal",
        ]

        missing_fields = [
            field for field in required_fields if field not in self.element_data or self.element_data[field] is None
        ]
        if missing_fields:
            error_msg = f"❌ Missing required data fields: {missing_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Calculate USL and LSL from nominal and tolerance
        tolerance = self.element_data["tolerance"]
        nominal = self.element_data["nominal"]
        
        # Log the values for debugging
        self.logger.info(f"📏 Nominal: {nominal}")
        self.logger.info(f"📏 Tolerance: {tolerance}")
        
        self.lsl = nominal + tolerance[0]  # tolerance[0] is typically negative
        self.usl = nominal + tolerance[1]  # tolerance[1] is typically positive

        self.logger.info(f"📏 Calculated limits: LSL={self.lsl:.4f}, USL={self.usl:.4f}")
        self.logger.info(f"✅ Data validation completed for element: {self.element_name}")

    def _get_chart_data(self):
        """Extract and return chart data from element_data."""
        self.logger.debug("📊 Extracting chart data from element_data")

        data = {
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

        self.logger.debug(
            f"📈 Chart data extracted: mean={data['mean']:.4f}, "
            f"std_short={data['std_short']:.4f}, std_long={data['std_long']:.4f}"
        )

        return data

    def _get_translations(self):
        """Get chart-specific translations."""
        self.logger.debug("🌐 Loading chart-specific translations")

        base_translations = {
            "short_term": "Short Term",
            "long_term": "Long Term",
            "specifications": "Specifications",
            "std_dev": "Std. Dev.",
            "usl_label": "USL = {usl:.3f}",
            "lsl_label": "LSL = {lsl:.3f}",
            "value_measured": "Measured Value",
            "process_capability_plot": "Process Capability Plot: {element}",
            "mean_label": "Mean",
        }

        # Update with loaded translations
        for key, default_value in base_translations.items():
            base_translations[key] = self.labels.get(key, default_value)

        self.logger.debug("✅ Chart translations loaded successfully")
        return base_translations

    def _calculate_scale_parameters(self, data):
        """Calculate chart scale parameters."""
        self.logger.debug("📐 Calculating scale parameters for chart")

        x_points = [
            data["lsl"],
            data["usl"],
            data["mean"] - 3 * data["std_short"],
            data["mean"] + 3 * data["std_short"],
            data["mean"] - 3 * data["std_long"],
            data["mean"] + 3 * data["std_long"],
            data["mean"],
        ]

        x_min, x_max = min(x_points), max(x_points)
        x_margin = 0.02 * (x_max - x_min) if x_max > x_min else 1

        scale_min = x_min - x_margin
        scale_max = x_max + x_margin

        self.logger.debug(
            f"📐 Scale parameters calculated: min={scale_min:.4f}, max={scale_max:.4f}"
        )

        return scale_min, scale_max

    def _draw_main_chart(self, ax, data, translations):
        """Draw the main capability chart."""
        self.logger.debug("🎨 Drawing main capability chart")

        scale_min, scale_max = self._calculate_scale_parameters(data)

        # Add row labels
        for y_pos, label in zip(
            [2, 1, 0],
            [
                translations["long_term"],
                translations["short_term"],
                translations["specifications"],
            ],
        ):
            ax.text(
                scale_min - 0.01 * abs(scale_max - scale_min),
                y_pos,
                label,
                verticalalignment="center",
                fontsize=10,
                fontweight="normal",
                rotation=90,
                ha="right",
                fontname=self.FONT_NAME,
            )

        # Draw horizontal lines
        ax.hlines(
            y=0,
            xmin=data["lsl"],
            xmax=data["usl"],
            color=self.COLOR_VERMELL,
            linestyle="-",
            linewidth=1,
        )
        ax.hlines(
            y=1,
            xmin=data["mean"] - 3 * data["std_short"],
            xmax=data["mean"] + 3 * data["std_short"],
            color=self.COLOR_BLAU,
            linestyle="-",
            linewidth=1,
        )
        ax.hlines(
            y=2,
            xmin=data["mean"] - 3 * data["std_long"],
            xmax=data["mean"] + 3 * data["std_long"],
            color=self.COLOR_BLAU,
            linestyle="-",
            linewidth=1,
        )

        # Add markers
        ax.plot(
            [data["lsl"], data["usl"]],
            [0, 0],
            "s",
            color=self.COLOR_VERMELL,
            markersize=5,
            zorder=6,
        )
        ax.plot(
            [
                data["mean"] - 3 * data["std_short"],
                data["mean"] + 3 * data["std_short"],
            ],
            [1, 1],
            "+",
            color=self.COLOR_BLAU,
            markersize=7,
            zorder=6,
        )
        ax.plot(
            [data["mean"] - 3 * data["std_long"], data["mean"] + 3 * data["std_long"]],
            [2, 2],
            "+",
            color=self.COLOR_BLAU,
            markersize=7,
            zorder=6,
        )
        ax.plot(data["mean"], 1, "x", color=self.COLOR_NEGRE, markersize=6, zorder=7)
        ax.plot(data["mean"], 2, "x", color=self.COLOR_NEGRE, markersize=6, zorder=7)

        # Add vertical lines
        ax.vlines(
            data["mean"],
            -0.3,
            2.7,
            color=self.COLOR_NEGRE,
            linestyle="-.",
            linewidth=0.75,
            zorder=5,
        )
        ax.vlines(
            data["usl"],
            -0.5,
            2.7,
            color=self.COLOR_VERMELL,
            linestyle="--",
            linewidth=0.75,
        )
        ax.vlines(
            data["lsl"],
            -0.5,
            2.7,
            color=self.COLOR_VERMELL,
            linestyle="--",
            linewidth=0.75,
        )

        # Add limit labels
        ax.text(
            data["usl"],
            2.5,
            translations["usl_label"].format(usl=data["usl"]),
            color=self.COLOR_VERMELL,
            fontsize=9,
            ha="center",
            va="bottom",
            fontname=self.FONT_NAME,
            bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"),
        )
        ax.text(
            data["lsl"],
            2.5,
            translations["lsl_label"].format(lsl=data["lsl"]),
            color=self.COLOR_VERMELL,
            fontsize=9,
            ha="center",
            va="bottom",
            fontname=self.FONT_NAME,
            bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.1"),
        )

        # Set axis properties
        ax.set_ylim(-0.3, 2.7)
        ax.set_xlim(scale_min, scale_max)
        ax.set_yticks([])
        ax.set_xlabel(
            translations["value_measured"], fontsize=10, fontname=self.FONT_NAME
        )
        ax.grid(True, axis="both", linestyle="--", alpha=0.4)

        # Add title and subtitle
        title = translations["process_capability_plot"].format(
            element=self.element_name
        )
        #subtitle = f"{translations['mean_label']}: {data['mean']:.4f}"
        ax.set_title(title, fontsize=15, pad=28, fontname=self.FONT_NAME)
        #ax.text(
        #    0.5,
        #    1.02,
        #    subtitle,
        #    transform=ax.transAxes,
        #    ha="center",
        #    fontsize=11,
        #    color="#444444",
        #    va="bottom",
        #    fontname=self.FONT_NAME,
        #)

        self.logger.debug("✅ Main capability chart drawn successfully")

    def _create_capability_table(self, axbox, data, translations, table_type="short"):
        """Create capability information table."""
        self.logger.debug(f"📊 Creating {table_type} term capability table")

        is_short = table_type == "short"

        # Table configuration
        bbox_y = 0.55 if is_short else 0.05
        bbox_height = 0.35 if is_short else 0.45
        header_text = (
            translations["short_term"] if is_short else translations["long_term"]
        )
        header_color = "#e6e6f2" if is_short else "#d9f2d9"
        cell_color = "#f9f9f9" if is_short else "#f9fff9"

        # Data selection
        if is_short:
            indices = {
                "primary": "cp",
                "secondary": "cpk",
                "ppm": "ppm_short",
                "std": "std_short",
            }
            labels = {"primary": "Cp", "secondary": "Cpk"}
        else:
            indices = {
                "primary": "pp",
                "secondary": "ppk",
                "ppm": "ppm_long",
                "std": "std_long",
            }
            labels = {"primary": "Pp", "secondary": "Ppk"}

        # Create table
        table = Table(axbox, bbox=[0, bbox_y, 1, bbox_height])
        wd = 0.5

        # Add cells
        table.add_cell(
            0,
            0,
            width=0.5,
            height=0.25,
            text=header_text,
            loc="center",
            facecolor=header_color,
        )
        table.add_cell(
            1,
            0,
            width=wd,
            height=0.2,
            text=labels["primary"],
            loc="left",
            facecolor=cell_color,
        )
        table.add_cell(
            1,
            1,
            width=wd,
            height=0.2,
            text=f"{data[indices['primary']]:.2f}",
            loc="left",
        )
        table.add_cell(
            2,
            0,
            width=wd,
            height=0.2,
            text=labels["secondary"],
            loc="left",
            facecolor=cell_color,
        )
        table.add_cell(
            2,
            1,
            width=wd,
            height=0.2,
            text=f"{data[indices['secondary']]:.2f}",
            loc="left",
        )
        table.add_cell(
            3, 0, width=wd, height=0.2, text="PPM", loc="left", facecolor=cell_color
        )
        table.add_cell(
            3, 1, width=wd, height=0.2, text=f"{data[indices['ppm']]:.2f}", loc="left"
        )
        table.add_cell(
            4,
            0,
            width=wd,
            height=0.2,
            text=translations["std_dev"],
            loc="left",
            facecolor=cell_color,
        )
        table.add_cell(
            4, 1, width=wd, height=0.2, text=f"{data[indices['std']]:.4f}", loc="left"
        )

        # Style table
        header_cell = table[(0, 0)]
        header_cell.get_text().set_fontsize(14)
        header_cell.get_text().set_fontname(self.FONT_NAME)
        header_cell.get_text().set_weight("normal")
        header_cell.get_text().set_ha("center")
        header_cell.visible_edges = "open"

        for i in range(1, 5):
            for j in range(2):
                cell = table[(i, j)]
                cell.get_text().set_fontsize(10)
                cell.get_text().set_fontname(self.FONT_NAME)
                if j == 0:
                    cell.set_facecolor(cell_color)
                    cell.get_text().set_weight("normal")
                else:
                    cell.get_text().set_weight("bold")

        axbox.add_table(table)

        self.logger.debug(f"✅ {table_type} term capability table created successfully")

    def plot(self):
        """Generate the capability chart."""
        self.logger.info(f"🚀 Starting capability chart generation for {self.element_name}")
        self.logger.info(f"💾 Save path: {self.save_path}")

        try:
            # Get data and translations
            self.logger.info("📊 Getting chart data and translations")
            data = self._get_chart_data()
            translations = self._get_translations()

            # Create figure with grid layout
            self.logger.info("🎨 Creating figure with grid layout")
            fig = plt.figure(figsize=(9, 6))
            gs = gridspec.GridSpec(1, 2, width_ratios=[2.2, 1])

            # Main chart
            self.logger.info("🎯 Drawing main chart")
            ax = fig.add_subplot(gs[0])
            self._draw_main_chart(ax, data, translations)

            # Tables
            self.logger.info("📋 Creating capability tables")
            axbox = fig.add_subplot(gs[1])
            axbox.axis("off")

            self._create_capability_table(axbox, data, translations, "short")
            self._create_capability_table(axbox, data, translations, "long")

            plt.tight_layout()
            self.logger.info("✅ Capability chart generated successfully")

        except Exception as e:
            self.logger.error(f"❌ Error generating capability chart: {e}", exc_info=True)
            raise

        finally:
            # CRITICAL: Always call _finalize to save the chart
            self.logger.info("🔄 Finalizing chart (saving/displaying)")
            self._finalize()