"""Single logging configuration point for the whole pipeline.

Every module gets its logger via `get_logger(__name__)`. All logs go to
the same file (config.settings.LOG_FILE) plus the console, so there is one
place to look for what happened during a run.
"""

from __future__ import annotations

import logging

from config.settings import LOG_DIR, LOG_FILE, LOG_LEVEL

_CONFIGURED = False


def configure_logging() -> None:
    """Set up the root logger once. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use."""
    configure_logging()
    return logging.getLogger(name)
