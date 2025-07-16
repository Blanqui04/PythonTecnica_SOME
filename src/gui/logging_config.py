import logging
import os

# Ensure the logs directory exists
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "gui.log")

# Create and configure logger
logger = logging.getLogger("gui_logger")
logger.setLevel(logging.DEBUG)  # Or INFO if you want less verbosity

# Prevent adding handlers multiple times
if not logger.handlers:
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(file_handler)

# Optional: Also log to console for debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
