"""Console + file logging.

Every send attempt (success or failure) MUST be logged here AND written to
reminder_log. Silent failures are not acceptable.
"""

import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to both console and automation.log."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(_FORMAT))
        fh = logging.FileHandler(LOG_DIR / "automation.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(console)
        logger.addHandler(fh)
    return logger
