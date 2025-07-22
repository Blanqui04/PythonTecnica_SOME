# src/models/plotting/base_chart.py
import json
from pathlib import Path
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import matplotlib as mpl
import logging
from .logging_config import logger as base_logger


class SPCChartBase(ABC):
    FONT_NAME = "Arial"
    COLOR_BLAU = "#0072B2"
    COLOR_NEGRE = "#000000"
    COLOR_TARONJA = "#E69F00"
    COLOR_VERMELL = "#D55E00"
    COLOR_VERD = "#009E73"
    COLOR_GRIS = "#999999"
    GOLDEN_RATIO = (1 + 5**0.5) / 2

    def __init__(
        self,
        input_json_path: str | Path,
        lang: str = "ca",
        show: bool = False,
        save_path: str | Path = None,
        i18n_folder: str | Path = None,
        extra_rcparams: dict = None,
        logger: logging.Logger = None,
        element_name: str = None,  # NEW: allows targeting a single element from the JSON
    ):
        self.logger = logger or base_logger.getChild(self.__class__.__name__)
        self.logger.info(f"Initializing SPCChartBase with input: {input_json_path}")

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
            self.logger.info(f"Selected SPC element: {self.element_name}")

            self.labels = self._load_translations()
            self._configure_style()

        except Exception as e:
            self.logger.error(f"Error during initialization: {e}", exc_info=True)
            raise

    def _load_data(self) -> dict:
        self.logger.debug(f"Loading data from {self.input_json_path}")
        if not self.input_json_path.exists():
            raise FileNotFoundError(
                f"Input JSON file not found: {self.input_json_path}"
            )
        with self.input_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("SPC input JSON must be a dictionary of elements.")
        self.logger.info(f"Loaded SPC data for {len(data)} element(s).")
        return data

    def _load_translations(self) -> dict:
        lang_file = self.i18n_folder / f"{self.lang}.json"
        default_file = self.i18n_folder / "ca.json"
        fallback_labels = {
            "title": "Gràfica",
            "xlabel": "Eix X",
            "ylabel": "Eix Y",
            "legend": "Llegenda",
        }

        if lang_file.exists():
            path = lang_file
            self.logger.info(f"Loading translations from {lang_file}")
        elif default_file.exists():
            path = default_file
            self.logger.warning(
                f"Translation file for '{self.lang}' not found. Using default 'ca.json'."
            )
        else:
            self.logger.warning("No translation file found. Using fallback labels.")
            return fallback_labels

        try:
            with path.open("r", encoding="utf-8") as f:
                translations = json.load(f)
            self.logger.info("Translations loaded successfully.")
            return translations
        except Exception as e:
            self.logger.error(f"Failed to load translation file: {e}")
            return fallback_labels

    def _configure_style(self):
        self.logger.debug("Configuring matplotlib style.")
        base_params = {
            "font.family": self.FONT_NAME,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "axes.labelcolor": self.COLOR_NEGRE,
            "axes.edgecolor": self.COLOR_GRIS,
            "axes.grid": True,
            "grid.color": self.COLOR_GRIS,
            "grid.linestyle": "--",
            "grid.alpha": 0.7,
            "xtick.color": self.COLOR_NEGRE,
            "ytick.color": self.COLOR_NEGRE,
            "legend.fontsize": 11,
            "legend.loc": "best",
            "figure.figsize": (8, 5),
            "lines.linewidth": 2,
            "lines.markersize": 6,
            "axes.prop_cycle": mpl.cycler(
                color=[
                    self.COLOR_BLAU,
                    self.COLOR_TARONJA,
                    self.COLOR_VERMELL,
                    self.COLOR_VERD,
                    self.COLOR_GRIS,
                ]
            ),
        }
        base_params.update(self.extra_rcparams)
        mpl.rcParams.update(base_params)
        self.logger.debug("Matplotlib style configured.")

    def _create_figure(self, figsize=None):
        if figsize is None:
            width = 10
            height = width / self.GOLDEN_RATIO
            figsize = (width, height)
        self.logger.debug(f"Creating figure with size: {figsize}")
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax

    def _set_titles_and_labels(self, ax, title=None, xlabel=None, ylabel=None):
        self.logger.debug(
            f"Setting titles and labels: title={title}, xlabel={xlabel}, ylabel={ylabel}"
        )
        ax.set_title(title or self.labels.get("title", ""))
        ax.set_xlabel(xlabel or self.labels.get("xlabel", ""))
        ax.set_ylabel(ylabel or self.labels.get("ylabel", ""))

    def _set_legend(self, ax):
        self.logger.debug("Setting legend.")
        ax.legend(title=self.labels.get("legend", ""))

    @abstractmethod
    def plot(self):
        """Implement this method in subclasses to generate the desired SPC chart."""
        pass

    def _finalize(self):
        if self.save_path:
            self.logger.info(f"Saving figure to {self.save_path}")
            plt.savefig(self.save_path, dpi=300, bbox_inches="tight")
        if self.show:
            self.logger.info("Showing figure on screen.")
            plt.show()
        plt.close()
        self.logger.debug("Figure closed.")
