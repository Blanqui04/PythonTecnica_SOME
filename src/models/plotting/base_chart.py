# src/models/plotting/base_chart.py - PROFESSIONAL PPAP AESTHETIC
import json
from pathlib import Path
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
import logging
from .logging_config import logger as base_logger


class SPCChartBase(ABC):
    """Professional base class for SPC charts with PPAP-compliant styling"""
    
    # Professional color palette (matching Excel export)
    COLOR_PRIMARY_BLUE = "#1B365D"      # Main headers, serious tone
    COLOR_SECONDARY_BLUE = "#2E5266"    # Secondary elements
    COLOR_ACCENT_BLUE = "#4A90A4"       # Data points, lines
    COLOR_SUCCESS_GREEN = "#27AE60"     # Nominal/target values
    COLOR_EXCELLENT_TEAL = "#1ABC9C"    # Superior performance
    COLOR_WARNING_ORANGE = "#F39C12"    # Warning zones
    COLOR_DANGER_RED = "#E74C3C"        # Out of control, reject zones
    COLOR_DARK_GRAY = "#2C3E50"         # Text, borders
    COLOR_MEDIUM_GRAY = "#95A5A6"       # Grid lines
    COLOR_LIGHT_GRAY = "#ECF0F1"        # Background accents
    COLOR_WHITE = "#FFFFFF"
    
    # Professional font settings
    FONT_NAME = "Arial"
    FONT_SIZE_TITLE = 14
    FONT_SIZE_SUBTITLE = 11
    FONT_SIZE_LABEL = 10
    FONT_SIZE_TICK = 9
    FONT_SIZE_LEGEND = 9
    FONT_SIZE_ANNOTATION = 8
    
    # Layout settings
    GOLDEN_RATIO = (1 + 5**0.5) / 2
    DPI = 300
    FIGURE_FACECOLOR = "#FFFFFF"
    AXES_FACECOLOR = "#FAFAFA"
    
    # Line weights (professional standards)
    LINEWIDTH_CONTROL = 1.8
    LINEWIDTH_DATA = 1.2
    LINEWIDTH_GRID = 0.6
    LINEWIDTH_SPEC = 1.0
    
    # Marker settings
    MARKERSIZE = 6
    MARKER_EDGEWIDTH = 0.8

    def __init__(
        self,
        input_json_path: str | Path,
        lang: str = "ca",
        show: bool = False,
        save_path: str | Path = None,
        i18n_folder: str | Path = None,
        extra_rcparams: dict = None,
        logger: logging.Logger = None,
        element_name: str = None,
    ):
        self.logger = logger or base_logger.getChild(self.__class__.__name__)
        self.logger.info(f"🔄 Initializing {self.__class__.__name__} with professional styling")

        self.input_json_path = Path(input_json_path)
        self.lang = lang
        self.show = show
        self.save_path = Path(save_path) if save_path else None
        self.i18n_folder = (
            Path(i18n_folder)
            if i18n_folder
            else self.input_json_path.parent.parent.parent / "i18n"
        )
        self.extra_rcparams = extra_rcparams or {}

        try:
            self.elements_data = self._load_data()
            if not self.elements_data:
                raise ValueError("No SPC elements found in the input JSON.")

            self.element_name = element_name or next(iter(self.elements_data))
            if self.element_name not in self.elements_data:
                raise KeyError(f"Element '{self.element_name}' not found in SPC data.")

            self.element_data = self.elements_data[self.element_name]
            self.labels = self._load_translations()
            self._configure_professional_style()

        except Exception as e:
            self.logger.error(f"❌ Error during initialization: {e}", exc_info=True)
            raise

    def _load_data(self) -> dict:
        """Load data from JSON file"""
        if not self.input_json_path.exists():
            raise FileNotFoundError(f"Input JSON file not found: {self.input_json_path}")
        with self.input_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("SPC input JSON must be a dictionary of elements.")
        return data

    def _load_translations(self) -> dict:
        """Load translations with fallback"""
        lang_file = self.i18n_folder / f"{self.lang}.json"
        default_file = self.i18n_folder / "ca.json"
        fallback_labels = {
            "title": "Control Chart",
            "xlabel": "Sample Number",
            "ylabel": "Measurement Value",
        }

        if lang_file.exists():
            path = lang_file
        elif default_file.exists():
            path = default_file
        else:
            return fallback_labels

        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return fallback_labels

    def _configure_professional_style(self):
        """Configure professional PPAP-compliant matplotlib style"""
        professional_params = {
            # Font settings
            'font.family': self.FONT_NAME,
            'font.size': self.FONT_SIZE_LABEL,
            
            # Figure settings
            'figure.facecolor': self.FIGURE_FACECOLOR,
            'figure.edgecolor': self.COLOR_DARK_GRAY,
            'figure.dpi': self.DPI,
            'savefig.dpi': self.DPI,
            'savefig.facecolor': self.FIGURE_FACECOLOR,
            'savefig.edgecolor': 'none',
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,
            
            # Axes settings
            'axes.facecolor': self.AXES_FACECOLOR,
            'axes.edgecolor': self.COLOR_DARK_GRAY,
            'axes.linewidth': 1.2,
            'axes.labelsize': self.FONT_SIZE_LABEL,
            'axes.labelweight': 'normal',
            'axes.labelcolor': self.COLOR_DARK_GRAY,
            'axes.titlesize': self.FONT_SIZE_TITLE,
            'axes.titleweight': 'bold',
            'axes.titlecolor': self.COLOR_PRIMARY_BLUE,
            'axes.titlepad': 15,
            'axes.grid': True,
            'axes.axisbelow': True,
            'axes.spines.top': True,
            'axes.spines.right': True,
            'axes.spines.left': True,
            'axes.spines.bottom': True,
            
            # Grid settings
            'grid.color': self.COLOR_MEDIUM_GRAY,
            'grid.linestyle': '--',
            'grid.linewidth': self.LINEWIDTH_GRID,
            'grid.alpha': 0.3,
            
            # Tick settings
            'xtick.labelsize': self.FONT_SIZE_TICK,
            'xtick.color': self.COLOR_DARK_GRAY,
            'xtick.major.size': 5,
            'xtick.major.width': 1,
            'xtick.direction': 'out',
            'ytick.labelsize': self.FONT_SIZE_TICK,
            'ytick.color': self.COLOR_DARK_GRAY,
            'ytick.major.size': 5,
            'ytick.major.width': 1,
            'ytick.direction': 'out',
            
            # Legend settings
            'legend.fontsize': self.FONT_SIZE_LEGEND,
            'legend.frameon': True,
            'legend.framealpha': 0.95,
            'legend.facecolor': self.COLOR_WHITE,
            'legend.edgecolor': self.COLOR_MEDIUM_GRAY,
            'legend.loc': 'best',
            'legend.borderpad': 0.6,
            'legend.labelspacing': 0.5,
            
            # Line settings
            'lines.linewidth': self.LINEWIDTH_DATA,
            'lines.markersize': self.MARKERSIZE,
            'lines.markeredgewidth': self.MARKER_EDGEWIDTH,
        }
        
        professional_params.update(self.extra_rcparams)
        mpl.rcParams.update(professional_params)

    def _create_figure(self, figsize=None):
        """Create figure with professional styling"""
        if figsize is None:
            width = 12
            height = width / self.GOLDEN_RATIO
            figsize = (width, height)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Professional border
        for spine in ax.spines.values():
            spine.set_edgecolor(self.COLOR_DARK_GRAY)
            spine.set_linewidth(1.2)
        
        return fig, ax

    def _set_titles_and_labels(self, ax, title=None, xlabel=None, ylabel=None, subtitle=None):
        """Set titles and labels with professional formatting and proper spacing"""
        if title:
            ax.set_title(title, fontsize=self.FONT_SIZE_TITLE, 
                        fontweight='bold', color=self.COLOR_PRIMARY_BLUE, pad=10)
        
        if subtitle:
            # Position subtitle below title with proper spacing
            ax.text(0.5, 1.00, subtitle, transform=ax.transAxes,
                   fontsize=self.FONT_SIZE_SUBTITLE, color=self.COLOR_DARK_GRAY,
                   ha='center', va='bottom', style='italic')
        
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=self.FONT_SIZE_LABEL, 
                         color=self.COLOR_DARK_GRAY, fontweight='normal')
        
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=self.FONT_SIZE_LABEL, 
                         color=self.COLOR_DARK_GRAY, fontweight='normal')

    def _set_legend(self, ax, **kwargs):
        """Set legend with professional styling"""
        legend_props = {
            'fontsize': self.FONT_SIZE_LEGEND,
            'frameon': True,
            'framealpha': 0.95,
            'facecolor': self.COLOR_WHITE,
            'edgecolor': self.COLOR_MEDIUM_GRAY,
            'loc': 'best',
            'ncol': 1,
        }
        legend_props.update(kwargs)
        
        legend = ax.legend(**legend_props)
        legend.get_frame().set_linewidth(0.8)

    def _add_professional_annotation(self, ax, x, y, text, color=None):
        """Add professional annotation to chart"""
        if color is None:
            color = self.COLOR_DARK_GRAY
        
        ax.annotate(text, xy=(x, y), xytext=(5, 5),
                   textcoords='offset points',
                   fontsize=self.FONT_SIZE_ANNOTATION,
                   color=color, weight='normal',
                   bbox=dict(boxstyle='round,pad=0.3', 
                            facecolor=self.COLOR_WHITE,
                            edgecolor=color, linewidth=0.8, alpha=0.9))

    @abstractmethod
    def plot(self):
        """Implement this method in subclasses"""
        pass

    def _finalize(self):
        """Finalize and save chart"""
        try:
            plt.tight_layout()
            
            if self.save_path:
                if not isinstance(self.save_path, Path):
                    self.save_path = Path(self.save_path)
                
                self.save_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(self.save_path, dpi=self.DPI, bbox_inches='tight',
                           facecolor=self.FIGURE_FACECOLOR, edgecolor='none')
                
                if self.save_path.exists():
                    file_size = self.save_path.stat().st_size
                    self.logger.info(f"✅ Chart saved: {self.save_path.name} ({file_size} bytes)")
                else:
                    raise RuntimeError(f"Chart file was not created: {self.save_path}")
            
            if self.show:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"❌ Error in _finalize(): {e}", exc_info=True)
            raise
        finally:
            plt.close()