# src/models/capability/logging_config.py

import logging
import os

# Ensure the logs directory exists
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../logs"))
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "capability_plot.log")

# Create and configure a module-specific logger
logger = logging.getLogger("spc_plot_logger")
logger.setLevel(logging.DEBUG)  # Use INFO or WARNING in production

# Avoid duplicate handlers
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == LOG_FILE_PATH for h in logger.handlers):
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Add console handler only if it's not already present
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Prevent log messages from being propagated to the root logger
logger.propagate = False
