"""Central logging configuration for CLI jobs and later pipeline phases."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_directory: Path, level: int = logging.INFO) -> None:
    """Send consistent messages to both the terminal and a UTF-8 log file."""

    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "project.log"

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
